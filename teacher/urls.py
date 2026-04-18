from django.urls import path
from . import views

app_name = 'teacher'

urlpatterns = [
    path('', views.home, name='home'),
    path('features/', views.features, name='features'),
    path('account/', views.account, name='account'),
    path('notify/', views.send_notification, name='send_notification'),
    path('students/', views.student_activity, name='student_activity'),
    path('students/<int:student_id>/', views.student_detail, name='student_detail'),
    path('upload-questions/', views.upload_questions, name='upload_questions'),
    
    # Exam Creation & Management
    path('exams/create/', views.create_exam, name='create_exam'),
    path('exams/<int:exam_id>/add-questions/', views.add_questions, name='add_questions'),
    
    # Marks Management
    path('marks/', views.marks_list, name='marks_list'),
    path('marks/enroll/<int:subject_id>/', views.enroll_students, name='enroll_students'),
    path('marks/dashboard/<int:subject_id>/', views.marks_dashboard, name='marks_dashboard'),
    path('marks/theory/<int:subject_id>/', views.manage_theory_marks, name='manage_theory_marks'),
    path('marks/mcq/<int:subject_id>/', views.manage_mcq_marks, name='manage_mcq_marks'),
    path('marks/quiz/<int:subject_id>/', views.manage_quiz_marks, name='manage_quiz_marks'),
    path('marks/assignment/<int:subject_id>/', views.manage_assignment_marks, name='manage_assignment_marks'),
    path('marks/view/<int:subject_id>/<int:student_id>/', views.view_student_marks, name='view_student_marks'),
    
    # Analytics & Performance
    path('performance/', views.student_performance, name='student_performance'),
    path('exam-analytics/', views.exam_analytics, name='exam_analytics'),
    path('subject-analytics/<int:subject_id>/', views.student_subject_analytics, name='subject_analytics'),
]
