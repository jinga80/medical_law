/**
 * 실시간 채팅 시스템 JavaScript 클라이언트
 */

class RealtimeChatManager {
    constructor(roomId, options = {}) {
        this.roomId = roomId;
        this.socket = null;
        this.isConnected = false;
        this.isTyping = false;
        this.typingTimeout = null;
        this.messages = [];
        this.participants = [];
        
        // 옵션 설정
        this.options = {
            container: options.container || '.chat-container',
            messageList: options.messageList || '.chat-messages',
            inputField: options.inputField || '.chat-input',
            sendButton: options.sendButton || '.chat-send',
            participantsList: options.participantsList || '.chat-participants',
            typingIndicator: options.typingIndicator || '.chat-typing',
            ...options
        };
        
        this.init();
    }
    
    init() {
        this.connect();
        this.setupEventListeners();
        this.setupUI();
    }
    
    connect() {
        const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
        const wsUrl = `${protocol}//${window.location.host}/ws/chat/${this.roomId}/`;
        
        this.socket = new WebSocket(wsUrl);
        
        this.socket.onopen = (event) => {
            console.log(`채팅방 ${this.roomId} 연결됨`);
            this.isConnected = true;
            this.updateConnectionStatus(true);
        };
        
        this.socket.onmessage = (event) => {
            const data = JSON.parse(event.data);
            this.handleMessage(data);
        };
        
        this.socket.onclose = (event) => {
            console.log(`채팅방 ${this.roomId} 연결 해제됨`);
            this.isConnected = false;
            this.updateConnectionStatus(false);
        };
        
        this.socket.onerror = (error) => {
            console.error(`채팅방 ${this.roomId} 오류:`, error);
        };
    }
    
    setupEventListeners() {
        const inputField = document.querySelector(this.options.inputField);
        const sendButton = document.querySelector(this.options.sendButton);
        
        if (inputField) {
            // 엔터키로 메시지 전송
            inputField.addEventListener('keypress', (e) => {
                if (e.key === 'Enter' && !e.shiftKey) {
                    e.preventDefault();
                    this.sendMessage();
                }
            });
            
            // 타이핑 상태 전송
            inputField.addEventListener('input', () => {
                this.handleTyping();
            });
            
            // 포커스 해제 시 타이핑 중지
            inputField.addEventListener('blur', () => {
                this.stopTyping();
            });
        }
        
        if (sendButton) {
            sendButton.addEventListener('click', () => {
                this.sendMessage();
            });
        }
        
        // 페이지 언로드 시 연결 해제
        window.addEventListener('beforeunload', () => {
            this.disconnect();
        });
    }
    
    setupUI() {
        // 채팅 컨테이너에 roomId 속성 추가
        const container = document.querySelector(this.options.container);
        if (container) {
            container.setAttribute('data-chat-room', this.roomId);
        }
        
        // 연결 상태 표시
        this.createConnectionIndicator();
        
        // 메시지 전송 폼 설정
        this.setupMessageForm();
    }
    
    createConnectionIndicator() {
        const container = document.querySelector(this.options.container);
        if (!container) return;
        
        const indicator = document.createElement('div');
        indicator.className = 'chat-connection-indicator';
        indicator.innerHTML = `
            <div class="connection-status">
                <span class="status-dot"></span>
                <span class="status-text">연결 중...</span>
            </div>
        `;
        
        container.appendChild(indicator);
        this.connectionIndicator = indicator;
    }
    
    setupMessageForm() {
        const inputField = document.querySelector(this.options.inputField);
        const sendButton = document.querySelector(this.options.sendButton);
        
        if (inputField && sendButton) {
            // 입력 필드 상태에 따라 전송 버튼 활성화/비활성화
            inputField.addEventListener('input', () => {
                const hasContent = inputField.value.trim().length > 0;
                sendButton.disabled = !hasContent || !this.isConnected;
            });
        }
    }
    
    handleMessage(data) {
        switch (data.type) {
            case 'chat_connection_established':
                console.log('채팅 연결 성립:', data.message);
                this.updateConnectionStatus(true);
                break;
                
            case 'participants_list':
                this.updateParticipantsList(data.participants);
                break;
                
            case 'chat_message':
                this.addMessage(data);
                break;
                
            case 'user_typing':
                this.handleUserTyping(data);
                break;
                
            case 'user_joined':
                this.handleUserJoined(data);
                break;
                
            case 'user_left':
                this.handleUserLeft(data);
                break;
                
            case 'chat_history':
                this.loadChatHistory(data.messages);
                break;
                
            case 'error':
                this.showError(data.message);
                break;
                
            default:
                console.log('알 수 없는 채팅 메시지 타입:', data.type);
        }
    }
    
