from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils import timezone
from accounts.models import User
from candidates.models import Candidate
from workflow.models import JobRequest


class DocumentReview(models.Model):
    """서류 검토 모델"""
    
    candidate = models.OneToOneField(
        Candidate, 
        on_delete=models.CASCADE,
        related_name='document_review',
        verbose_name='후보자'
    )
    reviewer = models.ForeignKey(
        User, 
        on_delete=models.CASCADE,
        verbose_name='검토자'
    )
    
    # 검토 항목 (기존 면접대장 기반)
    work_experience_score = models.IntegerField(
        default=0, 
        validators=[MinValueValidator(0), MaxValueValidator(20)],
        verbose_name='경력 점수',
        help_text='치원부야 (경력) - 20점 만점'
    )
    education_score = models.IntegerField(
        default=0, 
        validators=[MinValueValidator(0), MaxValueValidator(15)],
        verbose_name='학력 점수',
        help_text='학력 - 15점 만점'
    )
    skill_score = models.IntegerField(
        default=0, 
        validators=[MinValueValidator(0), MaxValueValidator(10)],
        verbose_name='스킬 점수',
        help_text='스킬 - 10점 만점'
    )
    
    # 총점 및 결과
    total_score = models.IntegerField(default=0, verbose_name='총점')
    passed = models.BooleanField(default=False, verbose_name='합격 여부')
    review_comments = models.TextField(blank=True, verbose_name='검토 의견')
    
    # 검토 시간
    reviewed_at = models.DateTimeField(auto_now_add=True, verbose_name='검토일')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='수정일')
    
    class Meta:
        verbose_name = '서류 검토'
        verbose_name_plural = '서류 검토들'
        ordering = ['-reviewed_at']
    
    def __str__(self):
        return f"{self.candidate.name} 서류검토 - {self.total_score}점 ({'합격' if self.passed else '불합격'})"
    
    def save(self, *args, **kwargs):
        """저장 시 총점 자동 계산"""
        self.total_score = self.work_experience_score + self.education_score + self.skill_score
        super().save(*args, **kwargs)
    
    def get_score_percentage(self):
        """점수 백분율 계산"""
        max_score = 45  # 20 + 15 + 10
        return (self.total_score / max_score) * 100 if max_score > 0 else 0


class Interview(models.Model):
    """면접 정보 모델"""
    
    INTERVIEW_TYPE_CHOICES = [
        ('in_person', '대면'),
        ('video', '화상'),
        ('phone', '전화'),
        ('hybrid', '혼합')
    ]
    
    STATUS_CHOICES = [
        ('scheduled', '예정'),
        ('in_progress', '진행중'),
        ('completed', '완료'),
        ('cancelled', '취소'),
        ('no_show', '미참석'),
        ('rescheduled', '재일정')
    ]
    
    candidate = models.ForeignKey(
        Candidate, 
        on_delete=models.CASCADE,
        related_name='interviews',
        verbose_name='후보자'
    )
    job_request = models.ForeignKey(
        JobRequest, 
        on_delete=models.CASCADE,
        related_name='interviews',
        verbose_name='채용 요청'
    )
    
    # 면접 일정
    scheduled_date = models.DateTimeField(verbose_name='면접 일시')
    duration_minutes = models.IntegerField(
        default=30, 
        verbose_name='면접 시간',
        help_text='분 단위'
    )
    interview_type = models.CharField(
        max_length=20, 
        choices=INTERVIEW_TYPE_CHOICES,
        verbose_name='면접 유형'
    )
    location = models.CharField(max_length=200, blank=True, verbose_name='면접 장소')
    
    # 면접관
    primary_interviewer = models.ForeignKey(
        User, 
        on_delete=models.CASCADE, 
        related_name='primary_interviews',
        verbose_name='주 면접관'
    )
    secondary_interviewers = models.ManyToManyField(
        User, 
        related_name='secondary_interviews', 
        blank=True,
        verbose_name='부 면접관'
    )
    
    # 상태 및 결과
    status = models.CharField(
        max_length=20, 
        choices=STATUS_CHOICES,
        default='scheduled',
        verbose_name='상태'
    )
    actual_start_time = models.DateTimeField(blank=True, null=True, verbose_name='실제 시작 시간')
    actual_end_time = models.DateTimeField(blank=True, null=True, verbose_name='실제 종료 시간')
    
    # 메모
    pre_interview_notes = models.TextField(blank=True, verbose_name='면접 전 메모')
    post_interview_notes = models.TextField(blank=True, verbose_name='면접 후 메모')
    
    # 메타 정보
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='생성일')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='수정일')
    
    class Meta:
        verbose_name = '면접'
        verbose_name_plural = '면접들'
        ordering = ['-scheduled_date']
    
    def __str__(self):
        return f"{self.candidate.name} 면접 - {self.scheduled_date.strftime('%Y-%m-%d %H:%M')}"
    
    def get_actual_duration(self):
        """실제 면접 시간 계산"""
        if self.actual_start_time and self.actual_end_time:
            duration = self.actual_end_time - self.actual_start_time
            return duration.total_seconds() / 60  # 분 단위
        return None
    
    def is_today(self):
        """오늘 면접인지 확인"""
        return self.scheduled_date.date() == timezone.now().date()
    
    def is_upcoming(self):
        """예정된 면접인지 확인"""
        return self.scheduled_date > timezone.now()
    
    def can_start(self):
        """면접 시작 가능 여부"""
        return self.status == 'scheduled' and self.scheduled_date <= timezone.now()
    
    def can_complete(self):
        """면접 완료 가능 여부"""
        return self.status in ['scheduled', 'in_progress']


