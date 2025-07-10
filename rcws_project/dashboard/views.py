from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.db.models import Count, Q, Avg, F, ExpressionWrapper, DurationField, Sum
from django.utils import timezone
from datetime import datetime, timedelta
from django.core.paginator import Paginator
from django.urls import reverse
from django.http import JsonResponse
from workflow.models import Workflow, JobRequest, WorkflowStep, JobPosting, WorkflowProgress, WorkflowActionLog
from candidates.models import Candidate, CandidateReview, CandidateHistory
from evaluations.models import InterviewEvaluation, Interview, DocumentReview
from notifications.models import Notification
from accounts.models import UserActivity, Organization, User


@login_required
def dashboard_main(request):
    """대시보드 메인 페이지"""
    user = request.user
    
    # 기본 통계
    stats = get_basic_stats(user)
    
    # 역할별 대시보드 데이터
    if user.is_hospital_user():
        dashboard_data = get_hospital_dashboard_data(user)
    elif user.is_headhunting_user():
        dashboard_data = get_headhunting_dashboard_data(user)
    else:
        dashboard_data = get_admin_dashboard_data(user)
    
    # 전체 채용 프로세스 현황
    process_overview = get_recruitment_process_overview(user)
    
    # 업무 이력 및 모니터링
    activity_data = get_activity_monitoring_data(user)
    
    # 성과 지표
    performance_metrics = get_performance_metrics(user)
    
    # 최근 활동
    recent_activities = UserActivity.objects.select_related('user').order_by('-created_at')[:10]
    
    # 최근 알림
    recent_notifications = Notification.objects.filter(recipient=request.user).order_by('-created_at')[:5]
    
    context = {
        'stats': stats,
        'dashboard_data': dashboard_data,
        'process_overview': process_overview,
        'activity_data': activity_data,
        'performance_metrics': performance_metrics,
        'recent_activities': recent_activities,
        'recent_notifications': recent_notifications,
        'user': user,
    }
    
    return render(request, 'dashboard/main.html', context)


def get_basic_stats(user):
    """기본 통계 데이터"""
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
        org_filter = Q(created_by__organization=user.organization)
        stats.update({
            'my_job_requests': JobRequest.objects.filter(requester__organization=user.organization).count(),
            'my_candidates': Candidate.objects.filter(job_request__requester__organization=user.organization).count(),
            'my_active_workflows': Workflow.objects.filter(org_filter, status='in_progress').count(),
        })
    elif user.is_headhunting_user():
        org_filter = Q(recommended_by__organization=user.organization)
        stats.update({
            'my_recommended_candidates': Candidate.objects.filter(org_filter).count(),
            'my_active_assignments': JobRequest.objects.filter(assigned_to__organization=user.organization).count(),
        })
    
    return stats


