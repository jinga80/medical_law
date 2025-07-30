from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('test/', views.test_view, name='test'),
    path('health/', views.health_check, name='health_check'),
    path('guidelines/', views.guidelines, name='guidelines'),
    path('history/', views.history, name='history'),
    path('medical-law-info/', views.medical_law_info, name='medical_law_info'),
    path('advertising-law-info/', views.advertising_law_info, name='advertising_law_info'),
    path('review-process-info/', views.review_process_info, name='review_process_info'),
    
    # 가이드라인 관리 시스템
    path('guideline-management/', views.guideline_management, name='guideline_management'),
    path('guideline-updates/', views.guideline_updates, name='guideline_updates'),
    path('ai-analysis-history/', views.ai_analysis_history, name='ai_analysis_history'),
    
    # 분석 결과 페이지
    path('result/<int:analysis_id>/', views.show_result, name='show_result'),
    
    # API endpoints
    path('api/analyze/text/', views.analyze_text, name='analyze_text'),
    path('api/analyze/url/', views.analyze_url, name='analyze_url'),
    path('api/analyze/file/', views.analyze_file, name='analyze_file'),
    path('api/analysis/<int:analysis_id>/', views.get_analysis_result, name='get_analysis_result'),
    path('api/analysis/<int:analysis_id>/delete/', views.delete_analysis, name='delete_analysis'),
    path('api/analysis/<int:analysis_id>/detailed-report/', views.get_detailed_report, name='detailed_report'),
    path('api/export/pdf/<int:analysis_id>/', views.export_pdf_report, name='export_pdf_report'),
    path('api/ai-analysis/<int:analysis_id>/', views.get_ai_analysis_result, name='get_ai_analysis_result'),
    path('api/violation-improvements/', views.get_violation_improvements, name='get_violation_improvements'),
    path('api/rewrite-text/', views.rewrite_text_with_ai, name='rewrite_text_with_ai'),
    
    # 가이드라인 관리 API
    path('api/guideline-documents/', views.create_guideline_document, name='create_guideline_document'),
    path('api/guideline-documents/<int:document_id>/', views.get_guideline_document, name='get_guideline_document'),
    path('api/guideline-documents/<int:document_id>/update/', views.update_guideline_document, name='update_guideline_document'),
    path('api/guideline-documents/<int:document_id>/delete/', views.delete_guideline_document, name='delete_guideline_document'),
    path('api/guideline-documents/<int:document_id>/analyze/', views.analyze_with_ai, name='analyze_with_ai'),
    path('api/guideline-updates/<int:update_id>/', views.get_guideline_update_detail, name='get_guideline_update_detail'),
] 