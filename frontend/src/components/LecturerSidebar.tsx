import { NavLink, useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import {
  LayoutDashboard,
  BookOpen,
  ClipboardCheck,
  BarChart3,
  Bell,
  User,
  LogOut,
  X,
  GraduationCap,
} from 'lucide-react';

interface LecturerSidebarProps {
  isOpen: boolean;
  onClose: () => void;
}

export default function LecturerSidebar({ isOpen, onClose }: LecturerSidebarProps) {
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
        { to: '/lecturer/dashboard', label: 'Dashboard', icon: LayoutDashboard },
      ],
    },
    {
      title: 'Teaching Workspace',
      items: [
        { to: '/lecturer/subjects', label: 'My Subjects', icon: BookOpen },
        { to: '/lecturer/attendance', label: 'Mark Attendance', icon: ClipboardCheck },
        { to: '/lecturer/reports', label: 'Records & Reports', icon: BarChart3 },
      ],
    },
    {
      title: 'Account',
      items: [
        { to: '/lecturer/notifications', label: 'Notifications', icon: Bell },
        { to: '/lecturer/profile', label: 'Profile', icon: User },
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
        aria-label="Lecturer Navigation Sidebar"
      >
        {/* Brand header */}
        <div className="px-5 py-4 border-b border-surface-100 flex items-center justify-between">
          <div className="flex items-center gap-2.5">
            <div className="w-9 h-9 rounded-xl bg-gradient-to-br from-indigo-600 to-primary-700 flex items-center justify-center shadow-sm">
              <GraduationCap className="w-5 h-5 text-white" aria-hidden="true" />
            </div>
            <div>
              <h1 className="text-lg font-bold text-surface-900 leading-tight">AttendX</h1>
              <p className="text-[0.65rem] text-indigo-600 font-semibold uppercase tracking-wider">
                Lecturer Portal
              </p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="lg:hidden text-surface-400 hover:text-surface-600 p-1.5 rounded-lg hover:bg-surface-100 transition-colors"
            aria-label="Close lecturer menu"
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

        {/* Lecturer profile & logout footer */}
        <div className="px-3 py-3 border-t border-surface-100 bg-surface-50/50">
          <div className="px-3 py-2 mb-1.5 flex items-center gap-2.5">
            <div className="w-8 h-8 rounded-lg bg-indigo-100 text-indigo-700 flex items-center justify-center font-bold text-xs">
              {user?.full_name?.charAt(0).toUpperCase() || 'L'}
            </div>
            <div className="flex-1 min-w-0">
              <p className="text-xs font-semibold text-surface-800 truncate">
                {user?.full_name || 'Faculty Member'}
              </p>
              <p className="text-[0.68rem] text-surface-400 truncate">
                {user?.employee_id ? `${user.employee_id} • ` : ''}{user?.department || user?.email}
              </p>
            </div>
          </div>
          <button
            onClick={handleLogout}
            className="flex items-center gap-3 w-full px-3 py-2 rounded-lg text-xs font-medium text-surface-600 hover:bg-red-50 hover:text-danger transition-colors focus:outline-none focus:ring-2 focus:ring-red-400/50"
            aria-label="Log out of Lecturer Portal"
          >
            <LogOut className="w-4 h-4 text-surface-400 group-hover:text-danger" aria-hidden="true" />
            <span>Logout</span>
          </button>
        </div>
      </aside>
    </>
  );
}
