from django import forms
from .models import InterviewEvaluation, DocumentReview, Interview, EvaluationTemplate


class InterviewEvaluationForm(forms.ModelForm):
    """면접 평가 폼"""
    
    class Meta:
        model = InterviewEvaluation
        fields = [
            'interview', 'work_experience_score', 'intellectual_ability_score',
            'transportation_score', 'communication_score', 'personality_score',
            'overall_impression_score', 'overall_rating', 'strengths', 'weaknesses',
            'recommendations', 'hire_recommendation'
        ]
        widgets = {
            'interview': forms.Select(attrs={'class': 'form-select'}),
            'work_experience_score': forms.NumberInput(attrs={'min': '0', 'max': '20', 'class': 'form-control'}),
            'intellectual_ability_score': forms.NumberInput(attrs={'min': '0', 'max': '20', 'class': 'form-control'}),
            'transportation_score': forms.NumberInput(attrs={'min': '0', 'max': '15', 'class': 'form-control'}),
            'communication_score': forms.NumberInput(attrs={'min': '0', 'max': '10', 'class': 'form-control'}),
            'personality_score': forms.NumberInput(attrs={'min': '0', 'max': '10', 'class': 'form-control'}),
            'overall_impression_score': forms.NumberInput(attrs={'min': '0', 'max': '10', 'class': 'form-control'}),
            'overall_rating': forms.Select(attrs={'class': 'form-select'}),
            'strengths': forms.Textarea(attrs={'rows': 3, 'class': 'form-control'}),
            'weaknesses': forms.Textarea(attrs={'rows': 3, 'class': 'form-control'}),
            'recommendations': forms.Textarea(attrs={'rows': 4, 'class': 'form-control'}),
            'hire_recommendation': forms.Select(attrs={'class': 'form-select'}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # 필수 필드 표시
        for field_name in ['interview', 'overall_rating']:
            if field_name in self.fields:
                self.fields[field_name].widget.attrs['required'] = 'required'


class DocumentReviewForm(forms.ModelForm):
    """서류 검토 폼"""
    
    class Meta:
        model = DocumentReview
        fields = [
            'candidate', 'work_experience_score', 'education_score',
            'skill_score', 'passed', 'review_comments'
        ]
        widgets = {
            'candidate': forms.Select(attrs={'class': 'form-select'}),
            'work_experience_score': forms.NumberInput(attrs={'min': '0', 'max': '20', 'class': 'form-control'}),
            'education_score': forms.NumberInput(attrs={'min': '0', 'max': '15', 'class': 'form-control'}),
            'skill_score': forms.NumberInput(attrs={'min': '0', 'max': '10', 'class': 'form-control'}),
            'passed': forms.Select(attrs={'class': 'form-select'}),
            'review_comments': forms.Textarea(attrs={'rows': 4, 'class': 'form-control'}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # 필수 필드 표시
        for field_name in ['candidate']:
            if field_name in self.fields:
                self.fields[field_name].widget.attrs['required'] = 'required'


class InterviewForm(forms.ModelForm):
    """면접 폼"""
    
    class Meta:
        model = Interview
        fields = [
            'candidate', 'job_request', 'scheduled_date', 'duration_minutes',
            'interview_type', 'location', 'primary_interviewer', 'secondary_interviewers',
            'pre_interview_notes'
        ]
        widgets = {
            'candidate': forms.Select(attrs={'class': 'form-select'}),
            'job_request': forms.Select(attrs={'class': 'form-select'}),
            'scheduled_date': forms.DateTimeInput(attrs={'type': 'datetime-local', 'class': 'form-control'}),
            'duration_minutes': forms.NumberInput(attrs={'min': '15', 'max': '180', 'class': 'form-control'}),
            'interview_type': forms.Select(attrs={'class': 'form-select'}),
            'location': forms.TextInput(attrs={'class': 'form-control'}),
            'primary_interviewer': forms.Select(attrs={'class': 'form-select'}),
            'secondary_interviewers': forms.SelectMultiple(attrs={'class': 'form-select'}),
            'pre_interview_notes': forms.Textarea(attrs={'rows': 3, 'class': 'form-control'}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # 필수 필드 표시
        for field_name in ['candidate', 'job_request', 'scheduled_date', 'primary_interviewer']:
            if field_name in self.fields:
                self.fields[field_name].widget.attrs['required'] = 'required'


class EvaluationTemplateForm(forms.ModelForm):
    """평가 템플릿 폼"""
    
    class Meta:
        model = EvaluationTemplate
        fields = ['name', 'description', 'is_default', 'is_active', 'criteria_config']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'rows': 3, 'class': 'form-control'}),
            'is_default': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'criteria_config': forms.Textarea(attrs={'rows': 5, 'class': 'form-control'}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # 필수 필드 표시
        if 'name' in self.fields:
            self.fields['name'].widget.attrs['required'] = 'required' 