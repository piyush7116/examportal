from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.db.models import Count, Q
from accounts.models import User, StudentProfile, TeacherProfile
from student.models import Subject, Exam, Question, ExamAttempt, PracticeSession, Notification, StudentEnrollment


def admin_required(view_func):
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated or request.user.role != 'admin':
            return redirect('admin_login')
        # Verify user is staff member (admin should have is_staff=True)
        if not request.user.is_staff:
            messages.error(request, 'Admin privileges not found. Please contact administrator.')
            return redirect('role_selection')
        return view_func(request, *args, **kwargs)
    return wrapper


@admin_required
def dashboard(request):
    total_students = StudentProfile.objects.count()
    total_teachers = TeacherProfile.objects.count()
    total_subjects  = Subject.objects.count()
    exams_taken     = ExamAttempt.objects.count()
    practice_count  = PracticeSession.objects.count()
    notifications   = Notification.objects.order_by('-created_at')[:5]
    recent_students = StudentProfile.objects.order_by('-id')[:5]
    return render(request, 'adminpanel/dashboard.html', {
        'total_students': total_students,
        'total_teachers': total_teachers,
        'total_subjects': total_subjects,
        'exams_taken': exams_taken,
        'practice_count': practice_count,
        'notifications': notifications,
        'recent_students': recent_students,
    })


# ── SYLLABUS MANAGEMENT ───────────────────────────────
@admin_required
def syllabus(request):
    subjects = Subject.objects.all().order_by('-created_at')
    return render(request, 'adminpanel/syllabus.html', {'subjects': subjects})


@admin_required
def add_subject(request):
    if request.method == 'POST':
        name   = request.POST.get('name', '').strip()
        topics = request.POST.get('topics', '').strip()
        if name and topics:
            Subject.objects.create(name=name, topics=topics, uploaded_by=request.user)
            messages.success(request, f'Subject "{name}" added successfully.')
        else:
            messages.error(request, 'Name and topics are required.')
        return redirect('adminpanel:syllabus')
    return render(request, 'adminpanel/add_subject.html')


@admin_required
def edit_subject(request, subject_id):
    subject = get_object_or_404(Subject, id=subject_id)
    if request.method == 'POST':
        subject.name   = request.POST.get('name', subject.name).strip()
        subject.topics = request.POST.get('topics', subject.topics).strip()
        subject.save()
        messages.success(request, 'Subject updated.')
        return redirect('adminpanel:syllabus')
    return render(request, 'adminpanel/edit_subject.html', {'subject': subject})


@admin_required
def delete_subject(request, subject_id):
    subject = get_object_or_404(Subject, id=subject_id)
    subject.delete()
    messages.success(request, 'Subject deleted.')
    return redirect('adminpanel:syllabus')


# ── NOTIFICATIONS ─────────────────────────────────────
@admin_required
def notifications(request):
    notifs = Notification.objects.order_by('-created_at')
    return render(request, 'adminpanel/notifications.html', {'notifications': notifs})


@admin_required
def send_notification(request):
    if request.method == 'POST':
        title    = request.POST.get('title', '').strip()
        message  = request.POST.get('message', '').strip()
        priority = request.POST.get('priority', 'medium')
        if title and message:
            Notification.objects.create(
                title=title, message=message,
                priority=priority, created_by=request.user
            )
            messages.success(request, 'Notification sent.')
        return redirect('adminpanel:notifications')
    return render(request, 'adminpanel/send_notification.html')


@admin_required
def delete_notification(request, notif_id):
    notif = get_object_or_404(Notification, id=notif_id)
    notif.delete()
    messages.success(request, 'Notification deleted.')
    return redirect('adminpanel:notifications')


# ── STUDENTS ──────────────────────────────────────────
@admin_required
def students(request):
    students_list = StudentProfile.objects.select_related('user').order_by('-id')
    return render(request, 'adminpanel/students.html', {'students': students_list})


@admin_required
def student_activity(request, student_id):
    profile = get_object_or_404(StudentProfile, id=student_id)
    attempts = ExamAttempt.objects.filter(student=profile).order_by('-attempted_at')
    sessions = PracticeSession.objects.filter(student=profile).order_by('-practiced_at')
    return render(request, 'adminpanel/student_activity.html', {
        'profile': profile, 'attempts': attempts, 'sessions': sessions
    })


