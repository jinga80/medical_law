from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.contrib.auth import authenticate
from django.db.models import Q
from .models import User, Organization, UserActivity, Hospital, HospitalBranch, PositionTemplate
from workflow.models import JobRequestTemplate
from .serializers import (
    UserSerializer, UserCreateSerializer, UserProfileSerializer,
    OrganizationSerializer, UserActivitySerializer
)
from django.http import JsonResponse
from django.views.decorators.http import require_GET


class UserViewSet(viewsets.ModelViewSet):
    """사용자 API 뷰셋"""
    serializer_class = UserSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        user = self.request.user
        if user.is_admin_user():
            return User.objects.all()
        elif user.is_hospital_user():
            return User.objects.filter(organization=user.organization)
        elif user.is_headhunting_user():
            return User.objects.filter(organization=user.organization)
        return User.objects.none()
    
    def get_serializer_class(self):
        if self.action == 'create':
            return UserCreateSerializer
        elif self.action in ['retrieve', 'update', 'partial_update']:
            return UserProfileSerializer
        return UserSerializer
    
    @action(detail=False, methods=['get'])
    def profile(self, request):
        """현재 사용자 프로필"""
        serializer = UserProfileSerializer(request.user)
        return Response(serializer.data)
    
    @action(detail=False, methods=['post'])
    def change_password(self, request):
        """비밀번호 변경"""
        old_password = request.data.get('old_password')
        new_password = request.data.get('new_password')
        
        if not request.user.check_password(old_password):
            return Response({'error': '현재 비밀번호가 올바르지 않습니다.'}, status=400)
        
        request.user.set_password(new_password)
        request.user.save()
        return Response({'status': 'password_changed'})
    
    @action(detail=False, methods=['get'])
    def activities(self, request):
        """사용자 활동 로그"""
        activities = UserActivity.objects.filter(user=request.user).order_by('-created_at')[:50]
        serializer = UserActivitySerializer(activities, many=True)
        return Response(serializer.data)


class OrganizationViewSet(viewsets.ReadOnlyModelViewSet):
    """기관 API 뷰셋 (읽기 전용)"""
    serializer_class = OrganizationSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        user = self.request.user
        if user.is_admin_user():
            return Organization.objects.all()
        elif user.is_hospital_user():
            return Organization.objects.filter(org_type__in=['hospital', 'headhunting'])
        elif user.is_headhunting_user():
            return Organization.objects.filter(org_type__in=['hospital', 'headhunting'])
        return Organization.objects.none()
    
    @action(detail=True, methods=['get'])
    def users(self, request, pk=None):
        """기관 소속 사용자 목록"""
        organization = self.get_object()
        users = organization.users.filter(is_active=True)
        serializer = UserSerializer(users, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['get'])
    def stats(self, request, pk=None):
        """기관 통계"""
        organization = self.get_object()
        stats = {
            'total_users': organization.users.count(),
            'active_users': organization.users.filter(is_active=True).count(),
            'user_roles': {}
        }
        
        # 역할별 사용자 수
        for role, _ in User.ROLE_CHOICES:
            count = organization.users.filter(role=role).count()
            if count > 0:
                stats['user_roles'][role] = count
        
        return Response(stats)


@require_GET
def hospital_list(request):
    hospitals = Hospital.objects.filter(is_active=True)
    data = [
        {'id': h.id, 'name': h.name, 'organization': h.organization.name}
        for h in hospitals
    ]
    return JsonResponse({'hospitals': data})

@require_GET
def hospital_branch_list(request, hospital_id):
    branches = HospitalBranch.objects.filter(hospital_id=hospital_id, is_active=True)
    data = [
        {'id': b.id, 'name': b.name}
        for b in branches
    ]
    return JsonResponse(data, safe=False)

@require_GET
def hospital_branch_detail(request, branch_id):
    try:
        b = HospitalBranch.objects.get(id=branch_id)
        data = {
            'id': b.id,
            'name': b.name,
            'address': b.address,
            'phone': b.phone,
            'manager_name': b.manager_name,
            'manager_phone': b.manager_phone,
            'manager_email': b.manager_email,
            'hospital': {
                'id': b.hospital.id,
                'name': b.hospital.name
            }
        }
        return JsonResponse(data)
    except HospitalBranch.DoesNotExist:
        return JsonResponse({'error': 'not found'}, status=404)

@require_GET
def position_template_list(request):
    positions = PositionTemplate.objects.filter(is_active=True)
    data = [
        {'id': p.id, 'name': p.name, 'department': p.department}
        for p in positions
    ]
    return JsonResponse(data, safe=False)

@require_GET
def position_template_detail(request, position_id):
    try:
        p = PositionTemplate.objects.get(id=position_id)
        data = {
            'id': p.id,
            'title': p.name,
            'department': p.department,
            'employment_type': p.employment_type,
            'salary_min': p.salary_min,
            'salary_max': p.salary_max,
            'required_experience': p.required_experience,
            'preferred_qualifications': p.preferred_qualifications,
            'job_description': p.job_description,
            'working_hours': p.working_hours,
            'working_location': p.working_location,
            'special_requirements': p.special_requirements,
            'recruitment_period': p.recruitment_period,
            'urgency_level': p.urgency_level,
        }
        return JsonResponse(data)
    except PositionTemplate.DoesNotExist:
        return JsonResponse({'error': 'not found'}, status=404)

@require_GET
def job_request_template_list(request):
    templates = JobRequestTemplate.objects.filter(is_active=True)
    data = [
        {'id': t.id, 'name': t.name, 'position_title': t.position_title}
        for t in templates
    ]
    return JsonResponse(data, safe=False)

@require_GET
def job_request_template_detail(request, template_id):
    try:
        t = JobRequestTemplate.objects.get(id=template_id)
        data = {
            'id': t.id,
            'title': t.position_title,
            'department': t.department,
            'employment_type': t.employment_type,
            'salary_min': t.salary_min,
            'salary_max': t.salary_max,
            'required_experience': t.required_experience,
            'preferred_qualifications': t.preferred_qualifications,
            'job_description': t.job_description,
            'working_hours': t.working_hours,
            'working_location': t.working_location,
            'special_requirements': t.special_requirements,
            'recruitment_period': t.recruitment_period,
            'urgency_level': t.urgency_level,
        }
        return JsonResponse(data)
    except JobRequestTemplate.DoesNotExist:
        return JsonResponse({'error': 'not found'}, status=404) 