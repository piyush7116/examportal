from django.db import models
from accounts.models import User, StudentProfile


class Subject(models.Model):
    name = models.CharField(max_length=100)
    topics = models.TextField(help_text="Comma-separated topics")
    uploaded_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    teachers = models.ManyToManyField(User, related_name='assigned_subjects', blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def get_topics_list(self):
        return [t.strip() for t in self.topics.split(',') if t.strip()]

    def __str__(self):
        return self.name


class Exam(models.Model):
    STATUS_CHOICES = [('active', 'Active'), ('inactive', 'Inactive')]
    title = models.CharField(max_length=200)
    subject = models.ForeignKey(Subject, on_delete=models.CASCADE)
    password = models.CharField(max_length=50)
    duration_minutes = models.IntegerField(default=60)
    total_marks = models.IntegerField(default=100)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='active')
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title


class Question(models.Model):
    exam = models.ForeignKey(Exam, on_delete=models.CASCADE, related_name='questions')
    text = models.TextField()
    option_a = models.CharField(max_length=300)
    option_b = models.CharField(max_length=300)
    option_c = models.CharField(max_length=300)
    option_d = models.CharField(max_length=300)
    correct_option = models.CharField(max_length=1, choices=[('A','A'),('B','B'),('C','C'),('D','D')])
    marks = models.IntegerField(default=1)

    def __str__(self):
        return self.text[:60]


class PracticeQuestion(models.Model):
    subject = models.ForeignKey(Subject, on_delete=models.CASCADE, related_name='practice_questions')
    topic = models.CharField(max_length=100)
    text = models.TextField()
    option_a = models.CharField(max_length=300)
    option_b = models.CharField(max_length=300)
    option_c = models.CharField(max_length=300)
    option_d = models.CharField(max_length=300)
    correct_option = models.CharField(max_length=1, choices=[('A','A'),('B','B'),('C','C'),('D','D')])
    explanation = models.TextField(blank=True)

    def __str__(self):
        return self.text[:60]


class ExamAttempt(models.Model):
    student = models.ForeignKey(StudentProfile, on_delete=models.CASCADE)
    exam = models.ForeignKey(Exam, on_delete=models.CASCADE)
    score = models.IntegerField(default=0)
    total = models.IntegerField(default=0)
    percentage = models.FloatField(default=0)
    attempted_at = models.DateTimeField(auto_now_add=True)
    answers = models.JSONField(default=dict)

    class Meta:
        unique_together = ('student', 'exam')

    def __str__(self):
        return f"{self.student} - {self.exam} ({self.percentage:.1f}%)"


class PracticeSession(models.Model):
    student = models.ForeignKey(StudentProfile, on_delete=models.CASCADE)
    subject = models.ForeignKey(Subject, on_delete=models.CASCADE)
    topic = models.CharField(max_length=100)
    score = models.IntegerField(default=0)
    total = models.IntegerField(default=0)
    practiced_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.student} - {self.subject} ({self.topic})"


class Notification(models.Model):
    PRIORITY_CHOICES = [('high', 'High'), ('medium', 'Medium'), ('low', 'Low')]
    title = models.CharField(max_length=200)
    message = models.TextField()
    priority = models.CharField(max_length=10, choices=PRIORITY_CHOICES, default='medium')
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return self.title