@admin_required
def delete_student(request, student_id):
    profile = get_object_or_404(StudentProfile, id=student_id)
    profile.user.delete()
    messages.success(request, 'Student deleted.')
    return redirect('adminpanel:students')


@admin_required
def enroll_student(request, student_id):
    """Manually enroll a student in subjects/teachers"""
    student = get_object_or_404(StudentProfile, id=student_id)
    
    if request.method == 'POST':
        subject_id = request.POST.get('subject')
        teacher_id = request.POST.get('teacher')
        
        subject = get_object_or_404(Subject, id=subject_id)
        teacher_user = get_object_or_404(User, id=teacher_id)
        
        enrollment, created = StudentEnrollment.objects.get_or_create(
            student=student,
            subject=subject,
            teacher=teacher_user
        )
        
        if created:
            messages.success(request, f'Successfully enrolled in {subject.name} (Teacher: {teacher_user.get_full_name()})')
        else:
            messages.info(request, 'Student is already enrolled in this course.')
        return redirect('adminpanel:student_activity', student_id=student.id)
    
    subjects = Subject.objects.all()
    teachers = User.objects.filter(role='teacher')
    
    return render(request, 'adminpanel/enroll_student.html', {
        'student': student,
        'subjects': subjects,
        'teachers': teachers
    })


@admin_required
def trigger_auto_enroll(request, student_id):
    """Strictly force auto-enrollment for a specific student based on department"""
    student = get_object_or_404(StudentProfile, id=student_id)
    enrollment_count = StudentEnrollment.auto_enroll_by_department(student)
    messages.success(request, f'Strict Auto-Enroll complete: {enrollment_count} new enrollments created for {student.user.get_full_name()}.')
    return redirect('adminpanel:student_activity', student_id=student.id)


# ── TEACHERS ─────────────────────────────────────────
@admin_required
def teachers(request):
    teachers_list = TeacherProfile.objects.select_related('user').order_by('-id')
    return render(request, 'adminpanel/teachers.html', {'teachers': teachers_list})


# ── EXAM CREATION ─────────────────────────────────────
@admin_required
def exam_list(request):
    exams = Exam.objects.select_related('subject').order_by('-created_at')
    return render(request, 'adminpanel/exam_list.html', {'exams': exams})


@admin_required
def create_exam(request):
    subjects = Subject.objects.all()
    if request.method == 'POST':
        title    = request.POST.get('title', '').strip()
        subj_id  = request.POST.get('subject')
        password = request.POST.get('password', '').strip()
        duration = request.POST.get('duration', 60)
        total    = request.POST.get('total_marks', 100)
        subject  = get_object_or_404(Subject, id=subj_id)
        exam = Exam.objects.create(
            title=title, subject=subject, password=password,
            duration_minutes=int(duration), total_marks=int(total),
            created_by=request.user
        )
        messages.success(request, f'Exam "{title}" created. Now add questions.')
        return redirect('adminpanel:add_questions', exam_id=exam.id)
    return render(request, 'adminpanel/create_exam.html', {'subjects': subjects})


@admin_required
def add_questions(request, exam_id):
    exam = get_object_or_404(Exam, id=exam_id)
    if request.method == 'POST':
        texts   = request.POST.getlist('question_text')
        opt_as  = request.POST.getlist('option_a')
        opt_bs  = request.POST.getlist('option_b')
        opt_cs  = request.POST.getlist('option_c')
        opt_ds  = request.POST.getlist('option_d')
        corrects = request.POST.getlist('correct')
        markss  = request.POST.getlist('marks')
        for i, text in enumerate(texts):
            if text.strip():
                Question.objects.create(
                    exam=exam, text=text,
                    option_a=opt_as[i], option_b=opt_bs[i],
                    option_c=opt_cs[i], option_d=opt_ds[i],
                    correct_option=corrects[i], marks=int(markss[i] or 1)
                )
        messages.success(request, 'Questions added.')
        return redirect('adminpanel:exam_list')
    existing = exam.questions.all()
    return render(request, 'adminpanel/add_questions.html', {'exam': exam, 'questions': existing})


