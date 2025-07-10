from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
from django.utils import timezone
from .models import Notification, NotificationTemplate, NotificationPreference, ChatRoom, ChatMessage
from django.contrib.auth import get_user_model
import json

User = get_user_model()


def send_real_time_notification(organization_id, message, action_required=False, workflow_step=None, **kwargs):
    """실시간 알림 발송"""
    channel_layer = get_channel_layer()
    async_to_sync(channel_layer.group_send)(
        f"org_{organization_id}",
        {
            'type': 'notification_message',
            'message': message,
            'action_required': action_required,
            'workflow_step': workflow_step,
            'timestamp': timezone.now().isoformat(),
            **kwargs
        }
    )


def send_notification(recipient, notification_type, title, message, related_object_id=None, related_object_type=None, **kwargs):
    """알림 발송 함수 (API에서 사용)"""
    notification = Notification.objects.create(
        recipient=recipient,
        organization=recipient.organization,
        notification_type=notification_type,
        title=title,
        message=message,
        related_object_id=related_object_id,
        related_object_type=related_object_type,
        **kwargs
    )
    
    # 실시간 알림 발송
    send_real_time_notification(
        organization_id=recipient.organization.id,
        message=message,
        action_required=kwargs.get('action_required', False),
        workflow_step=kwargs.get('workflow_step'),
        notification_id=notification.id,
        title=title,
        notification_type=notification_type,
        priority=kwargs.get('priority', 'normal'),
        action_url=kwargs.get('action_url', ''),
        action_text=kwargs.get('action_text', ''),
        created_at=notification.created_at.isoformat()
    )
    
    return notification


def send_user_notification(user, notification_type, title, message, **kwargs):
    """사용자별 알림 생성 및 발송"""
    # 사용자 알림 설정 확인
    try:
        preferences = user.notification_preferences
        if not preferences.should_send_notification(notification_type):
            return None
    except NotificationPreference.DoesNotExist:
        # 기본 설정으로 진행
        pass
    
    # 알림 생성
    notification = Notification.objects.create(
        recipient=user,
        organization=user.organization,
        notification_type=notification_type,
        title=title,
        message=message,
        **kwargs
    )
    
    # 실시간 알림 발송
    send_real_time_notification(
        organization_id=user.organization.id,
        message=message,
        action_required=kwargs.get('action_required', False),
        workflow_step=kwargs.get('workflow_step'),
        notification_id=notification.id,
        title=title,
        notification_type=notification_type,
        priority=kwargs.get('priority', 'normal'),
        action_url=kwargs.get('action_url', ''),
        action_text=kwargs.get('action_text', ''),
        created_at=notification.created_at.isoformat()
    )
    
    return notification


def send_workflow_notification(job_request, step_name, status, message, **kwargs):
    """워크플로우 관련 알림 발송"""
    # 관련 사용자들에게 알림 발송
    users_to_notify = []
    
    if step_name == 'request_submitted':
        # 헤드헌팅 회사 대표에게 알림
        users_to_notify = job_request.requester.organization.users.filter(
            role='hh_ceo',
            is_active_user=True
        )
    elif step_name == 'candidate_recommended':
        # 병원 인사담당자에게 알림
        users_to_notify = job_request.requester.organization.users.filter(
            role__in=['hospital_hr', 'hospital_manager'],
            is_active_user=True
        )
    elif step_name == 'document_review':
        # 헤드헌팅 회사 담당자에게 알림
        users_to_notify = job_request.requester.organization.users.filter(
            role__in=['hh_ceo', 'hh_manager', 'hh_staff'],
            is_active_user=True
        )
    
    for user in users_to_notify:
        send_user_notification(
            user=user,
            notification_type='workflow_step_completed',
            title=f'워크플로우 업데이트: {job_request.position_title}',
            message=message,
            action_required=True,
            workflow_step=step_name,
            related_object_type='JobRequest',
            related_object_id=job_request.id,
            **kwargs
        )


