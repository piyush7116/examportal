from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.db import models
from django.db.models import Avg, Count, Max, Min
from accounts.models import StudentProfile
from student.models import (Subject, Exam, Question, ExamAttempt, PracticeSession, 
                            Notification, PracticeQuestion, StudentEnrollment, 
                            TheoryExamMarks, MCQMarks, QuizMarks, AssignmentMarks, StudentTotalMarks)


def teacher_required(view_func):
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated or request.user.role != 'teacher':
            return redirect('teacher_login')
        # Check if teacher profile exists
        if not hasattr(request.user, 'teacher_profile'):
            messages.error(request, 'Teacher profile not found. Please contact administrator.')
            return redirect('role_selection')
        return view_func(request, *args, **kwargs)
    return wrapper


@teacher_required
def home(request):
    """Enhanced teacher dashboard with comprehensive analytics"""
    profile = request.user.teacher_profile
    
    # Get subjects assigned to this teacher by admin
    subjects = request.user.assigned_subjects.all()
    
    # Get all enrolled students for this teacher
    enrollments = StudentEnrollment.objects.filter(teacher=request.user).select_related('student', 'subject')
    total_students = enrollments.values('student').distinct().count()
    
    # Get exams created
    exams_created = Exam.objects.filter(created_by=request.user)
    
    # Get recent exam attempts
    enrolled_student_ids = enrollments.values_list('student_id', flat=True)
    recent_attempts = ExamAttempt.objects.filter(student_id__in=enrolled_student_ids).order_by('-attempted_at')[:10]
    
    # Statistics
    total_exams = exams_created.count()
    total_questions = Question.objects.filter(exam__created_by=request.user).count()
    total_exam_attempts = recent_attempts.count()
    
    # Subject-wise statistics
    subject_stats = []
    for subject in subjects:
        subject_enrollments = enrollments.filter(subject=subject)
        subject_stats.append({
            'subject': subject,
            'students': subject_enrollments.count(),
            'exams': exams_created.filter(subject=subject).count(),
        })
    
    # Performance metrics
    total_marks_obj = StudentTotalMarks.objects.filter(
        student_id__in=enrolled_student_ids,
        subject__in=subjects
    )
    
    avg_marks = 0
    if total_marks_obj.exists():
        avg_marks = total_marks_obj.aggregate(Avg('total_marks'))['total_marks__avg'] or 0
    
    # Get notifications
    notifications = Notification.objects.filter(is_active=True).order_by('-created_at')[:5]
    
    return render(request, 'teacher/home.html', {
        'profile': profile,
        'subjects': subjects,
        'total_students': total_students,
        'total_exams': total_exams,
        'total_questions': total_questions,
        'total_exam_attempts': total_exam_attempts,
        'avg_marks': round(avg_marks, 2),
        'subject_stats': subject_stats,
        'recent_attempts': recent_attempts,
        'notifications': notifications,
        'enrollments': enrollments,
    })


@teacher_required
def features(request):
    return render(request, 'teacher/features.html')


@teacher_required
def account(request):
    profile = request.user.teacher_profile
    if request.method == 'POST':
        request.user.first_name = request.POST.get('first_name', request.user.first_name)
        request.user.last_name  = request.POST.get('last_name', request.user.last_name)
        request.user.phone      = request.POST.get('phone', request.user.phone)
        request.user.save()
        profile.department  = request.POST.get('department', profile.department)
        profile.designation = request.POST.get('designation', profile.designation)
        profile.subjects    = request.POST.get('subjects', profile.subjects)
        profile.save()
        messages.success(request, 'Profile updated.')
    return render(request, 'teacher/account.html', {'profile': profile})


@teacher_required
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
            messages.success(request, 'Notification sent to students.')
        return redirect('teacher:home')
    return render(request, 'teacher/send_notification.html')


@teacher_required
def student_activity(request):
    students = StudentProfile.objects.select_related('user').order_by('-id')
    return render(request, 'teacher/student_activity.html', {'students': students})


