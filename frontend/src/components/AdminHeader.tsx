import { useState, useRef, useEffect } from 'react';
import { useLocation, useNavigate, Link } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import NotificationBell from './NotificationBell';
import {
  Menu,
  User as UserIcon,
  LogOut,
  ChevronDown,
  ChevronRight,
} from 'lucide-react';

interface AdminHeaderProps {
  onOpenSidebar: () => void;
}

const ROUTE_META: Record<string, { title: string; section?: string }> = {
  '/admin/dashboard': { title: 'Dashboard' },
  '/admin/students': { title: 'Students', section: 'Management' },
  '/admin/lecturers': { title: 'Lecturers', section: 'Management' },
  '/admin/subjects': { title: 'Subjects', section: 'Management' },
  '/admin/assignments': { title: 'Assignments', section: 'Management' },
  '/admin/attendance': { title: 'Attendance', section: 'Attendance' },
  '/admin/reports': { title: 'Reports', section: 'Attendance' },
  '/admin/notifications': { title: 'Notifications', section: 'Communication' },
  '/admin/profile': { title: 'Profile', section: 'Account' },
};

export default function AdminHeader({ onOpenSidebar }: AdminHeaderProps) {
  const { user, logout } = useAuth();
  const location = useLocation();
  const navigate = useNavigate();
  const [menuOpen, setMenuOpen] = useState(false);
  const menuRef = useRef<HTMLDivElement>(null);

  const currentMeta = ROUTE_META[location.pathname] || { title: 'Admin Portal' };

  useEffect(() => {
    function handleClickOutside(event: MouseEvent) {
      if (menuRef.current && !menuRef.current.contains(event.target as Node)) {
        setMenuOpen(false);
      }
    }
    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  const handleLogout = () => {
    setMenuOpen(false);
    logout();
    navigate('/login');
  };

  return (
    <header className="sticky top-0 z-30 bg-white/90 backdrop-blur-md border-b border-surface-200">
      <div className="flex items-center justify-between px-4 sm:px-6 py-3">
        {/* Left: Mobile hamburger & breadcrumbs/title */}
        <div className="flex items-center gap-3">
          <button
            onClick={onOpenSidebar}
            className="lg:hidden p-2 rounded-lg hover:bg-surface-100 text-surface-600 focus:outline-none focus:ring-2 focus:ring-primary-500/50"
            aria-label="Open navigation menu"
          >
            <Menu className="w-5 h-5" />
          </button>

          <div>
            {/* Breadcrumb */}
            <nav aria-label="Breadcrumb" className="hidden sm:flex items-center gap-1.5 text-xs text-surface-400">
              <Link to="/admin/dashboard" className="hover:text-surface-700 transition-colors">
                Admin
              </Link>
              {currentMeta.section && (
                <>
                  <ChevronRight className="w-3 h-3 text-surface-300" aria-hidden="true" />
                  <span className="text-surface-500">{currentMeta.section}</span>
                </>
              )}
              <ChevronRight className="w-3 h-3 text-surface-300" aria-hidden="true" />
              <span className="font-medium text-surface-700">{currentMeta.title}</span>
            </nav>
            {/* Title */}
            <h1 className="text-lg font-bold text-surface-900 leading-tight">
              {currentMeta.title}
            </h1>
          </div>
        </div>

        {/* Right: Notification bell & profile dropdown */}
        <div className="flex items-center gap-2 sm:gap-3">
          <NotificationBell />

          {/* Profile Dropdown */}
          <div className="relative" ref={menuRef}>
            <button
              onClick={() => setMenuOpen(!menuOpen)}
              className="flex items-center gap-2 p-1.5 rounded-lg hover:bg-surface-100 transition-colors focus:outline-none focus:ring-2 focus:ring-primary-500/50"
              aria-haspopup="true"
              aria-expanded={menuOpen}
              aria-label="Admin profile menu"
            >
              <div className="w-8 h-8 rounded-full bg-gradient-to-br from-primary-600 to-primary-700 text-white flex items-center justify-center font-bold text-sm shadow-xs">
                {user?.full_name?.charAt(0).toUpperCase() || 'A'}
              </div>
              <div className="hidden md:block text-left">
                <p className="text-xs font-semibold text-surface-800 leading-none">
                  {user?.full_name || 'Admin'}
                </p>
                <p className="text-[0.68rem] text-primary-600 font-medium">Administrator</p>
              </div>
              <ChevronDown className="w-3.5 h-3.5 text-surface-400 hidden sm:block" aria-hidden="true" />
            </button>

            {/* Menu */}
            {menuOpen && (
              <div
                className="absolute right-0 mt-2 w-52 bg-white rounded-xl shadow-lg border border-surface-200 py-1.5 z-50 fade-in"
                role="menu"
                aria-orientation="vertical"
              >
                <div className="px-4 py-2 border-b border-surface-100">
                  <p className="text-xs font-semibold text-surface-800 truncate">
                    {user?.full_name}
                  </p>
                  <p className="text-[0.7rem] text-surface-400 truncate">
                    {user?.email}
                  </p>
                </div>
                <button
                  onClick={() => {
                    setMenuOpen(false);
                    navigate('/admin/profile');
                  }}
                  className="flex items-center gap-2.5 w-full px-4 py-2 text-xs font-medium text-surface-700 hover:bg-surface-50 hover:text-surface-900 transition-colors text-left"
                  role="menuitem"
                >
                  <UserIcon className="w-4 h-4 text-surface-400" aria-hidden="true" />
                  Admin Profile
                </button>
                <div className="my-1 border-t border-surface-100" />
                <button
                  onClick={handleLogout}
                  className="flex items-center gap-2.5 w-full px-4 py-2 text-xs font-medium text-red-600 hover:bg-red-50 transition-colors text-left"
                  role="menuitem"
                >
                  <LogOut className="w-4 h-4 text-red-500" aria-hidden="true" />
                  Logout
                </button>
              </div>
            )}
          </div>
        </div>
      </div>
    </header>
  );
}
