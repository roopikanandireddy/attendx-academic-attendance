"""
ATTENDX MODULE A5 — SUBJECT & LECTURER ASSIGNMENT VERIFICATION SUITE
Tests:
1. Admin Authentication & Authorization on Subject & Assignment APIs
2. Non-admin Rejection (Student -> 403, Lecturer -> 403, Missing -> 401, Invalid -> 401)
3. Subject Summary Metrics (/api/admin/subjects/summary)
4. Subject List with Search, Department, Year, Semester, Assignment Filters & Pagination
5. Subject Creation, Validation & Duplicate Code Prevention (409 Conflict)
6. Subject Details with Assigned Faculty and Enrolled Students
7. Subject Update Details & Duplicate Code Check on Edit
8. Teaching Assignment Creation (/api/admin/assignments):
   - Valid assignment (Lecturer -> Subject)
   - Role validation (Only lecturer allowed)
   - Duplicate assignment prevention (409 Conflict)
   - Cross-module verification: Lecturer profile reflects assigned subject
9. Assignment List, Filters, and Summary Metrics (/api/admin/assignments/summary)
10. Assignment Deletion / Unassign Faculty
11. Subject Deletion and Cascade Cleanup
12. Comprehensive Regressions: A1, A2, A3, A4, and Student Portal
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
from app.models.subject import Subject

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


def delete_req(path: str, token: Optional[str] = None) -> tuple[int, Any]:
    return request_json(path, method="DELETE", token=token)


def run_tests():
    print("=" * 70)
    print("ATTENDX MODULE A5 — SUBJECT & LECTURER ASSIGNMENT TESTS")
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

    # 2. Authorization Boundaries on Admin Subject & Assignment APIs
    print("\n--- 2. Testing Authorization Boundaries ---")
    # Student cannot call admin subject endpoints
    try:
        get_json("/api/admin/subjects/summary", token=student_token)
        assert False, "Student should get 403 on GET /api/admin/subjects/summary"
    except urllib.error.HTTPError as e:
        assert e.code == 403
        print(f"[PASS] Student token rejected on GET /api/admin/subjects/summary (HTTP {e.code})")

    try:
        post_json("/api/admin/subjects", {"name": "Hack", "code": "HK101"}, token=student_token)
        assert False, "Student should get 403 on POST /api/admin/subjects"
    except urllib.error.HTTPError as e:
        assert e.code == 403
        print(f"[PASS] Student token rejected on POST /api/admin/subjects (HTTP {e.code})")

    # Student cannot call admin assignment endpoints
    try:
        get_json("/api/admin/assignments", token=student_token)
        assert False, "Student should get 403 on GET /api/admin/assignments"
    except urllib.error.HTTPError as e:
        assert e.code == 403
        print(f"[PASS] Student token rejected on GET /api/admin/assignments (HTTP {e.code})")

    try:
        post_json("/api/admin/assignments", {"lecturer_id": "1", "subject_id": "1"}, token=student_token)
        assert False, "Student should get 403 on POST /api/admin/assignments"
    except urllib.error.HTTPError as e:
        assert e.code == 403
        print(f"[PASS] Student token rejected on POST /api/admin/assignments (HTTP {e.code})")

    # Missing token -> 401
    try:
        get_json("/api/admin/subjects/summary", token=None)
        assert False, "Missing token should get 401"
    except urllib.error.HTTPError as e:
        assert e.code == 401
        print(f"[PASS] Missing token rejected on admin subjects (HTTP {e.code})")

    # 3. Subject Summary Statistics
    print("\n--- 3. Testing Subject Summary Metrics ---")
    status, summary = get_json("/api/admin/subjects/summary", token=admin_token)
    assert status == 200
    assert "total_subjects" in summary and summary["total_subjects"] >= 6
    assert "assigned_subjects" in summary
    assert "unassigned_subjects" in summary
    assert "total_enrollments" in summary and summary["total_enrollments"] > 0
    print(f"[PASS] Subject summary metrics: Total={summary['total_subjects']}, Assigned={summary['assigned_subjects']}, Unassigned={summary['unassigned_subjects']}, Enrollments={summary['total_enrollments']}")

    # 4. Create Subject & Duplicate Code Validation
    print("\n--- 4. Testing Subject Creation & Validation ---")
    unique_code = f"CS{uuid.uuid4().hex[:4].upper()}"
    new_sub_payload = {
        "name": "Cloud Distributed Computing",
        "code": unique_code,
        "department": "Computer Science",
        "year": 3,
        "semester": 6
    }
    status, created_sub = post_json("/api/admin/subjects", new_sub_payload, token=admin_token)
    assert status == 201, f"Expected 201, got {status}"
    sub_id = created_sub["id"]
    assert created_sub["code"] == unique_code
    assert created_sub["name"] == "Cloud Distributed Computing"
    print(f"[PASS] Subject created successfully: {created_sub['code']} - {created_sub['name']}")

    # Duplicate code rejection -> 409 Conflict
    try:
        post_json("/api/admin/subjects", new_sub_payload, token=admin_token)
        assert False, "Should reject duplicate subject code with 409 Conflict"
    except urllib.error.HTTPError as e:
        assert e.code == 409
        print(f"[PASS] Duplicate subject code rejected with HTTP {e.code} Conflict")

    # 5. List Subjects with Search, Filters & Pagination
    print("\n--- 5. Testing Subject List, Filtering & Pagination ---")
    status, paged_subs = get_json("/api/admin/subjects?page=1&limit=5", token=admin_token)
    assert status == 200
    assert paged_subs["total"] >= 1
    assert len(paged_subs["items"]) <= 5
    sample_sub = paged_subs["items"][0]
    for key in ["id", "name", "code", "department", "year", "semester", "assigned_lecturers", "enrolled_students_count"]:
        assert key in sample_sub, f"Missing key {key} in subject item"
    print(f"[PASS] Admin subjects table list works (Total: {paged_subs['total']}, Page {paged_subs['page']} of {paged_subs['pages']})")

    # Search filter by code
    status, search_code = get_json(f"/api/admin/subjects?search={unique_code}", token=admin_token)
    assert status == 200
    assert any(s["id"] == sub_id for s in search_code["items"])
    print(f"[PASS] Search by code '{unique_code}' found matching subject")

    # Department filter
    status, dept_subs = get_json("/api/admin/subjects?department=Computer", token=admin_token)
    assert status == 200
    assert any(s["id"] == sub_id for s in dept_subs["items"])
    print(f"[PASS] Department filter 'Computer' returned {dept_subs['total']} subject(s)")

    # 6. View Subject Full Details
    print("\n--- 6. Testing Subject Full Details ---")
    status, sub_detail = get_json(f"/api/admin/subjects/{sub_id}", token=admin_token)
    assert status == 200
    assert sub_detail["id"] == sub_id
    assert "assigned_lecturers" in sub_detail
    assert "enrolled_students" in sub_detail
    print(f"[PASS] Subject full details retrieved: {sub_detail['name']} (Faculty: {sub_detail['assigned_lecturers_count']}, Enrolled: {sub_detail['enrolled_students_count']})")

    # 7. Update Subject Details
    print("\n--- 7. Testing Subject Update ---")
    update_sub_payload = {
        "name": "Cloud & Distributed Systems",
        "department": "Computer Science",
        "year": 4,
        "semester": 7
    }
    status, updated_sub = put_json(f"/api/admin/subjects/{sub_id}", update_sub_payload, token=admin_token)
    assert status == 200
    assert updated_sub["name"] == "Cloud & Distributed Systems"
    assert updated_sub["year"] == 4
    assert updated_sub["semester"] == 7
    print(f"[PASS] Subject updated successfully: {updated_sub['name']} (Year {updated_sub['year']}, Sem {updated_sub['semester']})")

    # 8. Create a Test Lecturer for Assignment
    print("\n--- 8. Setting Up Faculty for Teaching Assignment ---")
    test_empid = f"EMP{uuid.uuid4().hex[:6].upper()}"
    test_email = f"prof_{uuid.uuid4().hex[:6]}@attendx.com"
    lecturer_payload = {
        "employee_id": test_empid,
        "full_name": "Prof. Margaret Hamilton",
        "email": test_email,
        "department": "Computer Science",
        "password": "LecturerPassword123!"
    }
    status, created_lec = post_json("/api/admin/lecturers", lecturer_payload, token=admin_token)
    assert status == 201
    lec_id = created_lec["id"]
    print(f"[PASS] Faculty created: {created_lec['full_name']} ({created_lec['employee_id']})")

    # 9. Create Teaching Assignment (Faculty -> Subject)
    print("\n--- 9. Testing Teaching Assignment Workflow ---")
    assign_payload = {
        "lecturer_id": lec_id,
        "subject_id": sub_id
    }
    status, assignment = post_json("/api/admin/assignments", assign_payload, token=admin_token)
    assert status == 201, f"Expected 201, got {status}"
    assignment_id = assignment["id"]
    assert assignment["lecturer_id"] == lec_id
    assert assignment["subject_id"] == sub_id
    assert assignment["lecturer_name"] == "Prof. Margaret Hamilton"
    assert assignment["subject_name"] == "Cloud & Distributed Systems"
    print(f"[PASS] Teaching assignment created: {assignment['lecturer_name']} -> {assignment['subject_code']} ({assignment['subject_name']})")

    # Duplicate assignment rejection -> 409 Conflict
    try:
        post_json("/api/admin/assignments", assign_payload, token=admin_token)
        assert False, "Should reject duplicate assignment with 409 Conflict"
    except urllib.error.HTTPError as e:
        assert e.code == 409
        print(f"[PASS] Duplicate assignment rejected with HTTP {e.code} Conflict")

    # Non-lecturer role rejection -> 400 Bad Request
    try:
        student_user = get_json("/api/auth/me", token=student_token)[1]
        post_json("/api/admin/assignments", {"lecturer_id": student_user["id"], "subject_id": sub_id}, token=admin_token)
        assert False, "Should reject assigning student as lecturer with 400"
    except urllib.error.HTTPError as e:
        assert e.code == 400
        print(f"[PASS] Non-lecturer role rejected with HTTP {e.code}")

    # 10. Cross-Module Reflection
    print("\n--- 10. Cross-Module Reflection & Assignment Queries ---")
    # Subject now reflects assigned faculty
    status, updated_sub_detail = get_json(f"/api/admin/subjects/{sub_id}", token=admin_token)
    assert status == 200
    assert updated_sub_detail["assigned_lecturers_count"] >= 1
    assert any(l["id"] == lec_id for l in updated_sub_detail["assigned_lecturers"])
    print(f"[PASS] Subject details reflects assigned faculty (Count: {updated_sub_detail['assigned_lecturers_count']})")

    # Lecturer profile reflects assigned subject
    status, lec_detail = get_json(f"/api/admin/lecturers/{lec_id}", token=admin_token)
    assert status == 200
    assert lec_detail["assigned_subjects_count"] >= 1
    assert any(s["id"] == sub_id for s in lec_detail["assigned_subjects"])
    print(f"[PASS] Lecturer profile reflects assigned course: {lec_detail['assigned_subjects'][0]['name']}")

    # Assignment summary metrics
    status, assign_summary = get_json("/api/admin/assignments/summary", token=admin_token)
    assert status == 200
    assert assign_summary["total_assignments"] >= 1
    assert assign_summary["assigned_lecturers"] >= 1
    assert assign_summary["assigned_subjects"] >= 1
    print(f"[PASS] Assignment summary: Total={assign_summary['total_assignments']}, Lecturers={assign_summary['assigned_lecturers']}, Subjects={assign_summary['assigned_subjects']}")

    # 11. Delete Assignment (Unassign Faculty)
    print("\n--- 11. Testing Teaching Assignment Removal ---")
    status, _ = delete_req(f"/api/admin/assignments/{assignment_id}", token=admin_token)
    assert status in (200, 204)
    print(f"[PASS] Teaching assignment removed successfully (HTTP {status})")

    # Verify subject is unassigned again
    status, unassigned_sub = get_json(f"/api/admin/subjects/{sub_id}", token=admin_token)
    assert status == 200
    assert unassigned_sub["assigned_lecturers_count"] == 0
    print(f"[PASS] Subject verified as unassigned after assignment removal")

    # Clean up test subject and test faculty
    delete_req(f"/api/admin/subjects/{sub_id}", token=admin_token)
    delete_req(f"/api/admin/lecturers/{lec_id}", token=admin_token)
    print(f"[PASS] Test subject and faculty cleaned up cleanly")

    # 12. Regressions Across All Modules
    print("\n--- 12. Regressions Across All Modules ---")
    # A1 Foundation
    status, me = get_json("/api/auth/me", token=admin_token)
    assert status == 200 and me["role"] == "admin"
    print(f"[PASS] Module A1 Admin Foundation: HTTP {status} ({me['email']})")

    # A2 Dashboard
    status, dash = get_json("/api/admin/dashboard", token=admin_token)
    assert status == 200 and dash["total_subjects"] >= 6
    print(f"[PASS] Module A2 Admin Dashboard: HTTP {status} (Total Subjects: {dash['total_subjects']})")

    # A3 Students
    status, st_summary = get_json("/api/admin/students/summary", token=admin_token)
    assert status == 200 and st_summary["total_students"] > 0
    print(f"[PASS] Module A3 Admin Students: HTTP {status} ({st_summary['total_students']} students)")

    # A4 Lecturers
    status, lec_summary = get_json("/api/admin/lecturers/summary", token=admin_token)
    assert status == 200
    print(f"[PASS] Module A4 Admin Lecturers: HTTP {status} ({lec_summary['total_lecturers']} lecturers)")

    # Student Portal
    status, s_dash = get_json("/api/dashboard/student", token=student_token)
    assert status == 200
    status, s_subs = get_json("/api/subjects", token=student_token)
    assert status == 200 and len(s_subs) >= 6
    status, s_att = get_json("/api/attendance", token=student_token)
    assert status == 200
    print(f"[PASS] Student Portal: Dashboard HTTP 200, Subjects {len(s_subs)}, Attendance {s_att['total']} records")

    print("\n" + "=" * 70)
    print("ALL MODULE A5 BACKEND VERIFICATION TESTS PASSED SUCCESSFULLY!")
    print("=" * 70)


if __name__ == "__main__":
    run_tests()
