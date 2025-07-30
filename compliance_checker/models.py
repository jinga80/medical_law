from django.db import models
from django.utils import timezone

class ComplianceRule(models.Model):
    """의료광고법 준수 규칙 모델"""
    
    category = models.CharField(max_length=100, verbose_name="위반 카테고리")
    title = models.CharField(max_length=200, verbose_name="규칙 제목")
    description = models.TextField(verbose_name="규칙 설명")
    severity = models.CharField(
        max_length=20,
        choices=[
            ('high', '고위험'),
            ('medium', '중위험'),
            ('low', '저위험'),
        ],
        verbose_name="심각도"
    )
    penalty = models.TextField(verbose_name="처벌 내용")
    legal_basis = models.TextField(verbose_name="법적 근거")
    improvement_guide = models.TextField(verbose_name="개선 가이드")
    is_active = models.BooleanField(default=True, verbose_name="활성화 여부")
    created_at = models.DateTimeField(default=timezone.now, verbose_name="생성일시")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="수정일시")
    
    class Meta:
        verbose_name = "준수 규칙"
        verbose_name_plural = "준수 규칙들"
        ordering = ['category', 'severity', 'title']
    
    def __str__(self):
        return f"{self.category} - {self.title}"

class ComplianceKeyword(models.Model):
    """위반 키워드 모델"""
    
    rule = models.ForeignKey(ComplianceRule, on_delete=models.CASCADE, related_name='keywords', verbose_name="관련 규칙")
    keyword = models.CharField(max_length=100, verbose_name="키워드")
    description = models.TextField(blank=True, verbose_name="키워드 설명")
    is_active = models.BooleanField(default=True, verbose_name="활성화 여부")
    created_at = models.DateTimeField(default=timezone.now, verbose_name="생성일시")
    
    class Meta:
        verbose_name = "위반 키워드"
        verbose_name_plural = "위반 키워드들"
        ordering = ['rule', 'keyword']
    
    def __str__(self):
        return f"{self.rule.category} - {self.keyword}"

class RecommendedExpression(models.Model):
    """권장 표현 모델"""
    
    category = models.CharField(max_length=100, verbose_name="카테고리")
    original_text = models.CharField(max_length=200, verbose_name="원문 표현")
    improved_text = models.CharField(max_length=200, verbose_name="개선 표현")
    reason = models.TextField(verbose_name="개선 이유")
    importance = models.CharField(
        max_length=20,
        choices=[
            ('high', '높음'),
            ('medium', '보통'),
            ('low', '낮음'),
        ],
        default='medium',
        verbose_name="중요도"
    )
    is_active = models.BooleanField(default=True, verbose_name="활성화 여부")
    created_at = models.DateTimeField(default=timezone.now, verbose_name="생성일시")
    
    class Meta:
        verbose_name = "권장 표현"
        verbose_name_plural = "권장 표현들"
        ordering = ['category', 'importance', 'original_text']
    
    def __str__(self):
        return f"{self.category} - {self.original_text}"

class MedicalLawInfo(models.Model):
    """의료법 정보 모델"""
    
    title = models.CharField(max_length=200, verbose_name="제목")
    category = models.CharField(
        max_length=50,
        choices=[
            ('medical_law', '의료법'),
            ('advertising_law', '의료광고법'),
            ('guidelines', '가이드라인'),
            ('notices', '공지사항'),
            ('penalties', '처벌 기준'),
            ('review_process', '심의 절차'),
        ],
        verbose_name="카테고리"
    )
    content = models.TextField(verbose_name="내용")
    source = models.CharField(max_length=200, blank=True, verbose_name="출처")
    effective_date = models.DateField(blank=True, null=True, verbose_name="시행일")
    is_active = models.BooleanField(default=True, verbose_name="활성화 여부")
    order = models.IntegerField(default=0, verbose_name="정렬 순서")
    created_at = models.DateTimeField(default=timezone.now, verbose_name="생성일시")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="수정일시")
    
    class Meta:
        verbose_name = "의료법 정보"
        verbose_name_plural = "의료법 정보들"
        ordering = ['category', 'order', 'title']
    
    def __str__(self):
        return f"{self.get_category_display()} - {self.title}"