@teacher_required
def student_detail(request, student_id):
    profile = get_object_or_404(StudentProfile, id=student_id)
    attempts = ExamAttempt.objects.filter(student=profile).order_by('-attempted_at')
    sessions = PracticeSession.objects.filter(student=profile).order_by('-practiced_at')
    return render(request, 'teacher/student_detail.html', {
        'profile': profile, 'attempts': attempts, 'sessions': sessions
    })


@teacher_required
def upload_questions(request):
    subjects = Subject.objects.all()
    if request.method == 'POST':
        subject_id  = request.POST.get('subject')
        topic       = request.POST.get('topic', '').strip()
        texts       = request.POST.getlist('question_text')
        opt_as      = request.POST.getlist('option_a')
        opt_bs      = request.POST.getlist('option_b')
        opt_cs      = request.POST.getlist('option_c')
        opt_ds      = request.POST.getlist('option_d')
        corrects    = request.POST.getlist('correct')
        explanations = request.POST.getlist('explanation')
        subject = get_object_or_404(Subject, id=subject_id)
        count = 0
        for i, text in enumerate(texts):
            if text.strip():
                PracticeQuestion.objects.create(
                    subject=subject, topic=topic, text=text,
                    option_a=opt_as[i], option_b=opt_bs[i],
                    option_c=opt_cs[i], option_d=opt_ds[i],
                    correct_option=corrects[i],
                    explanation=explanations[i] if i < len(explanations) else ''
                )
                count += 1
        messages.success(request, f'{count} practice questions uploaded.')
        return redirect('teacher:home')
    return render(request, 'teacher/upload_questions.html', {'subjects': subjects})


# ── MARKS MANAGEMENT ──────────────────────────────────

@teacher_required
def enroll_students(request, subject_id):
    """Enroll students in a subject"""
    subject = get_object_or_404(Subject, id=subject_id)
    teacher = request.user.teacher_profile
    
    if request.method == 'POST':
        student_ids = request.POST.getlist('student_ids')
        enrolled = 0
        for student_id in student_ids:
            try:
                student = StudentProfile.objects.get(id=student_id)
                StudentEnrollment.objects.get_or_create(
                    student=student,
                    subject=subject,
                    teacher=request.user
                )
                enrolled += 1
            except StudentProfile.DoesNotExist:
                continue
        messages.success(request, f'{enrolled} students enrolled in {subject.name}.')
        return redirect('teacher:marks_dashboard', subject_id=subject.id)
    
    # Get enrolled and available students
    enrolled_ids = StudentEnrollment.objects.filter(
        subject=subject, teacher=request.user
    ).values_list('student_id', flat=True)
    
    enrolled_students = StudentProfile.objects.filter(id__in=enrolled_ids)
    available_students = StudentProfile.objects.exclude(id__in=enrolled_ids)
    
    return render(request, 'teacher/enroll_students.html', {
        'subject': subject,
        'enrolled_students': enrolled_students,
        'available_students': available_students,
    })


@teacher_required
def marks_list(request):
    """List all subjects where teacher can manage marks"""
    # Get subjects assigned to this teacher
    assigned_subjects = request.user.assigned_subjects.all()
    
    # Group by subject
    subjects = []
    for subject in assigned_subjects:
        student_count = StudentEnrollment.objects.filter(
            subject=subject, teacher=request.user
        ).count()
        subjects.append({
            'subject': subject,
            'student_count': student_count,
        })
    
    return render(request, 'teacher/marks_list.html', {
        'subjects': subjects,
    })


@teacher_required
def marks_dashboard(request, subject_id):
    """Main dashboard for marks management"""
    subject = get_object_or_404(Subject, id=subject_id)
    
    # Get enrolled students for this teacher and subject
    enrollments = StudentEnrollment.objects.filter(
        subject=subject, teacher=request.user
    ).select_related('student')
    
    students = [e.student for e in enrollments]
    
    return render(request, 'teacher/marks_dashboard.html', {
        'subject': subject,
        'students': students,
    })


