import { useState, useEffect, useRef, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import {
  Bell,
  CheckCircle2,
  AlertTriangle,
  BookOpen,
  Sparkles,
  Clock,
  CheckCheck,
  AlertCircle,
  RefreshCw,
  ChevronRight,
} from 'lucide-react';
import notificationService from '../services/notificationService';
import { isRequestCancelled } from '../services/api';
import type { NotificationItem, NotificationType } from '../types';
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

    if (diffSec < 60) {
      return 'Just now';
    }
    if (diffMin < 60) {
      return `${diffMin}m ago`;
    }
    if (diffHours < 24) {
      return `${diffHours}h ago`;
    }
    if (diffDays === 1) {
      const timeStr = date.toLocaleTimeString([], { hour: 'numeric', minute: '2-digit' });
      return `Yesterday, ${timeStr}`;
    }
    if (diffDays < 7) {
      return `${diffDays}d ago`;
    }
    return (
      date.toLocaleDateString([], { month: 'short', day: 'numeric' }) +
      ', ' +
      date.toLocaleTimeString([], { hour: 'numeric', minute: '2-digit' })
    );
  } catch {
    return '';
  }
}

function getNotificationIcon(type: NotificationType) {
  switch (type) {
    case 'attendance':
      return (
        <div className="w-8 h-8 rounded-full bg-emerald-50 border border-emerald-200 flex items-center justify-center shrink-0">
          <CheckCircle2 className="w-4 h-4 text-emerald-600" />
        </div>
      );
    case 'low_attendance':
      return (
        <div className="w-8 h-8 rounded-full bg-amber-50 border border-amber-200 flex items-center justify-center shrink-0">
          <AlertTriangle className="w-4 h-4 text-amber-600" />
        </div>
      );
    case 'enrollment':
      return (
        <div className="w-8 h-8 rounded-full bg-primary-50 border border-primary-200 flex items-center justify-center shrink-0">
          <BookOpen className="w-4 h-4 text-primary-600" />
        </div>
      );
    case 'system':
      return (
        <div className="w-8 h-8 rounded-full bg-indigo-50 border border-indigo-200 flex items-center justify-center shrink-0">
          <Sparkles className="w-4 h-4 text-indigo-600" />
        </div>
      );
    case 'reminder':
      return (
        <div className="w-8 h-8 rounded-full bg-purple-50 border border-purple-200 flex items-center justify-center shrink-0">
          <Clock className="w-4 h-4 text-purple-600" />
        </div>
      );
    default:
      return (
        <div className="w-8 h-8 rounded-full bg-surface-100 border border-surface-200 flex items-center justify-center shrink-0">
          <Bell className="w-4 h-4 text-surface-600" />
        </div>
      );
  }
}

