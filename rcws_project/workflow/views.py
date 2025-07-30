from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages
from django.core.paginator import Paginator
from django.http import JsonResponse, HttpResponseForbidden
from django.views.decorators.http import require_POST, require_http_methods
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from django.urls import reverse, reverse_lazy
from django.db.models import Q, Count, Avg, Case, When, IntegerField
from django.utils import timezone
from accounts.models import User, UserActivity, Hospital, HospitalBranch, PositionTemplate
from accounts.decorators import hospital_only, headhunting_only, permission_required
from django.db.models import Q
from django.urls import reverse
from django.views.generic import CreateView
from .models import Workflow, WorkflowStep, WorkflowDocument, JobRequest, JobRequestTemplate, JobPosting, JobApplication, WorkflowProgress
from .forms import WorkflowForm, WorkflowStepForm, JobRequestForm, JobRequestTemplateForm, JobPostingForm


@login_required
def job_request_list(request):
    """채용 요청 목록 뷰 - 병원 관계자와 헤드헌팅 관계자 접근 가능"""
    # 사용자 유형에 따라 다른 쿼리셋 제공
    if request.user.is_hospital_user():
        # 병원 사용자: 자신의 조직의 요청만
        requests = JobRequest.objects.filter(requester__organization=request.user.organization)
    elif request.user.is_headhunting_user():
        # 헤드헌팅 사용자: 모든 요청 (제출된 요청 우선)
        requests = JobRequest.objects.annotate(
            status_order=Case(
                When(status='submitted', then=1),
                When(status='accepted', then=2),
                When(status='in_progress', then=3),
                When(status='completed', then=4),
                When(status='draft', then=5),
                When(status='cancelled', then=6),
                When(status='on_hold', then=7),
                default=8,
                output_field=IntegerField(),
            )
        ).order_by('status_order', '-created_at')
    else:
        # 기타 사용자: 권한이 있는 요청만
        requests = JobRequest.objects.filter(
            Q(requester=request.user) | 
            Q(requester__organization=request.user.organization)
        )
    
    breadcrumbs = [
        {'text': '대시보드', 'url': '/', 'icon': 'mdi-home'},
        {'text': '채용 요청 목록', 'url': None, 'icon': 'mdi-file-document-multiple'}
    ]
    
    context = {
        'requests': requests,
        'page_title': '채용 요청 목록',
        'breadcrumbs': breadcrumbs,
    }
    return render(request, 'workflow/job_request_list.html', context)


@login_required
@permission_required('can_create_job_request')
def job_request_create(request):
    """채용 요청 생성 뷰 - 병원 관계자만 접근 가능"""
    # 사용자 지점에 맞는 템플릿 조회
    templates = JobRequestTemplate.objects.filter(
        is_active=True
    ).filter(
        Q(branch=request.user.branch) | Q(branch__isnull=True)
    ).order_by('-is_default', 'name')
    
    if request.method == 'POST':
        form = JobRequestForm(request.POST)
        if form.is_valid():
            job_request = form.save(commit=False)
            job_request.requester = request.user
            
            # 병원/지점 정보 설정
            if form.cleaned_data.get('hospital') and form.cleaned_data.get('branch'):
                hospital = form.cleaned_data['hospital']
                branch = form.cleaned_data['branch']
                
                job_request.hospital_name = hospital.name
                job_request.hospital_branch = branch.name
                job_request.hospital_address = branch.address
                job_request.hospital_phone = branch.phone
                job_request.hospital_contact_person = branch.manager_name or request.user.get_full_name()
            
            # 포지션 템플릿 정보 설정
            if form.cleaned_data.get('position_template'):
                template = form.cleaned_data['position_template']
                job_request.position_title = template.name
                job_request.department = template.department
                job_request.employment_type = template.employment_type
                job_request.salary_min = template.salary_min
                job_request.salary_max = template.salary_max
                job_request.required_experience = template.required_experience
                job_request.preferred_qualifications = template.preferred_qualifications
                job_request.job_description = template.job_description
                job_request.working_hours = template.working_hours
                job_request.working_location = template.working_location
                job_request.special_requirements = template.special_requirements
                job_request.recruitment_period = template.recruitment_period
                job_request.urgency_level = template.urgency_level
            
            job_request.save()
            
            # 활동 로그 기록
            UserActivity.log_activity(
                user=request.user,
                activity_type='job_request_create',
                description=f'채용 요청 생성: {job_request.position_title}',
                related_object_type='JobRequest',
                related_object_id=job_request.id,
                related_object_name=job_request.position_title,
                request=request
            )
            
            messages.success(request, '채용 요청이 성공적으로 생성되었습니다.')
            return redirect('workflow:job_request_detail', request_id=job_request.id)
        else:
            messages.error(request, '폼에 오류가 있습니다. 다시 확인해주세요.')
    else:
        form = JobRequestForm()
        
        # 사용자 지점 정보로 기본값 설정
        if request.user.branch:
            form.fields['hospital'].initial = request.user.branch.hospital
            form.fields['branch'].queryset = HospitalBranch.objects.filter(hospital=request.user.branch.hospital)
            form.fields['branch'].initial = request.user.branch
    
    breadcrumbs = [
        {'text': '대시보드', 'url': '/', 'icon': 'mdi-home'},
        {'text': '채용 요청 목록', 'url': '/workflow/job-requests/', 'icon': 'mdi-file-document-multiple'},
        {'text': '새 채용 요청', 'url': None, 'icon': 'mdi-file-document-plus'}
    ]
    
    context = {
        'form': form,
        'templates': templates,
        'page_title': '새 채용 요청',
        'breadcrumbs': breadcrumbs,
        'hospitals': Hospital.objects.all(),
        'branches': HospitalBranch.objects.all(),
        'positions': PositionTemplate.objects.all(),
    }
    return render(request, 'workflow/job_request_create.html', context)


