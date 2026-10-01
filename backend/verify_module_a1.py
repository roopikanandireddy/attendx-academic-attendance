"""
ATTENDX MODULE A1 — VERIFICATION SUITE
Tests:
1. Backend Admin Authorization Dependency (app.core.security: get_current_admin)
2. Admin Token / Student Token / Lecturer Token / Invalid Token / Missing Token
3. Student Portal Regression (Login, Dashboard, Subjects, Enrollment, Attendance, History, Notifications, Profile)
4. Admin Endpoints Authentication Boundaries
"""
import sys
import os
import urllib.request
import urllib.error
import json

backend_dir = r"c:\Administrator\projects\attendx\backend"
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

from app.core.database import SessionLocal
from app.core.security import create_access_token, hash_password
from app.models.user import User

BASE_URL = "http://127.0.0.1:8000"

def post_json(path, data, token=None):
    url = f"{BASE_URL}{path}"
    headers = {"Content-Type": "application/json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    req = urllib.request.Request(url, data=json.dumps(data).encode("utf-8"), headers=headers)
    with urllib.request.urlopen(req) as resp:
        return resp.status, json.loads(resp.read().decode())

def get_json(path, token=None):
    url = f"{BASE_URL}{path}"
    headers = {}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    req = urllib.request.Request(url, headers=headers)
    with urllib.request.urlopen(req) as resp:
        return resp.status, json.loads(resp.read().decode())

def run_tests():
    print("=" * 60)
    print("ATTENDX MODULE A1 — VERIFICATION TESTS")
    print("=" * 60)

    # 1. Admin Login
    print("\n--- 1. Admin Authentication ---")
    status, data = post_json("/api/auth/login", {"email": "admin@attendx.com", "password": "AdminPassword123!"})
    assert status == 200, f"Expected 200, got {status}"
    admin_token = data["access_token"]
    admin_user = data["user"]
    assert admin_user["role"] == "admin", f"Expected admin role, got {admin_user['role']}"
    print(f"[PASS] Admin login succeeded: {admin_user['email']} (role: {admin_user['role']})")

    # 2. Student Login
    print("\n--- 2. Student Authentication ---")
    status, data = post_json("/api/auth/login", {"email": "john.doe@student.com", "password": "StudentPassword123!"})
    assert status == 200
    student_token = data["access_token"]
    student_user = data["user"]
    assert student_user["role"] == "student"
    print(f"[PASS] Student login succeeded: {student_user['email']} (role: {student_user['role']})")

    # 3. Backend Authorization on Admin-Only Endpoint
    print("\n--- 3. Backend Admin Authorization Boundaries ---")
    
    # 3A. Admin token -> Allowed (200)
    status, count_data = get_json("/api/students/count", token=admin_token)
    assert status == 200
    print(f"[PASS] Admin Token -> ALLOWED (HTTP {status}, count: {count_data['total']})")

    # 3B. Student token -> 403 Forbidden
    try:
        get_json("/api/students/count", token=student_token)
        assert False, "Student should have been rejected with 403"
    except urllib.error.HTTPError as e:
        assert e.code == 403, f"Expected 403, got {e.code}"
        print(f"[PASS] Student Token -> REJECTED (HTTP {e.code} Forbidden)")

    # 3C. Lecturer token -> 403 Forbidden
    db = SessionLocal()
    lecturer = db.query(User).filter(User.role == "lecturer").first()
    created_temp_lecturer = False
    if not lecturer:
        lecturer = User(
            email="temp.lecturer.test@attendx.com",
            full_name="Temporary Lecturer Test",
            password_hash=hash_password("Pass123!"),
            role="lecturer"
        )
        db.add(lecturer)
        db.commit()
        db.refresh(lecturer)
        created_temp_lecturer = True

    try:
        lecturer_token = create_access_token({"sub": lecturer.id, "role": "lecturer"})
        try:
            get_json("/api/students/count", token=lecturer_token)
            assert False, "Lecturer should have been rejected with 403"
        except urllib.error.HTTPError as e:
            assert e.code == 403, f"Expected 403, got {e.code}"
            print(f"[PASS] Lecturer Token -> REJECTED (HTTP {e.code} Forbidden)")
    finally:
        if created_temp_lecturer:
            db.delete(lecturer)
            db.commit()
            db.close()

    # 3D. Missing token -> 401 Unauthorized
    try:
        get_json("/api/students/count", token=None)
        assert False, "Missing token should have been rejected with 401"
    except urllib.error.HTTPError as e:
        assert e.code == 401, f"Expected 401, got {e.code}"
        print(f"[PASS] Missing Token -> REJECTED (HTTP {e.code} Unauthorized)")

    # 3E. Invalid token -> 401 Unauthorized
    try:
        get_json("/api/students/count", token="invalid.jwt.token.here")
        assert False, "Invalid token should have been rejected with 401"
    except urllib.error.HTTPError as e:
        assert e.code == 401, f"Expected 401, got {e.code}"
        print(f"[PASS] Invalid Token -> REJECTED (HTTP {e.code} Unauthorized)")

    # 4. Student Portal Full Regression Test
    print("\n--- 4. Student Portal Full Regression Test ---")
    
    # Dashboard
    status, dash = get_json("/api/dashboard/student", token=student_token)
    assert status == 200
    assert "overall_stats" in dash
    assert "subjects" in dash
    print(f"[PASS] Student Dashboard: HTTP {status} (Attendance: {dash['overall_stats']['percentage']}%, Subjects: {len(dash['subjects'])})")

    # Subject Catalog
    status, subjects = get_json("/api/subjects", token=student_token)
    assert status == 200
    assert len(subjects) > 0
    print(f"[PASS] Student Subjects Catalog: HTTP {status} (Total: {len(subjects)})")

    # Student Enrollments
    status, enrollments = get_json("/api/subjects/my-enrollments", token=student_token)
    assert status == 200
    print(f"[PASS] Student Enrolled Subjects: HTTP {status} (Enrolled: {len(enrollments)})")

    # Student Attendance Records
    status, attendance = get_json("/api/attendance", token=student_token)
    assert status == 200
    assert attendance["total"] > 0
    print(f"[PASS] Student Attendance History: HTTP {status} (Records: {attendance['total']})")

    # Student Notifications
    status, notifications = get_json("/api/notifications", token=student_token)
    assert status == 200
    print(f"[PASS] Student Notifications: HTTP {status} (Items: {len(notifications)})")

    # Student Unread Notification Count
    status, unread = get_json("/api/notifications/unread-count", token=student_token)
    assert status == 200
    print(f"[PASS] Student Unread Count: HTTP {status} (Unread: {unread['count']})")

    # Student Profile (/api/auth/me)
    status, me = get_json("/api/auth/me", token=student_token)
    assert status == 200
    assert me["role"] == "student"
    print(f"[PASS] Student Profile (/me): HTTP {status} ({me['full_name']}, {me['email']})")

    # Admin Profile (/api/auth/me)
    status, admin_me = get_json("/api/auth/me", token=admin_token)
    assert status == 200
    assert admin_me["role"] == "admin"
    print(f"[PASS] Admin Profile (/me): HTTP {status} ({admin_me['full_name']}, role: {admin_me['role']})")

    print("\n" + "=" * 60)
    print("ALL MODULE A1 VERIFICATION TESTS PASSED SUCCESSFULLY!")
    print("=" * 60)

if __name__ == "__main__":
    run_tests()
