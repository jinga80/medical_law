from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils import timezone
from accounts.models import User, Organization, Branch
import uuid


class Workflow(models.Model):
    """워크플로우 모델"""
    
    STATUS_CHOICES = [
        ('draft', '작성중'),
        ('in_progress', '진행중'),
        ('completed', '완료'),
        ('cancelled', '취소'),
        ('on_hold', '보류'),
        ('overdue', '지연')
    ]
    
    PRIORITY_CHOICES = [
        ('low', '낮음'),
        ('medium', '보통'),
        ('high', '높음'),
        ('urgent', '긴급')
    ]
    
    # 기본 정보
    title = models.CharField(max_length=200, verbose_name='제목')
    description = models.TextField(blank=True, verbose_name='설명')
    
    # 담당자 및 상태
    assigned_to = models.ForeignKey(
        User, 
        on_delete=models.CASCADE, 
        related_name='assigned_workflows',
        verbose_name='담당자'
    )
    created_by = models.ForeignKey(
        User, 
        on_delete=models.CASCADE, 
        related_name='created_workflows',
        verbose_name='생성자'
    )
    
    # 상태 및 우선순위
    status = models.CharField(
        max_length=20, 
        choices=STATUS_CHOICES,
        default='draft',
        verbose_name='상태'
    )
    priority = models.CharField(
        max_length=10, 
        choices=PRIORITY_CHOICES,
        default='medium',
        verbose_name='우선순위'
    )
    
    # 날짜 정보
    due_date = models.DateTimeField(blank=True, null=True, verbose_name='마감일')
    started_at = models.DateTimeField(blank=True, null=True, verbose_name='시작일')
    completed_at = models.DateTimeField(blank=True, null=True, verbose_name='완료일')
    
    # 메타 정보
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='생성일')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='수정일')
    
    class Meta:
        verbose_name = '워크플로우'
        verbose_name_plural = '워크플로우들'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.title} ({self.get_status_display()})"
    
    @property
    def progress(self):
        """진행률 계산"""
        total_steps = self.steps.count()
        if total_steps == 0:
            return 0
        completed_steps = self.steps.filter(status='completed').count()
        return int((completed_steps / total_steps) * 100)
    
    @property
    def is_overdue(self):
        """지연 여부"""
        if self.due_date and self.status not in ['completed', 'cancelled']:
            return timezone.now() > self.due_date
        return False
    
    def get_status_color(self):
        """상태별 색상 반환"""
        colors = {
            'draft': 'secondary',
            'in_progress': 'primary',
            'completed': 'success',
            'cancelled': 'danger',
            'on_hold': 'warning',
            'overdue': 'danger'
        }
        return colors.get(self.status, 'secondary')
    
    def advance_to_next_step(self):
        """다음 단계로 진행"""
        current_step = self.steps.filter(status='in_progress').first()
        if current_step:
            current_step.status = 'completed'
            current_step.completed_at = timezone.now()
            current_step.save()
            
            next_step = self.steps.filter(status='pending').first()
            if next_step:
                next_step.status = 'in_progress'
                next_step.started_at = timezone.now()
                next_step.save()
            else:
                self.status = 'completed'
                self.completed_at = timezone.now()
                self.save()
    
    def create_action_log(self, action_type, old_value='', new_value='', user=None, request=None):
        """액션 로그 생성"""
        if not user:
            return
        
        # 액션 설명 생성
        action_descriptions = {
            'workflow_create': f"워크플로우 '{self.title}' 생성",
            'workflow_edit': f"워크플로우 '{self.title}' 수정",
            'workflow_delete': f"워크플로우 '{self.title}' 삭제",
            'status_change': f"워크플로우 상태를 '{dict(self.STATUS_CHOICES).get(old_value, old_value)}'에서 '{dict(self.STATUS_CHOICES).get(new_value, new_value)}'로 변경",
            'priority_change': f"우선순위를 '{dict(self.PRIORITY_CHOICES).get(old_value, old_value)}'에서 '{dict(self.PRIORITY_CHOICES).get(new_value, new_value)}'로 변경",
            'assignment_change': f"담당자를 '{old_value}'에서 '{new_value}'로 변경",
            'due_date_change': f"마감일을 '{old_value}'에서 '{new_value}'로 변경",
        }
        
        action_description = action_descriptions.get(action_type, f"{action_type} 액션 수행")
        
        # IP 주소와 사용자 에이전트 가져오기
        ip_address = None
        user_agent = None
        if request:
            ip_address = self.get_client_ip(request)
            user_agent = request.META.get('HTTP_USER_AGENT', '')
        
        WorkflowActionLog.objects.create(
            workflow=self,
            action_type=action_type,
            action_description=action_description,
            old_value=str(old_value),
            new_value=str(new_value),
            performed_by=user,
            ip_address=ip_address,
            user_agent=user_agent
        )
    
    def get_client_ip(self, request):
        """클라이언트 IP 주소 가져오기"""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip


