from django.urls import path, include, re_path
from rest_framework.routers import DefaultRouter
from drf_yasg.views import get_schema_view
from drf_yasg import openapi
from rest_framework import permissions
from workflow.api import JobRequestViewSet, WorkflowStepViewSet
from candidates.api import CandidateViewSet
from evaluations.api import InterviewViewSet
from notifications.api import NotificationViewSet
from accounts.api import UserViewSet, OrganizationViewSet

# Swagger 스키마 뷰 설정
schema_view = get_schema_view(
    openapi.Info(
        title="RCWS API",
        default_version='v1',
        description="리버스 클리닉 헤드헌팅 협업 워크플로우 시스템 API",
        terms_of_service="https://www.rcws.com/terms/",
        contact=openapi.Contact(email="admin@rcws.com"),
        license=openapi.License(name="BSD License"),
    ),
    public=True,
    permission_classes=[permissions.AllowAny],
)

# API 라우터 설정
router = DefaultRouter()
router.register(r'job-requests', JobRequestViewSet, basename='job-request')
router.register(r'workflow-steps', WorkflowStepViewSet, basename='workflow-step')
router.register(r'candidates', CandidateViewSet, basename='candidate')
router.register(r'interviews', InterviewViewSet, basename='interview')
router.register(r'notifications', NotificationViewSet, basename='notification')
router.register(r'users', UserViewSet, basename='user')
router.register(r'organizations', OrganizationViewSet, basename='organization')

urlpatterns = [
    # API 루트
    path('', include(router.urls)),
    
    # 인증 관련 API
    path('auth/', include('rest_framework.urls')),
    
    # API 문서 (Swagger/OpenAPI)
    re_path(r'^swagger(?P<format>\.json|\.yaml)$', schema_view.without_ui(cache_timeout=0), name='schema-json'),
    re_path(r'^swagger/$', schema_view.with_ui('swagger', cache_timeout=0), name='schema-swagger-ui'),
    re_path(r'^redoc/$', schema_view.with_ui('redoc', cache_timeout=0), name='schema-redoc'),
    
    # 대시보드 API
    path('dashboard/', include('dashboard.api_urls')),
    
    # 보고서 API
    path('reports/', include('reports.api_urls')),
] 