from django.db import models
from django.utils import timezone
from accounts.models import User, Organization


class Notification(models.Model):
    """알림 모델"""
    
    NOTIFICATION_TYPE_CHOICES = [
        ('job_request_submitted', '채용 요청 제출'),
        ('job_request_accepted', '채용 요청 접수'),
        ('candidate_recommended', '후보자 추천'),
        ('document_review_completed', '서류 검토 완료'),
        ('interview_scheduled', '면접 일정 확정'),
        ('interview_completed', '면접 완료'),
        ('final_decision_made', '최종 결정'),
        ('workflow_step_completed', '워크플로우 단계 완료'),
        ('system_notification', '시스템 알림'),
        ('reminder', '리마인더')
    ]
    
    PRIORITY_CHOICES = [
        ('low', '낮음'),
        ('normal', '보통'),
        ('high', '높음'),
        ('urgent', '긴급')
    ]
    
    # 수신자 정보
    recipient = models.ForeignKey(
        User, 
        on_delete=models.CASCADE,
        related_name='notifications',
        verbose_name='수신자'
    )
    organization = models.ForeignKey(
        Organization,
        on_delete=models.CASCADE,
        related_name='notifications',
        verbose_name='소속 기관'
    )
    
    # 알림 내용
    notification_type = models.CharField(
        max_length=30,
        choices=NOTIFICATION_TYPE_CHOICES,
        verbose_name='알림 유형'
    )
    title = models.CharField(max_length=200, verbose_name='제목')
    message = models.TextField(verbose_name='메시지')
    priority = models.CharField(
        max_length=10,
        choices=PRIORITY_CHOICES,
        default='normal',
        verbose_name='우선순위'
    )
    
    # 액션 관련
    action_required = models.BooleanField(default=False, verbose_name='액션 필요')
    action_url = models.CharField(max_length=500, blank=True, verbose_name='액션 URL')
    action_text = models.CharField(max_length=100, blank=True, verbose_name='액션 텍스트')
    
    # 관련 객체 정보
    related_object_type = models.CharField(max_length=50, blank=True, verbose_name='관련 객체 타입')
    related_object_id = models.PositiveIntegerField(blank=True, null=True, verbose_name='관련 객체 ID')
    
    # 상태 및 시간
    is_read = models.BooleanField(default=False, verbose_name='읽음 여부')
    read_at = models.DateTimeField(blank=True, null=True, verbose_name='읽은 시간')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='생성일')
    scheduled_at = models.DateTimeField(blank=True, null=True, verbose_name='예약 발송 시간')
    sent_at = models.DateTimeField(blank=True, null=True, verbose_name='발송 시간')
    
    class Meta:
        verbose_name = '알림'
        verbose_name_plural = '알림들'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['recipient', 'is_read']),
            models.Index(fields=['organization', 'created_at']),
            models.Index(fields=['notification_type', 'created_at']),
        ]
    
    def __str__(self):
        return f"{self.recipient.get_full_name()} - {self.title}"
    
    def mark_as_read(self):
        """알림을 읽음으로 표시"""
        if not self.is_read:
            self.is_read = True
            self.read_at = timezone.now()
            self.save(update_fields=['is_read', 'read_at'])
    
    def is_urgent(self):
        """긴급 알림 여부"""
        return self.priority in ['high', 'urgent']
    
    def get_age_minutes(self):
        """알림 생성 후 경과 시간 (분)"""
        return int((timezone.now() - self.created_at).total_seconds() / 60)
    
    def should_send_now(self):
        """지금 발송해야 하는지 확인"""
        if self.scheduled_at:
            return timezone.now() >= self.scheduled_at
        return True


class NotificationTemplate(models.Model):
    """알림 템플릿"""
    
    name = models.CharField(max_length=100, verbose_name='템플릿명')
    notification_type = models.CharField(
        max_length=30,
        choices=Notification.NOTIFICATION_TYPE_CHOICES,
        verbose_name='알림 유형'
    )
    title_template = models.CharField(max_length=200, verbose_name='제목 템플릿')
    message_template = models.TextField(verbose_name='메시지 템플릿')
    is_active = models.BooleanField(default=True, verbose_name='활성화')
    
    # 템플릿 변수 설명
    variables_description = models.TextField(blank=True, verbose_name='변수 설명')
    
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='생성일')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='수정일')
    
    class Meta:
        verbose_name = '알림 템플릿'
        verbose_name_plural = '알림 템플릿들'
        ordering = ['name']
    
    def __str__(self):
        return f"{self.name} ({self.get_notification_type_display()})"
    
    def render_template(self, context_data):
        """템플릿 렌더링"""
        from django.template import Template, Context
        
        title = Template(self.title_template).render(Context(context_data))
        message = Template(self.message_template).render(Context(context_data))
        
        return title, message


