from django.urls import path
from . import views

app_name = 'evaluations'

urlpatterns = [
    path('', views.evaluation_list, name='list'),
    path('create/', views.evaluation_create, name='create'),
    path('<int:evaluation_id>/', views.evaluation_detail, name='detail'),
    path('<int:evaluation_id>/edit/', views.evaluation_update, name='update'),
    path('<int:evaluation_id>/delete/', views.evaluation_delete, name='delete'),
] 