from django import forms
from .models import Report

class ReportForm(forms.ModelForm):
    """보고서 생성 폼"""
    
    class Meta:
        model = Report
        fields = [
            'title', 'description', 'report_type', 'date_from', 'date_to',
            'include_charts', 'include_details'
        ]
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control', 'required': 'required'}),
            'description': forms.Textarea(attrs={'rows': 3, 'class': 'form-control'}),
            'report_type': forms.Select(attrs={'class': 'form-select', 'required': 'required'}),
            'date_from': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'date_to': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'include_charts': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'include_details': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # 날짜 필드에 오늘 날짜를 기본값으로 설정
        from datetime import date
        if not self.instance.pk:  # 새로 생성하는 경우
            self.fields['date_from'].initial = date.today()
            self.fields['date_to'].initial = date.today()

class ReportFilterForm(forms.Form):
    """보고서 필터 폼"""
    
    REPORT_TYPE_CHOICES = [
        ('candidate_summary', '후보자 요약'),
        ('workflow_progress', '워크플로우 진행상황'),
        ('evaluation_summary', '평가 요약'),
        ('performance_analysis', '성과 분석'),
        ('timeline_analysis', '타임라인 분석')
    ]
    
    PERIOD_CHOICES = [
        ('week', '1주일'),
        ('month', '1개월'),
        ('quarter', '3개월'),
        ('year', '1년'),
        ('custom', '사용자 정의')
    ]
    
    report_type = forms.ChoiceField(
        choices=REPORT_TYPE_CHOICES,
        label='보고서 유형',
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    
    period = forms.ChoiceField(
        choices=PERIOD_CHOICES,
        label='기간',
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    
    start_date = forms.DateField(
        label='시작일',
        required=False,
        widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-control'})
    )
    
    end_date = forms.DateField(
        label='종료일',
        required=False,
        widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-control'})
    )
    
    organization = forms.CharField(
        label='조직',
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )
    
    status = forms.CharField(
        label='상태',
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control'})
    ) 