from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.db.models import Count, Avg, Q
from django.utils import timezone
from datetime import timedelta
from workflow.models import JobRequest, WorkflowStep
from candidates.models import Candidate
from evaluations.models import Interview, InterviewEvaluation
from accounts.models import Organization, User


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def performance_report(request):
    """성과 보고서 API"""
    user = request.user
    start_date = request.GET.get('start_date')
    end_date = request.GET.get('end_date')
    
    if not start_date:
        start_date = timezone.now().replace(day=1)
    if not end_date:
        end_date = timezone.now()
    
    if user.organization.org_type == 'headhunting':
        # 헤드헌팅 성과 보고서
        total_recommendations = Candidate.objects.filter(
            recommended_by__organization=user.organization,
            created_at__range=[start_date, end_date]
        ).count()
        
        successful_hires = Candidate.objects.filter(
            recommended_by__organization=user.organization,
            status='hired',
            created_at__range=[start_date, end_date]
        ).count()
        
        success_rate = (successful_hires / total_recommendations * 100) if total_recommendations > 0 else 0
        
        performance_data = {
            'total_recommendations': total_recommendations,
            'successful_hires': successful_hires,
            'success_rate': round(success_rate, 2),
            'avg_response_time': calculate_avg_response_time(user.organization, start_date, end_date)
        }
    else:
        # 병원/관리자 성과 보고서
        performance_data = {
            'total_requests': JobRequest.objects.filter(
                created_at__range=[start_date, end_date]
            ).count(),
            'completed_requests': JobRequest.objects.filter(
                status='completed',
                completed_at__range=[start_date, end_date]
            ).count(),
            'avg_completion_time': calculate_avg_completion_time(start_date, end_date)
        }
    
    return Response(performance_data)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def workflow_analytics(request):
    """워크플로우 분석 API"""
    user = request.user
    
    # 단계별 진행 상황
    step_stats = {}
    # 실제 데이터베이스에서 사용 중인 단계명들을 가져옴
    step_names = WorkflowStep.objects.values_list('name', flat=True).distinct()
    
    for step_name in step_names:
        step_stats[step_name] = {
            'pending': WorkflowStep.objects.filter(name=step_name, status='pending').count(),
            'in_progress': WorkflowStep.objects.filter(name=step_name, status='in_progress').count(),
            'completed': WorkflowStep.objects.filter(name=step_name, status='completed').count()
        }
    
    # 병목 구간 분석
    bottleneck_analysis = get_bottleneck_analysis()
    
    analytics_data = {
        'step_statistics': step_stats,
        'bottleneck_analysis': bottleneck_analysis,
        'total_active_workflows': JobRequest.objects.filter(
            status__in=['submitted', 'accepted', 'in_progress']
        ).count()
    }
    
    return Response(analytics_data)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def candidate_stats(request):
    """후보자 통계 API"""
    user = request.user
    
    # 상태별 후보자 수
    status_stats = {}
    for status, _ in Candidate.STATUS_CHOICES:
        if user.is_admin_user():
            count = Candidate.objects.filter(status=status).count()
        elif user.is_hospital_user():
            count = Candidate.objects.filter(
                job_request__requester__organization=user.organization,
                status=status
            ).count()
        elif user.is_headhunting_user():
            count = Candidate.objects.filter(
                recommended_by__organization=user.organization,
                status=status
            ).count()
        else:
            count = 0
        
        if count > 0:
            status_stats[status] = count
    
    # 기관별 추천 현황
    org_recommendations = {}
    if user.is_admin_user():
        for org in Organization.objects.filter(org_type='headhunting'):
            count = Candidate.objects.filter(
                recommended_by__organization=org
            ).count()
            org_recommendations[org.name] = count
    
    candidate_data = {
        'status_statistics': status_stats,
        'organization_recommendations': org_recommendations,
        'total_candidates': Candidate.objects.count() if user.is_admin_user() else None
    }
    
    return Response(candidate_data)


def calculate_avg_response_time(organization, start_date, end_date):
    """평균 응답 시간 계산"""
    job_requests = JobRequest.objects.filter(
        status__in=['accepted', 'in_progress', 'completed'],
        accepted_at__range=[start_date, end_date]
    )
    
    total_time = 0
    count = 0
    
    for request in job_requests:
        if request.submitted_at and request.accepted_at:
            response_time = (request.accepted_at - request.submitted_at).total_seconds() / 3600  # 시간 단위
            total_time += response_time
            count += 1
    
    return round(total_time / count, 2) if count > 0 else 0


def calculate_avg_completion_time(start_date, end_date):
    """평균 완료 시간 계산"""
    completed_requests = JobRequest.objects.filter(
        status='completed',
        completed_at__range=[start_date, end_date]
    )
    
    total_time = 0
    count = 0
    
    for request in completed_requests:
        if request.submitted_at and request.completed_at:
            completion_time = (request.completed_at - request.submitted_at).days
            total_time += completion_time
            count += 1
    
    return round(total_time / count, 1) if count > 0 else 0


def get_bottleneck_analysis():
    """병목 구간 분석"""
    bottlenecks = []
    
    # 실제 데이터베이스에서 사용 중인 단계명들을 가져옴
    step_names = WorkflowStep.objects.values_list('name', flat=True).distinct()
    
    for step_name in step_names:
        pending_count = WorkflowStep.objects.filter(
            name=step_name, 
            status='pending'
        ).count()
        
        if pending_count > 5:  # 5개 이상 대기 중이면 병목으로 간주
            bottlenecks.append({
                'step': step_name,
                'pending_count': pending_count,
                'avg_wait_time': calculate_avg_wait_time(step_name)
            })
    
    return sorted(bottlenecks, key=lambda x: x['pending_count'], reverse=True)


def calculate_avg_wait_time(step_name):
    """단계별 평균 대기 시간"""
    steps = WorkflowStep.objects.filter(
        name=step_name,
        status__in=['in_progress', 'completed'],
        started_at__isnull=False
    )
    
    total_wait_time = 0
    count = 0
    
    for step in steps:
        if step.started_at:
            # 해당 단계의 이전 단계 완료 시간부터 시작 시간까지
            prev_step = WorkflowStep.objects.filter(
                workflow=step.workflow,
                order__lt=step.order,
                status='completed'
            ).order_by('-order').first()
            
            if prev_step and prev_step.completed_at:
                wait_time = (step.started_at - prev_step.completed_at).total_seconds() / 3600
                total_wait_time += wait_time
                count += 1
    
    return round(total_wait_time / count, 2) if count > 0 else 0 