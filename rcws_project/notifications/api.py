from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.db.models import Q
from .models import Notification
from .serializers import NotificationSerializer


class NotificationViewSet(viewsets.ReadOnlyModelViewSet):
    """알림 API 뷰셋 (읽기 전용)"""
    serializer_class = NotificationSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        return Notification.objects.filter(recipient=self.request.user)
    
    @action(detail=True, methods=['post'])
    def mark_read(self, request, pk=None):
        """알림 읽음 처리"""
        notification = self.get_object()
        notification.is_read = True
        notification.save()
        return Response({'status': 'marked_read'})
    
    @action(detail=False, methods=['post'])
    def mark_all_read(self, request):
        """모든 알림 읽음 처리"""
        unread_notifications = self.get_queryset().filter(is_read=False)
        unread_notifications.update(is_read=True)
        return Response({'status': 'all_marked_read'})
    
    @action(detail=False, methods=['get'])
    def unread_count(self, request):
        """읽지 않은 알림 개수"""
        count = self.get_queryset().filter(is_read=False).count()
        return Response({'unread_count': count})
    
    @action(detail=False, methods=['get'])
    def recent(self, request):
        """최근 알림 목록"""
        recent_notifications = self.get_queryset().order_by('-created_at')[:10]
        serializer = self.get_serializer(recent_notifications, many=True)
        return Response(serializer.data) 