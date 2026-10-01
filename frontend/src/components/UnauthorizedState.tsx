import { ShieldAlert, ArrowLeft } from 'lucide-react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';

interface UnauthorizedStateProps {
  title?: string;
  message?: string;
}

export default function UnauthorizedState({
  title = 'Access Denied',
  message = "You don't have permission to access this area.",
}: UnauthorizedStateProps) {
  const navigate = useNavigate();
  const { user } = useAuth();

  const handleReturn = () => {
    if (user?.role === 'admin') {
      navigate('/admin/dashboard');
    } else if (user?.role === 'lecturer') {
      navigate('/lecturer/dashboard');
    } else {
      navigate('/dashboard');
    }
  };

  const getDashboardName = () => {
    if (user?.role === 'admin') return 'Admin Dashboard';
    if (user?.role === 'lecturer') return 'Lecturer Dashboard';
    return 'Student Dashboard';
  };

  return (
    <div className="min-h-[70vh] flex flex-col items-center justify-center p-6 text-center fade-in">
      <div className="w-16 h-16 rounded-2xl bg-amber-50 border border-amber-100 flex items-center justify-center mb-5 text-amber-600 shadow-sm">
        <ShieldAlert className="w-8 h-8" aria-hidden="true" />
      </div>
      <h2 className="text-2xl font-bold text-surface-900 mb-2">{title}</h2>
      <p className="text-surface-500 max-w-md text-sm mb-6 leading-relaxed">
        {message}
      </p>
      <div className="flex flex-wrap items-center justify-center gap-3">
        <button
          onClick={handleReturn}
          className="btn btn-primary btn-md flex items-center gap-2"
          aria-label="Return to your accessible dashboard"
        >
          <ArrowLeft className="w-4 h-4" />
          Return to {getDashboardName()}
        </button>
      </div>
    </div>
  );
}
