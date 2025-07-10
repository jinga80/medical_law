from rest_framework import serializers
from .models import User, Organization, UserActivity


class OrganizationSerializer(serializers.ModelSerializer):
    """기관 시리얼라이저"""
    
    class Meta:
        model = Organization
        fields = [
            'id', 'name', 'org_type', 'address', 'phone', 'email',
            'description', 'is_active', 'created_at', 'updated_at'
        ]
        read_only_fields = ['created_at', 'updated_at']


class UserSerializer(serializers.ModelSerializer):
    """사용자 시리얼라이저"""
    organization = OrganizationSerializer(read_only=True)
    organization_id = serializers.IntegerField(write_only=True, required=False)
    full_name = serializers.SerializerMethodField()
    
    class Meta:
        model = User
        fields = [
            'id', 'username', 'email', 'first_name', 'last_name', 'full_name',
            'organization', 'organization_id', 'role', 'phone', 'department',
            'position', 'employee_id', 'is_active_user', 'profile_image',
            'last_activity', 'date_joined'
        ]
        read_only_fields = ['last_activity', 'date_joined']
        extra_kwargs = {
            'password': {'write_only': True}
        }
    
    def get_full_name(self, obj):
        """전체 이름"""
        return obj.get_full_name()
    
    def create(self, validated_data):
        """사용자 생성 시 비밀번호 해싱"""
        password = validated_data.pop('password', None)
        user = super().create(validated_data)
        if password:
            user.set_password(password)
            user.save()
        return user


class UserCreateSerializer(serializers.ModelSerializer):
    """사용자 생성용 시리얼라이저"""
    password = serializers.CharField(write_only=True)
    password_confirm = serializers.CharField(write_only=True)
    
    class Meta:
        model = User
        fields = [
            'username', 'email', 'first_name', 'last_name', 'password',
            'password_confirm', 'organization', 'role', 'phone', 'department',
            'position', 'employee_id'
        ]
    
    def validate(self, data):
        """비밀번호 확인"""
        if data['password'] != data['password_confirm']:
            raise serializers.ValidationError("비밀번호가 일치하지 않습니다.")
        return data
    
    def create(self, validated_data):
        validated_data.pop('password_confirm')
        password = validated_data.pop('password')
        user = User.objects.create(**validated_data)
        user.set_password(password)
        user.save()
        return user


class UserActivitySerializer(serializers.ModelSerializer):
    """사용자 활동 시리얼라이저"""
    user = UserSerializer(read_only=True)
    
    class Meta:
        model = UserActivity
        fields = [
            'id', 'user', 'activity_type', 'description', 'ip_address',
            'user_agent', 'related_object_id', 'related_object_type',
            'created_at'
        ]
        read_only_fields = ['created_at']


class UserProfileSerializer(serializers.ModelSerializer):
    """사용자 프로필 시리얼라이저"""
    organization = OrganizationSerializer(read_only=True)
    full_name = serializers.SerializerMethodField()
    role_display = serializers.SerializerMethodField()
    
    class Meta:
        model = User
        fields = [
            'id', 'username', 'email', 'first_name', 'last_name', 'full_name',
            'organization', 'role', 'role_display', 'phone', 'department',
            'position', 'employee_id', 'profile_image', 'last_activity'
        ]
        read_only_fields = ['username', 'last_activity']
    
    def get_full_name(self, obj):
        return obj.get_full_name()
    
    def get_role_display(self, obj):
        return obj.get_role_display() 