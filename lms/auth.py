import jwt
from datetime import datetime, timedelta
from django.conf import settings
from ninja.security import HttpBearer
from django.shortcuts import get_object_or_404
from .models import User

SECRET_KEY = settings.SECRET_KEY

# Fungsi untuk membuat JWT Token
def create_token(user_id, token_type="access"):
    # Access token mati dalam 60 menit, refresh token mati dalam 1 hari
    exp = datetime.utcnow() + timedelta(minutes=60 if token_type == "access" else 1440)
    payload = {"user_id": user_id, "type": token_type, "exp": exp}
    return jwt.encode(payload, SECRET_KEY, algorithm="HS256")

# Middleware untuk mengecek Header Authorization: Bearer <token>
class JWTAuth(HttpBearer):
    def authenticate(self, request, token):
        try:
            payload = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
            if payload["type"] != "access":
                return None
            user = get_object_or_404(User, id=payload["user_id"])
            request.user = user
            return user
        except (jwt.ExpiredSignatureError, jwt.InvalidTokenError):
            return None

# RBAC (Role-Based Access Control) Checkers
def is_admin(request):
    return request.user.role == 'admin'

def is_instructor(request):
    return request.user.role in ['instructor', 'admin']

def is_student(request):
    return request.user.role == 'student'