class WorkflowStep(models.Model):
    """워크플로우 단계 모델"""
    
    STATUS_CHOICES = [
        ('pending', '대기중'),
        ('in_progress', '진행중'),
        ('completed', '완료'),
        ('cancelled', '취소'),
        ('on_hold', '보류')
    ]
    
    workflow = models.ForeignKey(
        Workflow, 
        on_delete=models.CASCADE,
        related_name='steps',
        verbose_name='워크플로우'
    )
    name = models.CharField(max_length=100, verbose_name='단계명')
    description = models.TextField(blank=True, verbose_name='설명')
    
    # 상태 및 담당자
    status = models.CharField(
        max_length=20, 
        choices=STATUS_CHOICES,
        default='pending',
        verbose_name='상태'
    )
    previous_status = models.CharField(
        max_length=20, 
        choices=STATUS_CHOICES,
        blank=True, 
        null=True,
        verbose_name='이전 상태'
    )
    assigned_to = models.ForeignKey(
        User, 
        on_delete=models.CASCADE, 
        blank=True, 
        null=True,
        verbose_name='담당자'
    )
    
    # 순서 및 날짜
    order = models.PositiveIntegerField(default=0, verbose_name='순서')
    due_date = models.DateTimeField(blank=True, null=True, verbose_name='마감일')
    started_at = models.DateTimeField(blank=True, null=True, verbose_name='시작일')
    completed_at = models.DateTimeField(blank=True, null=True, verbose_name='완료일')
    
    # 상태 변경 히스토리
    status_history = models.JSONField(default=list, verbose_name='상태 변경 히스토리')
    
    # 메모
    notes = models.TextField(blank=True, verbose_name='메모')
    
    # 메타 정보
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='생성일')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='수정일')
    
    class Meta:
        verbose_name = '워크플로우 단계'
        verbose_name_plural = '워크플로우 단계들'
        ordering = ['workflow', 'order']
    
    def __str__(self):
        return f"{self.workflow.title} - {self.name}"
    
    def save(self, *args, **kwargs):
        # 상태가 변경되었는지 확인
        if self.pk:
            old_instance = WorkflowStep.objects.get(pk=self.pk)
            if old_instance.status != self.status:
                # 이전 상태 저장
                self.previous_status = old_instance.status
                # 히스토리에 추가
                self.add_status_history(old_instance.status, self.status)
                # 액션 로그 생성 (사용자 정보는 나중에 전달)
                self.create_action_log('status_change', old_instance.status, self.status)
        else:
            # 새로 생성되는 경우 초기 상태를 히스토리에 추가
            self.add_status_history(None, self.status)
        
        super().save(*args, **kwargs)
    
    def add_status_history(self, old_status, new_status):
        """상태 변경 히스토리에 추가"""
        history_entry = {
            'timestamp': timezone.now().isoformat(),
            'old_status': old_status,
            'new_status': new_status,
            'old_status_display': dict(self.STATUS_CHOICES).get(old_status, '') if old_status else '',
            'new_status_display': dict(self.STATUS_CHOICES).get(new_status, '') if new_status else ''
        }
        self.status_history.append(history_entry)
    
    def can_revert_status(self):
        """상태 되돌리기 가능 여부"""
        return self.previous_status and self.previous_status != self.status
    
    def revert_to_previous_status(self, user, request=None):
        """이전 상태로 되돌리기"""
        if not self.can_revert_status():
            return False, "되돌릴 수 있는 이전 상태가 없습니다."
        
        old_status = self.status
        new_status = self.previous_status
        
        # 상태 되돌리기
        self.status = new_status
        self.previous_status = old_status
        
        # 완료 시간 처리
        if new_status == 'completed':
            if not self.completed_at:
                self.completed_at = timezone.now()
        else:
            self.completed_at = None
        
        # 시작 시간 처리
        if new_status == 'in_progress':
            if not self.started_at:
                self.started_at = timezone.now()
        elif new_status != 'in_progress':
            self.started_at = None
        
        # 히스토리에 추가
        self.add_status_history(old_status, new_status)
        
        # 액션 로그 생성
        self.create_action_log('status_revert', old_status, new_status, user, request)
        
        self.save()
        return True, f"상태가 '{dict(self.STATUS_CHOICES)[old_status]}'에서 '{dict(self.STATUS_CHOICES)[new_status]}'로 되돌려졌습니다."
    
    def create_action_log(self, action_type, old_value='', new_value='', user=None, request=None):
        """액션 로그 생성"""
        if not user:
            return
        
        # 액션 설명 생성
        action_descriptions = {
            'status_change': f"상태를 '{dict(self.STATUS_CHOICES).get(old_value, old_value)}'에서 '{dict(self.STATUS_CHOICES).get(new_value, new_value)}'로 변경",
            'status_revert': f"상태를 '{dict(self.STATUS_CHOICES).get(old_value, old_value)}'에서 '{dict(self.STATUS_CHOICES).get(new_value, new_value)}'로 되돌림",
            'step_complete': f"단계 '{self.name}' 완료",
            'step_revert': f"단계 '{self.name}' 되돌리기",
            'note_add': f"메모 추가: {new_value[:50]}...",
            'note_edit': f"메모 수정: {new_value[:50]}...",
            'assignment_change': f"담당자를 '{old_value}'에서 '{new_value}'로 변경",
            'due_date_change': f"마감일을 '{old_value}'에서 '{new_value}'로 변경",
        }
        
        action_description = action_descriptions.get(action_type, f"{action_type} 액션 수행")
        
        # IP 주소와 사용자 에이전트 가져오기
        ip_address = None
        user_agent = None
        if request:
            ip_address = self.get_client_ip(request)
            user_agent = request.META.get('HTTP_USER_AGENT', '')
        
        WorkflowActionLog.objects.create(
            workflow=self.workflow,
            step=self,
            action_type=action_type,
            action_description=action_description,
            old_value=str(old_value),
            new_value=str(new_value),
            performed_by=user,
            ip_address=ip_address,
            user_agent=user_agent
        )
    
    def get_client_ip(self, request):
        """클라이언트 IP 주소 가져오기"""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip
    
    @property
    def is_overdue(self):
        """지연 여부"""
        if self.due_date and self.status not in ['completed', 'cancelled']:
            return timezone.now() > self.due_date
        return False
    
    def get_status_color(self):
        """상태별 색상 반환"""
        colors = {
            'pending': 'secondary',
            'in_progress': 'primary',
            'completed': 'success',
            'cancelled': 'danger',
            'on_hold': 'warning'
        }
        return colors.get(self.status, 'secondary')


class WorkflowDocument(models.Model):
    """워크플로우 문서 모델"""
    
    DOCUMENT_TYPE_CHOICES = [
        ('resume', '이력서'),
        ('cover_letter', '자기소개서'),
        ('reference', '추천서'),
        ('contract', '계약서'),
        ('other', '기타')
    ]
    
    workflow = models.ForeignKey(
        Workflow, 
        on_delete=models.CASCADE,
        related_name='documents',
        verbose_name='워크플로우'
    )
    title = models.CharField(max_length=200, verbose_name='제목')
    document_type = models.CharField(
        max_length=20, 
        choices=DOCUMENT_TYPE_CHOICES,
        verbose_name='문서 유형'
    )
    file = models.FileField(upload_to='workflow_documents/', verbose_name='파일')
    uploaded_by = models.ForeignKey(
        User, 
        on_delete=models.CASCADE,
        verbose_name='업로드자'
    )
    
    # 메타 정보
    uploaded_at = models.DateTimeField(auto_now_add=True, verbose_name='업로드일')
    
    class Meta:
        verbose_name = '워크플로우 문서'
        verbose_name_plural = '워크플로우 문서들'
        ordering = ['-uploaded_at']
    
    def __str__(self):
        return f"{self.title} ({self.get_document_type_display()})"


