from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.db.models import Count, Q, Avg, F, ExpressionWrapper, DurationField
from django.utils import timezone
from datetime import timedelta
from workflow.models import JobRequest, WorkflowStep, Workflow, JobPosting, WorkflowProgress, WorkflowActionLog
from candidates.models import Candidate, CandidateReview, CandidateHistory
from evaluations.models import InterviewEvaluation, Interview, DocumentReview
from notifications.models import Notification
from accounts.models import UserActivity, Organization, User
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def dashboard_stats(request):
    """대시보드 통계 API"""
    user = request.user
    
    if user.organization.org_type == 'hospital':
        # 병원 대시보드 통계
        this_month = timezone.now().replace(day=1)
        stats = {
            'new_requests': JobRequest.objects.filter(
                requester__organization=user.organization,
                created_at__gte=this_month
            ).count(),
            'completed_hires': JobRequest.objects.filter(
                requester__organization=user.organization,
                status='completed',
                completed_at__gte=this_month
            ).count(),
            'in_progress': JobRequest.objects.filter(
                requester__organization=user.organization,
                status__in=['submitted', 'accepted', 'in_progress']
            ).count(),
            'pending_reviews': Candidate.objects.filter(
                job_request__requester__organization=user.organization,
                status='document_review'
            ).count()
        }
    elif user.organization.org_type == 'headhunting':
        # 헤드헌팅 대시보드 통계
        this_month = timezone.now().replace(day=1)
        stats = {
            'new_requests': JobRequest.objects.filter(
                status='submitted',
                created_at__gte=this_month
            ).count(),
            'recommendations': Candidate.objects.filter(
                recommended_by__organization=user.organization,
                created_at__gte=this_month
            ).count(),
            'successful_hires': Candidate.objects.filter(
                recommended_by__organization=user.organization,
                status='hired',
                created_at__gte=this_month
            ).count(),
            'in_progress': JobRequest.objects.filter(
                status__in=['accepted', 'in_progress']
            ).count()
        }
    else:
        # 관리자 대시보드 통계
        this_month = timezone.now().replace(day=1)
        stats = {
            'total_organizations': Organization.objects.count(),
            'total_users': User.objects.count(),
            'active_workflows': JobRequest.objects.filter(
                status__in=['submitted', 'accepted', 'in_progress']
            ).count(),
            'completed_this_month': JobRequest.objects.filter(
                status='completed',
                completed_at__gte=this_month
            ).count()
        }
    
    return Response(stats)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def recent_activities(request):
    """최근 활동 API"""
    user = request.user
    
    if user.organization.org_type == 'hospital':
        # 병원 사용자 최근 활동
        activities = UserActivity.objects.filter(
            user__organization=user.organization
        ).order_by('-created_at')[:20]
    elif user.organization.org_type == 'headhunting':
        # 헤드헌팅 사용자 최근 활동
        activities = UserActivity.objects.filter(
            user__organization=user.organization
        ).order_by('-created_at')[:20]
    else:
        # 관리자 전체 활동
        activities = UserActivity.objects.all().order_by('-created_at')[:20]
    
    from accounts.serializers import UserActivitySerializer
    serializer = UserActivitySerializer(activities, many=True)
    return Response(serializer.data)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def pending_tasks(request):
    """대기중인 업무 API"""
    user = request.user
    
    if user.organization.org_type == 'hospital':
        # 병원 사용자 대기 업무
        pending_tasks = WorkflowStep.objects.filter(
            job_request__requester__organization=user.organization,
            status='pending'
        )
    elif user.organization.org_type == 'headhunting':
        # 헤드헌팅 사용자 대기 업무
        pending_tasks = WorkflowStep.objects.filter(
            assigned_to__organization=user.organization,
            status='pending'
        )
    else:
        # 관리자 전체 대기 업무
        pending_tasks = WorkflowStep.objects.filter(status='pending')
    
    from workflow.serializers import WorkflowStepSerializer
    serializer = WorkflowStepSerializer(pending_tasks, many=True)
    return Response(serializer.data)


@login_required
def dashboard_stats_api(request):
    """대시보드 통계 API"""
    user = request.user
    
    # 기본 통계
    stats = {
        'total_workflows': Workflow.objects.count(),
        'active_workflows': Workflow.objects.filter(status='in_progress').count(),
        'completed_workflows': Workflow.objects.filter(status='completed').count(),
        'total_candidates': Candidate.objects.count(),
        'new_notifications': Notification.objects.filter(is_read=False).count(),
        'job_requests_count': JobRequest.objects.count(),
        'job_postings_count': JobPosting.objects.filter(status='published').count(),
    }
    
    # 권한별 필터링
    if user.is_hospital_user():
        org_filter = Q(requester__organization=user.organization)
        stats.update({
            'my_job_requests': JobRequest.objects.filter(org_filter).count(),
            'my_candidates': Candidate.objects.filter(job_request__requester__organization=user.organization).count(),
            'my_active_workflows': Workflow.objects.filter(org_filter, status='in_progress').count(),
        })
    elif user.is_headhunting_user():
        org_filter = Q(recommended_by__organization=user.organization)
        stats.update({
            'my_recommended_candidates': Candidate.objects.filter(org_filter).count(),
            'my_active_assignments': JobRequest.objects.filter(assigned_to__organization=user.organization).count(),
        })
    
    return JsonResponse({
        'success': True,
        'stats': stats,
        'timestamp': timezone.now().isoformat()
    })


