from django.urls import path
from . import views

app_name = 'notifications'

urlpatterns = [
    path('', views.notification_list, name='list'),
    path('<int:notification_id>/', views.notification_detail, name='detail'),
    path('mark-as-read/', views.mark_as_read, name='mark_as_read'),
    path('delete-read/', views.delete_read, name='delete_read'),
    path('<int:notification_id>/delete/', views.notification_delete, name='delete'),
] 