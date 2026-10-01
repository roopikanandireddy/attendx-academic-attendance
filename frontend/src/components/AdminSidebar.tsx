import { NavLink, useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import {
  LayoutDashboard,
  Users,
  GraduationCap,
  BookOpen,
  Layers,
  ClipboardCheck,
  BarChart3,
  Bell,
  User,
  LogOut,
  X,
  ShieldCheck,
} from 'lucide-react';

interface AdminSidebarProps {
  isOpen: boolean;
  onClose: () => void;
}

export default function AdminSidebar({ isOpen, onClose }: AdminSidebarProps) {
  const { user, logout } = useAuth();
  const navigate = useNavigate();

  const handleLogout = () => {
    logout();
    navigate('/login');
  };

  const navSections = [
    {
      title: null,
      items: [
        { to: '/admin/dashboard', label: 'Dashboard', icon: LayoutDashboard },
      ],
    },
    {
      title: 'Management',
      items: [
        { to: '/admin/students', label: 'Students', icon: Users },
        { to: '/admin/lecturers', label: 'Lecturers', icon: GraduationCap },
        { to: '/admin/subjects', label: 'Subjects', icon: BookOpen },
        { to: '/admin/assignments', label: 'Assignments', icon: Layers },
      ],
    },
    {
      title: 'Attendance',
      items: [
        { to: '/admin/attendance', label: 'Attendance', icon: ClipboardCheck },
        { to: '/admin/reports', label: 'Reports', icon: BarChart3 },
      ],
    },
    {
      title: 'Communication',
      items: [
        { to: '/admin/notifications', label: 'Notifications', icon: Bell },
      ],
    },
    {
      title: 'Account',
      items: [
        { to: '/admin/profile', label: 'Profile', icon: User },
      ],
    },
  ];

  const linkClass = ({ isActive }: { isActive: boolean }) =>
    `flex items-center gap-3 px-3 py-2 rounded-lg text-sm font-medium transition-all duration-200 focus:outline-none focus:ring-2 focus:ring-primary-500/50 ${
      isActive
        ? 'bg-primary-50 text-primary-700 font-semibold shadow-xs'
        : 'text-surface-600 hover:bg-surface-100 hover:text-surface-900'
    }`;

  return (
    <>
      {/* Mobile overlay */}
      {isOpen && (
        <div
          className="fixed inset-0 bg-black/40 backdrop-blur-xs z-40 lg:hidden"
          onClick={onClose}
          aria-hidden="true"
        />
      )}

      {/* Sidebar shell */}
      <aside
        className={`fixed top-0 left-0 h-full w-64 bg-white border-r border-surface-200 z-50 flex flex-col transition-transform duration-300 ease-in-out lg:translate-x-0 ${
          isOpen ? 'translate-x-0' : '-translate-x-full'
        }`}
        aria-label="Admin Navigation Sidebar"
      >
        {/* Brand header */}
        <div className="px-5 py-4 border-b border-surface-100 flex items-center justify-between">
          <div className="flex items-center gap-2.5">
            <div className="w-9 h-9 rounded-xl bg-gradient-to-br from-primary-600 to-primary-700 flex items-center justify-center shadow-sm">
              <ShieldCheck className="w-5 h-5 text-white" aria-hidden="true" />
            </div>
            <div>
              <h1 className="text-lg font-bold text-surface-900 leading-tight">AttendX</h1>
              <p className="text-[0.65rem] text-primary-600 font-semibold uppercase tracking-wider">
                Admin Portal
              </p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="lg:hidden text-surface-400 hover:text-surface-600 p-1.5 rounded-lg hover:bg-surface-100 transition-colors"
            aria-label="Close admin menu"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Navigation list */}
        <nav className="flex-1 px-3 py-3 overflow-y-auto space-y-4">
          {navSections.map((section, idx) => (
            <div key={idx} className="space-y-1">
              {section.title && (
                <p className="px-3 text-[0.68rem] font-bold uppercase tracking-wider text-surface-400 mb-1">
                  {section.title}
                </p>
              )}
              {section.items.map((item) => (
                <NavLink
                  key={item.to}
                  to={item.to}
                  className={linkClass}
                  onClick={onClose}
                >
                  <item.icon className="w-4 h-4 flex-shrink-0" aria-hidden="true" />
                  <span>{item.label}</span>
                </NavLink>
              ))}
            </div>
          ))}
        </nav>

        {/* Administrator profile & logout footer */}
        <div className="px-3 py-3 border-t border-surface-100 bg-surface-50/50">
          <div className="px-3 py-2 mb-1.5 flex items-center gap-2.5">
            <div className="w-8 h-8 rounded-lg bg-primary-100 text-primary-700 flex items-center justify-center font-bold text-xs">
              {user?.full_name?.charAt(0).toUpperCase() || 'A'}
            </div>
            <div className="flex-1 min-w-0">
              <p className="text-xs font-semibold text-surface-800 truncate">
                {user?.full_name || 'System Admin'}
              </p>
              <p className="text-[0.68rem] text-surface-400 truncate">
                {user?.email || 'admin@attendx.com'}
              </p>
            </div>
          </div>
          <button
            onClick={handleLogout}
            className="flex items-center gap-3 w-full px-3 py-2 rounded-lg text-xs font-medium text-surface-600 hover:bg-red-50 hover:text-danger transition-colors focus:outline-none focus:ring-2 focus:ring-red-400/50"
            aria-label="Log out of Admin Portal"
          >
            <LogOut className="w-4 h-4 text-surface-400 group-hover:text-danger" aria-hidden="true" />
            <span>Logout</span>
          </button>
        </div>
      </aside>
    </>
  );
}