@login_required
def job_request_detail(request, request_id):
    """채용 요청 상세 뷰 - 관련 기관 사용자만 접근 가능"""
    job_request = get_object_or_404(JobRequest, id=request_id)
    
    # 권한 확인: 요청자 또는 관련 기관 사용자만 접근 가능
    if not (request.user == job_request.requester or 
            request.user.organization == job_request.requester.organization or
            request.user.is_superuser or 
            request.user.role == 'system_admin'):
        messages.error(request, '접근 권한이 없습니다.')
        return redirect('workflow:job_request_list')
    
    # 템플릿에서 사용할 수 있도록 is_editable_by_user 속성 추가
    job_request.is_editable_by_user = job_request.is_editable_by_user(request.user)
    
    # 사용자 권한 확인
    can_review_headhunting = job_request.can_be_reviewed_by_headhunting(request.user)
    can_review_hospital = job_request.can_be_reviewed_by_hospital(request.user)
    can_advance_to_workflow = (request.user.is_headhunting_user() and 
                              job_request.status == 'submitted')
    
    # 워크플로우 진행 상황 확인
    workflow_progress = None
    try:
        workflow_progress = job_request.workflow_progress
    except WorkflowProgress.DoesNotExist:
        pass
    
    breadcrumbs = [
        {'text': '대시보드', 'url': '/', 'icon': 'mdi-home'},
        {'text': '채용 요청 목록', 'url': '/workflow/job-requests/', 'icon': 'mdi-file-document-multiple'},
        {'text': f'채용 요청 #{job_request.id}', 'url': None, 'icon': 'mdi-file-document'}
    ]
    
    context = {
        'job_request': job_request,
        'page_title': f'채용 요청 상세 - #{job_request.id}',
        'breadcrumbs': breadcrumbs,
        'can_review_headhunting': can_review_headhunting,
        'can_review_hospital': can_review_hospital,
        'can_advance_to_workflow': can_advance_to_workflow,
        'workflow_progress': workflow_progress,
    }
    return render(request, 'workflow/job_request_detail.html', context)


@login_required
@permission_required('can_edit_job_request')
def job_request_edit(request, request_id):
    """채용 요청 수정 뷰 - 병원 관계자만 접근 가능"""
    job_request = get_object_or_404(JobRequest, id=request_id)
    
    # 수정 권한 확인
    if not job_request.is_editable_by_user:
        messages.error(request, '이 요청을 수정할 권한이 없거나 요청이 잠겨있습니다.')
        return redirect('workflow:job_request_detail', request_id=job_request.id)
    
    if request.method == 'POST':
        form = JobRequestForm(request.POST, instance=job_request)
        if form.is_valid():
            form.save()
            
            # 활동 로그 기록
            UserActivity.log_activity(
                user=request.user,
                activity_type='job_request_update',
                description=f'채용 요청 수정: {job_request.position_title}',
                related_object_type='JobRequest',
                related_object_id=job_request.id,
                related_object_name=job_request.position_title,
                request=request
            )
            
            messages.success(request, '채용 요청이 성공적으로 수정되었습니다.')
            return redirect('workflow:job_request_detail', request_id=job_request.id)
    else:
        form = JobRequestForm(instance=job_request)
    
    breadcrumbs = [
        {'text': '대시보드', 'url': '/', 'icon': 'mdi-home'},
        {'text': '채용 요청 목록', 'url': '/workflow/job-requests/', 'icon': 'mdi-file-document-multiple'},
        {'text': f'채용 요청 #{job_request.id}', 'url': f'/workflow/job-requests/{job_request.id}/', 'icon': 'mdi-file-document'},
        {'text': '수정', 'url': None, 'icon': 'mdi-file-document-edit'}
    ]
    
    context = {
        'form': form,
        'job_request': job_request,
        'page_title': f'채용 요청 수정 - #{job_request.id}',
        'breadcrumbs': breadcrumbs,
    }
    return render(request, 'workflow/job_request_edit.html', context)


@login_required
@permission_required('can_submit_job_request')
def job_request_submit(request, request_id):
    """채용 요청 제출 뷰 - 병원 관계자만 접근 가능"""
    job_request = get_object_or_404(JobRequest, id=request_id)
    
    # 제출 권한 확인
    if not job_request.is_editable_by_user:
        messages.error(request, '이 요청을 제출할 권한이 없거나 요청이 잠겨있습니다.')
        return redirect('workflow:job_request_detail', request_id=job_request.id)
    
    if request.method == 'POST':
        job_request.status = 'submitted'
        job_request.submitted_at = timezone.now()
        job_request.save()
        
        # 활동 로그 기록
        UserActivity.log_activity(
            user=request.user,
            activity_type='job_request_submit',
            description=f'채용 요청 제출: {job_request.position_title}',
            related_object_type='JobRequest',
            related_object_id=job_request.id,
            related_object_name=job_request.position_title,
            request=request
        )
        
        messages.success(request, '채용 요청이 성공적으로 제출되었습니다.')
        return redirect('workflow:job_request_detail', request_id=job_request.id)
    
    breadcrumbs = [
        {'text': '대시보드', 'url': '/', 'icon': 'mdi-home'},
        {'text': '채용 요청 목록', 'url': '/workflow/job-requests/', 'icon': 'mdi-file-document-multiple'},
        {'text': f'채용 요청 #{job_request.id}', 'url': f'/workflow/job-requests/{job_request.id}/', 'icon': 'mdi-file-document'},
        {'text': '제출', 'url': None, 'icon': 'mdi-send'}
    ]
    
    context = {
        'job_request': job_request,
        'page_title': f'채용 요청 제출 - #{job_request.id}',
        'breadcrumbs': breadcrumbs,
    }
    return render(request, 'workflow/job_request_submit.html', context)


