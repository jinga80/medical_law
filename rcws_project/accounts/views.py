from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.contrib.auth import update_session_auth_hash, logout
from django.contrib.auth.forms import PasswordChangeForm
from django.core.paginator import Paginator
from django.http import HttpResponseRedirect
from django.urls import reverse
from django.contrib.auth.decorators import user_passes_test
from django.db.models import Q
from django.utils import timezone
from datetime import datetime, timedelta
from .models import User, UserActivity
from .forms import UserProfileForm, CustomUserCreationForm, CustomUserChangeForm


def is_admin(user):
    """관리자 권한 확인"""
    return user.is_staff or user.is_superuser


@login_required
def profile_view(request):
    """사용자 프로필 뷰"""
    return render(request, 'accounts/profile.html', {'user': request.user})


@login_required
def user_list(request):
    """사용자 목록 뷰"""
    users = User.objects.all().order_by('-date_joined')
    paginator = Paginator(users, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'users': page_obj,
        'page_obj': page_obj,
        'is_paginated': paginator.num_pages > 1,
    }
    return render(request, 'accounts/user_list.html', context)


@login_required
def user_detail(request, user_id):
    """사용자 상세 뷰"""
    user = get_object_or_404(User, id=user_id)
    return render(request, 'accounts/user_detail.html', {'user': user})


@login_required
def profile(request):
    return render(request, 'accounts/profile.html', {'user': request.user})


@login_required
def profile_edit(request):
    if request.method == 'POST':
        form = UserProfileForm(request.POST, request.FILES, instance=request.user)
        if form.is_valid():
            # 변경 전 정보 저장
            old_first_name = request.user.first_name
            old_last_name = request.user.last_name
            old_email = request.user.email
            
            # 폼 저장
            user = form.save()
            
            # 활동 로그 기록
            UserActivity.log_activity(
                user=request.user,
                activity_type='profile_update',
                description=f'프로필 정보 수정: {old_first_name} {old_last_name} → {user.first_name} {user.last_name}',
                related_object_type='User',
                related_object_id=user.id,
                related_object_name=user.get_full_name(),
                request=request
            )
            
            messages.success(request, '프로필이 성공적으로 업데이트되었습니다.')
            return redirect('accounts:profile')
        else:
            messages.error(request, '프로필 수정 중 오류가 발생했습니다. 입력 정보를 확인해주세요.')
    else:
        form = UserProfileForm(instance=request.user)
    
    return render(request, 'accounts/profile_form.html', {'form': form})


@login_required
def change_password(request):
    if request.method == 'POST':
        form = PasswordChangeForm(request.user, request.POST)
        if form.is_valid():
            user = form.save()
            update_session_auth_hash(request, user)
            messages.success(request, '비밀번호가 성공적으로 변경되었습니다.')
            return redirect('accounts:profile')
    else:
        form = PasswordChangeForm(request.user)
    
    return render(request, 'accounts/change_password.html', {'form': form})


@login_required
@user_passes_test(is_admin)
def user_create(request):
    """사용자 생성 뷰"""
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST, request.FILES)
        if form.is_valid():
            user = form.save(commit=False)
            user.set_password(form.cleaned_data['password1'])
            user.save()
            messages.success(request, f'사용자 {user.get_full_name()}이(가) 성공적으로 생성되었습니다.')
            return redirect('accounts:user_detail', user_id=user.id)
    else:
        form = CustomUserCreationForm()
    
    return render(request, 'accounts/user_create.html', {'form': form})


@login_required
@user_passes_test(is_admin)
def user_edit(request, user_id):
    user = get_object_or_404(User, id=user_id)
    if request.method == 'POST':
        form = CustomUserChangeForm(request.POST, request.FILES, instance=user)
        if form.is_valid():
            form.save()
            messages.success(request, '사용자 정보가 성공적으로 업데이트되었습니다.')
            return redirect('accounts:user_detail', user_id=user.id)
    else:
        form = CustomUserChangeForm(instance=user)
    
    return render(request, 'accounts/user_form.html', {'form': form, 'user': user})


@login_required
@user_passes_test(is_admin)
def user_delete(request, user_id):
    """사용자 삭제 뷰"""
    user = get_object_or_404(User, id=user_id)
    
    # 현재 로그인한 사용자는 삭제할 수 없음
    if user == request.user:
        messages.error(request, '현재 로그인 중인 사용자는 삭제할 수 없습니다.')
        return redirect('accounts:user_detail', user_id=user.id)
    
    if request.method == 'POST':
        user_name = user.get_full_name()
        user.delete()
        messages.success(request, f'사용자 {user_name}이(가) 성공적으로 삭제되었습니다.')
        return redirect('accounts:user_list')
    
    return render(request, 'accounts/user_confirm_delete.html', {'user': user})


def logout_view(request):
    """커스텀 로그아웃 뷰"""
    if request.method == 'POST':
        logout(request)
        messages.success(request, '성공적으로 로그아웃되었습니다.')
        return redirect('accounts:login')
    else:
        # GET 요청의 경우 로그인 페이지로 리다이렉트
        return redirect('accounts:login')


