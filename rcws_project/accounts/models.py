from django.db import models
from django.contrib.auth.models import AbstractUser
from django.core.validators import MinValueValidator, MaxValueValidator


class Organization(models.Model):
    """기관 모델 - 리버스클리닉, 케이지아웃소싱, 메디킹 관리기관"""
    
    ORG_TYPE_CHOICES = [
        ('hospital', '병원'),
        ('headhunting', '헤드헌팅'),
        ('admin', '관리기관')
    ]
    
    name = models.CharField(max_length=100, verbose_name='기관명')
    org_type = models.CharField(
        max_length=20, 
        choices=ORG_TYPE_CHOICES,
        verbose_name='기관 유형'
    )
    address = models.TextField(blank=True, verbose_name='주소')
    phone = models.CharField(max_length=20, blank=True, verbose_name='전화번호')
    email = models.EmailField(blank=True, verbose_name='이메일')
    description = models.TextField(blank=True, verbose_name='기관 설명')
    is_active = models.BooleanField(default=True, verbose_name='활성화 여부')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='생성일')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='수정일')
    
    class Meta:
        verbose_name = '기관'
        verbose_name_plural = '기관들'
        ordering = ['name']
    
    def __str__(self):
        return f"{self.get_org_type_display()} - {self.name}"


class Branch(models.Model):
    """지점 모델 - 병원의 여러 지점을 관리"""
    
    organization = models.ForeignKey(
        Organization, 
        on_delete=models.CASCADE,
        verbose_name='소속 기관',
        related_name='branches'
    )
    name = models.CharField(max_length=100, verbose_name='지점명')
    address = models.TextField(verbose_name='지점 주소')
    phone = models.CharField(max_length=20, verbose_name='지점 전화번호')
    email = models.EmailField(blank=True, verbose_name='지점 이메일')
    manager_name = models.CharField(max_length=50, blank=True, verbose_name='지점장명')
    manager_phone = models.CharField(max_length=20, blank=True, verbose_name='지점장 연락처')
    description = models.TextField(blank=True, verbose_name='지점 설명')
    is_active = models.BooleanField(default=True, verbose_name='활성화 여부')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='생성일')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='수정일')
    
    class Meta:
        verbose_name = '지점'
        verbose_name_plural = '지점들'
        ordering = ['organization', 'name']
        unique_together = ['organization', 'name']
    
    def __str__(self):
        return f"{self.organization.name} - {self.name}"
    
    def get_full_name(self):
        """전체 지점명 반환"""
        return f"{self.organization.name} {self.name}"