class InterviewScheduling(models.Model):
    """면접 일정 조율 모델"""
    
    SCHEDULING_STATUS_CHOICES = [
        ('pending', '대기중'),
        ('candidate_contacted', '후보자 연락완료'),
        ('date_proposed', '일정 제안됨'),
        ('date_confirmed', '일정 확정됨'),
        ('date_rejected', '일정 거절됨'),
        ('rescheduled', '재일정'),
        ('cancelled', '취소됨')
    ]
    
    candidate = models.OneToOneField(
        Candidate, 
        on_delete=models.CASCADE,
        related_name='interview_scheduling',
        verbose_name='후보자'
    )
    coordinator = models.ForeignKey(
        User, 
        on_delete=models.CASCADE,
        verbose_name='일정 조율자'
    )
    
    # 일정 정보
    preferred_dates = models.JSONField(
        default=list,
        verbose_name='선호 일정',
        help_text='후보자가 선호하는 면접 일정 목록'
    )
    interviewer_availability = models.JSONField(
        default=list,
        verbose_name='면접관 가능 일정',
        help_text='면접관들의 가능한 일정 목록'
    )
    
    # 제안된 일정
    proposed_date = models.DateTimeField(
        blank=True, 
        null=True, 
        verbose_name='제안된 일정'
    )
    confirmed_date = models.DateTimeField(
        blank=True, 
        null=True, 
        verbose_name='확정된 일정'
    )
    
    # 상태 관리
    scheduling_status = models.CharField(
        max_length=20,
        choices=SCHEDULING_STATUS_CHOICES,
        default='pending',
        verbose_name='조율 상태'
    )
    
    # 연락 정보
    contact_method = models.CharField(
        max_length=20,
        choices=[
            ('phone', '전화'),
            ('email', '이메일'),
            ('sms', '문자'),
            ('kakao', '카카오톡')
        ],
        verbose_name='연락 방법'
    )
    contact_attempts = models.IntegerField(
        default=0,
        verbose_name='연락 시도 횟수'
    )
    last_contact_date = models.DateTimeField(
        blank=True, 
        null=True, 
        verbose_name='마지막 연락일'
    )
    
    # 메모 및 의견
    candidate_response = models.TextField(
        blank=True, 
        verbose_name='후보자 응답'
    )
    scheduling_notes = models.TextField(
        blank=True, 
        verbose_name='일정 조율 메모'
    )
    
    # 시간 기록
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='생성일')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='수정일')
    
    class Meta:
        verbose_name = '면접 일정 조율'
        verbose_name_plural = '면접 일정 조율들'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.candidate.name} 면접일정조율 - {self.get_scheduling_status_display()}"
    
    def add_preferred_date(self, date_time):
        """선호 일정 추가"""
        if date_time not in self.preferred_dates:
            self.preferred_dates.append(date_time.isoformat())
            self.save()
    
    def add_interviewer_availability(self, interviewer_id, available_dates):
        """면접관 가능 일정 추가"""
        availability = {
            'interviewer_id': interviewer_id,
            'available_dates': [date.isoformat() for date in available_dates]
        }
        self.interviewer_availability.append(availability)
        self.save()
    
    def find_common_slot(self):
        """공통 가능 시간 찾기"""
        if not self.preferred_dates or not self.interviewer_availability:
            return None
        
        # 후보자 선호 일정
        candidate_dates = set(self.preferred_dates)
        
        # 면접관 가능 일정
        interviewer_dates = set()
        for availability in self.interviewer_availability:
            interviewer_dates.update(availability['available_dates'])
        
        # 공통 시간 찾기
        common_slots = candidate_dates.intersection(interviewer_dates)
        
        if common_slots:
            # 가장 가까운 시간 선택
            from datetime import datetime
            now = timezone.now()
            closest_slot = min(common_slots, key=lambda x: abs(
                datetime.fromisoformat(x) - now
            ))
            return datetime.fromisoformat(closest_slot)
        
        return None
    
    def propose_date(self, proposed_date):
        """일정 제안"""
        self.proposed_date = proposed_date
        self.scheduling_status = 'date_proposed'
        self.save()
    
    def confirm_date(self, confirmed_date):
        """일정 확정"""
        self.confirmed_date = confirmed_date
        self.scheduling_status = 'date_confirmed'
        self.save()
        
        # Interview 모델 생성
        Interview.objects.create(
            candidate=self.candidate,
            job_request=self.candidate.job_request,
            scheduled_date=confirmed_date,
            interview_type='in_person',
            primary_interviewer=self.coordinator
        )
    
    def reject_date(self, reason=""):
        """일정 거절"""
        self.scheduling_status = 'date_rejected'
        self.candidate_response = reason
        self.save()
    
    def reschedule(self, new_date):
        """재일정"""
        self.proposed_date = new_date
        self.scheduling_status = 'rescheduled'
        self.save()
    
    def increment_contact_attempts(self):
        """연락 시도 횟수 증가"""
        self.contact_attempts += 1
        self.last_contact_date = timezone.now()
        self.save()
    
    def is_urgent(self):
        """긴급 여부 (3일 이상 지연)"""
        if self.created_at:
            days_since_creation = (timezone.now() - self.created_at).days
            return days_since_creation >= 3
        return False


