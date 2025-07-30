from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.paginator import Paginator
from django.utils import timezone
from django.db.models import Q
from .models import Candidate, CandidateReview, CandidateNote, CandidateHistory
from .forms import CandidateForm, CandidateReviewForm, CandidateNoteForm, CandidateStatusUpdateForm, CandidateInterviewForm


@login_required
def candidate_list(request):
    """후보자 목록 뷰"""
    user = request.user
    
    # 권한에 따른 후보자 필터링
    if user.is_admin_user():
        candidates = Candidate.objects.all()
    elif user.is_hospital_user():
        candidates = Candidate.objects.filter(
            job_request__requester__organization=user.organization
        )
    elif user.is_headhunting_user():
        candidates = Candidate.objects.filter(
            recommended_by__organization=user.organization
        )
    else:
        candidates = Candidate.objects.none()
    
    # 검색 필터
    search = request.GET.get('search', '')
    status_filter = request.GET.get('status', '')
    review_status_filter = request.GET.get('review_status', '')
    
    if search:
        candidates = candidates.filter(
            Q(name__icontains=search) |
            Q(email__icontains=search) |
            Q(phone__icontains=search) |
            Q(position__icontains=search)
        )
    
    if status_filter:
        candidates = candidates.filter(status=status_filter)
    
    if review_status_filter:
        candidates = candidates.filter(review_status=review_status_filter)
    
    candidates = candidates.order_by('-recommended_at')
    paginator = Paginator(candidates, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    breadcrumbs = [
        {'text': '대시보드', 'url': '/', 'icon': 'mdi-home'},
        {'text': '후보자 목록', 'url': None, 'icon': 'mdi-account-multiple'}
    ]
    
    context = {
        'candidates': page_obj,
        'page_obj': page_obj,
        'is_paginated': paginator.num_pages > 1,
        'page_title': '후보자 목록',
        'breadcrumbs': breadcrumbs,
        'search': search,
        'status_filter': status_filter,
        'review_status_filter': review_status_filter,
        'status_choices': Candidate.STATUS_CHOICES,
        'review_status_choices': Candidate._meta.get_field('review_status').choices,
    }
    return render(request, 'candidates/candidate_list.html', context)


@login_required
def candidate_create(request):
    """후보자 생성 뷰"""
    if request.method == 'POST':
        form = CandidateForm(request.POST, request.FILES)
        if form.is_valid():
            candidate = form.save(commit=False)
            candidate.recommended_by = request.user
            candidate.save()
            messages.success(request, '후보자가 성공적으로 추가되었습니다.')
            return redirect('candidates:detail', candidate_id=candidate.id)
    else:
        form = CandidateForm()
    
    breadcrumbs = [
        {'text': '대시보드', 'url': '/', 'icon': 'mdi-home'},
        {'text': '후보자 목록', 'url': '/candidates/', 'icon': 'mdi-account-multiple'},
        {'text': '새 후보자 추가', 'url': None, 'icon': 'mdi-account-plus'}
    ]
    
    context = {
        'form': form,
        'page_title': '새 후보자 추가',
        'breadcrumbs': breadcrumbs,
    }
    return render(request, 'candidates/candidate_form.html', context)


@login_required
def candidate_detail(request, candidate_id):
    """후보자 상세 뷰"""
    candidate = get_object_or_404(Candidate, id=candidate_id)
    
    # 권한 확인
    user = request.user
    if not user.is_admin_user():
        if user.is_hospital_user():
            if candidate.job_request.requester.organization != user.organization:
                messages.error(request, '접근 권한이 없습니다.')
                return redirect('candidates:list')
        elif user.is_headhunting_user():
            if candidate.recommended_by.organization != user.organization:
                messages.error(request, '접근 권한이 없습니다.')
                return redirect('candidates:list')
    
    # 검토 이력
    reviews = candidate.reviews.all().order_by('-reviewed_at')
    notes = candidate.notes.all().order_by('-created_at')
    history = candidate.history.all().order_by('-created_at')
    
    breadcrumbs = [
        {'text': '대시보드', 'url': '/', 'icon': 'mdi-home'},
        {'text': '후보자 목록', 'url': '/candidates/', 'icon': 'mdi-account-multiple'},
        {'text': candidate.name, 'url': None, 'icon': 'mdi-account'}
    ]
    
    context = {
        'candidate': candidate,
        'reviews': reviews,
        'notes': notes,
        'history': history,
        'page_title': f'후보자 상세 - {candidate.name}',
        'breadcrumbs': breadcrumbs,
    }
    return render(request, 'candidates/candidate_detail.html', context)


@login_required
def candidate_edit(request, candidate_id):
    """후보자 편집 뷰"""
    candidate = get_object_or_404(Candidate, id=candidate_id)
    if request.method == 'POST':
        form = CandidateForm(request.POST, request.FILES, instance=candidate)
        if form.is_valid():
            form.save()
            messages.success(request, '후보자 정보가 성공적으로 업데이트되었습니다.')
            return redirect('candidates:detail', candidate_id=candidate.id)
    else:
        form = CandidateForm(instance=candidate)
    
    breadcrumbs = [
        {'text': '대시보드', 'url': '/', 'icon': 'mdi-home'},
        {'text': '후보자 목록', 'url': '/candidates/', 'icon': 'mdi-account-multiple'},
        {'text': candidate.name, 'url': f'/candidates/{candidate.id}/', 'icon': 'mdi-account'},
        {'text': '수정', 'url': None, 'icon': 'mdi-account-edit'}
    ]
    
    context = {
        'form': form,
        'candidate': candidate,
        'page_title': f'후보자 수정 - {candidate.name}',
        'breadcrumbs': breadcrumbs,
    }
    return render(request, 'candidates/candidate_edit.html', context)


@login_required
def candidate_update(request, candidate_id):
    candidate = get_object_or_404(Candidate, id=candidate_id)
    if request.method == 'POST':
        form = CandidateForm(request.POST, request.FILES, instance=candidate)
        if form.is_valid():
            form.save()
            messages.success(request, '후보자 정보가 성공적으로 업데이트되었습니다.')
            return redirect('candidates:detail', candidate_id=candidate.id)
    else:
        form = CandidateForm(instance=candidate)
    
    breadcrumbs = [
        {'text': '대시보드', 'url': '/', 'icon': 'mdi-home'},
        {'text': '후보자 목록', 'url': '/candidates/', 'icon': 'mdi-account-multiple'},
        {'text': candidate.name, 'url': f'/candidates/{candidate.id}/', 'icon': 'mdi-account'},
        {'text': '수정', 'url': None, 'icon': 'mdi-account-edit'}
    ]
    
    context = {
        'form': form,
        'candidate': candidate,
        'page_title': f'후보자 수정 - {candidate.name}',
        'breadcrumbs': breadcrumbs,
    }
    return render(request, 'candidates/candidate_form.html', context)


@login_required
def candidate_delete(request, candidate_id):
    candidate = get_object_or_404(Candidate, id=candidate_id)
    if request.method == 'POST':
        candidate.delete()
        messages.success(request, '후보자가 성공적으로 삭제되었습니다.')
        return redirect('candidates:list')
    
    breadcrumbs = [
        {'text': '대시보드', 'url': '/', 'icon': 'mdi-home'},
        {'text': '후보자 목록', 'url': '/candidates/', 'icon': 'mdi-account-multiple'},
        {'text': candidate.name, 'url': f'/candidates/{candidate.id}/', 'icon': 'mdi-account'},
        {'text': '삭제', 'url': None, 'icon': 'mdi-delete'}
    ]
    
    context = {
        'candidate': candidate,
        'page_title': f'후보자 삭제 - {candidate.name}',
        'breadcrumbs': breadcrumbs,
    }
    return render(request, 'candidates/candidate_confirm_delete.html', context)


@login_required
def candidate_approve(request, candidate_id):
    """후보자 승인 뷰"""
    candidate = get_object_or_404(Candidate, id=candidate_id)
    
    if request.method == 'POST':
        approval_comment = request.POST.get('approval_comment', '')
        candidate.status = 'approved'
        candidate.save()
        
        # 승인 알림 생성 (실제 구현에서는 알림 시스템 사용)
        messages.success(request, f'후보자 {candidate.name}이(가) 성공적으로 승인되었습니다.')
        return redirect('candidates:detail', candidate_id=candidate.id)
    
    breadcrumbs = [
        {'text': '대시보드', 'url': '/', 'icon': 'mdi-home'},
        {'text': '후보자 목록', 'url': '/candidates/', 'icon': 'mdi-account-multiple'},
        {'text': candidate.name, 'url': f'/candidates/{candidate.id}/', 'icon': 'mdi-account'},
        {'text': '승인', 'url': None, 'icon': 'mdi-check-circle'}
    ]
    
    context = {
        'candidate': candidate,
        'page_title': f'후보자 승인 - {candidate.name}',
        'breadcrumbs': breadcrumbs,
    }
    return render(request, 'candidates/candidate_approve.html', context)


@login_required
def candidate_reject(request, candidate_id):
    """후보자 거절 뷰"""
    candidate = get_object_or_404(Candidate, id=candidate_id)
    
    if request.method == 'POST':
        rejection_reason = request.POST.get('rejection_reason', '')
        rejection_comment = request.POST.get('rejection_comment', '')
        
        if not rejection_reason:
            messages.error(request, '거절 사유를 선택해주세요.')
            return render(request, 'candidates/candidate_reject.html', {'candidate': candidate})
        
        candidate.status = 'rejected'
        candidate.save()
        
        # 거절 알림 생성 (실제 구현에서는 알림 시스템 사용)
        messages.success(request, f'후보자 {candidate.name}이(가) 거절되었습니다.')
        return redirect('candidates:detail', candidate_id=candidate.id)
    
    breadcrumbs = [
        {'text': '대시보드', 'url': '/', 'icon': 'mdi-home'},
        {'text': '후보자 목록', 'url': '/candidates/', 'icon': 'mdi-account-multiple'},
        {'text': candidate.name, 'url': f'/candidates/{candidate.id}/', 'icon': 'mdi-account'},
        {'text': '거절', 'url': None, 'icon': 'mdi-close-circle'}
    ]
    
    context = {
        'candidate': candidate,
        'page_title': f'후보자 거절 - {candidate.name}',
        'breadcrumbs': breadcrumbs,
    }
    return render(request, 'candidates/candidate_reject.html', context)


@login_required
def candidate_review(request, candidate_id):
    """후보자 검토 뷰"""
    candidate = get_object_or_404(Candidate, id=candidate_id)
    
    # 권한 확인 (병원 사용자만 검토 가능)
    user = request.user
    if not user.is_hospital_user() or candidate.job_request.requester.organization != user.organization:
        messages.error(request, '검토 권한이 없습니다.')
        return redirect('candidates:detail', candidate_id=candidate.id)
    
    if request.method == 'POST':
        form = CandidateReviewForm(request.POST)
        if form.is_valid():
            review = form.save(commit=False)
            review.candidate = candidate
            review.reviewer = user
            review.save()
            
            # 후보자 상태 업데이트
            if review.passed:
                candidate.update_review_status('passed', review.total_score, review.overall_comments, user)
                messages.success(request, f'후보자 {candidate.name} 검토가 완료되었습니다. (합격)')
            else:
                candidate.update_review_status('failed', review.total_score, review.overall_comments, user)
                messages.warning(request, f'후보자 {candidate.name} 검토가 완료되었습니다. (불합격)')
            
            # 이력 기록
            CandidateHistory.objects.create(
                candidate=candidate,
                action='evaluation_added',
                action_by=user,
                description=f'{review.get_review_type_display()} 검토 완료 - {review.total_score}점 ({review.get_score_level()})'
            )
            
            return redirect('candidates:detail', candidate_id=candidate.id)
    else:
        form = CandidateReviewForm()
    
    breadcrumbs = [
        {'text': '대시보드', 'url': '/', 'icon': 'mdi-home'},
        {'text': '후보자 목록', 'url': '/candidates/', 'icon': 'mdi-account-multiple'},
        {'text': candidate.name, 'url': f'/candidates/{candidate.id}/', 'icon': 'mdi-account'},
        {'text': '검토', 'url': None, 'icon': 'mdi-clipboard-check'}
    ]
    
    context = {
        'candidate': candidate,
        'form': form,
        'page_title': f'후보자 검토 - {candidate.name}',
        'breadcrumbs': breadcrumbs,
    }
    return render(request, 'candidates/candidate_review.html', context)


@login_required
def candidate_note_add(request, candidate_id):
    """후보자 메모 추가 뷰"""
    candidate = get_object_or_404(Candidate, id=candidate_id)
    
    if request.method == 'POST':
        form = CandidateNoteForm(request.POST)
        if form.is_valid():
            note = form.save(commit=False)
            note.candidate = candidate
            note.author = request.user
            note.save()
            
            # 이력 기록
            CandidateHistory.objects.create(
                candidate=candidate,
                action='note_added',
                action_by=request.user,
                description=f'메모 추가: {note.title}'
            )
            
            messages.success(request, '메모가 추가되었습니다.')
            return redirect('candidates:detail', candidate_id=candidate.id)
    else:
        form = CandidateNoteForm()
    
    breadcrumbs = [
        {'text': '대시보드', 'url': '/', 'icon': 'mdi-home'},
        {'text': '후보자 목록', 'url': '/candidates/', 'icon': 'mdi-account-multiple'},
        {'text': candidate.name, 'url': f'/candidates/{candidate.id}/', 'icon': 'mdi-account'},
        {'text': '메모 추가', 'url': None, 'icon': 'mdi-note-plus'}
    ]
    
    context = {
        'candidate': candidate,
        'form': form,
        'page_title': f'메모 추가 - {candidate.name}',
        'breadcrumbs': breadcrumbs,
    }
    return render(request, 'candidates/candidate_note_form.html', context)


@login_required
def candidate_status_update(request, candidate_id):
    """후보자 상태 업데이트 뷰"""
    candidate = get_object_or_404(Candidate, id=candidate_id)
    
    # 권한 확인
    user = request.user
    if not user.is_admin_user():
        if user.is_hospital_user():
            if candidate.job_request.requester.organization != user.organization:
                messages.error(request, '접근 권한이 없습니다.')
                return redirect('candidates:detail', candidate_id=candidate.id)
        elif user.is_headhunting_user():
            if candidate.recommended_by.organization != user.organization:
                messages.error(request, '접근 권한이 없습니다.')
                return redirect('candidates:detail', candidate_id=candidate.id)
    
    if request.method == 'POST':
        form = CandidateStatusUpdateForm(request.POST, instance=candidate)
        if form.is_valid():
            old_status = candidate.status
            old_review_status = candidate.review_status
            
            candidate = form.save()
            
            # 이력 기록
            if old_status != candidate.status:
                CandidateHistory.objects.create(
                    candidate=candidate,
                    action='status_change',
                    action_by=user,
                    old_value=old_status,
                    new_value=candidate.status,
                    description=f'상태 변경: {candidate.get_status_display()}'
                )
            
            if old_review_status != candidate.review_status:
                CandidateHistory.objects.create(
                    candidate=candidate,
                    action='status_change',
                    action_by=user,
                    old_value=old_review_status,
                    new_value=candidate.review_status,
                    description=f'검토 상태 변경: {candidate.get_review_status_display()}'
                )
            
            messages.success(request, '후보자 상태가 업데이트되었습니다.')
            return redirect('candidates:detail', candidate_id=candidate.id)
    else:
        form = CandidateStatusUpdateForm(instance=candidate)
    
    breadcrumbs = [
        {'text': '대시보드', 'url': '/', 'icon': 'mdi-home'},
        {'text': '후보자 목록', 'url': '/candidates/', 'icon': 'mdi-account-multiple'},
        {'text': candidate.name, 'url': f'/candidates/{candidate.id}/', 'icon': 'mdi-account'},
        {'text': '상태 변경', 'url': None, 'icon': 'mdi-account-edit'}
    ]
    
    context = {
        'candidate': candidate,
        'form': form,
        'page_title': f'상태 변경 - {candidate.name}',
        'breadcrumbs': breadcrumbs,
    }
    return render(request, 'candidates/candidate_status_update.html', context)


@login_required
def candidate_interview_evaluation(request, candidate_id):
    """후보자 면접 평가 뷰"""
    candidate = get_object_or_404(Candidate, id=candidate_id)
    
    # 권한 확인 (병원 사용자만 면접 평가 가능)
    user = request.user
    if not user.is_hospital_user() or candidate.job_request.requester.organization != user.organization:
        messages.error(request, '면접 평가 권한이 없습니다.')
        return redirect('candidates:detail', candidate_id=candidate.id)
    
    if request.method == 'POST':
        form = CandidateInterviewForm(request.POST, instance=candidate)
        if form.is_valid():
            old_decision = candidate.interview_decision
            
            candidate = form.save()
            
            # 이력 기록
            if old_decision != candidate.interview_decision:
                CandidateHistory.objects.create(
                    candidate=candidate,
                    action='decision_made',
                    action_by=user,
                    old_value=old_decision,
                    new_value=candidate.interview_decision,
                    description=f'면접 결정: {candidate.get_interview_decision_display()}'
                )
            
            messages.success(request, '면접 평가가 완료되었습니다.')
            return redirect('candidates:detail', candidate_id=candidate.id)
    else:
        form = CandidateInterviewForm(instance=candidate)
    
    breadcrumbs = [
        {'text': '대시보드', 'url': '/', 'icon': 'mdi-home'},
        {'text': '후보자 목록', 'url': '/candidates/', 'icon': 'mdi-account-multiple'},
        {'text': candidate.name, 'url': f'/candidates/{candidate.id}/', 'icon': 'mdi-account'},
        {'text': '면접 평가', 'url': None, 'icon': 'mdi-account-check'}
    ]
    
    context = {
        'candidate': candidate,
        'form': form,
        'page_title': f'면접 평가 - {candidate.name}',
        'breadcrumbs': breadcrumbs,
    }
    return render(request, 'candidates/candidate_interview_evaluation.html', context)