class ComplianceAnalysis(models.Model):
    """의료광고법 준수 분석 결과 모델"""
    
    # 입력 정보
    input_text = models.TextField(verbose_name="입력 텍스트")
    input_type = models.CharField(
        max_length=20, 
        choices=[
            ('text', '텍스트'),
            ('file', '파일'),
            ('url', 'URL'),
        ],
        verbose_name="입력 타입"
    )
    file_name = models.CharField(max_length=255, blank=True, null=True, verbose_name="파일명")
    url = models.URLField(blank=True, null=True, verbose_name="URL")
    
    # 분석 결과
    overall_score = models.IntegerField(verbose_name="전체 점수")
    compliance_status = models.CharField(
        max_length=20,
        choices=[
            ('적합', '적합'),
            ('부분적합', '부분적합'),
            ('부적합', '부적합'),
        ],
        verbose_name="준수 상태"
    )
    risk_level = models.CharField(
        max_length=20,
        choices=[
            ('low', '낮음'),
            ('medium', '보통'),
            ('high', '높음'),
        ],
        verbose_name="위험도"
    )
    
    # 위반 항목 (JSON 형태로 저장)
    violations = models.JSONField(default=list, verbose_name="위반 항목")
    recommendations = models.JSONField(default=list, verbose_name="개선 권장사항")
    
    # 메타데이터
    created_at = models.DateTimeField(default=timezone.now, verbose_name="생성일시")
    analysis_date = models.DateTimeField(default=timezone.now, verbose_name="분석일시")
    
    class Meta:
        verbose_name = "준수 분석 결과"
        verbose_name_plural = "준수 분석 결과들"
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.compliance_status} - {self.overall_score}점 ({self.created_at.strftime('%Y-%m-%d %H:%M')})"

class MedicalGuideline(models.Model):
    """의료법/광고법 가이드라인 문서 모델"""
    
    title = models.CharField(max_length=255, verbose_name="제목")
    category = models.CharField(
        max_length=50,
        choices=[
            ('medical_law', '의료법'),
            ('advertising_law', '의료광고법'),
            ('guidelines', '가이드라인'),
            ('notices', '공지사항'),
            ('cases', '판례'),
        ],
        default='guidelines',
        verbose_name="카테고리"
    )
    description = models.TextField(blank=True, verbose_name="설명")
    document_type = models.CharField(
        max_length=20,
        choices=[
            ('pdf', 'PDF'),
            ('doc', 'Word'),
            ('txt', '텍스트'),
        ],
        verbose_name="문서 타입"
    )
    file = models.FileField(upload_to='guidelines/', verbose_name="파일")
    extracted_text = models.TextField(blank=True, verbose_name="추출된 텍스트")
    uploaded_at = models.DateTimeField(default=timezone.now, verbose_name="업로드일시")
    is_active = models.BooleanField(default=True, verbose_name="활성화 여부")
    
    class Meta:
        verbose_name = "의료 가이드라인"
        verbose_name_plural = "의료 가이드라인들"
        ordering = ['-uploaded_at']
    
    def __str__(self):
        return f"{self.title} ({self.document_type.upper()})"
    
    @property
    def file_size(self):
        """파일 크기 반환 (bytes)"""
        if self.file:
            return self.file.size
        return 0