@teacher_required
def manage_theory_marks(request, subject_id):
    """Manage theory exam marks"""
    subject = get_object_or_404(Subject, id=subject_id)
    
    # Get enrolled students for this teacher and subject
    enrollments = StudentEnrollment.objects.filter(
        subject=subject, teacher=request.user
    ).select_related('student')
    
    students = [e.student for e in enrollments]
    
    if request.method == 'POST':
        exam_name = request.POST.get('exam_name', '').strip()
        total_marks = float(request.POST.get('total_marks', 50))
        
        if not exam_name:
            messages.error(request, 'Please enter exam name.')
            return redirect('teacher:manage_theory_marks', subject_id=subject.id)
        
        updated = 0
        for student in students:
            marks_str = request.POST.get(f'marks_{student.id}', '').strip()
            remarks = request.POST.get(f'remarks_{student.id}', '').strip()
            
            if marks_str:
                try:
                    marks = float(marks_str)
                    if marks <= total_marks:
                        theory_mark, _ = TheoryExamMarks.objects.update_or_create(
                            student=student,
                            exam_name=exam_name,
                            subject=subject,
                            defaults={
                                'teacher': request.user,
                                'marks_obtained': marks,
                                'total_marks': total_marks,
                                'remarks': remarks
                            }
                        )
                        updated += 1
                except ValueError:
                    continue
        
        # Update total marks
        for student in students:
            update_student_total_marks(student, subject)
        
        messages.success(request, f'Theory marks updated for {updated} students.')
        return redirect('teacher:marks_dashboard', subject_id=subject.id)
    
    # Get all exams for this subject
    exams = TheoryExamMarks.objects.filter(
        subject=subject, teacher=request.user
    ).values_list('exam_name', flat=True).distinct()
    
    return render(request, 'teacher/manage_theory_marks.html', {
        'subject': subject,
        'students': students,
        'exams': exams,
    })


@teacher_required
def manage_mcq_marks(request, subject_id):
    """Manage MCQ exam marks"""
    subject = get_object_or_404(Subject, id=subject_id)
    
    # Get enrolled students for this teacher and subject
    enrollments = StudentEnrollment.objects.filter(
        subject=subject, teacher=request.user
    ).select_related('student')
    
    students = [e.student for e in enrollments]
    exams = Exam.objects.filter(subject=subject)
    
    if request.method == 'POST':
        exam_id = request.POST.get('exam_id')
        exam = get_object_or_404(Exam, id=exam_id) if exam_id else None
        
        updated = 0
        for student in students:
            marks_str = request.POST.get(f'marks_{student.id}', '').strip()
            correct_str = request.POST.get(f'correct_{student.id}', '').strip()
            
            if marks_str:
                try:
                    marks = float(marks_str)
                    correct = int(correct_str) if correct_str else 0
                    
                    if marks <= 30:
                        mcq_mark, _ = MCQMarks.objects.update_or_create(
                            student=student,
                            subject=subject,
                            exam=exam,
                            defaults={
                                'teacher': request.user,
                                'marks_obtained': marks,
                                'total_questions': 30,
                                'correct_answers': correct
                            }
                        )
                        updated += 1
                except ValueError:
                    continue
        
        # Update total marks
        for student in students:
            update_student_total_marks(student, subject)
        
        messages.success(request, f'MCQ marks updated for {updated} students.')
        return redirect('teacher:marks_dashboard', subject_id=subject.id)
    
    return render(request, 'teacher/manage_mcq_marks.html', {
        'subject': subject,
        'students': students,
        'exams': exams,
    })