@login_required
def workflow_list(request):
    """워크플로우 목록 뷰 - 접근 가능한 워크플로우만 표시"""
    workflows = request.user.get_accessible_workflows().order_by('-created_at')
    paginator = Paginator(workflows, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # 통계 데이터
    accessible_workflows = request.user.get_accessible_workflows()
    stats = {
        'in_progress': accessible_workflows.filter(status='in_progress').count(),
        'completed': accessible_workflows.filter(status='completed').count(),
        'overdue': accessible_workflows.filter(status='overdue').count(),
        'total': accessible_workflows.count(),
        'in_progress_growth': 5,  # 임시 데이터
        'completed_growth': 12,
        'overdue_growth': -3,
        'total_growth': 8,
    }
    
    breadcrumbs = [
        {'text': '대시보드', 'url': '/', 'icon': 'mdi-home'},
        {'text': '채용 목록', 'url': None, 'icon': 'mdi-briefcase-multiple'}
    ]
    
    context = {
        'workflows': page_obj,
        'page_obj': page_obj,
        'is_paginated': paginator.num_pages > 1,
        'stats': stats,
        'page_title': '채용 목록',
        'breadcrumbs': breadcrumbs,
    }
    return render(request, 'workflow/workflow_list.html', context)


@login_required
@permission_required('can_manage_workflow')
def workflow_create(request):
    """워크플로우 생성 뷰 - 권한이 있는 사용자만 접근 가능"""
    if request.method == 'POST':
        form = WorkflowForm(request.POST)
        if form.is_valid():
            workflow = form.save(commit=False)
            workflow.created_by = request.user
            workflow.assigned_to = request.user  # 담당자를 현재 사용자로 설정
            
            # 채용 요청이 선택된 경우 제목과 설명 자동 설정
            job_request = form.cleaned_data.get('job_request')
            if job_request:
                if not workflow.title:
                    workflow.title = f"{job_request.position_title} - {job_request.hospital_name} {job_request.hospital_branch}"
                if not workflow.description:
                    workflow.description = f"병원: {job_request.hospital_name} {job_request.hospital_branch}\n포지션: {job_request.position_title}\n부서: {job_request.department}\n고용형태: {job_request.get_employment_type_display()}\n업무내용: {job_request.job_description[:200]}..."
            
            workflow.save()
            
            # 활동 로그 기록
            UserActivity.log_activity(
                user=request.user,
                activity_type='workflow_create',
                description=f'워크플로우 생성: {workflow.title}',
                related_object_type='Workflow',
                related_object_id=workflow.id,
                related_object_name=workflow.title,
                request=request
            )
            
            # 기본 워크플로우 단계 생성
            default_steps = [
                {'name': '채용 요청', 'order': 1, 'description': '채용 요청서 작성 및 제출'},
                {'name': '구인 공고', 'order': 2, 'description': '채용 공고 작성 및 게시'},
                {'name': '서류 심사', 'order': 3, 'description': '지원자 서류 검토 및 선별'},
                {'name': '면접 일정', 'order': 4, 'description': '면접 일정 조율 및 확정'},
                {'name': '면접 평가', 'order': 5, 'description': '면접 진행 및 평가'},
                {'name': '합격자 관리', 'order': 6, 'description': '합격자 선정 및 관리'},
            ]
            
            for step_data in default_steps:
                WorkflowStep.objects.create(
                    workflow=workflow,
                    name=step_data['name'],
                    order=step_data['order'],
                    description=step_data['description']
                )
            
            messages.success(request, '워크플로우가 성공적으로 생성되었습니다.')
            return redirect('workflow:detail', workflow_id=workflow.id)
    else:
        form = WorkflowForm()
    
    breadcrumbs = [
        {'text': '대시보드', 'url': '/', 'icon': 'mdi-home'},
        {'text': '채용 목록', 'url': '/workflow/', 'icon': 'mdi-briefcase-multiple'},
        {'text': '새 채용', 'url': None, 'icon': 'mdi-briefcase-plus'}
    ]
    
    context = {
        'form': form,
        'page_title': '새 채용',
        'breadcrumbs': breadcrumbs,
    }
    return render(request, 'workflow/workflow_form.html', context)


@login_required
def workflow_detail(request, workflow_id):
    workflow = get_object_or_404(Workflow, id=workflow_id)
    
    breadcrumbs = [
        {'text': '대시보드', 'url': '/', 'icon': 'mdi-home'},
        {'text': '채용 목록', 'url': '/workflow/', 'icon': 'mdi-briefcase-multiple'},
        {'text': f'채용 #{workflow.id}', 'url': None, 'icon': 'mdi-briefcase'}
    ]
    
    context = {
        'workflow': workflow,
        'page_title': f'채용 상세 - #{workflow.id}',
        'breadcrumbs': breadcrumbs,
    }
    return render(request, 'workflow/workflow_detail.html', context)


@login_required
def workflow_update(request, workflow_id):
    workflow = get_object_or_404(Workflow, id=workflow_id)
    if request.method == 'POST':
        form = WorkflowForm(request.POST, instance=workflow)
        if form.is_valid():
            form.save()
            messages.success(request, '워크플로우가 성공적으로 업데이트되었습니다.')
            return redirect('workflow:detail', workflow_id=workflow.id)
    else:
        form = WorkflowForm(instance=workflow)
    
    breadcrumbs = [
        {'text': '대시보드', 'url': '/', 'icon': 'mdi-home'},
        {'text': '채용 목록', 'url': '/workflow/', 'icon': 'mdi-briefcase-multiple'},
        {'text': f'채용 #{workflow.id}', 'url': f'/workflow/{workflow.id}/', 'icon': 'mdi-briefcase'},
        {'text': '수정', 'url': None, 'icon': 'mdi-briefcase-edit'}
    ]
    
    context = {
        'form': form,
        'workflow': workflow,
        'page_title': f'채용 수정 - #{workflow.id}',
        'breadcrumbs': breadcrumbs,
    }
    return render(request, 'workflow/workflow_form.html', context)


@login_required
def workflow_delete(request, workflow_id):
    workflow = get_object_or_404(Workflow, id=workflow_id)
    if request.method == 'POST':
        workflow.delete()
        messages.success(request, '워크플로우가 성공적으로 삭제되었습니다.')
        return redirect('workflow:list')
    
    breadcrumbs = [
        {'text': '대시보드', 'url': '/', 'icon': 'mdi-home'},
        {'text': '채용 목록', 'url': '/workflow/', 'icon': 'mdi-briefcase-multiple'},
        {'text': f'채용 #{workflow.id}', 'url': f'/workflow/{workflow.id}/', 'icon': 'mdi-briefcase'},
        {'text': '삭제', 'url': None, 'icon': 'mdi-delete'}
    ]
    
    context = {
        'workflow': workflow,
        'page_title': f'채용 삭제 - #{workflow.id}',
        'breadcrumbs': breadcrumbs,
    }
    return render(request, 'workflow/workflow_confirm_delete.html', context)


@login_required
@require_POST
@csrf_exempt
def workflow_advance(request, workflow_id):
    try:
        workflow = get_object_or_404(Workflow, id=workflow_id)
        # 워크플로우 진행 로직
        workflow.advance_to_next_step()
        return JsonResponse({'success': True})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})


@login_required
@require_POST
@csrf_exempt
def step_start(request, step_id):
    """워크플로우 단계 시작"""
    try:
        step = get_object_or_404(WorkflowStep, id=step_id)
        if step.status == 'pending':
            step.status = 'in_progress'
            step.started_at = timezone.now()
            step._changed_by = request.user.id
            step.save()
            
            # 활동 로그 기록
            UserActivity.log_activity(
                user=request.user,
                activity_type='step_start',
                description=f'워크플로우 단계 "{step.name}" 시작',
                related_object_type='WorkflowStep',
                related_object_id=step.id,
                related_object_name=step.name,
                request=request
            )
            
            return JsonResponse({'success': True, 'status': step.status})
        else:
            return JsonResponse({'success': False, 'error': '이미 진행 중인 단계입니다.'})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})