def get_recruitment_process_overview(user):
    """전체 채용 프로세스 현황"""
    process_data = {
        'stages': [
            {'name': '채용 요청', 'key': 'job_request', 'icon': 'mdi-file-document-outline'},
            {'name': '요청 검토', 'key': 'request_review', 'icon': 'mdi-clipboard-check-outline'},
            {'name': '후보자 추천', 'key': 'candidate_recommendation', 'icon': 'mdi-account-multiple-outline'},
            {'name': '후보자 검토', 'key': 'candidate_review', 'icon': 'mdi-account-check-outline'},
            {'name': '면접 진행', 'key': 'interview', 'icon': 'mdi-account-group-outline'},
            {'name': '최종 결정', 'key': 'final_decision', 'icon': 'mdi-flag-checkered'},
            {'name': '채용 완료', 'key': 'hiring_complete', 'icon': 'mdi-account-check'},
        ]
    }
    
    # 각 단계별 통계
    if user.is_hospital_user():
        job_request_filter = Q(requester__organization=user.organization)
        workflow_filter = Q(created_by__organization=user.organization)
        candidates_filter = Q(job_request__requester__organization=user.organization)
    elif user.is_headhunting_user():
        job_request_filter = Q(assigned_to__organization=user.organization)
        workflow_filter = Q(assigned_to__organization=user.organization)
        candidates_filter = Q(recommended_by__organization=user.organization)
    else:
        job_request_filter = Q()
        workflow_filter = Q()
        candidates_filter = Q()
    
    # 채용 요청 단계
    job_requests = JobRequest.objects.filter(job_request_filter)
    process_data['job_request'] = {
        'total': job_requests.count(),
        'draft': job_requests.filter(status='draft').count(),
        'submitted': job_requests.filter(status='submitted').count(),
        'accepted': job_requests.filter(status='accepted').count(),
        'in_progress': job_requests.filter(status='in_progress').count(),
        'completed': job_requests.filter(status='completed').count(),
    }
    
    # 후보자 추천 단계
    candidates = Candidate.objects.filter(candidates_filter)
    process_data['candidate_recommendation'] = {
        'total': candidates.count(),
        'waiting': candidates.filter(status='waiting').count(),
        'under_review': candidates.filter(status='under_review').count(),
        'approved': candidates.filter(status='approved').count(),
        'rejected': candidates.filter(status='rejected').count(),
    }
    
    # 후보자 검토 단계
    reviews = CandidateReview.objects.filter(candidate__in=candidates)
    process_data['candidate_review'] = {
        'total_reviews': reviews.count(),
        'passed': reviews.filter(passed=True).count(),
        'failed': reviews.filter(passed=False).count(),
        'avg_score': reviews.aggregate(avg=Avg('total_score'))['avg'] or 0,
    }
    
    # 면접 단계
    interviews = Interview.objects.filter(candidate__in=candidates)
    process_data['interview'] = {
        'total': interviews.count(),
        'scheduled': interviews.filter(status='scheduled').count(),
        'completed': interviews.filter(status='completed').count(),
        'cancelled': interviews.filter(status='cancelled').count(),
    }
    
    # 최종 결정 및 채용 완료
    process_data['final_decision'] = {
        'total_candidates': candidates.count(),
        'hired': candidates.filter(status='hired').count(),
        'final_approved': candidates.filter(status='final_approved').count(),
        'final_rejected': candidates.filter(status='final_rejected').count(),
    }
    
    process_data['hiring_complete'] = {
        'total_hired': candidates.filter(status='hired').count(),
        'this_month': candidates.filter(
            status='hired',
            updated_at__gte=timezone.now().replace(day=1)
        ).count(),
    }
    
    return process_data


def get_activity_monitoring_data(user):
    """업무 이력 및 모니터링 데이터"""
    # 최근 30일 활동
    thirty_days_ago = timezone.now() - timedelta(days=30)
    
    if user.is_hospital_user():
        job_request_filter = Q(requester__organization=user.organization)
        workflow_filter = Q(created_by__organization=user.organization)
        candidates_filter = Q(job_request__requester__organization=user.organization)
    elif user.is_headhunting_user():
        job_request_filter = Q(assigned_to__organization=user.organization)
        workflow_filter = Q(assigned_to__organization=user.organization)
        candidates_filter = Q(recommended_by__organization=user.organization)
    else:
        job_request_filter = Q()
        workflow_filter = Q()
        candidates_filter = Q()
    
    # 사용자 활동
    user_activities = UserActivity.objects.filter(
        user=user,
        created_at__gte=thirty_days_ago
    ).order_by('-created_at')
    
    # 워크플로우 액션 로그
    workflow_actions = WorkflowActionLog.objects.filter(
        performed_by=user,
        performed_at__gte=thirty_days_ago
    ).order_by('-performed_at')
    
    # 후보자 이력
    candidate_history = CandidateHistory.objects.filter(
        action_by=user,
        created_at__gte=thirty_days_ago
    ).order_by('-created_at')
    
    # 일별 활동 통계
    daily_activity = {}
    for i in range(30):
        date = timezone.now().date() - timedelta(days=i)
        daily_activity[date] = {
            'activities': user_activities.filter(created_at__date=date).count(),
            'workflow_actions': workflow_actions.filter(performed_at__date=date).count(),
            'candidate_actions': candidate_history.filter(created_at__date=date).count(),
        }
    
    # 활동 유형별 통계
    activity_types = user_activities.values('activity_type').annotate(
        count=Count('activity_type')
    ).order_by('-count')
    
    return {
        'recent_activities': list(user_activities[:20]),
        'recent_workflow_actions': list(workflow_actions[:10]),
        'recent_candidate_actions': list(candidate_history[:10]),
        'daily_activity': daily_activity,
        'activity_types': list(activity_types),
        'total_activities_30days': user_activities.count(),
        'avg_daily_activities': user_activities.count() / 30,
    }