@teacher_required
def manage_quiz_marks(request, subject_id):
    """Manage quiz marks"""
    subject = get_object_or_404(Subject, id=subject_id)
    
    # Get enrolled students for this teacher and subject
    enrollments = StudentEnrollment.objects.filter(
        subject=subject, teacher=request.user
    ).select_related('student')
    
    students = [e.student for e in enrollments]
    
    if request.method == 'POST':
        quiz_name = request.POST.get('quiz_name', '').strip()
        total_marks = float(request.POST.get('total_marks', 10))
        
        if not quiz_name:
            messages.error(request, 'Please enter quiz name.')
            return redirect('teacher:manage_quiz_marks', subject_id=subject.id)
        
        updated = 0
        for student in students:
            marks_str = request.POST.get(f'marks_{student.id}', '').strip()
            remarks = request.POST.get(f'remarks_{student.id}', '').strip()
            
            if marks_str:
                try:
                    marks = float(marks_str)
                    if marks <= total_marks:
                        quiz_mark, _ = QuizMarks.objects.update_or_create(
                            student=student,
                            quiz_name=quiz_name,
                            subject=subject,
                            defaults={
                                'teacher': request.user,
                                'marks_obtained': marks,
                                'total_marks': total_marks,
                                'remarks': remarks
                            }
                        )
                        updated += 1
                except ValueError:
                    continue
        
        # Update total marks
        for student in students:
            update_student_total_marks(student, subject)
        
        messages.success(request, f'Quiz marks updated for {updated} students.')
        return redirect('teacher:marks_dashboard', subject_id=subject.id)
    
    # Get all quizzes for this subject
    quizzes = QuizMarks.objects.filter(
        subject=subject, teacher=request.user
    ).values_list('quiz_name', flat=True).distinct()
    
    return render(request, 'teacher/manage_quiz_marks.html', {
        'subject': subject,
        'students': students,
        'quizzes': quizzes,
    })


@teacher_required
def manage_assignment_marks(request, subject_id):
    """Manage assignment marks"""
    subject = get_object_or_404(Subject, id=subject_id)
    
    # Get enrolled students for this teacher and subject
    enrollments = StudentEnrollment.objects.filter(
        subject=subject, teacher=request.user
    ).select_related('student')
    
    students = [e.student for e in enrollments]
    
    if request.method == 'POST':
        assignment_name = request.POST.get('assignment_name', '').strip()
        total_marks = float(request.POST.get('total_marks', 10))
        
        if not assignment_name:
            messages.error(request, 'Please enter assignment name.')
            return redirect('teacher:manage_assignment_marks', subject_id=subject.id)
        
        updated = 0
        for student in students:
            marks_str = request.POST.get(f'marks_{student.id}', '').strip()
            remarks = request.POST.get(f'remarks_{student.id}', '').strip()
            
            if marks_str:
                try:
                    marks = float(marks_str)
                    if marks <= total_marks:
                        assignment_mark, _ = AssignmentMarks.objects.update_or_create(
                            student=student,
                            assignment_name=assignment_name,
                            subject=subject,
                            defaults={
                                'teacher': request.user,
                                'marks_obtained': marks,
                                'total_marks': total_marks,
                                'remarks': remarks
                            }
                        )
                        updated += 1
                except ValueError:
                    continue
        
        # Update total marks
        for student in students:
            update_student_total_marks(student, subject)
        
        messages.success(request, f'Assignment marks updated for {updated} students.')
        return redirect('teacher:marks_dashboard', subject_id=subject.id)
    
    # Get all assignments for this subject
    assignments = AssignmentMarks.objects.filter(
        subject=subject, teacher=request.user
    ).values_list('assignment_name', flat=True).distinct()
    
    return render(request, 'teacher/manage_assignment_marks.html', {
        'subject': subject,
        'students': students,
        'assignments': assignments,
    })


def get_first_teacher(student, subject):
    """Get the first teacher assigned to this student-subject pair"""
    enrollment = StudentEnrollment.objects.filter(
        student=student, subject=subject
    ).first()
    return enrollment.teacher if enrollment else None


def update_student_total_marks(student, subject):
    """Update total marks for a student in a subject using the centralized sync method"""
    StudentTotalMarks.sync_all_marks(student, subject)