def send_candidate_notification(candidate, action, message, **kwargs):
    """후보자 관련 알림 발송"""
    notification_type = 'candidate_recommended'
    
    if action == 'recommended':
        notification_type = 'candidate_recommended'
        title = f'새로운 후보자 추천: {candidate.name}'
    elif action == 'reviewed':
        notification_type = 'document_review_completed'
        title = f'후보자 서류 검토 완료: {candidate.name}'
    elif action == 'interview_scheduled':
        notification_type = 'interview_scheduled'
        title = f'면접 일정 확정: {candidate.name}'
    elif action == 'interview_completed':
        notification_type = 'interview_completed'
        title = f'면접 완료: {candidate.name}'
    else:
        title = f'후보자 업데이트: {candidate.name}'
    
    # 관련 사용자들에게 알림
    users_to_notify = []
    
    if action == 'recommended':
        # 병원 담당자들에게 알림
        users_to_notify = candidate.job_request.requester.organization.users.filter(
            role__in=['hospital_hr', 'hospital_manager'],
            is_active_user=True
        )
    elif action in ['reviewed', 'interview_scheduled', 'interview_completed']:
        # 헤드헌팅 담당자들에게 알림
        users_to_notify = candidate.recommended_by.organization.users.filter(
            role__in=['hh_ceo', 'hh_manager', 'hh_staff'],
            is_active_user=True
        )
    
    for user in users_to_notify:
        send_user_notification(
            user=user,
            notification_type=notification_type,
            title=title,
            message=message,
            related_object_type='Candidate',
            related_object_id=candidate.id,
            **kwargs
        )


def send_interview_reminder(interview):
    """면접 리마인더 발송"""
    # 면접 1시간 전 리마인더
    reminder_time = interview.scheduled_date - timezone.timedelta(hours=1)
    
    if timezone.now() >= reminder_time:
        message = f"{interview.candidate.name}님의 면접이 1시간 후에 예정되어 있습니다."
        
        # 면접관들에게 알림
        interviewers = [interview.primary_interviewer] + list(interview.secondary_interviewers.all())
        
        for interviewer in interviewers:
            send_user_notification(
                user=interviewer,
                notification_type='reminder',
                title=f'면접 리마인더: {interview.candidate.name}',
                message=message,
                priority='high',
                related_object_type='Interview',
                related_object_id=interview.id,
                action_url=f'/interviews/{interview.id}/',
                action_text='면접 상세보기'
            )


def send_system_notification(organization, title, message, **kwargs):
    """시스템 알림 발송"""
    users = organization.users.filter(is_active_user=True)
    
    for user in users:
        send_user_notification(
            user=user,
            notification_type='system_notification',
            title=title,
            message=message,
            priority=kwargs.get('priority', 'normal'),
            **kwargs
        )


def create_notification_from_template(template_name, context_data, recipients, **kwargs):
    """템플릿을 사용하여 알림 생성"""
    try:
        template = NotificationTemplate.objects.get(
            name=template_name,
            is_active=True
        )
        
        title, message = template.render_template(context_data)
        
        notifications = []
        for recipient in recipients:
            notification = send_user_notification(
                user=recipient,
                notification_type=template.notification_type,
                title=title,
                message=message,
                **kwargs
            )
            if notification:
                notifications.append(notification)
        
        return notifications
        
    except NotificationTemplate.DoesNotExist:
        return []


def mark_notifications_as_read(user, notification_ids=None):
    """알림을 읽음으로 표시"""
    queryset = Notification.objects.filter(recipient=user, is_read=False)
    
    if notification_ids:
        queryset = queryset.filter(id__in=notification_ids)
    
    return queryset.update(is_read=True, read_at=timezone.now())


def get_unread_notification_count(user):
    """읽지 않은 알림 개수 조회"""
    return Notification.objects.filter(
        recipient=user,
        is_read=False
    ).count()


def cleanup_old_notifications(days=30):
    """오래된 알림 정리"""
    cutoff_date = timezone.now() - timezone.timedelta(days=days)
    
    # 읽은 알림 중 오래된 것들 삭제
    deleted_count = Notification.objects.filter(
        is_read=True,
        created_at__lt=cutoff_date
    ).delete()[0]
    
    return deleted_count


