from rest_framework import serializers
from .models import Candidate
from workflow.serializers import JobRequestSerializer
from accounts.serializers import UserSerializer


class CandidateSerializer(serializers.ModelSerializer):
    """후보자 시리얼라이저"""
    job_request = JobRequestSerializer(read_only=True)
    recommended_by = UserSerializer(read_only=True)
    recommended_by_organization = serializers.SerializerMethodField()
    
    class Meta:
        model = Candidate
        fields = [
            'id', 'name', 'email', 'phone', 'resume_file', 'cover_letter',
            'job_request', 'recommended_by', 'recommended_by_organization',
            'status', 'recommended_at', 'approved_at', 'rejected_at',
            'notes', 'created_at', 'updated_at'
        ]
        read_only_fields = ['recommended_by', 'recommended_at', 'approved_at', 'rejected_at', 'created_at', 'updated_at']
    
    def get_recommended_by_organization(self, obj):
        """추천 기관 정보"""
        if obj.recommended_by:
            return {
                'id': obj.recommended_by.organization.id,
                'name': obj.recommended_by.organization.name,
                'org_type': obj.recommended_by.organization.org_type
            }
        return None


class CandidateCreateSerializer(serializers.ModelSerializer):
    """후보자 생성용 시리얼라이저"""
    
    class Meta:
        model = Candidate
        fields = [
            'name', 'email', 'phone', 'resume_file', 'cover_letter',
            'job_request', 'notes'
        ]
    
    def create(self, validated_data):
        validated_data['recommended_by'] = self.context['request'].user
        return super().create(validated_data)


class CandidateUpdateSerializer(serializers.ModelSerializer):
    """후보자 업데이트용 시리얼라이저"""
    
    class Meta:
        model = Candidate
        fields = ['status', 'notes']
    
    def validate_status(self, value):
        """상태 변경 유효성 검사"""
        instance = self.instance
        if instance and instance.status == 'hired' and value != 'hired':
            raise serializers.ValidationError("채용 확정된 후보자는 상태를 변경할 수 없습니다.")
        return value 