class User(AbstractUser):
    """사용자 모델 - AbstractUser를 상속받아 확장"""
    
    ROLE_CHOICES = [
        ('hospital_hr', '병원 인사담당자'),
        ('hospital_manager', '병원 부서 관리자'),
        ('hh_ceo', '헤드헌팅 대표'),
        ('hh_manager', '헤드헌팅 팀장'),
        ('hh_staff', '헤드헌팅 대리'),
        ('system_admin', '시스템 관리자')
    ]
    
    organization = models.ForeignKey(
        Organization, 
        on_delete=models.CASCADE,
        verbose_name='소속 기관',
        related_name='users'
    )
    branch = models.ForeignKey(
        Branch, 
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name='소속 지점',
        related_name='users'
    )
    role = models.CharField(
        max_length=20, 
        choices=ROLE_CHOICES,
        verbose_name='역할'
    )
    phone = models.CharField(max_length=20, blank=True, verbose_name='연락처')
    department = models.CharField(max_length=50, blank=True, verbose_name='부서')
    position = models.CharField(max_length=50, blank=True, verbose_name='직책')
    employee_id = models.CharField(max_length=20, blank=True, verbose_name='사원번호')
    is_active_user = models.BooleanField(default=True, verbose_name='활성 사용자')
    profile_image = models.ImageField(
        upload_to='profile_images/',
        blank=True,
        null=True,
        verbose_name='프로필 이미지'
    )
    last_activity = models.DateTimeField(auto_now=True, verbose_name='마지막 활동')
    
    class Meta:
        verbose_name = '사용자'
        verbose_name_plural = '사용자들'
        ordering = ['organization', 'role', 'username']
    
    def __str__(self):
        return f"{self.get_full_name()} ({self.get_role_display()})"
    
    def get_organization_name(self):
        """소속 기관명 반환"""
        return self.organization.name
    
    def get_role_display_name(self):
        """역할 표시명 반환"""
        return self.get_role_display()
    
    def is_hospital_user(self):
        """병원 사용자 여부 확인"""
        return self.organization.org_type == 'hospital'
    
    def is_headhunting_user(self):
        """헤드헌팅 사용자 여부 확인"""
        return self.organization.org_type == 'headhunting'
    
    def is_admin_user(self):
        """관리자 사용자 여부 확인"""
        return self.organization.org_type == 'admin' or self.role == 'system_admin'
    
    def can_manage_workflow(self):
        """워크플로우 관리 권한 확인"""
        return self.role in ['hospital_hr', 'hospital_manager', 'hh_ceo', 'hh_manager', 'system_admin']
    
    def can_review_candidates(self):
        """후보자 검토 권한 확인"""
        return self.role in ['hospital_hr', 'hospital_manager', 'system_admin']
    
    def can_recommend_candidates(self):
        """후보자 추천 권한 확인"""
        return self.role in ['hh_ceo', 'hh_manager', 'hh_staff']
    
    def can_create_job_request(self):
        """채용 요청 생성 권한 확인"""
        return self.role in ['hospital_hr', 'hospital_manager', 'system_admin']
    
    def can_edit_job_request(self):
        """채용 요청 수정 권한 확인"""
        return self.role in ['hospital_hr', 'hospital_manager', 'system_admin']
    
    def can_submit_job_request(self):
        """채용 요청 제출 권한 확인"""
        return self.role in ['hospital_hr', 'hospital_manager', 'system_admin']
    
    def can_create_candidate(self):
        """후보자 생성 권한 확인"""
        return self.role in ['hh_ceo', 'hh_manager', 'hh_staff', 'system_admin']
    
    def can_edit_candidate(self):
        """후보자 수정 권한 확인"""
        return self.role in ['hh_ceo', 'hh_manager', 'hh_staff', 'system_admin']
    
    def can_create_evaluation(self):
        """평가 생성 권한 확인"""
        return self.role in ['hospital_hr', 'hospital_manager', 'system_admin']
    
    def can_edit_evaluation(self):
        """평가 수정 권한 확인"""
        return self.role in ['hospital_hr', 'hospital_manager', 'system_admin']
    
    def can_create_report(self):
        """보고서 생성 권한 확인"""
        return self.role in ['hospital_hr', 'hospital_manager', 'hh_ceo', 'hh_manager', 'system_admin']
    
    def can_edit_report(self):
        """보고서 수정 권한 확인"""
        return self.role in ['hospital_hr', 'hospital_manager', 'hh_ceo', 'hh_manager', 'system_admin']
    
    def can_access_admin(self):
        """관리자 페이지 접근 권한 확인"""
        return self.role == 'system_admin' or self.is_superuser
    
    def can_manage_users(self):
        """사용자 관리 권한 확인"""
        return self.role == 'system_admin' or self.is_superuser
    
    def can_view_all_organizations(self):
        """모든 기관 데이터 조회 권한 확인"""
        return self.role == 'system_admin' or self.is_superuser
    
    def get_accessible_workflows(self):
        """접근 가능한 워크플로우 쿼리셋 반환"""
        from workflow.models import Workflow
        if self.can_view_all_organizations():
            return Workflow.objects.all()
        else:
            return Workflow.objects.filter(created_by__organization=self.organization)
    
    def get_accessible_candidates(self):
        """접근 가능한 후보자 쿼리셋 반환"""
        from candidates.models import Candidate
        if self.can_view_all_organizations():
            return Candidate.objects.all()
        else:
            return Candidate.objects.filter(organization=self.organization)
    
    def get_user_group_display(self):
        """사용자 그룹 표시명 반환"""
        if self.role == 'system_admin':
            return '시스템 관리자'
        elif self.organization.org_type == 'hospital':
            return '병원 관계자'
        elif self.organization.org_type == 'headhunting':
            return '채용회사 담당자'
        else:
            return '기타'


