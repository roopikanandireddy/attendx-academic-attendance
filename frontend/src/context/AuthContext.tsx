import React, { createContext, useContext, useState, useEffect, useCallback, useRef } from 'react';
import api from '../services/api';
import type { User, TokenResponse } from '../types';
import {
  getStoredToken,
  getStoredUser,
  setStoredAuth,
  clearStoredAuth,
  isTokenExpired,
  AUTH_EXPIRED_EVENT,
} from '../utils/auth';
import {
  bootstrapSession,
  markSessionFresh,
  invalidateSessionCache,
} from '../services/authBootstrap';

interface AuthContextType {
  user: User | null;
  token: string | null;
  loading: boolean;
  login: (email: string, password: string) => Promise<User>;
  register: (data: Record<string, unknown>) => Promise<void>;
  logout: () => void;
  updateUser: (user: User) => void;
  refreshSession: () => Promise<User | null>;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export function AuthProvider({ children }: { children: React.ReactNode }) {
  // Synchronous initialization from localStorage: renders instantly without blocking on network
  const [user, setUser] = useState<User | null>(() => {
    const savedToken = getStoredToken();
    if (!savedToken || isTokenExpired(savedToken)) {
      clearStoredAuth();
      return null;
    }
    return getStoredUser();
  });

  const [token, setToken] = useState<string | null>(() => {
    const savedToken = getStoredToken();
    if (!savedToken || isTokenExpired(savedToken)) {
      clearStoredAuth();
      return null;
    }
    return savedToken;
  });

  const [loading, setLoading] = useState(false);
  const isVerifyingRef = useRef(false);

  // Background session verification: runs single deduplicated check via authBootstrap
  const verifySession = useCallback(async (force = false) => {
    if (isVerifyingRef.current) return;
    const currentToken = getStoredToken();
    if (!currentToken || isTokenExpired(currentToken)) {
      setUser(null);
      setToken(null);
      return;
    }

    isVerifyingRef.current = true;
    if (force) setLoading(true);
    try {
      const verifiedUser = await bootstrapSession({ force });
      if (verifiedUser) {
        setUser(verifiedUser);
        setToken(currentToken);
      } else {
        setUser(null);
        setToken(null);
      }
    } catch {
      // In case of unexpected bootstrap error, retain current user if token is still valid
    } finally {
      isVerifyingRef.current = false;
      if (force) setLoading(false);
    }
  }, []);

  useEffect(() => {
    // If a saved unexpired token exists, verify in background without blocking initial render
    const savedToken = getStoredToken();
    if (savedToken && !isTokenExpired(savedToken)) {
      verifySession();
    }

    // Listen for session expiration events from API response interceptor
    const handleSessionExpired = () => {
      setUser(null);
      setToken(null);
    };

    window.addEventListener(AUTH_EXPIRED_EVENT, handleSessionExpired);
    return () => {
      window.removeEventListener(AUTH_EXPIRED_EVENT, handleSessionExpired);
    };
  }, [verifySession]);

  const login = async (email: string, password: string): Promise<User> => {
    const res = await api.post<TokenResponse>('/api/auth/login', { email, password });
    const { access_token, user: userData } = res.data;

    // Mark session as fresh: prevents subsequent dashboard navigation from triggering /api/auth/me
    markSessionFresh(access_token, userData);
    setToken(access_token);
    setUser(userData);

    return userData;
  };

  const register = async (data: Record<string, unknown>) => {
    const res = await api.post<TokenResponse>('/api/auth/register', data);
    const { access_token, user: userData } = res.data;

    markSessionFresh(access_token, userData);
    setToken(access_token);
    setUser(userData);
  };

  const logout = () => {
    invalidateSessionCache();
    setToken(null);
    setUser(null);
  };

  const updateUser = (updatedUser: User) => {
    setUser(updatedUser);
    const currentToken = getStoredToken();
    if (currentToken) {
      setStoredAuth(currentToken, updatedUser);
    }
  };

  const refreshSession = async () => {
    const currentToken = getStoredToken();
    if (!currentToken) return null;
    const res = await bootstrapSession({ force: true });
    if (res) {
      setUser(res);
      setToken(currentToken);
    }
    return res;
  };

  return (
    <AuthContext.Provider value={{ user, token, loading, login, register, logout, updateUser, refreshSession }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error('useAuth must be used within AuthProvider');
  return ctx;
}