@teacher_required
def view_student_marks(request, subject_id, student_id):
    """View detailed marks for a student in a subject"""
    subject = get_object_or_404(Subject, id=subject_id)
    student = get_object_or_404(StudentProfile, id=student_id)
    
    # Verify teacher has enrolled this student
    enrollment = get_object_or_404(
        StudentEnrollment,
        student=student,
        subject=subject,
        teacher=request.user
    )
    
    theory_marks = TheoryExamMarks.objects.filter(student=student, subject=subject)
    mcq_marks = MCQMarks.objects.filter(student=student, subject=subject)
    quiz_marks = QuizMarks.objects.filter(student=student, subject=subject)
    assignment_marks = AssignmentMarks.objects.filter(student=student, subject=subject)
    total_marks = StudentTotalMarks.objects.filter(student=student, subject=subject).first()
    
    return render(request, 'teacher/view_student_marks.html', {
        'subject': subject,
        'student': student,
        'theory_marks': theory_marks,
        'mcq_marks': mcq_marks,
        'quiz_marks': quiz_marks,
        'assignment_marks': assignment_marks,
        'total_marks': total_marks,
    })


# ── STUDENT PERFORMANCE ANALYTICS ───────────────────────

@teacher_required
def student_performance(request):
    """View overall student performance and analytics"""
    # Get all enrolled students for this teacher
    enrollments = StudentEnrollment.objects.filter(teacher=request.user).select_related('student', 'subject')
    
    # Get total marks for all students
    student_performance_data = []
    for enrollment in enrollments:
        total_marks = StudentTotalMarks.objects.filter(
            student=enrollment.student,
            subject=enrollment.subject
        ).first()
        
        student_performance_data.append({
            'enrollment': enrollment,
            'total_marks': total_marks,
            'marks': total_marks.total_marks if total_marks else 0,
        })
    
    # Sort by marks (descending)
    student_performance_data.sort(key=lambda x: x['marks'], reverse=True)
    
    # Calculate statistics
    marks_list = [item['marks'] for item in student_performance_data if item['marks'] > 0]
    avg_marks = sum(marks_list) / len(marks_list) if marks_list else 0
    max_marks = max(marks_list) if marks_list else 0
    min_marks = min(marks_list) if marks_list else 0
    
    return render(request, 'teacher/student_performance.html', {
        'student_performance_data': student_performance_data,
        'avg_marks': round(avg_marks, 2),
        'max_marks': round(max_marks, 2),
        'min_marks': round(min_marks, 2),
        'total_students': len(student_performance_data),
    })


@teacher_required
def exam_analytics(request):
    """View exam analytics and student performance in exams"""
    exams = Exam.objects.filter(created_by=request.user).prefetch_related('questions')
    
    exam_data = []
    for exam in exams:
        attempts = ExamAttempt.objects.filter(exam=exam)
        
        if attempts.exists():
            avg_score = attempts.aggregate(Avg('percentage'))['percentage__avg'] or 0
            max_score = attempts.aggregate(Max('percentage'))['percentage__max'] or 0
            min_score = attempts.aggregate(Min('percentage'))['percentage__min'] or 0
            total_attempts = attempts.count()
        else:
            avg_score = max_score = min_score = 0
            total_attempts = 0
        
        exam_data.append({
            'exam': exam,
            'total_questions': exam.questions.count(),
            'total_attempts': total_attempts,
            'avg_score': round(avg_score, 2),
            'max_score': round(max_score, 2),
            'min_score': round(min_score, 2),
        })
    
    return render(request, 'teacher/exam_analytics.html', {'exam_data': exam_data})


