/**
 * Real-time Notification Manager
 * Handles notification polling, display, and management
 */

class NotificationManager {
    constructor(options = {}) {
        this.pollInterval = options.pollInterval || 10000; // 10 seconds
        this.maxNotifications = options.maxNotifications || 50;
        this.token = localStorage.getItem('token');
        this.pollTimer = null;
        this.notifications = [];
        this.unreadCount = 0;
        this.isInitialized = false;
    }

    /**
     * Initialize notification manager and start polling
     */
    init() {
        if (this.isInitialized) return;
        
        this.createNotificationUI();
        this.startPolling();
        this.setupEventListeners();
        this.isInitialized = true;
        
        console.log('Notification manager initialized');
    }

    /**
     * Create notification UI components
     */
    createNotificationUI() {
        // Check if already exists
        if (document.getElementById('notificationBell')) {
            return;
        }

        // Create notification bell icon (accessible from navbar)
        const bellHTML = `
            <div id="notificationCenter" class="notification-center">
                <button id="notificationBell" class="notification-bell" title="Notifications">
                    <i class="fas fa-bell"></i>
                    <span class="notification-badge" id="notificationBadge" style="display: none;">0</span>
                </button>
                
                <div id="notificationDropdown" class="notification-dropdown">
                    <div class="notification-header">
                        <h3>Notifications</h3>
                        <button id="markAllRead" class="btn-small" title="Mark all as read">
                            <i class="fas fa-check-double"></i>
                        </button>
                    </div>
                    
                    <div id="notificationList" class="notification-list">
                        <div class="notification-empty">
                            <i class="fas fa-inbox"></i>
                            <p>No notifications</p>
                        </div>
                    </div>
                    
                    <div class="notification-footer">
                        <a href="#" onclick="notificationManager.openNotificationCenter(); return false;" class="view-all-link">
                            View All Notifications
                        </a>
                    </div>
                </div>
            </div>
        `;

        // Inject into body
        const container = document.createElement('div');
        container.innerHTML = bellHTML;
        document.body.insertBefore(container.firstElementChild, document.body.firstChild);

        // Add styles
        this.injectStyles();
    }

