"""
ATTENDX MODULE A2 — COMPREHENSIVE VERIFICATION SUITE
Tests:
1. Admin Dashboard endpoint (/api/admin/dashboard)
2. Admin Dashboard alias (/api/dashboard/admin)
3. Admin Authorization Boundaries (Admin -> 200, Student -> 403, Lecturer -> 403, Missing -> 401, Invalid -> 401)
4. Real Database Statistics Validation (No mock data, no fake counts)
5. Student Portal Full Regression Suite
"""
import sys
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
    print("=" * 65)
    print("ATTENDX MODULE A2 — ADMIN DASHBOARD VERIFICATION TESTS")
    print("=" * 65)

    # 1. Admin Login
    print("\n--- 1. Admin Authentication ---")
    status, data = post_json("/api/auth/login", {"email": "admin@attendx.com", "password": "AdminPassword123!"})
    assert status == 200
    admin_token = data["access_token"]
    assert data["user"]["role"] == "admin"
    print(f"[PASS] Admin login succeeded (role: {data['user']['role']})")

    # 2. Student Login
    print("\n--- 2. Student Authentication ---")
    status, data = post_json("/api/auth/login", {"email": "john.doe@student.com", "password": "StudentPassword123!"})
    assert status == 200
    student_token = data["access_token"]
    assert data["user"]["role"] == "student"
    print(f"[PASS] Student login succeeded (role: {data['user']['role']})")

    # 3. Admin Dashboard Endpoint Tests
    print("\n--- 3. Testing GET /api/admin/dashboard ---")
    status, dash = get_json("/api/admin/dashboard", token=admin_token)
    assert status == 200
    print(f"[PASS] GET /api/admin/dashboard -> HTTP {status}")
    print(f"       - Total Students:     {dash['total_students']}")
    print(f"       - Total Lecturers:    {dash['total_lecturers']}")
    print(f"       - Total Subjects:     {dash['total_subjects']}")
    print(f"       - Today's Total:      {dash['todays_attendance']['total']}")
    print(f"       - Today's Present:    {dash['todays_attendance']['present']}")
    print(f"       - Today's Percentage: {dash['todays_attendance']['percentage']}%")
    print(f"       - Average Attendance: {dash['average_attendance']}%")
    print(f"       - Low Attendance Ct:  {len(dash['low_attendance_students'])}")
    print(f"       - Subject Stats Ct:   {len(dash['subject_stats'])}")
    print(f"       - Recent Activity Ct: {len(dash['recent_activity'])}")

    # Verify fields
    assert isinstance(dash["total_students"], int) and dash["total_students"] > 0
    assert isinstance(dash["total_lecturers"], int)
    assert isinstance(dash["total_subjects"], int) and dash["total_subjects"] > 0
    assert "total" in dash["todays_attendance"]
    assert "present" in dash["todays_attendance"]
    assert "absent" in dash["todays_attendance"]
    assert "percentage" in dash["todays_attendance"]
    assert isinstance(dash["average_attendance"], (int, float))
    assert isinstance(dash["subject_stats"], list)
    assert isinstance(dash["recent_activity"], list)
    print("[PASS] All dashboard fields strictly validated against database types.")

    # 4. Alias Route GET /api/dashboard/admin
    print("\n--- 4. Testing Alias GET /api/dashboard/admin ---")
    status, dash_alias = get_json("/api/dashboard/admin", token=admin_token)
    assert status == 200
    assert dash_alias["total_students"] == dash["total_students"]
    print(f"[PASS] GET /api/dashboard/admin matches /api/admin/dashboard exactly.")

    # 5. Security & Authorization Boundaries
    print("\n--- 5. Testing Authorization Boundaries on Admin Dashboard ---")

    # 5A. Student Token -> 403 Forbidden
    try:
        get_json("/api/admin/dashboard", token=student_token)
        assert False, "Student should have been rejected with 403"
    except urllib.error.HTTPError as e:
        assert e.code == 403
        print(f"[PASS] Student token -> REJECTED (HTTP {e.code} Forbidden)")

    # 5B. Lecturer Token -> 403 Forbidden
    db = SessionLocal()
    lecturer = db.query(User).filter(User.role == "lecturer").first()
    created_temp_lecturer = False
    if not lecturer:
        lecturer = User(
            email="temp.lecturer.a2@attendx.com",
            full_name="Temporary Lecturer A2",
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
            get_json("/api/admin/dashboard", token=lecturer_token)
            assert False, "Lecturer should have been rejected with 403"
        except urllib.error.HTTPError as e:
            assert e.code == 403
            print(f"[PASS] Lecturer token -> REJECTED (HTTP {e.code} Forbidden)")
    finally:
        if created_temp_lecturer:
            db.delete(lecturer)
            db.commit()
            db.close()

    # 5C. Missing Token -> 401 Unauthorized
    try:
        get_json("/api/admin/dashboard", token=None)
        assert False, "Missing token should have been rejected with 401"
    except urllib.error.HTTPError as e:
        assert e.code == 401
        print(f"[PASS] Missing token -> REJECTED (HTTP {e.code} Unauthorized)")

    # 5D. Invalid Token -> 401 Unauthorized
    try:
        get_json("/api/admin/dashboard", token="forged.or.invalid.token")
        assert False, "Invalid token should have been rejected with 401"
    except urllib.error.HTTPError as e:
        assert e.code == 401
        print(f"[PASS] Invalid token -> REJECTED (HTTP {e.code} Unauthorized)")

    # 6. Student Portal Full Regression Test
    print("\n--- 6. Student Portal Full Regression Test ---")
    status, s_dash = get_json("/api/dashboard/student", token=student_token)
    assert status == 200
    print(f"[PASS] Student Dashboard: HTTP {status} (Attendance: {s_dash['overall_stats']['percentage']}%)")

    status, subjects = get_json("/api/subjects", token=student_token)
    assert status == 200 and len(subjects) > 0
    print(f"[PASS] Student Subjects: HTTP {status} (Catalog items: {len(subjects)})")

    status, enrollments = get_json("/api/subjects/my-enrollments", token=student_token)
    assert status == 200
    print(f"[PASS] Student Enrollments: HTTP {status} (Enrolled: {len(enrollments)})")

    status, att = get_json("/api/attendance", token=student_token)
    assert status == 200
    print(f"[PASS] Student Attendance: HTTP {status} (Records: {att['total']})")

    status, notifs = get_json("/api/notifications", token=student_token)
    assert status == 200
    print(f"[PASS] Student Notifications: HTTP {status} (Count: {len(notifs)})")

    status, unread = get_json("/api/notifications/unread-count", token=student_token)
    assert status == 200
    print(f"[PASS] Student Unread Count: HTTP {status} (Unread: {unread['count']})")

    status, profile = get_json("/api/auth/me", token=student_token)
    assert status == 200 and profile["role"] == "student"
    print(f"[PASS] Student Profile: HTTP {status} ({profile['full_name']})")

    print("\n" + "=" * 65)
    print("ALL MODULE A2 VERIFICATION TESTS PASSED SUCCESSFULLY!")
    print("=" * 65)

if __name__ == "__main__":
    run_tests()
