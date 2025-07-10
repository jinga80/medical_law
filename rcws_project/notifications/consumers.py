import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.utils import timezone
from .models import Notification, ChatRoom, ChatMessage, ChatRoomParticipant


class NotificationConsumer(AsyncWebsocketConsumer):
    """실시간 알림을 위한 WebSocket Consumer"""
    
    async def connect(self):
        """WebSocket 연결"""
        self.user = self.scope["user"]
        
        # 인증되지 않은 사용자는 연결 거부
        if not self.user.is_authenticated:
            await self.close()
            return
        
        # 사용자별 그룹명 생성
        self.user_group = f"user_{self.user.id}"
        self.organization_group = f"org_{self.user.organization.id}"
        
        # 그룹에 추가
        await self.channel_layer.group_add(
            self.user_group,
            self.channel_name
        )
        await self.channel_layer.group_add(
            self.organization_group,
            self.channel_name
        )
        
        await self.accept()
        
        # 연결 성공 메시지 전송
        await self.send(text_data=json.dumps({
            'type': 'connection_established',
            'message': 'WebSocket 연결이 성립되었습니다.',
            'user_id': self.user.id,
            'organization_id': self.user.organization.id,
            'timestamp': timezone.now().isoformat()
        }))
        
        # 읽지 않은 알림 개수 전송
        unread_count = await self.get_unread_notification_count()
        await self.send(text_data=json.dumps({
            'type': 'unread_count',
            'count': unread_count,
            'timestamp': timezone.now().isoformat()
        }))

    async def disconnect(self, close_code):
        """WebSocket 연결 해제"""
        # 그룹에서 제거
        await self.channel_layer.group_discard(
            self.user_group,
            self.channel_name
        )
        await self.channel_layer.group_discard(
            self.organization_group,
            self.channel_name
        )

    async def receive(self, text_data):
        """클라이언트로부터 메시지 수신"""
        try:
            data = json.loads(text_data)
            message_type = data.get('type')
            
            if message_type == 'mark_as_read':
                # 알림을 읽음으로 표시
                notification_id = data.get('notification_id')
                await self.mark_notification_as_read(notification_id)
                
            elif message_type == 'get_notifications':
                # 알림 목록 요청
                await self.send_notifications_list()
                
            elif message_type == 'mark_all_as_read':
                # 모든 알림을 읽음으로 표시
                await self.mark_all_notifications_as_read()
                
            elif message_type == 'get_notification_stats':
                # 알림 통계 요청
                await self.send_notification_stats()
                
            elif message_type == 'ping':
                # 연결 상태 확인
                await self.send(text_data=json.dumps({
                    'type': 'pong',
                    'timestamp': timezone.now().isoformat()
                }))
                
        except json.JSONDecodeError:
            await self.send(text_data=json.dumps({
                'type': 'error',
                'message': '잘못된 JSON 형식입니다.',
                'timestamp': timezone.now().isoformat()
            }))

    async def notification_message(self, event):
        """알림 메시지 전송"""
        await self.send(text_data=json.dumps({
            'type': 'notification',
            'id': event.get('notification_id'),
            'title': event.get('title'),
            'message': event.get('message'),
            'notification_type': event.get('notification_type'),
            'priority': event.get('priority'),
            'action_required': event.get('action_required', False),
            'action_url': event.get('action_url', ''),
            'action_text': event.get('action_text', ''),
            'workflow_step': event.get('workflow_step'),
            'timestamp': event.get('timestamp'),
            'created_at': event.get('created_at')
        }))

    async def workflow_update(self, event):
        """워크플로우 업데이트 알림"""
        await self.send(text_data=json.dumps({
            'type': 'workflow_update',
            'job_request_id': event.get('job_request_id'),
            'step_name': event.get('step_name'),
            'status': event.get('status'),
            'message': event.get('message'),
            'timestamp': event.get('timestamp')
        }))

    async def candidate_update(self, event):
        """후보자 업데이트 알림"""
        await self.send(text_data=json.dumps({
            'type': 'candidate_update',
            'candidate_id': event.get('candidate_id'),
            'candidate_name': event.get('candidate_name'),
            'status': event.get('status'),
            'message': event.get('message'),
            'timestamp': event.get('timestamp')
        }))

    async def interview_reminder(self, event):
        """면접 리마인더"""
        await self.send(text_data=json.dumps({
            'type': 'interview_reminder',
            'interview_id': event.get('interview_id'),
            'candidate_name': event.get('candidate_name'),
            'scheduled_date': event.get('scheduled_date'),
            'message': event.get('message'),
            'timestamp': event.get('timestamp')
        }))

    async def urgent_notification(self, event):
        """긴급 알림"""
        await self.send(text_data=json.dumps({
            'type': 'urgent_notification',
            'id': event.get('notification_id'),
            'title': event.get('title'),
            'message': event.get('message'),
            'priority': event.get('priority'),
            'timestamp': event.get('timestamp')
        }))

    @database_sync_to_async
    def get_unread_notification_count(self):
        """읽지 않은 알림 개수 조회"""
        return Notification.objects.filter(
            recipient=self.user,
            is_read=False
        ).count()

    @database_sync_to_async
    def mark_notification_as_read(self, notification_id):
        """알림을 읽음으로 표시"""
        try:
            notification = Notification.objects.get(
                id=notification_id,
                recipient=self.user
            )
            notification.mark_as_read()
            return True
        except Notification.DoesNotExist:
            return False

    @database_sync_to_async
    def mark_all_notifications_as_read(self):
        """모든 알림을 읽음으로 표시"""
        Notification.objects.filter(
            recipient=self.user,
            is_read=False
        ).update(is_read=True, read_at=timezone.now())

    @database_sync_to_async
    def send_notifications_list(self):
        """최근 알림 목록 조회"""
        notifications = Notification.objects.filter(
            recipient=self.user
        ).order_by('-created_at')[:10]
        
        return [
            {
                'id': notif.id,
                'title': notif.title,
                'message': notif.message,
                'notification_type': notif.notification_type,
                'priority': notif.priority,
                'is_read': notif.is_read,
                'created_at': notif.created_at.isoformat(),
                'action_required': notif.action_required,
                'action_url': notif.action_url,
                'action_text': notif.action_text,
            }
            for notif in notifications
        ]

    @database_sync_to_async
    def send_notification_stats(self):
        """알림 통계 조회"""
        total = Notification.objects.filter(recipient=self.user).count()
        unread = Notification.objects.filter(recipient=self.user, is_read=False).count()
        urgent = Notification.objects.filter(
            recipient=self.user, 
            priority__in=['high', 'urgent'],
            is_read=False
        ).count()
        
        return {
            'total': total,
            'unread': unread,
            'urgent': urgent,
            'read_rate': ((total - unread) / total * 100) if total > 0 else 0
        }


