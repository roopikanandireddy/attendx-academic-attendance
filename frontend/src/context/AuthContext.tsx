import React, { createContext, useContext, useState, useEffect, useCallback } from 'react';
import api from '../services/api';
import type { User, TokenResponse } from '../types';

interface AuthContextType {
  user: User | null;
  token: string | null;
  loading: boolean;
  login: (email: string, password: string) => Promise<void>;
  register: (data: Record<string, unknown>) => Promise<void>;
  logout: () => void;
  updateUser: (user: User) => void;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [token, setToken] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  const initAuth = useCallback(async () => {
    const savedToken = localStorage.getItem('attendx_token');
    const savedUser = localStorage.getItem('attendx_user');
    if (savedToken && savedUser) {
      setToken(savedToken);
      try {
        const parsed = JSON.parse(savedUser);
        setUser(parsed);
        // Verify token is still valid
        const res = await api.get('/api/auth/me');
        setUser(res.data);
        localStorage.setItem('attendx_user', JSON.stringify(res.data));
      } catch {
        localStorage.removeItem('attendx_token');
        localStorage.removeItem('attendx_user');
        setToken(null);
        setUser(null);
      }
    }
    setLoading(false);
  }, []);

  useEffect(() => {
    initAuth();
  }, [initAuth]);

  const login = async (email: string, password: string) => {
    const res = await api.post<TokenResponse>('/api/auth/login', { email, password });
    const { access_token, user: userData } = res.data;
    setToken(access_token);
    setUser(userData);
    localStorage.setItem('attendx_token', access_token);
    localStorage.setItem('attendx_user', JSON.stringify(userData));
  };

  const register = async (data: Record<string, unknown>) => {
    const res = await api.post<TokenResponse>('/api/auth/register', data);
    const { access_token, user: userData } = res.data;
    setToken(access_token);
    setUser(userData);
    localStorage.setItem('attendx_token', access_token);
    localStorage.setItem('attendx_user', JSON.stringify(userData));
  };

  const logout = () => {
    setToken(null);
    setUser(null);
    localStorage.removeItem('attendx_token');
    localStorage.removeItem('attendx_user');
  };

  const updateUser = (updatedUser: User) => {
    setUser(updatedUser);
    localStorage.setItem('attendx_user', JSON.stringify(updatedUser));
  };

  return (
    <AuthContext.Provider value={{ user, token, loading, login, register, logout, updateUser }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error('useAuth must be used within AuthProvider');
  return ctx;
}
