"""
ATTENDX MODULE L1 — LECTURER FOUNDATION VERIFICATION SUITE
Comprehensive test suite verifying:
1. Lecturer Authentication:
   - Login with valid lecturer credentials succeeds (200 OK)
   - Returns JWT access_token and user object with role = 'lecturer'
   - Invalid password rejected with 401 Unauthorized
   - Disabled/inactive lecturer rejected with 403 Forbidden
2. Backend Authorization & RBAC:
   - get_current_lecturer succeeds for authenticated lecturer
   - Student token on GET /api/lecturer/me -> 403 Forbidden
   - Admin token on GET /api/lecturer/me -> 403 Forbidden
   - Missing token -> 401 Unauthorized
   - Invalid/malformed token -> 401 Unauthorized
   - Expired token -> 401 Unauthorized
   - GET /api/lecturers/me alias works identically
3. Security Boundaries & Privilege Isolation:
   - Lecturer cannot access admin dashboard -> 403 Forbidden
   - Lecturer cannot access admin students -> 403 Forbidden
   - Lecturer cannot access admin lecturers -> 403 Forbidden
   - Lecturer cannot access admin subjects -> 403 Forbidden
   - Lecturer cannot access admin assignments -> 403 Forbidden
   - Lecturer cannot access student dashboard -> 403 Forbidden
   - Attendance marking boundary: POST /api/attendance remains restricted to Admin (403 for lecturer)
4. Comprehensive Regressions:
   - Admin A1 Foundation: GET /api/auth/me (200 OK)
   - Admin A2 Dashboard: GET /api/admin/dashboard (200 OK)
   - Admin A3 Students: GET /api/admin/students/summary (200 OK)
   - Admin A4 Lecturers: GET /api/admin/lecturers/summary (200 OK)
   - Admin A5 Subjects: GET /api/admin/subjects/summary (200 OK)
   - Admin A5 Assignments: GET /api/admin/assignments/summary (200 OK)
   - Student Portal: Login, Dashboard, Subjects, Attendance, Notifications (200 OK)
"""
import sys
from pathlib import Path
from datetime import timedelta

backend_dir = Path(__file__).resolve().parent
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

from starlette.testclient import TestClient
from app.main import app
from app.core.database import SessionLocal
from app.core.security import create_access_token, hash_password
from app.models.user import User

client = TestClient(app)


