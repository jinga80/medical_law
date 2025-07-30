from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.paginator import Paginator
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import csrf_exempt
import json
from .models import Notification


@login_required
def notification_list(request):
    """알림 목록 뷰"""
    notifications = Notification.objects.filter(recipient=request.user).order_by('-created_at')
    paginator = Paginator(notifications, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'notifications': page_obj,
        'page_obj': page_obj,
        'is_paginated': paginator.num_pages > 1,
    }
    return render(request, 'notifications/notification_list.html', context)


@login_required
def notification_detail(request, notification_id):
    notification = get_object_or_404(Notification, id=notification_id, recipient=request.user)
    if not notification.is_read:
        notification.is_read = True
        notification.save()
    return render(request, 'notifications/notification_detail.html', {'notification': notification})


@login_required
@require_POST
@csrf_exempt
def mark_as_read(request):
    try:
        data = json.loads(request.body)
        notification_ids = data.get('notification_ids', [])
        
        notifications = Notification.objects.filter(
            id__in=notification_ids,
            recipient=request.user
        )
        notifications.update(is_read=True)
        
        return JsonResponse({'success': True})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})


@login_required
@require_POST
@csrf_exempt
def delete_read(request):
    try:
        Notification.objects.filter(recipient=request.user, is_read=True).delete()
        return JsonResponse({'success': True})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})


@login_required
@require_POST
@csrf_exempt
def notification_delete(request, notification_id):
    try:
        notification = get_object_or_404(Notification, id=notification_id, recipient=request.user)
        notification.delete()
        return JsonResponse({'success': True})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})
