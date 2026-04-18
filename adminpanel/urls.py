from django.urls import path
from . import views

app_name = 'adminpanel'

urlpatterns = [
    path('', views.dashboard, name='dashboard'),
    path('syllabus/', views.syllabus, name='syllabus'),
    path('syllabus/add/', views.add_subject, name='add_subject'),
    path('syllabus/edit/<int:subject_id>/', views.edit_subject, name='edit_subject'),
    path('syllabus/delete/<int:subject_id>/', views.delete_subject, name='delete_subject'),
    path('notifications/', views.notifications, name='notifications'),
    path('notifications/send/', views.send_notification, name='send_notification'),
    path('notifications/delete/<int:notif_id>/', views.delete_notification, name='delete_notification'),
    path('students/', views.students, name='students'),
    path('students/<int:student_id>/activity/', views.student_activity, name='student_activity'),
    path('students/<int:student_id>/delete/', views.delete_student, name='delete_student'),
    path('students/<int:student_id>/enroll/', views.enroll_student, name='enroll_student'),
    path('students/<int:student_id>/auto-enroll/', views.trigger_auto_enroll, name='trigger_auto_enroll'),
    path('teachers/', views.teachers, name='teachers'),
    path('teachers/manage/', views.teachers_manage, name='teachers_manage'),
    path('teachers/add/', views.add_teacher, name='add_teacher'),
    path('teachers/<int:teacher_id>/edit/', views.edit_teacher, name='edit_teacher'),
    path('teachers/<int:teacher_id>/view/', views.view_teacher_details, name='view_teacher_details'),
    path('teachers/<int:teacher_id>/delete/', views.delete_teacher, name='delete_teacher'),
    path('teachers/<int:teacher_id>/assign-subject/', views.assign_subject_to_teacher, name='assign_subject_to_teacher'),
    path('teachers/<int:teacher_id>/activity/', views.teacher_activity, name='teacher_activity'),
    path('exams/', views.exam_list, name='exam_list'),
    path('exams/create/', views.create_exam, name='create_exam'),
    path('exams/<int:exam_id>/questions/', views.add_questions, name='add_questions'),
    path('exams/password/', views.give_password, name='give_password'),
    path('attendance/', views.student_attendance, name='student_attendance'),
]
