"""
AttendX — Module I4 Security Audit Verification Suite
Tests the complete security architecture across all portals, database events, and APIs:

LAYER 1 — UNIT & INTEGRATION SECURITY TESTS
1. Authentication Security (401 on missing, invalid, expired, or malformed tokens)
2. Password Security (Bcrypt hashing, credentials verification, password_hash excluded from all responses)
3. Disabled Account Invalidation (Active check in get_current_user rejects disabled accounts immediately with 403)
4. Role-Based Access Control (RBAC matrix enforcement: Student, Lecturer, Admin)
5. Student Isolation & IDOR Protection (Profile, Attendance, Notifications, Rosters, Enrollments)
6. Lecturer Isolation & IDOR Protection (Assigned vs Unassigned Subject attendance, rosters, records, reports, export)
7. Attendance Engine Security (Student modification blocked, future dates rejected, invalid status handled)
8. Notification Privacy (Ownership isolation, ID guessing rejected, read-all scoped to self)
9. Database Integrity Constraints (Unique constraints on attendance, enrollments, assignments)
10. Configuration & CORS Security (JWT secrets, CORS origins handling)

LAYER 2 — END-TO-END SECURITY ATTACK FLOWS
11. FLOW 1: Student Isolation Attack Flow (Student A attempts Student B resources -> blocked)
12. FLOW 2: Lecturer Subject Isolation Attack Flow (Lecturer A attempts Lecturer B subject -> blocked)
13. FLOW 3: Admin Management & Account Revocation Flow (Admin disables account -> token invalidated)
14. FLOW 4: Cross-Role Privilege Escalation Attack Flow (Students/Lecturers attempt Admin/Lecturer actions -> blocked)

LAYER 3 — INPUT VALIDATION, EDGE CASES & REGRESSION
15. Malformed dates, out-of-range pagination, non-existent resource IDs handled cleanly
16. Safe error responses (Zero stack trace or internal database string leaks)
17. Full regression stability check across Student, Lecturer, and Admin workflows
"""
import sys
import os
from datetime import date, timedelta, datetime, timezone
import uuid

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__))))

from fastapi.testclient import TestClient
from app.main import app
from app.core.database import SessionLocal
from app.core.security import create_access_token, hash_password
from app.core.config import get_settings
from app.models.user import User
from app.models.subject import Subject
from app.models.student_subject import StudentSubject
from app.models.lecturer_subject import LecturerSubject
from app.models.attendance import Attendance
from app.models.notification import Notification

settings = get_settings()


