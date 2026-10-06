import React, { useState, useEffect } from 'react';
import { useSearchParams, Link, useNavigate } from 'react-router-dom';
import { GraduationCap, Lock, Eye, EyeOff, CheckCircle2, AlertTriangle, ArrowRight, Loader2, ShieldCheck } from 'lucide-react';
import api, { isRequestCancelled } from '../services/api';
import toast from 'react-hot-toast';

export default function AccountActivationPage() {
  const [searchParams] = useSearchParams();
  const navigate = useNavigate();
  const token = searchParams.get('token') || '';

  const [verifying, setVerifying] = useState(true);
  const [tokenError, setTokenError] = useState<string | null>(null);
  const [accountInfo, setAccountInfo] = useState<{
    email: string;
    full_name: string;
    role: string;
  } | null>(null);

  const [password, setPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [showPassword, setShowPassword] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const [isSuccess, setIsSuccess] = useState(false);
  const [errors, setErrors] = useState<Record<string, string>>({});

  useEffect(() => {
    if (!token) {
      setVerifying(false);
      setTokenError('No activation token provided. Please use the complete activation link from your email.');
      return;
    }

    const controller = new AbortController();

    const verify = async () => {
      try {
        setVerifying(true);
        const res = await api.get(`/api/auth/verify-activation-token?token=${encodeURIComponent(token)}`, {
          signal: controller.signal,
        });
        setAccountInfo({
          email: res.data.email || '',
          full_name: res.data.full_name || '',
          role: res.data.role || 'user',
        });
        setTokenError(null);
      } catch (err: any) {
        if (isRequestCancelled(err)) return;
        const msg = err.response?.data?.detail || 'Activation link is invalid, expired, or has already been used.';
        setTokenError(msg);
      } finally {
        setVerifying(false);
      }
    };

    verify();

    return () => {
      controller.abort();
    };
  }, [token]);

  const validate = () => {
    const errs: Record<string, string> = {};
    if (!password) {
      errs.password = 'Password is required';
    } else if (password.length < 6) {
      errs.password = 'Password must be at least 6 characters';
    }
    if (password !== confirmPassword) {
      errs.confirmPassword = 'Passwords do not match';
    }
    setErrors(errs);
    return Object.keys(errs).length === 0;
  };

  const handleActivate = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!validate()) return;

    setSubmitting(true);
    try {
      await api.post('/api/auth/activate', {
        token,
        password,
      });
      setIsSuccess(true);
      toast.success('Account activated successfully!');
    } catch (err: any) {
      const msg = err.response?.data?.detail || 'Failed to activate account. The link may have expired.';
      toast.error(msg);
      if (err.response?.status === 400) {
        setTokenError(msg);
      }
    } finally {
      setSubmitting(false);
    }
  };

  const roleLabel = accountInfo?.role ? accountInfo.role.charAt(0).toUpperCase() + accountInfo.role.slice(1) : 'Account';

  return (
    <div className="min-h-screen bg-gradient-to-br from-primary-50 via-white to-primary-50 flex items-center justify-center p-4">
      <div className="w-full max-w-md">
        {/* Brand Header */}
        <div className="text-center mb-8">
          <div className="w-14 h-14 rounded-2xl bg-gradient-to-br from-primary-600 to-primary-700 flex items-center justify-center mx-auto mb-4 shadow-lg shadow-primary-200 text-white">
            <GraduationCap className="w-7 h-7" aria-hidden="true" />
          </div>
          <h1 className="text-2xl font-bold text-surface-900">AttendX</h1>
          <p className="text-xs uppercase tracking-widest text-primary-700 font-semibold mt-0.5">
            Academic Attendance Management System
          </p>
        </div>

        {/* Card Content */}
        <div className="card shadow-xl shadow-surface-200/50">
          {verifying ? (
            <div className="py-12 text-center space-y-3">
              <Loader2 className="w-8 h-8 text-primary-600 animate-spin mx-auto" />
              <p className="text-sm font-medium text-surface-600">Verifying your activation link...</p>
              <p className="text-xs text-surface-400">Validating single-use security token</p>
            </div>
          ) : tokenError ? (
            <div className="text-center py-6 space-y-4">
              <div className="w-12 h-12 rounded-full bg-danger/10 text-danger flex items-center justify-center mx-auto">
                <AlertTriangle className="w-6 h-6" />
              </div>
              <div>
                <h2 className="text-lg font-bold text-surface-900">Activation Link Invalid</h2>
                <p className="text-sm text-surface-500 mt-2 px-2 leading-relaxed">{tokenError}</p>
              </div>
              <div className="pt-2 border-t border-surface-100 flex flex-col gap-2">
                <Link
                  to="/login"
                  className="btn btn-primary w-full py-2.5 text-sm justify-center"
                >
                  Return to Sign In
                </Link>
                <Link
                  to="/"
                  className="btn btn-secondary w-full py-2.5 text-sm justify-center"
                >
                  Back to Role Selection
                </Link>
              </div>
            </div>
          ) : isSuccess ? (
            <div className="text-center py-6 space-y-4">
              <div className="w-12 h-12 rounded-full bg-success/10 text-success flex items-center justify-center mx-auto">
                <CheckCircle2 className="w-7 h-7" />
              </div>
              <div>
                <h2 className="text-xl font-bold text-surface-900">Account Activated!</h2>
                <p className="text-sm text-surface-500 mt-2 px-2">
                  Your password has been created and your {roleLabel} account is now active.
                </p>
              </div>
              <div className="p-3 bg-surface-50 rounded-lg border border-surface-200/60 text-xs text-surface-600 text-left space-y-1">
                <div className="flex justify-between">
                  <span className="text-surface-400">Full Name:</span>
                  <span className="font-semibold text-surface-800">{accountInfo?.full_name}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-surface-400">Email:</span>
                  <span className="font-semibold text-surface-800">{accountInfo?.email}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-surface-400">Role:</span>
                  <span className="font-semibold text-surface-800">{roleLabel}</span>
                </div>
              </div>
              <button
                type="button"
                onClick={() => navigate(`/login?role=${accountInfo?.role || 'student'}`)}
                className="btn btn-primary w-full py-2.5 justify-center gap-2 mt-4"
              >
                <span>Continue to Login</span>
                <ArrowRight className="w-4 h-4" />
              </button>
            </div>
          ) : (
            <div>
              <div className="mb-6 text-center">
                <h2 className="text-xl font-bold text-surface-900">Activate Your Account</h2>
                <p className="text-xs text-surface-500 mt-1">
                  Your account was provisioned by your institution administrator.
                </p>
              </div>

              {accountInfo && (
                <div className="mb-6 p-3.5 bg-primary-50/50 rounded-xl border border-primary-100/80 flex items-center gap-3">
                  <div className="w-10 h-10 rounded-lg bg-primary-600 text-white flex items-center justify-center font-bold text-sm shrink-0">
                    {accountInfo.full_name ? accountInfo.full_name.charAt(0).toUpperCase() : 'U'}
                  </div>
                  <div className="min-w-0 flex-1">
                    <p className="text-xs font-semibold text-surface-900 truncate">{accountInfo.full_name}</p>
                    <p className="text-xs text-surface-500 truncate">{accountInfo.email}</p>
                    <span className="inline-block mt-0.5 px-2 py-0.2 text-[10px] font-medium uppercase tracking-wider bg-white text-primary-700 rounded border border-primary-200">
                      {roleLabel}
                    </span>
                  </div>
                </div>
              )}

              <form onSubmit={handleActivate} className="space-y-4">
                <div>
                  <label htmlFor="new-password" className="label">
                    Create Password <span className="text-danger">*</span>
                  </label>
                  <div className="relative">
                    <Lock className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-surface-400" />
                    <input
                      id="new-password"
                      type={showPassword ? 'text' : 'password'}
                      value={password}
                      onChange={(e) => setPassword(e.target.value)}
                      className={`input pl-10 pr-10 ${errors.password ? 'input-error' : ''}`}
                      placeholder="Minimum 6 characters"
                      autoComplete="new-password"
                    />
                    <button
                      type="button"
                      onClick={() => setShowPassword(!showPassword)}
                      className="absolute right-3 top-1/2 -translate-y-1/2 text-surface-400 hover:text-surface-600"
                      aria-label={showPassword ? 'Hide password' : 'Show password'}
                    >
                      {showPassword ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                    </button>
                  </div>
                  {errors.password && <p className="text-xs text-danger mt-1">{errors.password}</p>}
                </div>

                <div>
                  <label htmlFor="confirm-password" className="label">
                    Confirm Password <span className="text-danger">*</span>
                  </label>
                  <div className="relative">
                    <Lock className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-surface-400" />
                    <input
                      id="confirm-password"
                      type={showPassword ? 'text' : 'password'}
                      value={confirmPassword}
                      onChange={(e) => setConfirmPassword(e.target.value)}
                      className={`input pl-10 ${errors.confirmPassword ? 'input-error' : ''}`}
                      placeholder="Re-enter password"
                      autoComplete="new-password"
                    />
                  </div>
                  {errors.confirmPassword && (
                    <p className="text-xs text-danger mt-1">{errors.confirmPassword}</p>
                  )}
                </div>

                <div className="pt-2">
                  <button
                    type="submit"
                    className="btn btn-primary w-full btn-lg justify-center gap-2"
                    disabled={submitting}
                  >
                    {submitting ? (
                      <>
                        <Loader2 className="w-4 h-4 animate-spin" />
                        <span>Activating...</span>
                      </>
                    ) : (
                      <>
                        <ShieldCheck className="w-4 h-4" />
                        <span>Activate Account</span>
                      </>
                    )}
                  </button>
                </div>
              </form>

              <div className="mt-6 pt-4 border-t border-surface-100 text-center">
                <Link
                  to="/login"
                  className="text-xs font-medium text-surface-500 hover:text-surface-800 transition-colors"
                >
                  Already activated? Sign in
                </Link>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
