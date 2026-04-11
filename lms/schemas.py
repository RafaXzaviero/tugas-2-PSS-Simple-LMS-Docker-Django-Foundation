from ninja import Schema
from typing import List, Optional
from .models import User, Course, Lesson

# --- AUTH SCHEMAS ---
class RegisterSchema(Schema):
    username: str
    email: str
    password: str
    role: str = 'student'

class LoginSchema(Schema):
    username: str
    password: str

class RefreshSchema(Schema):
    refresh_token: str

class UpdateProfileSchema(Schema):
    email: Optional[str] = None
    username: Optional[str] = None

class TokenSchema(Schema):
    access_token: str
    refresh_token: str

class UserSchema(Schema):
    id: int
    username: str
    email: str
    role: str

# --- COURSE SCHEMAS ---
class LessonSchema(Schema):
    id: int
    title: str
    order: int

class CourseSchema(Schema):
    id: int
    title: str
    instructor_id: int
    category_id: Optional[int] = None

class CourseDetailSchema(CourseSchema):
    lessons: List[LessonSchema] = []

class CourseCreateSchema(Schema):
    title: str
    category_id: Optional[int] = None

class CourseUpdateSchema(Schema):
    title: Optional[str] = None
    category_id: Optional[int] = None

class EnrollmentSchema(Schema):
    course_id: int

class MessageSchema(Schema):
    message: str

class PageMetaSchema(Schema):
    total: int
    page: int
    page_size: int

class CourseListSchema(Schema):
    items: List[CourseSchema]
    meta: PageMetaSchema
