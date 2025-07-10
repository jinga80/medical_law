from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils import timezone
from accounts.models import User
from workflow.models import JobRequest


class Candidate(models.Model):
    """후보자 정보 모델"""
    
    STATUS_CHOICES = [
        ('waiting', '대기'),
        ('under_review', '검토중'),
        ('approved', '승인됨'),
        ('rejected', '거절됨'),
        ('evaluating', '평가 중'),
        ('interview_scheduled', '면접 예정'),
        ('interviewed', '면접 완료'),
        ('final_approved', '최종 승인'),
        ('final_rejected', '최종 거절'),
        ('hired', '채용됨'),
        ('withdrawn', '지원 철회')
    ]
    
    EDUCATION_LEVEL_CHOICES = [
        ('high_school', '고등학교'),
        ('college', '전문대학'),
        ('university', '대학교'),
        ('graduate', '대학원'),
        ('phd', '박사')
    ]
    
    POSITION_CHOICES = [
        ('total_manager', '총괄실장'),
        ('counseling_manager', '상담실장'),
        ('skin_manager', '피부매니저'),
        ('skin_staff', '피부팀원'),
        ('nurse_manager', '간호팀장'),
        ('nurse_staff', '간호조무사'),
        ('coordinator', '코디네이터'),
    ]
    
    BRANCH_CHOICES = [
        ('hongdae', '홍대점'),
        ('gangnam', '강남점'),
        ('bundang', '분당점'),
        ('other', '기타'),
    ]
    
    # 기본 연결 정보
    job_request = models.ForeignKey(
        JobRequest, 
        on_delete=models.CASCADE,
        related_name='candidates',
        verbose_name='채용 요청'
    )
    recommended_by = models.ForeignKey(
        User, 
        on_delete=models.CASCADE,
        verbose_name='추천자',
        related_name='recommended_candidates'
    )
    
    # 채용 정보
    position = models.CharField(
        max_length=30,
        choices=POSITION_CHOICES,
        default='skin_staff',
        verbose_name='지원 직무'
    )
    branch = models.CharField(
        max_length=20,
        choices=BRANCH_CHOICES,
        default='hongdae',
        verbose_name='지점'
    )
    
    # 개인 정보
    name = models.CharField(max_length=50, verbose_name='성명')
    email = models.EmailField(blank=True, verbose_name='이메일')
    phone = models.CharField(max_length=20, verbose_name='연락처')
    birth_date = models.DateField(blank=True, null=True, verbose_name='생년월일')
    address = models.TextField(blank=True, verbose_name='주소')
    gender = models.CharField(
        max_length=10, 
        choices=[('male', '남성'), ('female', '여성')],
        blank=True,
        verbose_name='성별'
    )
    
    # 경력 정보
    education_level = models.CharField(
        max_length=30, 
        choices=EDUCATION_LEVEL_CHOICES,
        verbose_name='최종학력'
    )
    major = models.CharField(max_length=50, blank=True, verbose_name='전공')
    university = models.CharField(max_length=100, blank=True, verbose_name='졸업학교')
    graduation_year = models.IntegerField(blank=True, null=True, verbose_name='졸업년도')
    total_experience_years = models.IntegerField(
        default=0, 
        verbose_name='총 경력(년)',
        help_text='관련 분야 총 경력'
    )
    relevant_experience = models.TextField(verbose_name='관련 경력')
    current_company = models.CharField(max_length=100, blank=True, verbose_name='현재 회사')
    current_position = models.CharField(max_length=50, blank=True, verbose_name='현재 직책')
    
    # 자격 및 스킬
    licenses = models.TextField(blank=True, verbose_name='보유 자격증')
    skills = models.TextField(blank=True, verbose_name='보유 스킬')
    languages = models.TextField(blank=True, verbose_name='언어 능력')
    
    # 파일 첨부
    resume_file = models.FileField(
        upload_to='resumes/',
        verbose_name='이력서 파일'
    )
    portfolio_file = models.FileField(
        upload_to='portfolios/',
        blank=True,
        verbose_name='포트폴리오 파일'
    )
    cover_letter = models.FileField(
        upload_to='cover_letters/',
        blank=True,
        verbose_name='자기소개서'
    )
    
    # 추천 정보
    recommendation_reason = models.TextField(verbose_name='추천 사유')
    expected_salary = models.IntegerField(
        blank=True, 
        null=True, 
        verbose_name='희망 급여',
        help_text='연봉 기준 (만원)'
    )
    available_start_date = models.DateField(
        blank=True, 
        null=True, 
        verbose_name='입사 가능일'
    )
    
    # 진행 상태
    status = models.CharField(
        max_length=20, 
        choices=STATUS_CHOICES,
        default='waiting',
        verbose_name='진행 상태'
    )
    
    # 메모 및 평가
    internal_notes = models.TextField(blank=True, verbose_name='내부 메모')
    candidate_notes = models.TextField(blank=True, verbose_name='후보자 메모')
    
    # 시간 기록
    recommended_at = models.DateTimeField(auto_now_add=True, verbose_name='추천일')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='수정일')
    
    # 검토 관련 필드 추가
    review_status = models.CharField(
        max_length=20,
        choices=[
            ('pending', '검토 대기'),
            ('in_progress', '검토중'),
            ('passed', '검토 통과'),
            ('failed', '검토 실패'),
            ('needs_more_info', '추가정보 필요')
        ],
        default='pending',
        verbose_name='검토 상태'
    )
    
    review_score = models.IntegerField(
        blank=True,
        null=True,
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        verbose_name='검토 점수',
        help_text='100점 만점'
    )
    
    review_comments = models.TextField(blank=True, verbose_name='검토 의견')
    review_date = models.DateTimeField(blank=True, null=True, verbose_name='검토일')
    reviewed_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name='reviewed_candidates',
        verbose_name='검토자'
    )
    
    # 면접 관련 필드
    interview_decision = models.CharField(
        max_length=20,
        choices=[
            ('pending', '대기'),
            ('pass', '합격'),
            ('fail', '불합격'),
            ('hold', '보류')
        ],
        default='pending',
        verbose_name='면접 결정'
    )
    
    interview_comments = models.TextField(blank=True, verbose_name='면접 의견')
    interview_score = models.IntegerField(
        blank=True,
        null=True,
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        verbose_name='면접 점수'
    )
    
    class Meta:
        verbose_name = '후보자'
        verbose_name_plural = '후보자들'
        ordering = ['-recommended_at']
    
    def __str__(self):
        return f"{self.name} - {self.get_position_display()} ({self.get_branch_display()}) - {self.get_status_display()}"
    
    def get_age(self):
        """나이 계산"""
        if self.birth_date:
            today = timezone.now().date()
            return today.year - self.birth_date.year - (
                (today.month, today.day) < (self.birth_date.month, self.birth_date.day)
            )
        return None
    
    def get_experience_level(self):
        """경력 수준 분류"""
        if self.total_experience_years < 1:
            return '신입'
        elif self.total_experience_years < 3:
            return '주니어'
        elif self.total_experience_years < 7:
            return '미들'
        else:
            return '시니어'
    
    def is_qualified_for_salary(self):
        """급여 조건 적합성 확인"""
        if not self.expected_salary or not self.job_request.salary_max:
            return True
        
        return self.expected_salary <= self.job_request.salary_max
    
    def can_proceed_to_interview(self):
        """면접 진행 가능 여부"""
        return self.status in ['document_passed', 'interview_scheduled']
    
    def can_be_hired(self):
        """채용 가능 여부"""
        return self.status == 'final_passed'
    
    def get_days_since_recommendation(self):
        """추천일로부터 경과 일수"""
        return (timezone.now() - self.recommended_at).days
    
    def get_latest_review(self):
        """최신 검토 정보 반환"""
        return self.reviews.order_by('-reviewed_at').first()
    
    def get_average_review_score(self):
        """평균 검토 점수 반환"""
        reviews = self.reviews.all()
        if not reviews:
            return None
        total_score = sum(review.total_score for review in reviews)
        return total_score / len(reviews)
    
    def get_review_count(self):
        """검토 횟수 반환"""
        return self.reviews.count()
    
    def can_start_review(self):
        """검토 시작 가능 여부"""
        return self.status in ['waiting', 'under_review']
    
    def can_proceed_to_interview(self):
        """면접 진행 가능 여부"""
        latest_review = self.get_latest_review()
        return (latest_review and latest_review.passed and 
                self.status in ['approved', 'evaluating'])
    
    def update_review_status(self, status, score=None, comments=None, reviewer=None):
        """검토 상태 업데이트"""
        self.review_status = status
        if score is not None:
            self.review_score = score
        if comments:
            self.review_comments = comments
        if reviewer:
            self.reviewed_by = reviewer
        self.review_date = timezone.now()
        
        # 상태에 따른 후보자 상태 업데이트
        if status == 'passed':
            self.status = 'approved'
        elif status == 'failed':
            self.status = 'rejected'
        elif status == 'in_progress':
            self.status = 'under_review'
        
        self.save()
    
    @classmethod
    def check_duplicate_candidate(cls, email=None, phone=None, name=None):
        """중복 지원자 확인"""
        filters = {}
        if email:
            filters['email'] = email
        if phone:
            filters['phone'] = phone
        if name:
            filters['name'] = name
        
        if filters:
            return cls.objects.filter(**filters).exists()
        return False
    
    @classmethod
    def find_duplicate_candidates(cls, email=None, phone=None, name=None):
        """중복 지원자 찾기"""
        filters = {}
        if email:
            filters['email'] = email
        if phone:
            filters['phone'] = phone
        if name:
            filters['name'] = name
        
        if filters:
            return cls.objects.filter(**filters)
        return cls.objects.none()
    
    def get_duplicate_candidates(self):
        """현재 후보자와 중복되는 다른 후보자들 찾기"""
        duplicates = []
        
        # 이메일로 중복 검색
        if self.email:
            email_duplicates = Candidate.objects.filter(
                email=self.email
            ).exclude(id=self.id)
            duplicates.extend(email_duplicates)
        
        # 전화번호로 중복 검색
        if self.phone:
            phone_duplicates = Candidate.objects.filter(
                phone=self.phone
            ).exclude(id=self.id)
            duplicates.extend(phone_duplicates)
        
        # 이름으로 중복 검색 (동명이인)
        if self.name:
            name_duplicates = Candidate.objects.filter(
                name=self.name
            ).exclude(id=self.id)
            duplicates.extend(name_duplicates)
        
        # 중복 제거
        return list(set(duplicates))
    
    def merge_with_candidate(self, other_candidate):
        """다른 후보자와 정보 통합"""
        # 더 완전한 정보를 가진 후보자로 통합
        if not self.email and other_candidate.email:
            self.email = other_candidate.email
        
        if not self.phone and other_candidate.phone:
            self.phone = other_candidate.phone
        
        if not self.birth_date and other_candidate.birth_date:
            self.birth_date = other_candidate.birth_date
        
        if not self.address and other_candidate.address:
            self.address = other_candidate.address
        
        if not self.resume_file and other_candidate.resume_file:
            self.resume_file = other_candidate.resume_file
        
        if not self.portfolio_file and other_candidate.portfolio_file:
            self.portfolio_file = other_candidate.portfolio_file
        
        if not self.cover_letter and other_candidate.cover_letter:
            self.cover_letter = other_candidate.cover_letter
        
        # 메모 통합
        if other_candidate.internal_notes:
            if self.internal_notes:
                self.internal_notes += f"\n\n[통합된 정보]\n{other_candidate.internal_notes}"
            else:
                self.internal_notes = other_candidate.internal_notes
        
        self.save()
        
        # 다른 후보자 삭제
        other_candidate.delete()
    
    def is_duplicate_of(self, other_candidate):
        """다른 후보자와 중복 여부 확인"""
        # 이메일 중복
        if self.email and other_candidate.email and self.email == other_candidate.email:
            return True
        
        # 전화번호 중복
        if self.phone and other_candidate.phone and self.phone == other_candidate.phone:
            return True
        
        # 이름 중복 (동명이인)
        if self.name and other_candidate.name and self.name == other_candidate.name:
            return True
        
        return False