class NotificationPreference(models.Model):
    """사용자별 알림 설정"""
    
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name='notification_preferences',
        verbose_name='사용자'
    )
    
    # 알림 유형별 설정
    email_notifications = models.BooleanField(default=True, verbose_name='이메일 알림')
    web_notifications = models.BooleanField(default=True, verbose_name='웹 알림')
    sms_notifications = models.BooleanField(default=False, verbose_name='SMS 알림')
    
    # 알림 유형별 상세 설정
    job_request_notifications = models.BooleanField(default=True, verbose_name='채용 요청 알림')
    candidate_notifications = models.BooleanField(default=True, verbose_name='후보자 관련 알림')
    interview_notifications = models.BooleanField(default=True, verbose_name='면접 관련 알림')
    workflow_notifications = models.BooleanField(default=True, verbose_name='워크플로우 알림')
    system_notifications = models.BooleanField(default=True, verbose_name='시스템 알림')
    
    # 시간 설정
    quiet_hours_start = models.TimeField(blank=True, null=True, verbose_name='방해 금지 시작 시간')
    quiet_hours_end = models.TimeField(blank=True, null=True, verbose_name='방해 금지 종료 시간')
    
    # 업데이트 시간
    updated_at = models.DateTimeField(auto_now=True, verbose_name='수정일')
    
    class Meta:
        verbose_name = '알림 설정'
        verbose_name_plural = '알림 설정들'
    
    def __str__(self):
        return f"{self.user.get_full_name()} 알림 설정"
    
    def is_quiet_hours(self):
        """방해 금지 시간인지 확인"""
        if not self.quiet_hours_start or not self.quiet_hours_end:
            return False
        
        now = timezone.now().time()
        if self.quiet_hours_start <= self.quiet_hours_end:
            return self.quiet_hours_start <= now <= self.quiet_hours_end
        else:  # 자정을 걸치는 경우
            return now >= self.quiet_hours_start or now <= self.quiet_hours_end
    
    def should_send_notification(self, notification_type):
        """특정 알림 유형을 발송해야 하는지 확인"""
        if self.is_quiet_hours():
            return False
        
        # 알림 유형별 설정 확인
        type_mapping = {
            'job_request_submitted': self.job_request_notifications,
            'job_request_accepted': self.job_request_notifications,
            'candidate_recommended': self.candidate_notifications,
            'document_review_completed': self.candidate_notifications,
            'interview_scheduled': self.interview_notifications,
            'interview_completed': self.interview_notifications,
            'workflow_step_completed': self.workflow_notifications,
            'system_notification': self.system_notifications,
        }
        
        return type_mapping.get(notification_type, True)


class NotificationLog(models.Model):
    """알림 발송 로그"""
    
    DELIVERY_METHOD_CHOICES = [
        ('email', '이메일'),
        ('web', '웹'),
        ('sms', 'SMS'),
        ('websocket', 'WebSocket')
    ]
    
    STATUS_CHOICES = [
        ('pending', '대기중'),
        ('sent', '발송됨'),
        ('failed', '실패'),
        ('delivered', '전달됨'),
        ('read', '읽음')
    ]
    
    notification = models.ForeignKey(
        Notification,
        on_delete=models.CASCADE,
        related_name='delivery_logs',
        verbose_name='알림'
    )
    delivery_method = models.CharField(
        max_length=20,
        choices=DELIVERY_METHOD_CHOICES,
        verbose_name='발송 방법'
    )
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='pending',
        verbose_name='상태'
    )
    error_message = models.TextField(blank=True, verbose_name='오류 메시지')
    sent_at = models.DateTimeField(blank=True, null=True, verbose_name='발송 시간')
    delivered_at = models.DateTimeField(blank=True, null=True, verbose_name='전달 시간')
    
    class Meta:
        verbose_name = '알림 발송 로그'
        verbose_name_plural = '알림 발송 로그들'
        ordering = ['-sent_at']
    
    def __str__(self):
        return f"{self.notification.title} - {self.get_delivery_method_display()} ({self.get_status_display()})"