class JobRequest(models.Model):
    """채용 요청서 모델 (병원 → 채용회사)"""
    
    EMPLOYMENT_TYPE_CHOICES = [
        ('full_time', '정규직'),
        ('part_time', '비정규직'),
        ('contract', '계약직'),
        ('intern', '인턴'),
        ('temporary', '임시직')
    ]
    
    URGENCY_LEVEL_CHOICES = [
        ('high', '높음'),
        ('medium', '보통'),
        ('low', '낮음')
    ]
    
    STATUS_CHOICES = [
        ('draft', '작성중'),
        ('submitted', '제출완료'),
        ('accepted', '접수완료'),
        ('in_progress', '진행중'),
        ('completed', '완료'),
        ('cancelled', '취소'),
        ('on_hold', '보류')
    ]
    
    # 기본 정보
    request_id = models.CharField(
        max_length=20, 
        unique=True, 
        verbose_name='요청 ID',
        help_text='자동 생성되는 고유 식별자'
    )
    requester = models.ForeignKey(
        User, 
        on_delete=models.CASCADE, 
        related_name='job_requests',
        verbose_name='요청자'
    )
    
    # 병원 정보
    hospital_name = models.CharField(max_length=100, verbose_name='병원명', default='')
    hospital_branch = models.CharField(max_length=50, verbose_name='지점명', default='')
    hospital_address = models.TextField(verbose_name='병원 주소', default='')
    hospital_phone = models.CharField(max_length=20, verbose_name='병원 연락처', default='')
    hospital_contact_person = models.CharField(max_length=50, verbose_name='담당자명', default='')
    
    # 채용 정보
    position_title = models.CharField(max_length=100, verbose_name='채용 포지션')
    department = models.CharField(max_length=50, verbose_name='부서')
    employment_type = models.CharField(
        max_length=20, 
        choices=EMPLOYMENT_TYPE_CHOICES,
        verbose_name='고용 형태'
    )
    
    # 급여 정보
    salary_min = models.IntegerField(
        blank=True, 
        null=True, 
        verbose_name='최소 급여',
        help_text='연봉 기준 (만원)'
    )
    salary_max = models.IntegerField(
        blank=True, 
        null=True, 
        verbose_name='최대 급여',
        help_text='연봉 기준 (만원)'
    )
    
    # 요구사항
    required_experience = models.TextField(verbose_name='필수 경력 요구사항')
    preferred_qualifications = models.TextField(blank=True, verbose_name='우대사항')
    job_description = models.TextField(verbose_name='업무 내용')
    working_hours = models.CharField(max_length=100, blank=True, verbose_name='근무 시간')
    working_location = models.CharField(max_length=200, blank=True, verbose_name='근무 장소')
    
    # 추가 요청사항
    special_requirements = models.TextField(blank=True, verbose_name='특별 요청사항')
    expected_start_date = models.DateField(blank=True, null=True, verbose_name='희망 입사일')
    recruitment_period = models.CharField(max_length=50, blank=True, verbose_name='채용 기간')
    
    # 추가 요청 관리
    additional_requests = models.JSONField(default=list, blank=True, verbose_name='추가 요청사항')
    is_locked = models.BooleanField(default=False, verbose_name='요청 잠금', help_text='요청이 잠기면 수정할 수 없습니다')
    locked_at = models.DateTimeField(blank=True, null=True, verbose_name='잠금 시간')
    locked_by = models.ForeignKey(
        User, 
        on_delete=models.SET_NULL, 
        blank=True, 
        null=True, 
        related_name='locked_job_requests',
        verbose_name='잠금 처리자'
    )
    
    # 긴급도 및 상태
    urgency_level = models.CharField(
        max_length=10, 
        choices=URGENCY_LEVEL_CHOICES,
        default='medium',
        verbose_name='긴급도'
    )
    status = models.CharField(
        max_length=20, 
        choices=STATUS_CHOICES,
        default='draft',
        verbose_name='상태'
    )
    
    # 시간 기록
    submitted_at = models.DateTimeField(blank=True, null=True, verbose_name='제출 시간')
    accepted_at = models.DateTimeField(blank=True, null=True, verbose_name='접수 시간')
    completed_at = models.DateTimeField(blank=True, null=True, verbose_name='완료 시간')
    
    # 채용담당 회사 확인 기록
    reviewed_by_headhunting = models.ForeignKey(
        User, 
        on_delete=models.SET_NULL, 
        blank=True, 
        null=True, 
        related_name='reviewed_job_requests',
        verbose_name='채용담당 확인자'
    )
    reviewed_at = models.DateTimeField(blank=True, null=True, verbose_name='채용담당 확인 시간')
    review_notes = models.TextField(blank=True, verbose_name='채용담당 검토 메모')
    
    # 병원 담당자 확인 기록
    reviewed_by_hospital = models.ForeignKey(
        User, 
        on_delete=models.SET_NULL, 
        blank=True, 
        null=True, 
        related_name='hospital_reviewed_job_requests',
        verbose_name='병원 담당 확인자'
    )
    hospital_reviewed_at = models.DateTimeField(blank=True, null=True, verbose_name='병원 담당 확인 시간')
    hospital_review_notes = models.TextField(blank=True, verbose_name='병원 담당 검토 메모')
    
    # 모니터링 정보
    last_activity_at = models.DateTimeField(blank=True, null=True, verbose_name='마지막 활동 시간')
    activity_count = models.IntegerField(default=0, verbose_name='활동 횟수')
    is_being_monitored = models.BooleanField(default=True, verbose_name='모니터링 활성화')
    
    # 메타 정보
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='생성일')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='수정일')
    
    class Meta:
        verbose_name = '채용 요청'
        verbose_name_plural = '채용 요청들'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.hospital_name} - {self.position_title} ({self.get_status_display()})"
    
    def save(self, *args, **kwargs):
        if not self.request_id:
            self.request_id = self.generate_request_id()
        super().save(*args, **kwargs)
    
    def generate_request_id(self):
        """요청 ID 생성"""
        import random
        import string
        prefix = f"JR{timezone.now().strftime('%Y%m')}"
        suffix = ''.join(random.choices(string.ascii_uppercase + string.digits, k=4))
        return f"{prefix}{suffix}"
    
    def get_duration_days(self):
        """요청 후 경과일 계산"""
        if self.submitted_at:
            return (timezone.now() - self.submitted_at).days
        return 0
    
    def is_urgent(self):
        """긴급 요청 여부"""
        return self.urgency_level == 'high'
    
    def can_be_edited(self):
        """수정 가능 여부"""
        return self.status in ['draft', 'submitted']
    
    def can_be_cancelled(self):
        """취소 가능 여부"""
        return self.status not in ['completed', 'cancelled']
    
    def add_additional_request(self, request_text, user):
        """추가 요청사항 추가"""
        if not self.is_locked:
            additional_request = {
                'id': len(self.additional_requests) + 1,
                'text': request_text,
                'created_at': timezone.now().isoformat(),
                'created_by': user.get_full_name(),
                'user_id': user.id
            }
            self.additional_requests.append(additional_request)
            self.save()
            return True
        return False
    
    def lock_request(self, user):
        """요청 잠금"""
        if not self.is_locked:
            self.is_locked = True
            self.locked_at = timezone.now()
            self.locked_by = user
            self.save()
            return True
        return False
    
    def unlock_request(self, user):
        """요청 잠금 해제 (관리자만 가능)"""
        if user.is_staff or user.is_superuser:
            self.is_locked = False
            self.locked_at = None
            self.locked_by = None
            self.save()
            return True
        return False
    
    def get_additional_requests_count(self):
        """추가 요청사항 개수"""
        return len(self.additional_requests)
    
    def is_editable_by_user(self, user):
        """사용자가 수정할 수 있는지 확인"""
        if user.is_superuser:
            return True
        if user == self.requester:
            return self.can_be_edited()
        return False
    
    def get_status_color(self):
        """상태별 색상 반환"""
        colors = {
            'draft': 'secondary',
            'submitted': 'info',
            'accepted': 'primary',
            'in_progress': 'warning',
            'completed': 'success',
            'cancelled': 'danger',
            'on_hold': 'warning'
        }
        return colors.get(self.status, 'secondary')
    
    def get_urgency_level_color(self):
        """긴급도별 색상 반환"""
        colors = {
            'low': 'success',
            'medium': 'warning',
            'high': 'danger'
        }
        return colors.get(self.urgency_level, 'secondary')
    
    def mark_as_reviewed_by_headhunting(self, user, notes=''):
        """채용담당 회사에서 확인 처리"""
        self.reviewed_by_headhunting = user
        self.reviewed_at = timezone.now()
        self.review_notes = notes
        self.last_activity_at = timezone.now()
        self.activity_count += 1
        self.save()
        
        # 활동 로그 생성
        self.create_review_log('headhunting_review', user, notes)
    
    def mark_as_reviewed_by_hospital(self, user, notes=''):
        """병원 담당자에서 확인 처리"""
        self.reviewed_by_hospital = user
        self.hospital_reviewed_at = timezone.now()
        self.hospital_review_notes = notes
        self.last_activity_at = timezone.now()
        self.activity_count += 1
        self.save()
        
        # 활동 로그 생성
        self.create_review_log('hospital_review', user, notes)
    
    def create_review_log(self, review_type, user, notes=''):
        """검토 로그 생성"""
        from accounts.models import UserActivity
        
        action_descriptions = {
            'headhunting_review': f"채용담당 회사에서 채용 요청 '{self.position_title}' 확인",
            'hospital_review': f"병원 담당자에서 채용 요청 '{self.position_title}' 확인"
        }
        
        description = action_descriptions.get(review_type, f"채용 요청 검토: {self.position_title}")
        if notes:
            description += f" (메모: {notes})"
        
        UserActivity.objects.create(
            user=user,
            activity_type='job_request_review',
            description=description,
            related_object_type='JobRequest',
            related_object_id=self.id,
            related_object_name=self.position_title
        )
    
    def can_be_reviewed_by_headhunting(self, user):
        """채용담당 회사 사용자가 확인할 수 있는지"""
        return user.is_headhunting_user() and self.status in ['submitted', 'accepted', 'in_progress']
    
    def can_be_reviewed_by_hospital(self, user):
        """병원 사용자가 확인할 수 있는지"""
        return user.is_hospital_user() and self.status in ['submitted', 'accepted', 'in_progress']
    
    def get_review_status(self):
        """검토 상태 반환"""
        if self.reviewed_by_headhunting and self.reviewed_by_hospital:
            return 'both_reviewed'
        elif self.reviewed_by_headhunting:
            return 'headhunting_reviewed'
        elif self.reviewed_by_hospital:
            return 'hospital_reviewed'
        else:
            return 'not_reviewed'
    
    def get_review_status_display(self):
        """검토 상태 표시명"""
        status_map = {
            'both_reviewed': '양측 확인 완료',
            'headhunting_reviewed': '채용담당 확인 완료',
            'hospital_reviewed': '병원 확인 완료',
            'not_reviewed': '미확인'
        }
        return status_map.get(self.get_review_status(), '미확인')
    
    def get_review_status_color(self):
        """검토 상태 색상"""
        colors = {
            'both_reviewed': 'success',
            'headhunting_reviewed': 'info',
            'hospital_reviewed': 'warning',
            'not_reviewed': 'secondary'
        }
        return colors.get(self.get_review_status(), 'secondary')
    
    def advance_to_workflow(self, user):
        """워크플로우로 진행"""
        if self.status == 'submitted':
            self.status = 'accepted'
            self.accepted_at = timezone.now()
            self.last_activity_at = timezone.now()
            self.activity_count += 1
            self.save()
            
            # 워크플로우 생성
            self.create_workflow_from_request(user)
            
            # 활동 로그 생성
            self.create_workflow_log(user)
            
            return True
        return False
    
    def create_workflow_from_request(self, user):
        """채용 요청으로부터 워크플로우 생성"""
        workflow = Workflow.objects.create(
            title=f"{self.hospital_name} - {self.position_title}",
            description=self.job_description,
            assigned_to=user,
            created_by=self.requester,
            status='in_progress',
            priority='high' if self.is_urgent() else 'medium',
            started_at=timezone.now()
        )
        
        # 워크플로우 진행 상황 생성
        WorkflowProgress.objects.create(
            job_request=self,
            current_step='job_request',
            step_completion_rate=100,
            overall_progress=5,
            target_completion_date=timezone.now().date() + timezone.timedelta(days=14)
        )
        
        return workflow
    
    def create_workflow_log(self, user):
        """워크플로우 생성 로그"""
        from accounts.models import UserActivity
        
        UserActivity.objects.create(
            user=user,
            activity_type='workflow_create',
            description=f"채용 요청 '{self.position_title}'을 워크플로우로 진행",
            related_object_type='JobRequest',
            related_object_id=self.id,
            related_object_name=self.position_title
        )
    
    def get_monitoring_info(self):
        """모니터링 정보 반환"""
        return {
            'request_id': self.request_id,
            'position_title': self.position_title,
            'hospital_name': self.hospital_name,
            'status': self.get_status_display(),
            'urgency_level': self.get_urgency_level_display(),
            'created_at': self.created_at,
            'submitted_at': self.submitted_at,
            'last_activity_at': self.last_activity_at,
            'activity_count': self.activity_count,
            'review_status': self.get_review_status_display(),
            'duration_days': self.get_duration_days(),
            'is_urgent': self.is_urgent(),
            'can_advance': self.status == 'submitted'
        }


class JobRequestTemplate(models.Model):
    """채용 요청 템플릿 모델"""
    
    EMPLOYMENT_TYPE_CHOICES = [
        ('full_time', '정규직'),
        ('part_time', '비정규직'),
        ('contract', '계약직'),
        ('intern', '인턴'),
        ('temporary', '임시직')
    ]
    
    URGENCY_LEVEL_CHOICES = [
        ('high', '높음'),
        ('medium', '보통'),
        ('low', '낮음')
    ]
    
    # 기본 정보
    name = models.CharField(max_length=100, verbose_name='템플릿명')
    description = models.TextField(blank=True, verbose_name='설명')
    is_default = models.BooleanField(default=False, verbose_name='기본 템플릿')
    is_active = models.BooleanField(default=True, verbose_name='활성화')
    
    # 생성자
    created_by = models.ForeignKey(
        User, 
        on_delete=models.CASCADE,
        verbose_name='생성자'
    )
    
    # 지점 정보
    branch = models.ForeignKey(
        Branch, 
        on_delete=models.CASCADE,
        blank=True,
        null=True,
        verbose_name='소속 지점',
        help_text='지점별 템플릿 관리 (선택사항)'
    )
    
    # 병원 정보 (기본값)
    hospital_name = models.CharField(max_length=100, verbose_name='병원명', default='')
    hospital_branch = models.CharField(max_length=50, verbose_name='지점명', default='')
    hospital_address = models.TextField(verbose_name='병원 주소', default='')
    hospital_phone = models.CharField(max_length=20, verbose_name='병원 연락처', default='')
    hospital_contact_person = models.CharField(max_length=50, verbose_name='담당자명', default='')
    
    # 채용 정보 (기본값)
    position_title = models.CharField(max_length=100, verbose_name='채용 포지션')
    department = models.CharField(max_length=50, verbose_name='부서')
    employment_type = models.CharField(
        max_length=20, 
        choices=EMPLOYMENT_TYPE_CHOICES,
        verbose_name='고용 형태'
    )
    
    # 급여 정보 (기본값)
    salary_min = models.IntegerField(
        blank=True, 
        null=True, 
        verbose_name='최소 급여',
        help_text='연봉 기준 (만원)'
    )
    salary_max = models.IntegerField(
        blank=True, 
        null=True, 
        verbose_name='최대 급여',
        help_text='연봉 기준 (만원)'
    )
    
    # 요구사항 (기본값)
    required_experience = models.TextField(verbose_name='필수 경력 요구사항')
    preferred_qualifications = models.TextField(blank=True, verbose_name='우대사항')
    job_description = models.TextField(verbose_name='업무 내용')
    working_hours = models.CharField(max_length=100, blank=True, verbose_name='근무 시간')
    working_location = models.CharField(max_length=200, blank=True, verbose_name='근무 장소')
    
    # 추가 요청사항 (기본값)
    special_requirements = models.TextField(blank=True, verbose_name='특별 요청사항')
    expected_start_date = models.DateField(blank=True, null=True, verbose_name='희망 입사일')
    recruitment_period = models.CharField(max_length=50, blank=True, verbose_name='채용 기간')
    
    # 긴급도 (기본값)
    urgency_level = models.CharField(
        max_length=10, 
        choices=URGENCY_LEVEL_CHOICES,
        default='medium',
        verbose_name='긴급도'
    )
    
    # 메타 정보
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='생성일')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='수정일')
    
    class Meta:
        verbose_name = '채용 요청 템플릿'
        verbose_name_plural = '채용 요청 템플릿들'
        ordering = ['-is_default', 'name']
    
    def __str__(self):
        return self.name
    
    def save(self, *args, **kwargs):
        # 기본 템플릿이 하나만 있도록 보장
        if self.is_default:
            JobRequestTemplate.objects.filter(is_default=True).update(is_default=False)
        super().save(*args, **kwargs)
    
    def create_job_request_from_template(self, requester, **kwargs):
        """템플릿에서 채용 요청 생성"""
        job_request = JobRequest(
            requester=requester,
            hospital_name=kwargs.get('hospital_name', self.hospital_name),
            hospital_branch=kwargs.get('hospital_branch', self.hospital_branch),
            hospital_address=kwargs.get('hospital_address', self.hospital_address),
            hospital_phone=kwargs.get('hospital_phone', self.hospital_phone),
            hospital_contact_person=kwargs.get('hospital_contact_person', self.hospital_contact_person),
            position_title=kwargs.get('position_title', self.position_title),
            department=kwargs.get('department', self.department),
            employment_type=kwargs.get('employment_type', self.employment_type),
            salary_min=kwargs.get('salary_min', self.salary_min),
            salary_max=kwargs.get('salary_max', self.salary_max),
            required_experience=kwargs.get('required_experience', self.required_experience),
            preferred_qualifications=kwargs.get('preferred_qualifications', self.preferred_qualifications),
            job_description=kwargs.get('job_description', self.job_description),
            working_hours=kwargs.get('working_hours', self.working_hours),
            working_location=kwargs.get('working_location', self.working_location),
            special_requirements=kwargs.get('special_requirements', self.special_requirements),
            expected_start_date=kwargs.get('expected_start_date', self.expected_start_date),
            recruitment_period=kwargs.get('recruitment_period', self.recruitment_period),
            urgency_level=kwargs.get('urgency_level', self.urgency_level),
        )
        job_request.save()
        return job_request


class WorkflowTemplate(models.Model):
    """워크플로우 템플릿"""
    
    name = models.CharField(max_length=100, verbose_name='템플릿명')
    description = models.TextField(blank=True, verbose_name='설명')
    is_default = models.BooleanField(default=False, verbose_name='기본 템플릿')
    is_active = models.BooleanField(default=True, verbose_name='활성화')
    
    # 단계별 설정
    steps_config = models.JSONField(default=dict, verbose_name='단계 설정')
    
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='생성일')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='수정일')
    
    class Meta:
        verbose_name = '워크플로우 템플릿'
        verbose_name_plural = '워크플로우 템플릿들'
        ordering = ['name']
    
    def __str__(self):
        return self.name
    
    def create_workflow_steps(self, workflow):
        """워크플로우 단계 생성"""
        for i, step_config in enumerate(self.steps_config.get('steps', [])):
            WorkflowStep.objects.create(
                workflow=workflow,
                name=step_config['name'],
                description=step_config.get('description', ''),
                order=i
            )


class JobPosting(models.Model):
    """구인 공고 모델"""
    
    POSTING_STATUS_CHOICES = [
        ('draft', '작성중'),
        ('published', '게시중'),
        ('paused', '일시중지'),
        ('closed', '마감'),
        ('expired', '만료')
    ]
    
    # 연결 정보
    job_request = models.OneToOneField(
        JobRequest, 
        on_delete=models.CASCADE,
        related_name='job_posting',
        verbose_name='채용 요청'
    )
    created_by = models.ForeignKey(
        User, 
        on_delete=models.CASCADE,
        verbose_name='작성자'
    )
    
    # 공고 정보
    posting_id = models.CharField(
        max_length=20, 
        unique=True, 
        verbose_name='공고 ID',
        help_text='자동 생성되는 고유 식별자'
    )
    title = models.CharField(max_length=200, verbose_name='공고 제목')
    summary = models.TextField(verbose_name='공고 요약')
    detailed_description = models.TextField(verbose_name='상세 설명')
    
    # 채용 조건
    requirements = models.TextField(verbose_name='자격 요건')
    preferred_qualifications = models.TextField(blank=True, verbose_name='우대사항')
    benefits = models.TextField(blank=True, verbose_name='복리후생')
    
    # 일정 관리
    posting_date = models.DateTimeField(verbose_name='게시일')
    closing_date = models.DateTimeField(verbose_name='마감일')
    application_deadline = models.DateTimeField(verbose_name='지원 마감일')
    
    # 채용 공고 링크 및 이미지 (실제 게시된 내용)
    posting_url = models.URLField(
        blank=True, 
        null=True, 
        verbose_name='채용 공고 링크',
        help_text='실제 채용 공고가 게시된 URL'
    )
    posting_image = models.ImageField(
        upload_to='job_postings/',
        blank=True, 
        null=True, 
        verbose_name='채용 공고 이미지',
        help_text='채용 공고 스크린샷 또는 관련 이미지'
    )
    posting_platform = models.CharField(
        max_length=50, 
        blank=True, 
        verbose_name='게시 플랫폼',
        help_text='예: 잡코리아, 사람인, 인크루트 등'
    )
    
    # 상태 관리
    status = models.CharField(
        max_length=20, 
        choices=POSTING_STATUS_CHOICES,
        default='draft',
        verbose_name='공고 상태'
    )
    is_featured = models.BooleanField(default=False, verbose_name='주요 공고')
    view_count = models.IntegerField(default=0, verbose_name='조회수')
    application_count = models.IntegerField(default=0, verbose_name='지원자 수')
    
    # 메타 정보
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='생성일')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='수정일')
    published_at = models.DateTimeField(blank=True, null=True, verbose_name='게시일')
    
    class Meta:
        verbose_name = '구인 공고'
        verbose_name_plural = '구인 공고들'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.title} ({self.get_status_display()})"
    
    def save(self, *args, **kwargs):
        if not self.posting_id:
            self.posting_id = self.generate_posting_id()
        super().save(*args, **kwargs)
    
    def generate_posting_id(self):
        """공고 ID 생성"""
        import random
        import string
        prefix = f"JP{timezone.now().strftime('%Y%m')}"
        suffix = ''.join(random.choices(string.ascii_uppercase + string.digits, k=4))
        return f"{prefix}{suffix}"
    
    def is_active(self):
        """활성 공고 여부"""
        now = timezone.now()
        return (self.status == 'published' and 
                self.posting_date <= now <= self.closing_date)
    
    def is_expired(self):
        """만료 여부"""
        return timezone.now() > self.closing_date
    
    def get_days_remaining(self):
        """남은 일수 계산"""
        if self.is_active():
            return (self.closing_date - timezone.now()).days
        return 0
    
    def increment_view_count(self):
        """조회수 증가"""
        self.view_count += 1
        self.save(update_fields=['view_count'])
    
    def increment_application_count(self):
        """지원자 수 증가"""
        self.application_count += 1
        self.save(update_fields=['application_count'])
    
    @property
    def has_posting_info(self):
        """채용 공고 정보가 있는지 확인"""
        return bool(self.posting_url or self.posting_image)
    
    def get_platform_display_name(self):
        """플랫폼 표시명 반환"""
        if not self.posting_platform:
            return "기타"
        
        platform_names = {
            'jobkorea': '잡코리아',
            'saramin': '사람인',
            'incruit': '인크루트',
            'wanted': '원티드',
            'linkedin': '링크드인',
            'indeed': '인디드',
            'other': '기타'
        }
        return platform_names.get(self.posting_platform, self.posting_platform)