    /**
     * Inject CSS styles for notification UI
     */
    injectStyles() {
        if (document.getElementById('notificationStyles')) return;

        const style = document.createElement('style');
        style.id = 'notificationStyles';
        style.textContent = `
            .notification-center {
                position: relative;
                display: inline-block;
                margin: 0 10px;
            }

            .notification-bell {
                background: none;
                border: none;
                color: #2c3e50;
                font-size: 1.3em;
                cursor: pointer;
                position: relative;
                padding: 5px 10px;
                transition: color 0.3s ease;
            }

            [data-theme="dark"] .notification-bell {
                color: #f1f5f9;
            }

            .notification-bell:hover {
                color: #3498db;
            }

            [data-theme="dark"] .notification-bell:hover {
                color: #64b5f6;
            }

            .notification-badge {
                position: absolute;
                top: -5px;
                right: -5px;
                background: #e74c3c;
                color: white;
                border-radius: 50%;
                width: 24px;
                height: 24px;
                display: flex;
                align-items: center;
                justify-content: center;
                font-size: 0.75em;
                font-weight: bold;
            }

            .notification-dropdown {
                position: absolute;
                top: 100%;
                right: 0;
                width: 420px;
                background: white;
                border: 1px solid #ddd;
                border-radius: 8px;
                box-shadow: 0 5px 20px rgba(0, 0, 0, 0.15);
                max-height: 600px;
                overflow: hidden;
                display: none;
                z-index: 1000;
                margin-top: 10px;
            }

            [data-theme="dark"] .notification-dropdown {
                background: #1e293b;
                border-color: #334155;
                box-shadow: 0 5px 20px rgba(0, 0, 0, 0.5);
            }

            .notification-dropdown.active {
                display: flex;
                flex-direction: column;
            }

            .notification-header {
                padding: 15px;
                border-bottom: 1px solid #eee;
                display: flex;
                justify-content: space-between;
                align-items: center;
            }

            [data-theme="dark"] .notification-header {
                border-bottom-color: #334155;
            }

            .notification-header h3 {
                margin: 0;
                font-size: 1.1em;
                color: #2c3e50;
            }

            [data-theme="dark"] .notification-header h3 {
                color: #f1f5f9;
            }

            .btn-small {
                background: none;
                border: none;
                color: #3498db;
                cursor: pointer;
                font-size: 1em;
                padding: 5px 10px;
                transition: color 0.3s ease;
            }

            .btn-small:hover {
                color: #2980b9;
            }

            [data-theme="dark"] .btn-small {
                color: #64b5f6;
            }

            [data-theme="dark"] .btn-small:hover {
                color: #3a8fd8;
            }

            .notification-list {
                overflow-y: auto;
                max-height: 450px;
                flex: 1;
            }

            .notification-empty {
                padding: 40px 20px;
                text-align: center;
                color: #7f8c8d;
            }

            [data-theme="dark"] .notification-empty {
                color: #cbd5e1;
            }

            .notification-empty i {
                font-size: 2.5em;
                margin-bottom: 10px;
                opacity: 0.5;
            }

            .notification-item {
                padding: 12px 15px;
                border-bottom: 1px solid #f0f0f0;
                cursor: pointer;
                transition: background 0.2s ease;
                display: flex;
                gap: 12px;
                align-items: flex-start;
            }

            [data-theme="dark"] .notification-item {
                border-bottom-color: #334155;
            }

            .notification-item:hover {
                background: #f9fafb;
            }

            [data-theme="dark"] .notification-item:hover {
                background: #334155;
            }

            .notification-item.unread {
                background: #f0f8ff;
                font-weight: 500;
            }

            [data-theme="dark"] .notification-item.unread {
                background: #1e3a5f;
            }

            .notification-icon {
                font-size: 1.2em;
                width: 32px;
                height: 32px;
                display: flex;
                align-items: center;
                justify-content: center;
                border-radius: 50%;
                flex-shrink: 0;
            }

            .notification-icon.academic {
                background: #d5e8f7;
                color: #2980b9;
            }

            [data-theme="dark"] .notification-icon.academic {
                background: #1e3a5f;
                color: #64b5f6;
            }

            .notification-icon.alert {
                background: #fadbd8;
                color: #c0392b;
            }

            [data-theme="dark"] .notification-icon.alert {
                background: #4e342e;
                color: #ef5350;
            }

            .notification-icon.assignment {
                background: #d5f4e6;
                color: #27ae60;
            }

            [data-theme="dark"] .notification-icon.assignment {
                background: #1b5e20;
                color: #4caf50;
            }

            .notification-icon.result {
                background: #fef5e7;
                color: #f39c12;
            }

            [data-theme="dark"] .notification-icon.result {
                background: #5d4037;
                color: #ffb74d;
            }

            .notification-content {
                flex: 1;
                overflow: hidden;
            }

            .notification-title {
                font-weight: 600;
                color: #2c3e50;
                margin: 0;
                margin-bottom: 4px;
            }

            [data-theme="dark"] .notification-title {
                color: #f1f5f9;
            }

            .notification-message {
                font-size: 0.9em;
                color: #7f8c8d;
                margin: 0;
                line-height: 1.3;
                overflow: hidden;
                text-overflow: ellipsis;
                display: -webkit-box;
                -webkit-line-clamp: 2;
                -webkit-box-orient: vertical;
            }

            [data-theme="dark"] .notification-message {
                color: #cbd5e1;
            }

            .notification-time {
                font-size: 0.8em;
                color: #95a5a6;
                margin-top: 4px;
            }

            [data-theme="dark"] .notification-time {
                color: #64748b;
            }

            .notification-actions {
                display: flex;
                gap: 8px;
            }

            .notification-action {
                background: none;
                border: none;
                color: #3498db;
                cursor: pointer;
                font-size: 0.9em;
                padding: 0;
                opacity: 0;
                transition: all 0.2s ease;
            }

            .notification-item:hover .notification-action {
                opacity: 1;
            }

            .notification-action:hover {
                color: #2980b9;
                transform: scale(1.2);
            }

            [data-theme="dark"] .notification-action {
                color: #64b5f6;
            }

            [data-theme="dark"] .notification-action:hover {
                color: #3a8fd8;
            }

            .notification-footer {
                padding: 12px 15px;
                border-top: 1px solid #eee;
                text-align: center;
            }

            [data-theme="dark"] .notification-footer {
                border-top-color: #334155;
            }

            .view-all-link {
                color: #3498db;
                text-decoration: none;
                font-size: 0.95em;
                transition: color 0.2s ease;
            }

            .view-all-link:hover {
                color: #2980b9;
                text-decoration: underline;
            }

            [data-theme="dark"] .view-all-link {
                color: #64b5f6;
            }

            [data-theme="dark"] .view-all-link:hover {
                color: #3a8fd8;
            }

            @media (max-width: 600px) {
                .notification-dropdown {
                    width: 100vw;
                    max-width: none;
                    right: auto;
                    left: 0;
                    border-radius: 0;
                    max-height: 70vh;
                }
            }
        `;

        document.head.appendChild(style);
    }

