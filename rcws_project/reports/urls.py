from django.urls import path
from . import views

app_name = 'reports'

urlpatterns = [
    path('', views.report_list, name='report_list'),
    path('create/', views.report_create, name='create'),
    path('performance/', views.performance_report, name='performance_report'),
    path('workflow-analytics/', views.workflow_analytics, name='workflow_analytics'),
    path('candidate-stats/', views.candidate_stats, name='candidate_stats'),
    path('generate-quick/', views.generate_quick_report, name='generate_quick'),
    path('<int:report_id>/', views.report_detail, name='detail'),
    path('<int:report_id>/edit/', views.report_update, name='update'),
    path('<int:report_id>/download/', views.report_download, name='download'),
] 