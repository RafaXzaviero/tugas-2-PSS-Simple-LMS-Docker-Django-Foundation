from django.db import models

# Create your models here.

from django.db import models
from django.contrib.auth.models import AbstractUser

# 1. Custom User Model
class User(AbstractUser):
    ROLE_CHOICES = (
        ('admin', 'Admin'),
        ('instructor', 'Instructor'),
        ('student', 'Student'),
    )
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='student')

# 2. Category Model (Self-referencing)
class Category(models.Model):
    name = models.CharField(max_length=100)
    parent = models.ForeignKey('self', on_delete=models.CASCADE, null=True, blank=True, related_name='children')

    def __str__(self):
        return self.name

# 3. Custom Managers for Optimization
class CourseManager(models.Manager):
    def for_listing(self):
        # Menggunakan select_related untuk ForeignKey dan prefetch_related untuk Reverse ForeignKey/M2M
        return self.select_related('instructor', 'category').prefetch_related('lessons')

class EnrollmentManager(models.Manager):
    def for_student_dashboard(self, student_user):
        return self.filter(student=student_user).select_related('course', 'course__instructor')

# 4. Course Model
class Course(models.Model):
    title = models.CharField(max_length=200)
    instructor = models.ForeignKey(User, on_delete=models.CASCADE, related_name='courses')
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True, related_name='courses')
    
    objects = CourseManager() # Activate custom manager

    def __str__(self):
        return self.title

# 5. Lesson Model (Ordering)
class Lesson(models.Model):
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='lessons')
    title = models.CharField(max_length=200)
    order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ['order']

    def __str__(self):
        return f"{self.course.title} - {self.title}"

# 6. Enrollment Model (Unique Constraint)
class Enrollment(models.Model):
    student = models.ForeignKey(User, on_delete=models.CASCADE, related_name='enrollments')
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='enrollments')
    enrolled_at = models.DateTimeField(auto_now_add=True)

    objects = EnrollmentManager()

    class Meta:
        unique_together = ('student', 'course')

# 7. Progress Model
class Progress(models.Model):
    student = models.ForeignKey(User, on_delete=models.CASCADE, related_name='progress')
    lesson = models.ForeignKey(Lesson, on_delete=models.CASCADE, related_name='progress')
    is_completed = models.BooleanField(default=False)

    class Meta:
        unique_together = ('student', 'lesson')