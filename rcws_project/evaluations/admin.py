from django.contrib import admin
from .models import Interview, InterviewEvaluation, DocumentReview, DocumentScreening, InterviewScheduling


@admin.register(Interview)
class InterviewAdmin(admin.ModelAdmin):
    list_display = ['candidate', 'scheduled_date', 'interview_type', 'status', 'primary_interviewer']
    list_filter = ['interview_type', 'status', 'scheduled_date']
    search_fields = ['candidate__name', 'primary_interviewer__username']
    date_hierarchy = 'scheduled_date'
    
    fieldsets = (
        ('기본 정보', {
            'fields': ('candidate', 'job_request', 'scheduled_date', 'duration_minutes')
        }),
        ('면접 정보', {
            'fields': ('interview_type', 'location', 'primary_interviewer', 'secondary_interviewers')
        }),
        ('상태 관리', {
            'fields': ('status', 'actual_start_time', 'actual_end_time')
        }),
        ('메모', {
            'fields': ('pre_interview_notes', 'post_interview_notes'),
            'classes': ('collapse',)
        }),
        ('시간 정보', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )


@admin.register(InterviewEvaluation)
class InterviewEvaluationAdmin(admin.ModelAdmin):
    list_display = ['interview', 'evaluator', 'total_score', 'overall_rating', 'hire_recommendation', 'evaluated_at']
    list_filter = ['overall_rating', 'hire_recommendation', 'evaluated_at']
    search_fields = ['interview__candidate__name', 'evaluator__username']
    readonly_fields = ['total_score', 'evaluated_at', 'updated_at']
    date_hierarchy = 'evaluated_at'
    
    fieldsets = (
        ('기본 정보', {
            'fields': ('interview', 'evaluator')
        }),
        ('평가 점수', {
            'fields': (
                'work_experience_score', 'intellectual_ability_score', 'transportation_score',
                'communication_score', 'personality_score', 'overall_impression_score', 'total_score'
            )
        }),
        ('종합 평가', {
            'fields': ('overall_rating', 'hire_recommendation')
        }),
        ('평가 의견', {
            'fields': ('strengths', 'weaknesses', 'recommendations'),
            'classes': ('collapse',)
        }),
        ('시간 정보', {
            'fields': ('evaluated_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )


@admin.register(DocumentReview)
class DocumentReviewAdmin(admin.ModelAdmin):
    list_display = ['candidate', 'reviewer', 'total_score', 'passed', 'reviewed_at']
    list_filter = ['passed', 'reviewed_at']
    search_fields = ['candidate__name', 'reviewer__username']
    readonly_fields = ['total_score', 'reviewed_at', 'updated_at']
    date_hierarchy = 'reviewed_at'
    
    fieldsets = (
        ('기본 정보', {
            'fields': ('candidate', 'reviewer')
        }),
        ('평가 점수', {
            'fields': ('work_experience_score', 'education_score', 'skill_score', 'total_score')
        }),
        ('결과', {
            'fields': ('passed', 'review_comments')
        }),
        ('시간 정보', {
            'fields': ('reviewed_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )


@admin.register(DocumentScreening)
class DocumentScreeningAdmin(admin.ModelAdmin):
    list_display = ['candidate', 'screener', 'screening_status', 'total_score', 'passed', 'created_at']
    list_filter = ['screening_status', 'passed', 'created_at']
    search_fields = ['candidate__name', 'screener__username']
    readonly_fields = ['total_score', 'created_at', 'updated_at']
    date_hierarchy = 'created_at'
    
    fieldsets = (
        ('기본 정보', {
            'fields': ('candidate', 'screener', 'screening_status')
        }),
        ('평가 점수', {
            'fields': (
                'resume_quality_score', 'experience_match_score', 'education_score',
                'skill_match_score', 'overall_impression_score', 'total_score', 'passing_score'
            )
        }),
        ('결과', {
            'fields': ('passed',)
        }),
        ('평가 의견', {
            'fields': ('strengths', 'weaknesses', 'improvement_suggestions', 'screening_notes'),
            'classes': ('collapse',)
        }),
        ('추가 정보 요청', {
            'fields': ('additional_info_requested', 'info_deadline'),
            'classes': ('collapse',)
        }),
        ('시간 정보', {
            'fields': ('screening_started_at', 'screening_completed_at', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )


@admin.register(InterviewScheduling)
class InterviewSchedulingAdmin(admin.ModelAdmin):
    list_display = ['candidate', 'coordinator', 'scheduling_status', 'contact_attempts', 'is_urgent', 'created_at']
    list_filter = ['scheduling_status', 'contact_method', 'created_at']
    search_fields = ['candidate__name', 'coordinator__username']
    readonly_fields = ['created_at', 'updated_at']
    date_hierarchy = 'created_at'
    
    fieldsets = (
        ('기본 정보', {
            'fields': ('candidate', 'coordinator', 'scheduling_status')
        }),
        ('일정 정보', {
            'fields': ('preferred_dates', 'interviewer_availability', 'proposed_date', 'confirmed_date')
        }),
        ('연락 정보', {
            'fields': ('contact_method', 'contact_attempts', 'last_contact_date')
        }),
        ('응답 및 메모', {
            'fields': ('candidate_response', 'scheduling_notes'),
            'classes': ('collapse',)
        }),
        ('시간 정보', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )
