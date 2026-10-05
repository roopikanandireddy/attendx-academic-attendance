import React, { useState, useEffect } from 'react';
import { useSearchParams, Link, useNavigate } from 'react-router-dom';
import { GraduationCap, Lock, Eye, EyeOff, CheckCircle2, AlertTriangle, ArrowRight, Loader2, KeyRound } from 'lucide-react';
import api from '../services/api';
import toast from 'react-hot-toast';

export default function ResetPasswordPage() {
  const [searchParams] = useSearchParams();
  const navigate = useNavigate();
  const token = searchParams.get('token') || '';

  const [verifying, setVerifying] = useState(true);
  const [tokenError, setTokenError] = useState<string | null>(null);
  const [accountEmail, setAccountEmail] = useState<string>('');

  const [password, setPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [showPassword, setShowPassword] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const [isSuccess, setIsSuccess] = useState(false);
  const [errors, setErrors] = useState<Record<string, string>>({});

  useEffect(() => {
    if (!token) {
      setVerifying(false);
      setTokenError('No password reset token provided. Please use the complete reset link sent to your email.');
      return;
    }

    const verify = async () => {
      try {
        setVerifying(true);
        const res = await api.get(`/api/auth/verify-reset-token?token=${encodeURIComponent(token)}`);
        setAccountEmail(res.data.email || '');
        setTokenError(null);
      } catch (err: any) {
        const msg = err.response?.data?.detail || 'Reset link is invalid, expired, or has already been used.';
        setTokenError(msg);
      } finally {
        setVerifying(false);
      }
    };

    verify();
  }, [token]);

  const validate = () => {
    const errs: Record<string, string> = {};
    if (!password) {
      errs.password = 'New password is required';
    } else if (password.length < 6) {
      errs.password = 'Password must be at least 6 characters';
    }
    if (password !== confirmPassword) {
      errs.confirmPassword = 'Passwords do not match';
    }
    setErrors(errs);
    return Object.keys(errs).length === 0;
  };

  const handleReset = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!validate()) return;

    setSubmitting(true);
    try {
      await api.post('/api/auth/reset-password', {
        token,
        password,
      });
      setIsSuccess(true);
      toast.success('Password reset successfully!');
    } catch (err: any) {
      const msg = err.response?.data?.detail || 'Failed to reset password. Link may have expired.';
      toast.error(msg);
      if (err.response?.status === 400) {
        setTokenError(msg);
      }
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-primary-50 via-white to-primary-50 flex items-center justify-center p-4">
      <div className="w-full max-w-md">
        <div className="text-center mb-8">
          <div className="w-14 h-14 rounded-2xl bg-gradient-to-br from-primary-600 to-primary-700 flex items-center justify-center mx-auto mb-4 shadow-lg shadow-primary-200 text-white">
            <GraduationCap className="w-7 h-7" aria-hidden="true" />
          </div>
          <h1 className="text-2xl font-bold text-surface-900">AttendX</h1>
          <p className="text-xs uppercase tracking-widest text-primary-700 font-semibold mt-0.5">
            Academic Attendance Management System
          </p>
        </div>

        <div className="card shadow-xl shadow-surface-200/50">
          {verifying ? (
            <div className="py-12 text-center space-y-3">
              <Loader2 className="w-8 h-8 text-primary-600 animate-spin mx-auto" />
              <p className="text-sm font-medium text-surface-600">Verifying reset token...</p>
              <p className="text-xs text-surface-400">Validating single-use security token</p>
            </div>
          ) : tokenError ? (
            <div className="text-center py-6 space-y-4">
              <div className="w-12 h-12 rounded-full bg-danger/10 text-danger flex items-center justify-center mx-auto">
                <AlertTriangle className="w-6 h-6" />
              </div>
              <div>
                <h2 className="text-lg font-bold text-surface-900">Reset Link Invalid</h2>
                <p className="text-sm text-surface-500 mt-2 px-2 leading-relaxed">{tokenError}</p>
              </div>
              <div className="pt-2 border-t border-surface-100 flex flex-col gap-2">
                <Link
                  to="/forgot-password"
                  className="btn btn-primary w-full py-2.5 text-sm justify-center"
                >
                  Request a New Link
                </Link>
                <Link
                  to="/login"
                  className="btn btn-secondary w-full py-2.5 text-sm justify-center"
                >
                  Return to Sign In
                </Link>
              </div>
            </div>
          ) : isSuccess ? (
            <div className="text-center py-6 space-y-4">
              <div className="w-12 h-12 rounded-full bg-success/10 text-success flex items-center justify-center mx-auto">
                <CheckCircle2 className="w-7 h-7" />
              </div>
              <div>
                <h2 className="text-xl font-bold text-surface-900">Password Reset Complete!</h2>
                <p className="text-sm text-surface-500 mt-2 px-2">
                  Your new password has been saved. You can now sign in with your updated credentials.
                </p>
              </div>
              <button
                type="button"
                onClick={() => navigate('/login')}
                className="btn btn-primary w-full py-2.5 justify-center gap-2 mt-4"
              >
                <span>Proceed to Sign In</span>
                <ArrowRight className="w-4 h-4" />
              </button>
            </div>
          ) : (
            <div>
              <div className="mb-6 text-center">
                <h2 className="text-xl font-bold text-surface-900">Set New Password</h2>
                {accountEmail && (
                  <p className="text-xs text-surface-500 mt-1">
                    Resetting password for: <span className="font-semibold text-surface-800">{accountEmail}</span>
                  </p>
                )}
              </div>

              <form onSubmit={handleReset} className="space-y-4">
                <div>
                  <label htmlFor="reset-new-password" className="label">
                    New Password <span className="text-danger">*</span>
                  </label>
                  <div className="relative">
                    <Lock className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-surface-400" />
                    <input
                      id="reset-new-password"
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
                  <label htmlFor="reset-confirm-password" className="label">
                    Confirm New Password <span className="text-danger">*</span>
                  </label>
                  <div className="relative">
                    <Lock className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-surface-400" />
                    <input
                      id="reset-confirm-password"
                      type={showPassword ? 'text' : 'password'}
                      value={confirmPassword}
                      onChange={(e) => setConfirmPassword(e.target.value)}
                      className={`input pl-10 ${errors.confirmPassword ? 'input-error' : ''}`}
                      placeholder="Re-enter new password"
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
                        <span>Updating Password...</span>
                      </>
                    ) : (
                      <>
                        <KeyRound className="w-4 h-4" />
                        <span>Reset Password</span>
                      </>
                    )}
                  </button>
                </div>
              </form>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
