from rest_framework import serializers
from .models import Interview, InterviewEvaluation, DocumentScreening, InterviewScheduling
from candidates.serializers import CandidateSerializer
from accounts.serializers import UserSerializer


class InterviewSerializer(serializers.ModelSerializer):
    """면접 시리얼라이저"""
    candidate = CandidateSerializer(read_only=True)
    interviewer = UserSerializer(read_only=True)
    evaluations = serializers.SerializerMethodField()
    
    class Meta:
        model = Interview
        fields = [
            'id', 'candidate', 'interviewer', 'scheduled_date', 'location',
            'interview_type', 'status', 'notes', 'completed_at', 'created_at',
            'updated_at', 'evaluations'
        ]
        read_only_fields = ['completed_at', 'created_at', 'updated_at']
    
    def get_evaluations(self, obj):
        """면접 평가 목록"""
        evaluations = obj.evaluations.all()
        return InterviewEvaluationSerializer(evaluations, many=True).data


class InterviewCreateSerializer(serializers.ModelSerializer):
    """면접 생성용 시리얼라이저"""
    
    class Meta:
        model = Interview
        fields = [
            'candidate', 'interviewer', 'scheduled_date', 'location',
            'interview_type', 'notes'
        ]
    
    def validate_scheduled_date(self, value):
        """면접 일정 유효성 검사"""
        from django.utils import timezone
        if value <= timezone.now():
            raise serializers.ValidationError("면접 일정은 현재 시간보다 이후여야 합니다.")
        return value


class InterviewEvaluationSerializer(serializers.ModelSerializer):
    """면접 평가 시리얼라이저"""
    interview = InterviewSerializer(read_only=True)
    evaluator = UserSerializer(read_only=True)
    
    class Meta:
        model = InterviewEvaluation
        fields = [
            'id', 'interview', 'evaluator', 'technical_skills', 'communication',
            'problem_solving', 'teamwork', 'leadership', 'overall_rating',
            'strengths', 'weaknesses', 'recommendation', 'comments',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['evaluator', 'created_at', 'updated_at']


class InterviewEvaluationCreateSerializer(serializers.ModelSerializer):
    """면접 평가 생성용 시리얼라이저"""
    
    class Meta:
        model = InterviewEvaluation
        fields = [
            'interview', 'technical_skills', 'communication', 'problem_solving',
            'teamwork', 'leadership', 'overall_rating', 'strengths',
            'weaknesses', 'recommendation', 'comments'
        ]
    
    def validate_overall_rating(self, value):
        """전체 평가 점수 유효성 검사"""
        if value < 1 or value > 5:
            raise serializers.ValidationError("평가 점수는 1-5 사이여야 합니다.")
        return value
    
    def validate(self, data):
        """평가 데이터 유효성 검사"""
        # 개별 항목 점수 검사
        score_fields = ['technical_skills', 'communication', 'problem_solving', 'teamwork', 'leadership']
        for field in score_fields:
            if data.get(field) and (data[field] < 1 or data[field] > 5):
                raise serializers.ValidationError(f"{field} 점수는 1-5 사이여야 합니다.")
        return data 


class DocumentScreeningSerializer(serializers.ModelSerializer):
    """서류 심사 시리얼라이저"""
    candidate = CandidateSerializer(read_only=True)
    screener = UserSerializer(read_only=True)
    score_percentage = serializers.SerializerMethodField()
    score_level = serializers.SerializerMethodField()
    
    class Meta:
        model = DocumentScreening
        fields = [
            'id', 'candidate', 'screener', 'screening_status',
            'resume_quality_score', 'experience_match_score', 'education_score',
            'skill_match_score', 'overall_impression_score', 'total_score',
            'passing_score', 'passed', 'strengths', 'weaknesses',
            'improvement_suggestions', 'screening_notes', 'additional_info_requested',
            'info_deadline', 'screening_started_at', 'screening_completed_at',
            'created_at', 'updated_at', 'score_percentage', 'score_level'
        ]
        read_only_fields = ['total_score', 'passed', 'created_at', 'updated_at']
    
    def get_score_percentage(self, obj):
        """점수 백분율"""
        return obj.get_score_percentage()
    
    def get_score_level(self, obj):
        """점수 수준"""
        return obj.get_score_level()


class DocumentScreeningCreateSerializer(serializers.ModelSerializer):
    """서류 심사 생성용 시리얼라이저"""
    
    class Meta:
        model = DocumentScreening
        fields = [
            'candidate', 'screening_status', 'resume_quality_score',
            'experience_match_score', 'education_score', 'skill_match_score',
            'overall_impression_score', 'passing_score', 'strengths',
            'weaknesses', 'improvement_suggestions', 'screening_notes',
            'additional_info_requested', 'info_deadline'
        ]
    
    def create(self, validated_data):
        validated_data['screener'] = self.context['request'].user
        return super().create(validated_data)


class InterviewSchedulingSerializer(serializers.ModelSerializer):
    """면접 일정 조율 시리얼라이저"""
    candidate = CandidateSerializer(read_only=True)
    coordinator = UserSerializer(read_only=True)
    is_urgent = serializers.SerializerMethodField()
    
    class Meta:
        model = InterviewScheduling
        fields = [
            'id', 'candidate', 'coordinator', 'preferred_dates',
            'interviewer_availability', 'proposed_date', 'confirmed_date',
            'scheduling_status', 'contact_method', 'contact_attempts',
            'last_contact_date', 'candidate_response', 'scheduling_notes',
            'created_at', 'updated_at', 'is_urgent'
        ]
        read_only_fields = ['created_at', 'updated_at']
    
    def get_is_urgent(self, obj):
        """긴급 여부"""
        return obj.is_urgent()


class InterviewSchedulingCreateSerializer(serializers.ModelSerializer):
    """면접 일정 조율 생성용 시리얼라이저"""
    
    class Meta:
        model = InterviewScheduling
        fields = [
            'candidate', 'preferred_dates', 'interviewer_availability',
            'contact_method', 'scheduling_notes'
        ]
    
    def create(self, validated_data):
        validated_data['coordinator'] = self.context['request'].user
        return super().create(validated_data) 