class UserActivity(models.Model):
    """사용자 활동 로그 모델"""
    
    ACTIVITY_TYPE_CHOICES = [
        ('login', '로그인'),
        ('logout', '로그아웃'),
        ('workflow_create', '워크플로우 생성'),
        ('workflow_update', '워크플로우 수정'),
        ('workflow_delete', '워크플로우 삭제'),
        ('step_start', '단계 시작'),
        ('step_complete', '단계 완료'),
        ('step_revert', '단계 되돌리기'),
        ('job_request_create', '채용 요청 생성'),
        ('job_request_update', '채용 요청 수정'),
        ('job_request_submit', '채용 요청 제출'),
        ('job_request_lock', '채용 요청 잠금'),
        ('job_request_unlock', '채용 요청 잠금 해제'),
        ('job_request_review', '채용 요청 확인'),
        ('workflow_create', '워크플로우 생성'),
        ('additional_request_add', '추가 요청사항 등록'),
        ('candidate_create', '후보자 생성'),
        ('candidate_update', '후보자 수정'),
        ('evaluation_create', '평가 생성'),
        ('evaluation_update', '평가 수정'),
        ('report_create', '보고서 생성'),
        ('report_update', '보고서 수정'),
        ('document_upload', '문서 업로드'),
        ('document_delete', '문서 삭제'),
        ('profile_update', '프로필 수정'),
        ('password_change', '비밀번호 변경'),
        ('system_access', '시스템 접근'),
        ('admin_action', '관리자 작업'),
        ('other', '기타')
    ]
    
    user = models.ForeignKey(
        User, 
        on_delete=models.CASCADE,
        related_name='activities',
        verbose_name='사용자'
    )
    activity_type = models.CharField(
        max_length=50, 
        choices=ACTIVITY_TYPE_CHOICES,
        verbose_name='활동 유형'
    )
    description = models.TextField(verbose_name='활동 설명')
    
    # 관련 객체 정보
    related_object_type = models.CharField(
        max_length=50, 
        blank=True, 
        verbose_name='관련 객체 유형'
    )
    related_object_id = models.IntegerField(
        blank=True, 
        null=True, 
        verbose_name='관련 객체 ID'
    )
    related_object_name = models.CharField(
        max_length=200, 
        blank=True, 
        verbose_name='관련 객체명'
    )
    
    # IP 주소 및 사용자 에이전트
    ip_address = models.GenericIPAddressField(
        blank=True, 
        null=True, 
        verbose_name='IP 주소'
    )
    user_agent = models.TextField(
        blank=True, 
        verbose_name='사용자 에이전트'
    )
    
    # 메타 정보
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='활동 시간')
    
    class Meta:
        verbose_name = '사용자 활동'
        verbose_name_plural = '사용자 활동들'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.user.get_full_name()} - {self.get_activity_type_display()} ({self.created_at.strftime('%Y-%m-%d %H:%M')})"
    
    @classmethod
    def log_activity(cls, user, activity_type, description, related_object_type=None, 
                    related_object_id=None, related_object_name=None, request=None):
        """활동 로그 생성"""
        ip_address = None
        user_agent = None
        
        if request:
            ip_address = cls.get_client_ip(request)
            user_agent = request.META.get('HTTP_USER_AGENT', '')
        
        return cls.objects.create(
            user=user,
            activity_type=activity_type,
            description=description,
            related_object_type=related_object_type,
            related_object_id=related_object_id,
            related_object_name=related_object_name,
            ip_address=ip_address,
            user_agent=user_agent
        )
    
    @staticmethod
    def get_client_ip(request):
        """클라이언트 IP 주소 가져오기"""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip
    
    def get_activity_icon(self):
        """활동 유형별 아이콘 반환"""
        icons = {
            'login': 'fas fa-sign-in-alt',
            'logout': 'fas fa-sign-out-alt',
            'workflow_create': 'fas fa-plus-circle',
            'workflow_update': 'fas fa-edit',
            'workflow_delete': 'fas fa-trash',
            'step_start': 'fas fa-play',
            'step_complete': 'fas fa-check',
            'step_revert': 'fas fa-undo',
            'job_request_create': 'fas fa-file-plus',
            'job_request_update': 'fas fa-file-edit',
            'job_request_submit': 'fas fa-paper-plane',
            'job_request_lock': 'fas fa-lock',
            'job_request_unlock': 'fas fa-unlock',
            'job_request_review': 'fas fa-check-circle',
            'workflow_create': 'fas fa-plus-circle',
            'additional_request_add': 'fas fa-plus',
            'candidate_create': 'fas fa-user-plus',
            'candidate_update': 'fas fa-user-edit',
            'evaluation_create': 'fas fa-star',
            'evaluation_update': 'fas fa-star-edit',
            'report_create': 'fas fa-chart-bar',
            'report_update': 'fas fa-chart-line',
            'document_upload': 'fas fa-upload',
            'document_delete': 'fas fa-file-times',
            'profile_update': 'fas fa-user-cog',
            'password_change': 'fas fa-key',
            'system_access': 'fas fa-desktop',
            'admin_action': 'fas fa-shield-alt',
            'other': 'fas fa-info-circle'
        }
        return icons.get(self.activity_type, 'fas fa-info-circle')
    
    def get_activity_color(self):
        """활동 유형별 색상 반환"""
        colors = {
            'login': 'success',
            'logout': 'secondary',
            'workflow_create': 'primary',
            'workflow_update': 'info',
            'workflow_delete': 'danger',
            'step_start': 'warning',
            'step_complete': 'success',
            'step_revert': 'warning',
            'job_request_create': 'primary',
            'job_request_update': 'info',
            'job_request_submit': 'success',
            'job_request_lock': 'warning',
            'job_request_unlock': 'info',
            'job_request_review': 'success',
            'workflow_create': 'primary',
            'additional_request_add': 'primary',
            'candidate_create': 'success',
            'candidate_update': 'info',
            'evaluation_create': 'warning',
            'evaluation_update': 'info',
            'report_create': 'primary',
            'report_update': 'info',
            'document_upload': 'success',
            'document_delete': 'danger',
            'profile_update': 'info',
            'password_change': 'warning',
            'system_access': 'secondary',
            'admin_action': 'danger',
            'other': 'secondary'
        }
        return colors.get(self.activity_type, 'secondary')


