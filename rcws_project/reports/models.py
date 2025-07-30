from django.db import models
from django.utils import timezone
from accounts.models import User
import uuid


class Report(models.Model):
    """보고서 모델"""
    
    REPORT_TYPE_CHOICES = [
        ('monthly_performance', '월간 성과 보고서'),
        ('candidate_analysis', '후보자 분석 보고서'),
        ('workflow_analysis', '워크플로우 분석'),
        ('interview_schedule', '면접 일정 보고서'),
        ('custom', '커스텀 보고서')
    ]
    
    STATUS_CHOICES = [
        ('draft', '작성중'),
        ('generating', '생성중'),
        ('completed', '완료'),
        ('failed', '실패')
    ]
    
    # 기본 정보
    title = models.CharField(max_length=200, verbose_name='제목')
    description = models.TextField(blank=True, verbose_name='설명')
    report_type = models.CharField(
        max_length=30,
        choices=REPORT_TYPE_CHOICES,
        verbose_name='보고서 유형'
    )
    
    # 생성자 및 상태
    created_by = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='created_reports',
        verbose_name='생성자'
    )
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='draft',
        verbose_name='상태'
    )
    
    # 파일 정보
    file_path = models.CharField(max_length=500, blank=True, verbose_name='파일 경로')
    file_size = models.IntegerField(default=0, verbose_name='파일 크기')
    
    # 생성 옵션
    date_from = models.DateField(blank=True, null=True, verbose_name='시작일')
    date_to = models.DateField(blank=True, null=True, verbose_name='종료일')
    include_charts = models.BooleanField(default=True, verbose_name='차트 포함')
    include_details = models.BooleanField(default=True, verbose_name='상세 정보 포함')
    
    # 메타 정보
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='생성일')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='수정일')
    generated_at = models.DateTimeField(blank=True, null=True, verbose_name='생성 완료일')
    
    class Meta:
        verbose_name = '보고서'
        verbose_name_plural = '보고서들'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.title} ({self.get_report_type_display()})"
    
    def get_type_color(self):
        """보고서 유형별 색상 반환"""
        colors = {
            'monthly_performance': 'primary',
            'candidate_analysis': 'success',
            'workflow_analysis': 'warning',
            'interview_schedule': 'info',
            'custom': 'secondary'
        }
        return colors.get(self.report_type, 'secondary')
    
    @property
    def is_generated(self):
        """생성 완료 여부"""
        return self.status == 'completed' and self.file_path
    
    @property
    def is_generating(self):
        """생성 중 여부"""
        return self.status == 'generating'
    
    def generate_report(self):
        """보고서 생성"""
        self.status = 'generating'
        self.save()
        
        try:
            # 실제 보고서 생성 로직 (여기서는 간단히 시뮬레이션)
            import time
            time.sleep(2)  # 생성 시간 시뮬레이션
            
            self.status = 'completed'
            self.generated_at = timezone.now()
            self.file_path = f'reports/{self.id}_{self.title}.pdf'
            self.file_size = 1024 * 1024  # 1MB 시뮬레이션
            self.save()
            
            return True
        except Exception as e:
            self.status = 'failed'
            self.save()
            return False
