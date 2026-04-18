from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from .models import (Subject, Exam, Question, PracticeQuestion, ExamAttempt, PracticeSession, 
                     Notification, StudentEnrollment, TheoryExamMarks, MCQMarks, QuizMarks, 
                     AssignmentMarks, StudentTotalMarks)
import json


def student_required(view_func):
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated or request.user.role != 'student':
            return redirect('student_login')
        # Check if student profile exists
        if not hasattr(request.user, 'student_profile'):
            messages.error(request, 'Student profile not found. Please contact administrator.')
            return redirect('role_selection')
        return view_func(request, *args, **kwargs)
    return wrapper


@student_required
def home(request):
    profile = request.user.student_profile
    recent_attempts = ExamAttempt.objects.filter(student=profile).order_by('-attempted_at')[:3]
    practice_sessions = PracticeSession.objects.filter(student=profile).count()
    notifications = Notification.objects.filter(is_active=True).order_by('-created_at')[:5]
    exams_taken = ExamAttempt.objects.filter(student=profile).count()
    subjects = Subject.objects.all()
    return render(request, 'student/home.html', {
        'profile': profile,
        'recent_attempts': recent_attempts,
        'practice_count': practice_sessions,
        'notifications': notifications,
        'exams_taken': exams_taken,
        'subjects': subjects,
    })


@student_required
def features(request):
    return render(request, 'student/features.html')


@student_required
def account(request):
    profile = request.user.student_profile
    if request.method == 'POST':
        request.user.first_name = request.POST.get('first_name', request.user.first_name)
        request.user.last_name  = request.POST.get('last_name', request.user.last_name)
        request.user.phone      = request.POST.get('phone', request.user.phone)
        request.user.save()
        
        old_department = profile.department
        new_department = request.POST.get('department', profile.department)
        
        profile.department = new_department
        profile.semester   = request.POST.get('semester', profile.semester)
        profile.email      = request.POST.get('email', profile.email)
        profile.save()
        
        # Auto-enroll if department changed
        if old_department != new_department:
            enrollment_count = StudentEnrollment.auto_enroll_by_department(profile)
            messages.success(request, f'Profile updated! Auto-enrolled in {enrollment_count} new courses.')
        else:
            messages.success(request, 'Profile updated successfully.')
    return render(request, 'student/account.html', {'profile': profile})


# ── EXAM MANAGEMENT ───────────────────────────────────
@student_required
def exam_list(request):
    exams = Exam.objects.filter(status='active')
    profile = request.user.student_profile
    attempted_ids = ExamAttempt.objects.filter(student=profile).values_list('exam_id', flat=True)
    return render(request, 'student/exam_list.html', {
        'exams': exams, 'attempted_ids': list(attempted_ids)
    })


@student_required
def exam_enter(request, exam_id):
    exam = get_object_or_404(Exam, id=exam_id)
    profile = request.user.student_profile
    if ExamAttempt.objects.filter(student=profile, exam=exam).exists():
        messages.warning(request, 'You have already attempted this exam.')
        return redirect('student:exam_list')
    if request.method == 'POST':
        entered_pass = request.POST.get('exam_password', '').strip()
        if entered_pass == exam.password:
            return redirect('student:exam_take', exam_id=exam.id)
        else:
            messages.error(request, 'Incorrect exam password.')
    return render(request, 'student/exam_enter.html', {'exam': exam})


@student_required
def exam_take(request, exam_id):
    exam = get_object_or_404(Exam, id=exam_id)
    profile = request.user.student_profile
    if ExamAttempt.objects.filter(student=profile, exam=exam).exists():
        messages.warning(request, 'You have already attempted this exam.')
        return redirect('student:exam_list')
    questions = exam.questions.all()
    if request.method == 'POST':
        answers = {}
        score = 0
        for q in questions:
            selected = request.POST.get(f'q_{q.id}', '')
            answers[str(q.id)] = selected
            if selected == q.correct_option:
                score += q.marks
        total = sum(q.marks for q in questions)
        pct = (score / total * 100) if total > 0 else 0
        ExamAttempt.objects.create(
            student=profile, exam=exam, score=score, total=total,
            percentage=round(pct, 2), answers=answers
        )
        messages.success(request, f'Exam submitted! You scored {score}/{total} ({pct:.1f}%)')
        return redirect('student:history')
    return render(request, 'student/exam_take.html', {
        'exam': exam, 'questions': questions,
        'duration': exam.duration_minutes * 60
    })


# ── QUESTION PRACTICE ─────────────────────────────────
@student_required
def question_practice(request):
    subjects = Subject.objects.all()
    selected_subject = None
    topics = []
    if request.GET.get('subject'):
        selected_subject = get_object_or_404(Subject, id=request.GET['subject'])
        topics = selected_subject.get_topics_list()
    return render(request, 'student/question_practice.html', {
        'subjects': subjects, 'selected_subject': selected_subject, 'topics': topics
    })


