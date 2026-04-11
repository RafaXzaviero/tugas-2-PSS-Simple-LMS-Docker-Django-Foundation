from ninja import NinjaAPI, Router
from django.contrib.auth.hashers import make_password, check_password
from django.shortcuts import get_object_or_404
from django.core.paginator import Paginator
from typing import List, Optional
import jwt
from django.conf import settings

from .models import User, Course, Enrollment, Lesson, Progress
from .schemas import (
    RegisterSchema,
    LoginSchema,
    RefreshSchema,
    UpdateProfileSchema,
    TokenSchema,
    UserSchema,
    CourseSchema,
    CourseDetailSchema,
    CourseCreateSchema,
    CourseUpdateSchema,
    EnrollmentSchema,
    MessageSchema,
    CourseListSchema,
)
from .auth import JWTAuth, create_token, is_admin, is_instructor, is_student

# Inisialisasi API & Swagger Docs
api = NinjaAPI(title="Simple LMS API", description="API Documentation for Simple LMS with JWT & RBAC")

# --- ROUTERS ---
auth_router = Router(tags=["Authentication"])
courses_router = Router(tags=["Courses"])
enrollments_router = Router(tags=["Enrollments"])

# ==========================================
# Helpers
# ==========================================

def serialize_course(course: Course):
    return {
        "id": course.id,
        "title": course.title,
        "instructor_id": course.instructor_id,
        "category_id": course.category_id,
    }


def serialize_course_detail(course: Course):
    return {
        "id": course.id,
        "title": course.title,
        "instructor_id": course.instructor_id,
        "category_id": course.category_id,
        "lessons": [
            {"id": lesson.id, "title": lesson.title, "order": lesson.order}
            for lesson in course.lessons.all()
        ],
    }

# ==========================================
# 1. AUTHENTICATION ENDPOINTS
# ==========================================
@auth_router.post("/register", response={201: UserSchema, 400: MessageSchema})
def register(request, payload: RegisterSchema):
    if User.objects.filter(username=payload.username).exists():
        return 400, {"message": "Username already exists"}

    user = User.objects.create(
        username=payload.username,
        email=payload.email,
        password=make_password(payload.password),
        role=payload.role,
    )
    return 201, user


@auth_router.post("/login", response={200: TokenSchema, 401: MessageSchema})
def login(request, payload: LoginSchema):
    user = User.objects.filter(username=payload.username).first()
    if not user or not check_password(payload.password, user.password):
        return 401, {"message": "Invalid credentials"}

    return 200, {
        "access_token": create_token(user.id, "access"),
        "refresh_token": create_token(user.id, "refresh"),
    }


@auth_router.post("/refresh", response={200: TokenSchema, 401: MessageSchema})
def refresh_token(request, payload: RefreshSchema):
    try:
        token_data = jwt.decode(payload.refresh_token, settings.SECRET_KEY, algorithms=["HS256"])
        if token_data.get("type") != "refresh":
            return 401, {"message": "Invalid token type"}

        return 200, {
            "access_token": create_token(token_data["user_id"], "access"),
            "refresh_token": create_token(token_data["user_id"], "refresh"),
        }
    except jwt.ExpiredSignatureError:
        return 401, {"message": "Refresh token expired"}
    except jwt.InvalidTokenError:
        return 401, {"message": "Invalid refresh token"}


@auth_router.get("/me", response=UserSchema, auth=JWTAuth())
def get_me(request):
    return request.user


@auth_router.put("/me", response=UserSchema, auth=JWTAuth())
def update_me(request, payload: UpdateProfileSchema):
    user = request.user
    if payload.email:
        user.email = payload.email
    if payload.username:
        if User.objects.filter(username=payload.username).exclude(id=user.id).exists():
            return 400, {"message": "Username already taken"}
        user.username = payload.username
    user.save()
    return user


# ==========================================
# 2. COURSES ENDPOINTS
# ==========================================
@courses_router.get("", response=CourseListSchema)
def list_courses(
    request,
    page: int = 1,
    page_size: int = 10,
    category_id: Optional[int] = None,
    instructor_id: Optional[int] = None,
):
    qs = Course.objects.for_listing().all()
    if category_id:
        qs = qs.filter(category_id=category_id)
    if instructor_id:
        qs = qs.filter(instructor_id=instructor_id)

    paginator = Paginator(qs, page_size)
    page_obj = paginator.get_page(page)
    return {
        "items": [serialize_course(course) for course in page_obj.object_list],
        "meta": {
            "total": paginator.count,
            "page": page_obj.number,
            "page_size": page_obj.paginator.per_page,
        },
    }


@courses_router.get("/{course_id}", response=CourseDetailSchema)
def course_detail(request, course_id: int):
    course = get_object_or_404(Course.objects.prefetch_related("lessons"), id=course_id)
    return serialize_course_detail(course)


@courses_router.post("", response={201: CourseSchema, 403: MessageSchema}, auth=JWTAuth())
def create_course(request, payload: CourseCreateSchema):
    if not is_instructor(request):
        return 403, {"message": "Only instructors can create courses"}

    course = Course.objects.create(
        title=payload.title,
        category_id=payload.category_id,
        instructor=request.user,
    )
    return 201, serialize_course(course)


@courses_router.patch("/{course_id}", response={200: CourseSchema, 403: MessageSchema}, auth=JWTAuth())
def update_course(request, course_id: int, payload: CourseUpdateSchema):
    course = get_object_or_404(Course, id=course_id)
    if course.instructor != request.user and not is_admin(request):
        return 403, {"message": "You do not have permission to edit this course"}

    if payload.title is not None:
        course.title = payload.title
    if payload.category_id is not None:
        course.category_id = payload.category_id
    course.save()
    return 200, serialize_course(course)


@courses_router.delete("/{course_id}", response={204: None, 403: MessageSchema}, auth=JWTAuth())
def delete_course(request, course_id: int):
    if not is_admin(request):
        return 403, {"message": "Only admins can delete courses"}

    course = get_object_or_404(Course, id=course_id)
    course.delete()
    return 204, None


# ==========================================
# 3. ENROLLMENTS ENDPOINTS
# ==========================================
@enrollments_router.post("", response={201: MessageSchema, 400: MessageSchema, 403: MessageSchema}, auth=JWTAuth())
def enroll_course(request, payload: EnrollmentSchema):
    if not is_student(request):
        return 403, {"message": "Only students can enroll"}

    course = get_object_or_404(Course, id=payload.course_id)
    enrollment, created = Enrollment.objects.get_or_create(student=request.user, course=course)
    if not created:
        return 400, {"message": "Already enrolled"}
    return 201, {"message": "Enrolled successfully"}


@enrollments_router.get("/my-courses", response=List[CourseSchema], auth=JWTAuth())
def my_courses(request):
    if not is_student(request):
        return []

    enrollments = Enrollment.objects.filter(student=request.user).select_related("course")
    return [serialize_course(enrollment.course) for enrollment in enrollments]


@enrollments_router.post("/{lesson_id}/progress", response={200: MessageSchema, 403: MessageSchema}, auth=JWTAuth())
def mark_lesson_complete(request, lesson_id: int):
    if not is_student(request):
        return 403, {"message": "Only students can track progress"}

    lesson = get_object_or_404(Lesson, id=lesson_id)
    progress, _ = Progress.objects.get_or_create(student=request.user, lesson=lesson)
    progress.is_completed = True
    progress.save()
    return 200, {"message": "Lesson marked as complete"}


# Mendaftarkan router ke API utama
api.add_router("/auth", auth_router)
api.add_router("/courses", courses_router)
api.add_router("/enrollments", enrollments_router)