class ChatConsumer(AsyncWebsocketConsumer):
    """실시간 채팅을 위한 WebSocket Consumer"""
    
    async def connect(self):
        """WebSocket 연결"""
        self.user = self.scope["user"]
        self.room_id = self.scope['url_route']['kwargs']['room_id']
        
        # 인증되지 않은 사용자는 연결 거부
        if not self.user.is_authenticated:
            await self.close()
            return
        
        # 채팅방 존재 및 참여 권한 확인
        room = await self.get_chat_room()
        if not room or not await self.can_user_join_room(room):
            await self.close()
            return
        
        # 채팅방 그룹명 생성
        self.room_group_name = f"chat_{self.room_id}"
        
        # 그룹에 추가
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )
        
        # 참여자로 등록
        await self.add_participant(room)
        
        await self.accept()
        
        # 연결 성공 메시지 전송
        await self.send(text_data=json.dumps({
            'type': 'chat_connection_established',
            'message': f'채팅방 "{room.name}"에 연결되었습니다.',
            'room_id': self.room_id,
            'user_id': self.user.id,
            'timestamp': timezone.now().isoformat()
        }))
        
        # 참여자 목록 전송
        participants = await self.get_room_participants(room)
        await self.send(text_data=json.dumps({
            'type': 'participants_list',
            'participants': participants,
            'timestamp': timezone.now().isoformat()
        }))

    async def disconnect(self, close_code):
        """WebSocket 연결 해제"""
        # 그룹에서 제거
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )
        
        # 참여자 상태 업데이트
        await self.update_participant_status(False)

    async def receive(self, text_data):
        """클라이언트로부터 메시지 수신"""
        try:
            data = json.loads(text_data)
            message_type = data.get('type')
            
            if message_type == 'chat_message':
                # 채팅 메시지 전송
                content = data.get('content', '').strip()
                if content:
                    await self.save_and_broadcast_message(content)
                    
            elif message_type == 'typing':
                # 타이핑 상태 전송
                await self.broadcast_typing_status(True)
                
            elif message_type == 'stop_typing':
                # 타이핑 중지 상태 전송
                await self.broadcast_typing_status(False)
                
            elif message_type == 'mark_messages_read':
                # 메시지 읽음 표시
                await self.mark_messages_as_read()
                
            elif message_type == 'get_chat_history':
                # 채팅 히스토리 요청
                await self.send_chat_history()
                
        except json.JSONDecodeError:
            await self.send(text_data=json.dumps({
                'type': 'error',
                'message': '잘못된 JSON 형식입니다.',
                'timestamp': timezone.now().isoformat()
            }))

    async def chat_message(self, event):
        """채팅 메시지 전송"""
        await self.send(text_data=json.dumps({
            'type': 'chat_message',
            'id': event.get('message_id'),
            'sender_id': event.get('sender_id'),
            'sender_name': event.get('sender_name'),
            'content': event.get('content'),
            'message_type': event.get('message_type'),
            'timestamp': event.get('timestamp'),
            'is_edited': event.get('is_edited', False)
        }))

    async def user_typing(self, event):
        """사용자 타이핑 상태 전송"""
        await self.send(text_data=json.dumps({
            'type': 'user_typing',
            'user_id': event.get('user_id'),
            'user_name': event.get('user_name'),
            'is_typing': event.get('is_typing')
        }))

    async def user_joined(self, event):
        """사용자 참여 알림"""
        await self.send(text_data=json.dumps({
            'type': 'user_joined',
            'user_id': event.get('user_id'),
            'user_name': event.get('user_name'),
            'timestamp': event.get('timestamp')
        }))

    async def user_left(self, event):
        """사용자 퇴장 알림"""
        await self.send(text_data=json.dumps({
            'type': 'user_left',
            'user_id': event.get('user_id'),
            'user_name': event.get('user_name'),
            'timestamp': event.get('timestamp')
        }))

    @database_sync_to_async
    def get_chat_room(self):
        """채팅방 조회"""
        try:
            return ChatRoom.objects.get(id=self.room_id, is_active=True)
        except ChatRoom.DoesNotExist:
            return None

    @database_sync_to_async
    def can_user_join_room(self, room):
        """사용자가 채팅방에 참여할 수 있는지 확인"""
        return room.can_user_join(self.user)

    @database_sync_to_async
    def add_participant(self, room):
        """참여자 추가"""
        participant, created = ChatRoomParticipant.objects.get_or_create(
            chat_room=room,
            user=self.user,
            defaults={'role': 'member'}
        )
        if created:
            # 그룹에 참여자 추가 알림
            self.channel_layer.group_send(
                self.room_group_name,
                {
                    'type': 'user_joined',
                    'user_id': self.user.id,
                    'user_name': self.user.get_full_name(),
                    'timestamp': timezone.now().isoformat()
                }
            )

    @database_sync_to_async
    def update_participant_status(self, is_active):
        """참여자 상태 업데이트"""
        try:
            participant = ChatRoomParticipant.objects.get(
                chat_room_id=self.room_id,
                user=self.user
            )
            participant.is_active = is_active
            participant.save()
        except ChatRoomParticipant.DoesNotExist:
            pass

    @database_sync_to_async
    def get_room_participants(self, room):
        """채팅방 참여자 목록 조회"""
        participants = room.participant_relations.filter(is_active=True).select_related('user')
        return [
            {
                'user_id': p.user.id,
                'user_name': p.user.get_full_name(),
                'role': p.role,
                'joined_at': p.joined_at.isoformat()
            }
            for p in participants
        ]

    async def save_and_broadcast_message(self, content):
        """메시지 저장 및 브로드캐스트"""
        message_data = await self.save_message(content)
        
        # 그룹에 메시지 전송
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'chat_message',
                'message_id': message_data['id'],
                'sender_id': message_data['sender_id'],
                'sender_name': message_data['sender_name'],
                'content': message_data['content'],
                'message_type': message_data['message_type'],
                'timestamp': message_data['timestamp'],
                'is_edited': False
            }
        )

    @database_sync_to_async
    def save_message(self, content):
        """메시지 저장"""
        room = ChatRoom.objects.get(id=self.room_id)
        message = ChatMessage.objects.create(
            chat_room=room,
            sender=self.user,
            content=content,
            message_type='text'
        )
        
        return {
            'id': message.id,
            'sender_id': message.sender.id,
            'sender_name': message.sender.get_full_name(),
            'content': message.content,
            'message_type': message.message_type,
            'timestamp': message.created_at.isoformat()
        }

    async def broadcast_typing_status(self, is_typing):
        """타이핑 상태 브로드캐스트"""
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'user_typing',
                'user_id': self.user.id,
                'user_name': self.user.get_full_name(),
                'is_typing': is_typing
            }
        )

    @database_sync_to_async
    def mark_messages_as_read(self):
        """메시지 읽음 표시"""
        participant = ChatRoomParticipant.objects.get(
            chat_room_id=self.room_id,
            user=self.user
        )
        participant.last_read_at = timezone.now()
        participant.save()

    @database_sync_to_async
    def send_chat_history(self):
        """채팅 히스토리 조회"""
        messages = ChatMessage.objects.filter(
            chat_room_id=self.room_id
        ).select_related('sender').order_by('-created_at')[:50]
        
        return [
            {
                'id': msg.id,
                'sender_id': msg.sender.id,
                'sender_name': msg.sender.get_full_name(),
                'content': msg.content,
                'message_type': msg.message_type,
                'timestamp': msg.created_at.isoformat(),
                'is_edited': msg.is_edited
            }
            for msg in reversed(messages)  # 시간순 정렬
        ]


