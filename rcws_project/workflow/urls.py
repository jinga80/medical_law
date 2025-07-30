from django.urls import path
from . import views

app_name = 'workflow'

urlpatterns = [
    path('', views.workflow_list, name='list'),
    path('create/', views.workflow_create, name='create'),
    path('<int:workflow_id>/', views.workflow_detail, name='detail'),
    path('<int:workflow_id>/edit/', views.workflow_update, name='update'),
    path('<int:workflow_id>/delete/', views.workflow_delete, name='delete'),
    path('<int:workflow_id>/advance/', views.workflow_advance, name='advance'),
    path('<int:workflow_id>/reset/', views.workflow_status_reset, name='reset'),
    path('<int:workflow_id>/activity/', views.workflow_activity_log, name='activity'),
    path('step/<int:step_id>/start/', views.step_start, name='step_start'),
    path('step/<int:step_id>/complete/', views.step_complete, name='step_complete'),
    path('step/<int:step_id>/detail/', views.step_detail, name='step_detail'),
    path('step/<int:step_id>/revert/', views.step_revert, name='step_revert'),
    path('step/<int:step_id>/revert-status/', views.step_revert_status, name='step_revert_status'),
    path('step/<int:step_id>/update-status/', views.step_update_status, name='step_update_status'),
    path('step/<int:step_id>/delete/', views.document_delete, name='document_delete'),
    
    # Job Request URLs
    path('job-requests/', views.job_request_list, name='job_request_list'),
    path('job-requests/create/', views.job_request_create, name='job_request_create'),
    path('job-requests/<int:request_id>/', views.job_request_detail, name='job_request_detail'),
    path('job-requests/<int:request_id>/edit/', views.job_request_edit, name='job_request_edit'),
    path('job-requests/<int:request_id>/submit/', views.job_request_submit, name='job_request_submit'),
    path('job-requests/<int:request_id>/add-request/', views.job_request_add_additional_request, name='job_request_add_additional_request'),
    path('job-requests/<int:request_id>/lock/', views.job_request_lock, name='job_request_lock'),
    path('job-requests/<int:request_id>/unlock/', views.job_request_unlock, name='job_request_unlock'),
    path('job-requests/<int:request_id>/add-request-ajax/', views.job_request_add_additional_request_ajax, name='job_request_add_additional_request_ajax'),
    
    # 채용 요청 확인 및 워크플로우 진행
    path('job-requests/<int:request_id>/review-headhunting/', views.job_request_review_headhunting, name='job_request_review_headhunting'),
    path('job-requests/<int:request_id>/review-hospital/', views.job_request_review_hospital, name='job_request_review_hospital'),
    path('job-requests/<int:request_id>/advance-workflow/', views.job_request_advance_to_workflow, name='job_request_advance_to_workflow'),
    
    # 모니터링
    path('job-requests/monitoring/', views.job_request_monitoring, name='job_request_monitoring'),
    
    # API URLs
    path('api/job-request/<int:request_id>/', views.get_job_request_data, name='get_job_request_data'),
    
    # 채용 공고 관리
    path('job-postings/', views.job_posting_list, name='job_posting_list'),
    path('job-postings/<int:posting_id>/', views.job_posting_detail, name='job_posting_detail'),
    path('job-requests/<int:job_request_id>/create-posting/', views.job_posting_create, name='job_posting_create'),
    path('job-postings/<int:posting_id>/update/', views.job_posting_update, name='job_posting_update'),
    path('job-postings/<int:posting_id>/publish/', views.job_posting_publish, name='job_posting_publish'),
    path('job-postings/<int:posting_id>/close/', views.job_posting_close, name='job_posting_close'),
    
    # 구인 공고 지원
    path('job-postings/<int:posting_id>/apply/', views.job_application_create, name='job_application_create'),
    path('job-postings/<int:posting_id>/applications/', views.job_application_list, name='job_application_list'),
    path('applications/<int:application_id>/', views.job_application_detail, name='job_application_detail'),

    # 템플릿 관리
    path('templates/', views.template_list, name='template_list'),
    path('templates/create/', views.template_create, name='template_create'),
    path('templates/<int:pk>/', views.template_detail, name='template_detail'),
    path('templates/<int:pk>/update/', views.template_update, name='template_update'),
    path('templates/<int:pk>/delete/', views.template_delete, name='template_delete'),
    path('templates/<int:template_pk>/create-request/', views.job_request_create_from_template, name='job_request_create_from_template'),
] 