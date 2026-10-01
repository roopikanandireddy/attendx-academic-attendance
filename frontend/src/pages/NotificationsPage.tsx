import { useState, useEffect, useCallback, useMemo } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import notificationService from '../services/notificationService';
import type { NotificationItem, NotificationType } from '../types';
import {
  Bell,
  CheckCircle2,
  AlertTriangle,
  BookOpen,
  Sparkles,
  Clock,
  CheckCheck,
  Check,
  ArrowRight,
  RefreshCw,
  Inbox,
  Filter,
  AlertCircle,
} from 'lucide-react';
import toast from 'react-hot-toast';

function formatRelativeTime(dateString: string): string {
  try {
    const date = new Date(dateString);
    if (isNaN(date.getTime())) return '';
    const now = new Date();
    const diffMs = now.getTime() - date.getTime();
    const diffSec = Math.floor(diffMs / 1000);
    const diffMin = Math.floor(diffSec / 60);
    const diffHours = Math.floor(diffMin / 60);
    const diffDays = Math.floor(diffHours / 24);

    if (diffSec < 60) return 'Just now';
    if (diffMin < 60) return `${diffMin}m ago`;
    if (diffHours < 24) return `${diffHours}h ago`;
    if (diffDays === 1) {
      const timeStr = date.toLocaleTimeString([], { hour: 'numeric', minute: '2-digit' });
      return `Yesterday at ${timeStr}`;
    }
    if (diffDays < 7) return `${diffDays} days ago`;

    return (
      date.toLocaleDateString([], { month: 'short', day: 'numeric', year: 'numeric' }) +
      ' at ' +
      date.toLocaleTimeString([], { hour: 'numeric', minute: '2-digit' })
    );
  } catch {
    return '';
  }
}

function getNotificationBadge(type: NotificationType) {
  switch (type) {
    case 'attendance':
      return {
        label: 'Attendance',
        bg: 'bg-emerald-50 text-emerald-700 border-emerald-200',
        iconBg: 'bg-emerald-100 text-emerald-600',
        icon: CheckCircle2,
      };
    case 'low_attendance':
      return {
        label: 'Attendance Warning',
        bg: 'bg-amber-50 text-amber-700 border-amber-200',
        iconBg: 'bg-amber-100 text-amber-600',
        icon: AlertTriangle,
      };
    case 'enrollment':
      return {
        label: 'Course Enrollment',
        bg: 'bg-primary-50 text-primary-700 border-primary-200',
        iconBg: 'bg-primary-100 text-primary-600',
        icon: BookOpen,
      };
    case 'system':
      return {
        label: 'System Notice',
        bg: 'bg-indigo-50 text-indigo-700 border-indigo-200',
        iconBg: 'bg-indigo-100 text-indigo-600',
        icon: Sparkles,
      };
    case 'reminder':
      return {
        label: 'Reminder',
        bg: 'bg-purple-50 text-purple-700 border-purple-200',
        iconBg: 'bg-purple-100 text-purple-600',
        icon: Clock,
      };
    default:
      return {
        label: 'Notification',
        bg: 'bg-surface-100 text-surface-700 border-surface-200',
        iconBg: 'bg-surface-100 text-surface-600',
        icon: Bell,
      };
  }
}

