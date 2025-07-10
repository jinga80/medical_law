from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.db.models import Q
from django.utils import timezone
from .models import JobRequest, WorkflowStep
from .serializers import JobRequestSerializer, WorkflowStepSerializer
from notifications.utils import send_notification
from accounts.models import User


class JobRequestViewSet(viewsets.ModelViewSet):
    """채용 요청 API 뷰셋"""
    serializer_class = JobRequestSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        user = self.request.user
        if user.is_admin_user():
            return JobRequest.objects.all()
        elif user.is_hospital_user():
            return JobRequest.objects.filter(requester__organization=user.organization)
        elif user.is_headhunting_user():
            return JobRequest.objects.filter(status__in=['submitted', 'accepted', 'in_progress'])
        return JobRequest.objects.none()
    
    def perform_create(self, serializer):
        job_request = serializer.save(requester=self.request.user)
        # 헤드헌팅 기관에 알림 발송
        headhunting_users = User.objects.filter(
            organization__org_type='headhunting',
            role__in=['hh_ceo', 'hh_manager']
        )
        for user in headhunting_users:
            send_notification(
                recipient=user,
                notification_type='new_job_request',
                title=f'새로운 채용 요청: {job_request.position_title}',
                message=f'{job_request.requester.organization.name}에서 {job_request.position_title} 포지션 채용을 요청했습니다.',
                related_object_id=job_request.id,
                related_object_type='JobRequest'
            )
    
    @action(detail=True, methods=['post'])
    def submit(self, request, pk=None):
        """채용 요청 제출"""
        job_request = self.get_object()
        if job_request.status == 'draft':
            job_request.status = 'submitted'
            job_request.submitted_at = timezone.now()
            job_request.save()
            return Response({'status': 'submitted'})
        return Response({'error': '이미 제출된 요청입니다.'}, status=400)
    
    @action(detail=True, methods=['post'])
    def accept(self, request, pk=None):
        """채용 요청 접수"""
        job_request = self.get_object()
        if job_request.status == 'submitted':
            job_request.status = 'accepted'
            job_request.accepted_at = timezone.now()
            job_request.save()
            return Response({'status': 'accepted'})
        return Response({'error': '접수할 수 없는 상태입니다.'}, status=400)


class WorkflowStepViewSet(viewsets.ModelViewSet):
    """워크플로우 단계 API 뷰셋"""
    serializer_class = WorkflowStepSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        user = self.request.user
        if user.is_admin_user():
            return WorkflowStep.objects.all()
        return WorkflowStep.objects.filter(
            Q(assigned_to=user) | 
            Q(job_request__requester__organization=user.organization)
        )
    
    @action(detail=True, methods=['post'])
    def start(self, request, pk=None):
        """워크플로우 단계 시작"""
        step = self.get_object()
        if step.status == 'pending':
            step.status = 'in_progress'
            step.started_at = timezone.now()
            step.assigned_to = request.user
            step.save()
            return Response({'status': 'started'})
        return Response({'error': '시작할 수 없는 상태입니다.'}, status=400)
    
    @action(detail=True, methods=['post'])
    def complete(self, request, pk=None):
        """워크플로우 단계 완료"""
        step = self.get_object()
        if step.status == 'in_progress':
            step.status = 'completed'
            step.completed_at = timezone.now()
            step.save()
            return Response({'status': 'completed'})
        return Response({'error': '완료할 수 없는 상태입니다.'}, status=400) 