# ── MARKS MANAGEMENT ──────────────────────────────────
class StudentEnrollment(models.Model):
    """Enrolls students in subjects taught by teachers"""
    student = models.ForeignKey(StudentProfile, on_delete=models.CASCADE, related_name='enrollments')
    subject = models.ForeignKey(Subject, on_delete=models.CASCADE, related_name='enrollments')
    teacher = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='enrolled_students')
    enrolled_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('student', 'subject', 'teacher')

    def __str__(self):
        return f"{self.student} enrolled in {self.subject} by {self.teacher}"
    
    @staticmethod
    def auto_enroll_by_department(student_profile):
        """
        Auto-enroll a student in all subjects taught by teachers of their department.
        Called when student registers or updates their department.
        """
        from accounts.models import TeacherProfile
        from django.db import transaction
        
        if not student_profile.department:
            return 0
        
        # Find all teachers in the same department
        teachers = TeacherProfile.objects.filter(department=student_profile.department)
        enrollment_count = 0
        
        with transaction.atomic():
            for teacher_profile in teachers:
                teacher_user = teacher_profile.user
                # Use the new assigned_subjects relationship
                subjects = teacher_user.assigned_subjects.all()
                
                for subject in subjects:
                    # Create enrollment only if it doesn't exist
                    enrollment, created = StudentEnrollment.objects.get_or_create(
                        student=student_profile,
                        subject=subject,
                        teacher=teacher_user
                    )
                    if created:
                        enrollment_count += 1
        
        return enrollment_count


class TheoryExamMarks(models.Model):
    """Marks for theory/written exams"""
    student = models.ForeignKey(StudentProfile, on_delete=models.CASCADE, related_name='theory_exam_marks')
    subject = models.ForeignKey(Subject, on_delete=models.CASCADE)
    teacher = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    exam_name = models.CharField(max_length=200)
    marks_obtained = models.FloatField(default=0)
    total_marks = models.FloatField(default=50)
    date_marked = models.DateTimeField(auto_now=True)
    remarks = models.TextField(blank=True)

    class Meta:
        unique_together = ('student', 'exam_name', 'subject')

    def __str__(self):
        return f"{self.student} - {self.exam_name} ({self.marks_obtained}/{self.total_marks})"


class MCQMarks(models.Model):
    """Marks for Online MCQ exams (30 questions based)"""
    student = models.ForeignKey(StudentProfile, on_delete=models.CASCADE, related_name='mcq_marks')
    subject = models.ForeignKey(Subject, on_delete=models.CASCADE)
    exam = models.ForeignKey(Exam, on_delete=models.SET_NULL, null=True)
    teacher = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    marks_obtained = models.FloatField(default=0)
    total_questions = models.IntegerField(default=30)
    correct_answers = models.IntegerField(default=0)
    date_marked = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('student', 'subject', 'exam')

    def __str__(self):
        return f"{self.student} - MCQ {self.subject} ({self.marks_obtained}/30)"


class QuizMarks(models.Model):
    """Marks for Quizzes"""
    student = models.ForeignKey(StudentProfile, on_delete=models.CASCADE, related_name='quiz_marks')
    subject = models.ForeignKey(Subject, on_delete=models.CASCADE)
    teacher = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    quiz_name = models.CharField(max_length=200)
    marks_obtained = models.FloatField(default=0)
    total_marks = models.FloatField(default=10)
    date_marked = models.DateTimeField(auto_now=True)
    remarks = models.TextField(blank=True)

    class Meta:
        unique_together = ('student', 'quiz_name', 'subject')

    def __str__(self):
        return f"{self.student} - {self.quiz_name} ({self.marks_obtained}/{self.total_marks})"


class AssignmentMarks(models.Model):
    """Marks for Assignments"""
    student = models.ForeignKey(StudentProfile, on_delete=models.CASCADE, related_name='assignment_marks')
    subject = models.ForeignKey(Subject, on_delete=models.CASCADE)
    teacher = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    assignment_name = models.CharField(max_length=200)
    marks_obtained = models.FloatField(default=0)
    total_marks = models.FloatField(default=10)
    date_marked = models.DateTimeField(auto_now=True)
    remarks = models.TextField(blank=True)

    class Meta:
        unique_together = ('student', 'assignment_name', 'subject')

    def __str__(self):
        return f"{self.student} - {self.assignment_name} ({self.marks_obtained}/{self.total_marks})"


