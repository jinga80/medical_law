from django.urls import path
from . import views

app_name = 'candidates'

urlpatterns = [
    path('', views.candidate_list, name='list'),
    path('create/', views.candidate_create, name='create'),
    path('<int:candidate_id>/', views.candidate_detail, name='detail'),
    path('<int:candidate_id>/edit/', views.candidate_edit, name='edit'),
    path('<int:candidate_id>/update/', views.candidate_update, name='update'),
    path('<int:candidate_id>/delete/', views.candidate_delete, name='delete'),
    path('<int:candidate_id>/review/', views.candidate_review, name='review'),
    path('<int:candidate_id>/note/add/', views.candidate_note_add, name='note_add'),
    path('<int:candidate_id>/status/update/', views.candidate_status_update, name='status_update'),
    path('<int:candidate_id>/interview/evaluation/', views.candidate_interview_evaluation, name='interview_evaluation'),
    path('<int:candidate_id>/approve/', views.candidate_approve, name='approve'),
    path('<int:candidate_id>/reject/', views.candidate_reject, name='reject'),
] 