class ChatRoom(models.Model):
    """실시간 채팅방 모델"""
    
    ROOM_TYPE_CHOICES = [
        ('workflow', '워크플로우'),
        ('candidate', '후보자'),
        ('interview', '면접'),
        ('general', '일반'),
        ('support', '지원')
    ]
    
    name = models.CharField(max_length=200, verbose_name='채팅방명')
    room_type = models.CharField(
        max_length=20,
        choices=ROOM_TYPE_CHOICES,
        verbose_name='채팅방 유형'
    )
    
    # 관련 객체 정보
    related_object_type = models.CharField(max_length=50, blank=True, verbose_name='관련 객체 타입')
    related_object_id = models.PositiveIntegerField(blank=True, null=True, verbose_name='관련 객체 ID')
    
    # 참여자 관리
    participants = models.ManyToManyField(
        User,
        through='ChatRoomParticipant',
        related_name='chat_rooms',
        verbose_name='참여자'
    )
    
    # 채팅방 설정
    is_active = models.BooleanField(default=True, verbose_name='활성화')
    is_private = models.BooleanField(default=False, verbose_name='비공개')
    max_participants = models.PositiveIntegerField(default=50, verbose_name='최대 참여자 수')
    
    # 메타 정보
    created_by = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='created_chat_rooms',
        verbose_name='생성자'
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='생성일')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='수정일')
    
    class Meta:
        verbose_name = '채팅방'
        verbose_name_plural = '채팅방들'
        ordering = ['-updated_at']
    
    def __str__(self):
        return f"{self.name} ({self.get_room_type_display()})"
    
    def get_participant_count(self):
        """참여자 수 반환"""
        return self.participants.count()
    
    def can_user_join(self, user):
        """사용자가 참여할 수 있는지 확인"""
        if not self.is_active:
            return False
        if self.is_private and not self.participants.filter(id=user.id).exists():
            return False
        if self.get_participant_count() >= self.max_participants:
            return False
        return True
    
    def get_last_message(self):
        """마지막 메시지 반환"""
        return self.messages.order_by('-created_at').first()


class ChatRoomParticipant(models.Model):
    """채팅방 참여자 모델"""
    
    ROLE_CHOICES = [
        ('admin', '관리자'),
        ('moderator', '운영자'),
        ('member', '일반 멤버'),
        ('guest', '게스트')
    ]
    
    chat_room = models.ForeignKey(
        ChatRoom,
        on_delete=models.CASCADE,
        related_name='participant_relations',
        verbose_name='채팅방'
    )
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='chat_room_relations',
        verbose_name='사용자'
    )
    
    role = models.CharField(
        max_length=20,
        choices=ROLE_CHOICES,
        default='member',
        verbose_name='역할'
    )
    
    # 참여 정보
    joined_at = models.DateTimeField(auto_now_add=True, verbose_name='참여일')
    last_read_at = models.DateTimeField(blank=True, null=True, verbose_name='마지막 읽은 시간')
    is_active = models.BooleanField(default=True, verbose_name='활성 참여자')
    
    class Meta:
        verbose_name = '채팅방 참여자'
        verbose_name_plural = '채팅방 참여자들'
        unique_together = ['chat_room', 'user']
    
    def __str__(self):
        return f"{self.user.get_full_name()} - {self.chat_room.name}"


