from django.urls import path
from . import views

urlpatterns = [
    path('register/', views.register, name='register'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('check-auth/', views.check_auth, name='check_auth'),
    path('analyze/', views.analyze_resume, name='analyze_resume'),
    path('history/', views.analysis_history_list, name='analysis_history_list'),
    path('history/<int:history_id>/', views.analysis_history_detail, name='analysis_history_detail'),
    path('history/<int:history_id>/delete/', views.analysis_history_delete, name='analysis_history_delete'),
    path('export/<str:fmt>/', views.export_report, name='export_report'),
    path('fetch-job/', views.fetch_job, name='fetch_job'),
    path('recommend-jobs/', views.recommend_jobs, name='recommend_jobs'),
    path('feedback/', views.submit_feedback, name='submit_feedback'),
]