class InterviewEvaluation(models.Model):
    """면접 평가 모델 (기존 면접대장 디지털화)"""
    
    RATING_CHOICES = [
        ('excellent', '매우 양호'),
        ('good', '양호'),
        ('average', '보통'),
        ('poor', '불량'),
        ('very_poor', '매우 불량')
    ]
    
    interview = models.OneToOneField(
        Interview, 
        on_delete=models.CASCADE,
        related_name='evaluation',
        verbose_name='면접'
    )
    evaluator = models.ForeignKey(
        User, 
        on_delete=models.CASCADE,
        verbose_name='평가자'
    )
    
    # 기존 면접대장 평가 항목
    work_experience_score = models.IntegerField(
        default=0, 
        validators=[MinValueValidator(0), MaxValueValidator(20)],
        verbose_name='경력 점수',
        help_text='치원부야 (경력) - 20점 만점'
    )
    intellectual_ability_score = models.IntegerField(
        default=0, 
        validators=[MinValueValidator(0), MaxValueValidator(20)],
        verbose_name='지적 능력 점수',
        help_text='지적증 여부 (지적 능력) - 20점 만점'
    )
    transportation_score = models.IntegerField(
        default=0, 
        validators=[MinValueValidator(0), MaxValueValidator(15)],
        verbose_name='교통수단 점수',
        help_text='자동차 여부 (교통수단) - 15점 만점'
    )
    communication_score = models.IntegerField(
        default=0, 
        validators=[MinValueValidator(0), MaxValueValidator(10)],
        verbose_name='의사소통 점수',
        help_text='의사소통 능력 - 10점 만점'
    )
    personality_score = models.IntegerField(
        default=0, 
        validators=[MinValueValidator(0), MaxValueValidator(10)],
        verbose_name='인성 점수',
        help_text='인성 평가 - 10점 만점'
    )
    overall_impression_score = models.IntegerField(
        default=0, 
        validators=[MinValueValidator(0), MaxValueValidator(10)],
        verbose_name='종합 인상 점수',
        help_text='종합 인상 - 10점 만점'
    )
    
    # 총점 (85점 만점)
    total_score = models.IntegerField(default=0, verbose_name='총점')
    
    # 종합 평가
    overall_rating = models.CharField(
        max_length=20, 
        choices=RATING_CHOICES,
        verbose_name='종합 평가'
    )
    
    # 추가 의견
    strengths = models.TextField(blank=True, verbose_name='장점')
    weaknesses = models.TextField(blank=True, verbose_name='단점')
    recommendations = models.TextField(blank=True, verbose_name='종합 의견')
    hire_recommendation = models.BooleanField(default=False, verbose_name='채용 추천')
    
    # 평가 시간
    evaluated_at = models.DateTimeField(auto_now_add=True, verbose_name='평가일')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='수정일')
    
    class Meta:
        verbose_name = '면접 평가'
        verbose_name_plural = '면접 평가들'
        ordering = ['-evaluated_at']
    
    def __str__(self):
        return f"{self.interview.candidate.name} 면접평가 - {self.total_score}점 ({self.get_overall_rating_display()})"
    
    def save(self, *args, **kwargs):
        """저장 시 총점 자동 계산"""
        self.total_score = (
            self.work_experience_score +
            self.intellectual_ability_score +
            self.transportation_score +
            self.communication_score +
            self.personality_score +
            self.overall_impression_score
        )
        super().save(*args, **kwargs)
    
    def get_score_percentage(self):
        """점수 백분율 계산"""
        max_score = 85
        return (self.total_score / max_score) * 100 if max_score > 0 else 0
    
    def get_score_level(self):
        """점수 수준 분류"""
        percentage = self.get_score_percentage()
        if percentage >= 90:
            return '매우 우수'
        elif percentage >= 80:
            return '우수'
        elif percentage >= 70:
            return '양호'
        elif percentage >= 60:
            return '보통'
        else:
            return '미흡'


