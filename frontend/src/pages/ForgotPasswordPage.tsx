import React, { useState } from 'react';
import { Link } from 'react-router-dom';
import { GraduationCap, Mail, ArrowLeft, Loader2, CheckCircle2, KeyRound } from 'lucide-react';
import api from '../services/api';
import toast from 'react-hot-toast';

export default function ForgotPasswordPage() {
  const [email, setEmail] = useState('');
  const [loading, setLoading] = useState(false);
  const [submitted, setSubmitted] = useState(false);
  const [error, setError] = useState('');

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!email.trim() || !/\S+@\S+\.\S+/.test(email)) {
      setError('Please enter a valid email address');
      return;
    }
    setError('');
    setLoading(true);
    try {
      await api.post('/api/auth/forgot-password', { email: email.trim().toLowerCase() });
      setSubmitted(true);
      toast.success('Password reset request submitted');
    } catch (err: any) {
      toast.error('Unable to process request. Please try again later.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-primary-50 via-white to-primary-50 flex items-center justify-center p-4">
      <div className="w-full max-w-md">
        <div className="mb-4">
          <Link
            to="/login"
            className="inline-flex items-center gap-1.5 text-xs font-medium text-surface-500 hover:text-surface-800 transition-colors"
          >
            <ArrowLeft className="w-3.5 h-3.5" />
            <span>Back to Sign In</span>
          </Link>
        </div>

        <div className="text-center mb-8">
          <div className="w-14 h-14 rounded-2xl bg-gradient-to-br from-primary-600 to-primary-700 flex items-center justify-center mx-auto mb-4 shadow-lg shadow-primary-200 text-white">
            <GraduationCap className="w-7 h-7" aria-hidden="true" />
          </div>
          <h1 className="text-2xl font-bold text-surface-900">Reset Password</h1>
          <p className="text-surface-500 text-sm mt-1">
            Enter your email to receive a secure password reset link
          </p>
        </div>

        <div className="card shadow-xl shadow-surface-200/50">
          {submitted ? (
            <div className="text-center py-6 space-y-4">
              <div className="w-12 h-12 rounded-full bg-success/10 text-success flex items-center justify-center mx-auto">
                <CheckCircle2 className="w-7 h-7" />
              </div>
              <div>
                <h2 className="text-lg font-bold text-surface-900">Check Your Email</h2>
                <p className="text-sm text-surface-500 mt-2 leading-relaxed">
                  If an account exists with <span className="font-semibold text-surface-800">{email}</span>, a secure one-time password reset link has been sent.
                </p>
              </div>
              <div className="p-3 bg-surface-50 rounded-lg border border-surface-200/60 text-xs text-surface-500 text-left">
                <p>• The reset link expires in 2 hours.</p>
                <p>• If you don't receive an email, please check your spam folder or contact your administrator.</p>
              </div>
              <div className="pt-2">
                <Link to="/login" className="btn btn-primary w-full py-2.5 justify-center">
                  Return to Sign In
                </Link>
              </div>
            </div>
          ) : (
            <form onSubmit={handleSubmit} className="space-y-4">
              <div>
                <label htmlFor="reset-email" className="label">
                  Institutional / Registered Email
                </label>
                <div className="relative">
                  <Mail className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-surface-400" />
                  <input
                    id="reset-email"
                    type="email"
                    value={email}
                    onChange={(e) => setEmail(e.target.value)}
                    className={`input pl-10 ${error ? 'input-error' : ''}`}
                    placeholder="e.g. rahul.kumar@university.edu"
                    autoComplete="email"
                    required
                  />
                </div>
                {error && <p className="text-xs text-danger mt-1">{error}</p>}
              </div>

              <button
                type="submit"
                className="btn btn-primary w-full btn-lg justify-center gap-2"
                disabled={loading}
              >
                {loading ? (
                  <>
                    <Loader2 className="w-4 h-4 animate-spin" />
                    <span>Sending Instructions...</span>
                  </>
                ) : (
                  <>
                    <KeyRound className="w-4 h-4" />
                    <span>Send Reset Link</span>
                  </>
                )}
              </button>
            </form>
          )}
        </div>
      </div>
    </div>
  );
}
