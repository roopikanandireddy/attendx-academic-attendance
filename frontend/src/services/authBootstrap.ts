import api from './api';
import type { User } from '../types';
import {
  getStoredToken,
  getStoredUser,
  setStoredAuth,
  clearStoredAuth,
  isTokenExpired,
  AUTH_EXPIRED_EVENT,
} from '../utils/auth';

let inFlightBootstrapPromise: Promise<User | null> | null = null;
let lastVerifiedToken: string | null = null;
let lastVerifiedTimestamp = 0;

// Freshness TTL: sessions verified within 60 seconds skip redundant network roundtrips
const BOOTSTRAP_FRESHNESS_TTL_MS = 60 * 1000;

/**
 * Mark session as freshly verified (called immediately after login or registration).
 */
export function markSessionFresh(token: string, user: User): void {
  lastVerifiedToken = token;
  lastVerifiedTimestamp = Date.now();
  setStoredAuth(token, user);
}

/**
 * Invalidate session cache (called on logout or unrecoverable session rejection).
 */
export function invalidateSessionCache(): void {
  lastVerifiedToken = null;
  lastVerifiedTimestamp = 0;
  inFlightBootstrapPromise = null;
  clearStoredAuth();
}

/**
 * Check if the active session was verified within the freshness window.
 */
export function isSessionFresh(): boolean {
  const token = getStoredToken();
  if (!token || isTokenExpired(token)) return false;
  return lastVerifiedToken === token && (Date.now() - lastVerifiedTimestamp < BOOTSTRAP_FRESHNESS_TTL_MS);
}

/**
 * Get current verification metrics for diagnostics/testing.
 */
export function getBootstrapMetrics() {
  return {
    hasInFlightPromise: inFlightBootstrapPromise !== null,
    lastVerifiedToken: lastVerifiedToken ? `${lastVerifiedToken.slice(0, 10)}...` : null,
    lastVerifiedTimestamp,
    freshnessTtlMs: BOOTSTRAP_FRESHNESS_TTL_MS,
  };
}

/**
 * Bootstrap authentication session with:
 * 1. Client-side JWT expiration checking (0ms)
 * 2. Freshness check to avoid login -> /me -> dashboard duplicate chains
 * 3. Singleton in-flight request deduplication (prevents React 18 StrictMode double-fetch)
 * 4. Session resilience (preserves cached user across network drops and Render 502/503 cold starts)
 */
export async function bootstrapSession(options?: { force?: boolean }): Promise<User | null> {
  const token = getStoredToken();
  const cachedUser = getStoredUser();

  // 1. If no token or no cached user, clear any orphan state and return null
  if (!token || !cachedUser) {
    if (token || cachedUser) {
      clearStoredAuth();
    }
    return null;
  }

  // 2. Client-side expiration check (0 ms - avoids doomed network roundtrip)
  if (isTokenExpired(token)) {
    invalidateSessionCache();
    if (typeof window !== 'undefined') {
      window.dispatchEvent(new CustomEvent(AUTH_EXPIRED_EVENT, { detail: { reason: 'expired' } }));
    }
    return null;
  }

  // 3. Freshness check — avoid duplicate verification if verified within TTL (e.g. right after login)
  if (!options?.force && lastVerifiedToken === token && (Date.now() - lastVerifiedTimestamp < BOOTSTRAP_FRESHNESS_TTL_MS)) {
    return cachedUser;
  }

  // 4. In-flight promise sharing (singleton deduplication)
  if (inFlightBootstrapPromise) {
    return inFlightBootstrapPromise;
  }

  // 5. Execute single network verification call to /api/auth/me
  inFlightBootstrapPromise = (async () => {
    try {
      const res = await api.get<User>('/api/auth/me');
      const freshUser = res.data;
      markSessionFresh(token, freshUser);
      return freshUser;
    } catch (err: any) {
      const status = err.response?.status;
      if (status === 401) {
        // Token revoked or rejected by backend
        invalidateSessionCache();
        if (typeof window !== 'undefined') {
          window.dispatchEvent(new CustomEvent(AUTH_EXPIRED_EVENT, { detail: { reason: 'unauthorized' } }));
        }
        return null;
      }
      if (status === 403) {
        // Account disabled or suspended
        invalidateSessionCache();
        if (typeof window !== 'undefined') {
          window.dispatchEvent(new CustomEvent(AUTH_EXPIRED_EVENT, { detail: { reason: 'forbidden' } }));
        }
        return null;
      }

      // SESSION RESILIENCE:
      // Network drop, timeout, or server cold start (500, 502, 503)
      // Do NOT wipe the session! Retain the cached user session so users are not locked out.
      console.warn(
        '[AttendX AuthBootstrap] Server verification temporarily unavailable, retaining resilient cached session:',
        err.message || status
      );
      return cachedUser;
    } finally {
      inFlightBootstrapPromise = null;
    }
  })();

  return inFlightBootstrapPromise;
}
