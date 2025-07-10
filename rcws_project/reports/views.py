from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import csrf_exempt
from django.core.paginator import Paginator
import json
from candidates.models import Candidate
from workflow.models import JobRequest, Workflow
from evaluations.models import InterviewEvaluation, DocumentReview
from .models import Report
from .forms import ReportForm


@login_required
def report_list(request):
    """보고서 목록 뷰"""
    reports = Report.objects.all().order_by('-created_at')
    paginator = Paginator(reports, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    breadcrumbs = [
        {'text': '대시보드', 'url': '/', 'icon': 'mdi-home'},
        {'text': '보고서 목록', 'url': None, 'icon': 'mdi-chart-line'}
    ]
    
    context = {
        'reports': page_obj,
        'page_obj': page_obj,
        'is_paginated': paginator.num_pages > 1,
        'total_candidates': Candidate.objects.count(),
        'total_job_requests': JobRequest.objects.count(),
        'total_workflows': Workflow.objects.count(),
        'total_evaluations': InterviewEvaluation.objects.count(),
        'page_title': '보고서 목록',
        'breadcrumbs': breadcrumbs,
    }
    return render(request, 'reports/report_list.html', context)


@login_required
def report_create(request):
    """보고서 생성 뷰"""
    if request.method == 'POST':
        form = ReportForm(request.POST)
        if form.is_valid():
            report = form.save(commit=False)
            report.created_by = request.user
            report.save()
            
            # 보고서 생성 시작
            if report.generate_report():
                messages.success(request, '보고서가 성공적으로 생성되었습니다.')
            else:
                messages.warning(request, '보고서 생성 중 오류가 발생했습니다.')
            
            return redirect('reports:detail', report_id=report.id)
    else:
        form = ReportForm()
    
    breadcrumbs = [
        {'text': '대시보드', 'url': '/', 'icon': 'mdi-home'},
        {'text': '보고서 목록', 'url': '/reports/', 'icon': 'mdi-chart-line'},
        {'text': '새 보고서', 'url': None, 'icon': 'mdi-chart-line-plus'}
    ]
    
    context = {
        'form': form,
        'total_candidates': Candidate.objects.count(),
        'total_job_requests': JobRequest.objects.count(),
        'total_workflows': Workflow.objects.count(),
        'total_evaluations': InterviewEvaluation.objects.count(),
        'page_title': '새 보고서',
        'breadcrumbs': breadcrumbs,
    }
    return render(request, 'reports/report_create.html', context)


@login_required
def report_detail(request, report_id):
    """보고서 상세 뷰"""
    report = get_object_or_404(Report, id=report_id)
    
    breadcrumbs = [
        {'text': '대시보드', 'url': '/', 'icon': 'mdi-home'},
        {'text': '보고서 목록', 'url': '/reports/', 'icon': 'mdi-chart-line'},
        {'text': report.title, 'url': None, 'icon': 'mdi-chart-line'}
    ]
    
    context = {
        'report': report,
        'page_title': f'보고서 상세 - {report.title}',
        'breadcrumbs': breadcrumbs,
    }
    return render(request, 'reports/report_detail.html', context)


@login_required
def report_update(request, report_id):
    """보고서 수정 뷰"""
    report = get_object_or_404(Report, id=report_id)
    if request.method == 'POST':
        form = ReportForm(request.POST, instance=report)
        if form.is_valid():
            form.save()
            messages.success(request, '보고서가 성공적으로 업데이트되었습니다.')
            return redirect('reports:detail', report_id=report.id)
    else:
        form = ReportForm(instance=report)
    
    breadcrumbs = [
        {'text': '대시보드', 'url': '/', 'icon': 'mdi-home'},
        {'text': '보고서 목록', 'url': '/reports/', 'icon': 'mdi-chart-line'},
        {'text': report.title, 'url': f'/reports/{report.id}/', 'icon': 'mdi-chart-line'},
        {'text': '수정', 'url': None, 'icon': 'mdi-chart-line-edit'}
    ]
    
    context = {
        'form': form,
        'report': report,
        'page_title': f'보고서 수정 - {report.title}',
        'breadcrumbs': breadcrumbs,
    }
    return render(request, 'reports/report_update.html', context)


@login_required
def report_download(request, report_id):
    """보고서 다운로드 뷰"""
    report = get_object_or_404(Report, id=report_id)
    
    if report.is_generated:
        # 실제 파일 다운로드 로직 (여기서는 시뮬레이션)
        messages.success(request, '보고서 다운로드가 시작되었습니다.')
        return JsonResponse({'success': True, 'message': '다운로드 시작'})
    else:
        messages.error(request, '보고서가 아직 생성되지 않았습니다.')
        return JsonResponse({'success': False, 'message': '보고서가 생성되지 않음'})


@login_required
def performance_report(request):
    """성과 보고서 뷰"""
    # 기본 통계 데이터
    breadcrumbs = [
        {'text': '대시보드', 'url': '/', 'icon': 'mdi-home'},
        {'text': '보고서 목록', 'url': '/reports/', 'icon': 'mdi-chart-line'},
        {'text': '성과 보고서', 'url': None, 'icon': 'mdi-chart-areaspline'}
    ]
    
    context = {
        'total_candidates': Candidate.objects.count(),
        'active_candidates': Candidate.objects.filter(status__in=['recommended', 'document_review', 'interview_scheduled']).count(),
        'hired_candidates': Candidate.objects.filter(status='hired').count(),
        'total_job_requests': JobRequest.objects.count(),
        'completed_workflows': Workflow.objects.filter(status='completed').count(),
        'total_evaluations': InterviewEvaluation.objects.count(),
        'page_title': '성과 보고서',
        'breadcrumbs': breadcrumbs,
    }
    return render(request, 'reports/performance_report.html', context)


@login_required
def workflow_analytics(request):
    """워크플로우 분석 뷰"""
    # 워크플로우 통계
    workflows = Workflow.objects.all()
    
    breadcrumbs = [
        {'text': '대시보드', 'url': '/', 'icon': 'mdi-home'},
        {'text': '보고서 목록', 'url': '/reports/', 'icon': 'mdi-chart-line'},
        {'text': '워크플로우 분석', 'url': None, 'icon': 'mdi-chart-timeline-variant'}
    ]
    
    context = {
        'total_workflows': workflows.count(),
        'active_workflows': workflows.filter(status='in_progress').count(),
        'completed_workflows': workflows.filter(status='completed').count(),
        'pending_workflows': workflows.filter(status='pending').count(),
        'workflows_by_priority': {
            'high': workflows.filter(priority='high').count(),
            'medium': workflows.filter(priority='medium').count(),
            'low': workflows.filter(priority='low').count(),
        },
        'page_title': '워크플로우 분석',
        'breadcrumbs': breadcrumbs,
    }
    return render(request, 'reports/workflow_analytics.html', context)


@login_required
def candidate_stats(request):
    """후보자 통계 뷰"""
    candidates = Candidate.objects.all()
    
    breadcrumbs = [
        {'text': '대시보드', 'url': '/', 'icon': 'mdi-home'},
        {'text': '보고서 목록', 'url': '/reports/', 'icon': 'mdi-chart-line'},
        {'text': '후보자 통계', 'url': None, 'icon': 'mdi-chart-pie'}
    ]
    
    context = {
        'total_candidates': candidates.count(),
        'candidates_by_status': {
            'recommended': candidates.filter(status='recommended').count(),
            'document_review': candidates.filter(status='document_review').count(),
            'document_passed': candidates.filter(status='document_passed').count(),
            'document_failed': candidates.filter(status='document_failed').count(),
            'interview_scheduled': candidates.filter(status='interview_scheduled').count(),
            'interviewed': candidates.filter(status='interviewed').count(),
            'final_passed': candidates.filter(status='final_passed').count(),
            'final_failed': candidates.filter(status='final_failed').count(),
            'hired': candidates.filter(status='hired').count(),
            'withdrawn': candidates.filter(status='withdrawn').count(),
        },
        'candidates_by_education': {
            'high_school': candidates.filter(education_level='high_school').count(),
            'college': candidates.filter(education_level='college').count(),
            'university': candidates.filter(education_level='university').count(),
            'graduate': candidates.filter(education_level='graduate').count(),
            'phd': candidates.filter(education_level='phd').count(),
        },
        'page_title': '후보자 통계',
        'breadcrumbs': breadcrumbs,
    }
    return render(request, 'reports/candidate_stats.html', context)


@login_required
@require_POST
@csrf_exempt
def generate_quick_report(request):
    """빠른 보고서 생성 API"""
    try:
        data = json.loads(request.body)
        report_type = data.get('report_type')
        
        # 보고서 생성
        report = Report.objects.create(
            title=f"{data.get('report_type', 'quick')} 보고서",
            description=f"빠른 {data.get('report_type', 'quick')} 보고서",
            report_type=report_type,
            created_by=request.user
        )
        
        # 보고서 생성 시작
        if report.generate_report():
            return JsonResponse({'success': True, 'report_id': report.id, 'message': '보고서 생성 완료'})
        else:
            return JsonResponse({'success': False, 'message': '보고서 생성 실패'})
            
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})
