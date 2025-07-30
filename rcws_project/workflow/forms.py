from django import forms
from accounts.models import User, Hospital, HospitalBranch, PositionTemplate
from .models import JobRequest, WorkflowStep, Workflow, WorkflowDocument, JobPosting, JobApplication, JobRequestTemplate
from django.utils import timezone
from datetime import timedelta
import os
from urllib.parse import urlparse


class JobRequestForm(forms.ModelForm):
    """채용 요청 폼 (병원 → 채용회사)"""
    
    hospital = forms.ModelChoiceField(
        queryset=Hospital.objects.all(), 
        required=True, 
        label='병원명',
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    branch = forms.ModelChoiceField(
        queryset=HospitalBranch.objects.none(), 
        required=True, 
        label='지점',
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    position_template = forms.ModelChoiceField(
        queryset=JobRequestTemplate.objects.filter(is_active=True), 
        required=False, 
        label='포지션 템플릿',
        widget=forms.Select(attrs={'class': 'form-select'})
    )

    class Meta:
        model = JobRequest
        fields = [
            'hospital', 'branch', 'hospital_name', 'hospital_branch', 'hospital_address', 'hospital_phone', 'hospital_contact_person',
            'position_template', 'position_title', 'department', 'employment_type',
            'salary_min', 'salary_max', 'required_experience', 'preferred_qualifications',
            'job_description', 'working_hours', 'working_location',
            'special_requirements', 'expected_start_date', 'recruitment_period',
            'urgency_level', 'status'
        ]
        widgets = {
            'hospital_name': forms.TextInput(attrs={'class': 'form-control', 'readonly': 'readonly'}),
            'hospital_branch': forms.TextInput(attrs={'class': 'form-control', 'readonly': 'readonly'}),
            'hospital_address': forms.Textarea(attrs={'rows': 3, 'class': 'form-control', 'readonly': 'readonly'}),
            'hospital_phone': forms.TextInput(attrs={'class': 'form-control', 'readonly': 'readonly'}),
            'hospital_contact_person': forms.TextInput(attrs={'class': 'form-control', 'readonly': 'readonly'}),
            'position_title': forms.TextInput(attrs={'class': 'form-control'}),
            'department': forms.TextInput(attrs={'class': 'form-control'}),
            'employment_type': forms.Select(attrs={'class': 'form-select'}),
            'salary_min': forms.NumberInput(attrs={'min': '0', 'class': 'form-control'}),
            'salary_max': forms.NumberInput(attrs={'min': '0', 'class': 'form-control'}),
            'required_experience': forms.Textarea(attrs={'rows': 3, 'class': 'form-control'}),
            'preferred_qualifications': forms.Textarea(attrs={'rows': 2, 'class': 'form-control'}),
            'job_description': forms.Textarea(attrs={'rows': 4, 'class': 'form-control'}),
            'working_hours': forms.TextInput(attrs={'class': 'form-control'}),
            'working_location': forms.TextInput(attrs={'class': 'form-control'}),
            'special_requirements': forms.Textarea(attrs={'rows': 3, 'class': 'form-control'}),
            'expected_start_date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'recruitment_period': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '예: 2주, 1개월'}),
            'urgency_level': forms.Select(attrs={'class': 'form-select'}),
            'status': forms.Select(attrs={'class': 'form-select'}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # 병원 선택 시 지점 쿼리셋 동적 변경
        if 'hospital' in self.data:
            try:
                hospital_id = int(self.data.get('hospital'))
                self.fields['branch'].queryset = HospitalBranch.objects.filter(hospital_id=hospital_id)
            except (ValueError, TypeError):
                self.fields['branch'].queryset = HospitalBranch.objects.none()
        elif self.instance.pk and self.instance.hospital:
            self.fields['branch'].queryset = HospitalBranch.objects.filter(hospital=self.instance.hospital)
        else:
            self.fields['branch'].queryset = HospitalBranch.objects.none()
        # 기본값 설정
        if not self.instance.pk:
            self.fields['status'].initial = 'draft'
            self.fields['urgency_level'].initial = 'medium'


class JobPostingForm(forms.ModelForm):
    """채용 공고 폼"""
    
    class Meta:
        model = JobPosting
        fields = [
            'title', 'summary', 'detailed_description',
            'requirements', 'preferred_qualifications', 'benefits',
            'posting_date', 'closing_date', 'application_deadline',
            'posting_url', 'posting_image', 'posting_platform',
            'status', 'is_featured'
        ]
        widgets = {
            'title': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': '채용 공고 제목을 입력하세요'
            }),
            'summary': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': '채용 공고 요약을 입력하세요'
            }),
            'detailed_description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 5,
                'placeholder': '상세한 업무 내용과 설명을 입력하세요'
            }),
            'requirements': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': '필수 자격 요건을 입력하세요'
            }),
            'preferred_qualifications': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': '우대사항을 입력하세요 (선택사항)'
            }),
            'benefits': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': '복리후생 및 혜택을 입력하세요 (선택사항)'
            }),
            'posting_date': forms.DateTimeInput(attrs={
                'class': 'form-control',
                'type': 'datetime-local'
            }),
            'closing_date': forms.DateTimeInput(attrs={
                'class': 'form-control',
                'type': 'datetime-local'
            }),
            'application_deadline': forms.DateTimeInput(attrs={
                'class': 'form-control',
                'type': 'datetime-local'
            }),
            'posting_url': forms.URLInput(attrs={
                'class': 'form-control',
                'placeholder': 'https://example.com/job-posting'
            }),
            'posting_platform': forms.Select(attrs={
                'class': 'form-select'
            }, choices=[
                ('', '플랫폼 선택'),
                ('jobkorea', '잡코리아'),
                ('saramin', '사람인'),
                ('incruit', '인크루트'),
                ('wanted', '원티드'),
                ('linkedin', '링크드인'),
                ('indeed', '인디드'),
                ('other', '기타')
            ]),
            'status': forms.Select(attrs={
                'class': 'form-select'
            }),
            'is_featured': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            })
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # 기본값 설정
        if not self.instance.pk:
            self.fields['posting_date'].initial = timezone.now()
            self.fields['closing_date'].initial = timezone.now() + timedelta(days=30)
            self.fields['application_deadline'].initial = timezone.now() + timedelta(days=25)
    
    def clean(self):
        cleaned_data = super().clean()
        posting_date = cleaned_data.get('posting_date')
        closing_date = cleaned_data.get('closing_date')
        application_deadline = cleaned_data.get('application_deadline')
        
        if posting_date and closing_date and posting_date >= closing_date:
            raise forms.ValidationError('게시일은 마감일보다 이전이어야 합니다.')
        
        if application_deadline and closing_date and application_deadline >= closing_date:
            raise forms.ValidationError('지원 마감일은 공고 마감일보다 이전이어야 합니다.')
        
        return cleaned_data


