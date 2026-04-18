from django.contrib import admin
from .models import (Subject, Exam, Question, PracticeQuestion, ExamAttempt, PracticeSession, 
                     Notification, StudentEnrollment, TheoryExamMarks, MCQMarks, QuizMarks, 
                     AssignmentMarks, StudentTotalMarks)

admin.site.register(Subject)
admin.site.register(Exam)
admin.site.register(Question)
admin.site.register(PracticeQuestion)
admin.site.register(ExamAttempt)
admin.site.register(PracticeSession)
admin.site.register(Notification)

# Marks Management
admin.site.register(StudentEnrollment)
admin.site.register(TheoryExamMarks)
admin.site.register(MCQMarks)
admin.site.register(QuizMarks)
admin.site.register(AssignmentMarks)
admin.site.register(StudentTotalMarks)