def run_i4_security_audit_suite():
    print("=" * 80)
    print("ATTENDX — MODULE I4 SECURITY AUDIT VERIFICATION SUITE")
    print("=" * 80)

    client = TestClient(app)
    db = SessionLocal()

    total_tests = 0
    passed_tests = 0

    def check(title: str, condition: bool, details: str = ""):
        nonlocal total_tests, passed_tests
        total_tests += 1
        if condition:
            passed_tests += 1
            print(f"  [PASS] {title}")
        else:
            print(f"  [FAIL] {title} — {details}")
            assert False, f"Security Check Failed: {title} — {details}"

    admin = None
    student_a = None
    student_b = None
    lecturer_a = None
    lecturer_b = None
    subj_a = None
    subj_b = None
    disabled_user = None

    try:
        # ====================================================================
        # SETUP TEST FIXTURES
        # ====================================================================
        print("\n--- [SETUP] Provisioning Isolated Test Entities ---")
        suffix = uuid.uuid4().hex[:6]

        # 1. Admin
        admin = User(
            full_name=f"Security Admin {suffix}",
            email=f"admin_{suffix}@attendx.com",
            password_hash=hash_password("adminSecret123"),
            role="admin",
            is_active=True,
        )
        db.add(admin)

        # 2. Student A & Student B
        student_a = User(
            full_name=f"Alice Student {suffix}",
            email=f"alice_{suffix}@attendx.com",
            password_hash=hash_password("alicePass123"),
            role="student",
            student_id=f"STU-A-{suffix}",
            department="CSE",
            year=3,
            section="A",
            is_active=True,
        )
        student_b = User(
            full_name=f"Bob Student {suffix}",
            email=f"bob_{suffix}@attendx.com",
            password_hash=hash_password("bobPass123"),
            role="student",
            student_id=f"STU-B-{suffix}",
            department="CSE",
            year=3,
            section="B",
            is_active=True,
        )
        db.add_all([student_a, student_b])

        # 3. Lecturer A & Lecturer B
        lecturer_a = User(
            full_name=f"Dr. Alan Lecturer {suffix}",
            email=f"alan_{suffix}@attendx.com",
            password_hash=hash_password("alanPass123"),
            role="lecturer",
            employee_id=f"EMP-A-{suffix}",
            department="CSE",
            is_active=True,
        )
        lecturer_b = User(
            full_name=f"Dr. Barbara Lecturer {suffix}",
            email=f"barbara_{suffix}@attendx.com",
            password_hash=hash_password("barbaraPass123"),
            role="lecturer",
            employee_id=f"EMP-B-{suffix}",
            department="ECE",
            is_active=True,
        )
        db.add_all([lecturer_a, lecturer_b])

        # 4. Subject A (taught by Lecturer A) & Subject B (taught by Lecturer B)
        subj_a = Subject(
            name=f"Artificial Intelligence {suffix}",
            code=f"AI-{suffix.upper()}",
            department="CSE",
            year=3,
            semester=1,
        )
        subj_b = Subject(
            name=f"Embedded Systems {suffix}",
            code=f"ES-{suffix.upper()}",
            department="ECE",
            year=3,
            semester=2,
        )
        db.add_all([subj_a, subj_b])
        db.commit()
        db.refresh(admin)
        db.refresh(student_a)
        db.refresh(student_b)
        db.refresh(lecturer_a)
        db.refresh(lecturer_b)
        db.refresh(subj_a)
        db.refresh(subj_b)

        # 5. Teaching Assignments: Lecturer A -> Subj A, Lecturer B -> Subj B
        assign_a = LecturerSubject(lecturer_id=lecturer_a.id, subject_id=subj_a.id)
        assign_b = LecturerSubject(lecturer_id=lecturer_b.id, subject_id=subj_b.id)
        db.add_all([assign_a, assign_b])

        # 6. Student Enrollments: Student A in Subj A, Student B in Subj B
        enroll_a = StudentSubject(student_id=student_a.id, subject_id=subj_a.id)
        enroll_b = StudentSubject(student_id=student_b.id, subject_id=subj_b.id)
        db.add_all([enroll_a, enroll_b])

        # 7. Attendance: Subj A attended by Student A, Subj B attended by Student B
        today = date.today()
        yesterday = today - timedelta(days=1)
        att_a = Attendance(
            student_id=student_a.id,
            subject_id=subj_a.id,
            attendance_date=yesterday,
            status="present",
            marked_by=lecturer_a.id,
        )
        att_b = Attendance(
            student_id=student_b.id,
            subject_id=subj_b.id,
            attendance_date=yesterday,
            status="absent",
            marked_by=lecturer_b.id,
        )
        db.add_all([att_a, att_b])

        # 8. Notifications for Student A and Student B
        notif_a = Notification(
            user_id=student_a.id,
            title="Attendance Recorded",
            message="You were marked Present in AI",
            type="attendance",
            is_read=False,
        )
        notif_b = Notification(
            user_id=student_b.id,
            title="Attendance Recorded",
            message="You were marked Absent in ES",
            type="attendance",
            is_read=False,
        )
        db.add_all([notif_a, notif_b])
        db.commit()
        db.refresh(att_a)
        db.refresh(att_b)
        db.refresh(notif_a)
        db.refresh(notif_b)

        # Tokens
        admin_token = create_access_token({"sub": admin.id, "role": admin.role})
        student_a_token = create_access_token({"sub": student_a.id, "role": student_a.role})
        student_b_token = create_access_token({"sub": student_b.id, "role": student_b.role})
        lecturer_a_token = create_access_token({"sub": lecturer_a.id, "role": lecturer_a.role})
        lecturer_b_token = create_access_token({"sub": lecturer_b.id, "role": lecturer_b.role})

        h_admin = {"Authorization": f"Bearer {admin_token}"}
        h_student_a = {"Authorization": f"Bearer {student_a_token}"}
        h_student_b = {"Authorization": f"Bearer {student_b_token}"}
        h_lecturer_a = {"Authorization": f"Bearer {lecturer_a_token}"}
        h_lecturer_b = {"Authorization": f"Bearer {lecturer_b_token}"}

        print("[SETUP] Fixtures provisioned successfully.")

        # ====================================================================
        # LAYER 1: UNIT & INTEGRATION SECURITY TESTS
        # ====================================================================
        print("\n" + "=" * 60)
        print("LAYER 1: UNIT & INTEGRATION SECURITY TESTS")
        print("=" * 60)

        # 1.1 Authentication & Token Validation
        print("\n--- 1. Authentication & Token Security ---")
        # Missing token
        r = client.get("/api/auth/me")
        check("Missing token rejected with 401 Unauthorized", r.status_code == 401)

        # Malformed token
        r = client.get("/api/auth/me", headers={"Authorization": "Bearer not-a-valid-jwt"})
        check("Malformed token rejected with 401 Unauthorized", r.status_code == 401)

        # Expired token
        expired_token = create_access_token({"sub": student_a.id, "role": "student"}, expires_delta=timedelta(minutes=-10))
        r = client.get("/api/auth/me", headers={"Authorization": f"Bearer {expired_token}"})
        check("Expired token rejected with 401 Unauthorized", r.status_code == 401)

        # Invalid login credentials
        r = client.post("/api/auth/login", json={"email": student_a.email, "password": "WrongPassword"})
        check("Invalid password rejected with 401 Unauthorized", r.status_code == 401, f"got {r.status_code}: {r.text}")

        # Successful login verification
        r = client.post("/api/auth/login", json={"email": student_a.email, "password": "alicePass123"})
        check("Valid credentials succeed with 200 OK", r.status_code == 200)
        login_body = r.json()
        check("Login response contains access_token", "access_token" in login_body)
        check("Login response does NOT leak password_hash", "password_hash" not in str(login_body))
        check("Login response does NOT leak raw password", "password" not in login_body.get("user", {}))

        # Check /api/auth/me does not leak password hash
        r = client.get("/api/auth/me", headers=h_student_a)
        check("/api/auth/me does NOT leak password_hash", "password_hash" not in str(r.json()))

        # 1.2 Disabled Account Revocation
        print("\n--- 2. Disabled Account Security ---")
        disabled_user = User(
            full_name=f"Disabled User {suffix}",
            email=f"disabled_{suffix}@attendx.com",
            password_hash=hash_password("secret123"),
            role="student",
            is_active=False,
        )
        db.add(disabled_user)
        db.commit()
        db.refresh(disabled_user)

        # Disabled account cannot login
        r = client.post("/api/auth/login", json={"email": disabled_user.email, "password": "secret123"})
        check("Disabled account cannot log in (403)", r.status_code == 403)

        # Token held by a disabled account is rejected across endpoints
        disabled_token = create_access_token({"sub": disabled_user.id, "role": "student"})
        r = client.get("/api/auth/me", headers={"Authorization": f"Bearer {disabled_token}"})
        check("Existing token for disabled account rejected immediately with 403", r.status_code == 403)

        # 1.3 Role-Based Access Control (RBAC)
        print("\n--- 3. Role-Based Access Control (RBAC) ---")
        # Student attempting Admin routes -> 403
        check("Student blocked from /api/admin/students (403)", client.get("/api/admin/students", headers=h_student_a).status_code == 403)
        check("Student blocked from /api/admin/lecturers (403)", client.get("/api/admin/lecturers", headers=h_student_a).status_code == 403)
        check("Student blocked from /api/admin/subjects (403)", client.get("/api/admin/subjects", headers=h_student_a).status_code == 403)
        check("Student blocked from /api/admin/assignments (403)", client.get("/api/admin/assignments", headers=h_student_a).status_code == 403)
        check("Student blocked from /api/admin/dashboard (403)", client.get("/api/admin/dashboard", headers=h_student_a).status_code == 403)

        # Student attempting Lecturer routes -> 403
        check("Student blocked from /api/lecturer/subjects (403)", client.get("/api/lecturer/subjects", headers=h_student_a).status_code == 403)
        check("Student blocked from /api/lecturer/attendance (403)", client.get("/api/lecturer/attendance", headers=h_student_a).status_code == 403)
        check("Student blocked from /api/lecturer/records (403)", client.get("/api/lecturer/records", headers=h_student_a).status_code == 403)
        check("Student blocked from /api/lecturer/reports/export (403)", client.get("/api/lecturer/reports/export", headers=h_student_a).status_code == 403)

        # Lecturer attempting Admin routes -> 403
        check("Lecturer blocked from /api/admin/students (403)", client.get("/api/admin/students", headers=h_lecturer_a).status_code == 403)
        check("Lecturer blocked from /api/admin/lecturers (403)", client.get("/api/admin/lecturers", headers=h_lecturer_a).status_code == 403)
        check("Lecturer blocked from /api/admin/subjects (403)", client.get("/api/admin/subjects", headers=h_lecturer_a).status_code == 403)
        check("Lecturer blocked from /api/admin/assignments (403)", client.get("/api/admin/assignments", headers=h_lecturer_a).status_code == 403)
        check("Lecturer blocked from /api/admin/dashboard (403)", client.get("/api/admin/dashboard", headers=h_lecturer_a).status_code == 403)

        # Lecturer attempting Student Dashboard -> 403
        check("Lecturer blocked from /api/dashboard/student (403)", client.get("/api/dashboard/student", headers=h_lecturer_a).status_code == 403)

        # 1.4 Student Isolation & IDOR Protection
        print("\n--- 4. Student Isolation & IDOR Protection ---")
        # Student A requesting Student B's profile
        r = client.get(f"/api/students/{student_b.id}", headers=h_student_a)
        check("Student A cannot view Student B's profile via /api/students/{id} (403)", r.status_code == 403)

        # Student A requesting own profile
        r = client.get(f"/api/students/{student_a.id}", headers=h_student_a)
        check("Student A can view own profile via /api/students/{id} (200)", r.status_code == 200)

        # Student A requesting attendance with student_id=student_b.id
        r = client.get(f"/api/attendance?student_id={student_b.id}", headers=h_student_a)
        check("Student A calling /api/attendance?student_id={B} is scoped to self", r.status_code == 200)
        data = r.json().get("records", [])
        for rec in data:
            check("Returned attendance strictly belongs to Student A", rec["student_id"] == student_a.id)

        # Student A requesting Student B's attendance record by ID
        r = client.get(f"/api/attendance/{att_b.id}", headers=h_student_a)
        check("Student A cannot access Student B's attendance record by ID (403)", r.status_code == 403)

        # Student A requesting own attendance record by ID
        r = client.get(f"/api/attendance/{att_a.id}", headers=h_student_a)
        check("Student A can access own attendance record by ID (200)", r.status_code == 200)

        # Student A attempting to view subject enrolled student roster
        r = client.get(f"/api/subjects/{subj_a.id}/students", headers=h_student_a)
        check("Student A cannot view subject student roster (403 Forbidden)", r.status_code == 403)

        # Student A viewing subject details — enrolled_students must be empty
        r = client.get(f"/api/subjects/{subj_a.id}", headers=h_student_a)
        check("Student A get subject details succeeds (200)", r.status_code == 200)
        check("Student A subject details has enrolled_students list stripped", r.json().get("enrolled_students") == [])

        # Student A attempting to enroll Student B
        r = client.post("/api/subjects/enroll", json={"student_id": student_b.id, "subject_id": subj_a.id}, headers=h_student_a)
        check("Student A cannot enroll Student B in a subject (403 Forbidden)", r.status_code == 403)

        # 1.5 Lecturer Subject Isolation & IDOR Protection
        print("\n--- 5. Lecturer Subject Isolation & IDOR Protection ---")
        # Lecturer A attempting to view students of unassigned Subject B
        r = client.get(f"/api/subjects/{subj_b.id}/students", headers=h_lecturer_a)
        check("Lecturer A blocked from student roster of unassigned Subject B (403)", r.status_code == 403)

        # Lecturer A viewing students of assigned Subject A
        r = client.get(f"/api/subjects/{subj_a.id}/students", headers=h_lecturer_a)
        check("Lecturer A can view student roster of assigned Subject A (200)", r.status_code == 200)

        # Lecturer A querying attendance for unassigned Subject B
        r = client.get(f"/api/attendance?subject_id={subj_b.id}", headers=h_lecturer_a)
        check("Lecturer A blocked from listing attendance for unassigned Subject B (403)", r.status_code == 403)

        # Lecturer A querying attendance for assigned Subject A
        r = client.get(f"/api/attendance?subject_id={subj_a.id}", headers=h_lecturer_a)
        check("Lecturer A can list attendance for assigned Subject A (200)", r.status_code == 200)

        # Lecturer A querying single attendance record belonging to unassigned Subject B
        r = client.get(f"/api/attendance/{att_b.id}", headers=h_lecturer_a)
        check("Lecturer A cannot fetch attendance record of unassigned Subject B (403)", r.status_code == 403)

        # Lecturer A querying single attendance record belonging to assigned Subject A
        r = client.get(f"/api/attendance/{att_a.id}", headers=h_lecturer_a)
        check("Lecturer A can fetch attendance record of assigned Subject A (200)", r.status_code == 200)

        # Lecturer A attempting to mark attendance for unassigned Subject B
        mark_payload_unassigned = {
            "subject_id": subj_b.id,
            "attendance_date": yesterday.isoformat(),
            "records": [{"student_id": student_b.id, "status": "present"}],
        }
        r = client.post("/api/lecturer/attendance", json=mark_payload_unassigned, headers=h_lecturer_a)
        check("Lecturer A cannot mark attendance for unassigned Subject B (403)", r.status_code == 403)

        # Lecturer A attempting to update attendance for unassigned Subject B
        r = client.put(f"/api/lecturer/attendance/{att_b.id}", json={"status": "present"}, headers=h_lecturer_a)
        check("Lecturer A cannot update attendance record for unassigned Subject B (403)", r.status_code == 403)

        # Lecturer A attempting to view records for unassigned Subject B
        r = client.get(f"/api/lecturer/records?subject_id={subj_b.id}", headers=h_lecturer_a)
        check("Lecturer A cannot access attendance records for unassigned Subject B (403)", r.status_code == 403)

        # Lecturer A attempting to view subject report for unassigned Subject B
        r = client.get(f"/api/lecturer/reports/subject/{subj_b.id}", headers=h_lecturer_a)
        check("Lecturer A cannot access subject report for unassigned Subject B (403)", r.status_code == 403)

        # Lecturer A attempting to export report for unassigned Subject B
        r = client.get(f"/api/lecturer/reports/export?export_type=subject&subject_id={subj_b.id}", headers=h_lecturer_a)
        check("Lecturer A cannot export report for unassigned Subject B (403)", r.status_code == 403)

        # 1.6 Attendance Engine Security
        print("\n--- 6. Attendance Engine Security ---")
        # Student cannot mark attendance via admin endpoint
        r = client.post("/api/attendance", json=mark_payload_unassigned, headers=h_student_a)
        check("Student cannot mark attendance via /api/attendance (403)", r.status_code == 403)

        # Student cannot mark attendance via lecturer endpoint
        r = client.post("/api/lecturer/attendance", json=mark_payload_unassigned, headers=h_student_a)
        check("Student cannot mark attendance via /api/lecturer/attendance (403)", r.status_code == 403)

        # Student cannot update attendance record
        r = client.put(f"/api/attendance/{att_a.id}", json={"status": "absent"}, headers=h_student_a)
        check("Student cannot update attendance via /api/attendance/{id} (403)", r.status_code == 403)

        # Student cannot delete attendance record
        r = client.delete(f"/api/attendance/{att_a.id}", headers=h_student_a)
        check("Student cannot delete attendance via /api/attendance/{id} (403)", r.status_code == 403)

        # Future date attendance marking rejected
        future_date = (today + timedelta(days=5)).isoformat()
        future_payload = {
            "subject_id": subj_a.id,
            "attendance_date": future_date,
            "records": [{"student_id": student_a.id, "status": "present"}],
        }
        r = client.post("/api/lecturer/attendance", json=future_payload, headers=h_lecturer_a)
        check("Marking attendance for future dates rejected with 400 Bad Request", r.status_code == 400)

        # 1.7 Notification Privacy & Ownership
        print("\n--- 7. Notification Privacy & Ownership ---")
        # Student A gets only own notifications
        r = client.get("/api/notifications", headers=h_student_a)
        check("Student A can retrieve notifications (200)", r.status_code == 200)
        notifs = r.json()
        check("Student A receives only own notifications", all(n["id"] != notif_b.id for n in notifs))

        # Student A attempting to mark Student B's notification as read
        r = client.patch(f"/api/notifications/{notif_b.id}/read", headers=h_student_a)
        check("Student A cannot mark Student B's notification as read (403)", r.status_code == 403)

        # Student A marks own notification as read
        r = client.patch(f"/api/notifications/{notif_a.id}/read", headers=h_student_a)
        check("Student A can mark own notification as read (200)", r.status_code == 200)
        check("Notification is_read is True", r.json()["is_read"] is True)

        # Read-all only updates current user's notifications
        r = client.patch("/api/notifications/read-all", headers=h_student_a)
        check("Student A read-all succeeds (200)", r.status_code == 200)
        db.refresh(notif_b)
        check("Student B's notification remains unread after Student A's read-all", notif_b.is_read is False)

        # 1.8 Database Constraints Verification
        print("\n--- 8. Database Constraints & Integrity ---")
        # Unique attendance record constraint check
        dup_att = Attendance(
            student_id=student_a.id,
            subject_id=subj_a.id,
            attendance_date=yesterday,
            status="present",
            marked_by=lecturer_a.id,
        )
        db.add(dup_att)
        caught_integrity_error = False
        try:
            db.commit()
        except Exception:
            db.rollback()
            caught_integrity_error = True
        check("Database enforces UniqueConstraint('student_id', 'subject_id', 'attendance_date')", caught_integrity_error)

        # Unique student enrollment constraint check
        dup_enroll = StudentSubject(student_id=student_a.id, subject_id=subj_a.id)
        db.add(dup_enroll)
        caught_enroll_error = False
        try:
            db.commit()
        except Exception:
            db.rollback()
            caught_enroll_error = True
        check("Database enforces UniqueConstraint('student_id', 'subject_id') on enrollments", caught_enroll_error)

        # Unique lecturer assignment constraint check
        dup_assign = LecturerSubject(lecturer_id=lecturer_a.id, subject_id=subj_a.id)
        db.add(dup_assign)
        caught_assign_error = False
        try:
            db.commit()
        except Exception:
            db.rollback()
            caught_assign_error = True
        check("Database enforces UniqueConstraint('lecturer_id', 'subject_id') on assignments", caught_assign_error)

        # 1.9 Configuration & CORS Verification
        print("\n--- 9. Configuration & CORS Security ---")
        check("JWT Secret is defined in configuration", len(settings.JWT_SECRET) >= 16)
        check("JWT Algorithm is HS256", settings.JWT_ALGORITHM == "HS256")
        check("Frontend URL is configured", bool(settings.FRONTEND_URL))

        # ====================================================================
        # LAYER 2: REAL END-TO-END SECURITY ATTACK FLOWS
        # ====================================================================
        print("\n" + "=" * 60)
        print("LAYER 2: REAL END-TO-END SECURITY ATTACK FLOWS")
        print("=" * 60)

        # Flow 1: Student Isolation Attack Flow
        print("\n--- FLOW 1: Student Isolation Attack Flow ---")
        # Alice logs in and inspects her dashboard
        r = client.get("/api/dashboard/student", headers=h_student_a)
        check("Flow 1: Alice accesses own dashboard (200)", r.status_code == 200)
        # Alice attempts to inspect Bob's attendance history
        r = client.get(f"/api/attendance?student_id={student_b.id}", headers=h_student_a)
        check("Flow 1: Alice query for Bob's attendance returns zero Bob records", not any(rec["student_id"] == student_b.id for rec in r.json().get("records", [])))
        # Alice attempts to inspect Bob's private attendance record directly
        r = client.get(f"/api/attendance/{att_b.id}", headers=h_student_a)
        check("Flow 1: Direct IDOR probe on Bob's attendance record blocked (403)", r.status_code == 403)
        # Alice attempts to mark Bob's notification
        r = client.patch(f"/api/notifications/{notif_b.id}/read", headers=h_student_a)
        check("Flow 1: IDOR probe on Bob's notification blocked (403)", r.status_code == 403)

        # Flow 2: Lecturer Subject Isolation Attack Flow
        print("\n--- FLOW 2: Lecturer Subject Isolation Attack Flow ---")
        # Alan accesses his assigned subject attendance session
        r = client.get(f"/api/lecturer/attendance/session?subject_id={subj_a.id}&attendance_date={yesterday.isoformat()}", headers=h_lecturer_a)
        check("Flow 2: Alan accesses assigned Subject A session (200)", r.status_code == 200)
        # Alan attempts to access Subject B attendance session
        r = client.get(f"/api/lecturer/attendance/session?subject_id={subj_b.id}&attendance_date={yesterday.isoformat()}", headers=h_lecturer_a)
        check("Flow 2: Alan probe on unassigned Subject B session blocked (403)", r.status_code == 403)

        # Alan attempts to modify Bob's attendance in Subject B
        r = client.put(f"/api/lecturer/attendance/{att_b.id}", json={"status": "present"}, headers=h_lecturer_a)
        check("Flow 2: Alan modification of Subject B attendance record blocked (403)", r.status_code == 403)
        # Alan attempts to export Subject B attendance report
        r = client.get(f"/api/lecturer/reports/export?export_type=subject&subject_id={subj_b.id}", headers=h_lecturer_a)
        check("Flow 2: Alan export of unassigned Subject B blocked (403)", r.status_code == 403)

        # Flow 3: Admin Management & Account Revocation Flow
        print("\n--- FLOW 3: Admin Management & Account Revocation Flow ---")
        # Admin checks system health and summaries
        r = client.get("/api/admin/dashboard", headers=h_admin)
        check("Flow 3: Admin accesses dashboard (200)", r.status_code == 200)
        # Admin disables Bob's account
        r = client.post(f"/api/admin/students/{student_b.id}/disable", headers=h_admin)
        check("Flow 3: Admin disables Bob's student account (200)", r.status_code == 200)
        # Bob attempts to make request with existing token
        r = client.get("/api/dashboard/student", headers=h_student_b)
        check("Flow 3: Bob's existing token blocked immediately after account disabling (403)", r.status_code == 403)
        # Admin re-enables Bob's account
        r = client.post(f"/api/admin/students/{student_b.id}/enable", headers=h_admin)
        check("Flow 3: Admin re-enables Bob's account (200)", r.status_code == 200)
        # Bob's token works again
        r = client.get("/api/dashboard/student", headers=h_student_b)
        check("Flow 3: Bob's token is functional again after re-enabling (200)", r.status_code == 200)

        # Flow 4: Cross-Role Privilege Escalation Attack Flow
        print("\n--- FLOW 4: Cross-Role Privilege Escalation Attack Flow ---")
        # Student attempts to create a lecturer
        new_lec_payload = {
            "full_name": "Rogue Lecturer",
            "email": f"rogue_{suffix}@attendx.com",
            "password": "Password123",
            "employee_id": f"EMP-ROGUE-{suffix}",
            "department": "CSE",
        }
        r = client.post("/api/admin/lecturers", json=new_lec_payload, headers=h_student_a)
        check("Flow 4: Student creation of lecturer account blocked (403)", r.status_code == 403)

        # Lecturer attempts to create teaching assignment
        assign_payload = {
            "lecturer_id": lecturer_a.id,
            "subject_id": subj_b.id,
        }
        r = client.post("/api/admin/assignments", json=assign_payload, headers=h_lecturer_a)
        check("Flow 4: Lecturer creation of teaching assignment blocked (403)", r.status_code == 403)

        # Student attempts to delete subject
        r = client.delete(f"/api/subjects/{subj_a.id}", headers=h_student_a)
        check("Flow 4: Student deletion of subject blocked (403)", r.status_code == 403)

        # ====================================================================
        # LAYER 3: INPUT VALIDATION, EDGE CASES & REGRESSION
        # ====================================================================
        print("\n" + "=" * 60)
        print("LAYER 3: INPUT VALIDATION, EDGE CASES & REGRESSION")
        print("=" * 60)

        # Malformed date format handling
        r = client.get("/api/lecturer/reports/export?export_type=records&date_from=invalid-date", headers=h_lecturer_a)
        check("Malformed date_from parameter rejected with 400 Bad Request", r.status_code == 400)

        # Inverted date range handling (date_from > date_to)
        r = client.get(f"/api/lecturer/reports/subject/{subj_a.id}?date_from=2026-10-10&date_to=2026-10-01", headers=h_lecturer_a)
        check("Inverted date range rejected with 400 Bad Request", r.status_code == 400)

        # Out of bounds pagination limit
        r = client.get("/api/admin/students?limit=500", headers=h_admin)
        check("Excessive pagination limit (>100) rejected with 422 Unprocessable Entity", r.status_code == 422)

        # Non-existent ID handling
        r = client.get(f"/api/subjects/{uuid.uuid4()}/students", headers=h_admin)
        check("Non-existent subject ID returns 404 Not Found", r.status_code == 404)

        r = client.get(f"/api/attendance/{uuid.uuid4()}", headers=h_admin)
        check("Non-existent attendance ID returns 404 Not Found", r.status_code == 404)

        r = client.patch(f"/api/notifications/{uuid.uuid4()}/read", headers=h_student_a)
        check("Non-existent notification ID returns 404 Not Found", r.status_code == 404)

        # Safe error handling (no stack traces)
        r = client.get("/api/non-existent-endpoint-probe")
        check("404 endpoint returns JSON without stack trace", r.status_code == 404 and "Traceback" not in r.text)

        # Core Regressions Check
        print("\n--- Regression Check on Core Portals ---")
        # Student Core
        check("Regression: Student GET /api/dashboard/student (200)", client.get("/api/dashboard/student", headers=h_student_a).status_code == 200)
        check("Regression: Student GET /api/subjects/my-enrollments (200)", client.get("/api/subjects/my-enrollments", headers=h_student_a).status_code == 200)
        check("Regression: Student GET /api/attendance (200)", client.get("/api/attendance", headers=h_student_a).status_code == 200)
        check("Regression: Student GET /api/notifications/unread-count (200)", client.get("/api/notifications/unread-count", headers=h_student_a).status_code == 200)

        # Lecturer Core
        check("Regression: Lecturer GET /api/dashboard/lecturer (200)", client.get("/api/dashboard/lecturer", headers=h_lecturer_a).status_code == 200)
        check("Regression: Lecturer GET /api/lecturer/subjects (200)", client.get("/api/lecturer/subjects", headers=h_lecturer_a).status_code == 200)
        check("Regression: Lecturer GET /api/lecturer/attendance (200)", client.get("/api/lecturer/attendance", headers=h_lecturer_a).status_code == 200)
        check("Regression: Lecturer GET /api/lecturer/records (200)", client.get("/api/lecturer/records", headers=h_lecturer_a).status_code == 200)
        check("Regression: Lecturer GET /api/lecturer/reports/export (200)", client.get("/api/lecturer/reports/export", headers=h_lecturer_a).status_code == 200)

        # Admin Core
        check("Regression: Admin GET /api/admin/dashboard (200)", client.get("/api/admin/dashboard", headers=h_admin).status_code == 200)
        check("Regression: Admin GET /api/admin/students/summary (200)", client.get("/api/admin/students/summary", headers=h_admin).status_code == 200)
        check("Regression: Admin GET /api/admin/lecturers/summary (200)", client.get("/api/admin/lecturers/summary", headers=h_admin).status_code == 200)
        check("Regression: Admin GET /api/admin/subjects/summary (200)", client.get("/api/admin/subjects/summary", headers=h_admin).status_code == 200)
        check("Regression: Admin GET /api/admin/assignments/summary (200)", client.get("/api/admin/assignments/summary", headers=h_admin).status_code == 200)

        # ====================================================================
        # SUMMARY
        # ====================================================================
        print("\n" + "=" * 80)
        print(f"VERIFICATION COMPLETE: {passed_tests}/{total_tests} CHECKS PASSED")
        print("=" * 80)

    finally:
        # Cleanup test fixtures
        print("\n[CLEANUP] Cleaning up test fixtures...")
        try:
            stu_ids = [u.id for u in [student_a, student_b] if u is not None]
            if stu_ids:
                db.query(Notification).filter(Notification.user_id.in_(stu_ids)).delete(synchronize_session=False)
                db.query(Attendance).filter(Attendance.student_id.in_(stu_ids)).delete(synchronize_session=False)
                db.query(StudentSubject).filter(StudentSubject.student_id.in_(stu_ids)).delete(synchronize_session=False)

            lec_ids = [u.id for u in [lecturer_a, lecturer_b] if u is not None]
            if lec_ids:
                db.query(LecturerSubject).filter(LecturerSubject.lecturer_id.in_(lec_ids)).delete(synchronize_session=False)

            sub_ids = [s.id for s in [subj_a, subj_b] if s is not None]
            if sub_ids:
                db.query(Subject).filter(Subject.id.in_(sub_ids)).delete(synchronize_session=False)

            user_ids = [u.id for u in [admin, student_a, student_b, lecturer_a, lecturer_b, disabled_user] if u is not None]
            if user_ids:
                db.query(User).filter(User.id.in_(user_ids)).delete(synchronize_session=False)

            db.commit()
            print("[CLEANUP] Cleaned up all test records.")

        except Exception as e:
            print(f"[CLEANUP ERROR] {e}")
        finally:
            db.close()


if __name__ == "__main__":
    run_i4_security_audit_suite()