def run_tests():
    print("=" * 70)
    print("ATTENDX MODULE L1 — LECTURER FOUNDATION VERIFICATION SUITE")
    print("=" * 70)

    # 1. Setup & Pre-flight Database Check
    print("\n--- 1. Pre-flight & Account Verification ---")
    db = SessionLocal()
    try:
        # Verify/ensure standard sample lecturer
        lecturer = db.query(User).filter(User.email == "dr.alan@lecturer.com").first()
        if not lecturer:
            lecturer = User(
                email="dr.alan@lecturer.com",
                full_name="Dr. Alan Turing",
                password_hash=hash_password("LecturerPassword123!"),
                role="lecturer",
                employee_id="EMP-CS-001",
                department="Computer Science",
                is_active=True,
            )
            db.add(lecturer)
            db.commit()
            db.refresh(lecturer)
            print("  Created sample lecturer: dr.alan@lecturer.com")
        else:
            lecturer.is_active = True
            lecturer.password_hash = hash_password("LecturerPassword123!")
            db.commit()
            print(f"  Verified sample lecturer: {lecturer.email} (Role: {lecturer.role})")
    finally:
        db.close()

    # 2. Authentication Flow
    print("\n--- 2. Authentication Flow Tests ---")
    # Valid Lecturer Login
    resp = client.post("/api/auth/login", json={"email": "dr.alan@lecturer.com", "password": "LecturerPassword123!"})
    assert resp.status_code == 200, f"Expected 200, got {resp.status_code}: {resp.text}"
    data = resp.json()
    lecturer_token = data["access_token"]
    assert data["user"]["role"] == "lecturer"
    assert data["user"]["employee_id"] == "EMP-CS-001"
    assert "password" not in data["user"] and "password_hash" not in data["user"]
    print(f"[PASS] Lecturer login succeeded: role='{data['user']['role']}', employee_id='{data['user']['employee_id']}'")

    # Invalid Password for Lecturer
    bad_resp = client.post("/api/auth/login", json={"email": "dr.alan@lecturer.com", "password": "WrongPassword!"})
    assert bad_resp.status_code == 401
    print(f"[PASS] Invalid lecturer password rejected (HTTP 401: {bad_resp.json().get('detail')})")

    # Admin Login
    a_resp = client.post("/api/auth/login", json={"email": "admin@attendx.com", "password": "AdminPassword123!"})
    assert a_resp.status_code == 200
    admin_token = a_resp.json()["access_token"]
    print(f"[PASS] Admin login succeeded (role='{a_resp.json()['user']['role']}')")

    # Student Login
    s_resp = client.post("/api/auth/login", json={"email": "john.doe@student.com", "password": "StudentPassword123!"})
    assert s_resp.status_code == 200
    student_token = s_resp.json()["access_token"]
    print(f"[PASS] Student login succeeded (role='{s_resp.json()['user']['role']}')")

    # 3. GET /api/lecturer/me Endpoint Tests
    print("\n--- 3. Lecturer Profile (/api/lecturer/me) Tests ---")
    me_resp = client.get("/api/lecturer/me", headers={"Authorization": f"Bearer {lecturer_token}"})
    assert me_resp.status_code == 200, f"Expected 200, got {me_resp.status_code}: {me_resp.text}"
    me_data = me_resp.json()
    assert me_data["role"] == "lecturer"
    assert me_data["email"] == "dr.alan@lecturer.com"
    assert me_data["full_name"] == "Dr. Alan Turing"
    assert "password_hash" not in me_data
    print(f"[PASS] GET /api/lecturer/me returned lecturer profile: {me_data['full_name']} ({me_data['email']})")

    # Alias /api/lecturers/me
    alias_resp = client.get("/api/lecturers/me", headers={"Authorization": f"Bearer {lecturer_token}"})
    assert alias_resp.status_code == 200
    assert alias_resp.json()["id"] == me_data["id"]
    print("[PASS] GET /api/lecturers/me alias returned identical profile (HTTP 200)")

    # 4. RBAC & Security Boundary Tests on /api/lecturer/me
    print("\n--- 4. Lecturer RBAC & Security Boundary Tests ---")
    # Student token on lecturer endpoint -> 403 Forbidden
    st_resp = client.get("/api/lecturer/me", headers={"Authorization": f"Bearer {student_token}"})
    assert st_resp.status_code == 403, f"Expected 403 for student token, got {st_resp.status_code}"
    print(f"[PASS] Student token rejected on GET /api/lecturer/me (HTTP 403: {st_resp.json().get('detail')})")

    # Admin token on lecturer endpoint -> 403 Forbidden
    adm_resp = client.get("/api/lecturer/me", headers={"Authorization": f"Bearer {admin_token}"})
    assert adm_resp.status_code == 403, f"Expected 403 for admin token, got {adm_resp.status_code}"
    print(f"[PASS] Admin token rejected on GET /api/lecturer/me (HTTP 403: {adm_resp.json().get('detail')})")

    # Missing token -> 401 Unauthorized
    no_resp = client.get("/api/lecturer/me")
    assert no_resp.status_code == 401
    print("[PASS] Missing token rejected (HTTP 401)")

    # Invalid token -> 401 Unauthorized
    inv_resp = client.get("/api/lecturer/me", headers={"Authorization": "Bearer invalid.jwt.token"})
    assert inv_resp.status_code == 401
    print("[PASS] Invalid token rejected (HTTP 401)")

    # Expired token -> 401 Unauthorized
    expired_token = create_access_token({"sub": me_data["id"], "role": "lecturer"}, expires_delta=timedelta(seconds=-10))
    exp_resp = client.get("/api/lecturer/me", headers={"Authorization": f"Bearer {expired_token}"})
    assert exp_resp.status_code == 401
    print("[PASS] Expired token rejected (HTTP 401)")

    # Inactive / Disabled Lecturer token -> 403 Forbidden
    db = SessionLocal()
    try:
        lecturer_obj = db.query(User).filter(User.email == "dr.alan@lecturer.com").first()
        lecturer_obj.is_active = False
        db.commit()

        disabled_resp = client.get("/api/lecturer/me", headers={"Authorization": f"Bearer {lecturer_token}"})
        assert disabled_resp.status_code == 403
        print(f"[PASS] Disabled lecturer account rejected with HTTP 403: {disabled_resp.json().get('detail')}")

        # Restore active status
        lecturer_obj.is_active = True
        db.commit()
    finally:
        db.close()

    # 5. Lecturer Privilege Escalation Isolation Tests
    print("\n--- 5. Lecturer Privilege Escalation Isolation Tests ---")
    # Lecturer cannot access admin dashboard
    r1 = client.get("/api/admin/dashboard", headers={"Authorization": f"Bearer {lecturer_token}"})
    assert r1.status_code == 403
    print(f"[PASS] Lecturer blocked from /api/admin/dashboard (HTTP 403: {r1.json().get('detail')})")

    # Lecturer cannot access admin students
    r2 = client.get("/api/admin/students", headers={"Authorization": f"Bearer {lecturer_token}"})
    assert r2.status_code == 403
    print(f"[PASS] Lecturer blocked from /api/admin/students (HTTP 403)")

    # Lecturer cannot access admin lecturers
    r3 = client.get("/api/admin/lecturers", headers={"Authorization": f"Bearer {lecturer_token}"})
    assert r3.status_code == 403
    print(f"[PASS] Lecturer blocked from /api/admin/lecturers (HTTP 403)")

    # Lecturer cannot access admin subjects
    r4 = client.get("/api/admin/subjects", headers={"Authorization": f"Bearer {lecturer_token}"})
    assert r4.status_code == 403
    print(f"[PASS] Lecturer blocked from /api/admin/subjects (HTTP 403)")

    # Lecturer cannot access admin assignments
    r5 = client.get("/api/admin/assignments", headers={"Authorization": f"Bearer {lecturer_token}"})
    assert r5.status_code == 403
    print(f"[PASS] Lecturer blocked from /api/admin/assignments (HTTP 403)")

    # Lecturer cannot access student dashboard
    r6 = client.get("/api/dashboard/student", headers={"Authorization": f"Bearer {lecturer_token}"})
    assert r6.status_code == 403
    print(f"[PASS] Lecturer blocked from /api/dashboard/student (HTTP 403)")

    # Attendance marking boundary check: POST /api/attendance remains admin-only in L1
    r7 = client.post("/api/attendance", json={"subject_id": "dummy", "attendance_date": "2026-09-30", "records": []},
                     headers={"Authorization": f"Bearer {lecturer_token}"})
    assert r7.status_code == 403
    print(f"[PASS] Attendance marking boundary preserved: lecturer gets HTTP 403 on POST /api/attendance")

    # 6. Regressions Across All Preceding Modules
    print("\n--- 6. Regression Testing Across All Modules ---")
    # A1: Admin Me
    reg_me = client.get("/api/auth/me", headers={"Authorization": f"Bearer {admin_token}"})
    assert reg_me.status_code == 200 and reg_me.json()["role"] == "admin"
    print(f"[PASS] Regression Module A1: Admin auth verified ({reg_me.json()['email']})")

    # A2: Admin Dashboard
    reg_dash = client.get("/api/admin/dashboard", headers={"Authorization": f"Bearer {admin_token}"})
    assert reg_dash.status_code == 200 and reg_dash.json()["total_students"] > 0
    print(f"[PASS] Regression Module A2: Admin dashboard verified ({reg_dash.json()['total_students']} students)")

    # A3: Admin Students
    reg_st = client.get("/api/admin/students/summary", headers={"Authorization": f"Bearer {admin_token}"})
    assert reg_st.status_code == 200
    print(f"[PASS] Regression Module A3: Admin students summary verified")

    # A4: Admin Lecturers
    reg_lec = client.get("/api/admin/lecturers/summary", headers={"Authorization": f"Bearer {admin_token}"})
    assert reg_lec.status_code == 200
    print(f"[PASS] Regression Module A4: Admin lecturers summary verified")

    # A5: Admin Subjects & Assignments
    reg_sub = client.get("/api/admin/subjects/summary", headers={"Authorization": f"Bearer {admin_token}"})
    assert reg_sub.status_code == 200
    reg_asg = client.get("/api/admin/assignments/summary", headers={"Authorization": f"Bearer {admin_token}"})
    assert reg_asg.status_code == 200
    print(f"[PASS] Regression Module A5: Admin subjects & assignments verified")

    # Student Portal Regressions
    s_dash = client.get("/api/dashboard/student", headers={"Authorization": f"Bearer {student_token}"})
    assert s_dash.status_code == 200
    s_subs = client.get("/api/subjects", headers={"Authorization": f"Bearer {student_token}"})
    assert s_subs.status_code == 200
    s_att = client.get("/api/attendance", headers={"Authorization": f"Bearer {student_token}"})
    assert s_att.status_code == 200
    s_notif = client.get("/api/notifications", headers={"Authorization": f"Bearer {student_token}"})
    assert s_notif.status_code == 200
    print(f"[PASS] Regression Student Portal: Dashboard, Subjects, Attendance, Notifications verified (HTTP 200)")

    print("\n" + "=" * 70)
    print("ALL MODULE L1 LECTURER FOUNDATION TESTS PASSED SUCCESSFULLY!")
    print("=" * 70)


if __name__ == "__main__":
    run_tests()