    /**
     * Setup event listeners
     */
    setupEventListeners() {
        const bell = document.getElementById('notificationBell');
        const dropdown = document.getElementById('notificationDropdown');
        const markAllRead = document.getElementById('markAllRead');

        if (bell) {
            bell.addEventListener('click', (e) => {
                e.stopPropagation();
                this.toggleDropdown();
            });
        }

        if (markAllRead) {
            markAllRead.addEventListener('click', (e) => {
                e.preventDefault();
                this.markAllAsRead();
            });
        }

        // Close dropdown when clicking outside
        document.addEventListener('click', (e) => {
            if (!e.target.closest('#notificationCenter')) {
                this.closeDropdown();
            }
        });
    }

    /**
     * Toggle dropdown visibility
     */
    toggleDropdown() {
        const dropdown = document.getElementById('notificationDropdown');
        dropdown.classList.toggle('active');
    }

    /**
     * Close dropdown
     */
    closeDropdown() {
        const dropdown = document.getElementById('notificationDropdown');
        dropdown.classList.remove('active');
    }

    /**
     * Start polling for notifications
     */
    startPolling() {
        this.pollNotifications();
        this.pollTimer = setInterval(() => this.pollNotifications(), this.pollInterval);
    }

    /**
     * Stop polling
     */
    stopPolling() {
        if (this.pollTimer) {
            clearInterval(this.pollTimer);
            this.pollTimer = null;
        }
    }

    /**
     * Poll for notifications from server
     */
    async pollNotifications() {
        try {
            const response = await fetch('/api/notifications/poll', {
                headers: { 'Authorization': `Bearer ${this.token}` }
            });

            if (!response.ok) {
                if (response.status === 401) {
                    this.stopPolling();
                }
                return;
            }

            const data = await response.json();

            if (data.status === 'success') {
                this.notifications = data.notifications || [];
                this.unreadCount = data.unread_count || 0;
                this.updateUI();
            }
        } catch (error) {
            console.error('Error polling notifications:', error);
        }
    }

    /**
     * Update notification UI
     */
    updateUI() {
        this.updateBadge();
        this.updateNotificationList();
    }

    /**
     * Update badge count
     */
    updateBadge() {
        const badge = document.getElementById('notificationBadge');
        if (!badge) return;

        if (this.unreadCount > 0) {
            badge.textContent = this.unreadCount > 99 ? '99+' : this.unreadCount;
            badge.style.display = 'flex';
        } else {
            badge.style.display = 'none';
        }
    }

    /**
     * Update notification list
     */
    updateNotificationList() {
        const list = document.getElementById('notificationList');
        if (!list) return;

        if (this.notifications.length === 0) {
            list.innerHTML = `
                <div class="notification-empty">
                    <i class="fas fa-inbox"></i>
                    <p>No notifications</p>
                </div>
            `;
            return;
        }

        list.innerHTML = this.notifications.map(notif => this.createNotificationItemHTML(notif)).join('');

        // Add event listeners to actions
        list.querySelectorAll('.notification-item').forEach((item, index) => {
            const readBtn = item.querySelector('.notification-read');
            const deleteBtn = item.querySelector('.notification-delete');

            if (readBtn) {
                readBtn.addEventListener('click', (e) => {
                    e.stopPropagation();
                    const notifId = this.notifications[index].id;
                    this.markAsRead(notifId);
                });
            }

            if (deleteBtn) {
                deleteBtn.addEventListener('click', (e) => {
                    e.stopPropagation();
                    const notifId = this.notifications[index].id;
                    this.deleteNotification(notifId);
                });
            }

            // Click to view details
            item.addEventListener('click', (e) => {
                e.stopPropagation();
                if (!e.target.closest('button')) {
                    const notif = this.notifications[index];
                    if (notif.action_url) {
                        window.location.href = notif.action_url;
                    }
                }
            });
        });
    }

