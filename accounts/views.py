from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from .models import User, StudentProfile, TeacherProfile
from student.models import StudentEnrollment


def role_selection(request):
    if request.user.is_authenticated:
        return redirect_by_role(request.user)
    return render(request, 'accounts/role_selection.html')


def redirect_by_role(user):
    if user.role == 'student':
        return redirect('student:home')
    elif user.role == 'teacher':
        return redirect('teacher:home')
    elif user.role == 'admin':
        return redirect('adminpanel:dashboard')
    return redirect('role_selection')


# ── STUDENT ──────────────────────────────────────────
def student_login(request):
    if request.method == 'POST':
        roll = request.POST.get('roll_number', '').strip()
        password = request.POST.get('password', '').strip()
        try:
            profile = StudentProfile.objects.get(roll_number=roll)
            user = authenticate(request, username=profile.user.username, password=password)
            if user and user.role == 'student':
                login(request, user)
                return redirect('student:home')
            else:
                messages.error(request, 'Invalid roll number or password.')
        except StudentProfile.DoesNotExist:
            messages.error(request, 'Student with this roll number not found.')
    return render(request, 'accounts/student_login.html')


def student_register(request):
    if request.method == 'POST':
        first_name = request.POST.get('first_name', '').strip()
        last_name  = request.POST.get('last_name', '').strip()
        roll       = request.POST.get('roll_number', '').strip()
        email      = request.POST.get('email', '').strip()
        dept       = request.POST.get('department', '').strip()
        semester   = request.POST.get('semester', '').strip()
        phone      = request.POST.get('phone', '').strip()
        password   = request.POST.get('password', '').strip()
        confirm    = request.POST.get('confirm_password', '').strip()

        if password != confirm:
            messages.error(request, 'Passwords do not match.')
            return render(request, 'accounts/student_register.html')
        if User.objects.filter(username=roll).exists():
            messages.error(request, 'Roll number already registered.')
            return render(request, 'accounts/student_register.html')

        user = User.objects.create_user(
            username=roll, password=password,
            first_name=first_name, last_name=last_name,
            email=email, role='student', phone=phone
        )
        student_profile = StudentProfile.objects.create(
            user=user, roll_number=roll, department=dept,
            semester=semester, email=email
        )
        # Auto-enroll student in courses of their department teachers
        enrollment_count = StudentEnrollment.auto_enroll_by_department(student_profile)
        messages.success(request, f'Account created! Auto-enrolled in {enrollment_count} courses. Please login.')
        return redirect('student_login')
    return render(request, 'accounts/student_register.html')


# ── TEACHER ──────────────────────────────────────────
def teacher_login(request):
    if request.method == 'POST':
        emp_id   = request.POST.get('employee_id', '').strip()
        password = request.POST.get('password', '').strip()
        try:
            profile = TeacherProfile.objects.get(employee_id=emp_id)
            user = authenticate(request, username=profile.user.username, password=password)
            if user and user.role == 'teacher':
                login(request, user)
                return redirect('teacher:home')
            else:
                messages.error(request, 'Invalid employee ID or password.')
        except TeacherProfile.DoesNotExist:
            messages.error(request, 'Teacher with this Employee ID not found.')
    return render(request, 'accounts/teacher_login.html')


def teacher_register(request):
    if request.method == 'POST':
        first_name  = request.POST.get('first_name', '').strip()
        last_name   = request.POST.get('last_name', '').strip()
        emp_id      = request.POST.get('employee_id', '').strip()
        email       = request.POST.get('email', '').strip()
        dept        = request.POST.get('department', '').strip()
        designation = request.POST.get('designation', '').strip()
        subjects    = request.POST.get('subjects', '').strip()
        phone       = request.POST.get('phone', '').strip()
        password    = request.POST.get('password', '').strip()
        confirm     = request.POST.get('confirm_password', '').strip()

        if password != confirm:
            messages.error(request, 'Passwords do not match.')
            return render(request, 'accounts/teacher_register.html')
        if TeacherProfile.objects.filter(employee_id=emp_id).exists():
            messages.error(request, 'Employee ID already registered.')
            return render(request, 'accounts/teacher_register.html')

        user = User.objects.create_user(
            username=emp_id, password=password,
            first_name=first_name, last_name=last_name,
            email=email, role='teacher', phone=phone
        )
        TeacherProfile.objects.create(
            user=user, employee_id=emp_id, department=dept,
            designation=designation, subjects=subjects, email=email
        )
        messages.success(request, 'Teacher account created! Please login.')
        return redirect('teacher_login')
    return render(request, 'accounts/teacher_register.html')


# ── ADMIN ─────────────────────────────────────────────
def admin_login(request):
    if request.method == 'POST':
        username = request.POST.get('username', '').strip()
        password = request.POST.get('password', '').strip()
        user = authenticate(request, username=username, password=password)
        if user and user.role == 'admin':
            login(request, user)
            return redirect('adminpanel:dashboard')
        else:
            messages.error(request, 'Invalid credentials or not an admin account.')
    return render(request, 'accounts/admin_login.html')


def admin_register(request):
    if request.method == 'POST':
        first_name  = request.POST.get('first_name', '').strip()
        last_name   = request.POST.get('last_name', '').strip()
        username    = request.POST.get('username', '').strip()
        email       = request.POST.get('email', '').strip()
        phone       = request.POST.get('phone', '').strip()
        admin_role  = request.POST.get('admin_role', '').strip()
        secret      = request.POST.get('secret_key', '').strip()
        password    = request.POST.get('password', '').strip()
        confirm     = request.POST.get('confirm_password', '').strip()

        import os
        if secret != os.getenv('ADMIN_REGISTRATION_SECRET', 'ADMIN2024'):
            messages.error(request, 'Invalid secret key.')
            return render(request, 'accounts/admin_register.html')
        if password != confirm:
            messages.error(request, 'Passwords do not match.')
            return render(request, 'accounts/admin_register.html')
        if User.objects.filter(username=username).exists():
            messages.error(request, 'Username already taken.')
            return render(request, 'accounts/admin_register.html')

        User.objects.create_user(
            username=username, password=password,
            first_name=first_name, last_name=last_name,
            email=email, role='admin', phone=phone, is_staff=True
        )
        messages.success(request, 'Admin account created! Please login.')
        return redirect('admin_login')
    return render(request, 'accounts/admin_register.html')


def logout_view(request):
    logout(request)
    return redirect('role_selection')