@admin_required
def give_password(request):
    exams = Exam.objects.all()
    if request.method == 'POST':
        exam_id  = request.POST.get('exam_id')
        password = request.POST.get('new_password', '').strip()
        exam = get_object_or_404(Exam, id=exam_id)
        exam.password = password
        exam.save()
        messages.success(request, f'Password for "{exam.title}" updated.')
    return render(request, 'adminpanel/give_password.html', {'exams': exams})


# ── STUDENT ATTENDANCE ────────────────────────────────
@admin_required
def student_attendance(request):
    attempts = ExamAttempt.objects.select_related('student__user', 'exam').order_by('-attempted_at')
    return render(request, 'adminpanel/student_attendance.html', {'attempts': attempts})


# ── TEACHER MANAGEMENT ────────────────────────────────
@admin_required
def teachers_manage(request):
    """View all teachers with detailed information"""
    teachers_list = TeacherProfile.objects.select_related('user').order_by('-id')
    
    # Add additional data for each teacher
    teachers_data = []
    for teacher in teachers_list:
        enrolled_students = StudentEnrollment.objects.filter(teacher=teacher.user).count()
        exams_created = Exam.objects.filter(created_by=teacher.user).count()
        teachers_data.append({
            'profile': teacher,
            'enrolled_students': enrolled_students,
            'exams_created': exams_created,
        })
    
    return render(request, 'adminpanel/teachers_manage.html', {'teachers_data': teachers_data})


@admin_required
def add_teacher(request):
    """Add a new teacher to the system"""
    if request.method == 'POST':
        first_name = request.POST.get('first_name', '').strip()
        last_name = request.POST.get('last_name', '').strip()
        emp_id = request.POST.get('employee_id', '').strip()
        email = request.POST.get('email', '').strip()
        phone = request.POST.get('phone', '').strip()
        department = request.POST.get('department', '').strip()
        designation = request.POST.get('designation', '').strip()
        password = request.POST.get('password', '').strip()
        
        if not all([first_name, last_name, emp_id, email, password]):
            messages.error(request, 'All required fields must be filled.')
            return render(request, 'adminpanel/add_teacher.html')
        
        if User.objects.filter(username=emp_id).exists():
            messages.error(request, 'Employee ID already exists.')
            return render(request, 'adminpanel/add_teacher.html')
        
        if User.objects.filter(email=email).exists():
            messages.error(request, 'Email already registered.')
            return render(request, 'adminpanel/add_teacher.html')
        
        # Create user
        user = User.objects.create_user(
            username=emp_id,
            password=password,
            first_name=first_name,
            last_name=last_name,
            email=email,
            role='teacher',
            phone=phone
        )
        
        # Create teacher profile
        TeacherProfile.objects.create(
            user=user,
            employee_id=emp_id,
            department=department,
            designation=designation,
            email=email
        )
        
        messages.success(request, f'Teacher {first_name} {last_name} added successfully.')
        return redirect('adminpanel:teachers_manage')
    
    return render(request, 'adminpanel/add_teacher.html')


@admin_required
def edit_teacher(request, teacher_id):
    """Edit teacher details"""
    teacher = get_object_or_404(TeacherProfile, id=teacher_id)
    
    if request.method == 'POST':
        teacher.user.first_name = request.POST.get('first_name', teacher.user.first_name).strip()
        teacher.user.last_name = request.POST.get('last_name', teacher.user.last_name).strip()
        teacher.user.email = request.POST.get('email', teacher.user.email).strip()
        teacher.user.phone = request.POST.get('phone', teacher.user.phone).strip()
        teacher.user.save()
        
        teacher.department = request.POST.get('department', teacher.department).strip()
        teacher.designation = request.POST.get('designation', teacher.designation).strip()
        teacher.email = request.POST.get('email', teacher.email).strip()
        teacher.save()
        
        # Change password if provided
        new_password = request.POST.get('new_password', '').strip()
        if new_password:
            teacher.user.set_password(new_password)
            teacher.user.save()
            messages.info(request, 'Password updated.')
        
        messages.success(request, 'Teacher details updated.')
        return redirect('adminpanel:teachers_manage')
    
    return render(request, 'adminpanel/edit_teacher.html', {'teacher': teacher})


