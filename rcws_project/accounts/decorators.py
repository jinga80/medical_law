from django.shortcuts import redirect
from django.contrib import messages
from django.http import HttpResponseForbidden
from functools import wraps


def role_required(allowed_roles):
    """특정 역할을 가진 사용자만 접근 가능하도록 하는 데코레이터"""
    def decorator(view_func):
        @wraps(view_func)
        def _wrapped_view(request, *args, **kwargs):
            if not request.user.is_authenticated:
                return redirect('accounts:login')
            
            if request.user.role in allowed_roles or request.user.is_superuser:
                return view_func(request, *args, **kwargs)
            else:
                messages.error(request, '접근 권한이 없습니다.')
                return HttpResponseForbidden('접근 권한이 없습니다.')
        return _wrapped_view
    return decorator


def organization_required(allowed_org_types):
    """특정 기관 유형의 사용자만 접근 가능하도록 하는 데코레이터"""
    def decorator(view_func):
        @wraps(view_func)
        def _wrapped_view(request, *args, **kwargs):
            if not request.user.is_authenticated:
                return redirect('accounts:login')
            
            if (request.user.organization.org_type in allowed_org_types or 
                request.user.is_superuser or 
                request.user.role == 'system_admin'):
                return view_func(request, *args, **kwargs)
            else:
                messages.error(request, '접근 권한이 없습니다.')
                return HttpResponseForbidden('접근 권한이 없습니다.')
        return _wrapped_view
    return decorator


def hospital_only(view_func):
    """병원 사용자만 접근 가능하도록 하는 데코레이터"""
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('accounts:login')
        
        if (request.user.is_hospital_user() or 
            request.user.is_superuser or 
            request.user.role == 'system_admin'):
            return view_func(request, *args, **kwargs)
        else:
            messages.error(request, '병원 관계자만 접근할 수 있습니다.')
            return HttpResponseForbidden('병원 관계자만 접근할 수 있습니다.')
    return _wrapped_view


def headhunting_only(view_func):
    """헤드헌팅 사용자만 접근 가능하도록 하는 데코레이터"""
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('accounts:login')
        
        if (request.user.is_headhunting_user() or 
            request.user.is_superuser or 
            request.user.role == 'system_admin'):
            return view_func(request, *args, **kwargs)
        else:
            messages.error(request, '채용회사 담당자만 접근할 수 있습니다.')
            return HttpResponseForbidden('채용회사 담당자만 접근할 수 있습니다.')
    return _wrapped_view


def admin_only(view_func):
    """관리자만 접근 가능하도록 하는 데코레이터"""
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('accounts:login')
        
        if request.user.is_superuser or request.user.role == 'system_admin':
            return view_func(request, *args, **kwargs)
        else:
            messages.error(request, '관리자만 접근할 수 있습니다.')
            return HttpResponseForbidden('관리자만 접근할 수 있습니다.')
    return _wrapped_view


def permission_required(permission_method):
    """특정 권한을 가진 사용자만 접근 가능하도록 하는 데코레이터"""
    def decorator(view_func):
        @wraps(view_func)
        def _wrapped_view(request, *args, **kwargs):
            if not request.user.is_authenticated:
                return redirect('accounts:login')
            
            if hasattr(request.user, permission_method):
                permission_check = getattr(request.user, permission_method)
                if permission_check() or request.user.is_superuser:
                    return view_func(request, *args, **kwargs)
            
            messages.error(request, '접근 권한이 없습니다.')
            return HttpResponseForbidden('접근 권한이 없습니다.')
        return _wrapped_view
    return decorator 