class GuidelineDocument(models.Model):
    """가이드라인 문서 모델"""
    
    title = models.CharField(max_length=255, verbose_name="제목")
    category = models.CharField(
        max_length=50,
        choices=[
            ('guidelines', '가이드라인'),
            ('laws', '법령'),
            ('precedents', '판례'),
            ('penalties', '처벌사례'),
            ('notices', '공지사항'),
            ('reviews', '심의안내'),
        ],
        verbose_name="카테고리"
    )
    description = models.TextField(blank=True, verbose_name="설명")
    content = models.TextField(verbose_name="내용")
    source = models.CharField(max_length=200, blank=True, verbose_name="출처")
    effective_date = models.DateField(blank=True, null=True, verbose_name="시행일")
    file = models.FileField(upload_to='guidelines/', blank=True, null=True, verbose_name="첨부파일")
    is_active = models.BooleanField(default=True, verbose_name="활성화 여부")
    order = models.IntegerField(default=0, verbose_name="정렬 순서")
    created_at = models.DateTimeField(default=timezone.now, verbose_name="생성일시")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="수정일시")
    
    class Meta:
        verbose_name = "가이드라인 문서"
        verbose_name_plural = "가이드라인 문서들"
        ordering = ['category', 'order', '-created_at']
    
    def __str__(self):
        return f"{self.get_category_display()} - {self.title}"
    
    @property
    def category_display(self):
        return self.get_category_display()

class GuidelineUpdate(models.Model):
    """가이드라인 업데이트 이력 모델"""
    
    document = models.ForeignKey(GuidelineDocument, on_delete=models.CASCADE, related_name='updates', verbose_name="문서")
    update_type = models.CharField(
        max_length=50,
        choices=[
            ('content_update', '내용 업데이트'),
            ('new_document', '새 문서 추가'),
            ('category_change', '카테고리 변경'),
            ('status_change', '상태 변경'),
        ],
        verbose_name="업데이트 유형"
    )
    previous_content = models.TextField(blank=True, verbose_name="이전 내용")
    new_content = models.TextField(blank=True, verbose_name="새 내용")
    update_reason = models.TextField(blank=True, verbose_name="업데이트 사유")
    updated_by = models.CharField(max_length=100, blank=True, verbose_name="업데이트자")
    created_at = models.DateTimeField(default=timezone.now, verbose_name="업데이트일시")
    
    class Meta:
        verbose_name = "가이드라인 업데이트"
        verbose_name_plural = "가이드라인 업데이트들"
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.document.title} - {self.get_update_type_display()} ({self.created_at.strftime('%Y-%m-%d')})"

class AIAnalysisResult(models.Model):
    """AI 분석 결과 모델"""
    
    document = models.ForeignKey(GuidelineDocument, on_delete=models.CASCADE, related_name='ai_analyses', verbose_name="문서")
    analysis_type = models.CharField(
        max_length=50,
        choices=[
            ('content_analysis', '내용 분석'),
            ('compliance_check', '준수성 검토'),
            ('risk_assessment', '위험도 평가'),
            ('improvement_suggestions', '개선 제안'),
        ],
        verbose_name="분석 유형"
    )
    analysis_result = models.JSONField(verbose_name="분석 결과")
    ai_model_used = models.CharField(max_length=100, verbose_name="사용된 AI 모델")
    processing_time = models.FloatField(blank=True, null=True, verbose_name="처리 시간(초)")
    created_at = models.DateTimeField(default=timezone.now, verbose_name="분석일시")
    
    class Meta:
        verbose_name = "AI 분석 결과"
        verbose_name_plural = "AI 분석 결과들"
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.document.title} - {self.get_analysis_type_display()} ({self.created_at.strftime('%Y-%m-%d %H:%M')})"

class ComplianceCategory(models.Model):
    """준수 카테고리 모델"""
    
    name = models.CharField(max_length=100, verbose_name="카테고리명")
    description = models.TextField(blank=True, verbose_name="설명")
    parent = models.ForeignKey('self', on_delete=models.CASCADE, blank=True, null=True, related_name='children', verbose_name="상위 카테고리")
    order = models.IntegerField(default=0, verbose_name="정렬 순서")
    is_active = models.BooleanField(default=True, verbose_name="활성화 여부")
    created_at = models.DateTimeField(default=timezone.now, verbose_name="생성일시")
    
    class Meta:
        verbose_name = "준수 카테고리"
        verbose_name_plural = "준수 카테고리들"
        ordering = ['order', 'name']
    
    def __str__(self):
        return self.name
    
    def get_full_path(self):
        """전체 경로 반환"""
        path = [self.name]
        parent = self.parent
        while parent:
            path.insert(0, parent.name)
            parent = parent.parent
        return ' > '.join(path)