@login_required
@require_POST
@csrf_exempt
def step_complete(request, step_id):
    """워크플로우 단계 완료"""
    try:
        step = get_object_or_404(WorkflowStep, id=step_id)
        if step.status == 'in_progress':
            step.status = 'completed'
            step.completed_at = timezone.now()
            step._changed_by = request.user.id
            step.save()
            
            # 활동 로그 기록
            UserActivity.log_activity(
                user=request.user,
                activity_type='step_complete',
                description=f'워크플로우 단계 "{step.name}" 완료',
                related_object_type='WorkflowStep',
                related_object_id=step.id,
                related_object_name=step.name,
                request=request
            )
            
            return JsonResponse({'success': True, 'status': step.status})
        else:
            return JsonResponse({'success': False, 'error': '완료할 수 없는 단계입니다.'})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})


@login_required
@require_POST
@csrf_exempt
def step_revert(request, step_id):
    """워크플로우 단계 상태 되돌리기"""
    step = get_object_or_404(WorkflowStep, id=step_id)
    
    # 권한 확인
    if not (request.user == step.workflow.assigned_to or 
            request.user == step.workflow.created_by or
            request.user.is_superuser or 
            request.user.role == 'system_admin'):
        return JsonResponse({
            'success': False,
            'message': '상태를 되돌릴 권한이 없습니다.'
        })
    
    # 상태 되돌리기 가능 여부 확인
    if not step.can_revert_status():
        return JsonResponse({
            'success': False,
            'message': '되돌릴 수 있는 이전 상태가 없습니다.'
        })
    
    # 상태 되돌리기 실행
    success, message = step.revert_to_previous_status(request.user, request)
    
    if success:
        # 활동 로그 기록
        UserActivity.log_activity(
            user=request.user,
            activity_type='workflow_step_revert',
            description=f'워크플로우 단계 상태 되돌리기: {step.name}',
            related_object_type='WorkflowStep',
            related_object_id=step.id,
            related_object_name=step.name,
            request=request
        )
    
    return JsonResponse({
        'success': success,
        'message': message,
        'new_status': step.status,
        'new_status_display': step.get_status_display(),
        'can_revert': step.can_revert_status()
    })


@login_required
@require_POST
@csrf_exempt
def step_revert_status(request, step_id):
    """워크플로우 단계 상태 되돌리기 (새로운 뷰)"""
    step = get_object_or_404(WorkflowStep, id=step_id)
    
    # 권한 확인
    if not (request.user == step.workflow.assigned_to or 
            request.user == step.workflow.created_by or
            request.user.is_superuser or 
            request.user.role == 'system_admin'):
        messages.error(request, '상태를 되돌릴 권한이 없습니다.')
        return redirect('workflow:step_detail', step_id=step.id)
    
    # 상태 되돌리기 가능 여부 확인
    if not step.can_revert_status():
        messages.error(request, '되돌릴 수 있는 이전 상태가 없습니다.')
        return redirect('workflow:step_detail', step_id=step.id)
    
    # 상태 되돌리기 실행
    success, message = step.revert_to_previous_status(request.user, request)
    
    if success:
        # 활동 로그 기록
        UserActivity.log_activity(
            user=request.user,
            activity_type='workflow_step_revert',
            description=f'워크플로우 단계 상태 되돌리기: {step.name}',
            related_object_type='WorkflowStep',
            related_object_id=step.id,
            related_object_name=step.name,
            request=request
        )
        messages.success(request, message)
    else:
        messages.error(request, message)
    
    return redirect('workflow:step_detail', step_id=step.id)


@login_required
def step_detail(request, step_id):
    step = get_object_or_404(WorkflowStep, id=step_id)
    users = User.objects.all()
    return render(request, 'workflow/step_detail.html', {'step': step, 'users': users})


@login_required
@require_POST
@csrf_exempt
def step_update_status(request, step_id):
    """워크플로우 단계 상태 업데이트"""
    try:
        import json
        step = get_object_or_404(WorkflowStep, id=step_id)
        data = json.loads(request.body)
        new_status = data.get('status')
        
        if new_status in ['pending', 'in_progress', 'completed', 'cancelled', 'on_hold']:
            step.status = new_status
            
            # 상태에 따른 시간 설정
            if new_status == 'in_progress' and not step.started_at:
                step.started_at = timezone.now()
            elif new_status == 'completed':
                step.completed_at = timezone.now()
            
            step.save()
            return JsonResponse({'success': True})
        else:
            return JsonResponse({'success': False, 'error': 'Invalid status'})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})


@login_required
@require_POST
@csrf_exempt
def document_delete(request, document_id):
    try:
        document = get_object_or_404(WorkflowDocument, id=document_id)
        document.delete()
        return JsonResponse({'success': True})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})


@login_required
def job_request_add_additional_request(request, request_id):
    """채용 요청에 추가 요청사항 추가"""
    job_request = get_object_or_404(JobRequest, id=request_id)
    
    if request.method == 'POST':
        request_text = request.POST.get('additional_request_text', '').strip()
        if request_text:
            if job_request.add_additional_request(request_text, request.user):
                messages.success(request, '추가 요청사항이 성공적으로 등록되었습니다.')
            else:
                messages.error(request, '요청이 잠겨있어 추가 요청사항을 등록할 수 없습니다.')
        else:
            messages.error(request, '추가 요청사항 내용을 입력해주세요.')
        
        return redirect('workflow:job_request_detail', request_id=job_request.id)
    
    return render(request, 'workflow/job_request_add_additional_request.html', {
        'job_request': job_request
    })


@login_required
def job_request_lock(request, request_id):
    """채용 요청 잠금"""
    job_request = get_object_or_404(JobRequest, id=request_id)
    
    if request.method == 'POST':
        if job_request.lock_request(request.user):
            messages.success(request, '채용 요청이 잠겨 수정할 수 없습니다.')
        else:
            messages.error(request, '이미 잠겨있거나 잠금 처리할 수 없습니다.')
        
        return redirect('workflow:job_request_detail', request_id=job_request.id)
    
    return render(request, 'workflow/job_request_lock_confirm.html', {
        'job_request': job_request
    })


