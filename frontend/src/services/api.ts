import axios from 'axios';
import {
  getStoredToken,
  clearStoredAuth,
  isPublicAuthEndpoint,
  isPublicRoute,
  AUTH_EXPIRED_EVENT,
} from '../utils/auth';

const rawApiUrl = import.meta.env.VITE_API_URL;
const API_URL = (rawApiUrl && typeof rawApiUrl === 'string' && rawApiUrl.trim())
  ? rawApiUrl.trim().replace(/\/+$/, '')
  : 'http://localhost:8000';

const api = axios.create({
  baseURL: API_URL,
  timeout: 20000,
  headers: {
    'Content-Type': 'application/json',
  },
});

/**
 * Check whether an error was caused by an aborted or cancelled request.
 * Cancellation is a normal control-flow event in React component lifecycles,
 * NOT a server or network failure.
 */
export function isRequestCancelled(error: unknown): boolean {
  if (!error) return false;
  if (axios.isCancel(error)) return true;
  if (typeof error === 'object' && error !== null) {
    const err = error as Record<string, unknown>;
    if (err.name === 'CanceledError' || err.name === 'AbortError') return true;
    if (err.code === 'ERR_CANCELED') return true;
  }
  return false;
}

export type ApiErrorKind =
  | 'CANCELLED'
  | 'AUTHENTICATION_FAILURE'
  | 'AUTHORIZATION_FAILURE'
  | 'VALIDATION_FAILURE'
  | 'NOT_FOUND'
  | 'CONFLICT'
  | 'SERVER_FAILURE'
  | 'NETWORK_FAILURE'
  | 'UNKNOWN';

/**
 * Classify API errors into standardized semantic categories
 * for clean, predictable UI handling.
 */
export function classifyApiError(error: unknown): ApiErrorKind {
  if (isRequestCancelled(error)) {
    return 'CANCELLED';
  }
  if (axios.isAxiosError(error)) {
    const status = error.response?.status;
    if (status === 401) return 'AUTHENTICATION_FAILURE';
    if (status === 403) return 'AUTHORIZATION_FAILURE';
    if (status === 422) return 'VALIDATION_FAILURE';
    if (status === 404) return 'NOT_FOUND';
    if (status === 409) return 'CONFLICT';
    if (status && status >= 500) return 'SERVER_FAILURE';
    if (!error.response && error.request) return 'NETWORK_FAILURE';
  }
  return 'UNKNOWN';
}

export interface RequestTiming {
  requestId?: string;
  durationMs: number;
  status?: number;
  category?: ApiErrorKind;
}

/**
 * Generate a cryptographically secure random UUID v4 for request correlation.
 * Contains no credentials, JWTs, or user identifiers.
 */
export function generateRequestId(): string {
  if (typeof crypto !== 'undefined' && typeof crypto.randomUUID === 'function') {
    return crypto.randomUUID();
  }
  return 'req_' + Math.random().toString(36).substring(2, 10) + Date.now().toString(36);
}

/**
 * Helper to inspect measured timing on completed Axios responses.
 */
export function getResponseTiming(response: unknown): RequestTiming | null {
  if (response && typeof response === 'object' && 'timing' in response) {
    return (response as { timing: RequestTiming }).timing;
  }
  return null;
}

// Request interceptor — attach token if present & generate correlation X-Request-ID
api.interceptors.request.use(
  (config) => {
    // 1. Attach JWT Authorization header if authenticated
    const token = getStoredToken();
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }

    // 2. Attach or propagate correlation X-Request-ID
    if (!config.headers['X-Request-ID']) {
      config.headers['X-Request-ID'] = generateRequestId();
    }

    // 3. Mark request start timestamp
    const now = typeof performance !== 'undefined' ? performance.now() : Date.now();
    (config as unknown as Record<string, unknown>).__startTime = now;
    (config as unknown as Record<string, unknown>).__requestId = config.headers['X-Request-ID'];

    return config;
  },
  (error) => Promise.reject(error)
);

// Response interceptor — handle session expiration safely while recording duration
api.interceptors.response.use(
  (response) => {
    const config = response.config as unknown as Record<string, unknown>;
    const startTime = typeof config?.__startTime === 'number' ? config.__startTime : null;
    const now = typeof performance !== 'undefined' ? performance.now() : Date.now();
    const durationMs = startTime !== null ? Math.round(now - startTime) : 0;
    const requestId =
      response.headers?.['x-request-id'] ||
      response.headers?.['X-Request-ID'] ||
      (config?.__requestId as string) ||
      undefined;

    // Attach timing metadata onto response object for safe client observability
    (response as unknown as Record<string, unknown>).timing = {
      requestId,
      durationMs,
      status: response.status,
      category: 'SUCCESS',
    };

    return response;
  },
  (error) => {
    // Measure duration on failed/cancelled requests
    const config = error?.config as unknown as Record<string, unknown> | undefined;
    const startTime = typeof config?.__startTime === 'number' ? config.__startTime : null;
    const now = typeof performance !== 'undefined' ? performance.now() : Date.now();
    const durationMs = startTime !== null ? Math.round(now - startTime) : 0;
    const requestId =
      error?.response?.headers?.['x-request-id'] ||
      (config?.__requestId as string) ||
      undefined;
    const category = classifyApiError(error);

    if (error && typeof error === 'object') {
      (error as unknown as Record<string, unknown>).timing = {
        requestId,
        durationMs,
        status: error.response?.status,
        category,
      };
    }

    // Expected lifecycle cancellations must NEVER trigger session expiration or logout
    if (isRequestCancelled(error)) {
      return Promise.reject(error);
    }

    const url = error.config?.url;
    const isPublicAuth = isPublicAuthEndpoint(url);

    // Only clear session on 401 for authenticated protected requests
    if (error.response?.status === 401 && !isPublicAuth) {
      clearStoredAuth();
      if (typeof window !== 'undefined') {
        window.dispatchEvent(new CustomEvent(AUTH_EXPIRED_EVENT, { detail: { reason: 'expired' } }));
        // Only perform fallback redirect if currently on a protected route
        if (!isPublicRoute(window.location.pathname) && window.location.pathname !== '/login') {
          window.location.href = '/login';
        }
      }
    }
    return Promise.reject(error);
  }
);

export default api;