@login_required
def process_overview_api(request):
    """채용 프로세스 현황 API"""
    user = request.user
    
    # 권한별 필터링
    if user.is_hospital_user():
        org_filter = Q(requester__organization=user.organization)
        candidates_filter = Q(job_request__requester__organization=user.organization)
    elif user.is_headhunting_user():
        org_filter = Q(assigned_to__organization=user.organization)
        candidates_filter = Q(recommended_by__organization=user.organization)
    else:
        org_filter = Q()
        candidates_filter = Q()
    
    # 채용 요청 단계
    job_requests = JobRequest.objects.filter(org_filter)
    job_request_data = {
        'total': job_requests.count(),
        'draft': job_requests.filter(status='draft').count(),
        'submitted': job_requests.filter(status='submitted').count(),
        'accepted': job_requests.filter(status='accepted').count(),
        'in_progress': job_requests.filter(status='in_progress').count(),
        'completed': job_requests.filter(status='completed').count(),
    }
    
    # 후보자 추천 단계
    candidates = Candidate.objects.filter(candidates_filter)
    candidate_data = {
        'total': candidates.count(),
        'waiting': candidates.filter(status='waiting').count(),
        'under_review': candidates.filter(status='under_review').count(),
        'approved': candidates.filter(status='approved').count(),
        'rejected': candidates.filter(status='rejected').count(),
    }
    
    # 후보자 검토 단계
    reviews = CandidateReview.objects.filter(candidate__in=candidates)
    review_data = {
        'total_reviews': reviews.count(),
        'passed': reviews.filter(passed=True).count(),
        'failed': reviews.filter(passed=False).count(),
        'avg_score': reviews.aggregate(avg=Avg('total_score'))['avg'] or 0,
    }
    
    # 면접 단계
    interviews = Interview.objects.filter(candidate__in=candidates)
    interview_data = {
        'total': interviews.count(),
        'scheduled': interviews.filter(status='scheduled').count(),
        'completed': interviews.filter(status='completed').count(),
        'cancelled': interviews.filter(status='cancelled').count(),
    }
    
    # 최종 결정 및 채용 완료
    final_decision_data = {
        'total_candidates': candidates.count(),
        'hired': candidates.filter(status='hired').count(),
        'final_approved': candidates.filter(status='final_approved').count(),
        'final_rejected': candidates.filter(status='final_rejected').count(),
    }
    
    hiring_complete_data = {
        'total_hired': candidates.filter(status='hired').count(),
        'this_month': candidates.filter(
            status='hired',
            updated_at__gte=timezone.now().replace(day=1)
        ).count(),
    }
    
    return JsonResponse({
        'success': True,
        'process_data': {
            'job_request': job_request_data,
            'candidate_recommendation': candidate_data,
            'candidate_review': review_data,
            'interview': interview_data,
            'final_decision': final_decision_data,
            'hiring_complete': hiring_complete_data,
        },
        'timestamp': timezone.now().isoformat()
    })


