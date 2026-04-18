from django.urls import path
from . import views

app_name = 'student'

urlpatterns = [
    path('', views.home, name='home'),
    path('features/', views.features, name='features'),
    path('account/', views.account, name='account'),
    path('exams/', views.exam_list, name='exam_list'),
    path('exams/<int:exam_id>/enter/', views.exam_enter, name='exam_enter'),
    path('exams/<int:exam_id>/take/', views.exam_take, name='exam_take'),
    path('practice/', views.question_practice, name='question_practice'),
    path('practice/<int:subject_id>/<str:topic>/', views.practice_quiz, name='practice_quiz'),
    path('history/', views.history, name='history'),
    path('notifications/', views.notifications, name='notifications'),
    
    # Marks & Grades
    path('marks/', views.view_marks, name='view_marks'),
    path('marks/<int:subject_id>/', views.subject_marks_detail, name='subject_marks_detail'),
    path('exams/result/<int:attempt_id>/', views.view_exam_result, name='view_exam_result'),
]
