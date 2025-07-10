from django.contrib import admin
from .models import JobRequest, Workflow, WorkflowStep, WorkflowDocument, JobPosting, JobApplication, WorkflowProgress, JobRequestTemplate, WorkflowActionLog


@admin.register(JobRequest)
class JobRequestAdmin(admin.ModelAdmin):
    list_display = ['request_id', 'position_title', 'requester', 'status', 'urgency_level', 'created_at']
    list_filter = ['status', 'urgency_level', 'employment_type', 'created_at']
    search_fields = ['request_id', 'position_title', 'requester__username']
    readonly_fields = ['request_id', 'created_at', 'updated_at']
    date_hierarchy = 'created_at'
    
    fieldsets = (
        ('기본 정보', {
            'fields': ('request_id', 'requester', 'position_title', 'department', 'employment_type')
        }),
        ('급여 정보', {
            'fields': ('salary_min', 'salary_max')
        }),
        ('요구사항', {
            'fields': ('required_experience', 'preferred_qualifications', 'job_description')
        }),
        ('근무 조건', {
            'fields': ('working_hours', 'working_location')
        }),
        ('상태 관리', {
            'fields': ('urgency_level', 'status')
        }),
        ('시간 정보', {
            'fields': ('submitted_at', 'accepted_at', 'completed_at', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )


@admin.register(JobPosting)
class JobPostingAdmin(admin.ModelAdmin):
    list_display = [
        'posting_id', 'title', 'job_request', 'status', 'posting_platform',
        'view_count', 'application_count', 'created_by', 'created_at'
    ]
    list_filter = [
        'status', 'posting_platform', 'is_featured', 'created_at', 'posting_date'
    ]
    search_fields = ['title', 'summary', 'job_request__hospital_name', 'job_request__position_title']
    readonly_fields = ['posting_id', 'view_count', 'application_count', 'created_at', 'updated_at']
    date_hierarchy = 'created_at'
    
    fieldsets = (
        ('기본 정보', {
            'fields': ('posting_id', 'job_request', 'created_by', 'title', 'summary', 'detailed_description')
        }),
        ('자격 요건', {
            'fields': ('requirements', 'preferred_qualifications', 'benefits')
        }),
        ('일정 관리', {
            'fields': ('posting_date', 'closing_date', 'application_deadline')
        }),
        ('외부 게시 정보', {
            'fields': ('posting_url', 'posting_image', 'posting_platform')
        }),
        ('상태 및 통계', {
            'fields': ('status', 'is_featured', 'view_count', 'application_count')
        }),
        ('메타 정보', {
            'fields': ('created_at', 'updated_at', 'published_at'),
            'classes': ('collapse',)
        })
    )
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('job_request', 'created_by')


@admin.register(JobApplication)
class JobApplicationAdmin(admin.ModelAdmin):
    list_display = [
        'application_id', 'job_posting', 'applicant', 'status', 'submitted_at'
    ]
    list_filter = ['status', 'submitted_at', 'job_posting__status']
    search_fields = [
        'applicant__first_name', 'applicant__last_name', 'applicant__email',
        'job_posting__title'
    ]
    readonly_fields = ['application_id', 'submitted_at', 'updated_at']
    date_hierarchy = 'submitted_at'
    
    fieldsets = (
        ('기본 정보', {
            'fields': ('application_id', 'job_posting', 'applicant')
        }),
        ('지원 내용', {
            'fields': ('cover_letter', 'resume_file', 'portfolio_file')
        }),
        ('상태 관리', {
            'fields': ('status', 'reviewed_at')
        }),
        ('메타 정보', {
            'fields': ('submitted_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('job_posting', 'applicant')


@admin.register(WorkflowProgress)
class WorkflowProgressAdmin(admin.ModelAdmin):
    list_display = ['job_request', 'current_step', 'overall_progress', 'is_on_track', 'is_completed']
    list_filter = ['current_step', 'is_on_track', 'is_completed', 'created_at']
    search_fields = ['job_request__position_title', 'job_request__request_id']
    readonly_fields = ['overall_progress', 'created_at', 'updated_at']
    date_hierarchy = 'created_at'
    
    fieldsets = (
        ('기본 정보', {
            'fields': ('job_request', 'current_step', 'step_completion_rate')
        }),
        ('진행률', {
            'fields': ('overall_progress', 'is_completed')
        }),
        ('일정 관리', {
            'fields': ('target_completion_date', 'estimated_completion_date', 'actual_completion_date', 'is_on_track')
        }),
        ('성과 지표', {
            'fields': ('total_candidates', 'screened_candidates', 'interviewed_candidates', 'hired_candidates')
        }),
        ('병목 지점', {
            'fields': ('bottlenecks',),
            'classes': ('collapse',)
        }),
        ('시간 추적', {
            'fields': ('step_start_times', 'step_end_times', 'step_durations'),
            'classes': ('collapse',)
        }),
        ('시간 정보', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )


@admin.register(Workflow)
class WorkflowAdmin(admin.ModelAdmin):
    list_display = ['title', 'description', 'status', 'priority', 'assigned_to', 'created_at']
    list_filter = ['status', 'priority', 'created_at']
    search_fields = ['title', 'description', 'assigned_to__username']


@admin.register(WorkflowStep)
class WorkflowStepAdmin(admin.ModelAdmin):
    list_display = ['workflow', 'name', 'order', 'status', 'assigned_to', 'due_date']
    list_filter = ['workflow', 'status']
    search_fields = ['name', 'workflow__title']


@admin.register(WorkflowDocument)
class WorkflowDocumentAdmin(admin.ModelAdmin):
    list_display = ['workflow', 'title', 'document_type', 'uploaded_by', 'uploaded_at']
    list_filter = ['document_type', 'uploaded_at']
    search_fields = ['title', 'workflow__title']


@admin.register(JobRequestTemplate)
class JobRequestTemplateAdmin(admin.ModelAdmin):
    """채용 요청 템플릿 관리"""
    list_display = [
        'name', 'position_title', 'department', 'employment_type', 
        'is_default', 'is_active', 'created_by', 'created_at'
    ]
    list_filter = [
        'is_default', 'is_active', 'employment_type', 'urgency_level',
        'created_at', 'updated_at'
    ]
    search_fields = [
        'name', 'position_title', 'department', 'hospital_name',
        'hospital_branch', 'description'
    ]
    readonly_fields = ['created_at', 'updated_at']
    fieldsets = (
        ('기본 정보', {
            'fields': ('name', 'description', 'is_default', 'is_active', 'created_by')
        }),
        ('병원 정보', {
            'fields': (
                'hospital_name', 'hospital_branch', 'hospital_address',
                'hospital_phone', 'hospital_contact_person'
            )
        }),
        ('채용 정보', {
            'fields': (
                'position_title', 'department', 'employment_type',
                'salary_min', 'salary_max'
            )
        }),
        ('요구사항', {
            'fields': (
                'required_experience', 'preferred_qualifications',
                'job_description', 'working_hours', 'working_location'
            )
        }),
        ('추가 정보', {
            'fields': (
                'special_requirements', 'expected_start_date',
                'recruitment_period', 'urgency_level'
            )
        }),
        ('메타 정보', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def save_model(self, request, obj, form, change):
        if not change:  # 새로 생성하는 경우
            obj.created_by = request.user
        super().save_model(request, obj, form, change)


@admin.register(WorkflowActionLog)
class WorkflowActionLogAdmin(admin.ModelAdmin):
    """워크플로우 액션 로그 관리"""
    list_display = [
        'workflow', 'action_type', 'performed_by', 'performed_at', 'ip_address'
    ]
    list_filter = [
        'action_type', 'performed_at', 'workflow__status'
    ]
    search_fields = [
        'workflow__title', 'performed_by__username', 'action_description',
        'old_value', 'new_value'
    ]
    readonly_fields = [
        'workflow', 'step', 'action_type', 'action_description',
        'old_value', 'new_value', 'performed_by', 'performed_at',
        'ip_address', 'user_agent'
    ]
    date_hierarchy = 'performed_at'
    
    fieldsets = (
        ('기본 정보', {
            'fields': ('workflow', 'step', 'action_type', 'action_description')
        }),
        ('변경 정보', {
            'fields': ('old_value', 'new_value')
        }),
        ('사용자 정보', {
            'fields': ('performed_by', 'performed_at')
        }),
        ('시스템 정보', {
            'fields': ('ip_address', 'user_agent'),
            'classes': ('collapse',)
        })
    )
    
    def has_add_permission(self, request):
        return False
    
    def has_change_permission(self, request, obj=None):
        return False
    
    def has_delete_permission(self, request, obj=None):
        return request.user.is_superuser
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related(
            'workflow', 'step', 'performed_by'
        )
