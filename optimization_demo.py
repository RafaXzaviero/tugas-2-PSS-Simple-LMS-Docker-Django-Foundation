import os
import django
from django.db import connection

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from lms.models import Course

def demo_optimization():
    print("--- 1. N+1 Problem (Tanpa Optimasi) ---")
    connection.queries_log.clear()
    courses = Course.objects.all() # Query standar
    for course in courses:
        print(f"Course: {course.title}, Instructor: {course.instructor.username}")
    print(f"Jumlah Query: {len(connection.queries)}")

    print("\n--- 2. Optimized (Dengan select_related) ---")
    connection.queries_log.clear()
    # Menggunakan manager custom .for_listing() yang sudah kita buat
    courses_optimized = Course.objects.for_listing() 
    for course in courses_optimized:
        print(f"Course: {course.title}, Instructor: {course.instructor.username}")
    print(f"Jumlah Query: {len(connection.queries)}")

if __name__ == "__main__":
    demo_optimization()