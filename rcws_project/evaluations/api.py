from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.utils import timezone
from .models import Interview, InterviewEvaluation
from .serializers import InterviewSerializer, InterviewEvaluationSerializer
from notifications.utils import send_notification


class InterviewViewSet(viewsets.ModelViewSet):
    """면접 API 뷰셋"""
    serializer_class = InterviewSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        user = self.request.user
        if user.is_admin_user():
            return Interview.objects.all()
        elif user.is_hospital_user():
            return Interview.objects.filter(
                candidate__job_request__requester__organization=user.organization
            )
        elif user.is_headhunting_user():
            return Interview.objects.filter(
                candidate__recommended_by__organization=user.organization
            )
        return Interview.objects.none()
    
    def perform_create(self, serializer):
        interview = serializer.save()
        # 면접자와 후보자에게 알림 발송
        send_notification(
            recipient=interview.interviewer,
            notification_type='interview_scheduled',
            title=f'면접 일정: {interview.candidate.name}',
            message=f'{interview.scheduled_date.strftime("%Y-%m-%d %H:%M")}에 {interview.candidate.name} 후보자 면접이 예정되었습니다.',
            related_object_id=interview.id,
            related_object_type='Interview'
        )
    
    @action(detail=True, methods=['post'])
    def complete(self, request, pk=None):
        """면접 완료"""
        interview = self.get_object()
        if interview.status == 'scheduled':
            interview.status = 'completed'
            interview.completed_at = timezone.now()
            interview.save()
            return Response({'status': 'completed'})
        return Response({'error': '완료할 수 없는 상태입니다.'}, status=400)
    
    @action(detail=True, methods=['post'])
    def cancel(self, request, pk=None):
        """면접 취소"""
        interview = self.get_object()
        if interview.status == 'scheduled':
            interview.status = 'cancelled'
            interview.save()
            return Response({'status': 'cancelled'})
        return Response({'error': '취소할 수 없는 상태입니다.'}, status=400)


class InterviewEvaluationViewSet(viewsets.ModelViewSet):
    """면접 평가 API 뷰셋"""
    serializer_class = InterviewEvaluationSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        user = self.request.user
        if user.is_admin_user():
            return InterviewEvaluation.objects.all()
        elif user.is_hospital_user():
            return InterviewEvaluation.objects.filter(
                interview__candidate__job_request__requester__organization=user.organization
            )
        elif user.is_headhunting_user():
            return InterviewEvaluation.objects.filter(
                interview__candidate__recommended_by__organization=user.organization
            )
        return InterviewEvaluation.objects.none()
    
    def perform_create(self, serializer):
        evaluation = serializer.save(evaluator=self.request.user)
        # 평가 완료 시 후보자 상태 업데이트
        if evaluation.overall_rating >= 4:  # 4점 이상이면 통과
            evaluation.interview.candidate.status = 'interview_passed'
            evaluation.interview.candidate.save()
        else:
            evaluation.interview.candidate.status = 'interview_failed'
            evaluation.interview.candidate.save() 