@student_required
def practice_quiz(request, subject_id, topic):
    subject = get_object_or_404(Subject, id=subject_id)
    questions = PracticeQuestion.objects.filter(subject=subject, topic=topic)
    if request.method == 'POST':
        score = 0
        for q in questions:
            if request.POST.get(f'q_{q.id}') == q.correct_option:
                score += 1
        profile = request.user.student_profile
        PracticeSession.objects.create(
            student=profile, subject=subject, topic=topic,
            score=score, total=questions.count()
        )
        messages.success(request, f'Practice done! Score: {score}/{questions.count()}')
        return redirect('student:question_practice')
    return render(request, 'student/practice_quiz.html', {
        'subject': subject, 'topic': topic, 'questions': questions
    })


# ── HISTORY & MARKS ───────────────────────────────────
@student_required
def history(request):
    profile = request.user.student_profile
    attempts = ExamAttempt.objects.filter(student=profile).order_by('-attempted_at')
    sessions = PracticeSession.objects.filter(student=profile).order_by('-practiced_at')
    return render(request, 'student/history.html', {
        'attempts': attempts, 'sessions': sessions
    })


# ── NOTIFICATIONS ─────────────────────────────────────
@student_required
def notifications(request):
    notifs = Notification.objects.filter(is_active=True).order_by('-created_at')
    return render(request, 'student/notifications.html', {'notifications': notifs})


# ── MARKS & GRADES ────────────────────────────────────
@student_required
def view_marks(request):
    """View all subjects where student is enrolled and their total marks"""
    profile = request.user.student_profile
    
    # Get all enrollments for this student
    enrollments = StudentEnrollment.objects.filter(student=profile).select_related('subject')
    
    # Get total marks for each subject
    subject_marks = []
    for enrollment in enrollments:
        total_marks = StudentTotalMarks.objects.filter(
            student=profile,
            subject=enrollment.subject
        ).first()
        subject_marks.append({
            'subject': enrollment.subject,
            'total_marks': total_marks,
            'teacher': enrollment.teacher
        })
    
    return render(request, 'student/view_marks.html', {
        'subject_marks': subject_marks,
    })


@student_required
def subject_marks_detail(request, subject_id):
    """View detailed marks for a specific subject"""
    profile = request.user.student_profile
    subject = get_object_or_404(Subject, id=subject_id)
    
    # Verify student is enrolled in this subject
    enrollment = get_object_or_404(
        StudentEnrollment,
        student=profile,
        subject=subject
    )
    
    # Get all marks for this subject
    theory_marks = TheoryExamMarks.objects.filter(
        student=profile,
        subject=subject
    ).order_by('-date_marked')
    
    mcq_marks = MCQMarks.objects.filter(
        student=profile,
        subject=subject
    ).order_by('-date_marked')
    
    quiz_marks = QuizMarks.objects.filter(
        student=profile,
        subject=subject
    ).order_by('-date_marked')
    
    assignment_marks = AssignmentMarks.objects.filter(
        student=profile,
        subject=subject
    ).order_by('-date_marked')
    
    # Get total marks
    total_marks = StudentTotalMarks.objects.filter(
        student=profile,
        subject=subject
    ).first()
    
    # Calculate aggregates
    theory_total = sum(m.marks_obtained for m in theory_marks)
    theory_max = sum(m.total_marks for m in theory_marks)
    
    quiz_total = sum(m.marks_obtained for m in quiz_marks)
    quiz_max = sum(m.total_marks for m in quiz_marks)
    
    assignment_total = sum(m.marks_obtained for m in assignment_marks)
    assignment_max = sum(m.total_marks for m in assignment_marks)
    
    mcq_total = sum(m.marks_obtained for m in mcq_marks)
    
    return render(request, 'student/subject_marks_detail.html', {
        'subject': subject,
        'teacher': enrollment.teacher,
        'theory_marks': theory_marks,
        'theory_total': theory_total,
        'theory_max': theory_max,
        'mcq_marks': mcq_marks,
        'mcq_total': mcq_total,
        'quiz_marks': quiz_marks,
        'quiz_total': quiz_total,
        'quiz_max': quiz_max,
        'assignment_marks': assignment_marks,
        'assignment_total': assignment_total,
        'assignment_max': assignment_max,
        'total_marks': total_marks,
    })


@student_required
def view_exam_result(request, attempt_id):
    """View detailed exam results with correct answers"""
    profile = request.user.student_profile
    attempt = get_object_or_404(ExamAttempt, id=attempt_id, student=profile)
    exam = attempt.exam
    questions = exam.questions.all()
    
    # attempt.answers is a dict like {'question_id': 'selected_option'}
    student_answers = attempt.answers
    
    return render(request, 'student/exam_result.html', {
        'attempt': attempt,
        'exam': exam,
        'questions': questions,
        'student_answers': student_answers,
    })
