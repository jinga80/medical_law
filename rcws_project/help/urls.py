from django.urls import path
from . import views

app_name = 'help'

urlpatterns = [
    path('', views.help_main, name='main'),
    path('dashboard/', views.help_dashboard, name='dashboard'),
    path('users/', views.help_users, name='users'),
    path('candidates/', views.help_candidates, name='candidates'),
    path('workflow/', views.help_workflow, name='workflow'),
    path('evaluations/', views.help_evaluations, name='evaluations'),
    path('reports/', views.help_reports, name='reports'),
    path('notifications/', views.help_notifications, name='notifications'),
    path('faq/', views.help_faq, name='faq'),
    path('contact/', views.help_contact, name='contact'),
] 