class NotificationService:
    """알림 서비스 클래스"""
    
    @staticmethod
    def send_notification(recipient, notification_type, title, message, **kwargs):
        """알림 전송"""
        # 알림 설정 확인
        if not NotificationService._should_send_notification(recipient, notification_type):
            return None
        
        # 알림 생성
        notification = Notification.objects.create(
            recipient=recipient,
            organization=recipient.organization,
            notification_type=notification_type,
            title=title,
            message=message,
            priority=kwargs.get('priority', 'normal'),
            action_required=kwargs.get('action_required', False),
            action_url=kwargs.get('action_url', ''),
            action_text=kwargs.get('action_text', ''),
            related_object_type=kwargs.get('related_object_type', ''),
            related_object_id=kwargs.get('related_object_id'),
            scheduled_at=kwargs.get('scheduled_at')
        )
        
        # 실시간 알림 전송
        NotificationService._send_realtime_notification(notification)
        
        return notification
    
    @staticmethod
    def send_bulk_notifications(recipients, notification_type, title, message, **kwargs):
        """대량 알림 전송"""
        notifications = []
        for recipient in recipients:
            if NotificationService._should_send_notification(recipient, notification_type):
                notification = NotificationService.send_notification(
                    recipient, notification_type, title, message, **kwargs
                )
                if notification:
                    notifications.append(notification)
        return notifications
    
    @staticmethod
    def send_urgent_notification(recipient, title, message, **kwargs):
        """긴급 알림 전송"""
        return NotificationService.send_notification(
            recipient, 'system_notification', title, message,
            priority='urgent', **kwargs
        )
    
    @staticmethod
    def send_workflow_notification(workflow, step_name, status, message, **kwargs):
        """워크플로우 알림 전송"""
        recipients = [workflow.assigned_to]
        if workflow.created_by != workflow.assigned_to:
            recipients.append(workflow.created_by)
        
        title = f"워크플로우 '{workflow.title}' - {step_name}"
        
        return NotificationService.send_bulk_notifications(
            recipients, 'workflow_step_completed', title, message,
            related_object_type='workflow',
            related_object_id=workflow.id,
            **kwargs
        )
    
    @staticmethod
    def send_candidate_notification(candidate, status, message, **kwargs):
        """후보자 관련 알림 전송"""
        recipients = [candidate.recommended_by]
        if candidate.job_request.requester != candidate.recommended_by:
            recipients.append(candidate.job_request.requester)
        
        title = f"후보자 '{candidate.name}' 상태 변경"
        
        return NotificationService.send_bulk_notifications(
            recipients, 'candidate_recommended', title, message,
            related_object_type='candidate',
            related_object_id=candidate.id,
            **kwargs
        )
    
    @staticmethod
    def send_interview_reminder(interview, hours_before=24):
        """면접 리마인더 전송"""
        scheduled_time = interview.scheduled_date
        reminder_time = scheduled_time - timezone.timedelta(hours=hours_before)
        
        if timezone.now() >= reminder_time:
            title = f"면접 리마인더: {interview.candidate.name}"
            message = f"내일 {scheduled_time.strftime('%H:%M')}에 {interview.candidate.name}님과의 면접이 예정되어 있습니다."
            
            recipients = [interview.interviewer]
            if interview.candidate.recommended_by != interview.interviewer:
                recipients.append(interview.candidate.recommended_by)
            
            return NotificationService.send_bulk_notifications(
                recipients, 'reminder', title, message,
                priority='high',
                action_required=True,
                action_url=f'/evaluations/{interview.id}/',
                action_text='면접 상세보기'
            )
    
    @staticmethod
    def send_deadline_reminder(workflow, days_before=3):
        """마감일 리마인더 전송"""
        if workflow.due_date:
            reminder_date = workflow.due_date - timezone.timedelta(days=days_before)
            
            if timezone.now().date() >= reminder_date:
                days_remaining = (workflow.due_date - timezone.now().date()).days
                
                title = f"마감일 임박: {workflow.title}"
                message = f"워크플로우 '{workflow.title}'의 마감일이 {days_remaining}일 남았습니다."
                
                recipients = [workflow.assigned_to]
                if workflow.created_by != workflow.assigned_to:
                    recipients.append(workflow.created_by)
                
                return NotificationService.send_bulk_notifications(
                    recipients, 'reminder', title, message,
                    priority='high' if days_remaining <= 1 else 'normal',
                    action_required=True,
                    action_url=f'/workflow/{workflow.id}/',
                    action_text='워크플로우 보기'
                )
    
    @staticmethod
    def _should_send_notification(user, notification_type):
        """알림을 전송해야 하는지 확인"""
        try:
            preferences = user.notification_preferences
            if preferences.is_quiet_hours():
                return False
            
            # 알림 유형별 설정 확인
            type_mapping = {
                'job_request_submitted': preferences.job_request_notifications,
                'job_request_accepted': preferences.job_request_notifications,
                'candidate_recommended': preferences.candidate_notifications,
                'document_review_completed': preferences.candidate_notifications,
                'interview_scheduled': preferences.interview_notifications,
                'interview_completed': preferences.interview_notifications,
                'final_decision_made': preferences.candidate_notifications,
                'workflow_step_completed': preferences.workflow_notifications,
                'system_notification': preferences.system_notifications,
                'reminder': preferences.system_notifications
            }
            
            return type_mapping.get(notification_type, True)
        except:
            return True
    
    @staticmethod
    def _send_realtime_notification(notification):
        """실시간 알림 전송"""
        channel_layer = get_channel_layer()
        
        # 사용자별 알림
        async_to_sync(channel_layer.group_send)(
            f"user_{notification.recipient.id}",
            {
                'type': 'notification_message',
                'notification_id': notification.id,
                'title': notification.title,
                'message': notification.message,
                'notification_type': notification.notification_type,
                'priority': notification.priority,
                'action_required': notification.action_required,
                'action_url': notification.action_url,
                'action_text': notification.action_text,
                'timestamp': timezone.now().isoformat(),
                'created_at': notification.created_at.isoformat()
            }
        )
        
        # 긴급 알림인 경우 추가 처리
        if notification.is_urgent():
            async_to_sync(channel_layer.group_send)(
                f"user_{notification.recipient.id}",
                {
                    'type': 'urgent_notification',
                    'notification_id': notification.id,
                    'title': notification.title,
                    'message': notification.message,
                    'priority': notification.priority,
                    'timestamp': timezone.now().isoformat()
                }
            )


