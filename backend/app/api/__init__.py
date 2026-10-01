# API package
from app.api import auth, students, subjects, attendance, dashboard, notifications, lecturers, assignments

notification = notifications

__all__ = [
    "auth",
    "students",
    "subjects",
    "attendance",
    "dashboard",
    "notifications",
    "notification",
    "lecturers",
    "assignments",
]


