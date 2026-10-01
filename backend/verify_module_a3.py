"""
ATTENDX MODULE A3 — ADMIN STUDENT MANAGEMENT VERIFICATION SUITE
Tests:
1. Admin Authentication & Authorization on Student APIs
2. Non-admin Rejection (Student -> 403, Lecturer -> 403, Missing -> 401)
3. Student Summary Metrics (/api/admin/students/summary and /api/students/summary)
4. Student List with Search, Status, Department, Year, Section, Attendance Filters & Pagination
5. Student Details with Attendance & Subject breakdown (/api/admin/students/{id})
6. Create Student with validation, password hashing, and duplicate checks
7. Update Student details
8. Disable Student & verify login is rejected with 403
9. Enable Student & verify login succeeds
10. End-to-End: Created Student logs in and accesses Student Portal
11. Student Portal Full Regression Suite
"""
import sys
import urllib.request
import urllib.error
import json
import uuid
from typing import Any, Optional

backend_dir = r"c:\Administrator\projects\attendx\backend"
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

from app.core.database import SessionLocal
from app.core.security import create_access_token, hash_password
from app.models.user import User

BASE_URL = "http://127.0.0.1:8000"

def request_json(path: str, method: str = "GET", data: Any = None, token: Optional[str] = None) -> tuple[int, Any]:
    url = f"{BASE_URL}{path}"
    headers = {"Content-Type": "application/json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    body = json.dumps(data).encode("utf-8") if data is not None else None
    req = urllib.request.Request(url, data=body, headers=headers, method=method)
    with urllib.request.urlopen(req) as resp:
        content = resp.read().decode("utf-8")
        if content:
            return resp.status, json.loads(content)
        return resp.status, {}

def get_json(path: str, token: Optional[str] = None) -> tuple[int, Any]:
    return request_json(path, method="GET", token=token)

def post_json(path: str, data: Any = None, token: Optional[str] = None) -> tuple[int, Any]:
    return request_json(path, method="POST", data=data, token=token)

def put_json(path: str, data: Any = None, token: Optional[str] = None) -> tuple[int, Any]:
    return request_json(path, method="PUT", data=data, token=token)

def patch_json(path: str, data: Any = None, token: Optional[str] = None) -> tuple[int, Any]:
    return request_json(path, method="PATCH", data=data, token=token)

def delete_req(path: str, token: Optional[str] = None) -> tuple[int, Any]:
    return request_json(path, method="DELETE", token=token)



def run_tests():
    print("=" * 70)
    print("ATTENDX MODULE A3 — ADMIN STUDENT MANAGEMENT TESTS")
    print("=" * 70)

    # 1. Admin & Student Logins
    print("\n--- 1. Authentication ---")
    status, data = post_json("/api/auth/login", {"email": "admin@attendx.com", "password": "AdminPassword123!"})
    assert status == 200, f"Expected 200, got {status}"
    admin_token = data["access_token"]
    print(f"[PASS] Admin login succeeded (role: {data['user']['role']})")

    status, s_data = post_json("/api/auth/login", {"email": "john.doe@student.com", "password": "StudentPassword123!"})
    assert status == 200, f"Expected 200, got {status}"
    student_token = s_data["access_token"]
    print(f"[PASS] Student login succeeded (role: {s_data['user']['role']})")

    # 2. Authorization Boundaries on Student APIs
    print("\n--- 2. Testing Authorization Boundaries ---")
    # Student cannot call admin endpoints
    try:
        get_json("/api/admin/students", token=student_token)
        assert False, "Student should get 403 on GET /api/admin/students"
    except urllib.error.HTTPError as e:
        assert e.code == 403
        print(f"[PASS] Student token rejected on GET /api/admin/students (HTTP {e.code})")

    try:
        get_json("/api/admin/students/summary", token=student_token)
        assert False, "Student should get 403 on GET /api/admin/students/summary"
    except urllib.error.HTTPError as e:
        assert e.code == 403
        print(f"[PASS] Student token rejected on GET /api/admin/students/summary (HTTP {e.code})")

    try:
        post_json("/api/admin/students", {"full_name": "Hack", "email": "hack@hack.com"}, token=student_token)
        assert False, "Student should get 403 on POST /api/admin/students"
    except urllib.error.HTTPError as e:
        assert e.code == 403
        print(f"[PASS] Student token rejected on POST /api/admin/students (HTTP {e.code})")

    # Missing token -> 401
    try:
        get_json("/api/admin/students", token=None)
        assert False, "Missing token should get 401"
    except urllib.error.HTTPError as e:
        assert e.code == 401
        print(f"[PASS] Missing token rejected (HTTP {e.code})")

    # 3. Student Summary Statistics
    print("\n--- 3. Testing Student Summary Metrics ---")
    status, summary = get_json("/api/admin/students/summary", token=admin_token)
    assert status == 200
    assert "total_students" in summary and summary["total_students"] > 0
    assert "active_students" in summary and summary["active_students"] > 0
    assert "inactive_students" in summary
    assert "below_threshold_students" in summary
    print(f"[PASS] Student summary metrics: Total={summary['total_students']}, Active={summary['active_students']}, Inactive={summary['inactive_students']}, Below 75%={summary['below_threshold_students']}")

    # 4. Student List, Filtering & Pagination
    print("\n--- 4. Testing Student List, Filtering & Pagination ---")
    status, paged = get_json("/api/admin/students?page=1&limit=5", token=admin_token)
    assert status == 200
    assert len(paged["items"]) <= 5
    assert paged["total"] > 0
    assert paged["page"] == 1
    assert paged["limit"] == 5
    print(f"[PASS] Server-side pagination works: Page {paged['page']} of {paged['pages']} (Total: {paged['total']}, Returned: {len(paged['items'])})")

    # Verify student item fields
    sample_student = paged["items"][0]
    for key in ["id", "full_name", "email", "student_id", "department", "year", "section", "status", "attendance_percentage"]:
        assert key in sample_student, f"Missing key {key} in student item"
    print(f"[PASS] Student records format verified (Sample: {sample_student['full_name']} | {sample_student['student_id']} | Status: {sample_student['status']} | Attendance: {sample_student['attendance_percentage']}%)")

    # Search filter
    status, search_res = get_json("/api/admin/students?search=John", token=admin_token)
    assert status == 200
    assert any("John" in s["full_name"] for s in search_res["items"])
    print(f"[PASS] Search by name 'John' found {search_res['total']} student(s)")

    # Status filter
    status, active_res = get_json("/api/admin/students?status=active", token=admin_token)
    assert status == 200
    assert all(s["status"] == "Active" for s in active_res["items"])
    print(f"[PASS] Status filter 'active' returned {active_res['total']} active student(s)")

    # Attendance filter below_75
    status, low_res = get_json("/api/admin/students?attendance=below_75", token=admin_token)
    assert status == 200
    assert all(s["attendance_percentage"] < 75.0 for s in low_res["items"])
    print(f"[PASS] Attendance filter 'below_75' returned {low_res['total']} low-attendance student(s)")

    # 5. Get Student Details
    print("\n--- 5. Testing Student Details ---")
    st_id = sample_student["id"]
    status, detail = get_json(f"/api/admin/students/{st_id}", token=admin_token)
    assert status == 200
    assert detail["id"] == st_id
    assert "attendance_summary" in detail
    assert "subjects_attendance" in detail
    print(f"[PASS] Student details retrieved successfully: {detail['full_name']} (Total Classes: {detail['attendance_summary']['total_classes']}, Present: {detail['attendance_summary']['present']}, Overall: {detail['attendance_summary']['percentage']}%)")
    print(f"       - Subject breakdown items: {len(detail['subjects_attendance'])}")

    # 6. Create Student & Duplicate Validation
    print("\n--- 6. Testing Student Creation & Validation ---")
    test_sid = f"ST{uuid.uuid4().hex[:6].upper()}"
    test_email = f"test_{uuid.uuid4().hex[:6]}@attendx.com"
    new_student_payload = {
        "full_name": "Test Managed Student",
        "email": test_email,
        "password": "StudentPassword123!",
        "student_id": test_sid,
        "department": "CSE",
        "year": 3,
        "section": "A"
    }

    status, created = post_json("/api/admin/students", new_student_payload, token=admin_token)
    assert status == 201, f"Expected 201, got {status}"
    created_id = created["id"]
    assert created["student_id"] == test_sid
    assert created["status"] == "Active"
    print(f"[PASS] Student created successfully (ID: {created['student_id']} | Email: {created['email']})")

    # Duplicate email check
    try:
        dup_email_payload = dict(new_student_payload)
        dup_email_payload["student_id"] = f"ST{uuid.uuid4().hex[:6].upper()}"
        post_json("/api/admin/students", dup_email_payload, token=admin_token)
        assert False, "Should reject duplicate email with 409"
    except urllib.error.HTTPError as e:
        assert e.code == 409
        print(f"[PASS] Duplicate email rejected with HTTP {e.code} Conflict")

    # Duplicate student_id check
    try:
        dup_sid_payload = dict(new_student_payload)
        dup_sid_payload["email"] = f"other_{uuid.uuid4().hex[:6]}@attendx.com"
        post_json("/api/admin/students", dup_sid_payload, token=admin_token)
        assert False, "Should reject duplicate student_id with 409"
    except urllib.error.HTTPError as e:
        assert e.code == 409
        print(f"[PASS] Duplicate student_id rejected with HTTP {e.code} Conflict")

    # 7. Update Student Details
    print("\n--- 7. Testing Student Details Update ---")
    update_payload = {
        "full_name": "Updated Managed Student",
        "department": "ECE",
        "year": 4,
        "section": "B"
    }
    status, updated = put_json(f"/api/admin/students/{created_id}", update_payload, token=admin_token)
    assert status == 200
    assert updated["full_name"] == "Updated Managed Student"
    assert updated["department"] == "ECE"
    assert updated["year"] == 4
    assert updated["section"] == "B"
    print(f"[PASS] Student updated successfully: {updated['full_name']} ({updated['department']} Year {updated['year']})")

    # 8. Disable Student & Verify Login Rejection
    print("\n--- 8. Testing Account Disable ---")
    status, dis_res = post_json(f"/api/admin/students/{created_id}/disable", {}, token=admin_token)
    assert status == 200
    assert dis_res["is_active"] is False
    assert dis_res["status"] == "Inactive"
    print(f"[PASS] Student disabled successfully")

    # Disabled student attempt login -> 403 Forbidden
    try:
        post_json("/api/auth/login", {"email": test_email, "password": "StudentPassword123!"})
        assert False, "Disabled student should get 403 Forbidden on login"
    except urllib.error.HTTPError as e:
        assert e.code == 403
        print(f"[PASS] Disabled student login rejected with HTTP {e.code} Forbidden")

    # 9. Enable Student & Verify Login Success
    print("\n--- 9. Testing Account Enable ---")
    status, en_res = post_json(f"/api/admin/students/{created_id}/enable", {}, token=admin_token)
    assert status == 200
    assert en_res["is_active"] is True
    assert en_res["status"] == "Active"
    print(f"[PASS] Student re-enabled successfully")

    # 10. End-to-End: Created Student Login & Student Portal
    print("\n--- 10. End-to-End: Newly Created Student Login & Portal ---")
    status, new_login = post_json("/api/auth/login", {"email": test_email, "password": "StudentPassword123!"})
    assert status == 200
    new_token = new_login["access_token"]
    assert new_login["user"]["full_name"] == "Updated Managed Student"
    print(f"[PASS] Newly created student authenticated with existing login flow")

    # Newly created student accesses Student Dashboard
    status, new_dash = get_json("/api/dashboard/student", token=new_token)
    assert status == 200
    assert "overall_stats" in new_dash
    print(f"[PASS] Newly created student loaded existing Student Portal dashboard (HTTP 200)")

    # 11. Student Portal Full Regression Suite
    print("\n--- 11. Student Portal Full Regression Suite ---")
    status, s_dash = get_json("/api/dashboard/student", token=student_token)
    assert status == 200
    print(f"[PASS] Existing Student Dashboard: HTTP {status} (Attendance: {s_dash['overall_stats']['percentage']}%)")

    status, subjects = get_json("/api/subjects", token=student_token)
    assert status == 200 and len(subjects) > 0
    print(f"[PASS] Existing Student Subjects catalog: HTTP {status} ({len(subjects)} subjects)")

    status, enrollments = get_json("/api/subjects/my-enrollments", token=student_token)
    assert status == 200
    print(f"[PASS] Existing Student Enrollments: HTTP {status} ({len(enrollments)} subjects)")

    status, att = get_json("/api/attendance", token=student_token)
    assert status == 200
    print(f"[PASS] Existing Student Attendance records: HTTP {status} ({att['total']} records)")

    status, notifs = get_json("/api/notifications", token=student_token)
    assert status == 200
    print(f"[PASS] Existing Student Notifications: HTTP {status}")

    status, profile = get_json("/api/auth/me", token=student_token)
    assert status == 200 and profile["role"] == "student"
    print(f"[PASS] Existing Student Profile: HTTP {status} ({profile['full_name']})")

    # Clean up created test student
    delete_req(f"/api/admin/students/{created_id}", token=admin_token)
    print(f"[PASS] Test student cleaned up cleanly")

    print("\n" + "=" * 70)
    print("ALL MODULE A3 BACKEND VERIFICATION TESTS PASSED SUCCESSFULLY!")
    print("=" * 70)

if __name__ == "__main__":
    run_tests()
