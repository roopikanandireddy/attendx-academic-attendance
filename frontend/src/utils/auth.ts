import type { User } from '../types';

export const TOKEN_STORAGE_KEY = 'attendx_token';
export const USER_STORAGE_KEY = 'attendx_user';
export const AUTH_EXPIRED_EVENT = 'attendx:session_expired';

export interface JwtPayload {
  sub?: string;
  role?: string;
  exp?: number;
  [key: string]: unknown;
}

/**
 * Robust zero-dependency JWT decoder.
 * Safely decodes base64url-encoded JWT payloads across all browsers and Node.js environments.
 */
export function parseJwtPayload(token: string): JwtPayload | null {
  try {
    const parts = token.split('.');
    if (parts.length !== 3) return null;
    const base64Url = parts[1];
    const base64 = base64Url.replace(/-/g, '+').replace(/_/g, '/');
    const jsonPayload = decodeURIComponent(
      atob(base64)
        .split('')
        .map((c) => '%' + ('00' + c.charCodeAt(0).toString(16)).slice(-2))
        .join('')
    );
    return JSON.parse(jsonPayload) as JwtPayload;
  } catch {
    return null;
  }
}

/**
 * Check if JWT is expired based on its client-side `exp` timestamp.
 * Includes a 5-second buffer to prevent race conditions at expiry boundary.
 */
export function isTokenExpired(token: string, bufferSeconds = 5): boolean {
  const payload = parseJwtPayload(token);
  if (!payload || typeof payload.exp !== 'number') return true;
  return payload.exp * 1000 <= Date.now() + bufferSeconds * 1000;
}

/**
 * Retrieve saved JWT token from localStorage.
 */
export function getStoredToken(): string | null {
  try {
    return localStorage.getItem(TOKEN_STORAGE_KEY);
  } catch {
    return null;
  }
}

/**
 * Retrieve and parse saved User profile from localStorage.
 */
export function getStoredUser(): User | null {
  try {
    const raw = localStorage.getItem(USER_STORAGE_KEY);
    if (!raw) return null;
    return JSON.parse(raw) as User;
  } catch {
    return null;
  }
}

/**
 * Persist authentication session to localStorage.
 */
export function setStoredAuth(token: string, user: User): void {
  try {
    localStorage.setItem(TOKEN_STORAGE_KEY, token);
    localStorage.setItem(USER_STORAGE_KEY, JSON.stringify(user));
  } catch (err) {
    console.error('[AttendX Auth] Failed to save authentication session to localStorage', err);
  }
}

/**
 * Clear authentication session from localStorage.
 */
export function clearStoredAuth(): void {
  try {
    localStorage.removeItem(TOKEN_STORAGE_KEY);
    localStorage.removeItem(USER_STORAGE_KEY);
  } catch (err) {
    console.error('[AttendX Auth] Failed to remove authentication session from localStorage', err);
  }
}

/**
 * Determine if an API request endpoint is a public authentication route
 * where 401/400 errors represent validation/credential failures, not expired sessions.
 */
export function isPublicAuthEndpoint(url?: string): boolean {
  if (!url) return false;
  const publicPaths = [
    '/api/auth/login',
    '/api/auth/register',
    '/api/auth/verify-token',
    '/api/auth/verify-activation-token',
    '/api/auth/activate',
    '/api/auth/forgot-password',
    '/api/auth/verify-reset-token',
    '/api/auth/reset-password',
  ];
  return publicPaths.some((p) => url.includes(p));
}

/**
 * Determine if a browser route is public.
 */
export function isPublicRoute(pathname?: string): boolean {
  if (!pathname) return true;
  const publicRoutes = [
    '/',
    '/login',
    '/register',
    '/activate-account',
    '/forgot-password',
    '/reset-password',
    '/student/login',
    '/lecturer/login',
    '/admin/login',
    '/student/register',
    '/lecturer/register',
    '/admin/register',
  ];
  return publicRoutes.includes(pathname);
}
