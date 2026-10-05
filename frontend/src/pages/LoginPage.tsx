import { useState } from 'react';
import { Link, Navigate, useSearchParams } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { GraduationCap, BookOpen, ShieldCheck, Mail, Lock, Eye, EyeOff, Loader2, ArrowLeft } from 'lucide-react';
import toast from 'react-hot-toast';

export default function LoginPage() {
  const { user, login, logout } = useAuth();
  const [searchParams] = useSearchParams();
  const roleParam = searchParams.get('role')?.toLowerCase();

  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [showPassword, setShowPassword] = useState(false);
  const [loading, setLoading] = useState(false);
  const [errors, setErrors] = useState<Record<string, string>>({});

  // Only redirect if user's existing session already matches the requested role (or if no specific role was requested)
  if (user && (!roleParam || user.role === roleParam)) {
    if (user.role === 'admin') {
      return <Navigate to="/admin/dashboard" replace />;
    }
    if (user.role === 'lecturer') {
      return <Navigate to="/lecturer/dashboard" replace />;
    }
    return <Navigate to="/dashboard" replace />;
  }

  const roleMeta = {
    student: {
      badge: 'Student Portal',
      title: 'Student Sign In',
      subtitle: 'Sign in to access your attendance, enrolled subjects and profile',
      badgeClass: 'bg-blue-50 text-blue-700 border-blue-200/60',
      icon: GraduationCap,
      iconGradient: 'from-blue-600 to-blue-700',
    },
    lecturer: {
      badge: 'Lecturer Portal',
      title: 'Lecturer Sign In',
      subtitle: 'Sign in to manage assigned subjects, mark attendance and view rosters',
      badgeClass: 'bg-indigo-50 text-indigo-700 border-indigo-200/60',
      icon: BookOpen,
      iconGradient: 'from-indigo-600 to-indigo-700',
    },
    admin: {
      badge: 'Admin Portal',
      title: 'Admin Sign In',
      subtitle: 'Institutional credentials required for academic administration',
      badgeClass: 'bg-purple-50 text-purple-700 border-purple-200/60',
      icon: ShieldCheck,
      iconGradient: 'from-slate-800 to-slate-900',
    },
  }[roleParam as 'student' | 'lecturer' | 'admin'] || {
    badge: null,
    title: 'Welcome back',
    subtitle: 'Sign in to your AttendX account',
    badgeClass: '',
    icon: GraduationCap,
    iconGradient: 'from-primary-600 to-primary-700',
  };

  const HeaderIcon = roleMeta.icon;

  const validate = () => {
    const errs: Record<string, string> = {};
    if (!email.trim()) errs.email = 'Email is required';
    else if (!/\S+@\S+\.\S+/.test(email)) errs.email = 'Invalid email format';
    if (!password) errs.password = 'Password is required';
    setErrors(errs);
    return Object.keys(errs).length === 0;
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!validate()) return;

    setLoading(true);
    try {
      await login(email, password);
      toast.success('Welcome back!');
    } catch (err: any) {
      const detail = err.response?.data?.detail;
      let msg = 'Invalid email or password';
      if (typeof detail === 'string') {
        msg = detail;
      } else if (Array.isArray(detail)) {
        msg = detail.map((d: any) => d.msg || JSON.stringify(d)).join(', ');
      }
      toast.error(msg);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-primary-50 via-white to-primary-50 flex items-center justify-center p-4">
      <div className="w-full max-w-md">
        {/* Back to Role Selection */}
        <div className="mb-4">
          <Link
            to="/"
            className="inline-flex items-center gap-1.5 text-xs font-medium text-surface-500 hover:text-surface-800 transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary-500 rounded px-1 py-0.5"
            aria-label="Back to role selection"
          >
            <ArrowLeft className="w-3.5 h-3.5" aria-hidden="true" />
            <span>Back to role selection</span>
          </Link>
        </div>

        {/* Logo and Header */}
        <div className="text-center mb-8">
          {roleMeta.badge && (
            <div className="mb-3">
              <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-semibold uppercase tracking-wider border ${roleMeta.badgeClass}`}>
                {roleMeta.badge}
              </span>
            </div>
          )}
          <div className={`w-14 h-14 rounded-2xl bg-gradient-to-br ${roleMeta.iconGradient} flex items-center justify-center mx-auto mb-4 shadow-lg shadow-surface-200/50 text-white`}>
            <HeaderIcon className="w-7 h-7" aria-hidden="true" />
          </div>
          <h1 className="text-2xl font-bold text-surface-900">{roleMeta.title}</h1>
          <p className="text-surface-500 text-sm mt-1">{roleMeta.subtitle}</p>
        </div>

        {/* Form Card */}
        <div className="card shadow-xl shadow-surface-200/50">
          {/* Active Session Switch Notice */}
          {user && roleParam && user.role !== roleParam && (
            <div className="mb-4 p-3 bg-amber-50 border border-amber-200 rounded-xl text-xs text-amber-900 flex items-center justify-between">
              <div>
                <p className="font-semibold">Signed in as {user.role.toUpperCase()}</p>
                <p className="text-amber-700 text-[11px]">{user.email}</p>
              </div>
              <button
                type="button"
                onClick={() => logout()}
                className="text-xs font-semibold text-danger hover:underline px-2 py-1"
              >
                Sign Out
              </button>
            </div>
          )}

          <form onSubmit={handleSubmit} className="space-y-4">
            <div>
              <label htmlFor="email" className="label">Email</label>
              <div className="relative">
                <Mail className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-surface-400" />
                <input
                  id="email"
                  type="email"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  className={`input pl-10 ${errors.email ? 'input-error' : ''}`}
                  placeholder="you@example.com"
                  autoComplete="email"
                />
              </div>
              {errors.email && <p className="text-xs text-danger mt-1">{errors.email}</p>}
            </div>

            <div>
              <div className="flex items-center justify-between">
                <label htmlFor="password" className="label mb-0">Password</label>
                <Link
                  to="/forgot-password"
                  className="text-xs text-primary-600 hover:text-primary-700 font-medium"
                >
                  Forgot password?
                </Link>
              </div>
              <div className="relative mt-1">
                <Lock className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-surface-400" />
                <input
                  id="password"
                  type={showPassword ? 'text' : 'password'}
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  className={`input pl-10 pr-10 ${errors.password ? 'input-error' : ''}`}
                  placeholder="Enter your password"
                  autoComplete="current-password"
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

            <button type="submit" className="btn btn-primary w-full btn-lg" disabled={loading}>
              {loading ? <Loader2 className="w-4 h-4 animate-spin" /> : 'Sign In'}
            </button>
          </form>

          <div className="mt-6 pt-5 border-t border-surface-100 text-center">
            <p className="text-xs text-surface-500 leading-relaxed">
              Student and Faculty accounts are created by your institution administrator.
            </p>
            <p className="text-[11px] text-surface-400 mt-1">
              Received an invitation email?{' '}
              <Link to="/activate-account" className="text-primary-600 font-medium hover:underline">
                Activate your account
              </Link>
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}