    sendMessage() {
        const inputField = document.querySelector(this.options.inputField);
        if (!inputField || !this.isConnected) return;
        
        const content = inputField.value.trim();
        if (!content) return;
        
        // 메시지 전송
        this.socket.send(JSON.stringify({
            type: 'chat_message',
            content: content
        }));
        
        // 입력 필드 초기화
        inputField.value = '';
        inputField.focus();
        
        // 타이핑 중지
        this.stopTyping();
        
        // 전송 버튼 비활성화
        const sendButton = document.querySelector(this.options.sendButton);
        if (sendButton) {
            sendButton.disabled = true;
        }
    }
    
    handleTyping() {
        if (!this.isTyping) {
            this.isTyping = true;
            this.socket.send(JSON.stringify({
                type: 'typing'
            }));
        }
        
        // 타이핑 타임아웃 리셋
        if (this.typingTimeout) {
            clearTimeout(this.typingTimeout);
        }
        
        this.typingTimeout = setTimeout(() => {
            this.stopTyping();
        }, 3000);
    }
    
    stopTyping() {
        if (this.isTyping) {
            this.isTyping = false;
            this.socket.send(JSON.stringify({
                type: 'stop_typing'
            }));
        }
        
        if (this.typingTimeout) {
            clearTimeout(this.typingTimeout);
            this.typingTimeout = null;
        }
    }
    
    addMessage(data) {
        const messageList = document.querySelector(this.options.messageList);
        if (!messageList) return;
        
        const messageElement = this.createMessageElement(data);
        messageList.appendChild(messageElement);
        
        // 스크롤을 맨 아래로
        messageList.scrollTop = messageList.scrollHeight;
        
        // 메시지 목록에 추가
        this.messages.push(data);
        
        // 메시지 읽음 표시
        this.markMessagesAsRead();
    }
    
    createMessageElement(data) {
        const messageDiv = document.createElement('div');
        messageDiv.className = 'chat-message';
        
        const isOwnMessage = data.sender_id === this.getCurrentUserId();
        const messageClass = isOwnMessage ? 'own-message' : 'other-message';
        
        messageDiv.innerHTML = `
            <div class="chat-message-content ${messageClass}">
                <div class="message-header">
                    <span class="sender-name">${data.sender_name}</span>
                    <span class="message-time">${this.formatTime(data.timestamp)}</span>
                </div>
                <div class="message-body">
                    ${this.escapeHtml(data.content)}
                </div>
                ${data.is_edited ? '<small class="text-muted">수정됨</small>' : ''}
            </div>
        `;
        
        return messageDiv;
    }
    
    handleUserTyping(data) {
        const typingIndicator = document.querySelector(this.options.typingIndicator);
        if (!typingIndicator) return;
        
        if (data.is_typing) {
            typingIndicator.innerHTML = `<small class="text-muted">${data.user_name}님이 입력 중...</small>`;
            typingIndicator.style.display = 'block';
        } else {
            typingIndicator.style.display = 'none';
        }
    }
    
    handleUserJoined(data) {
        // 참여자 목록 업데이트
        this.addParticipant(data);
        
        // 시스템 메시지 표시
        this.addSystemMessage(`${data.user_name}님이 참여했습니다.`, 'join');
    }
    
    handleUserLeft(data) {
        // 참여자 목록에서 제거
        this.removeParticipant(data.user_id);
        
        // 시스템 메시지 표시
        this.addSystemMessage(`${data.user_name}님이 나갔습니다.`, 'leave');
    }
    
    addSystemMessage(message, type = 'info') {
        const messageList = document.querySelector(this.options.messageList);
        if (!messageList) return;
        
        const messageDiv = document.createElement('div');
        messageDiv.className = 'chat-system-message';
        
        const typeClass = type === 'join' ? 'text-success' : type === 'leave' ? 'text-muted' : 'text-info';
        
        messageDiv.innerHTML = `
            <div class="system-message ${typeClass}">
                <small>${message}</small>
            </div>
        `;
        
        messageList.appendChild(messageDiv);
        messageList.scrollTop = messageList.scrollHeight;
    }
    
    updateParticipantsList(participants) {
        this.participants = participants;
        
        const participantsList = document.querySelector(this.options.participantsList);
        if (!participantsList) return;
        
        participantsList.innerHTML = '';
        
        participants.forEach(participant => {
            const participantElement = document.createElement('div');
            participantElement.className = 'chat-participant';
            participantElement.innerHTML = `
                <div class="participant-info">
                    <span class="participant-name">${participant.user_name}</span>
                    <span class="participant-role badge bg-secondary">${this.getRoleDisplay(participant.role)}</span>
                </div>
            `;
            participantsList.appendChild(participantElement);
        });
    }
    
    addParticipant(participant) {
        const existingIndex = this.participants.findIndex(p => p.user_id === participant.user_id);
        if (existingIndex === -1) {
            this.participants.push(participant);
            this.updateParticipantsList(this.participants);
        }
    }
    
    removeParticipant(userId) {
        this.participants = this.participants.filter(p => p.user_id !== userId);
        this.updateParticipantsList(this.participants);
    }
    