class ChatService:
    """채팅 서비스 클래스"""
    
    @staticmethod
    def create_workflow_chat_room(workflow, created_by):
        """워크플로우 채팅방 생성"""
        room_name = f"워크플로우: {workflow.title}"
        
        chat_room = ChatRoom.objects.create(
            name=room_name,
            room_type='workflow',
            related_object_type='workflow',
            related_object_id=workflow.id,
            created_by=created_by
        )
        
        # 워크플로우 관련자들을 참여자로 추가
        participants = [workflow.assigned_to, workflow.created_by]
        for participant in participants:
            ChatRoomParticipant.objects.create(
                chat_room=chat_room,
                user=participant,
                role='member'
            )
        
        return chat_room
    
    @staticmethod
    def create_candidate_chat_room(candidate, created_by):
        """후보자 채팅방 생성"""
        room_name = f"후보자: {candidate.name}"
        
        chat_room = ChatRoom.objects.create(
            name=room_name,
            room_type='candidate',
            related_object_type='candidate',
            related_object_id=candidate.id,
            created_by=created_by
        )
        
        # 후보자 관련자들을 참여자로 추가
        participants = [candidate.recommended_by, candidate.job_request.requester]
        for participant in participants:
            ChatRoomParticipant.objects.create(
                chat_room=chat_room,
                user=participant,
                role='member'
            )
        
        return chat_room
    
    @staticmethod
    def send_system_message(chat_room, message, sender=None):
        """시스템 메시지 전송"""
        if not sender:
            sender = chat_room.created_by
        
        chat_message = ChatMessage.objects.create(
            chat_room=chat_room,
            sender=sender,
            content=message,
            message_type='system'
        )
        
        # 실시간 메시지 전송
        ChatService._send_realtime_message(chat_message)
        
        return chat_message
    
    @staticmethod
    def _send_realtime_message(chat_message):
        """실시간 메시지 전송"""
        channel_layer = get_channel_layer()
        
        async_to_sync(channel_layer.group_send)(
            f"chat_{chat_message.chat_room.id}",
            {
                'type': 'chat_message',
                'message_id': chat_message.id,
                'sender_id': chat_message.sender.id,
                'sender_name': chat_message.sender.get_full_name(),
                'content': chat_message.content,
                'message_type': chat_message.message_type,
                'timestamp': chat_message.created_at.isoformat(),
                'is_edited': chat_message.is_edited
            }
        )


