from django.shortcuts import render
from django.contrib.auth.decorators import login_required


@login_required
def help_main(request):
    """도움말 메인 페이지"""
    return render(request, 'help/help_main.html')


@login_required
def help_dashboard(request):
    """대시보드 사용법"""
    return render(request, 'help/help_dashboard.html')


@login_required
def help_users(request):
    """사용자 관리 사용법"""
    return render(request, 'help/help_users.html')


@login_required
def help_candidates(request):
    """후보자 관리 사용법"""
    return render(request, 'help/help_candidates.html')


@login_required
def help_workflow(request):
    """워크플로우 사용법"""
    return render(request, 'help/help_workflow.html')


@login_required
def help_evaluations(request):
    """평가 관리 사용법"""
    return render(request, 'help/help_evaluations.html')


@login_required
def help_reports(request):
    """보고서 사용법"""
    return render(request, 'help/help_reports.html')


@login_required
def help_notifications(request):
    """알림 사용법"""
    return render(request, 'help/help_notifications.html')


@login_required
def help_faq(request):
    """자주 묻는 질문"""
    return render(request, 'help/help_faq.html')


@login_required
def help_contact(request):
    """문의하기"""
    return render(request, 'help/help_contact.html')
