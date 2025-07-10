from django.urls import path
from . import api_views

urlpatterns = [
    path('performance/', api_views.performance_report, name='performance_report'),
    path('workflow-analytics/', api_views.workflow_analytics, name='workflow_analytics'),
    path('candidate-stats/', api_views.candidate_stats, name='candidate_stats'),
] 