@login_required
def user_activity_list(request):
    """사용자 활동 로그 목록 뷰"""
    # 필터링 옵션
    user_filter = request.GET.get('user')
    activity_type_filter = request.GET.get('activity_type')
    date_from = request.GET.get('date_from')
    date_to = request.GET.get('date_to')
    
    activities = UserActivity.objects.all().order_by('-created_at')
    
    # 사용자별 필터링
    if user_filter:
        activities = activities.filter(user__id=user_filter)
    
    # 활동 유형별 필터링
    if activity_type_filter:
        activities = activities.filter(activity_type=activity_type_filter)
    
    # 날짜 범위 필터링
    if date_from:
        try:
            date_from_obj = datetime.strptime(date_from, '%Y-%m-%d').date()
            activities = activities.filter(created_at__date__gte=date_from_obj)
        except ValueError:
            pass
    
    if date_to:
        try:
            date_to_obj = datetime.strptime(date_to, '%Y-%m-%d').date()
            activities = activities.filter(created_at__date__lte=date_to_obj)
        except ValueError:
            pass
    
    # 통계 데이터
    total_activities = activities.count()
    today_activities = activities.filter(created_at__date=timezone.now().date()).count()
    this_week_activities = activities.filter(
        created_at__gte=timezone.now() - timedelta(days=7)
    ).count()
    this_month_activities = activities.filter(
        created_at__gte=timezone.now() - timedelta(days=30)
    ).count()
    
    # 활동 유형별 통계
    activity_stats = {}
    for activity_type, _ in UserActivity.ACTIVITY_TYPE_CHOICES:
        activity_stats[activity_type] = activities.filter(activity_type=activity_type).count()
    
    # 사용자별 통계
    user_stats = {}
    for user in User.objects.all():
        user_stats[user.get_full_name()] = activities.filter(user=user).count()
    
    paginator = Paginator(activities, 50)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'activities': page_obj,
        'page_obj': page_obj,
        'is_paginated': paginator.num_pages > 1,
        'total_activities': total_activities,
        'today_activities': today_activities,
        'this_week_activities': this_week_activities,
        'this_month_activities': this_month_activities,
        'activity_stats': activity_stats,
        'user_stats': user_stats,
        'activity_types': UserActivity.ACTIVITY_TYPE_CHOICES,
        'users': User.objects.all(),
        'filters': {
            'user': user_filter,
            'activity_type': activity_type_filter,
            'date_from': date_from,
            'date_to': date_to,
        }
    }
    return render(request, 'accounts/user_activity_list.html', context)


@login_required
def user_activity_detail(request, activity_id):
    """사용자 활동 로그 상세 뷰"""
    activity = get_object_or_404(UserActivity, id=activity_id)
    return render(request, 'accounts/user_activity_detail.html', {'activity': activity})


@login_required
def my_activity_list(request):
    """내 활동 로그 목록 뷰"""
    activities = UserActivity.objects.filter(user=request.user).order_by('-created_at')
    
    # 통계 데이터
    total_activities = activities.count()
    today_activities = activities.filter(created_at__date=timezone.now().date()).count()
    this_week_activities = activities.filter(
        created_at__gte=timezone.now() - timedelta(days=7)
    ).count()
    this_month_activities = activities.filter(
        created_at__gte=timezone.now() - timedelta(days=30)
    ).count()
    
    # 활동 유형별 통계
    activity_stats = {}
    for activity_type, _ in UserActivity.ACTIVITY_TYPE_CHOICES:
        activity_stats[activity_type] = activities.filter(activity_type=activity_type).count()
    
    paginator = Paginator(activities, 30)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'activities': page_obj,
        'page_obj': page_obj,
        'is_paginated': paginator.num_pages > 1,
        'total_activities': total_activities,
        'today_activities': today_activities,
        'this_week_activities': this_week_activities,
        'this_month_activities': this_month_activities,
        'activity_stats': activity_stats,
    }
    return render(request, 'accounts/my_activity_list.html', context)


@login_required
def activity_dashboard(request):
    """활동 대시보드 뷰"""
    # 전체 활동 통계
    all_activities = UserActivity.objects.all()
    total_activities = all_activities.count()
    
    # 최근 30일 활동 추이
    daily_activities = []
    for i in range(30):
        date = timezone.now().date() - timedelta(days=i)
        count = all_activities.filter(created_at__date=date).count()
        daily_activities.append({
            'date': date.strftime('%Y-%m-%d'),
            'count': count
        })
    daily_activities.reverse()
    
    # 활동 유형별 통계
    activity_type_stats = {}
    for activity_type, label in UserActivity.ACTIVITY_TYPE_CHOICES:
        count = all_activities.filter(activity_type=activity_type).count()
        if count > 0:
            activity_type_stats[label] = count
    
    # 사용자별 활동 통계 (상위 10명)
    user_activity_stats = []
    for user in User.objects.all():
        count = all_activities.filter(user=user).count()
        if count > 0:
            user_activity_stats.append({
                'user': user.get_full_name(),
                'count': count
            })
    user_activity_stats.sort(key=lambda x: x['count'], reverse=True)
    user_activity_stats = user_activity_stats[:10]
    
    # 최근 활동 (최근 20개)
    recent_activities = all_activities[:20]
    
    context = {
        'total_activities': total_activities,
        'daily_activities': daily_activities,
        'activity_type_stats': activity_type_stats,
        'user_activity_stats': user_activity_stats,
        'recent_activities': recent_activities,
    }
    return render(request, 'accounts/activity_dashboard.html', context)
