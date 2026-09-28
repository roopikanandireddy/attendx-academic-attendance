import { useState } from 'react';
import { Link, Navigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { GraduationCap, Eye, EyeOff, Loader2 } from 'lucide-react';
import toast from 'react-hot-toast';

export default function RegisterPage() {
  const { user, register } = useAuth();
  const [form, setForm] = useState({
    full_name: '', email: '', password: '', confirmPassword: '',
    student_id: '', department: '', year: '', section: '',
  });
  const [showPassword, setShowPassword] = useState(false);
  const [loading, setLoading] = useState(false);
  const [errors, setErrors] = useState<Record<string, string>>({});

  if (user) {
    return <Navigate to={user.role === 'admin' ? '/admin/dashboard' : '/dashboard'} replace />;
  }

  const update = (field: string, value: string) => {
    setForm((prev) => ({ ...prev, [field]: value }));
    if (errors[field]) setErrors((prev) => ({ ...prev, [field]: '' }));
  };

  const validate = () => {
    const errs: Record<string, string> = {};
    if (!form.full_name.trim()) errs.full_name = 'Full name is required';
    if (!form.email.trim()) errs.email = 'Email is required';
    else if (!/\S+@\S+\.\S+/.test(form.email)) errs.email = 'Invalid email format';
    if (!form.password) errs.password = 'Password is required';
    else if (form.password.length < 6) errs.password = 'Password must be at least 6 characters';
    if (form.password !== form.confirmPassword) errs.confirmPassword = 'Passwords do not match';
    if (form.year && (parseInt(form.year) < 1 || parseInt(form.year) > 6)) errs.year = 'Year must be 1-6';
    setErrors(errs);
    return Object.keys(errs).length === 0;
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!validate()) return;

    setLoading(true);
    try {
      await register({
        full_name: form.full_name.trim(),
        email: form.email.trim(),
        password: form.password,
        student_id: form.student_id.trim() || undefined,
        department: form.department.trim() || undefined,
        year: form.year ? parseInt(form.year) : undefined,
        section: form.section.trim() || undefined,
      });
      toast.success('Account created successfully!');
    } catch (err: any) {
      const msg = err.response?.data?.detail || 'Registration failed';
      toast.error(msg);
    } finally {
      setLoading(false);
    }
  };

  const inputField = (
    id: string, label: string, value: string, type = 'text',
    placeholder = '', required = false
  ) => (
    <div>
      <label htmlFor={id} className="label">
        {label} {required && <span className="text-danger">*</span>}
      </label>
      <input
        id={id}
        type={type}
        value={value}
        onChange={(e) => update(id, e.target.value)}
        className={`input ${errors[id] ? 'input-error' : ''}`}
        placeholder={placeholder}
      />
      {errors[id] && <p className="text-xs text-danger mt-1">{errors[id]}</p>}
    </div>
  );

  return (
    <div className="min-h-screen bg-gradient-to-br from-primary-50 via-white to-primary-50 flex items-center justify-center p-4">
      <div className="w-full max-w-lg">
        <div className="text-center mb-8">
          <div className="w-14 h-14 rounded-2xl bg-gradient-to-br from-primary-600 to-primary-700 flex items-center justify-center mx-auto mb-4 shadow-lg shadow-primary-200">
            <GraduationCap className="w-7 h-7 text-white" />
          </div>
          <h1 className="text-2xl font-bold text-surface-900">Create your account</h1>
          <p className="text-surface-500 text-sm mt-1">Join AttendX to track your attendance</p>
        </div>

        <div className="card shadow-xl shadow-surface-200/50">
          <form onSubmit={handleSubmit} className="space-y-4">
            {inputField('full_name', 'Full Name', form.full_name, 'text', 'John Doe', true)}
            {inputField('email', 'Email', form.email, 'email', 'you@example.com', true)}

            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              <div>
                <label htmlFor="password" className="label">
                  Password <span className="text-danger">*</span>
                </label>
                <div className="relative">
                  <input
                    id="password"
                    type={showPassword ? 'text' : 'password'}
                    value={form.password}
                    onChange={(e) => update('password', e.target.value)}
                    className={`input pr-10 ${errors.password ? 'input-error' : ''}`}
                    placeholder="Min 6 characters"
                  />
                  <button
                    type="button"
                    onClick={() => setShowPassword(!showPassword)}
                    className="absolute right-3 top-1/2 -translate-y-1/2 text-surface-400"
                    aria-label={showPassword ? 'Hide password' : 'Show password'}
                  >
                    {showPassword ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                  </button>
                </div>
                {errors.password && <p className="text-xs text-danger mt-1">{errors.password}</p>}
              </div>
              <div>
                <label htmlFor="confirmPassword" className="label">
                  Confirm Password <span className="text-danger">*</span>
                </label>
                <input
                  id="confirmPassword"
                  type="password"
                  value={form.confirmPassword}
                  onChange={(e) => update('confirmPassword', e.target.value)}
                  className={`input ${errors.confirmPassword ? 'input-error' : ''}`}
                  placeholder="Re-enter password"
                />
                {errors.confirmPassword && <p className="text-xs text-danger mt-1">{errors.confirmPassword}</p>}
              </div>
            </div>

            <hr className="border-surface-100" />

            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              {inputField('student_id', 'Student ID', form.student_id, 'text', 'e.g. 2024CS001')}
              {inputField('department', 'Department', form.department, 'text', 'e.g. Computer Science')}
            </div>
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              {inputField('year', 'Year', form.year, 'number', 'e.g. 2')}
              {inputField('section', 'Section', form.section, 'text', 'e.g. A')}
            </div>

            <button type="submit" className="btn btn-primary w-full btn-lg" disabled={loading}>
              {loading ? <Loader2 className="w-4 h-4 animate-spin" /> : 'Create Account'}
            </button>
          </form>

          <p className="text-center text-sm text-surface-500 mt-6">
            Already have an account?{' '}
            <Link to="/login" className="text-primary-600 font-medium hover:text-primary-700">
              Sign in
            </Link>
          </p>
        </div>
      </div>
    </div>
  );
}
