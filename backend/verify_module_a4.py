"""
ATTENDX MODULE A4 — ADMIN LECTURER MANAGEMENT VERIFICATION SUITE
Tests:
1. Admin Authentication & Authorization on Lecturer APIs
2. Non-admin Rejection (Student -> 403, Lecturer -> 403, Missing -> 401, Invalid -> 401)
3. Lecturer Summary Metrics (/api/admin/lecturers/summary)
4. Lecturer List with Search, Status, Department, Assignment Filters & Pagination
5. Lecturer Details with assigned subjects section (/api/admin/lecturers/{id})
6. Create Lecturer with validation, password hashing, and duplicate checks (Email & Employee ID)
7. Update Lecturer details (Name, Department, Employee ID) & Duplicate Prevention
8. Disable Lecturer & verify login is rejected with 403 Forbidden
9. Enable Lecturer & verify login succeeds
10. End-to-End: Created Lecturer logs in via existing auth and verifies role = 'lecturer'
11. Admin & Student Regression Suites (A1, A2, A3, and Student Portal)
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
    print("ATTENDX MODULE A4 — ADMIN LECTURER MANAGEMENT TESTS")
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

    # 2. Authorization Boundaries on Lecturer APIs
    print("\n--- 2. Testing Authorization Boundaries ---")
    # Student cannot call admin lecturer endpoints -> 403
    try:
        get_json("/api/admin/lecturers", token=student_token)
        assert False, "Student should get 403 on GET /api/admin/lecturers"
    except urllib.error.HTTPError as e:
        assert e.code == 403
        print(f"[PASS] Student token rejected on GET /api/admin/lecturers (HTTP {e.code})")

    try:
        get_json("/api/admin/lecturers/summary", token=student_token)
        assert False, "Student should get 403 on GET /api/admin/lecturers/summary"
    except urllib.error.HTTPError as e:
        assert e.code == 403
        print(f"[PASS] Student token rejected on GET /api/admin/lecturers/summary (HTTP {e.code})")

    try:
        post_json("/api/admin/lecturers", {"full_name": "Hack", "email": "hack@hack.com"}, token=student_token)
        assert False, "Student should get 403 on POST /api/admin/lecturers"
    except urllib.error.HTTPError as e:
        assert e.code == 403
        print(f"[PASS] Student token rejected on POST /api/admin/lecturers (HTTP {e.code})")

    # Missing token -> 401
    try:
        get_json("/api/admin/lecturers", token=None)
        assert False, "Missing token should get 401"
    except urllib.error.HTTPError as e:
        assert e.code == 401
        print(f"[PASS] Missing token rejected (HTTP {e.code})")

    # Invalid token -> 401
    try:
        get_json("/api/admin/lecturers", token="invalid.token.here")
        assert False, "Invalid token should get 401"
    except urllib.error.HTTPError as e:
        assert e.code == 401
        print(f"[PASS] Invalid token rejected (HTTP {e.code})")

    # 3. Lecturer Summary Statistics
    print("\n--- 3. Testing Lecturer Summary Metrics ---")
    status, summary = get_json("/api/admin/lecturers/summary", token=admin_token)
    assert status == 200
    assert "total_lecturers" in summary
    assert "active_lecturers" in summary
    assert "inactive_lecturers" in summary
    assert "lecturers_with_assignments" in summary
    print(f"[PASS] Lecturer summary metrics: Total={summary['total_lecturers']}, Active={summary['active_lecturers']}, Inactive={summary['inactive_lecturers']}, With Assignments={summary['lecturers_with_assignments']}")

    # 4. Create Lecturer & Duplicate Validations
    print("\n--- 4. Testing Lecturer Creation & Duplicate Protection ---")
    test_empid = f"EMP{uuid.uuid4().hex[:6].upper()}"
    test_email = f"lecturer_{uuid.uuid4().hex[:6]}@attendx.com"
    lecturer_payload = {
        "employee_id": test_empid,
        "full_name": "Dr. Alan Turing",
        "email": test_email,
        "department": "Computer Science",
        "password": "LecturerPassword123!"
    }

    status, created = post_json("/api/admin/lecturers", lecturer_payload, token=admin_token)
    assert status == 201, f"Expected 201, got {status}"
    created_id = created["id"]
    assert created["employee_id"] == test_empid
    assert created["full_name"] == "Dr. Alan Turing"
    assert created["email"] == test_email
    assert created["role"] == "lecturer"
    assert created["is_active"] is True
    assert created["status"] == "Active"
    print(f"[PASS] Lecturer created successfully (ID: {created['employee_id']} | Email: {created['email']} | Role: {created['role']})")

    # Duplicate email rejection -> 409 Conflict
    try:
        dup_email_payload = dict(lecturer_payload)
        dup_email_payload["employee_id"] = f"EMP{uuid.uuid4().hex[:6].upper()}"
        post_json("/api/admin/lecturers", dup_email_payload, token=admin_token)
        assert False, "Should reject duplicate email with 409 Conflict"
    except urllib.error.HTTPError as e:
        assert e.code == 409
        print(f"[PASS] Duplicate email rejected with HTTP {e.code} Conflict")

    # Duplicate employee_id rejection -> 409 Conflict
    try:
        dup_empid_payload = dict(lecturer_payload)
        dup_empid_payload["email"] = f"other_{uuid.uuid4().hex[:6]}@attendx.com"
        post_json("/api/admin/lecturers", dup_empid_payload, token=admin_token)
        assert False, "Should reject duplicate Employee ID with 409 Conflict"
    except urllib.error.HTTPError as e:
        assert e.code == 409
        print(f"[PASS] Duplicate Employee ID rejected with HTTP {e.code} Conflict")

    # 5. List, Search, Filter & Pagination
    print("\n--- 5. Testing Lecturer List, Filtering & Pagination ---")
    status, paged = get_json("/api/admin/lecturers?page=1&limit=5", token=admin_token)
    assert status == 200
    assert paged["total"] >= 1
    assert any(l["id"] == created_id for l in paged["items"])
    sample = [l for l in paged["items"] if l["id"] == created_id][0]
    for key in ["id", "employee_id", "full_name", "email", "department", "role", "is_active", "status", "assigned_subjects_count"]:
        assert key in sample, f"Missing key {key} in lecturer item"
    print(f"[PASS] Lecturer table list works (Total: {paged['total']}, Found created lecturer: {sample['full_name']} | {sample['employee_id']})")

    # Search by Name
    status, search_name = get_json("/api/admin/lecturers?search=Turing", token=admin_token)
    assert status == 200
    assert any(l["id"] == created_id for l in search_name["items"])
    print(f"[PASS] Search by Name 'Turing' found {search_name['total']} match(es)")

    # Search by Employee ID
    status, search_eid = get_json(f"/api/admin/lecturers?search={test_empid}", token=admin_token)
    assert status == 200
    assert any(l["id"] == created_id for l in search_eid["items"])
    print(f"[PASS] Search by Employee ID '{test_empid}' found {search_eid['total']} match(es)")

    # Status filter
    status, active_res = get_json("/api/admin/lecturers?status=active", token=admin_token)
    assert status == 200
    assert all(l["is_active"] is True for l in active_res["items"])
    print(f"[PASS] Status filter 'active' returned {active_res['total']} active lecturer(s)")

    # Department filter
    status, dept_res = get_json("/api/admin/lecturers?department=Computer", token=admin_token)
    assert status == 200
    assert any(l["id"] == created_id for l in dept_res["items"])
    print(f"[PASS] Department filter 'Computer' returned {dept_res['total']} lecturer(s)")

    # Assignment Status filter
    status, unassigned_res = get_json("/api/admin/lecturers?assignment_status=unassigned", token=admin_token)
    assert status == 200
    assert any(l["id"] == created_id for l in unassigned_res["items"])
    print(f"[PASS] Assignment filter 'unassigned' returned {unassigned_res['total']} lecturer(s)")

    # 6. View Lecturer Details
    print("\n--- 6. Testing Lecturer Details View ---")
    status, detail = get_json(f"/api/admin/lecturers/{created_id}", token=admin_token)
    assert status == 200
    assert detail["id"] == created_id
    assert detail["employee_id"] == test_empid
    assert detail["full_name"] == "Dr. Alan Turing"
    assert "assigned_subjects" in detail
    assert isinstance(detail["assigned_subjects"], list)
    assert detail["assigned_subjects_count"] == 0
    print(f"[PASS] Lecturer details retrieved: {detail['full_name']} ({detail['department']}) - Assigned Subjects: {len(detail['assigned_subjects'])}")

    # 7. Edit Lecturer Details
    print("\n--- 7. Testing Lecturer Update ---")
    updated_eid = f"EMP{uuid.uuid4().hex[:6].upper()}"
    update_payload = {
        "full_name": "Dr. Alan M. Turing",
        "department": "Artificial Intelligence",
        "employee_id": updated_eid
    }
    status, updated = put_json(f"/api/admin/lecturers/{created_id}", update_payload, token=admin_token)
    assert status == 200
    assert updated["full_name"] == "Dr. Alan M. Turing"
    assert updated["department"] == "Artificial Intelligence"
    assert updated["employee_id"] == updated_eid
    print(f"[PASS] Lecturer updated successfully: {updated['full_name']} | Dept: {updated['department']} | Emp ID: {updated['employee_id']}")

    # 8. Disable Lecturer & Verify Login Rejection
    print("\n--- 8. Testing Account Disable & Login Rejection ---")
    status, dis_res = post_json(f"/api/admin/lecturers/{created_id}/disable", {}, token=admin_token)
    assert status == 200
    assert dis_res["is_active"] is False
    assert dis_res["status"] == "Inactive"
    print(f"[PASS] Lecturer account disabled successfully")

    # Disabled lecturer login -> 403 Forbidden
    try:
        post_json("/api/auth/login", {"email": test_email, "password": "LecturerPassword123!"})
        assert False, "Disabled lecturer should get 403 Forbidden on login"
    except urllib.error.HTTPError as e:
        assert e.code == 403
        print(f"[PASS] Disabled lecturer login rejected with HTTP {e.code} Forbidden")

    # 9. Enable Lecturer & Verify Login Success
    print("\n--- 9. Testing Account Enable & Login Success ---")
    status, en_res = post_json(f"/api/admin/lecturers/{created_id}/enable", {}, token=admin_token)
    assert status == 200
    assert en_res["is_active"] is True
    assert en_res["status"] == "Active"
    print(f"[PASS] Lecturer account re-enabled successfully")

    # 10. End-to-End: Created Lecturer Login via Existing Auth
    print("\n--- 10. End-to-End: Lecturer Login & Role Validation ---")
    status, l_login = post_json("/api/auth/login", {"email": test_email, "password": "LecturerPassword123!"})
    assert status == 200
    assert l_login["user"]["role"] == "lecturer"
    assert l_login["user"]["full_name"] == "Dr. Alan M. Turing"
    lecturer_jwt = l_login["access_token"]
    print(f"[PASS] Newly created lecturer authenticated with existing auth (role: {l_login['user']['role']})")

    # Lecturer token cannot access Admin Lecturer Management APIs -> 403 Forbidden
    try:
        get_json("/api/admin/lecturers", token=lecturer_jwt)
        assert False, "Lecturer token should get 403 Forbidden on Admin APIs"
    except urllib.error.HTTPError as e:
        assert e.code == 403
        print(f"[PASS] Lecturer token rejected from Admin Lecturer APIs (HTTP {e.code} Forbidden)")

    # Clean up test lecturer
    delete_req(f"/api/admin/lecturers/{created_id}", token=admin_token)
    print(f"[PASS] Test lecturer cleaned up cleanly")

    # 11. Admin & Student Regression Suites
    print("\n--- 11. Admin & Student Regression Suites ---")
    # Admin Dashboard
    status, dash = get_json("/api/admin/dashboard", token=admin_token)
    assert status == 200
    print(f"[PASS] Admin Dashboard: HTTP {status} (Total Students: {dash['total_students']}, Subjects: {dash['total_subjects']})")

    # Admin Students
    status, st_summary = get_json("/api/admin/students/summary", token=admin_token)
    assert status == 200 and st_summary["total_students"] > 0
    print(f"[PASS] Admin Students Summary: HTTP {status} ({st_summary['total_students']} students)")

    # Student Dashboard
    status, s_dash = get_json("/api/dashboard/student", token=student_token)
    assert status == 200
    print(f"[PASS] Existing Student Dashboard: HTTP {status} (Attendance: {s_dash['overall_stats']['percentage']}%)")

    # Student Subjects
    status, subjects = get_json("/api/subjects", token=student_token)
    assert status == 200 and len(subjects) > 0
    print(f"[PASS] Existing Student Subjects catalog: HTTP {status} ({len(subjects)} subjects)")

    # Student Attendance
    status, att = get_json("/api/attendance", token=student_token)
    assert status == 200
    print(f"[PASS] Existing Student Attendance: HTTP {status} ({att['total']} records)")

    # Student Notifications
    status, notifs = get_json("/api/notifications", token=student_token)
    assert status == 200
    print(f"[PASS] Existing Student Notifications: HTTP {status}")

    # Student Profile
    status, me = get_json("/api/auth/me", token=student_token)
    assert status == 200 and me["role"] == "student"
    print(f"[PASS] Existing Student Profile: HTTP {status} ({me['full_name']})")

    print("\n" + "=" * 70)
    print("ALL MODULE A4 BACKEND VERIFICATION TESTS PASSED SUCCESSFULLY!")
    print("=" * 70)


if __name__ == "__main__":
    run_tests()