class JobPostingUpdateForm(forms.ModelForm):
    """채용 공고 수정 폼"""
    
    class Meta:
        model = JobPosting
        fields = [
            'posting_url', 'posting_image', 'posting_platform',
            'status', 'is_featured'
        ]
        widgets = {
            'posting_url': forms.URLInput(attrs={
                'class': 'form-control',
                'placeholder': 'https://example.com/job-posting'
            }),
            'posting_platform': forms.Select(attrs={
                'class': 'form-select'
            }, choices=[
                ('', '플랫폼 선택'),
                ('jobkorea', '잡코리아'),
                ('saramin', '사람인'),
                ('incruit', '인크루트'),
                ('wanted', '원티드'),
                ('linkedin', '링크드인'),
                ('indeed', '인디드'),
                ('other', '기타')
            ]),
            'status': forms.Select(attrs={
                'class': 'form-select'
            }),
            'is_featured': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            })
        }
    
    def clean_posting_url(self):
        url = self.cleaned_data.get('posting_url')
        if url:
            # URL 유효성 검사
            try:
                result = urlparse(url)
                if not all([result.scheme, result.netloc]):
                    raise forms.ValidationError('올바른 URL 형식을 입력해주세요.')
            except Exception:
                raise forms.ValidationError('올바른 URL 형식을 입력해주세요.')
        return url