class WorkflowConsumer(AsyncWebsocketConsumer):
    """워크플로우 실시간 업데이트를 위한 Consumer"""
    
    async def connect(self):
        """WebSocket 연결"""
        self.user = self.scope["user"]
        
        if not self.user.is_authenticated:
            await self.close()
            return
        
        # 워크플로우 그룹에 추가
        self.workflow_group = f"workflow_{self.user.organization.id}"
        
        await self.channel_layer.group_add(
            self.workflow_group,
            self.channel_name
        )
        
        await self.accept()
        
        # 연결 성공 메시지 전송
        await self.send(text_data=json.dumps({
            'type': 'workflow_connection_established',
            'message': '워크플로우 실시간 업데이트에 연결되었습니다.',
            'timestamp': timezone.now().isoformat()
        }))

    async def disconnect(self, close_code):
        """WebSocket 연결 해제"""
        await self.channel_layer.group_discard(
            self.workflow_group,
            self.channel_name
        )

    async def workflow_status_update(self, event):
        """워크플로우 상태 업데이트"""
        await self.send(text_data=json.dumps({
            'type': 'workflow_status_update',
            'workflow_id': event.get('workflow_id'),
            'status': event.get('status'),
            'step_name': event.get('step_name'),
            'progress': event.get('progress'),
            'message': event.get('message'),
            'timestamp': event.get('timestamp')
        }))

    async def task_assignment(self, event):
        """작업 할당 알림"""
        await self.send(text_data=json.dumps({
            'type': 'task_assignment',
            'task_id': event.get('task_id'),
            'task_name': event.get('task_name'),
            'assigned_to': event.get('assigned_to'),
            'due_date': event.get('due_date'),
            'message': event.get('message'),
            'timestamp': event.get('timestamp')
        }))

    async def deadline_reminder(self, event):
        """마감일 리마인더"""
        await self.send(text_data=json.dumps({
            'type': 'deadline_reminder',
            'workflow_id': event.get('workflow_id'),
            'workflow_name': event.get('workflow_name'),
            'deadline': event.get('deadline'),
            'days_remaining': event.get('days_remaining'),
            'message': event.get('message'),
            'timestamp': event.get('timestamp')
        })) 