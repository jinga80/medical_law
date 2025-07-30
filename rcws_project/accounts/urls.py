from django.urls import path
from django.contrib.auth import views as auth_views
from . import views, api

app_name = 'accounts'

urlpatterns = [
    path('login/', auth_views.LoginView.as_view(template_name='accounts/login.html'), name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('profile/', views.profile, name='profile'),
    path('profile/edit/', views.profile_edit, name='profile_edit'),
    path('change-password/', views.change_password, name='change_password'),
    path('users/', views.user_list, name='user_list'),
    path('users/create/', views.user_create, name='user_create'),
    path('users/<int:user_id>/', views.user_detail, name='user_detail'),
    path('users/<int:user_id>/edit/', views.user_edit, name='user_edit'),
    path('users/<int:user_id>/delete/', views.user_delete, name='user_delete'),
    path('activities/', views.user_activity_list, name='activity_list'),
    path('activities/my/', views.my_activity_list, name='my_activity_list'),
    path('activities/dashboard/', views.activity_dashboard, name='activity_dashboard'),
    path('activities/<int:activity_id>/', views.user_activity_detail, name='activity_detail'),
    path('api/hospitals/', api.hospital_list, name='api_hospital_list'),
    path('api/hospitals/<int:hospital_id>/branches/', api.hospital_branch_list, name='api_hospital_branch_list'),
    path('api/branches/<int:branch_id>/', api.hospital_branch_detail, name='api_hospital_branch_detail'),
    path('api/positions/', api.position_template_list, name='api_position_template_list'),
    path('api/positions/<int:position_id>/', api.position_template_detail, name='api_position_template_detail'),
    path('api/job-templates/', api.job_request_template_list, name='api_job_request_template_list'),
    path('api/job-templates/<int:template_id>/', api.job_request_template_detail, name='api_job_request_template_detail'),
] 