class CandidateHistory(models.Model):
    """후보자 상태 변경 이력"""
    
    ACTION_CHOICES = [
        ('status_change', '상태 변경'),
        ('note_added', '메모 추가'),
        ('file_uploaded', '파일 업로드'),
        ('interview_scheduled', '면접 일정'),
        ('evaluation_added', '평가 추가'),
        ('decision_made', '결정 사항')
    ]
    
    candidate = models.ForeignKey(
        Candidate, 
        on_delete=models.CASCADE,
        related_name='history',
        verbose_name='후보자'
    )
    action = models.CharField(
        max_length=20,
        choices=ACTION_CHOICES,
        verbose_name='액션'
    )
    action_by = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        verbose_name='실행자'
    )
    old_value = models.CharField(max_length=100, blank=True, verbose_name='이전 값')
    new_value = models.CharField(max_length=100, blank=True, verbose_name='새 값')
    description = models.TextField(verbose_name='설명')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='생성일')
    
    class Meta:
        verbose_name = '후보자 이력'
        verbose_name_plural = '후보자 이력들'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.candidate.name} - {self.get_action_display()} ({self.created_at.strftime('%Y-%m-%d %H:%M')})"


class CandidateNote(models.Model):
    """후보자별 메모"""
    
    NOTE_TYPE_CHOICES = [
        ('internal', '내부 메모'),
        ('candidate', '후보자 메모'),
        ('evaluation', '평가 메모'),
        ('interview', '면접 메모'),
        ('general', '일반 메모')
    ]
    
    candidate = models.ForeignKey(
        Candidate,
        on_delete=models.CASCADE,
        related_name='notes',
        verbose_name='후보자'
    )
    note_type = models.CharField(
        max_length=20,
        choices=NOTE_TYPE_CHOICES,
        verbose_name='메모 유형'
    )
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        verbose_name='작성자'
    )
    title = models.CharField(max_length=200, verbose_name='제목')
    content = models.TextField(verbose_name='내용')
    is_private = models.BooleanField(default=False, verbose_name='비공개')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='작성일')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='수정일')
    
    class Meta:
        verbose_name = '후보자 메모'
        verbose_name_plural = '후보자 메모들'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.candidate.name} - {self.title}"