export default function NotificationsPage() {
  const { user } = useAuth();
  const navigate = useNavigate();

  const [notifications, setNotifications] = useState<NotificationItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [markingAll, setMarkingAll] = useState(false);
  const [markingId, setMarkingId] = useState<string | null>(null);

  // Filters
  const [statusTab, setStatusTab] = useState<'all' | 'unread'>('all');
  const [categoryFilter, setCategoryFilter] = useState<string>('all');

  const fetchNotifications = useCallback(async (isRefresh = false) => {
    if (isRefresh) {
      setRefreshing(true);
    } else {
      setLoading(true);
    }
    setError(null);
    try {
      const data = await notificationService.getNotifications(100, 1);
      setNotifications(data);
    } catch {
      setError('Unable to load notifications. Please check your connection and try again.');
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  }, []);

  useEffect(() => {
    fetchNotifications();
  }, [fetchNotifications]);

  const unreadCount = useMemo(() => {
    return notifications.filter((n) => !n.is_read).length;
  }, [notifications]);

  // Filtered notifications
  const filteredNotifications = useMemo(() => {
    return notifications.filter((notif) => {
      // Status filter
      if (statusTab === 'unread' && notif.is_read) {
        return false;
      }
      // Category filter
      if (categoryFilter !== 'all' && notif.type !== categoryFilter) {
        return false;
      }
      return true;
    });
  }, [notifications, statusTab, categoryFilter]);

  // Mark single notification as read
  const handleMarkAsRead = async (id: string, e?: React.MouseEvent) => {
    if (e) e.stopPropagation();
    setMarkingId(id);

    // Optimistic UI update
    setNotifications((prev) =>
      prev.map((item) => (item.id === id ? { ...item, is_read: true } : item))
    );

    try {
      await notificationService.markNotificationAsRead(id);
      toast.success('Marked as read');
    } catch {
      // Revert on error
      setNotifications((prev) =>
        prev.map((item) => (item.id === id ? { ...item, is_read: false } : item))
      );
      toast.error('Failed to update notification');
    } finally {
      setMarkingId(null);
    }
  };

  // Mark all notifications as read
  const handleMarkAllAsRead = async () => {
    if (unreadCount === 0 || markingAll) return;
    setMarkingAll(true);
    const prev = [...notifications];

    // Optimistic UI update
    setNotifications((items) => items.map((i) => ({ ...i, is_read: true })));

    try {
      await notificationService.markAllNotificationsAsRead();
      toast.success('All notifications marked as read');
    } catch {
      setNotifications(prev);
      toast.error('Failed to mark all as read');
    } finally {
      setMarkingAll(false);
    }
  };

  // Safe navigation target based on notification context and user role
  const getActionTarget = (notif: NotificationItem) => {
    const role = user?.role;
    if (notif.type === 'attendance' || notif.type === 'low_attendance') {
      if (role === 'lecturer') return { path: '/lecturer/reports', label: 'View Records & Reports' };
      if (role === 'admin') return { path: '/admin/attendance', label: 'View Attendance Records' };
      return { path: '/my-attendance', label: 'View My Attendance' };
    }

    if (notif.type === 'enrollment') {
      if (role === 'lecturer') return { path: '/lecturer/subjects', label: 'View Assigned Subjects' };
      if (role === 'admin') return { path: '/admin/subjects', label: 'Manage Subjects' };
      return { path: '/my-subjects', label: 'View My Subjects' };
    }

    if (notif.type === 'system') {
      if (notif.related_entity_type === 'subject') {
        if (role === 'lecturer') return { path: '/lecturer/subjects', label: 'View Teaching Subjects' };
        if (role === 'admin') return { path: '/admin/assignments', label: 'View Subject Assignments' };
      }
      if (notif.related_entity_type === 'faculty') {
        if (role === 'lecturer') return { path: '/lecturer/dashboard', label: 'Go to Faculty Dashboard' };
      }
    }

    return null;
  };

  return (
    <div className="max-w-5xl mx-auto space-y-6">
      {/* Top Header Card */}
      <div className="bg-white rounded-2xl p-6 sm:p-8 border border-surface-200 shadow-xs relative overflow-hidden">
        <div className="absolute top-0 right-0 w-80 h-80 bg-gradient-to-bl from-primary-100/40 via-transparent to-transparent pointer-events-none rounded-tr-2xl" />

        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 relative z-10">
          <div>
            <div className="flex items-center gap-2.5 mb-1.5">
              <div className="w-10 h-10 rounded-xl bg-primary-100 text-primary-700 flex items-center justify-center shadow-xs">
                <Bell className="w-5 h-5" />
              </div>
              <h1 className="text-2xl font-bold text-surface-900 tracking-tight">Notifications</h1>
              {unreadCount > 0 && (
                <span className="px-2.5 py-0.5 text-xs font-semibold rounded-full bg-primary-100 text-primary-700 border border-primary-200">
                  {unreadCount} unread
                </span>
              )}
            </div>
            <p className="text-sm text-surface-500 max-w-xl">
              Stay up to date with attendance updates, course enrollments, faculty notices, and system alerts.
            </p>
          </div>

          <div className="flex items-center gap-2.5 shrink-0">
            <button
              type="button"
              onClick={() => fetchNotifications(true)}
              disabled={loading || refreshing}
              className="px-3.5 py-2 text-xs font-medium text-surface-700 bg-surface-50 hover:bg-surface-100 border border-surface-200 rounded-lg transition-colors flex items-center gap-1.5 disabled:opacity-50 cursor-pointer"
              title="Refresh notifications"
            >
              <RefreshCw className={`w-3.5 h-3.5 ${refreshing ? 'animate-spin' : ''}`} />
              <span>Refresh</span>
            </button>

            {unreadCount > 0 && (
              <button
                type="button"
                onClick={handleMarkAllAsRead}
                disabled={markingAll || loading}
                className="px-3.5 py-2 text-xs font-medium text-white bg-primary-600 hover:bg-primary-700 active:bg-primary-800 rounded-lg shadow-xs transition-colors flex items-center gap-1.5 disabled:opacity-50 cursor-pointer"
              >
                <CheckCheck className="w-4 h-4" />
                <span>Mark all as read</span>
              </button>
            )}
          </div>
        </div>

        {/* Filter Navigation Bar */}
        <div className="mt-6 pt-5 border-t border-surface-100 flex flex-col md:flex-row md:items-center justify-between gap-4">
          {/* Status Tabs */}
          <div className="flex items-center gap-1 p-1 bg-surface-100/80 rounded-xl w-fit">
            <button
              type="button"
              onClick={() => setStatusTab('all')}
              className={`px-4 py-1.5 text-xs font-semibold rounded-lg transition-all cursor-pointer ${
                statusTab === 'all'
                  ? 'bg-white text-surface-900 shadow-xs'
                  : 'text-surface-600 hover:text-surface-900'
              }`}
            >
              All ({notifications.length})
            </button>
            <button
              type="button"
              onClick={() => setStatusTab('unread')}
              className={`px-4 py-1.5 text-xs font-semibold rounded-lg transition-all cursor-pointer flex items-center gap-1.5 ${
                statusTab === 'unread'
                  ? 'bg-white text-primary-700 shadow-xs'
                  : 'text-surface-600 hover:text-surface-900'
              }`}
            >
              <span>Unread</span>
              {unreadCount > 0 && (
                <span className="w-5 h-5 rounded-full bg-primary-600 text-white text-[10px] flex items-center justify-center font-bold">
                  {unreadCount}
                </span>
              )}
            </button>
          </div>

          {/* Category Filter Pills */}
          <div className="flex items-center gap-1.5 flex-wrap">
            <span className="text-xs text-surface-400 font-medium mr-1 flex items-center gap-1">
              <Filter className="w-3.5 h-3.5" />
              <span>Category:</span>
            </span>
            {[
              { id: 'all', label: 'All' },
              { id: 'attendance', label: 'Attendance' },
              { id: 'low_attendance', label: 'Warnings' },
              { id: 'enrollment', label: 'Enrollments' },
              { id: 'system', label: 'System' },
            ].map((cat) => (
              <button
                key={cat.id}
                type="button"
                onClick={() => setCategoryFilter(cat.id)}
                className={`px-3 py-1 text-xs font-medium rounded-full transition-colors cursor-pointer border ${
                  categoryFilter === cat.id
                    ? 'bg-surface-900 text-white border-surface-900 shadow-xs'
                    : 'bg-white text-surface-600 hover:bg-surface-50 border-surface-200'
                }`}
              >
                {cat.label}
              </button>
            ))}
          </div>
        </div>
      </div>

      {/* Main Content Area */}
      {/* Loading Skeletons */}
      {loading && notifications.length === 0 && (
        <div className="space-y-3">
          {[1, 2, 3, 4, 5].map((idx) => (
            <div
              key={idx}
              className="bg-white rounded-xl p-5 border border-surface-200 animate-pulse flex items-start gap-4"
            >
              <div className="w-10 h-10 rounded-xl bg-surface-200 shrink-0" />
              <div className="flex-1 space-y-2.5">
                <div className="flex items-center justify-between">
                  <div className="h-4 bg-surface-200 rounded w-1/4" />
                  <div className="h-3 bg-surface-100 rounded w-20" />
                </div>
                <div className="h-3.5 bg-surface-100 rounded w-3/4" />
                <div className="h-3 bg-surface-100 rounded w-1/2" />
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Error State */}
      {!loading && error && (
        <div className="bg-white rounded-xl p-8 border border-rose-200 text-center">
          <div className="w-12 h-12 rounded-full bg-rose-50 text-rose-600 flex items-center justify-center mx-auto mb-3">
            <AlertCircle className="w-6 h-6" />
          </div>
          <h2 className="text-base font-semibold text-surface-900 mb-1">Failed to Load Notifications</h2>
          <p className="text-sm text-surface-500 mb-4">{error}</p>
          <button
            type="button"
            onClick={() => fetchNotifications(false)}
            className="px-4 py-2 text-xs font-semibold text-white bg-primary-600 hover:bg-primary-700 rounded-lg transition-colors cursor-pointer"
          >
            Retry Connection
          </button>
        </div>
      )}

      {/* Empty State */}
      {!loading && !error && filteredNotifications.length === 0 && (
        <div className="bg-white rounded-2xl p-12 border border-surface-200 text-center shadow-xs">
          <div className="w-16 h-16 rounded-2xl bg-surface-100 text-surface-400 flex items-center justify-center mx-auto mb-4">
            <Inbox className="w-8 h-8" />
          </div>
          <h2 className="text-lg font-semibold text-surface-900 mb-1">
            {statusTab === 'unread'
              ? "You're all caught up!"
              : categoryFilter !== 'all'
              ? 'No notifications in this category'
              : 'No notifications yet'}
          </h2>
          <p className="text-sm text-surface-500 max-w-sm mx-auto mb-5">
            {statusTab === 'unread'
              ? 'There are no unread notifications at the moment. All recorded updates have been reviewed.'
              : categoryFilter !== 'all'
              ? 'Try selecting a different filter above to see other notification records.'
              : 'When attendance is recorded, courses are enrolled, or notices are issued, they will appear here.'}
          </p>
          {statusTab === 'unread' && notifications.length > 0 && (
            <button
              type="button"
              onClick={() => {
                setStatusTab('all');
                setCategoryFilter('all');
              }}
              className="px-4 py-2 text-xs font-semibold text-primary-700 bg-primary-50 hover:bg-primary-100 rounded-lg transition-colors cursor-pointer"
            >
              View all notification history
            </button>
          )}
        </div>
      )}

      {/* Notifications List */}
      {!loading && !error && filteredNotifications.length > 0 && (
        <div className="space-y-3">
          {filteredNotifications.map((notif) => {
            const badge = getNotificationBadge(notif.type);
            const Icon = badge.icon;
            const timeAgo = formatRelativeTime(notif.created_at);
            const actionTarget = getActionTarget(notif);

            return (
              <div
                key={notif.id}
                onClick={() => {
                  if (!notif.is_read) {
                    handleMarkAsRead(notif.id);
                  }
                }}
                className={`bg-white rounded-xl p-5 border transition-all duration-200 relative group cursor-pointer ${
                  notif.is_read
                    ? 'border-surface-200 hover:border-surface-300 hover:shadow-xs'
                    : 'border-primary-200 bg-primary-50/20 shadow-xs border-l-4 border-l-primary-600'
                }`}
              >
                <div className="flex items-start gap-4">
                  {/* Category Icon */}
                  <div
                    className={`w-10 h-10 rounded-xl flex items-center justify-center shrink-0 ${badge.iconBg}`}
                  >
                    <Icon className="w-5 h-5" />
                  </div>

                  {/* Body Content */}
                  <div className="flex-1 min-w-0">
                    <div className="flex flex-wrap items-center justify-between gap-2 mb-1">
                      <div className="flex items-center gap-2">
                        <span
                          className={`px-2 py-0.5 rounded-md text-[11px] font-semibold border ${badge.bg}`}
                        >
                          {badge.label}
                        </span>
                        {!notif.is_read && (
                          <span className="px-2 py-0.5 rounded-md text-[10px] font-bold uppercase tracking-wider bg-primary-600 text-white shadow-xs">
                            New
                          </span>
                        )}
                      </div>

                      <div className="flex items-center gap-1.5 text-xs text-surface-400">
                        <Clock className="w-3.5 h-3.5" />
                        <span>{timeAgo}</span>
                      </div>
                    </div>

                    <h2
                      className={`text-sm tracking-tight mb-1 ${
                        notif.is_read
                          ? 'font-semibold text-surface-800'
                          : 'font-bold text-surface-950'
                      }`}
                    >
                      {notif.title}
                    </h2>

                    <p className="text-sm text-surface-600 leading-relaxed">{notif.message}</p>

                    {/* Action Bar */}
                    <div className="mt-3 pt-3 border-t border-surface-100 flex flex-wrap items-center justify-between gap-2">
                      <div>
                        {actionTarget && (
                          <button
                            type="button"
                            onClick={(e) => {
                              e.stopPropagation();
                              if (!notif.is_read) {
                                handleMarkAsRead(notif.id);
                              }
                              navigate(actionTarget.path);
                            }}
                            className="inline-flex items-center gap-1.5 text-xs font-semibold text-primary-600 hover:text-primary-700 hover:underline cursor-pointer"
                          >
                            <span>{actionTarget.label}</span>
                            <ArrowRight className="w-3.5 h-3.5" />
                          </button>
                        )}
                      </div>

                      <div className="flex items-center gap-2">
                        {!notif.is_read ? (
                          <button
                            type="button"
                            onClick={(e) => handleMarkAsRead(notif.id, e)}
                            disabled={markingId === notif.id}
                            className="px-2.5 py-1 text-xs font-medium text-surface-600 hover:text-surface-900 hover:bg-surface-100 rounded-md transition-colors flex items-center gap-1 cursor-pointer disabled:opacity-50"
                            title="Mark as read"
                          >
                            <Check className="w-3.5 h-3.5 text-primary-600" />
                            <span>Mark read</span>
                          </button>
                        ) : (
                          <span className="text-[11px] text-surface-400 font-medium flex items-center gap-1">
                            <Check className="w-3 h-3 text-emerald-600" />
                            <span>Read</span>
                          </span>
                        )}
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}