class JobApplication(models.Model):
    """구인 공고 지원 모델"""
    
    APPLICATION_STATUS_CHOICES = [
        ('submitted', '지원완료'),
        ('under_review', '검토중'),
        ('shortlisted', '서류합격'),
        ('rejected', '서류불합격'),
        ('withdrawn', '지원철회')
    ]
    
    # 연결 정보
    job_posting = models.ForeignKey(
        JobPosting, 
        on_delete=models.CASCADE,
        related_name='applications',
        verbose_name='구인 공고'
    )
    applicant = models.ForeignKey(
        User, 
        on_delete=models.CASCADE,
        verbose_name='지원자'
    )
    
    # 지원 정보
    application_id = models.CharField(
        max_length=20, 
        unique=True, 
        verbose_name='지원 ID'
    )
    cover_letter = models.TextField(verbose_name='자기소개서')
    resume_file = models.FileField(
        upload_to='applications/resumes/',
        verbose_name='이력서'
    )
    portfolio_file = models.FileField(
        upload_to='applications/portfolios/',
        blank=True,
        verbose_name='포트폴리오'
    )
    
    # 상태 관리
    status = models.CharField(
        max_length=20, 
        choices=APPLICATION_STATUS_CHOICES,
        default='submitted',
        verbose_name='지원 상태'
    )
    
    # 메타 정보
    submitted_at = models.DateTimeField(auto_now_add=True, verbose_name='지원일')
    reviewed_at = models.DateTimeField(blank=True, null=True, verbose_name='검토일')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='수정일')
    
    class Meta:
        verbose_name = '구인 공고 지원'
        verbose_name_plural = '구인 공고 지원들'
        ordering = ['-submitted_at']
        unique_together = ['job_posting', 'applicant']
    
    def __str__(self):
        return f"{self.application_id} - {self.applicant.get_full_name()} ({self.get_status_display()})"
    
    def save(self, *args, **kwargs):
        """저장 시 application_id 자동 생성"""
        if not self.application_id:
            self.application_id = self.generate_application_id()
        super().save(*args, **kwargs)
    
    def generate_application_id(self):
        """지원 ID 자동 생성 (APP + YYYYMMDD + 4자리 랜덤)"""
        import random
        date_str = timezone.now().strftime('%Y%m%d')
        random_str = str(random.randint(1000, 9999))
        return f"APP{date_str}{random_str}"