class JobApplicationForm(forms.ModelForm):
    """구인 공고 지원 폼"""
    
    class Meta:
        model = JobApplication
        fields = ['cover_letter', 'resume_file', 'portfolio_file']
        widgets = {
            'cover_letter': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 6,
                'placeholder': '자기소개서를 작성해주세요...'
            }),
            'resume_file': forms.FileInput(attrs={
                'class': 'form-control',
                'accept': '.pdf,.doc,.docx'
            }),
            'portfolio_file': forms.FileInput(attrs={
                'class': 'form-control',
                'accept': '.pdf,.doc,.docx,.zip,.rar'
            })
        }
    
    def clean_resume_file(self):
        file = self.cleaned_data.get('resume_file')
        if file:
            # 파일 크기 검사 (5MB 제한)
            if file.size > 5 * 1024 * 1024:
                raise forms.ValidationError('이력서 파일 크기는 5MB 이하여야 합니다.')
            
            # 파일 확장자 검사
            ext = os.path.splitext(file.name)[1].lower()
            if ext not in ['.pdf', '.doc', '.docx']:
                raise forms.ValidationError('이력서는 PDF, DOC, DOCX 형식만 업로드 가능합니다.')
        
        return file
    
    def clean_portfolio_file(self):
        file = self.cleaned_data.get('portfolio_file')
        if file:
            # 파일 크기 검사 (10MB 제한)
            if file.size > 10 * 1024 * 1024:
                raise forms.ValidationError('포트폴리오 파일 크기는 10MB 이하여야 합니다.')
            
            # 파일 확장자 검사
            ext = os.path.splitext(file.name)[1].lower()
            if ext not in ['.pdf', '.doc', '.docx', '.zip', '.rar']:
                raise forms.ValidationError('포트폴리오는 PDF, DOC, DOCX, ZIP, RAR 형식만 업로드 가능합니다.')
        
        return file


class WorkflowStepForm(forms.ModelForm):
    """워크플로우 단계 폼"""
    
    class Meta:
        model = WorkflowStep
        fields = [
            'workflow', 'name', 'order', 'status', 'assigned_to',
            'due_date', 'started_at', 'completed_at', 'description', 'notes'
        ]
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'order': forms.NumberInput(attrs={'min': '1', 'class': 'form-control'}),
            'status': forms.Select(attrs={'class': 'form-select'}),
            'due_date': forms.DateTimeInput(attrs={'type': 'datetime-local', 'class': 'form-control'}),
            'started_at': forms.DateTimeInput(attrs={'type': 'datetime-local', 'class': 'form-control'}),
            'completed_at': forms.DateTimeInput(attrs={'type': 'datetime-local', 'class': 'form-control'}),
            'description': forms.Textarea(attrs={'rows': 3, 'class': 'form-control'}),
            'notes': forms.Textarea(attrs={'rows': 2, 'class': 'form-control'}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field_name in ['workflow', 'name', 'order', 'status']:
            if field_name in self.fields:
                self.fields[field_name].widget.attrs['required'] = 'required'


class WorkflowForm(forms.ModelForm):
    """워크플로우 폼"""
    
    job_request = forms.ModelChoiceField(
        queryset=JobRequest.objects.filter(status__in=['submitted', 'accepted', 'in_progress']),
        required=False,
        label='기존 채용 요청 선택',
        help_text='기존 채용 요청을 선택하면 제목과 설명이 자동으로 입력됩니다',
        widget=forms.Select(attrs={
            'class': 'form-select',
            'id': 'id_job_request'
        })
    )
    
    class Meta:
        model = Workflow
        fields = [
            'title', 'description', 'status', 'priority',
            'due_date'
        ]
        widgets = {
            'title': forms.TextInput(attrs={
                'class': 'form-control', 
                'required': 'required',
                'id': 'id_title',
                'placeholder': '채용 제목을 입력하세요'
            }),
            'description': forms.Textarea(attrs={
                'rows': 3, 
                'class': 'form-control',
                'id': 'id_description',
                'placeholder': '채용에 대한 설명을 입력하세요'
            }),
            'status': forms.Select(attrs={'class': 'form-select'}),
            'priority': forms.Select(attrs={'class': 'form-select'}),
            'due_date': forms.DateTimeInput(attrs={
                'type': 'datetime-local', 
                'class': 'form-control'
            }),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # 기본값 설정
        if not self.instance.pk:  # 새로 생성하는 경우
            self.fields['status'].initial = 'pending'
            self.fields['priority'].initial = 'medium'
        
        # 채용 요청 선택 옵션에 빈 옵션 추가
        self.fields['job_request'].empty_label = "직접 입력 (채용 요청 선택 안함)"
        
        # 채용 요청 필드를 첫 번째로 이동
        field_order = ['job_request'] + [field for field in self.fields if field != 'job_request']
        self.fields = {field: self.fields[field] for field in field_order}


class WorkflowDocumentForm(forms.ModelForm):
    """워크플로우 문서 폼"""
    
    class Meta:
        model = WorkflowDocument
        fields = ['workflow', 'document_type', 'title', 'file', 'uploaded_by']
        widgets = {
            'workflow': forms.Select(attrs={'class': 'form-select'}),
            'document_type': forms.Select(attrs={'class': 'form-select'}),
            'title': forms.TextInput(attrs={'class': 'form-control'}),
            'file': forms.FileInput(attrs={'class': 'form-control'}),
            'uploaded_by': forms.Select(attrs={'class': 'form-select'}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field_name in ['workflow', 'document_type', 'title', 'file', 'uploaded_by']:
            if field_name in self.fields:
                self.fields[field_name].widget.attrs['required'] = 'required'


class JobRequestUpdateForm(forms.ModelForm):
    """채용 요청 수정 폼"""
    
    class Meta:
        model = JobRequest
        fields = [
            'hospital_name', 'hospital_branch', 'hospital_address', 'hospital_phone', 'hospital_contact_person',
            'position_title', 'department', 'employment_type',
            'salary_min', 'salary_max',
            'required_experience', 'preferred_qualifications', 'job_description',
            'working_hours', 'working_location',
            'special_requirements', 'expected_start_date', 'recruitment_period',
            'urgency_level'
        ]
        widgets = {
            'hospital_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': '병원명을 입력하세요'
            }),
            'hospital_branch': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': '지점명을 입력하세요'
            }),
            'hospital_address': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 2,
                'placeholder': '병원 주소를 입력하세요'
            }),
            'hospital_phone': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': '연락처를 입력하세요'
            }),
            'hospital_contact_person': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': '담당자명을 입력하세요'
            }),
            'position_title': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': '채용 포지션을 입력하세요'
            }),
            'department': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': '부서를 입력하세요'
            }),
            'employment_type': forms.Select(attrs={
                'class': 'form-select'
            }),
            'salary_min': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': '최소 급여 (만원)'
            }),
            'salary_max': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': '최대 급여 (만원)'
            }),
            'required_experience': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': '필수 경력 요구사항을 입력하세요'
            }),
            'preferred_qualifications': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': '우대사항을 입력하세요'
            }),
            'job_description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': '업무 내용을 상세히 입력하세요'
            }),
            'working_hours': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': '근무 시간을 입력하세요'
            }),
            'working_location': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': '근무 장소를 입력하세요'
            }),
            'special_requirements': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': '특별 요청사항을 입력하세요'
            }),
            'expected_start_date': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date'
            }),
            'recruitment_period': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': '채용 기간을 입력하세요'
            }),
            'urgency_level': forms.Select(attrs={
                'class': 'form-select'
            })
        }