@login_required
def job_request_unlock(request, request_id):
    """채용 요청 잠금 해제 (관리자만)"""
    job_request = get_object_or_404(JobRequest, id=request_id)
    
    if not (request.user.is_staff or request.user.is_superuser):
        messages.error(request, '잠금 해제 권한이 없습니다.')
        return redirect('workflow:job_request_detail', request_id=job_request.id)
    
    if request.method == 'POST':
        if job_request.unlock_request(request.user):
            messages.success(request, '채용 요청 잠금이 해제되었습니다.')
        else:
            messages.error(request, '잠금 해제에 실패했습니다.')
        
        return redirect('workflow:job_request_detail', request_id=job_request.id)
    
    return render(request, 'workflow/job_request_unlock_confirm.html', {
        'job_request': job_request
    })


@login_required
@require_POST
@csrf_exempt
def job_request_add_additional_request_ajax(request, request_id):
    """AJAX로 추가 요청사항 추가"""
    try:
        job_request = get_object_or_404(JobRequest, id=request_id)
        request_text = request.POST.get('request_text', '').strip()
        
        if not request_text:
            return JsonResponse({'success': False, 'error': '요청 내용을 입력해주세요.'})
        
        job_request.add_additional_request(request_text, request.user)
        
        return JsonResponse({
            'success': True, 
            'message': '추가 요청사항이 성공적으로 추가되었습니다.',
            'additional_requests_count': job_request.get_additional_requests_count()
        })
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})


@login_required
def get_job_request_data(request, request_id):
    """채용 요청 데이터를 JSON으로 반환하는 API"""
    try:
        job_request = get_object_or_404(JobRequest, id=request_id)
        
        data = {
            'success': True,
            'job_request': {
                'id': job_request.id,
                'request_id': job_request.request_id,
                'hospital_name': job_request.hospital_name,
                'hospital_branch': job_request.hospital_branch,
                'position_title': job_request.position_title,
                'department': job_request.department,
                'employment_type': job_request.employment_type,
                'employment_type_display': job_request.get_employment_type_display(),
                'job_description': job_request.job_description,
                'salary_min': job_request.salary_min,
                'salary_max': job_request.salary_max,
                'required_experience': job_request.required_experience,
                'preferred_qualifications': job_request.preferred_qualifications,
                'working_hours': job_request.working_hours,
                'working_location': job_request.working_location,
                'special_requirements': job_request.special_requirements,
                'urgency_level': job_request.urgency_level,
                'status': job_request.status,
                'created_at': job_request.created_at.strftime('%Y-%m-%d %H:%M'),
            }
        }
        
        return JsonResponse(data)
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})


@login_required
def workflow_status_reset(request, workflow_id):
    """워크플로우 상태 되돌리기"""
    workflow = get_object_or_404(Workflow, id=workflow_id)
    if request.method == 'POST':
        workflow.reset_status()
        messages.success(request, '워크플로우가 성공적으로 상태가 되돌아갔습니다.')
        return redirect('workflow:detail', workflow_id=workflow.id)
    
    return render(request, 'workflow/workflow_status_reset_confirm.html', {'workflow': workflow})