class WorkflowProgress(models.Model):
    """워크플로우 진행 상황 모델"""
    
    STEP_CHOICES = [
        ('job_request', '채용 요청'),
        ('job_posting', '구인 공고'),
        ('candidate_collection', '지원자 모집'),
        ('document_screening', '서류 심사'),
        ('interview_scheduling', '면접 일정 조율'),
        ('interview', '면접 진행'),
        ('evaluation', '면접 평가'),
        ('final_decision', '최종 결정'),
        ('hiring', '채용 확정')
    ]
    
    STEP_WEIGHTS = {
        'job_request': 5,
        'job_posting': 10,
        'candidate_collection': 15,
        'document_screening': 20,
        'interview_scheduling': 15,
        'interview': 15,
        'evaluation': 10,
        'final_decision': 5,
        'hiring': 5
    }
    
    job_request = models.OneToOneField(
        JobRequest, 
        on_delete=models.CASCADE,
        related_name='workflow_progress',
        verbose_name='채용 요청'
    )
    
    # 현재 단계
    current_step = models.CharField(
        max_length=30,
        choices=STEP_CHOICES,
        default='job_request',
        verbose_name='현재 단계'
    )
    
    # 진행률
    step_completion_rate = models.IntegerField(
        default=0,
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        verbose_name='단계 완료율',
        help_text='0-100%'
    )
    overall_progress = models.IntegerField(
        default=0,
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        verbose_name='전체 진행률',
        help_text='0-100%'
    )
    
    # 일정 관리
    estimated_completion_date = models.DateField(
        blank=True, 
        null=True, 
        verbose_name='예상 완료일'
    )
    actual_completion_date = models.DateField(
        blank=True, 
        null=True, 
        verbose_name='실제 완료일'
    )
    target_completion_date = models.DateField(
        verbose_name='목표 완료일',
        help_text='2주 이내 완료 목표'
    )
    
    # 병목 지점
    bottlenecks = models.JSONField(
        default=list,
        verbose_name='병목 지점',
        help_text='진행을 막고 있는 문제점들'
    )
    
    # 성과 지표
    total_candidates = models.IntegerField(
        default=0,
        verbose_name='총 지원자 수'
    )
    screened_candidates = models.IntegerField(
        default=0,
        verbose_name='서류 심사 완료 수'
    )
    interviewed_candidates = models.IntegerField(
        default=0,
        verbose_name='면접 완료 수'
    )
    hired_candidates = models.IntegerField(
        default=0,
        verbose_name='채용 확정 수'
    )
    
    # 시간 추적
    step_start_times = models.JSONField(
        default=dict,
        verbose_name='단계별 시작 시간'
    )
    step_end_times = models.JSONField(
        default=dict,
        verbose_name='단계별 완료 시간'
    )
    step_durations = models.JSONField(
        default=dict,
        verbose_name='단계별 소요 시간'
    )
    
    # 상태 관리
    is_on_track = models.BooleanField(
        default=True,
        verbose_name='일정 준수 여부'
    )
    is_completed = models.BooleanField(
        default=False,
        verbose_name='완료 여부'
    )
    
    # 메타 정보
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='생성일')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='수정일')
    
    class Meta:
        verbose_name = '워크플로우 진행 상황'
        verbose_name_plural = '워크플로우 진행 상황들'
        ordering = ['-updated_at']
    
    def __str__(self):
        return f"{self.job_request.position_title} - {self.get_current_step_display()} ({self.overall_progress}%)"
    
    def save(self, *args, **kwargs):
        """저장 시 진행률 자동 계산"""
        self.calculate_progress()
        super().save(*args, **kwargs)
    
    def calculate_progress(self):
        """전체 진행률 계산"""
        total_weight = sum(self.STEP_WEIGHTS.values())
        current_weight = 0
        
        # 완료된 단계들의 가중치 합계
        for step, weight in self.STEP_WEIGHTS.items():
            if self.is_step_completed(step):
                current_weight += weight
            elif step == self.current_step:
                # 현재 단계는 완료율만큼 가중치 적용
                current_weight += weight * (self.step_completion_rate / 100)
        
        self.overall_progress = int((current_weight / total_weight) * 100)
        
        # 일정 준수 여부 확인
        if self.estimated_completion_date and self.target_completion_date:
            self.is_on_track = self.estimated_completion_date <= self.target_completion_date
        
        # 완료 여부 확인
        self.is_completed = self.overall_progress >= 100
    
    def is_step_completed(self, step):
        """특정 단계 완료 여부"""
        if step in self.step_end_times:
            return True
        
        # 단계별 완료 조건 확인
        if step == 'job_request':
            return self.job_request.status in ['submitted', 'accepted', 'in_progress', 'completed']
        elif step == 'job_posting':
            return hasattr(self.job_request, 'job_posting') and self.job_request.job_posting.status == 'published'
        elif step == 'candidate_collection':
            return self.total_candidates > 0
        elif step == 'document_screening':
            return self.screened_candidates > 0
        elif step == 'interview_scheduling':
            return self.interviewed_candidates > 0
        elif step == 'interview':
            return self.interviewed_candidates > 0
        elif step == 'evaluation':
            return self.interviewed_candidates > 0
        elif step == 'final_decision':
            return self.hired_candidates > 0
        elif step == 'hiring':
            return self.hired_candidates > 0
        
        return False
    
    def start_step(self, step):
        """단계 시작"""
        self.current_step = step
        self.step_start_times[step] = timezone.now().isoformat()
        self.step_completion_rate = 0
        self.save()
    
    def complete_step(self, step):
        """단계 완료"""
        self.step_end_times[step] = timezone.now().isoformat()
        self.step_completion_rate = 100
        
        # 소요 시간 계산
        if step in self.step_start_times:
            start_time = timezone.datetime.fromisoformat(self.step_start_times[step])
            end_time = timezone.now()
            duration = end_time - start_time
            self.step_durations[step] = duration.total_seconds() / 3600  # 시간 단위
        
        # 다음 단계로 이동
        self.move_to_next_step()
        self.save()
    
    def move_to_next_step(self):
        """다음 단계로 이동"""
        step_order = [choice[0] for choice in self.STEP_CHOICES]
        current_index = step_order.index(self.current_step)
        
        if current_index < len(step_order) - 1:
            next_step = step_order[current_index + 1]
            self.current_step = next_step
            self.step_completion_rate = 0
        else:
            # 모든 단계 완료
            self.is_completed = True
            self.actual_completion_date = timezone.now().date()
    
    def update_step_progress(self, progress_percentage):
        """단계 진행률 업데이트"""
        self.step_completion_rate = min(100, max(0, progress_percentage))
        self.save()
    
    def add_bottleneck(self, bottleneck_description):
        """병목 지점 추가"""
        if bottleneck_description not in self.bottlenecks:
            self.bottlenecks.append(bottleneck_description)
            self.save()
    
    def remove_bottleneck(self, bottleneck_description):
        """병목 지점 제거"""
        if bottleneck_description in self.bottlenecks:
            self.bottlenecks.remove(bottleneck_description)
            self.save()
    
    def get_days_remaining(self):
        """목표 완료일까지 남은 일수"""
        if self.target_completion_date:
            remaining = self.target_completion_date - timezone.now().date()
            return max(0, remaining.days)
        return None
    
    def get_days_overdue(self):
        """지연 일수"""
        if self.target_completion_date and self.actual_completion_date:
            overdue = self.actual_completion_date - self.target_completion_date
            return max(0, overdue.days)
        return 0
    
    def is_urgent(self):
        """긴급 여부 (목표일 3일 이내)"""
        days_remaining = self.get_days_remaining()
        return days_remaining is not None and days_remaining <= 3