    loadChatHistory(messages) {
        const messageList = document.querySelector(this.options.messageList);
        if (!messageList) return;
        
        // 기존 메시지 제거
        messageList.innerHTML = '';
        
        // 히스토리 메시지 추가
        messages.forEach(message => {
            this.addMessage(message);
        });
    }
    
    markMessagesAsRead() {
        if (this.socket && this.socket.readyState === WebSocket.OPEN) {
            this.socket.send(JSON.stringify({
                type: 'mark_messages_read'
            }));
        }
    }
    
    requestChatHistory() {
        if (this.socket && this.socket.readyState === WebSocket.OPEN) {
            this.socket.send(JSON.stringify({
                type: 'get_chat_history'
            }));
        }
    }
    
    updateConnectionStatus(connected) {
        if (this.connectionIndicator) {
            const statusDot = this.connectionIndicator.querySelector('.status-dot');
            const statusText = this.connectionIndicator.querySelector('.status-text');
            
            if (connected) {
                statusDot.className = 'status-dot connected';
                statusText.textContent = '연결됨';
            } else {
                statusDot.className = 'status-dot disconnected';
                statusText.textContent = '연결 해제됨';
            }
        }
        
        // 전송 버튼 상태 업데이트
        const sendButton = document.querySelector(this.options.sendButton);
        if (sendButton) {
            sendButton.disabled = !connected;
        }
    }
    
    showError(message) {
        // 에러 메시지 표시
        this.addSystemMessage(`오류: ${message}`, 'error');
    }
    
    disconnect() {
        if (this.socket) {
            this.socket.close();
        }
    }
    
    // 유틸리티 메서드들
    getCurrentUserId() {
        // 현재 사용자 ID를 가져오는 방법 (페이지에서 설정된 변수 사용)
        return window.currentUserId || null;
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
            return date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
        } else {
            return date.toLocaleDateString();
        }
    }
    
    getRoleDisplay(role) {
        const roleMap = {
            'admin': '관리자',
            'moderator': '운영자',
            'member': '멤버',
            'guest': '게스트'
        };
        return roleMap[role] || role;
    }
    
    escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }
}

// 채팅 스타일 CSS 추가
const chatStyles = `
<style>
.chat-container {
    display: flex;
    flex-direction: column;
    height: 500px;
    border: 1px solid #dee2e6;
    border-radius: 0.375rem;
}

.chat-header {
    padding: 1rem;
    background-color: #f8f9fa;
    border-bottom: 1px solid #dee2e6;
    border-radius: 0.375rem 0.375rem 0 0;
}

.chat-messages {
    flex: 1;
    overflow-y: auto;
    padding: 1rem;
    background-color: #fff;
}

.chat-message {
    margin-bottom: 1rem;
}

.chat-message-content {
    max-width: 70%;
    padding: 0.5rem 1rem;
    border-radius: 1rem;
    word-wrap: break-word;
}

.own-message {
    margin-left: auto;
    background-color: #007bff;
    color: white;
}

.other-message {
    margin-right: auto;
    background-color: #f8f9fa;
    border: 1px solid #dee2e6;
}

.chat-system-message {
    text-align: center;
    margin: 0.5rem 0;
}

.chat-input-area {
    padding: 1rem;
    background-color: #f8f9fa;
    border-top: 1px solid #dee2e6;
    border-radius: 0 0 0.375rem 0.375rem;
}

.chat-input {
    width: 100%;
    padding: 0.5rem;
    border: 1px solid #ced4da;
    border-radius: 0.375rem;
    resize: none;
}

.chat-send {
    margin-top: 0.5rem;
    width: 100%;
}

.chat-participants {
    padding: 1rem;
    background-color: #f8f9fa;
    border-left: 1px solid #dee2e6;
}

.chat-participant {
    padding: 0.5rem 0;
    border-bottom: 1px solid #dee2e6;
}

.chat-connection-indicator {
    position: absolute;
    top: 0.5rem;
    right: 0.5rem;
    z-index: 1000;
}

.connection-status {
    display: flex;
    align-items: center;
    gap: 0.5rem;
    font-size: 0.875rem;
}

.status-dot {
    width: 8px;
    height: 8px;
    border-radius: 50%;
    background-color: #6c757d;
}

.status-dot.connected {
    background-color: #28a745;
}

.status-dot.disconnected {
    background-color: #dc3545;
}

.chat-typing {
    padding: 0.5rem 1rem;
    font-style: italic;
    color: #6c757d;
    display: none;
}

.message-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 0.25rem;
    font-size: 0.875rem;
}

.sender-name {
    font-weight: 600;
}

.message-time {
    opacity: 0.7;
}

.message-body {
    line-height: 1.4;
}

.system-message {
    text-align: center;
    padding: 0.5rem;
    background-color: #f8f9fa;
    border-radius: 0.375rem;
    font-size: 0.875rem;
}
</style>
`;

// 스타일 추가
document.head.insertAdjacentHTML('beforeend', chatStyles);

// 전역 함수로 채팅 매니저 생성
window.createChatManager = function(roomId, options) {
    return new RealtimeChatManager(roomId, options);
}; 