/**
 * 실시간 알림 시스템 JavaScript 클라이언트
 */

class RealtimeNotificationManager {
    constructor() {
        this.notificationSocket = null;
        this.workflowSocket = null;
        this.chatSockets = new Map();
        this.isConnected = false;
        this.reconnectAttempts = 0;
        this.maxReconnectAttempts = 5;
        this.reconnectDelay = 1000;
        this.notificationCount = 0;
        this.unreadNotifications = [];
        
        this.init();
    }
    
    init() {
        this.setupNotificationSocket();
        this.setupWorkflowSocket();
        this.setupNotificationUI();
        this.setupEventListeners();
    }
    
    setupNotificationSocket() {
        const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
        const wsUrl = `${protocol}//${window.location.host}/ws/notifications/`;
        
        this.notificationSocket = new WebSocket(wsUrl);
        
        this.notificationSocket.onopen = (event) => {
            console.log('알림 WebSocket 연결됨');
            this.isConnected = true;
            this.reconnectAttempts = 0;
            this.updateConnectionStatus(true);
        };
        
        this.notificationSocket.onmessage = (event) => {
            const data = JSON.parse(event.data);
            this.handleNotificationMessage(data);
        };
        
        this.notificationSocket.onclose = (event) => {
            console.log('알림 WebSocket 연결 해제됨');
            this.isConnected = false;
            this.updateConnectionStatus(false);
            this.scheduleReconnect();
        };
        
        this.notificationSocket.onerror = (error) => {
            console.error('알림 WebSocket 오류:', error);
        };
    }
    
    setupWorkflowSocket() {
        const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
        const wsUrl = `${protocol}//${window.location.host}/ws/workflow/`;
        
        this.workflowSocket = new WebSocket(wsUrl);
        
        this.workflowSocket.onopen = (event) => {
            console.log('워크플로우 WebSocket 연결됨');
        };
        
        this.workflowSocket.onmessage = (event) => {
            const data = JSON.parse(event.data);
            this.handleWorkflowMessage(data);
        };
        
        this.workflowSocket.onclose = (event) => {
            console.log('워크플로우 WebSocket 연결 해제됨');
        };
        
        this.workflowSocket.onerror = (error) => {
            console.error('워크플로우 WebSocket 오류:', error);
        };
    }
    
    setupNotificationUI() {
        // 알림 아이콘 생성
        this.createNotificationIcon();
        
        // 알림 드롭다운 생성
        this.createNotificationDropdown();
        
        // 알림 토스트 컨테이너 생성
        this.createToastContainer();
    }
    
    createNotificationIcon() {
        const navbar = document.querySelector('.navbar-nav');
        if (!navbar) return;
        
        const notificationItem = document.createElement('li');
        notificationItem.className = 'nav-item dropdown';
        notificationItem.innerHTML = `
            <a class="nav-link dropdown-toggle position-relative" href="#" id="notificationDropdown" role="button" data-bs-toggle="dropdown" aria-expanded="false">
                <i class="mdi mdi-bell"></i>
                <span class="position-absolute top-0 start-100 translate-middle badge rounded-pill bg-danger notification-badge" style="display: none;">
                    0
                </span>
            </a>
            <ul class="dropdown-menu dropdown-menu-end notification-dropdown" aria-labelledby="notificationDropdown" style="width: 350px; max-height: 400px; overflow-y: auto;">
                <li><h6 class="dropdown-header">알림</h6></li>
                <li><hr class="dropdown-divider"></li>
                <li class="notification-list"></li>
                <li><hr class="dropdown-divider"></li>
                <li><a class="dropdown-item text-center" href="/notifications/">모든 알림 보기</a></li>
            </ul>
        `;
        
        navbar.appendChild(notificationItem);
        
        this.notificationBadge = notificationItem.querySelector('.notification-badge');
        this.notificationList = notificationItem.querySelector('.notification-list');
    }
    
    createNotificationDropdown() {
        // 알림 드롭다운은 이미 createNotificationIcon에서 생성됨
    }
    
    createToastContainer() {
        const toastContainer = document.createElement('div');
        toastContainer.className = 'toast-container position-fixed top-0 end-0 p-3';
        toastContainer.style.zIndex = '9999';
        document.body.appendChild(toastContainer);
        
        this.toastContainer = toastContainer;
    }
    
    setupEventListeners() {
        // 페이지 언로드 시 WebSocket 연결 해제
        window.addEventListener('beforeunload', () => {
            this.disconnect();
        });
        
        // 알림 클릭 이벤트
        document.addEventListener('click', (e) => {
            if (e.target.closest('.notification-item')) {
                const notificationId = e.target.closest('.notification-item').dataset.notificationId;
                this.markNotificationAsRead(notificationId);
            }
        });
        
        // 모든 알림 읽음 처리
        document.addEventListener('click', (e) => {
            if (e.target.closest('.mark-all-read')) {
                this.markAllNotificationsAsRead();
            }
        });
    }
    