class NotificationAnalyticsService:
    """알림 분석 서비스 클래스"""
    
    @staticmethod
    def update_daily_analytics(organization, date=None):
        """일일 알림 분석 업데이트"""
        if not date:
            date = timezone.now().date()
        
        # 기존 분석 데이터 조회 또는 생성
        analytics, created = NotificationAnalytics.objects.get_or_create(
            date=date,
            organization=organization
        )
        
        # 알림 통계 계산
        notifications = Notification.objects.filter(
            organization=organization,
            created_at__date=date
        )
        
        analytics.total_notifications = notifications.count()
        analytics.read_notifications = notifications.filter(is_read=True).count()
        analytics.unread_notifications = analytics.total_notifications - analytics.read_notifications
        
        # 알림 유형별 통계
        type_counts = {}
        for notification_type, _ in Notification.NOTIFICATION_TYPE_CHOICES:
            count = notifications.filter(notification_type=notification_type).count()
            if count > 0:
                type_counts[notification_type] = count
        analytics.notification_type_counts = type_counts
        
        # 우선순위별 통계
        priority_counts = {}
        for priority, _ in Notification.PRIORITY_CHOICES:
            count = notifications.filter(priority=priority).count()
            if count > 0:
                priority_counts[priority] = count
        analytics.priority_counts = priority_counts
        
        # 전송 방법별 통계 (로그에서 계산)
        delivery_counts = {}
        for log in NotificationLog.objects.filter(
            notification__organization=organization,
            sent_at__date=date
        ):
            method = log.delivery_method
            delivery_counts[method] = delivery_counts.get(method, 0) + 1
        analytics.delivery_method_counts = delivery_counts
        
        # 평균 응답 시간 계산 (읽은 알림의 경우)
        read_notifications = notifications.filter(is_read=True)
        total_response_time = 0
        response_count = 0
        
        for notification in read_notifications:
            if notification.read_at:
                response_time = notification.read_at - notification.created_at
                total_response_time += response_time.total_seconds()
                response_count += 1
        
        if response_count > 0:
            analytics.avg_response_time_minutes = (total_response_time / response_count) / 60
        
        analytics.save()
        return analytics
    
    @staticmethod
    def get_organization_stats(organization, days=30):
        """조직별 알림 통계 조회"""
        end_date = timezone.now().date()
        start_date = end_date - timezone.timedelta(days=days)
        
        analytics = NotificationAnalytics.objects.filter(
            organization=organization,
            date__range=[start_date, end_date]
        ).order_by('date')
        
        return analytics
    
    @staticmethod
    def get_user_stats(user, days=30):
        """사용자별 알림 통계 조회"""
        end_date = timezone.now().date()
        start_date = end_date - timezone.timedelta(days=days)
        
        notifications = Notification.objects.filter(
            recipient=user,
            created_at__date__range=[start_date, end_date]
        )
        
        stats = {
            'total': notifications.count(),
            'read': notifications.filter(is_read=True).count(),
            'unread': notifications.filter(is_read=False).count(),
            'urgent': notifications.filter(priority__in=['high', 'urgent']).count(),
            'read_rate': 0
        }
        
        if stats['total'] > 0:
            stats['read_rate'] = (stats['read'] / stats['total']) * 100
        
        return stats 