class ChatMessage(models.Model):
    """채팅 메시지 모델"""
    
    MESSAGE_TYPE_CHOICES = [
        ('text', '텍스트'),
        ('file', '파일'),
        ('image', '이미지'),
        ('system', '시스템 메시지'),
        ('notification', '알림')
    ]
    
    chat_room = models.ForeignKey(
        ChatRoom,
        on_delete=models.CASCADE,
        related_name='messages',
        verbose_name='채팅방'
    )
    sender = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='sent_messages',
        verbose_name='발신자'
    )
    
    # 메시지 내용
    message_type = models.CharField(
        max_length=20,
        choices=MESSAGE_TYPE_CHOICES,
        default='text',
        verbose_name='메시지 유형'
    )
    content = models.TextField(verbose_name='내용')
    
    # 파일 관련
    file_url = models.CharField(max_length=500, blank=True, verbose_name='파일 URL')
    file_name = models.CharField(max_length=200, blank=True, verbose_name='파일명')
    file_size = models.PositiveIntegerField(blank=True, null=True, verbose_name='파일 크기')
    
    # 메시지 상태
    is_edited = models.BooleanField(default=False, verbose_name='수정됨')
    is_deleted = models.BooleanField(default=False, verbose_name='삭제됨')
    edited_at = models.DateTimeField(blank=True, null=True, verbose_name='수정일')
    
    # 메타 정보
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='생성일')
    
    class Meta:
        verbose_name = '채팅 메시지'
        verbose_name_plural = '채팅 메시지들'
        ordering = ['created_at']
        indexes = [
            models.Index(fields=['chat_room', 'created_at']),
            models.Index(fields=['sender', 'created_at']),
        ]
    
    def __str__(self):
        return f"{self.sender.get_full_name()}: {self.content[:50]}"
    
    def get_unread_count_for_user(self, user):
        """특정 사용자에 대한 읽지 않은 메시지 수"""
        participant = self.chat_room.participant_relations.filter(user=user).first()
        if not participant or not participant.last_read_at:
            return self.chat_room.messages.filter(created_at__gt=participant.joined_at).count()
        
        return self.chat_room.messages.filter(
            created_at__gt=participant.last_read_at
        ).count()


class NotificationGroup(models.Model):
    """알림 그룹 모델"""
    
    name = models.CharField(max_length=100, verbose_name='그룹명')
    description = models.TextField(blank=True, verbose_name='설명')
    
    # 그룹 멤버
    members = models.ManyToManyField(
        User,
        related_name='notification_groups',
        verbose_name='멤버'
    )
    
    # 그룹 설정
    is_active = models.BooleanField(default=True, verbose_name='활성화')
    auto_add_new_users = models.BooleanField(default=False, verbose_name='신규 사용자 자동 추가')
    
    # 알림 설정
    notification_types = models.JSONField(default=list, verbose_name='알림 유형')
    priority_filter = models.CharField(
        max_length=10,
        choices=Notification.PRIORITY_CHOICES,
        default='normal',
        verbose_name='우선순위 필터'
    )
    
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='생성일')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='수정일')
    
    class Meta:
        verbose_name = '알림 그룹'
        verbose_name_plural = '알림 그룹들'
        ordering = ['name']
    
    def __str__(self):
        return self.name
    
    def add_member(self, user):
        """멤버 추가"""
        self.members.add(user)
    
    def remove_member(self, user):
        """멤버 제거"""
        self.members.remove(user)
    
    def get_member_count(self):
        """멤버 수 반환"""
        return self.members.count()


class NotificationAnalytics(models.Model):
    """알림 분석 모델"""
    
    date = models.DateField(verbose_name='날짜')
    organization = models.ForeignKey(
        Organization,
        on_delete=models.CASCADE,
        related_name='notification_analytics',
        verbose_name='소속 기관'
    )
    
    # 알림 통계
    total_notifications = models.PositiveIntegerField(default=0, verbose_name='총 알림 수')
    read_notifications = models.PositiveIntegerField(default=0, verbose_name='읽은 알림 수')
    unread_notifications = models.PositiveIntegerField(default=0, verbose_name='읽지 않은 알림 수')
    
    # 알림 유형별 통계
    notification_type_counts = models.JSONField(default=dict, verbose_name='알림 유형별 개수')
    priority_counts = models.JSONField(default=dict, verbose_name='우선순위별 개수')
    
    # 전송 방법별 통계
    delivery_method_counts = models.JSONField(default=dict, verbose_name='전송 방법별 개수')
    
    # 응답 시간 통계
    avg_response_time_minutes = models.FloatField(default=0, verbose_name='평균 응답 시간(분)')
    
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='생성일')
    
    class Meta:
        verbose_name = '알림 분석'
        verbose_name_plural = '알림 분석들'
        unique_together = ['date', 'organization']
        ordering = ['-date']
    
    def __str__(self):
        return f"{self.organization.name} - {self.date}"
    
    def get_read_rate(self):
        """읽음률 계산"""
        if self.total_notifications == 0:
            return 0
        return (self.read_notifications / self.total_notifications) * 100
