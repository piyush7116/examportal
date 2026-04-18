from django.urls import path
from . import views

urlpatterns = [
    path('', views.role_selection, name='role_selection'),
    path('logout/', views.logout_view, name='logout'),

    # Student auth
    path('student/login/', views.student_login, name='student_login'),
    path('student/register/', views.student_register, name='student_register'),

    # Teacher auth
    path('teacher/login/', views.teacher_login, name='teacher_login'),
    path('teacher/register/', views.teacher_register, name='teacher_register'),

    # Admin auth
    path('admin-login/', views.admin_login, name='admin_login'),
    path('admin-register/', views.admin_register, name='admin_register'),
]