class StudentTotalMarks(models.Model):
    """Total marks out of 100 for each student per subject"""
    student = models.ForeignKey(StudentProfile, on_delete=models.CASCADE, related_name='total_marks')
    subject = models.ForeignKey(Subject, on_delete=models.CASCADE)
    teacher = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    
    # Components (max marks: Theory-50, MCQ-30, Quizzes-10, Assignments-10 = 100)
    theory_marks = models.FloatField(default=0)
    mcq_marks = models.FloatField(default=0)
    quiz_marks = models.FloatField(default=0)
    assignment_marks = models.FloatField(default=0)
    
    # Weightage (percentages)
    theory_weight = models.FloatField(default=50)
    mcq_weight = models.FloatField(default=30)
    quiz_weight = models.FloatField(default=10)
    assignment_weight = models.FloatField(default=10)
    
    total_marks = models.FloatField(default=0)  # Out of 100
    last_updated = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('student', 'subject')

    def calculate_total(self):
        """Calculate total marks out of 100 (weighted sum)"""
        self.total_marks = (
            (self.theory_marks) +
            (self.mcq_marks) +
            (self.quiz_marks) +
            (self.assignment_marks)
        )
        return self.total_marks

    @classmethod
    def sync_all_marks(cls, student, subject):
        """Aggregate all marks for a student in a subject and update total"""
        # 1. Sum Theory Marks (Usually 50 max)
        theory = TheoryExamMarks.objects.filter(student=student, subject=subject).aggregate(total=models.Sum('marks_obtained'))['total'] or 0
        
        # 2. MCQ Marks (Scale latest attempt to 30 max)
        mcq = MCQMarks.objects.filter(student=student, subject=subject).aggregate(total=models.Sum('marks_obtained'))['total'] or 0
        
        # 3. Quiz Marks (Sum up to 10 max)
        quiz = QuizMarks.objects.filter(student=student, subject=subject).aggregate(total=models.Sum('marks_obtained'))['total'] or 0
        
        # 4. Assignment Marks (Sum up to 10 max)
        assignment = AssignmentMarks.objects.filter(student=student, subject=subject).aggregate(total=models.Sum('marks_obtained'))['total'] or 0
        
        # Get or create total marks record
        total_obj, _ = cls.objects.get_or_create(student=student, subject=subject)
        
        # Update components
        total_obj.theory_marks = min(theory, total_obj.theory_weight)
        total_obj.mcq_marks = min(mcq, total_obj.mcq_weight)
        total_obj.quiz_marks = min(quiz, total_obj.quiz_weight)
        total_obj.assignment_marks = min(assignment, total_obj.assignment_weight)
        
        total_obj.calculate_total()
        total_obj.save()
        return total_obj

    def __str__(self):
        return f"{self.student} - {self.subject} ({self.total_marks}/100)"

# Signals to auto-update marks
from django.db.models.signals import post_save
from django.dispatch import receiver

@receiver(post_save, sender=ExamAttempt)
def update_mcq_marks_on_attempt(sender, instance, created, **kwargs):
    """When an exam is submitted, update the MCQMarks and TotalMarks"""
    if created:
        subject = instance.exam.subject
        student = instance.student
        
        # Get the teacher for this subject enrollment
        enrollment = StudentEnrollment.objects.filter(student=student, subject=subject).first()
        teacher = enrollment.teacher if enrollment else None
        
        # Calculate score out of 30
        mcq_score = (instance.score / instance.total * 30) if instance.total > 0 else 0
        
        # Update or create MCQMarks
        MCQMarks.objects.update_or_create(
            student=student,
            subject=subject,
            exam=instance.exam,
            defaults={
                'teacher': teacher,
                'marks_obtained': round(mcq_score, 2),
                'total_questions': 30,
                'correct_answers': instance.score # assuming 1 mark per question for tracking
            }
        )
        
        # Sync total marks
        StudentTotalMarks.sync_all_marks(student, subject)