class Hospital(models.Model):
    """병원 정보 모델"""
    name = models.CharField(max_length=100, verbose_name='병원명')
    organization = models.ForeignKey(Organization, on_delete=models.CASCADE, verbose_name='소속 기관')
    address = models.TextField(verbose_name='병원 주소')
    phone = models.CharField(max_length=20, verbose_name='병원 연락처')
    website = models.URLField(blank=True, null=True, verbose_name='웹사이트')
    description = models.TextField(blank=True, verbose_name='병원 설명')
    is_active = models.BooleanField(default=True, verbose_name='활성화')
    
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='생성일')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='수정일')
    
    class Meta:
        verbose_name = '병원'
        verbose_name_plural = '병원들'
        ordering = ['name']
    
    def __str__(self):
        return self.name


class HospitalBranch(models.Model):
    """병원 지점 정보 모델"""
    hospital = models.ForeignKey(Hospital, on_delete=models.CASCADE, related_name='branches', verbose_name='병원')
    name = models.CharField(max_length=50, verbose_name='지점명')
    address = models.TextField(verbose_name='지점 주소')
    phone = models.CharField(max_length=20, verbose_name='지점 연락처')
    manager_name = models.CharField(max_length=50, verbose_name='담당자명')
    manager_phone = models.CharField(max_length=20, verbose_name='담당자 연락처')
    manager_email = models.EmailField(verbose_name='담당자 이메일')
    business_hours = models.CharField(max_length=100, blank=True, verbose_name='영업시간')
    description = models.TextField(blank=True, verbose_name='지점 설명')
    is_active = models.BooleanField(default=True, verbose_name='활성화')
    
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='생성일')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='수정일')
    
    class Meta:
        verbose_name = '병원 지점'
        verbose_name_plural = '병원 지점들'
        ordering = ['hospital', 'name']
        unique_together = ['hospital', 'name']
    
    def __str__(self):
        return f"{self.hospital.name} - {self.name}"
    
    def get_full_name(self):
        return f"{self.hospital.name} {self.name}"


class PositionTemplate(models.Model):
    """채용 포지션 템플릿 모델"""
    EMPLOYMENT_TYPE_CHOICES = [
        ('full_time', '정규직'),
        ('part_time', '비정규직'),
        ('contract', '계약직'),
        ('intern', '인턴'),
        ('temporary', '임시직')
    ]
    
    name = models.CharField(max_length=100, verbose_name='포지션명')
    department = models.CharField(max_length=50, verbose_name='부서')
    employment_type = models.CharField(max_length=20, choices=EMPLOYMENT_TYPE_CHOICES, verbose_name='고용 형태')
    
    # 급여 정보
    salary_min = models.IntegerField(blank=True, null=True, verbose_name='최소 급여 (만원)')
    salary_max = models.IntegerField(blank=True, null=True, verbose_name='최대 급여 (만원)')
    
    # 요구사항
    required_experience = models.TextField(verbose_name='필수 경력 요구사항')
    preferred_qualifications = models.TextField(blank=True, verbose_name='우대사항')
    job_description = models.TextField(verbose_name='업무 내용')
    working_hours = models.CharField(max_length=100, blank=True, verbose_name='근무 시간')
    working_location = models.CharField(max_length=200, blank=True, verbose_name='근무 장소')
    
    # 추가 정보
    special_requirements = models.TextField(blank=True, verbose_name='특별 요청사항')
    recruitment_period = models.CharField(max_length=50, blank=True, verbose_name='채용 기간')
    
    # 관리 정보
    is_default = models.BooleanField(default=False, verbose_name='기본 템플릿')
    is_active = models.BooleanField(default=True, verbose_name='활성화')
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name='생성자')
    
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='생성일')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='수정일')
    
    class Meta:
        verbose_name = '포지션 템플릿'
        verbose_name_plural = '포지션 템플릿들'
        ordering = ['department', 'name']
    
    def __str__(self):
        return f"{self.department} - {self.name}"
    
    def save(self, *args, **kwargs):
        # 기본 템플릿이 하나만 있도록 보장
        if self.is_default:
            PositionTemplate.objects.filter(is_default=True).update(is_default=False)
        super().save(*args, **kwargs)