export default function NotificationBell() {
  const navigate = useNavigate();
  const { user } = useAuth();
  const [isOpen, setIsOpen] = useState(false);
  const [unreadCount, setUnreadCount] = useState<number>(0);
  const [notifications, setNotifications] = useState<NotificationItem[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(false);
  const [markingAll, setMarkingAll] = useState(false);

  const containerRef = useRef<HTMLDivElement>(null);

  const getNotificationsPath = () => {
    if (user?.role === 'admin') return '/admin/notifications';
    if (user?.role === 'lecturer') return '/lecturer/notifications';
    return '/notifications';
  };

  // Fetch unread count
  const fetchUnreadCount = useCallback(async (signal?: AbortSignal) => {
    try {
      const count = await notificationService.getUnreadNotificationCount({ signal });
      setUnreadCount(count);
    } catch (err) {
      if (isRequestCancelled(err)) return;
      // Ignore background count errors
    }
  }, []);

  // Fetch notifications list
  const fetchNotifications = useCallback(async (isInitial = true, signal?: AbortSignal) => {
    if (isInitial) setLoading(true);
    setError(false);
    try {
      const data = await notificationService.getNotifications(50, 1, undefined, undefined, { signal });
      setNotifications(data);
      const unread = data.filter((n) => !n.is_read).length;
      setUnreadCount(unread);
    } catch (err) {
      if (isRequestCancelled(err)) return;
      setError(true);
    } finally {
      setLoading(false);
    }
  }, []);

  // Initial count load & 30s background poll with cleanup
  useEffect(() => {
    const controller = new AbortController();
    fetchUnreadCount(controller.signal);
    const interval = setInterval(() => {
      fetchUnreadCount();
    }, 30000);
    return () => {
      controller.abort();
      clearInterval(interval);
    };
  }, [fetchUnreadCount]);

  // When dropdown opens, fetch latest notifications with cleanup
  useEffect(() => {
    if (isOpen) {
      const controller = new AbortController();
      fetchNotifications(true, controller.signal);
      return () => {
        controller.abort();
      };
    }
  }, [isOpen, fetchNotifications]);

  // Click outside listener
  useEffect(() => {
    function handleClickOutside(event: MouseEvent | TouchEvent) {
      if (containerRef.current && !containerRef.current.contains(event.target as Node)) {
        setIsOpen(false);
      }
    }

    if (isOpen) {
      document.addEventListener('mousedown', handleClickOutside);
      document.addEventListener('touchstart', handleClickOutside);
    }
    return () => {
      document.removeEventListener('mousedown', handleClickOutside);
      document.removeEventListener('touchstart', handleClickOutside);
    };
  }, [isOpen]);

  // Escape key listener
  useEffect(() => {
    function handleKeyDown(event: KeyboardEvent) {
      if (event.key === 'Escape') {
        setIsOpen(false);
      }
    }

    if (isOpen) {
      document.addEventListener('keydown', handleKeyDown);
    }
    return () => {
      document.removeEventListener('keydown', handleKeyDown);
    };
  }, [isOpen]);

  // Mark single notification as read
  const handleItemClick = async (notif: NotificationItem) => {
    if (notif.is_read) return;

    // Optimistic UI update
    setNotifications((prev) =>
      prev.map((item) => (item.id === notif.id ? { ...item, is_read: true } : item))
    );
    setUnreadCount((prev) => Math.max(0, prev - 1));

    try {
      await notificationService.markNotificationAsRead(notif.id);
    } catch {
      // Revert optimistic update on failure
      setNotifications((prev) =>
        prev.map((item) => (item.id === notif.id ? { ...item, is_read: false } : item))
      );
      setUnreadCount((prev) => prev + 1);
      toast.error('Failed to mark notification as read');
    }
  };

  // Mark all notifications as read
  const handleMarkAllAsRead = async () => {
    if (markingAll || unreadCount === 0) return;
    setMarkingAll(true);

    const prevNotifs = [...notifications];
    const prevCount = unreadCount;

    // Optimistic UI update
    setNotifications((prev) => prev.map((item) => ({ ...item, is_read: true })));
    setUnreadCount(0);

    try {
      await notificationService.markAllNotificationsAsRead();
      toast.success('All marked as read');
    } catch {
      // Revert on error
      setNotifications(prevNotifs);
      setUnreadCount(prevCount);
      toast.error('Failed to mark all as read');
    } finally {
      setMarkingAll(false);
    }
  };

  const badgeText = unreadCount > 9 ? '9+' : unreadCount > 0 ? unreadCount.toString() : null;

  return (
    <div className="relative" ref={containerRef}>
      {/* Existing Bell Button preserved */}
      <button
        type="button"
        onClick={() => setIsOpen((prev) => !prev)}
        className="p-2 rounded-lg hover:bg-surface-100 text-surface-500 relative transition-colors focus:outline-none"
        aria-label="Notifications"
        aria-expanded={isOpen}
      >
        <Bell className="w-5 h-5" />

        {/* Unread indicator badge */}
        {badgeText && (
          <span
            className="absolute -top-0.5 -right-0.5 bg-rose-500 text-white font-bold text-[10px] min-w-[18px] h-[18px] px-1 rounded-full flex items-center justify-center border-2 border-white shadow-xs pointer-events-none"
            title={`${unreadCount} unread notification${unreadCount > 1 ? 's' : ''}`}
          >
            {badgeText}
          </span>
        )}
      </button>

      {/* Notification Dropdown Popover */}
      {isOpen && (
        <div
          className="absolute right-0 mt-2 w-80 sm:w-96 bg-white rounded-xl shadow-xl border border-surface-200 z-50 overflow-hidden animate-in fade-in zoom-in-95 duration-150 max-w-[calc(100vw-2rem)]"
          role="dialog"
          aria-label="Notification panel"
        >
          {/* Header */}
          <div className="px-4 py-3 border-b border-surface-100 flex items-center justify-between bg-surface-50/70">
            <div className="flex items-center gap-2">
              <span className="font-semibold text-surface-900 text-sm">Notifications</span>
              {unreadCount > 0 && (
                <span className="text-[11px] font-medium px-2 py-0.5 rounded-full bg-primary-100 text-primary-700">
                  {unreadCount} new
                </span>
              )}
            </div>

            {unreadCount > 0 && (
              <button
                type="button"
                onClick={handleMarkAllAsRead}
                disabled={markingAll}
                className="text-xs font-medium text-primary-600 hover:text-primary-700 hover:underline flex items-center gap-1 disabled:opacity-50 transition-colors cursor-pointer"
                title="Mark all notifications as read"
              >
                <CheckCheck className="w-3.5 h-3.5" />
                <span>Mark all as read</span>
              </button>
            )}
          </div>

          {/* Body */}
          <div className="max-h-[380px] overflow-y-auto divide-y divide-surface-100">
            {/* Loading Skeleton */}
            {loading && notifications.length === 0 && (
              <div className="p-2 space-y-2">
                {[1, 2, 3].map((i) => (
                  <div key={i} className="p-3 flex items-start gap-3 animate-pulse">
                    <div className="w-8 h-8 rounded-full bg-surface-200 shrink-0" />
                    <div className="flex-1 space-y-2">
                      <div className="h-3.5 bg-surface-200 rounded w-3/4" />
                      <div className="h-3 bg-surface-100 rounded w-full" />
                      <div className="h-2.5 bg-surface-100 rounded w-1/3" />
                    </div>
                  </div>
                ))}
              </div>
            )}

            {/* Error State */}
            {!loading && error && (
              <div className="py-8 px-4 text-center">
                <AlertCircle className="w-8 h-8 text-rose-500 mx-auto mb-2" />
                <p className="text-sm font-medium text-surface-800">Unable to load notifications.</p>
                <button
                  type="button"
                  onClick={() => fetchNotifications(true)}
                  className="mt-2.5 inline-flex items-center gap-1.5 px-3 py-1.5 text-xs font-medium text-primary-600 bg-primary-50 rounded-lg hover:bg-primary-100 transition-colors"
                >
                  <RefreshCw className="w-3.5 h-3.5" />
                  Try again
                </button>
              </div>
            )}

            {/* Empty State */}
            {!loading && !error && notifications.length === 0 && (
              <div className="py-10 px-4 text-center">
                <div className="w-12 h-12 rounded-full bg-surface-100 flex items-center justify-center mx-auto mb-3 text-surface-400">
                  <Bell className="w-6 h-6" />
                </div>
                <p className="text-sm font-semibold text-surface-800">No notifications yet</p>
                <p className="text-xs text-surface-400 mt-1">You're all caught up.</p>
              </div>
            )}

            {/* Notification List */}
            {!error &&
              notifications.map((notif) => {
                const timeAgo = formatRelativeTime(notif.created_at);
                return (
                  <div
                    key={notif.id}
                    onClick={() => handleItemClick(notif)}
                    className={`p-3.5 flex items-start gap-3 transition-colors cursor-pointer text-left ${
                      notif.is_read
                        ? 'bg-white hover:bg-surface-50/80 text-surface-600'
                        : 'bg-primary-50/40 hover:bg-primary-50/70 border-l-2 border-primary-500'
                    }`}
                  >
                    {getNotificationIcon(notif.type)}

                    <div className="flex-1 min-w-0">
                      <div className="flex items-center justify-between gap-1 mb-0.5">
                        <span
                          className={`text-xs font-semibold truncate ${
                            notif.is_read ? 'text-surface-800' : 'text-surface-950 font-bold'
                          }`}
                        >
                          {notif.title}
                        </span>
                        {!notif.is_read && (
                          <span
                            className="w-2 h-2 rounded-full bg-primary-600 shrink-0"
                            title="Unread"
                          />
                        )}
                      </div>

                      <p className="text-xs text-surface-600 leading-snug line-clamp-2">
                        {notif.message}
                      </p>

                      <div className="mt-1 flex items-center gap-1.5 text-[11px] text-surface-400">
                        <Clock className="w-3 h-3" />
                        <span>{timeAgo}</span>
                      </div>
                    </div>
                  </div>
                );
              })}
          </div>

          {/* Footer */}
          <div className="p-2 border-t border-surface-100 bg-surface-50/70 text-center">
            <button
              type="button"
              onClick={() => {
                setIsOpen(false);
                navigate(getNotificationsPath());
              }}
              className="w-full py-1.5 px-3 text-xs font-medium text-primary-600 hover:text-primary-700 hover:bg-primary-50/80 rounded-lg transition-colors flex items-center justify-center gap-1.5 cursor-pointer"
            >
              <span>View all notifications</span>
              <ChevronRight className="w-3.5 h-3.5" />
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