@login_required
def performance_metrics_api(request):
    """성과 지표 API"""
    user = request.user
    
    # 최근 3개월 데이터
    three_months_ago = timezone.now() - timedelta(days=90)
    
    if user.is_hospital_user():
        org_filter = Q(requester__organization=user.organization)
        candidates_filter = Q(job_request__requester__organization=user.organization)
    elif user.is_headhunting_user():
        org_filter = Q(assigned_to__organization=user.organization)
        candidates_filter = Q(recommended_by__organization=user.organization)
    else:
        org_filter = Q()
        candidates_filter = Q()
    
    # 채용 완료율
    completed_requests = JobRequest.objects.filter(
        org_filter,
        status='completed',
        completed_at__gte=three_months_ago
    ).count()
    
    total_requests = JobRequest.objects.filter(
        org_filter,
        created_at__gte=three_months_ago
    ).count()
    
    completion_rate = (completed_requests / total_requests * 100) if total_requests > 0 else 0
    
    # 평균 채용 기간
    avg_hiring_days = JobRequest.objects.filter(
        org_filter,
        status='completed',
        completed_at__isnull=False
    ).aggregate(
        avg_days=Avg(
            ExpressionWrapper(
                F('completed_at') - F('created_at'),
                output_field=DurationField()
            )
        )
    )['avg_days']
    
    # 후보자 품질 지표
    candidate_reviews = CandidateReview.objects.filter(
        candidate__in=Candidate.objects.filter(candidates_filter),
        reviewed_at__gte=three_months_ago
    )
    
    avg_review_score = candidate_reviews.aggregate(avg=Avg('total_score'))['avg'] or 0
    pass_rate = (candidate_reviews.filter(passed=True).count() / candidate_reviews.count() * 100) if candidate_reviews.count() > 0 else 0
    
    # 응답 시간 (평균)
    response_times = []
    recent_requests = JobRequest.objects.filter(
        org_filter,
        created_at__gte=three_months_ago
    )
    
    for request in recent_requests:
        if request.status != 'draft':
            # JobRequest에서 관련된 Workflow를 찾기
            try:
                # WorkflowProgress를 통해 관련된 Workflow 찾기
                workflow_progress = request.workflow_progress
                if hasattr(workflow_progress, 'workflow'):
                    workflow = workflow_progress.workflow
                    first_action = WorkflowActionLog.objects.filter(
                        workflow=workflow
                    ).order_by('performed_at').first()
                    
                    if first_action:
                        response_time = (first_action.performed_at - request.created_at).days
                        response_times.append(response_time)
            except:
                # Workflow가 없는 경우 건너뛰기
                continue
    
    avg_response_days = sum(response_times) / len(response_times) if response_times else 0
    
    return JsonResponse({
        'success': True,
        'metrics': {
            'completion_rate': round(completion_rate, 1),
            'avg_hiring_days': round(avg_hiring_days.days if avg_hiring_days else 0, 1),
            'avg_review_score': round(avg_review_score, 1),
            'candidate_pass_rate': round(pass_rate, 1),
            'avg_response_days': round(avg_response_days, 1),
            'completed_requests_3months': completed_requests,
            'total_requests_3months': total_requests,
        },
        'timestamp': timezone.now().isoformat()
    })


@login_required
def recent_activities_api(request):
    """최근 활동 API"""
    user = request.user
    
    # 최근 30일 활동
    thirty_days_ago = timezone.now() - timedelta(days=30)
    
    # 사용자 활동
    user_activities = UserActivity.objects.filter(
        user=user,
        created_at__gte=thirty_days_ago
    ).order_by('-created_at')[:20]
    
    # 워크플로우 액션 로그
    workflow_actions = WorkflowActionLog.objects.filter(
        performed_by=user,
        performed_at__gte=thirty_days_ago
    ).order_by('-performed_at')[:10]
    
    # 후보자 이력
    candidate_history = CandidateHistory.objects.filter(
        action_by=user,
        created_at__gte=thirty_days_ago
    ).order_by('-created_at')[:10]
    
    activities = []
    for activity in user_activities:
        activities.append({
            'id': activity.id,
            'type': activity.get_activity_type_display(),
            'description': activity.description,
            'created_at': activity.created_at.isoformat(),
            'time_ago': activity.created_at.strftime('%m/%d %H:%M'),
        })
    
    return JsonResponse({
        'success': True,
        'activities': activities,
        'total_activities': user_activities.count(),
        'timestamp': timezone.now().isoformat()
    })


@login_required
def notifications_api(request):
    """알림 API"""
    user = request.user
    
    # 최근 알림
    recent_notifications = Notification.objects.filter(
        recipient=user
    ).order_by('-created_at')[:10]
    
    notifications = []
    for notification in recent_notifications:
        notifications.append({
            'id': notification.id,
            'title': notification.title,
            'message': notification.message,
            'is_read': notification.is_read,
            'created_at': notification.created_at.isoformat(),
            'time_ago': notification.created_at.strftime('%m/%d %H:%M'),
        })
    
    return JsonResponse({
        'success': True,
        'notifications': notifications,
        'unread_count': Notification.objects.filter(recipient=user, is_read=False).count(),
        'timestamp': timezone.now().isoformat()
    })


@login_required
def pending_tasks_api(request):
    """대기 중인 작업 API"""
    user = request.user
    
    # 사용자에게 할당된 대기 중인 작업들
    if user.is_hospital_user():
        pending_tasks = WorkflowStep.objects.filter(
            job_request__requester__organization=user.organization,
            status='pending'
        ).select_related('job_request', 'assigned_to')
    elif user.is_headhunting_user():
        pending_tasks = WorkflowStep.objects.filter(
            assigned_to=user,
            status='pending'
        ).select_related('job_request', 'assigned_to')
    else:
        pending_tasks = WorkflowStep.objects.filter(
            status='pending'
        ).select_related('job_request', 'assigned_to')
    
    tasks = []
    for task in pending_tasks:
        tasks.append({
            'id': task.id,
            'title': task.title,
            'description': task.description,
            'job_request': task.job_request.title if task.job_request else '',
            'assigned_to': task.assigned_to.get_full_name() if task.assigned_to else '',
            'due_date': task.due_date.isoformat() if task.due_date else None,
            'created_at': task.created_at.isoformat(),
        })
    
    return JsonResponse({
        'success': True,
        'tasks': tasks,
        'total_tasks': pending_tasks.count(),
        'timestamp': timezone.now().isoformat()
    }) 