/**
 * Frontend Auth Bootstrap Verification Script
 * Validates:
 * 1. Client-side JWT parsing & expiration checking
 * 2. Synchronous storage hydration
 * 3. Freshness TTL cache (0 network requests right after login)
 * 4. Concurrent in-flight promise deduplication
 * 5. Session resilience against 502/503/timeout/network failures
 * 6. Clean session invalidation on 401/403
 * 7. Public endpoint / route classification
 */

const assert = require('assert');

// Mock localStorage
const storage = new Map();
global.localStorage = {
  getItem: (k) => storage.get(k) || null,
  setItem: (k, v) => storage.set(k, String(v)),
  removeItem: (k) => storage.delete(k),
  clear: () => storage.clear(),
};

// Mock window and CustomEvent
global.window = {
  location: { pathname: '/dashboard', href: '/dashboard' },
  dispatchEvent: (evt) => {
    dispatchedEvents.push(evt);
  },
};
const dispatchedEvents = [];
global.CustomEvent = class CustomEvent {
  constructor(type, init) {
    this.type = type;
    this.detail = init?.detail;
  }
};

// Base64 helper for Node
global.atob = (str) => Buffer.from(str, 'base64').toString('binary');

// Helper to make mock JWT
function createMockJwt(payload) {
  const header = Buffer.from(JSON.stringify({ alg: 'HS256', typ: 'JWT' })).toString('base64url');
  const body = Buffer.from(JSON.stringify(payload)).toString('base64url');
  const sig = 'mock_signature';
  return `${header}.${body}.${sig}`;
}

// Inline implementations identical to auth.ts for isolated testing
function parseJwtPayload(token) {
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
    return JSON.parse(jsonPayload);
  } catch {
    return null;
  }
}

function isTokenExpired(token, bufferSeconds = 5) {
  const payload = parseJwtPayload(token);
  if (!payload || typeof payload.exp !== 'number') return true;
  return payload.exp * 1000 <= Date.now() + bufferSeconds * 1000;
}

class MockAuthBootstrapService {
  constructor() {
    this.inFlightPromise = null;
    this.lastVerifiedToken = null;
    this.lastVerifiedTimestamp = 0;
    this.freshnessTtlMs = 60000;
    this.apiCallsCount = 0;
    this.mockApiResponse = null;
    this.mockApiError = null;
  }

  markSessionFresh(token, user) {
    this.lastVerifiedToken = token;
    this.lastVerifiedTimestamp = Date.now();
    localStorage.setItem('attendx_token', token);
    localStorage.setItem('attendx_user', JSON.stringify(user));
  }

  invalidateSessionCache() {
    this.lastVerifiedToken = null;
    this.lastVerifiedTimestamp = 0;
    this.inFlightPromise = null;
    localStorage.removeItem('attendx_token');
    localStorage.removeItem('attendx_user');
  }

  async bootstrapSession(options = {}) {
    const token = localStorage.getItem('attendx_token');
    const cachedUser = localStorage.getItem('attendx_user') ? JSON.parse(localStorage.getItem('attendx_user')) : null;

    if (!token || !cachedUser) {
      if (token || cachedUser) this.invalidateSessionCache();
      return null;
    }

    if (isTokenExpired(token)) {
      this.invalidateSessionCache();
      return null;
    }

    // Freshness check
    if (!options.force && this.lastVerifiedToken === token && (Date.now() - this.lastVerifiedTimestamp < this.freshnessTtlMs)) {
      return cachedUser;
    }

    // Deduplication
    if (this.inFlightPromise) {
      return this.inFlightPromise;
    }

    this.inFlightPromise = (async () => {
      this.apiCallsCount++;
      try {
        if (this.mockApiError) {
          throw this.mockApiError;
        }
        const user = this.mockApiResponse;
        this.markSessionFresh(token, user);
        return user;
      } catch (err) {
        const status = err.response?.status;
        if (status === 401 || status === 403) {
          this.invalidateSessionCache();
          return null;
        }
        // Resilient fallback: retain cached user and token!
        return cachedUser;
      } finally {
        this.inFlightPromise = null;
      }
    })();

    return this.inFlightPromise;
  }
}