class WorkflowActionLog(models.Model):
    """워크플로우 액션 로그 모델"""
    
    ACTION_CHOICES = [
        ('status_change', '상태 변경'),
        ('status_revert', '상태 되돌리기'),
        ('step_complete', '단계 완료'),
        ('step_revert', '단계 되돌리기'),
        ('note_add', '메모 추가'),
        ('note_edit', '메모 수정'),
        ('assignment_change', '담당자 변경'),
        ('due_date_change', '마감일 변경'),
        ('workflow_create', '워크플로우 생성'),
        ('workflow_edit', '워크플로우 수정'),
        ('workflow_delete', '워크플로우 삭제'),
        ('step_create', '단계 생성'),
        ('step_edit', '단계 수정'),
        ('step_delete', '단계 삭제'),
    ]
    
    # 연결 정보
    workflow = models.ForeignKey(
        'Workflow',
        on_delete=models.CASCADE,
        related_name='action_logs',
        verbose_name='워크플로우'
    )
    step = models.ForeignKey(
        'WorkflowStep',
        on_delete=models.CASCADE,
        related_name='action_logs',
        blank=True,
        null=True,
        verbose_name='워크플로우 단계'
    )
    
    # 액션 정보
    action_type = models.CharField(
        max_length=20,
        choices=ACTION_CHOICES,
        verbose_name='액션 유형'
    )
    action_description = models.TextField(verbose_name='액션 설명')
    
    # 변경 정보
    old_value = models.TextField(blank=True, verbose_name='이전 값')
    new_value = models.TextField(blank=True, verbose_name='새 값')
    
    # 사용자 정보
    performed_by = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        verbose_name='실행자'
    )
    
    # 메타 정보
    performed_at = models.DateTimeField(auto_now_add=True, verbose_name='실행 시간')
    ip_address = models.GenericIPAddressField(blank=True, null=True, verbose_name='IP 주소')
    user_agent = models.TextField(blank=True, verbose_name='사용자 에이전트')
    
    class Meta:
        verbose_name = '워크플로우 액션 로그'
        verbose_name_plural = '워크플로우 액션 로그들'
        ordering = ['-performed_at']
    
    def __str__(self):
        return f"{self.workflow.title} - {self.get_action_type_display()} ({self.performed_at.strftime('%Y-%m-%d %H:%M')})"
