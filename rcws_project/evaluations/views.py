from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.paginator import Paginator
from .models import InterviewEvaluation, DocumentReview, Interview
from .forms import InterviewEvaluationForm, DocumentReviewForm, InterviewForm


@login_required
def evaluation_list(request):
    """평가 목록 뷰"""
    evaluations = InterviewEvaluation.objects.all().order_by('-evaluated_at')
    paginator = Paginator(evaluations, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    breadcrumbs = [
        {'text': '대시보드', 'url': '/', 'icon': 'mdi-home'},
        {'text': '평가 목록', 'url': None, 'icon': 'mdi-clipboard-check-multiple'}
    ]
    
    context = {
        'evaluations': page_obj,
        'page_obj': page_obj,
        'is_paginated': paginator.num_pages > 1,
        'page_title': '평가 목록',
        'breadcrumbs': breadcrumbs,
    }
    return render(request, 'evaluations/evaluation_list.html', context)


@login_required
def evaluation_create(request):
    """평가 생성 뷰"""
    if request.method == 'POST':
        form = InterviewEvaluationForm(request.POST)
        if form.is_valid():
            evaluation = form.save(commit=False)
            evaluation.evaluator = request.user
            evaluation.save()
            messages.success(request, '평가가 성공적으로 생성되었습니다.')
            return redirect('evaluations:detail', evaluation_id=evaluation.id)
    else:
        form = InterviewEvaluationForm()
    
    breadcrumbs = [
        {'text': '대시보드', 'url': '/', 'icon': 'mdi-home'},
        {'text': '평가 목록', 'url': '/evaluations/', 'icon': 'mdi-clipboard-check-multiple'},
        {'text': '새 평가', 'url': None, 'icon': 'mdi-clipboard-check-plus'}
    ]
    
    context = {
        'form': form,
        'page_title': '새 평가',
        'breadcrumbs': breadcrumbs,
    }
    return render(request, 'evaluations/evaluation_form.html', context)


@login_required
def evaluation_detail(request, evaluation_id):
    """평가 상세 뷰"""
    evaluation = get_object_or_404(InterviewEvaluation, id=evaluation_id)
    
    breadcrumbs = [
        {'text': '대시보드', 'url': '/', 'icon': 'mdi-home'},
        {'text': '평가 목록', 'url': '/evaluations/', 'icon': 'mdi-clipboard-check-multiple'},
        {'text': f'평가 #{evaluation.id}', 'url': None, 'icon': 'mdi-clipboard-check'}
    ]
    
    context = {
        'evaluation': evaluation,
        'page_title': f'평가 상세 - #{evaluation.id}',
        'breadcrumbs': breadcrumbs,
    }
    return render(request, 'evaluations/evaluation_detail.html', context)


@login_required
def evaluation_update(request, evaluation_id):
    """평가 수정 뷰"""
    evaluation = get_object_or_404(InterviewEvaluation, id=evaluation_id)
    if request.method == 'POST':
        form = InterviewEvaluationForm(request.POST, instance=evaluation)
        if form.is_valid():
            form.save()
            messages.success(request, '평가가 성공적으로 업데이트되었습니다.')
            return redirect('evaluations:detail', evaluation_id=evaluation.id)
    else:
        form = InterviewEvaluationForm(instance=evaluation)
    
    breadcrumbs = [
        {'text': '대시보드', 'url': '/', 'icon': 'mdi-home'},
        {'text': '평가 목록', 'url': '/evaluations/', 'icon': 'mdi-clipboard-check-multiple'},
        {'text': f'평가 #{evaluation.id}', 'url': f'/evaluations/{evaluation.id}/', 'icon': 'mdi-clipboard-check'},
        {'text': '수정', 'url': None, 'icon': 'mdi-clipboard-edit'}
    ]
    
    context = {
        'form': form,
        'evaluation': evaluation,
        'page_title': f'평가 수정 - #{evaluation.id}',
        'breadcrumbs': breadcrumbs,
    }
    return render(request, 'evaluations/evaluation_form.html', context)


@login_required
def evaluation_delete(request, evaluation_id):
    """평가 삭제 뷰"""
    evaluation = get_object_or_404(InterviewEvaluation, id=evaluation_id)
    if request.method == 'POST':
        evaluation.delete()
        messages.success(request, '평가가 성공적으로 삭제되었습니다.')
        return redirect('evaluations:list')
    
    breadcrumbs = [
        {'text': '대시보드', 'url': '/', 'icon': 'mdi-home'},
        {'text': '평가 목록', 'url': '/evaluations/', 'icon': 'mdi-clipboard-check-multiple'},
        {'text': f'평가 #{evaluation.id}', 'url': f'/evaluations/{evaluation.id}/', 'icon': 'mdi-clipboard-check'},
        {'text': '삭제', 'url': None, 'icon': 'mdi-delete'}
    ]
    
    context = {
        'evaluation': evaluation,
        'page_title': f'평가 삭제 - #{evaluation.id}',
        'breadcrumbs': breadcrumbs,
    }
    return render(request, 'evaluations/evaluation_confirm_delete.html', context)


@login_required
def document_review_list(request):
    """서류 검토 목록 뷰"""
    reviews = DocumentReview.objects.all().order_by('-reviewed_at')
    paginator = Paginator(reviews, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    breadcrumbs = [
        {'text': '대시보드', 'url': '/', 'icon': 'mdi-home'},
        {'text': '서류 검토 목록', 'url': None, 'icon': 'mdi-file-document-multiple'}
    ]
    
    context = {
        'reviews': page_obj,
        'page_obj': page_obj,
        'is_paginated': paginator.num_pages > 1,
        'page_title': '서류 검토 목록',
        'breadcrumbs': breadcrumbs,
    }
    return render(request, 'evaluations/document_review_list.html', context)


@login_required
def document_review_create(request):
    """서류 검토 생성 뷰"""
    if request.method == 'POST':
        form = DocumentReviewForm(request.POST)
        if form.is_valid():
            review = form.save(commit=False)
            review.reviewer = request.user
            review.save()
            messages.success(request, '서류 검토가 성공적으로 생성되었습니다.')
            return redirect('evaluations:document_review_detail', review_id=review.id)
    else:
        form = DocumentReviewForm()
    
    breadcrumbs = [
        {'text': '대시보드', 'url': '/', 'icon': 'mdi-home'},
        {'text': '서류 검토 목록', 'url': '/evaluations/document-reviews/', 'icon': 'mdi-file-document-multiple'},
        {'text': '새 서류 검토', 'url': None, 'icon': 'mdi-file-document-plus'}
    ]
    
    context = {
        'form': form,
        'page_title': '새 서류 검토',
        'breadcrumbs': breadcrumbs,
    }
    return render(request, 'evaluations/document_review_form.html', context)


@login_required
def interview_list(request):
    """면접 목록 뷰"""
    interviews = Interview.objects.all().order_by('-scheduled_date')
    paginator = Paginator(interviews, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    breadcrumbs = [
        {'text': '대시보드', 'url': '/', 'icon': 'mdi-home'},
        {'text': '면접 목록', 'url': None, 'icon': 'mdi-account-group'}
    ]
    
    context = {
        'interviews': page_obj,
        'page_obj': page_obj,
        'is_paginated': paginator.num_pages > 1,
        'page_title': '면접 목록',
        'breadcrumbs': breadcrumbs,
    }
    return render(request, 'evaluations/interview_list.html', context)


@login_required
def interview_create(request):
    """면접 생성 뷰"""
    if request.method == 'POST':
        form = InterviewForm(request.POST)
        if form.is_valid():
            interview = form.save(commit=False)
            interview.save()
            form.save_m2m()  # ManyToMany 필드 저장
            messages.success(request, '면접이 성공적으로 생성되었습니다.')
            return redirect('evaluations:interview_detail', interview_id=interview.id)
    else:
        form = InterviewForm()
    
    breadcrumbs = [
        {'text': '대시보드', 'url': '/', 'icon': 'mdi-home'},
        {'text': '면접 목록', 'url': '/evaluations/interviews/', 'icon': 'mdi-account-group'},
        {'text': '새 면접', 'url': None, 'icon': 'mdi-account-plus'}
    ]
    
    context = {
        'form': form,
        'page_title': '새 면접',
        'breadcrumbs': breadcrumbs,
    }
    return render(request, 'evaluations/interview_form.html', context) 