class JobRequestTemplateForm(forms.ModelForm):
    """채용 요청 템플릿 폼"""
    
    class Meta:
        model = JobRequestTemplate
        fields = [
            'name', 'description', 'is_default', 'is_active',
            'hospital_name', 'hospital_branch', 'hospital_address', 
            'hospital_phone', 'hospital_contact_person',
            'position_title', 'department', 'employment_type',
            'salary_min', 'salary_max', 'required_experience', 
            'preferred_qualifications', 'job_description',
            'working_hours', 'working_location', 'special_requirements',
            'expected_start_date', 'recruitment_period', 'urgency_level'
        ]
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'hospital_name': forms.TextInput(attrs={'class': 'form-control'}),
            'hospital_branch': forms.TextInput(attrs={'class': 'form-control'}),
            'hospital_address': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
            'hospital_phone': forms.TextInput(attrs={'class': 'form-control'}),
            'hospital_contact_person': forms.TextInput(attrs={'class': 'form-control'}),
            'position_title': forms.TextInput(attrs={'class': 'form-control'}),
            'department': forms.TextInput(attrs={'class': 'form-control'}),
            'employment_type': forms.Select(attrs={'class': 'form-select'}),
            'salary_min': forms.NumberInput(attrs={'class': 'form-control'}),
            'salary_max': forms.NumberInput(attrs={'class': 'form-control'}),
            'required_experience': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'preferred_qualifications': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'job_description': forms.Textarea(attrs={'class': 'form-control', 'rows': 4}),
            'working_hours': forms.TextInput(attrs={'class': 'form-control'}),
            'working_location': forms.TextInput(attrs={'class': 'form-control'}),
            'special_requirements': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'expected_start_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'recruitment_period': forms.TextInput(attrs={'class': 'form-control'}),
            'urgency_level': forms.Select(attrs={'class': 'form-select'}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # 필수 필드 표시
        required_fields = ['name', 'position_title', 'department', 'employment_type', 
                          'required_experience', 'job_description']
        for field_name in required_fields:
            if field_name in self.fields:
                self.fields[field_name].widget.attrs['required'] = 'required' 