    handleNotificationMessage(data) {
        switch (data.type) {
            case 'connection_established':
                console.log('알림 WebSocket 연결 성립:', data.message);
                break;
                
            case 'unread_count':
                this.updateNotificationCount(data.count);
                break;
                
            case 'notification':
                this.addNotification(data);
                this.showToast(data);
                break;
                
            case 'urgent_notification':
                this.addUrgentNotification(data);
                this.showUrgentToast(data);
                break;
                
            case 'notification_stats':
                this.updateNotificationStats(data);
                break;
                
            case 'pong':
                // 연결 상태 확인 응답
                break;
                
            default:
                console.log('알 수 없는 알림 메시지 타입:', data.type);
        }
    }
    
    handleWorkflowMessage(data) {
        switch (data.type) {
            case 'workflow_connection_established':
                console.log('워크플로우 WebSocket 연결 성립:', data.message);
                break;
                
            case 'workflow_status_update':
                this.handleWorkflowUpdate(data);
                break;
                
            case 'task_assignment':
                this.handleTaskAssignment(data);
                break;
                
            case 'deadline_reminder':
                this.handleDeadlineReminder(data);
                break;
                
            default:
                console.log('알 수 없는 워크플로우 메시지 타입:', data.type);
        }
    }
    
    addNotification(data) {
        // 알림 목록에 추가
        const notificationItem = this.createNotificationItem(data);
        this.notificationList.insertBefore(notificationItem, this.notificationList.firstChild);
        
        // 최대 10개까지만 표시
        const items = this.notificationList.querySelectorAll('.notification-item');
        if (items.length > 10) {
            items[items.length - 1].remove();
        }
        
        // 읽지 않은 알림 개수 증가
        this.notificationCount++;
        this.updateNotificationBadge();
        
        // 읽지 않은 알림 목록에 추가
        this.unreadNotifications.push(data);
    }
    
    addUrgentNotification(data) {
        // 긴급 알림은 별도 처리
        this.addNotification(data);
        
        // 브라우저 알림 표시
        this.showBrowserNotification(data);
    }
    
    createNotificationItem(data) {
        const item = document.createElement('li');
        item.className = 'notification-item';
        item.dataset.notificationId = data.id;
        
        const priorityClass = this.getPriorityClass(data.priority);
        const icon = this.getNotificationIcon(data.notification_type);
        
        item.innerHTML = `
            <a class="dropdown-item d-flex align-items-center py-2 ${priorityClass}" href="${data.action_url || '#'}">
                <div class="flex-shrink-0">
                    <i class="${icon} me-2"></i>
                </div>
                <div class="flex-grow-1">
                    <div class="fw-bold small">${data.title}</div>
                    <div class="small text-muted">${data.message}</div>
                    <div class="small text-muted">${this.formatTime(data.timestamp)}</div>
                </div>
                ${data.action_required ? '<span class="badge bg-warning ms-2">액션 필요</span>' : ''}
            </a>
        `;
        
        return item;
    }
    
    getPriorityClass(priority) {
        const classes = {
            'low': 'text-muted',
            'normal': '',
            'high': 'text-warning',
            'urgent': 'text-danger fw-bold'
        };
        return classes[priority] || '';
    }
    
    getNotificationIcon(type) {
        const icons = {
            'job_request_submitted': 'mdi mdi-file-document-plus',
            'job_request_accepted': 'mdi mdi-check-circle',
            'candidate_recommended': 'mdi mdi-account-plus',
            'document_review_completed': 'mdi mdi-file-check',
            'interview_scheduled': 'mdi mdi-calendar-clock',
            'interview_completed': 'mdi mdi-calendar-check',
            'final_decision_made': 'mdi mdi-flag-checkered',
            'workflow_step_completed': 'mdi mdi-progress-clock',
            'system_notification': 'mdi mdi-bell-ring',
            'reminder': 'mdi mdi-alarm'
        };
        return icons[type] || 'mdi mdi-bell';
    }
    