    /**
     * Create notification item HTML
     */
    createNotificationItemHTML(notification) {
        const iconClass = this.getIconClass(notification.type);
        const icon = this.getIcon(notification.type);
        const timeAgo = this.formatTimeAgo(notification.created_at);
        const classes = `notification-item ${notification.is_read ? '' : 'unread'}`;

        return `
            <div class="${classes}" data-id="${notification.id}">
                <div class="notification-icon ${notification.type}">
                    ${icon}
                </div>
                <div class="notification-content">
                    <p class="notification-title">${this.escapeHtml(notification.title)}</p>
                    <p class="notification-message">${this.escapeHtml(notification.message)}</p>
                    <div class="notification-time">${timeAgo}</div>
                </div>
                <div class="notification-actions">
                    ${!notification.is_read ? '<button class="notification-action notification-read" title="Mark as read"><i class="fas fa-envelope-open"></i></button>' : ''}
                    <button class="notification-action notification-delete" title="Delete"><i class="fas fa-trash"></i></button>
                </div>
            </div>
        `;
    }

    /**
     * Get icon for notification type
     */
    getIcon(type) {
        const icons = {
            'academic': '<i class="fas fa-graduation-cap"></i>',
            'system': '<i class="fas fa-bell"></i>',
            'alert': '<i class="fas fa-exclamation-circle"></i>',
            'assignment': '<i class="fas fa-tasks"></i>',
            'result': '<i class="fas fa-check-circle"></i>',
            'attendance': '<i class="fas fa-calendar-check"></i>'
        };
        return icons[type] || icons['system'];
    }

    /**
     * Mark notification as read
     */
    async markAsRead(notificationId) {
        try {
            const response = await fetch(`/api/notifications/${notificationId}/read`, {
                method: 'PUT',
                headers: { 'Authorization': `Bearer ${this.token}` }
            });

            if (response.ok) {
                this.pollNotifications();
            }
        } catch (error) {
            console.error('Error marking notification as read:', error);
        }
    }

    /**
     * Mark all as read
     */
    async markAllAsRead() {
        try {
            const response = await fetch('/api/notifications/mark-all-read', {
                method: 'PUT',
                headers: { 'Authorization': `Bearer ${this.token}` }
            });

            if (response.ok) {
                this.pollNotifications();
            }
        } catch (error) {
            console.error('Error marking all as read:', error);
        }
    }

    /**
     * Delete notification
     */
    async deleteNotification(notificationId) {
        try {
            const response = await fetch(`/api/notifications/${notificationId}`, {
                method: 'DELETE',
                headers: { 'Authorization': `Bearer ${this.token}` }
            });

            if (response.ok) {
                this.pollNotifications();
            }
        } catch (error) {
            console.error('Error deleting notification:', error);
        }
    }

    /**
     * Open full notification center
     */
    openNotificationCenter() {
        window.location.href = '/notifications';
        this.closeDropdown();
    }

    /**
     * Format time ago
     */
    formatTimeAgo(dateString) {
        if (typeof moment !== 'undefined') {
            return moment(dateString).fromNow();
        }

        const date = new Date(dateString);
        const seconds = Math.floor((new Date() - date) / 1000);

        if (seconds < 60) return 'Just now';
        if (seconds < 3600) return Math.floor(seconds / 60) + 'm ago';
        if (seconds < 86400) return Math.floor(seconds / 3600) + 'h ago';
        return Math.floor(seconds / 86400) + 'd ago';
    }

    /**
     * Escape HTML to prevent XSS
     */
    escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }
}

// Initialize notification manager on page load
const notificationManager = new NotificationManager();
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', () => notificationManager.init());
} else {
    notificationManager.init();
}
