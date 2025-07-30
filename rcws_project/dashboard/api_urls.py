from django.urls import path
from . import api_views

app_name = 'dashboard_api'

urlpatterns = [
    # 대시보드 통계 API
    path('stats/', api_views.dashboard_stats_api, name='stats'),
    
    # 채용 프로세스 현황 API
    path('process-overview/', api_views.process_overview_api, name='process_overview'),
    
    # 성과 지표 API
    path('performance-metrics/', api_views.performance_metrics_api, name='performance_metrics'),
    
    # 최근 활동 API
    path('recent-activities/', api_views.recent_activities_api, name='recent_activities'),
    
    # 알림 API
    path('notifications/', api_views.notifications_api, name='notifications'),
    
    # 기존 API
    path('pending-tasks/', api_views.pending_tasks_api, name='pending_tasks'),
] 