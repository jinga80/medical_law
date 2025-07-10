from django import forms
from .models import Candidate, CandidateReview, CandidateNote

class CandidateForm(forms.ModelForm):
    """후보자 등록/수정 폼"""
    
    class Meta:
        model = Candidate
        fields = [
            'name', 'email', 'phone', 'birth_date', 'address', 'gender',
            'education_level', 'major', 'university', 'graduation_year',
            'total_experience_years', 'relevant_experience', 'current_company',
            'current_position', 'licenses', 'skills', 'languages',
            'resume_file', 'portfolio_file', 'cover_letter',
            'recommendation_reason', 'expected_salary', 'available_start_date',
            'position', 'branch', 'internal_notes'
        ]
        widgets = {
            'birth_date': forms.DateInput(attrs={'type': 'date'}),
            'available_start_date': forms.DateInput(attrs={'type': 'date'}),
            'relevant_experience': forms.Textarea(attrs={'rows': 4}),
            'recommendation_reason': forms.Textarea(attrs={'rows': 3}),
            'internal_notes': forms.Textarea(attrs={'rows': 3}),
        }

class CandidateReviewForm(forms.ModelForm):
    """후보자 검토 폼"""
    
    class Meta:
        model = CandidateReview
        fields = [
            'review_type', 'experience_score', 'education_score', 'skill_score',
            'personality_score', 'motivation_score', 'strengths', 'weaknesses',
            'improvement_areas', 'overall_comments'
        ]
        widgets = {
            'strengths': forms.Textarea(attrs={'rows': 3, 'placeholder': '후보자의 강점을 입력하세요...'}),
            'weaknesses': forms.Textarea(attrs={'rows': 3, 'placeholder': '후보자의 약점을 입력하세요...'}),
            'improvement_areas': forms.Textarea(attrs={'rows': 3, 'placeholder': '개선이 필요한 영역을 입력하세요...'}),
            'overall_comments': forms.Textarea(attrs={'rows': 4, 'placeholder': '종합적인 검토 의견을 입력하세요...'}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # 점수 필드에 도움말 추가
        self.fields['experience_score'].help_text = '경력의 적합성 및 품질 (25점 만점)'
        self.fields['education_score'].help_text = '학력 및 전공 적합성 (20점 만점)'
        self.fields['skill_score'].help_text = '필요 스킬 보유 여부 (25점 만점)'
        self.fields['personality_score'].help_text = '인성 및 적응력 (15점 만점)'
        self.fields['motivation_score'].help_text = '지원 동기 및 열정 (15점 만점)'

class CandidateNoteForm(forms.ModelForm):
    """후보자 메모 폼"""
    
    class Meta:
        model = CandidateNote
        fields = ['note_type', 'title', 'content', 'is_private']
        widgets = {
            'content': forms.Textarea(attrs={'rows': 4, 'placeholder': '메모 내용을 입력하세요...'}),
        }

class CandidateStatusUpdateForm(forms.ModelForm):
    """후보자 상태 업데이트 폼"""
    
    class Meta:
        model = Candidate
        fields = ['status', 'review_status', 'review_comments']
        widgets = {
            'review_comments': forms.Textarea(attrs={'rows': 3, 'placeholder': '상태 변경 사유를 입력하세요...'}),
        }

class CandidateInterviewForm(forms.ModelForm):
    """후보자 면접 평가 폼"""
    
    class Meta:
        model = Candidate
        fields = ['interview_decision', 'interview_score', 'interview_comments']
        widgets = {
            'interview_comments': forms.Textarea(attrs={'rows': 4, 'placeholder': '면접 평가 의견을 입력하세요...'}),
        } 