class CandidateReview(models.Model):
    """후보자 검토 모델"""
    
    REVIEW_TYPE_CHOICES = [
        ('initial', '초기 검토'),
        ('document', '서류 검토'),
        ('technical', '기술 검토'),
        ('final', '최종 검토')
    ]
    
    candidate = models.ForeignKey(
        Candidate,
        on_delete=models.CASCADE,
        related_name='reviews',
        verbose_name='후보자'
    )
    reviewer = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        verbose_name='검토자'
    )
    review_type = models.CharField(
        max_length=20,
        choices=REVIEW_TYPE_CHOICES,
        verbose_name='검토 유형'
    )
    
    # 검토 항목별 점수
    experience_score = models.IntegerField(
        default=0,
        validators=[MinValueValidator(0), MaxValueValidator(25)],
        verbose_name='경력 점수',
        help_text='25점 만점'
    )
    education_score = models.IntegerField(
        default=0,
        validators=[MinValueValidator(0), MaxValueValidator(20)],
        verbose_name='학력 점수',
        help_text='20점 만점'
    )
    skill_score = models.IntegerField(
        default=0,
        validators=[MinValueValidator(0), MaxValueValidator(25)],
        verbose_name='스킬 점수',
        help_text='25점 만점'
    )
    personality_score = models.IntegerField(
        default=0,
        validators=[MinValueValidator(0), MaxValueValidator(15)],
        verbose_name='인성 점수',
        help_text='15점 만점'
    )
    motivation_score = models.IntegerField(
        default=0,
        validators=[MinValueValidator(0), MaxValueValidator(15)],
        verbose_name='동기 점수',
        help_text='15점 만점'
    )
    
    # 총점 및 결과
    total_score = models.IntegerField(default=0, verbose_name='총점')
    passed = models.BooleanField(default=False, verbose_name='합격 여부')
    
    # 검토 의견
    strengths = models.TextField(blank=True, verbose_name='강점')
    weaknesses = models.TextField(blank=True, verbose_name='약점')
    improvement_areas = models.TextField(blank=True, verbose_name='개선 영역')
    overall_comments = models.TextField(blank=True, verbose_name='종합 의견')
    
    # 검토 시간
    reviewed_at = models.DateTimeField(auto_now_add=True, verbose_name='검토일')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='수정일')
    
    class Meta:
        verbose_name = '후보자 검토'
        verbose_name_plural = '후보자 검토들'
        ordering = ['-reviewed_at']
    
    def __str__(self):
        return f"{self.candidate.name} - {self.get_review_type_display()} 검토 ({self.total_score}점)"
    
    def save(self, *args, **kwargs):
        """저장 시 총점 자동 계산"""
        self.total_score = (
            self.experience_score + 
            self.education_score + 
            self.skill_score + 
            self.personality_score + 
            self.motivation_score
        )
        # 70점 이상이면 합격
        self.passed = self.total_score >= 70
        super().save(*args, **kwargs)
    
    def get_score_percentage(self):
        """점수 백분율 계산"""
        max_score = 100
        return (self.total_score / max_score) * 100 if max_score > 0 else 0
    
    def get_score_level(self):
        """점수 등급 반환"""
        if self.total_score >= 90:
            return 'A+'
        elif self.total_score >= 80:
            return 'A'
        elif self.total_score >= 70:
            return 'B+'
        elif self.total_score >= 60:
            return 'B'
        elif self.total_score >= 50:
            return 'C'
        else:
            return 'D'
