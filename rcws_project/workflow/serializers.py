from rest_framework import serializers
from .models import JobRequest, WorkflowStep, WorkflowTemplate, JobPosting, JobApplication, WorkflowProgress
from accounts.serializers import UserSerializer, OrganizationSerializer


class JobRequestSerializer(serializers.ModelSerializer):
    """채용 요청 시리얼라이저"""
    requester = UserSerializer(read_only=True)
    requester_organization = OrganizationSerializer(source='requester.organization', read_only=True)
    workflow_steps = serializers.SerializerMethodField()
    duration_days = serializers.SerializerMethodField()
    
    class Meta:
        model = JobRequest
        fields = [
            'id', 'request_id', 'requester', 'requester_organization',
            'position_title', 'department', 'employment_type',
            'salary_min', 'salary_max', 'required_experience',
            'preferred_qualifications', 'job_description',
            'working_hours', 'working_location', 'urgency_level',
            'status', 'submitted_at', 'accepted_at', 'completed_at',
            'created_at', 'updated_at', 'workflow_steps', 'duration_days'
        ]
        read_only_fields = ['request_id', 'requester', 'created_at', 'updated_at']
    
    def get_workflow_steps(self, obj):
        """워크플로우 단계 정보"""
        steps = obj.workflow_steps.all()
        return WorkflowStepSerializer(steps, many=True).data
    
    def get_duration_days(self, obj):
        """소요 일수"""
        return obj.get_duration_days()


class WorkflowStepSerializer(serializers.ModelSerializer):
    """워크플로우 단계 시리얼라이저"""
    assigned_to = UserSerializer(read_only=True)
    duration_hours = serializers.SerializerMethodField()
    is_overdue = serializers.SerializerMethodField()
    
    class Meta:
        model = WorkflowStep
        fields = [
            'id', 'job_request', 'step_name', 'status', 'assigned_to',
            'started_at', 'completed_at', 'due_date', 'notes', 'feedback',
            'created_at', 'updated_at', 'duration_hours', 'is_overdue'
        ]
        read_only_fields = ['created_at', 'updated_at']
    
    def get_duration_hours(self, obj):
        """소요 시간 (시간 단위)"""
        return obj.get_duration_hours()
    
    def get_is_overdue(self, obj):
        """마감일 초과 여부"""
        return obj.is_overdue()


class WorkflowTemplateSerializer(serializers.ModelSerializer):
    """워크플로우 템플릿 시리얼라이저"""
    
    class Meta:
        model = WorkflowTemplate
        fields = [
            'id', 'name', 'description', 'is_default', 'is_active',
            'steps_config', 'created_at', 'updated_at'
        ]
        read_only_fields = ['created_at', 'updated_at']


class JobRequestCreateSerializer(serializers.ModelSerializer):
    """채용 요청 생성용 시리얼라이저"""
    
    class Meta:
        model = JobRequest
        fields = [
            'position_title', 'department', 'employment_type',
            'salary_min', 'salary_max', 'required_experience',
            'preferred_qualifications', 'job_description',
            'working_hours', 'working_location', 'urgency_level'
        ]
    
    def create(self, validated_data):
        validated_data['requester'] = self.context['request'].user
        return super().create(validated_data)


class WorkflowStepUpdateSerializer(serializers.ModelSerializer):
    """워크플로우 단계 업데이트용 시리얼라이저"""
    
    class Meta:
        model = WorkflowStep
        fields = ['status', 'notes', 'feedback', 'due_date']
    
    def validate_status(self, value):
        """상태 변경 유효성 검사"""
        instance = self.instance
        if instance and instance.status == 'completed' and value != 'completed':
            raise serializers.ValidationError("완료된 단계는 상태를 변경할 수 없습니다.")
        return value 


class JobPostingSerializer(serializers.ModelSerializer):
    """구인 공고 시리얼라이저"""
    job_request = JobRequestSerializer(read_only=True)
    created_by = UserSerializer(read_only=True)
    applications_count = serializers.SerializerMethodField()
    days_remaining = serializers.SerializerMethodField()
    
    class Meta:
        model = JobPosting
        fields = [
            'id', 'posting_id', 'job_request', 'created_by', 'title', 'summary',
            'detailed_description', 'requirements', 'preferred_qualifications', 'benefits',
            'posting_date', 'closing_date', 'application_deadline', 'status',
            'is_featured', 'view_count', 'application_count', 'applications_count',
            'published_at', 'created_at', 'updated_at', 'days_remaining'
        ]
        read_only_fields = ['posting_id', 'created_by', 'view_count', 'application_count', 'created_at', 'updated_at']
    
    def get_applications_count(self, obj):
        """지원자 수"""
        return obj.applications.count()
    
    def get_days_remaining(self, obj):
        """마감까지 남은 일수"""
        return obj.get_days_remaining()


class JobPostingCreateSerializer(serializers.ModelSerializer):
    """구인 공고 생성용 시리얼라이저"""
    
    class Meta:
        model = JobPosting
        fields = [
            'job_request', 'title', 'summary', 'detailed_description',
            'requirements', 'preferred_qualifications', 'benefits',
            'posting_date', 'closing_date', 'application_deadline',
            'status', 'is_featured'
        ]
    
    def create(self, validated_data):
        validated_data['created_by'] = self.context['request'].user
        return super().create(validated_data)


class JobApplicationSerializer(serializers.ModelSerializer):
    """구인 공고 지원 시리얼라이저"""
    job_posting = JobPostingSerializer(read_only=True)
    applicant = UserSerializer(read_only=True)
    
    class Meta:
        model = JobApplication
        fields = [
            'id', 'application_id', 'job_posting', 'applicant', 'cover_letter',
            'resume_file', 'portfolio_file', 'status', 'submitted_at',
            'reviewed_at', 'updated_at'
        ]
        read_only_fields = ['application_id', 'applicant', 'submitted_at', 'updated_at']


class JobApplicationCreateSerializer(serializers.ModelSerializer):
    """구인 공고 지원 생성용 시리얼라이저"""
    
    class Meta:
        model = JobApplication
        fields = [
            'job_posting', 'cover_letter', 'resume_file', 'portfolio_file'
        ]
    
    def create(self, validated_data):
        validated_data['applicant'] = self.context['request'].user
        return super().create(validated_data)


class WorkflowProgressSerializer(serializers.ModelSerializer):
    """워크플로우 진행 상황 시리얼라이저"""
    job_request = JobRequestSerializer(read_only=True)
    days_remaining = serializers.SerializerMethodField()
    days_overdue = serializers.SerializerMethodField()
    
    class Meta:
        model = WorkflowProgress
        fields = [
            'id', 'job_request', 'current_step', 'step_completion_rate',
            'overall_progress', 'estimated_completion_date', 'actual_completion_date',
            'target_completion_date', 'bottlenecks', 'total_candidates',
            'screened_candidates', 'interviewed_candidates', 'hired_candidates',
            'step_start_times', 'step_end_times', 'step_durations',
            'is_on_track', 'is_completed', 'created_at', 'updated_at',
            'days_remaining', 'days_overdue'
        ]
        read_only_fields = ['overall_progress', 'created_at', 'updated_at']
    
    def get_days_remaining(self, obj):
        """목표 완료일까지 남은 일수"""
        return obj.get_days_remaining()
    
    def get_days_overdue(self, obj):
        """지연 일수"""
        return obj.get_days_overdue() 