    showToast(data) {
        const toast = document.createElement('div');
        toast.className = 'toast';
        toast.setAttribute('role', 'alert');
        toast.setAttribute('aria-live', 'assertive');
        toast.setAttribute('aria-atomic', 'true');
        
        const priorityClass = this.getPriorityClass(data.priority);
        const icon = this.getNotificationIcon(data.notification_type);
        
        toast.innerHTML = `
            <div class="toast-header ${priorityClass}">
                <i class="${icon} me-2"></i>
                <strong class="me-auto">${data.title}</strong>
                <small>${this.formatTime(data.timestamp)}</small>
                <button type="button" class="btn-close" data-bs-dismiss="toast" aria-label="Close"></button>
            </div>
            <div class="toast-body">
                ${data.message}
                ${data.action_required ? '<br><small class="text-warning"><i class="mdi mdi-alert"></i> 액션이 필요합니다.</small>' : ''}
            </div>
        `;
        
        this.toastContainer.appendChild(toast);
        
        const bsToast = new bootstrap.Toast(toast, {
            autohide: true,
            delay: 5000
        });
        
        bsToast.show();
        
        // 5초 후 자동 제거
        setTimeout(() => {
            if (toast.parentNode) {
                toast.parentNode.removeChild(toast);
            }
        }, 5000);
    }
    
    showUrgentToast(data) {
        // 긴급 알림은 더 오래 표시
        const toast = document.createElement('div');
        toast.className = 'toast border-danger';
        toast.setAttribute('role', 'alert');
        toast.setAttribute('aria-live', 'assertive');
        toast.setAttribute('aria-atomic', 'true');
        
        toast.innerHTML = `
            <div class="toast-header bg-danger text-white">
                <i class="mdi mdi-alert-circle me-2"></i>
                <strong class="me-auto">긴급: ${data.title}</strong>
                <small>${this.formatTime(data.timestamp)}</small>
                <button type="button" class="btn-close btn-close-white" data-bs-dismiss="toast" aria-label="Close"></button>
            </div>
            <div class="toast-body">
                ${data.message}
                <br><small class="text-danger"><i class="mdi mdi-alert"></i> 즉시 확인이 필요합니다.</small>
            </div>
        `;
        
        this.toastContainer.appendChild(toast);
        
        const bsToast = new bootstrap.Toast(toast, {
            autohide: true,
            delay: 10000
        });
        
        bsToast.show();
        
        // 10초 후 자동 제거
        setTimeout(() => {
            if (toast.parentNode) {
                toast.parentNode.removeChild(toast);
            }
        }, 10000);
    }
    
    showBrowserNotification(data) {
        if ('Notification' in window && Notification.permission === 'granted') {
            new Notification(data.title, {
                body: data.message,
                icon: '/static/images/logo.png',
                tag: data.id,
                requireInteraction: data.priority === 'urgent'
            });
        }
    }
    
    updateNotificationCount(count) {
        this.notificationCount = count;
        this.updateNotificationBadge();
    }
    
    updateNotificationBadge() {
        if (this.notificationBadge) {
            if (this.notificationCount > 0) {
                this.notificationBadge.textContent = this.notificationCount;
                this.notificationBadge.style.display = 'block';
            } else {
                this.notificationBadge.style.display = 'none';
            }
        }
    }
    
    updateConnectionStatus(connected) {
        // 연결 상태 표시 (선택사항)
        if (connected) {
            console.log('실시간 알림 연결됨');
        } else {
            console.log('실시간 알림 연결 해제됨');
        }
    }
    
    markNotificationAsRead(notificationId) {
        if (this.notificationSocket && this.notificationSocket.readyState === WebSocket.OPEN) {
            this.notificationSocket.send(JSON.stringify({
                type: 'mark_as_read',
                notification_id: notificationId
            }));
        }
    }
    
    markAllNotificationsAsRead() {
        if (this.notificationSocket && this.notificationSocket.readyState === WebSocket.OPEN) {
            this.notificationSocket.send(JSON.stringify({
                type: 'mark_all_as_read'
            }));
        }
    }
    
    getNotificationStats() {
        if (this.notificationSocket && this.notificationSocket.readyState === WebSocket.OPEN) {
            this.notificationSocket.send(JSON.stringify({
                type: 'get_notification_stats'
            }));
        }
    }
    
    handleWorkflowUpdate(data) {
        // 워크플로우 업데이트 처리
        console.log('워크플로우 업데이트:', data);
        
        // 대시보드가 있는 경우 업데이트
        const dashboard = document.querySelector('.workflow-progress');
        if (dashboard) {
            this.updateWorkflowProgress(data);
        }
    }
    
    handleTaskAssignment(data) {
        // 작업 할당 알림 처리
        console.log('작업 할당:', data);
        
        // 작업 할당 알림 표시
        this.showToast({
            title: '새 작업 할당',
            message: `"${data.task_name}" 작업이 할당되었습니다.`,
            priority: 'normal',
            timestamp: data.timestamp
        });
    }
    
    handleDeadlineReminder(data) {
        // 마감일 리마인더 처리
        console.log('마감일 리마인더:', data);
        
        // 마감일 리마인더 알림 표시
        this.showUrgentToast({
            title: '마감일 임박',
            message: `"${data.workflow_name}"의 마감일이 ${data.days_remaining}일 남았습니다.`,
            priority: 'high',
            timestamp: data.timestamp
        });
    }
    
    updateWorkflowProgress(data) {
        // 워크플로우 진행률 업데이트
        const progressElement = document.querySelector(`[data-workflow-id="${data.workflow_id}"] .progress-bar`);
        if (progressElement) {
            progressElement.style.width = `${data.progress}%`;
            progressElement.textContent = `${data.progress}%`;
        }
    }
    
    scheduleReconnect() {
        if (this.reconnectAttempts < this.maxReconnectAttempts) {
            this.reconnectAttempts++;
            setTimeout(() => {
                console.log(`재연결 시도 ${this.reconnectAttempts}/${this.maxReconnectAttempts}`);
                this.setupNotificationSocket();
            }, this.reconnectDelay * this.reconnectAttempts);
        }
    }
    
    disconnect() {
        if (this.notificationSocket) {
            this.notificationSocket.close();
        }
        if (this.workflowSocket) {
            this.workflowSocket.close();
        }
        
        // 채팅 소켓들도 모두 닫기
        this.chatSockets.forEach(socket => {
            socket.close();
        });
        this.chatSockets.clear();
    }
    
    formatTime(timestamp) {
        const date = new Date(timestamp);
        const now = new Date();
        const diff = now - date;
        
        if (diff < 60000) { // 1분 미만
            return '방금 전';
        } else if (diff < 3600000) { // 1시간 미만
            return `${Math.floor(diff / 60000)}분 전`;
        } else if (diff < 86400000) { // 1일 미만
            return `${Math.floor(diff / 3600000)}시간 전`;
        } else {
            return date.toLocaleDateString();
        }
    }
    
    // 채팅 관련 메서드들
    connectToChat(roomId) {
        if (this.chatSockets.has(roomId)) {
            return this.chatSockets.get(roomId);
        }
        
        const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
        const wsUrl = `${protocol}//${window.location.host}/ws/chat/${roomId}/`;
        
        const chatSocket = new WebSocket(wsUrl);
        
        chatSocket.onopen = (event) => {
            console.log(`채팅방 ${roomId} 연결됨`);
        };
        
        chatSocket.onmessage = (event) => {
            const data = JSON.parse(event.data);
            this.handleChatMessage(roomId, data);
        };
        
        chatSocket.onclose = (event) => {
            console.log(`채팅방 ${roomId} 연결 해제됨`);
            this.chatSockets.delete(roomId);
        };
        
        this.chatSockets.set(roomId, chatSocket);
        return chatSocket;
    }
    
    handleChatMessage(roomId, data) {
        // 채팅 메시지 처리 (채팅 UI가 있는 경우)
        const chatContainer = document.querySelector(`[data-chat-room="${roomId}"]`);
        if (chatContainer) {
            this.addChatMessage(chatContainer, data);
        }
    }
    
    addChatMessage(container, data) {
        const messageElement = document.createElement('div');
        messageElement.className = 'chat-message';
        
        if (data.type === 'chat_message') {
            messageElement.innerHTML = `
                <div class="chat-message-content">
                    <strong>${data.sender_name}:</strong> ${data.content}
                    <small class="text-muted">${this.formatTime(data.timestamp)}</small>
                </div>
            `;
        } else if (data.type === 'user_joined') {
            messageElement.innerHTML = `
                <div class="chat-system-message text-info">
                    <small>${data.user_name}님이 참여했습니다.</small>
                </div>
            `;
        } else if (data.type === 'user_left') {
            messageElement.innerHTML = `
                <div class="chat-system-message text-muted">
                    <small>${data.user_name}님이 나갔습니다.</small>
                </div>
            `;
        }
        
        container.appendChild(messageElement);
        container.scrollTop = container.scrollHeight;
    }
    
    sendChatMessage(roomId, content) {
        const socket = this.chatSockets.get(roomId);
        if (socket && socket.readyState === WebSocket.OPEN) {
            socket.send(JSON.stringify({
                type: 'chat_message',
                content: content
            }));
        }
    }
}

// 페이지 로드 시 실시간 알림 매니저 초기화
document.addEventListener('DOMContentLoaded', function() {
    window.realtimeNotificationManager = new RealtimeNotificationManager();
});

// 브라우저 알림 권한 요청
if ('Notification' in window) {
    if (Notification.permission === 'default') {
        Notification.requestPermission();
    }
} 