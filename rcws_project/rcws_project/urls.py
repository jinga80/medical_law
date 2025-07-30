"""
URL configuration for rcws_project project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/4.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from drf_yasg.views import get_schema_view
from drf_yasg import openapi
from rest_framework import permissions
from django.contrib.auth import views as auth_views

schema_view = get_schema_view(
    openapi.Info(
        title="리버스 클리닉 헤드헌팅 협업 워크플로우 API",
        default_version='v1',
        description="리버스 클리닉과 케이지아웃소싱 간의 헤드헌팅 협업 워크플로우 시스템 API",
        terms_of_service="https://www.google.com/policies/terms/",
        contact=openapi.Contact(email="contact@reverseclinic.com"),
        license=openapi.License(name="BSD License"),
    ),
    public=True,
    permission_classes=(permissions.AllowAny,),
)

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('dashboard.urls')),
    path('dashboard/api/', include('dashboard.api_urls')),
    
    path('accounts/', include('accounts.urls')),
    path('candidates/', include('candidates.urls')),
    path('evaluations/', include('evaluations.urls')),
    path('notifications/', include('notifications.urls')),
    path('reports/', include('reports.urls')),
    path('workflow/', include('workflow.urls')),
    path('help/', include('help.urls')),
    path('api/', include('api.urls')),
    path('swagger/', schema_view.with_ui('swagger', cache_timeout=0), name='schema-swagger-ui'),
    path('redoc/', schema_view.with_ui('redoc', cache_timeout=0), name='schema-redoc'),
]

# 개발 환경에서 미디어 파일 서빙
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
