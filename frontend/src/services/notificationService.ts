import api from './api';
import type { NotificationItem, UnreadCountResponse } from '../types';

export const notificationService = {
  /**
   * Fetch all notifications for the authenticated user, newest first.
   */
  async getNotifications(
    limit: number = 50,
    page: number = 1,
    unread_only?: boolean,
    type?: string
  ): Promise<NotificationItem[]> {
    const params: Record<string, any> = { limit, page };
    if (unread_only !== undefined) {
      params.unread_only = unread_only;
    }
    if (type && type !== 'all') {
      params.type = type;
    }
    const response = await api.get<NotificationItem[]>('/api/notifications', {
      params,
    });
    return response.data;
  },

  /**
   * Fetch unread notification count for the authenticated user.
   */
  async getUnreadNotificationCount(): Promise<number> {
    const response = await api.get<UnreadCountResponse>('/api/notifications/unread-count');
    return response.data.count;
  },

  /**
   * Mark a single notification as read.
   */
  async markNotificationAsRead(id: string): Promise<NotificationItem> {
    const response = await api.patch<NotificationItem>(`/api/notifications/${id}/read`);
    return response.data;
  },

  /**
   * Mark all notifications for the authenticated user as read.
   */
  async markAllNotificationsAsRead(): Promise<{ message: string; updated_count: number }> {
    const response = await api.patch<{ message: string; updated_count: number }>('/api/notifications/read-all');
    return response.data;
  },
};

export default notificationService;