def get_performance_metrics(user):
    """성과 지표"""
    # 최근 3개월 데이터
    three_months_ago = timezone.now() - timedelta(days=90)
    
    if user.is_hospital_user():
        job_request_filter = Q(requester__organization=user.organization)
        workflow_filter = Q(created_by__organization=user.organization)
        candidates_filter = Q(job_request__requester__organization=user.organization)
    elif user.is_headhunting_user():
        job_request_filter = Q(assigned_to__organization=user.organization)
        workflow_filter = Q(assigned_to__organization=user.organization)
        candidates_filter = Q(recommended_by__organization=user.organization)
    else:
        job_request_filter = Q()
        workflow_filter = Q()
        candidates_filter = Q()
    
    # 채용 완료율
    completed_requests = JobRequest.objects.filter(
        job_request_filter,
        status='completed',
        completed_at__gte=three_months_ago
    ).count()
    
    total_requests = JobRequest.objects.filter(
        job_request_filter,
        created_at__gte=three_months_ago
    ).count()
    
    completion_rate = (completed_requests / total_requests * 100) if total_requests > 0 else 0
    
    # 평균 채용 기간
    avg_hiring_days = JobRequest.objects.filter(
        job_request_filter,
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
        job_request_filter,
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
    
    return {
        'completion_rate': round(completion_rate, 1),
        'avg_hiring_days': round(avg_hiring_days.days if avg_hiring_days else 0, 1),
        'avg_review_score': round(avg_review_score, 1),
        'candidate_pass_rate': round(pass_rate, 1),
        'avg_response_days': round(avg_response_days, 1),
        'completed_requests_3months': completed_requests,
        'total_requests_3months': total_requests,
    }


def get_hospital_dashboard_data(user):
    """병원 사용자 대시보드 데이터"""
    org = user.organization
    
    # 진행 중인 채용 요청
    active_requests = JobRequest.objects.filter(
        requester__organization=user.organization,
        status__in=['submitted', 'accepted', 'in_progress']
    )
    
    # 대기중인 업무
    pending_tasks = WorkflowStep.objects.filter(
        workflow__created_by__organization=user.organization,
        status='pending',
        name__in=['document_review', 'interview_scheduled']
    )
    
    # 이번 주 면접 일정
    week_start = timezone.now().date()
    week_end = week_start + timedelta(days=7)
    upcoming_interviews = Interview.objects.filter(
        candidate__job_request__requester__organization=user.organization,
        scheduled_date__date__range=[week_start, week_end],
        status='scheduled'
    )
    
    # 통계 데이터
    this_month = timezone.now().replace(day=1)
    monthly_stats = {
        'new_requests': JobRequest.objects.filter(
            requester__organization=user.organization,
            created_at__gte=this_month
        ).count(),
        'completed_hires': JobRequest.objects.filter(
            requester__organization=user.organization,
            status='completed',
            completed_at__gte=this_month
        ).count(),
        'in_progress': active_requests.count()
    }
    
    # 읽지 않은 알림
    unread_notifications = Notification.objects.filter(
        recipient=user,
        is_read=False
    ).count()
    
    return {
        'dashboard_type': 'hospital',
        'active_requests': active_requests,
        'pending_tasks': pending_tasks,
        'upcoming_interviews': upcoming_interviews,
        'monthly_stats': monthly_stats,
        'unread_notifications': unread_notifications
    }


def get_headhunting_dashboard_data(user):
    """헤드헌팅 사용자 대시보드 데이터"""
    org = user.organization
    
    # 내가 추천한 후보자 현황
    my_candidates = Candidate.objects.filter(
        recommended_by__organization=org
    ).order_by('-recommended_at')[:10]
    
    # 진행 중인 채용 요청
    active_assignments = JobRequest.objects.filter(
        assigned_to__organization=org,
        status__in=['accepted', 'in_progress']
    ).order_by('-created_at')[:5]
    
    # 최근 추천한 후보자
    recent_recommendations = Candidate.objects.filter(
        recommended_by__organization=org
    ).order_by('-recommended_at')[:5]
    
    # 검토 결과 대기 중인 후보자
    pending_review_results = Candidate.objects.filter(
        recommended_by__organization=org,
        review_status='in_progress'
    ).order_by('-recommended_at')[:5]
    
    return {
        'my_candidates': my_candidates,
        'active_assignments': active_assignments,
        'recent_recommendations': recent_recommendations,
        'pending_review_results': pending_review_results,
    }


def get_admin_dashboard_data(user):
    """관리자 대시보드 데이터"""
    # 전체 시스템 현황
    total_organizations = Organization.objects.count()
    total_users = User.objects.count()
    total_workflows = Workflow.objects.count()
    
    # 최근 가입한 기관
    recent_organizations = Organization.objects.order_by('-created_at')[:5]
    
    # 시스템 활동
    recent_system_activities = UserActivity.objects.select_related('user').order_by('-created_at')[:10]
    
    # 전체 채용 통계
    total_job_requests = JobRequest.objects.count()
    total_candidates = Candidate.objects.count()
    total_interviews = Interview.objects.count()
    
    return {
        'total_organizations': total_organizations,
        'total_users': total_users,
        'total_workflows': total_workflows,
        'recent_organizations': recent_organizations,
        'recent_system_activities': recent_system_activities,
        'total_job_requests': total_job_requests,
        'total_candidates': total_candidates,
        'total_interviews': total_interviews,
    }


def get_recruitment_progress_data(organization):
    """채용 진행률 데이터"""
    job_requests = JobRequest.objects.filter(requester__organization=organization)
    
    progress_data = {
        'total_requests': job_requests.count(),
        'draft': job_requests.filter(status='draft').count(),
        'submitted': job_requests.filter(status='submitted').count(),
        'accepted': job_requests.filter(status='accepted').count(),
        'in_progress': job_requests.filter(status='in_progress').count(),
        'completed': job_requests.filter(status='completed').count(),
        'cancelled': job_requests.filter(status='cancelled').count(),
    }
    
    # 진행률 계산
    if progress_data['total_requests'] > 0:
        progress_data['completion_rate'] = round(
            (progress_data['completed'] / progress_data['total_requests']) * 100, 1
        )
    else:
        progress_data['completion_rate'] = 0
    
    return progress_data


def get_upcoming_completions(organization):
    """예상 완료일이 가까운 채용 요청들"""
    # WorkflowProgress에서 예상 완료일이 가까운 것들
    upcoming = WorkflowProgress.objects.filter(
        job_request__requester__organization=organization,
        is_completed=False
    ).filter(
        target_completion_date__lte=timezone.now().date() + timedelta(days=7)
    ).select_related('job_request').order_by('target_completion_date')[:5]
    
    return upcoming


def get_candidate_status(organization):
    """후보자 현황"""
    candidates = Candidate.objects.filter(
        job_request__requester__organization=organization
    )
    
    status_data = {
        'total': candidates.count(),
        'recommended': candidates.filter(status='recommended').count(),
        'document_review': candidates.filter(status='document_review').count(),
        'interview_scheduled': candidates.filter(status='interview_scheduled').count(),
        'interviewed': candidates.filter(status='interviewed').count(),
        'hired': candidates.filter(status='hired').count(),
        'rejected': candidates.filter(status='rejected').count(),
    }
    
    return status_data


def get_this_week_interviews(organization):
    """이번 주 면접 일정"""
    week_start = timezone.now().date()
    week_end = week_start + timedelta(days=7)
    
    interviews = Interview.objects.filter(
        candidate__job_request__requester__organization=organization,
        scheduled_date__date__range=[week_start, week_end],
        status='scheduled'
    ).select_related('candidate', 'candidate__job_request').order_by('scheduled_date')[:5]
    
    return interviews


def get_headhunting_dashboard_data(user):
    """케이지아웃소싱 대시보드 데이터"""
    # 신규 채용 요청
    new_requests = JobRequest.objects.filter(
        status='submitted'
    ).order_by('-created_at')[:5]
    
    # 진행중인 요청
    in_progress_requests = JobRequest.objects.filter(
        status__in=['accepted', 'in_progress']
    )
    
    # 후보자 현황
    candidate_stats = {
        'recommended': Candidate.objects.filter(
            recommended_by__organization=user.organization,
            status='recommended'
        ).count(),
        'in_review': Candidate.objects.filter(
            recommended_by__organization=user.organization,
            status='document_review'
        ).count(),
        'interviewing': Candidate.objects.filter(
            recommended_by__organization=user.organization,
            status__in=['interview_scheduled', 'interviewed']
        ).count(),
        'hired': Candidate.objects.filter(
            recommended_by__organization=user.organization,
            status='hired'
        ).count()
    }
    
    # 성과 지표
    this_month = timezone.now().replace(day=1)
    performance_stats = {
        'success_rate': calculate_success_rate(user.organization, this_month),
        'avg_response_time': calculate_avg_response_time(user.organization),
        'total_recommendations': Candidate.objects.filter(
            recommended_by__organization=user.organization,
            created_at__gte=this_month
        ).count()
    }
    
    # 읽지 않은 알림
    unread_notifications = Notification.objects.filter(
        recipient=user,
        is_read=False
    ).count()
    
    return {
        'dashboard_type': 'headhunting',
        'new_requests': new_requests,
        'in_progress_requests': in_progress_requests,
        'candidate_stats': candidate_stats,
        'performance_stats': performance_stats,
        'unread_notifications': unread_notifications
    }


def get_admin_dashboard_data(user):
    """메디킹 관리자 대시보드 데이터"""
    # 전체 통계
    total_stats = {
        'total_organizations': Organization.objects.count(),
        'total_users': User.objects.count(),
        'total_workflows': Workflow.objects.count(),
        'total_candidates': Candidate.objects.count(),
        'total_job_requests': JobRequest.objects.count(),
        'total_notifications': Notification.objects.count()
    }
    
    # 기관별 통계
    org_stats = Organization.objects.annotate(
        user_count=Count('users'),
        workflow_count=Count('users__created_workflows'),
        candidate_count=Count('users__job_requests__candidates')
    )
    
    # 최근 활동
    recent_activities = UserActivity.objects.select_related('user').order_by('-created_at')[:10]
    
    # 시스템 상태
    system_status = {
        'active_users_today': UserActivity.objects.filter(
            created_at__date=timezone.now().date()
        ).values('user').distinct().count(),
        'new_registrations_this_month': User.objects.filter(
            date_joined__gte=timezone.now().replace(day=1)
        ).count(),
        'total_notifications_today': Notification.objects.filter(
            created_at__date=timezone.now().date()
        ).count()
    }
    
    return {
        'dashboard_type': 'admin',
        'total_stats': total_stats,
        'org_stats': org_stats,
        'recent_activities': recent_activities,
        'system_status': system_status
    }


def calculate_success_rate(organization, start_date):
    """성공률 계산"""
    total_recommendations = Candidate.objects.filter(
        recommended_by__organization=organization,
        created_at__gte=start_date
    ).count()
    
    successful_hires = Candidate.objects.filter(
        recommended_by__organization=organization,
        status='hired',
        created_at__gte=start_date
    ).count()
    
    if total_recommendations > 0:
        return round((successful_hires / total_recommendations) * 100, 1)
    return 0


def calculate_avg_response_time(organization):
    """평균 응답 시간 계산 (시간 단위)"""
    # 채용 요청 제출부터 접수까지의 평균 시간
    response_times = JobRequest.objects.filter(
        requester__organization=organization,
        submitted_at__isnull=False,
        accepted_at__isnull=False
    ).annotate(
        response_time=ExpressionWrapper(
            F('accepted_at') - F('submitted_at'),
            output_field=DurationField()
        )
    ).aggregate(avg_time=Avg('response_time'))
    
    if response_times['avg_time']:
        return round(response_times['avg_time'].total_seconds() / 3600, 1)  # 시간 단위
    return 0


def get_bottleneck_analysis():
    """병목 지점 분석"""
    bottlenecks = []
    
    # 진행 중인 워크플로우 중 지연된 것들
    delayed_workflows = Workflow.objects.filter(
        status='in_progress',
        due_date__lt=timezone.now()
    )
    
    if delayed_workflows.exists():
        bottlenecks.append({
            'type': 'delayed_workflows',
            'count': delayed_workflows.count(),
            'description': '마감일을 초과한 워크플로우가 있습니다.'
        })
    
    # 대기 중인 면접
    pending_interviews = Interview.objects.filter(status='scheduled')
    if pending_interviews.count() > 10:
        bottlenecks.append({
            'type': 'pending_interviews',
            'count': pending_interviews.count(),
            'description': '대기 중인 면접이 많습니다.'
        })
    
    return bottlenecks


def get_monthly_activity(organization):
    """월별 활동 통계"""
    current_month = timezone.now().month
    current_year = timezone.now().year
    
    monthly_data = []
    for i in range(6):  # 최근 6개월
        month = current_month - i
        year = current_year
        if month <= 0:
            month += 12
            year -= 1
        
        start_date = timezone.datetime(year, month, 1)
        if month == 12:
            end_date = timezone.datetime(year + 1, 1, 1)
        else:
            end_date = timezone.datetime(year, month + 1, 1)
        
        monthly_stats = {
            'month': f"{year}-{month:02d}",
            'job_requests': JobRequest.objects.filter(
                requester__organization=organization,
                created_at__gte=start_date,
                created_at__lt=end_date
            ).count(),
            'completed_hires': JobRequest.objects.filter(
                requester__organization=organization,
                status='completed',
                completed_at__gte=start_date,
                completed_at__lt=end_date
            ).count()
        }
        monthly_data.append(monthly_stats)
    
    return list(reversed(monthly_data))


@login_required
def notifications_view(request):
    """알림 목록 페이지 - notifications 앱으로 리다이렉트"""
    return redirect('notifications:list')


@login_required
def mark_notification_read(request, notification_id):
    """알림 읽음 처리"""
    try:
        notification = Notification.objects.get(
            id=notification_id,
            recipient=request.user
        )
        notification.is_read = True
        notification.save()
        return JsonResponse({'success': True})
    except Notification.DoesNotExist:
        return JsonResponse({'success': False, 'error': '알림을 찾을 수 없습니다.'})


@login_required
def mark_all_notifications_read(request):
    """모든 알림 읽음 처리"""
    Notification.objects.filter(
        recipient=request.user,
        is_read=False
    ).update(is_read=True)
    
    return JsonResponse({'success': True})
