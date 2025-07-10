from celery import shared_task
from django.utils import timezone
from django.core.mail import send_mail
from django.template.loader import render_to_string
from .models import JobRequest, WorkflowStep
from candidates.models import Candidate
from evaluations.models import Interview
from notifications.utils import send_notification


@shared_task
def send_job_request_notification(job_request_id):
    """채용 요청 알림 발송"""
    try:
        job_request = JobRequest.objects.get(id=job_request_id)
        
        # 헤드헌팅 기관에 알림 발송
        from accounts.models import User
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
            
            # 이메일 알림도 발송
            send_job_request_email.delay(job_request_id, user.id)
            
    except JobRequest.DoesNotExist:
        pass


@shared_task
def send_job_request_email(job_request_id, user_id):
    """채용 요청 이메일 발송"""
    try:
        job_request = JobRequest.objects.get(id=job_request_id)
        from accounts.models import User
        user = User.objects.get(id=user_id)
        
        subject = f'새로운 채용 요청: {job_request.position_title}'
        message = render_to_string('emails/new_job_request.html', {
            'job_request': job_request,
            'user': user
        })
        
        send_mail(
            subject=subject,
            message=message,
            from_email=None,  # DEFAULT_FROM_EMAIL 사용
            recipient_list=[user.email],
            html_message=message
        )
        
    except (JobRequest.DoesNotExist, User.DoesNotExist):
        pass


@shared_task
def check_overdue_workflow_steps():
    """마감일 초과된 워크플로우 단계 확인"""
    overdue_steps = WorkflowStep.objects.filter(
        status='in_progress',
        due_date__lt=timezone.now()
    )
    
    for step in overdue_steps:
        if step.assigned_to:
            send_notification(
                recipient=step.assigned_to,
                notification_type='workflow_overdue',
                title=f'워크플로우 마감일 초과: {step.get_step_name_display()}',
                message=f'{step.job_request.position_title}의 {step.get_step_name_display()} 단계가 마감일을 초과했습니다.',
                related_object_id=step.id,
                related_object_type='WorkflowStep',
                priority='high'
            )


@shared_task
def send_interview_reminders():
    """면접 리마인더 발송"""
    from datetime import timedelta
    
    # 1시간 후 면접
    reminder_time = timezone.now() + timedelta(hours=1)
    upcoming_interviews = Interview.objects.filter(
        scheduled_date__range=[reminder_time - timedelta(minutes=5), reminder_time + timedelta(minutes=5)],
        status='scheduled'
    )
    
    for interview in upcoming_interviews:
        send_notification(
            recipient=interview.interviewer,
            notification_type='interview_reminder',
            title=f'면접 리마인더: {interview.candidate.name}',
            message=f'{interview.candidate.name}님의 면접이 1시간 후에 예정되어 있습니다.',
            related_object_id=interview.id,
            related_object_type='Interview',
            priority='high'
        )


@shared_task
def generate_weekly_report():
    """주간 보고서 생성"""
    from datetime import timedelta
    
    end_date = timezone.now()
    start_date = end_date - timedelta(days=7)
    
    # 통계 데이터 수집
    stats = {
        'new_job_requests': JobRequest.objects.filter(
            created_at__range=[start_date, end_date]
        ).count(),
        'completed_job_requests': JobRequest.objects.filter(
            status='completed',
            completed_at__range=[start_date, end_date]
        ).count(),
        'new_candidates': Candidate.objects.filter(
            created_at__range=[start_date, end_date]
        ).count(),
        'completed_interviews': Interview.objects.filter(
            status='completed',
            completed_at__range=[start_date, end_date]
        ).count()
    }
    
    # 관리자에게 보고서 발송
    from accounts.models import User
    admin_users = User.objects.filter(role='system_admin')
    
    for user in admin_users:
        send_notification(
            recipient=user,
            notification_type='weekly_report',
            title='주간 보고서',
            message=f'지난 주 통계: 신규 요청 {stats["new_job_requests"]}건, 완료 {stats["completed_job_requests"]}건',
            priority='normal'
        )


@shared_task
def cleanup_old_data():
    """오래된 데이터 정리"""
    from datetime import timedelta
    
    # 1년 이상 된 완료된 채용 요청
    old_date = timezone.now() - timedelta(days=365)
    old_job_requests = JobRequest.objects.filter(
        status='completed',
        completed_at__lt=old_date
    )
    
    # 로그만 남기고 실제 삭제는 하지 않음 (데이터 보존)
    print(f"Found {old_job_requests.count()} old completed job requests")
    
    # 6개월 이상 된 읽지 않은 알림
    from notifications.models import Notification
    old_notifications = Notification.objects.filter(
        is_read=False,
        created_at__lt=old_date
    )
    
    # 읽지 않은 오래된 알림은 읽음 처리
    old_notifications.update(is_read=True)
    print(f"Marked {old_notifications.count()} old notifications as read") 