@admin_required
def view_teacher_details(request, teacher_id):
    """View comprehensive teacher details and activity"""
    teacher = get_object_or_404(TeacherProfile, id=teacher_id)
    
    # Get enrollment data
    enrollments = StudentEnrollment.objects.filter(teacher=teacher.user).select_related('student', 'subject')
    
    # Get exam creation data
    exams_created = Exam.objects.filter(created_by=teacher.user)
    
    # Get subject-wise student count
    subject_stats = {}
    for enrollment in enrollments:
        if enrollment.subject.name not in subject_stats:
            subject_stats[enrollment.subject.name] = 0
        subject_stats[enrollment.subject.name] += 1
    
    return render(request, 'adminpanel/view_teacher_details.html', {
        'teacher': teacher,
        'enrollments': enrollments,
        'exams_created': exams_created,
        'subject_stats': subject_stats,
        'total_students': enrollments.count(),
        'total_exams': exams_created.count(),
    })


@admin_required
def delete_teacher(request, teacher_id):
    """Delete a teacher"""
    teacher = get_object_or_404(TeacherProfile, id=teacher_id)
    teacher_name = teacher.user.get_full_name()
    teacher.user.delete()
    messages.success(request, f'Teacher {teacher_name} has been deleted.')
    return redirect('adminpanel:teachers_manage')


@admin_required
def assign_subject_to_teacher(request, teacher_id):
    """Assign subjects to a teacher"""
    teacher = get_object_or_404(TeacherProfile, id=teacher_id)
    teacher_user = teacher.user
    
    if request.method == 'POST':
        subject_ids = request.POST.getlist('subject_ids')
        new_subject_ids = [int(sid) for sid in subject_ids]
        
        # Get existing assignments to find what to remove
        old_subject_ids = list(teacher_user.assigned_subjects.values_list('id', flat=True))
        
        # Clear and update M2M
        teacher_user.assigned_subjects.clear()
        new_assignments = Subject.objects.filter(id__in=new_subject_ids)
        for subject in new_assignments:
            subject.teachers.add(teacher_user)
            
            # Auto-enroll all students from the same department
            students = StudentProfile.objects.filter(department=teacher.department)
            for student in students:
                StudentEnrollment.objects.get_or_create(
                    student=student, subject=subject, teacher=teacher_user
                )
        
        # Remove enrollments for subjects that were unassigned
        removed_ids = set(old_subject_ids) - set(new_subject_ids)
        if removed_ids:
            deleted_count, _ = StudentEnrollment.objects.filter(
                teacher=teacher_user, subject_id__in=removed_ids
            ).delete()
            if deleted_count > 0:
                messages.warning(request, f'Unassigned {len(removed_ids)} subjects and removed {deleted_count} student enrollments.')

        # Update teacher profile text for display
        teacher.subjects = ', '.join([s.name for s in new_assignments])
        teacher.save()
        
        messages.success(request, f'Assignments updated for {teacher_user.get_full_name()}. Students auto-synced.')
        return redirect('adminpanel:teachers_manage')
    
    # Get all subjects and already assigned subjects
    all_subjects = Subject.objects.all()
    assigned_subjects = teacher_user.assigned_subjects.all()
    
    return render(request, 'adminpanel/assign_subject_to_teacher.html', {
        'teacher': teacher,
        'all_subjects': all_subjects,
        'assigned_subjects': assigned_subjects,
    })


@admin_required
def teacher_activity(request, teacher_id):
    """View teacher's activity and performance"""
    teacher = get_object_or_404(TeacherProfile, id=teacher_id)
    
    # Get enrollments
    enrollments = StudentEnrollment.objects.filter(teacher=teacher.user).select_related('student', 'subject')
    
    # Get exams created
    exams = Exam.objects.filter(created_by=teacher.user).select_related('subject')
    
    # Get exam attempts for students taught by this teacher
    attempts_count = 0
    for enrollment in enrollments:
        attempts_count += ExamAttempt.objects.filter(student=enrollment.student).count()
    
    return render(request, 'adminpanel/teacher_activity.html', {
        'teacher': teacher,
        'enrollments': enrollments,
        'exams': exams,
        'attempts_count': attempts_count,
        'total_students_taught': enrollments.count(),
    })