@teacher_required
def student_subject_analytics(request, subject_id):
    """View detailed analytics for a specific subject"""
    subject = get_object_or_404(Subject, id=subject_id)
    
    # Verify teacher teaches this subject
    enrollments = StudentEnrollment.objects.filter(
        subject=subject, teacher=request.user
    ).select_related('student')
    
    if not enrollments.exists():
        messages.error(request, 'You do not have access to this subject.')
        return redirect('teacher:home')
    
    # Get student performance in this subject
    student_data = []
    for enrollment in enrollments:
        total_marks = StudentTotalMarks.objects.filter(
            student=enrollment.student,
            subject=subject
        ).first()
        
        exam_attempts = ExamAttempt.objects.filter(
            student=enrollment.student,
            exam__subject=subject
        ).aggregate(
            avg_percentage=Avg('percentage'),
            total_attempts=Count('id')
        )
        
        student_data.append({
            'enrollment': enrollment,
            'total_marks': total_marks,
            'exam_attempts': exam_attempts['total_attempts'],
            'avg_exam_percentage': round(exam_attempts['avg_percentage'], 2) if exam_attempts['avg_percentage'] else 0,
        })
    
    # Sort by total marks
    student_data.sort(key=lambda x: x['total_marks'].total_marks if x['total_marks'] else 0, reverse=True)
    
    # Calculate class statistics
    total_marks_list = [s['total_marks'].total_marks for s in student_data if s['total_marks']]
    
    class_avg = sum(total_marks_list) / len(total_marks_list) if total_marks_list else 0
    class_max = max(total_marks_list) if total_marks_list else 0
    class_min = min(total_marks_list) if total_marks_list else 0
    
    return render(request, 'teacher/subject_analytics.html', {
        'subject': subject,
        'student_data': student_data,
        'class_avg': round(class_avg, 2),
        'class_max': round(class_max, 2),
        'class_min': round(class_min, 2),
        'total_students': len(student_data),
    })


# ── EXAM CREATION ───────────────────────────────────────

@teacher_required
def create_exam(request):
    """Create a new exam (for assigned subjects)"""
    # Show only subjects assigned to this teacher
    subjects = request.user.assigned_subjects.all().order_by('name')
    
    # If no subjects assigned, inform the user
    if not subjects.exists():
        messages.warning(request, 'No subjects have been assigned to you by the admin yet.')
    
    if request.method == 'POST':
        title    = request.POST.get('title', '').strip()
        subj_id  = request.POST.get('subject')
        password = request.POST.get('password', '').strip()
        duration = request.POST.get('duration', 60)
        total    = request.POST.get('total_marks', 100)
        
        if not title:
            messages.error(request, 'Please enter exam title.')
            return render(request, 'teacher/create_exam.html', {'subjects': subjects})
        
        subject  = get_object_or_404(Subject, id=subj_id)
        
        exam = Exam.objects.create(
            title=title, subject=subject, password=password,
            duration_minutes=int(duration), total_marks=int(total),
            created_by=request.user
        )
        messages.success(request, f'Exam "{title}" created. Now add questions.')
        return redirect('teacher:add_questions', exam_id=exam.id)
    
    return render(request, 'teacher/create_exam.html', {'subjects': subjects})


@teacher_required
def add_questions(request, exam_id):
    """Add questions to an exam"""
    exam = get_object_or_404(Exam, id=exam_id)
    
    # Verify teacher created this exam
    if exam.created_by != request.user:
        messages.error(request, 'You do not have permission to edit this exam.')
        return redirect('teacher:home')
    
    if request.method == 'POST':
        texts   = request.POST.getlist('question_text')
        opt_as  = request.POST.getlist('option_a')
        opt_bs  = request.POST.getlist('option_b')
        opt_cs  = request.POST.getlist('option_c')
        opt_ds  = request.POST.getlist('option_d')
        corrects = request.POST.getlist('correct')
        markss  = request.POST.getlist('marks')
        
        count = 0
        for i, text in enumerate(texts):
            if text.strip():
                Question.objects.create(
                    exam=exam, text=text,
                    option_a=opt_as[i], option_b=opt_bs[i],
                    option_c=opt_cs[i], option_d=opt_ds[i],
                    correct_option=corrects[i], marks=int(markss[i] or 1)
                )
                count += 1
        
        messages.success(request, f'{count} questions added to exam.')
        return redirect('teacher:exam_analytics')
    
    existing = exam.questions.all()
    return render(request, 'teacher/add_questions.html', {'exam': exam, 'questions': existing})