class EvaluationTemplate(models.Model):
    """평가 템플릿"""
    
    name = models.CharField(max_length=100, verbose_name='템플릿명')
    description = models.TextField(blank=True, verbose_name='설명')
    is_default = models.BooleanField(default=False, verbose_name='기본 템플릿')
    is_active = models.BooleanField(default=True, verbose_name='활성화')
    
    # 평가 항목 설정
    criteria_config = models.JSONField(default=dict, verbose_name='평가 기준 설정')
    
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='생성일')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='수정일')
    
    class Meta:
        verbose_name = '평가 템플릿'
        verbose_name_plural = '평가 템플릿들'
        ordering = ['name']
    
    def __str__(self):
        return self.name


class DocumentScreening(models.Model):
    """서류 심사 모델"""
    
    SCREENING_STATUS_CHOICES = [
        ('pending', '대기중'),
        ('in_progress', '검토중'),
        ('passed', '합격'),
        ('failed', '불합격'),
        ('needs_more_info', '추가정보 필요')
    ]
    
    candidate = models.OneToOneField(
        Candidate, 
        on_delete=models.CASCADE,
        related_name='document_screening',
        verbose_name='후보자'
    )
    screener = models.ForeignKey(
        User, 
        on_delete=models.CASCADE,
        verbose_name='심사자'
    )
    
    # 심사 결과
    screening_status = models.CharField(
        max_length=20,
        choices=SCREENING_STATUS_CHOICES,
        default='pending',
        verbose_name='심사 상태'
    )
    
    # 심사 항목별 점수
    resume_quality_score = models.IntegerField(
        default=0,
        validators=[MinValueValidator(0), MaxValueValidator(20)],
        verbose_name='이력서 품질 점수',
        help_text='이력서 완성도 및 내용 - 20점 만점'
    )
    experience_match_score = models.IntegerField(
        default=0,
        validators=[MinValueValidator(0), MaxValueValidator(25)],
        verbose_name='경력 적합성 점수',
        help_text='지원 직무와의 경력 일치도 - 25점 만점'
    )
    education_score = models.IntegerField(
        default=0,
        validators=[MinValueValidator(0), MaxValueValidator(15)],
        verbose_name='학력 점수',
        help_text='학력 및 전공 적합성 - 15점 만점'
    )
    skill_match_score = models.IntegerField(
        default=0,
        validators=[MinValueValidator(0), MaxValueValidator(20)],
        verbose_name='스킬 적합성 점수',
        help_text='필요 스킬 보유 여부 - 20점 만점'
    )
    overall_impression_score = models.IntegerField(
        default=0,
        validators=[MinValueValidator(0), MaxValueValidator(20)],
        verbose_name='종합 인상 점수',
        help_text='전체적인 인상 및 잠재력 - 20점 만점'
    )
    
    # 총점 및 결과
    total_score = models.IntegerField(default=0, verbose_name='총점')
    passing_score = models.IntegerField(default=70, verbose_name='합격 점수')
    passed = models.BooleanField(default=False, verbose_name='합격 여부')
    
    # 심사 의견
    strengths = models.TextField(blank=True, verbose_name='장점')
    weaknesses = models.TextField(blank=True, verbose_name='단점')
    improvement_suggestions = models.TextField(blank=True, verbose_name='개선 제안')
    screening_notes = models.TextField(blank=True, verbose_name='심사 메모')
    
    # 추가 정보 요청
    additional_info_requested = models.TextField(blank=True, verbose_name='추가 정보 요청사항')
    info_deadline = models.DateField(blank=True, null=True, verbose_name='정보 제출 마감일')
    
    # 시간 기록
    screening_started_at = models.DateTimeField(blank=True, null=True, verbose_name='심사 시작일')
    screening_completed_at = models.DateTimeField(blank=True, null=True, verbose_name='심사 완료일')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='생성일')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='수정일')
    
    class Meta:
        verbose_name = '서류 심사'
        verbose_name_plural = '서류 심사들'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.candidate.name} 서류심사 - {self.get_screening_status_display()} ({self.total_score}점)"
    
    def save(self, *args, **kwargs):
        """저장 시 총점 자동 계산 및 합격 여부 결정"""
        self.total_score = (
            self.resume_quality_score +
            self.experience_match_score +
            self.education_score +
            self.skill_match_score +
            self.overall_impression_score
        )
        
        self.passed = self.total_score >= self.passing_score
        
        # 심사 완료 시 상태 업데이트
        if self.screening_status == 'in_progress' and self.total_score > 0:
            if self.passed:
                self.screening_status = 'passed'
            else:
                self.screening_status = 'failed'
        
        super().save(*args, **kwargs)
    
    def get_score_percentage(self):
        """점수 백분율 계산"""
        max_score = 100
        return (self.total_score / max_score) * 100 if max_score > 0 else 0
    
    def get_score_level(self):
        """점수 수준 분류"""
        percentage = self.get_score_percentage()
        if percentage >= 90:
            return '매우 우수'
        elif percentage >= 80:
            return '우수'
        elif percentage >= 70:
            return '양호'
        elif percentage >= 60:
            return '보통'
        else:
            return '미흡'
    
    def can_proceed_to_interview(self):
        """면접 진행 가능 여부"""
        return self.passed and self.screening_status == 'passed'
    
    def start_screening(self):
        """심사 시작"""
        if self.screening_status == 'pending':
            self.screening_status = 'in_progress'
            self.screening_started_at = timezone.now()
            self.save()
    
    def complete_screening(self):
        """심사 완료"""
        if self.screening_status == 'in_progress':
            self.screening_completed_at = timezone.now()
            self.save()
