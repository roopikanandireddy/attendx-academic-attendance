import { NavLink, useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import {
  LayoutDashboard,
  Users,
  BookOpen,
  ClipboardCheck,
  History,
  BarChart3,
  User,
  LogOut,
  X,
  GraduationCap,
} from 'lucide-react';

interface SidebarProps {
  isOpen: boolean;
  onClose: () => void;
}

export default function Sidebar({ isOpen, onClose }: SidebarProps) {
  const { user, logout } = useAuth();
  const navigate = useNavigate();

  const handleLogout = () => {
    logout();
    navigate('/login');
  };

  const studentLinks = [
    { to: '/dashboard', label: 'Dashboard', icon: LayoutDashboard },
    { to: '/my-subjects', label: 'My Subjects', icon: BookOpen },
    { to: '/my-attendance', label: 'Attendance', icon: ClipboardCheck },
    { to: '/attendance-history', label: 'History', icon: History },
    { to: '/profile', label: 'Profile', icon: User },
  ];

  const adminLinks = [
    { to: '/admin/dashboard', label: 'Dashboard', icon: LayoutDashboard },
    { to: '/admin/students', label: 'Students', icon: Users },
    { to: '/admin/subjects', label: 'Subjects', icon: BookOpen },
    { to: '/admin/mark-attendance', label: 'Mark Attendance', icon: ClipboardCheck },
    { to: '/admin/attendance-records', label: 'Attendance Records', icon: History },
    { to: '/admin/reports', label: 'Reports', icon: BarChart3 },
    { to: '/profile', label: 'Profile', icon: User },
  ];

  const links = user?.role === 'admin' ? adminLinks : studentLinks;

  const linkClass = ({ isActive }: { isActive: boolean }) =>
    `flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium transition-all duration-200 ${
      isActive
        ? 'bg-primary-50 text-primary-700 shadow-sm'
        : 'text-surface-600 hover:bg-surface-100 hover:text-surface-800'
    }`;

  return (
    <>
      {/* Mobile overlay */}
      {isOpen && (
        <div className="fixed inset-0 bg-black/40 backdrop-blur-sm z-40 lg:hidden" onClick={onClose} />
      )}

      {/* Sidebar */}
      <aside
        className={`fixed top-0 left-0 h-full w-64 bg-white border-r border-surface-200 z-50 flex flex-col transition-transform duration-300 ease-in-out lg:translate-x-0 ${
          isOpen ? 'translate-x-0' : '-translate-x-full'
        }`}
      >
        {/* Logo */}
        <div className="px-5 py-5 border-b border-surface-100 flex items-center justify-between">
          <div className="flex items-center gap-2.5">
            <div className="w-9 h-9 rounded-xl bg-gradient-to-br from-primary-600 to-primary-700 flex items-center justify-center shadow-md">
              <GraduationCap className="w-5 h-5 text-white" />
            </div>
            <div>
              <h1 className="text-lg font-bold text-surface-900 leading-tight">AttendX</h1>
              <p className="text-[0.65rem] text-surface-400 font-medium uppercase tracking-wider">
                {user?.role === 'admin' ? 'Admin Panel' : 'Student Portal'}
              </p>
            </div>
          </div>
          <button onClick={onClose} className="lg:hidden text-surface-400 hover:text-surface-600">
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Nav links */}
        <nav className="flex-1 px-3 py-4 space-y-1 overflow-y-auto">
          {links.map((link) => (
            <NavLink key={link.to} to={link.to} className={linkClass} onClick={onClose}>
              <link.icon className="w-[18px] h-[18px]" />
              {link.label}
            </NavLink>
          ))}
        </nav>

        {/* User info + Logout */}
        <div className="px-3 py-4 border-t border-surface-100">
          <div className="px-3 py-2 mb-2">
            <p className="text-sm font-medium text-surface-800 truncate">{user?.full_name}</p>
            <p className="text-xs text-surface-400 truncate">{user?.email}</p>
          </div>
          <button
            onClick={handleLogout}
            className="flex items-center gap-3 w-full px-3 py-2.5 rounded-lg text-sm font-medium text-surface-600 hover:bg-red-50 hover:text-danger transition-colors"
          >
            <LogOut className="w-[18px] h-[18px]" />
            Logout
          </button>
        </div>
      </aside>
    </>
  );
}