@login_required
def workflow_activity_log(request, workflow_id):
    """워크플로우 활동 로그 뷰"""
    workflow = get_object_or_404(Workflow, id=workflow_id)
    
    # 권한 확인
    if not (request.user == workflow.assigned_to or 
            request.user == workflow.created_by or
            request.user.is_superuser or 
            request.user.role == 'system_admin'):
        messages.error(request, '활동 로그를 볼 권한이 없습니다.')
        return redirect('workflow:workflow_detail', workflow_id=workflow.id)
    
    # 액션 로그 조회
    action_logs = workflow.action_logs.all().order_by('-performed_at')
    
    # 페이지네이션
    paginator = Paginator(action_logs, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    breadcrumbs = [
        {'text': '대시보드', 'url': '/', 'icon': 'mdi-home'},
        {'text': '워크플로우 목록', 'url': '/workflow/', 'icon': 'mdi-workflow'},
        {'text': workflow.title, 'url': f'/workflow/{workflow.id}/', 'icon': 'mdi-workflow'},
        {'text': '활동 로그', 'url': None, 'icon': 'mdi-history'}
    ]
    
    context = {
        'workflow': workflow,
        'page_obj': page_obj,
        'page_title': f'활동 로그 - {workflow.title}',
        'breadcrumbs': breadcrumbs,
    }
    return render(request, 'workflow/workflow_activity_log.html', context)


@login_required
def job_posting_list(request):
    """채용 공고 목록"""
    postings = JobPosting.objects.select_related('job_request', 'created_by').all()
    
    # 필터링
    status = request.GET.get('status')
    if status:
        postings = postings.filter(status=status)
    
    platform = request.GET.get('platform')
    if platform:
        postings = postings.filter(posting_platform=platform)
    
    # 검색
    search = request.GET.get('search')
    if search:
        postings = postings.filter(
            Q(title__icontains=search) |
            Q(summary__icontains=search) |
            Q(job_request__position_title__icontains=search)
        )
    
    # 정렬
    sort_by = request.GET.get('sort', '-created_at')
    postings = postings.order_by(sort_by)
    
    # 페이지네이션
    paginator = Paginator(postings, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
        'status_choices': JobPosting.POSTING_STATUS_CHOICES,
        'platform_choices': [
            ('jobkorea', '잡코리아'),
            ('saramin', '사람인'),
            ('incruit', '인크루트'),
            ('wanted', '원티드'),
            ('linkedin', '링크드인'),
            ('indeed', '인디드'),
            ('other', '기타')
        ]
    }
    return render(request, 'workflow/job_posting_list.html', context)


@login_required
def job_posting_detail(request, posting_id):
    """채용 공고 상세"""
    try:
        posting = JobPosting.objects.select_related(
            'job_request', 'created_by'
        ).prefetch_related('applications').get(id=posting_id)
    except JobPosting.DoesNotExist:
        messages.error(request, '채용 공고를 찾을 수 없습니다.')
        return redirect('workflow:job_posting_list')
    
    # 조회수 증가
    posting.increment_view_count()
    
    context = {
        'posting': posting,
        'applications': posting.applications.all()[:10],  # 최근 10개 지원
        'can_edit': request.user == posting.created_by or request.user.is_staff
    }
    return render(request, 'workflow/job_posting_detail.html', context)


@login_required
def job_posting_create(request, job_request_id):
    """채용 공고 생성"""
    try:
        job_request = JobRequest.objects.get(id=job_request_id)
    except JobRequest.DoesNotExist:
        messages.error(request, '채용 요청을 찾을 수 없습니다.')
        return redirect('workflow:job_request_list')
    
    # 이미 채용 공고가 있는지 확인
    if hasattr(job_request, 'job_posting'):
        messages.warning(request, '이미 채용 공고가 존재합니다.')
        return redirect('workflow:job_posting_detail', posting_id=job_request.job_posting.id)
    
    if request.method == 'POST':
        form = JobPostingForm(request.POST, request.FILES)
        if form.is_valid():
            posting = form.save(commit=False)
            posting.job_request = job_request
            posting.created_by = request.user
            posting.save()
            
            messages.success(request, '채용 공고가 성공적으로 생성되었습니다.')
            return redirect('workflow:job_posting_detail', posting_id=posting.id)
    else:
        form = JobPostingForm()
        # 채용 요청 정보를 기본값으로 설정
        form.fields['title'].initial = f"{job_request.position_title} - {job_request.hospital_name}"
        form.fields['summary'].initial = job_request.job_description[:200] + "..." if len(job_request.job_description) > 200 else job_request.job_description
        form.fields['detailed_description'].initial = job_request.job_description
        form.fields['requirements'].initial = job_request.required_experience
    
    context = {
        'form': form,
        'job_request': job_request
    }
    return render(request, 'workflow/job_posting_form.html', context)


@login_required
def job_posting_update(request, posting_id):
    """채용 공고 수정 (실제 게시 정보만)"""
    try:
        posting = JobPosting.objects.get(id=posting_id)
    except JobPosting.DoesNotExist:
        messages.error(request, '채용 공고를 찾을 수 없습니다.')
        return redirect('workflow:job_posting_list')
    
    # 권한 확인
    if request.user != posting.created_by and not request.user.is_staff:
        messages.error(request, '수정 권한이 없습니다.')
        return redirect('workflow:job_posting_detail', posting_id=posting.id)
    
    if request.method == 'POST':
        form = JobPostingUpdateForm(request.POST, request.FILES, instance=posting)
        if form.is_valid():
            form.save()
            messages.success(request, '채용 공고가 성공적으로 수정되었습니다.')
            return redirect('workflow:job_posting_detail', posting_id=posting.id)
    else:
        form = JobPostingUpdateForm(instance=posting)
    
    context = {
        'form': form,
        'posting': posting
    }
    return render(request, 'workflow/job_posting_update.html', context)


@login_required
def job_posting_publish(request, posting_id):
    """채용 공고 게시"""
    try:
        posting = JobPosting.objects.get(id=posting_id)
    except JobPosting.DoesNotExist:
        messages.error(request, '채용 공고를 찾을 수 없습니다.')
        return redirect('workflow:job_posting_list')
    
    if request.method == 'POST':
        posting.status = 'published'
        posting.published_at = timezone.now()
        posting.save()
        
        messages.success(request, '채용 공고가 게시되었습니다.')
        return redirect('workflow:job_posting_detail', posting_id=posting.id)
    
    return redirect('workflow:job_posting_detail', posting_id=posting.id)


@login_required
def job_posting_close(request, posting_id):
    """채용 공고 마감"""
    try:
        posting = JobPosting.objects.get(id=posting_id)
    except JobPosting.DoesNotExist:
        messages.error(request, '채용 공고를 찾을 수 없습니다.')
        return redirect('workflow:job_posting_list')
    
    if request.method == 'POST':
        posting.status = 'closed'
        posting.save()
        
        messages.success(request, '채용 공고가 마감되었습니다.')
        return redirect('workflow:job_posting_detail', posting_id=posting.id)
    
    return redirect('workflow:job_posting_detail', posting_id=posting.id)


@login_required
def job_application_create(request, posting_id):
    """구인 공고 지원"""
    try:
        posting = JobPosting.objects.get(id=posting_id)
    except JobPosting.DoesNotExist:
        messages.error(request, '채용 공고를 찾을 수 없습니다.')
        return redirect('workflow:job_posting_list')
    
    # 이미 지원했는지 확인
    if posting.applications.filter(applicant=request.user).exists():
        messages.warning(request, '이미 지원한 채용 공고입니다.')
        return redirect('workflow:job_posting_detail', posting_id=posting.id)
    
    if request.method == 'POST':
        form = JobApplicationForm(request.POST, request.FILES)
        if form.is_valid():
            application = form.save(commit=False)
            application.job_posting = posting
            application.applicant = request.user
            application.save()
            
            # 지원자 수 증가
            posting.increment_application_count()
            
            messages.success(request, '지원이 완료되었습니다.')
            return redirect('workflow:job_posting_detail', posting_id=posting.id)
    else:
        form = JobApplicationForm()
    
    context = {
        'form': form,
        'posting': posting
    }
    return render(request, 'workflow/job_application_form.html', context)


@login_required
def job_application_list(request, posting_id):
    """구인 공고 지원자 목록"""
    try:
        posting = JobPosting.objects.get(id=posting_id)
    except JobPosting.DoesNotExist:
        messages.error(request, '채용 공고를 찾을 수 없습니다.')
        return redirect('workflow:job_posting_list')
    
    # 권한 확인
    if request.user != posting.created_by and not request.user.is_staff:
        messages.error(request, '접근 권한이 없습니다.')
        return redirect('workflow:job_posting_detail', posting_id=posting.id)
    
    applications = posting.applications.select_related('applicant').all()
    
    # 필터링
    status = request.GET.get('status')
    if status:
        applications = applications.filter(status=status)
    
    # 검색
    search = request.GET.get('search')
    if search:
        applications = applications.filter(
            Q(applicant__first_name__icontains=search) |
            Q(applicant__last_name__icontains=search) |
            Q(applicant__email__icontains=search)
        )
    
    # 정렬
    sort_by = request.GET.get('sort', '-submitted_at')
    applications = applications.order_by(sort_by)
    
    # 페이지네이션
    paginator = Paginator(applications, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'posting': posting,
        'page_obj': page_obj,
        'status_choices': JobApplication.APPLICATION_STATUS_CHOICES
    }
    return render(request, 'workflow/job_application_list.html', context)


@login_required
def job_application_detail(request, application_id):
    """구인 공고 지원 상세"""
    try:
        application = JobApplication.objects.select_related(
            'job_posting', 'applicant'
        ).get(id=application_id)
    except JobApplication.DoesNotExist:
        messages.error(request, '지원 내역을 찾을 수 없습니다.')
        return redirect('workflow:job_posting_list')
    
    # 권한 확인
    can_view = (
        request.user == application.applicant or
        request.user == application.job_posting.created_by or
        request.user.is_staff
    )
    
    if not can_view:
        messages.error(request, '접근 권한이 없습니다.')
        return redirect('workflow:job_posting_detail', posting_id=application.job_posting.id)
    
    context = {
        'application': application,
        'can_edit': request.user == application.job_posting.created_by or request.user.is_staff
    }
    return render(request, 'workflow/job_application_detail.html', context)


@login_required
def template_list(request):
    """채용 요청 템플릿 목록"""
    templates = JobRequestTemplate.objects.filter(is_active=True).order_by('-is_default', 'name')
    
    context = {
        'templates': templates,
    }
    return render(request, 'workflow/template_list.html', context)


@login_required
def template_create(request):
    """채용 요청 템플릿 생성"""
    if request.method == 'POST':
        form = JobRequestTemplateForm(request.POST)
        if form.is_valid():
            template = form.save(commit=False)
            template.created_by = request.user
            template.save()
            messages.success(request, '템플릿이 성공적으로 생성되었습니다.')
            return redirect('workflow:template_list')
    else:
        form = JobRequestTemplateForm()
    
    context = {
        'form': form,
        'title': '새 템플릿 생성'
    }
    return render(request, 'workflow/template_form.html', context)


@login_required
def template_update(request, pk):
    """채용 요청 템플릿 수정"""
    template = get_object_or_404(JobRequestTemplate, pk=pk)
    
    if request.method == 'POST':
        form = JobRequestTemplateForm(request.POST, instance=template)
        if form.is_valid():
            form.save()
            messages.success(request, '템플릿이 성공적으로 수정되었습니다.')
            return redirect('workflow:template_list')
    else:
        form = JobRequestTemplateForm(instance=template)
    
    context = {
        'form': form,
        'template': template,
        'title': '템플릿 수정'
    }
    return render(request, 'workflow/template_form.html', context)


@login_required
def template_delete(request, pk):
    """채용 요청 템플릿 삭제"""
    template = get_object_or_404(JobRequestTemplate, pk=pk)
    
    if request.method == 'POST':
        template.is_active = False
        template.save()
        messages.success(request, '템플릿이 삭제되었습니다.')
        return redirect('workflow:template_list')
    
    context = {
        'template': template,
    }
    return render(request, 'workflow/template_confirm_delete.html', context)


@login_required
def template_detail(request, pk):
    """채용 요청 템플릿 상세"""
    template = get_object_or_404(JobRequestTemplate, pk=pk)
    
    context = {
        'template': template,
    }
    return render(request, 'workflow/template_detail.html', context)


@login_required
def job_request_create_from_template(request, template_pk):
    """템플릿에서 채용 요청 생성"""
    template = get_object_or_404(JobRequestTemplate, pk=template_pk, is_active=True)
    
    # 권한 확인: 템플릿이 사용자의 지점에 속하거나 공통 템플릿인 경우
    if template.branch and template.branch != request.user.branch:
        messages.error(request, '이 템플릿에 접근할 권한이 없습니다.')
        return redirect('workflow:job_request_create')
    
    if request.method == 'POST':
        # 템플릿에서 채용 요청 생성
        job_request = template.create_job_request_from_template(
            requester=request.user,
            # 사용자가 입력한 값으로 덮어쓰기
            hospital_name=request.POST.get('hospital_name', template.hospital_name),
            hospital_branch=request.POST.get('hospital_branch', template.hospital_branch),
            hospital_address=request.POST.get('hospital_address', template.hospital_address),
            hospital_phone=request.POST.get('hospital_phone', template.hospital_phone),
            hospital_contact_person=request.POST.get('hospital_contact_person', template.hospital_contact_person),
            position_title=request.POST.get('position_title', template.position_title),
            department=request.POST.get('department', template.department),
            employment_type=request.POST.get('employment_type', template.employment_type),
            salary_min=request.POST.get('salary_min', template.salary_min),
            salary_max=request.POST.get('salary_max', template.salary_max),
            required_experience=request.POST.get('required_experience', template.required_experience),
            preferred_qualifications=request.POST.get('preferred_qualifications', template.preferred_qualifications),
            job_description=request.POST.get('job_description', template.job_description),
            working_hours=request.POST.get('working_hours', template.working_hours),
            working_location=request.POST.get('working_location', template.working_location),
            special_requirements=request.POST.get('special_requirements', template.special_requirements),
            expected_start_date=request.POST.get('expected_start_date', template.expected_start_date),
            recruitment_period=request.POST.get('recruitment_period', template.recruitment_period),
            urgency_level=request.POST.get('urgency_level', template.urgency_level),
        )
        
        # 활동 로그 기록
        UserActivity.log_activity(
            user=request.user,
            activity_type='job_request_create',
            description=f'템플릿에서 채용 요청 생성: {job_request.position_title} (템플릿: {template.name})',
            related_object_type='JobRequest',
            related_object_id=job_request.id,
            related_object_name=job_request.position_title,
            request=request
        )
        
        messages.success(request, f'"{template.name}" 템플릿을 사용하여 채용 요청이 성공적으로 생성되었습니다.')
        return redirect('workflow:job_request_detail', request_id=job_request.id)
    
    # 템플릿 데이터로 폼 초기화
    form = JobRequestForm(initial={
        'hospital_name': template.hospital_name,
        'hospital_branch': template.hospital_branch,
        'hospital_address': template.hospital_address,
        'hospital_phone': template.hospital_phone,
        'hospital_contact_person': template.hospital_contact_person,
        'position_title': template.position_title,
        'department': template.department,
        'employment_type': template.employment_type,
        'salary_min': template.salary_min,
        'salary_max': template.salary_max,
        'required_experience': template.required_experience,
        'preferred_qualifications': template.preferred_qualifications,
        'job_description': template.job_description,
        'working_hours': template.working_hours,
        'working_location': template.working_location,
        'special_requirements': template.special_requirements,
        'expected_start_date': template.expected_start_date,
        'recruitment_period': template.recruitment_period,
        'urgency_level': template.urgency_level,
    })
    
    breadcrumbs = [
        {'text': '대시보드', 'url': '/', 'icon': 'mdi-home'},
        {'text': '채용 요청 목록', 'url': '/workflow/job-requests/', 'icon': 'mdi-file-document-multiple'},
        {'text': '새 채용 요청', 'url': '/workflow/job-requests/create/', 'icon': 'mdi-file-document-plus'},
        {'text': f'템플릿 사용: {template.name}', 'url': None, 'icon': 'mdi-file-document-edit'}
    ]
    
    context = {
        'form': form,
        'template': template,
        'page_title': f'템플릿 사용: {template.name}',
        'breadcrumbs': breadcrumbs,
        'hospitals': Hospital.objects.filter(is_active=True),
        'branches': HospitalBranch.objects.filter(is_active=True),
    }
    return render(request, 'workflow/job_request_create_from_template.html', context)


class JobRequestCreateView(LoginRequiredMixin, CreateView):
    model = JobRequest
    form_class = JobRequestForm
    template_name = 'workflow/job_request_create.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['page_title'] = '새 채용 요청'
        return context


@login_required
@require_POST
@csrf_exempt
def job_request_review_headhunting(request, request_id):
    """채용담당 회사에서 채용 요청 확인 처리"""
    job_request = get_object_or_404(JobRequest, id=request_id)
    
    # 권한 확인
    if not job_request.can_be_reviewed_by_headhunting(request.user):
        messages.error(request, '이 요청을 확인할 권한이 없습니다.')
        return JsonResponse({'success': False, 'message': '권한이 없습니다.'})
    
    # 이미 확인했는지 확인
    if job_request.reviewed_by_headhunting:
        messages.warning(request, '이미 확인한 요청입니다.')
        return JsonResponse({'success': False, 'message': '이미 확인한 요청입니다.'})
    
    # 확인 처리
    notes = request.POST.get('notes', '')
    job_request.mark_as_reviewed_by_headhunting(request.user, notes)
    
    messages.success(request, '채용 요청을 확인했습니다.')
    return JsonResponse({
        'success': True, 
        'message': '확인 완료',
        'reviewed_at': job_request.reviewed_at.strftime('%Y-%m-%d %H:%M'),
        'reviewer': request.user.get_full_name()
    })


@login_required
@require_POST
@csrf_exempt
def job_request_review_hospital(request, request_id):
    """병원 담당자에서 채용 요청 확인 처리"""
    job_request = get_object_or_404(JobRequest, id=request_id)
    
    # 권한 확인
    if not job_request.can_be_reviewed_by_hospital(request.user):
        messages.error(request, '이 요청을 확인할 권한이 없습니다.')
        return JsonResponse({'success': False, 'message': '권한이 없습니다.'})
    
    # 이미 확인했는지 확인
    if job_request.reviewed_by_hospital:
        messages.warning(request, '이미 확인한 요청입니다.')
        return JsonResponse({'success': False, 'message': '이미 확인한 요청입니다.'})
    
    # 확인 처리
    notes = request.POST.get('notes', '')
    job_request.mark_as_reviewed_by_hospital(request.user, notes)
    
    messages.success(request, '채용 요청을 확인했습니다.')
    return JsonResponse({
        'success': True, 
        'message': '확인 완료',
        'reviewed_at': job_request.hospital_reviewed_at.strftime('%Y-%m-%d %H:%M'),
        'reviewer': request.user.get_full_name()
    })


@login_required
@require_POST
@csrf_exempt
def job_request_advance_to_workflow(request, request_id):
    """채용 요청을 워크플로우로 진행"""
    job_request = get_object_or_404(JobRequest, id=request_id)
    
    # 권한 확인
    if not (request.user.is_headhunting_user() and job_request.status == 'submitted'):
        messages.error(request, '워크플로우로 진행할 권한이 없거나 요청 상태가 올바르지 않습니다.')
        return JsonResponse({'success': False, 'message': '권한이 없습니다.'})
    
    # 워크플로우로 진행
    if job_request.advance_to_workflow(request.user):
        messages.success(request, '채용 요청이 워크플로우로 진행되었습니다.')
        return JsonResponse({
            'success': True, 
            'message': '워크플로우 진행 완료',
            'redirect_url': reverse('workflow:workflow_detail', kwargs={'workflow_id': job_request.workflow_progress.workflow.id})
        })
    else:
        messages.error(request, '워크플로우 진행에 실패했습니다.')
        return JsonResponse({'success': False, 'message': '워크플로우 진행 실패'})


@login_required
def job_request_monitoring(request):
    """채용 요청 모니터링 대시보드"""
    # 사용자 유형에 따라 다른 데이터 제공
    if request.user.is_headhunting_user():
        # 헤드헌팅 사용자: 모든 요청의 모니터링 정보
        requests = JobRequest.objects.filter(is_being_monitored=True)
    elif request.user.is_hospital_user():
        # 병원 사용자: 자신의 조직의 요청만
        requests = JobRequest.objects.filter(
            requester__organization=request.user.organization,
            is_being_monitored=True
        )
    else:
        # 기타 사용자: 권한이 있는 요청만
        requests = JobRequest.objects.filter(
            Q(requester=request.user) | 
            Q(requester__organization=request.user.organization),
            is_being_monitored=True
        )
    
    # 통계 정보
    total_requests = requests.count()
    urgent_requests = requests.filter(urgency_level='high').count()
    pending_reviews = requests.filter(
        Q(reviewed_by_headhunting__isnull=True) | 
        Q(reviewed_by_hospital__isnull=True)
    ).count()
    completed_requests = requests.filter(status='completed').count()
    
    # 최근 활동
    recent_activities = UserActivity.objects.filter(
        activity_type__in=['job_request_review', 'workflow_create', 'job_request_submit']
    ).order_by('-created_at')[:10]
    
    breadcrumbs = [
        {'text': '대시보드', 'url': '/', 'icon': 'mdi-home'},
        {'text': '채용 요청 모니터링', 'url': None, 'icon': 'mdi-monitor-dashboard'}
    ]
    
    context = {
        'requests': requests,
        'total_requests': total_requests,
        'urgent_requests': urgent_requests,
        'pending_reviews': pending_reviews,
        'completed_requests': completed_requests,
        'recent_activities': recent_activities,
        'page_title': '채용 요청 모니터링',
        'breadcrumbs': breadcrumbs,
    }
    return render(request, 'workflow/job_request_monitoring.html', context)