function isPublicAuthEndpoint(url) {
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

function isPublicRoute(pathname) {
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

async function runAllTests() {
  console.log('='.repeat(70));
  console.log('ATTENDX FRONTEND AUTH BOOTSTRAP UNIT VERIFICATION');
  console.log('='.repeat(70));

  let passed = 0;
  let total = 0;
  async function test(name, fn) {
    total++;
    try {
      await fn();
      passed++;
      console.log(`[PASS] ${name}`);
    } catch (err) {
      console.error(`[FAIL] ${name}: ${err.message}`);
      throw err;
    }
  }

  // Section 1
  await test('parseJwtPayload parses valid JWT correctly', () => {
    const expFuture = Math.floor(Date.now() / 1000) + 3600;
    const token = createMockJwt({ sub: 'user-123', role: 'admin', exp: expFuture });
    const payload = parseJwtPayload(token);
    assert.strictEqual(payload.sub, 'user-123');
    assert.strictEqual(payload.role, 'admin');
    assert.strictEqual(payload.exp, expFuture);
  });

  await test('parseJwtPayload returns null on malformed token', () => {
    assert.strictEqual(parseJwtPayload('not-a-token'), null);
    assert.strictEqual(parseJwtPayload('a.b'), null);
    assert.strictEqual(parseJwtPayload(''), null);
  });

  await test('isTokenExpired detects valid future token as NOT expired', () => {
    const expFuture = Math.floor(Date.now() / 1000) + 3600;
    const token = createMockJwt({ sub: 'user-123', exp: expFuture });
    assert.strictEqual(isTokenExpired(token), false);
  });

  await test('isTokenExpired detects past token as EXPIRED', () => {
    const expPast = Math.floor(Date.now() / 1000) - 3600;
    const token = createMockJwt({ sub: 'user-123', exp: expPast });
    assert.strictEqual(isTokenExpired(token), true);
  });

  await test('isTokenExpired treats malformed token as EXPIRED (safe fallback)', () => {
    assert.strictEqual(isTokenExpired('gibberish'), true);
    assert.strictEqual(isTokenExpired(''), true);
  });

  // Section 2
  console.log('\n--- Bootstrap Service Behavior & Resilience ---');

  await test('Bootstrap returns null without making API calls when no token is present', async () => {
    storage.clear();
    const service = new MockAuthBootstrapService();
    const res = await service.bootstrapSession();
    assert.strictEqual(res, null);
    assert.strictEqual(service.apiCallsCount, 0);
  });

  await test('Bootstrap clears expired token in 0 ms without making network call', async () => {
    storage.clear();
    const expPast = Math.floor(Date.now() / 1000) - 100;
    const expiredTok = createMockJwt({ sub: 'user-old', exp: expPast });
    localStorage.setItem('attendx_token', expiredTok);
    localStorage.setItem('attendx_user', JSON.stringify({ id: 'user-old', role: 'student' }));

    const service = new MockAuthBootstrapService();
    const res = await service.bootstrapSession();
    assert.strictEqual(res, null);
    assert.strictEqual(service.apiCallsCount, 0);
    assert.strictEqual(localStorage.getItem('attendx_token'), null);
  });

  await test('Fresh session (after login) returns cached user with 0 API calls', async () => {
    storage.clear();
    const expFuture = Math.floor(Date.now() / 1000) + 3600;
    const token = createMockJwt({ sub: 'user-fresh', role: 'admin', exp: expFuture });
    const user = { id: 'user-fresh', role: 'admin', full_name: 'Admin User' };

    const service = new MockAuthBootstrapService();
    service.markSessionFresh(token, user);

    const res = await service.bootstrapSession();
    assert.deepStrictEqual(res, user);
    assert.strictEqual(service.apiCallsCount, 0, 'Must NOT trigger /api/auth/me right after login');
  });

  await test('Concurrent bootstrap calls are deduplicated into a single API request', async () => {
    storage.clear();
    const expFuture = Math.floor(Date.now() / 1000) + 3600;
    const token = createMockJwt({ sub: 'user-dedup', role: 'lecturer', exp: expFuture });
    const user = { id: 'user-dedup', role: 'lecturer', full_name: 'Dr. Alan' };
    localStorage.setItem('attendx_token', token);
    localStorage.setItem('attendx_user', JSON.stringify(user));

    const service = new MockAuthBootstrapService();
    service.mockApiResponse = { ...user, full_name: 'Dr. Alan Turing (Server Verified)' };

    const results = await Promise.all([
      service.bootstrapSession({ force: true }),
      service.bootstrapSession({ force: true }),
      service.bootstrapSession({ force: true }),
      service.bootstrapSession({ force: true }),
      service.bootstrapSession({ force: true }),
    ]);

    assert.strictEqual(service.apiCallsCount, 1, 'Concurrent bootstrap requests must be deduplicated to exactly 1 call');
    results.forEach((r) => {
      assert.strictEqual(r.full_name, 'Dr. Alan Turing (Server Verified)');
    });
  });

  await test('Session resilience: 502/503 cold start does NOT log the user out', async () => {
    storage.clear();
    const expFuture = Math.floor(Date.now() / 1000) + 3600;
    const token = createMockJwt({ sub: 'user-resilient', role: 'student', exp: expFuture });
    const cachedUser = { id: 'user-resilient', role: 'student', full_name: 'John Doe' };
    localStorage.setItem('attendx_token', token);
    localStorage.setItem('attendx_user', JSON.stringify(cachedUser));

    const service = new MockAuthBootstrapService();
    service.mockApiError = { response: { status: 502, data: 'Bad Gateway' } };

    const res = await service.bootstrapSession({ force: true });
    assert.deepStrictEqual(res, cachedUser, 'Must retain cached user during 502/503 backend cold starts');
    assert.strictEqual(localStorage.getItem('attendx_token'), token, 'Token must not be deleted on 502/503');
  });

  await test('Session resilience: network timeout does NOT log the user out', async () => {
    storage.clear();
    const expFuture = Math.floor(Date.now() / 1000) + 3600;
    const token = createMockJwt({ sub: 'user-timeout', role: 'student', exp: expFuture });
    const cachedUser = { id: 'user-timeout', role: 'student', full_name: 'Jane Doe' };
    localStorage.setItem('attendx_token', token);
    localStorage.setItem('attendx_user', JSON.stringify(cachedUser));

    const service = new MockAuthBootstrapService();
    service.mockApiError = { code: 'ECONNABORTED', message: 'timeout of 20000ms exceeded' };

    const res = await service.bootstrapSession({ force: true });
    assert.deepStrictEqual(res, cachedUser, 'Must retain cached user during connection timeout');
    assert.strictEqual(localStorage.getItem('attendx_token'), token);
  });

  await test('Unrecoverable 401 Unauthorized clears session and logs out', async () => {
    storage.clear();
    const expFuture = Math.floor(Date.now() / 1000) + 3600;
    const token = createMockJwt({ sub: 'user-revoked', role: 'student', exp: expFuture });
    const cachedUser = { id: 'user-revoked', role: 'student' };
    localStorage.setItem('attendx_token', token);
    localStorage.setItem('attendx_user', JSON.stringify(cachedUser));

    const service = new MockAuthBootstrapService();
    service.mockApiError = { response: { status: 401, data: { detail: 'Invalid or expired token' } } };

    const res = await service.bootstrapSession({ force: true });
    assert.strictEqual(res, null);
    assert.strictEqual(localStorage.getItem('attendx_token'), null);
    assert.strictEqual(localStorage.getItem('attendx_user'), null);
  });

  await test('Disabled account (403 Forbidden) clears session and logs out', async () => {
    storage.clear();
    const expFuture = Math.floor(Date.now() / 1000) + 3600;
    const token = createMockJwt({ sub: 'user-disabled', role: 'student', exp: expFuture });
    localStorage.setItem('attendx_token', token);
    localStorage.setItem('attendx_user', JSON.stringify({ id: 'user-disabled', role: 'student' }));

    const service = new MockAuthBootstrapService();
    service.mockApiError = { response: { status: 403, data: { detail: 'Account is disabled.' } } };

    const res = await service.bootstrapSession({ force: true });
    assert.strictEqual(res, null);
    assert.strictEqual(localStorage.getItem('attendx_token'), null);
  });

  // Section 3
  console.log('\n--- Endpoint & Route Classification ---');

  await test('isPublicAuthEndpoint correctly identifies public endpoints', () => {
    assert.strictEqual(isPublicAuthEndpoint('/api/auth/login'), true);
    assert.strictEqual(isPublicAuthEndpoint('/api/auth/activate'), true);
    assert.strictEqual(isPublicAuthEndpoint('/api/auth/forgot-password'), true);
    assert.strictEqual(isPublicAuthEndpoint('/api/auth/verify-reset-token?token=123'), true);
    assert.strictEqual(isPublicAuthEndpoint('/api/auth/me'), false);
    assert.strictEqual(isPublicAuthEndpoint('/api/admin/dashboard'), false);
    assert.strictEqual(isPublicAuthEndpoint('/api/dashboard/student'), false);
    assert.strictEqual(isPublicAuthEndpoint('/api/lecturer/attendance'), false);
  });

  await test('isPublicRoute correctly identifies public pages', () => {
    assert.strictEqual(isPublicRoute('/'), true);
    assert.strictEqual(isPublicRoute('/login'), true);
    assert.strictEqual(isPublicRoute('/register'), true);
    assert.strictEqual(isPublicRoute('/activate-account'), true);
    assert.strictEqual(isPublicRoute('/reset-password'), true);
    assert.strictEqual(isPublicRoute('/admin/dashboard'), false);
    assert.strictEqual(isPublicRoute('/lecturer/dashboard'), false);
    assert.strictEqual(isPublicRoute('/dashboard'), false);
    assert.strictEqual(isPublicRoute('/my-subjects'), false);
  });

  console.log('\n' + '='.repeat(70));
  console.log(`ALL FRONTEND AUTH BOOTSTRAP UNIT TESTS PASSED: ${passed}/${total}`);
  console.log('='.repeat(70));
}

runAllTests().catch((e) => {
  console.error(e);
  process.exit(1);
});
