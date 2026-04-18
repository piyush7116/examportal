from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    ROLE_CHOICES = [
        ('student', 'Student'),
        ('teacher', 'Teacher'),
        ('admin', 'Admin'),
    ]
    role = models.CharField(max_length=10, choices=ROLE_CHOICES, default='student')
    phone = models.CharField(max_length=15, blank=True)

    def is_student(self):
        return self.role == 'student'

    def is_teacher(self):
        return self.role == 'teacher'

    def is_admin_user(self):
        return self.role == 'admin'


class StudentProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='student_profile')
    roll_number = models.CharField(max_length=20, unique=True)
    department = models.CharField(max_length=100)
    semester = models.CharField(max_length=20)
    email = models.EmailField(blank=True)

    def __str__(self):
        return f"{self.user.get_full_name()} ({self.roll_number})"


class TeacherProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='teacher_profile')
    employee_id = models.CharField(max_length=20, unique=True)
    department = models.CharField(max_length=100)
    designation = models.CharField(max_length=100)
    subjects = models.TextField(blank=True)
    email = models.EmailField(blank=True)

    def __str__(self):
        return f"{self.user.get_full_name()} ({self.employee_id})"
