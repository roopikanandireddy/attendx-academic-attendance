import { Link, Navigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { GraduationCap, ShieldAlert, ArrowLeft, LogIn } from 'lucide-react';

export default function RegisterPage() {
  const { user } = useAuth();

  if (user) {
    return <Navigate to={user.role === 'admin' ? '/admin/dashboard' : user.role === 'lecturer' ? '/lecturer/dashboard' : '/dashboard'} replace />;
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-primary-50 via-white to-primary-50 flex items-center justify-center p-4">
      <div className="w-full max-w-md">
        {/* Navigation back */}
        <div className="mb-4">
          <Link
            to="/"
            className="inline-flex items-center gap-1.5 text-xs font-medium text-surface-500 hover:text-surface-800 transition-colors"
          >
            <ArrowLeft className="w-3.5 h-3.5" />
            <span>Back to Role Selection</span>
          </Link>
        </div>

        {/* Brand header */}
        <div className="text-center mb-8">
          <div className="w-14 h-14 rounded-2xl bg-gradient-to-br from-primary-600 to-primary-700 flex items-center justify-center mx-auto mb-4 shadow-lg shadow-primary-200 text-white">
            <GraduationCap className="w-7 h-7" aria-hidden="true" />
          </div>
          <h1 className="text-2xl font-bold text-surface-900">AttendX</h1>
          <p className="text-xs uppercase tracking-widest text-primary-700 font-semibold mt-0.5">
            Academic Attendance Management System
          </p>
        </div>

        {/* Institutional notice card */}
        <div className="card shadow-xl shadow-surface-200/50 text-center py-6 px-6 sm:px-8 space-y-6">
          <div className="w-14 h-14 rounded-full bg-amber-50 border border-amber-200 text-amber-600 flex items-center justify-center mx-auto">
            <ShieldAlert className="w-7 h-7" />
          </div>

          <div className="space-y-2">
            <h2 className="text-xl font-bold text-surface-900">
              Institutional Provisioning
            </h2>
            <p className="text-sm text-surface-600 leading-relaxed">
              Student and Lecturer accounts are created exclusively by your institution administrator.
            </p>
          </div>

          <div className="p-4 bg-surface-50 rounded-xl border border-surface-200/70 text-xs text-surface-500 text-left space-y-2">
            <p className="font-semibold text-surface-700">Account Activation Instructions:</p>
            <p>1. When an administrator creates your account, you will receive an activation email.</p>
            <p>2. Open the secure link in your email to set your initial password.</p>
            <p>3. Once activated, log in to access your portal.</p>
          </div>

          <div className="space-y-3 pt-2">
            <Link
              to="/login"
              className="btn btn-primary w-full py-2.5 justify-center gap-2"
            >
              <LogIn className="w-4 h-4" />
              <span>Back to Login</span>
            </Link>

            <Link
              to="/"
              className="btn btn-secondary w-full py-2.5 justify-center"
            >
              Select Role
            </Link>
          </div>
        </div>
      </div>
    </div>
  );
}
