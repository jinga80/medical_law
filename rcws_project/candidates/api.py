from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.db.models import Q
from .models import Candidate
from .serializers import CandidateSerializer, CandidateCreateSerializer
from notifications.utils import send_notification


class CandidateViewSet(viewsets.ModelViewSet):
    """후보자 API 뷰셋"""
    serializer_class = CandidateSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        user = self.request.user
        if user.is_admin_user():
            return Candidate.objects.all()
        elif user.is_hospital_user():
            return Candidate.objects.filter(
                job_request__requester__organization=user.organization
            )
        elif user.is_headhunting_user():
            return Candidate.objects.filter(
                recommended_by__organization=user.organization
            )
        return Candidate.objects.none()
    
    def get_serializer_class(self):
        if self.action == 'create':
            return CandidateCreateSerializer
        return CandidateSerializer
    
    def perform_create(self, serializer):
        candidate = serializer.save(recommended_by=self.request.user)
        # 병원 사용자에게 알림 발송
        hospital_users = candidate.job_request.requester.organization.users.filter(
            role__in=['hospital_hr', 'hospital_manager']
        )
        for user in hospital_users:
            send_notification(
                recipient=user,
                notification_type='new_candidate',
                title=f'새로운 후보자 추천: {candidate.name}',
                message=f'{candidate.recommended_by.organization.name}에서 {candidate.name} 후보자를 추천했습니다.',
                related_object_id=candidate.id,
                related_object_type='Candidate'
            )
    
    @action(detail=True, methods=['post'])
    def approve(self, request, pk=None):
        """후보자 승인"""
        candidate = self.get_object()
        if candidate.status == 'recommended':
            candidate.status = 'approved'
            candidate.save()
            return Response({'status': 'approved'})
        return Response({'error': '승인할 수 없는 상태입니다.'}, status=400)
    
    @action(detail=True, methods=['post'])
    def reject(self, request, pk=None):
        """후보자 거절"""
        candidate = self.get_object()
        if candidate.status in ['recommended', 'document_review']:
            candidate.status = 'rejected'
            candidate.save()
            return Response({'status': 'rejected'})
        return Response({'error': '거절할 수 없는 상태입니다.'}, status=400)
    
    @action(detail=False, methods=['get'])
    def my_recommendations(self, request):
        """내가 추천한 후보자 목록"""
        candidates = self.get_queryset().filter(recommended_by=request.user)
        serializer = self.get_serializer(candidates, many=True)
        return Response(serializer.data) 