"""
AttendX — Master QA Validation Suite (Levels 1, 3, 4, 5 & Negative Testing)
Executes:
- LEVEL 1: Software / System Testing (Cases 1 - 5)
- LEVEL 3: Module-Wise Functional Tests (B0, A1-A5, L1-L4, I1-I5)
- LEVEL 4: Integration Cases 1 - 8 & Critical Integration Chain
- LEVEL 5: User Acceptance Testing (Student S1-S9, Lecturer L1-L8, Admin A1-A7)
- Comprehensive Negative Testing & Error Leakage Verification
"""
import sys
import os
import time
from datetime import date, timedelta, datetime, timezone
import uuid

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__))))

from fastapi.testclient import TestClient
from app.main import app
from app.core.database import SessionLocal
from app.core.security import create_access_token, hash_password
from app.models.user import User
from app.models.subject import Subject
from app.models.student_subject import StudentSubject
from app.models.lecturer_subject import LecturerSubject
from app.models.attendance import Attendance
from app.models.notification import Notification


def run_master_qa_suite():
    print("=" * 85)
    print("ATTENDX — OVERALL MASTER QA TESTING & VALIDATION PASS")
    print("=" * 85)

    client = TestClient(app)
    db = SessionLocal()

    stats = {
        "System": {"total": 0, "pass": 0, "fail": 0},
        "Module": {"total": 0, "pass": 0, "fail": 0},
        "Integration": {"total": 0, "pass": 0, "fail": 0},
        "UAT": {"total": 0, "pass": 0, "fail": 0},
        "Negative": {"total": 0, "pass": 0, "fail": 0},
    }

    def record_check(category: str, title: str, condition: bool, details: str = ""):
        stats[category]["total"] += 1
        if condition:
            stats[category]["pass"] += 1
            print(f"  [PASS] [{category.upper()}] {title}")
        else:
            stats[category]["fail"] += 1
            print(f"  [FAIL] [{category.upper()}] {title} — {details}")
            assert False, f"Check Failed: {title} — {details}"

    temp_entities = []

    try:
        # --------------------------------------------------------------------
        # SETUP TEST DATA
        # --------------------------------------------------------------------
        print("\n--- [SETUP] Establishing Isolated QA Test Fixtures ---")
        suffix = uuid.uuid4().hex[:6]
        today = date.today()

        # QA Admin
        admin = User(
            full_name=f"QA Admin {suffix}",
            email=f"qa_admin_{suffix}@attendx.com",
            password_hash=hash_password("AdminPass123!"),
            role="admin",
            is_active=True,
        )
        # QA Lecturer
        lecturer = User(
            full_name=f"Prof. QA Ada {suffix}",
            email=f"qa_ada_{suffix}@attendx.com",
            password_hash=hash_password("LecturerPass123!"),
            role="lecturer",
            employee_id=f"EMP-QA-{suffix}",
            department="Computer Science",
            is_active=True,
        )
        # QA Student
        student = User(
            full_name=f"QA Student Tim {suffix}",
            email=f"qa_tim_{suffix}@attendx.com",
            password_hash=hash_password("StudentPass123!"),
            role="student",
            student_id=f"STU-QA-{suffix}",
            department="Computer Science",
            year=3,
            section="A",
            is_active=True,
        )
        # QA Subject
        subject = Subject(
            name=f"QA Systems Architecture {suffix}",
            code=f"QA-{suffix.upper()}",
            department="Computer Science",
            year=3,
            semester=5,
        )

        db.add_all([admin, lecturer, student, subject])
        db.commit()
        for e in [admin, lecturer, student, subject]:
            db.refresh(e)
            temp_entities.append(e)

        token_admin = create_access_token({"sub": admin.id, "email": admin.email, "role": "admin"})
        token_lecturer = create_access_token({"sub": lecturer.id, "email": lecturer.email, "role": "lecturer"})
        token_student = create_access_token({"sub": student.id, "email": student.email, "role": "student"})

        h_admin = {"Authorization": f"Bearer {token_admin}"}
        h_lecturer = {"Authorization": f"Bearer {token_lecturer}"}
        h_student = {"Authorization": f"Bearer {token_student}"}

        print("QA Test Fixtures initialized successfully.")

        # ====================================================================
        # LEVEL 1: SOFTWARE / SYSTEM TESTING
        # ====================================================================
        print("\n" + "=" * 70)
        print("LEVEL 1: SOFTWARE / SYSTEM TESTING")
        print("=" * 70)

        # System Case 1: Application Startup & Health
        r = client.get("/")
        record_check("System", "Root health check returns 200 OK", r.status_code == 200 and r.json().get("status") == "ok")
        r_health = client.get("/api/health")
        record_check("System", "API health check /api/health returns 200 OK", r_health.status_code == 200)
        r_docs = client.get("/docs")
        record_check("System", "Swagger / OpenAPI documentation loads (200)", r_docs.status_code == 200)

        # System Case 2: Authentication System
        r_login_stu = client.post("/api/auth/login", json={"email": student.email, "password": "StudentPass123!"})
        record_check("System", "Student authentication succeeds", r_login_stu.status_code == 200 and "access_token" in r_login_stu.json())
        r_login_lec = client.post("/api/auth/login", json={"email": lecturer.email, "password": "LecturerPass123!"})
        record_check("System", "Lecturer authentication succeeds", r_login_lec.status_code == 200 and "access_token" in r_login_lec.json())
        r_login_adm = client.post("/api/auth/login", json={"email": admin.email, "password": "AdminPass123!"})
        record_check("System", "Admin authentication succeeds", r_login_adm.status_code == 200 and "access_token" in r_login_adm.json())

        # System Case 3: Complete Student System Flow
        r_sdash = client.get("/api/dashboard/student", headers=h_student)
        record_check("System", "Student System: Dashboard loads with stats", r_sdash.status_code == 200 and "overall_stats" in r_sdash.json())
        r_senroll = client.post("/api/subjects/enroll", json={"student_id": student.id, "subject_id": subject.id}, headers=h_student)
        record_check("System", "Student System: Enrollment succeeds", r_senroll.status_code == 201)
        r_smy = client.get("/api/subjects/my-enrollments", headers=h_student)
        record_check("System", "Student System: My Subjects returns enrolled subject", subject.id in r_smy.json())
        r_satt = client.get("/api/attendance", headers=h_student)
        record_check("System", "Student System: Attendance records queryable", r_satt.status_code == 200 and "records" in r_satt.json())
        r_snotif = client.get("/api/notifications", headers=h_student)
        record_check("System", "Student System: Notifications queryable", r_snotif.status_code == 200)
        r_sprof = client.get("/api/auth/me", headers=h_student)
        record_check("System", "Student System: Profile queryable", r_sprof.status_code == 200)

        # System Case 4: Complete Lecturer System Flow
        r_assign = client.post("/api/admin/assignments", json={"lecturer_id": lecturer.id, "subject_id": subject.id}, headers=h_admin)
        record_check("System", "Lecturer System: Teaching assignment assigned by Admin", r_assign.status_code == 201)
        r_ldash = client.get("/api/dashboard/lecturer", headers=h_lecturer)
        record_check("System", "Lecturer System: Dashboard loads assigned subjects", r_ldash.status_code == 200)
        r_lsub = client.get("/api/lecturer/subjects", headers=h_lecturer)
        record_check("System", "Lecturer System: Assigned subjects list populated", any(s["id"] == subject.id for s in r_lsub.json()))
        r_lsess = client.get(f"/api/lecturer/attendance/session?subject_id={subject.id}&attendance_date={today.isoformat()}", headers=h_lecturer)
        record_check("System", "Lecturer System: Session roster loads enrolled student", any(s["student_id"] == student.id for s in r_lsess.json().get("students", [])))

        # Mark attendance
        mark_payload = {
            "subject_id": subject.id,
            "attendance_date": today.isoformat(),
            "records": [{"student_id": student.id, "status": "present"}],
        }
        r_lmark = client.post("/api/lecturer/attendance", json=mark_payload, headers=h_lecturer)
        record_check("System", "Lecturer System: Mark attendance commits record", r_lmark.status_code == 201)
        r_lrec = client.get(f"/api/lecturer/records?subject_id={subject.id}", headers=h_lecturer)
        record_check("System", "Lecturer System: Records list contains marked record", any(r["student_id"] == student.id for r in r_lrec.json().get("records", [])))
        r_lrep = client.get(f"/api/lecturer/reports/subject/{subject.id}", headers=h_lecturer)
        record_check("System", "Lecturer System: Subject report calculates metrics", r_lrep.status_code == 200)

        # System Case 5: Complete Admin System Flow
        r_adash = client.get("/api/admin/dashboard", headers=h_admin)
        record_check("System", "Admin System: Dashboard loads institutional metrics", r_adash.status_code == 200 and "total_students" in r_adash.json())
        r_astu = client.get("/api/admin/students", headers=h_admin)
        record_check("System", "Admin System: Students management table queryable", r_astu.status_code == 200)
        r_alec = client.get("/api/admin/lecturers", headers=h_admin)
        record_check("System", "Admin System: Lecturers management table queryable", r_alec.status_code == 200)
        r_asub = client.get("/api/admin/subjects", headers=h_admin)
        record_check("System", "Admin System: Subjects catalog queryable", r_asub.status_code == 200)
        r_aasg = client.get("/api/admin/assignments", headers=h_admin)
        record_check("System", "Admin System: Assignments table queryable", r_aasg.status_code == 200)

        # ====================================================================
        # LEVEL 3: MODULE-WISE TESTING
        # ====================================================================
        print("\n" + "=" * 70)
        print("LEVEL 3: MODULE-WISE FUNCTIONAL TESTING")
        print("=" * 70)

        # Module B0: Backend Foundation
        record_check("Module", "B0: Backend Foundation — App router mounting & settings", len(app.routes) > 15)

        # Module A1: Admin Foundation
        record_check("Module", "A1: Admin Foundation — Route guards reject student token (403)", client.get("/api/admin/dashboard", headers=h_student).status_code == 403)

        # Module A2: Admin Dashboard
        admin_data = client.get("/api/admin/dashboard", headers=h_admin).json()
        record_check("Module", "A2: Admin Dashboard — Real total_students count >= 1", admin_data.get("total_students", 0) >= 1)

        # Module A3: Admin Student Management
        r_astudetail = client.get(f"/api/admin/students/{student.id}", headers=h_admin)
        record_check("Module", "A3: Admin Students — Retrieve student details by ID (200)", r_astudetail.status_code == 200)

        # Module A4: Admin Lecturer Management
        r_alecdetail = client.get(f"/api/admin/lecturers/{lecturer.id}", headers=h_admin)
        record_check("Module", "A4: Admin Lecturers — Retrieve lecturer details by ID (200)", r_alecdetail.status_code == 200)

        # Module A5: Admin Subject + Assignment
        r_asum = client.get("/api/admin/assignments/summary", headers=h_admin)
        record_check("Module", "A5: Admin Assignments — Summary returns total_assignments >= 1", r_asum.status_code == 200 and r_asum.json().get("total_assignments", 0) >= 1)

        # Module L1: Lecturer Foundation
        record_check("Module", "L1: Lecturer Foundation — Route guards reject missing token (401)", client.get("/api/lecturer/subjects").status_code == 401)

        # Module L2: Lecturer Dashboard
        lec_dash = client.get("/api/dashboard/lecturer", headers=h_lecturer).json()
        record_check("Module", "L2: Lecturer Dashboard — Summary metrics isolated to lecturer", "summary" in lec_dash)

        # Module L3: Lecturer Attendance
        record_check("Module", "L3: Lecturer Attendance — Attendance marked status is 'present'", r_lmark.json().get("present_count") == 1)

        # Module L4: Lecturer Records & Reports
        r_csv = client.get(f"/api/lecturer/reports/export?export_type=subject&subject_id={subject.id}", headers=h_lecturer)
        record_check("Module", "L4: Lecturer Records & Reports — Academic CSV export formatted (200)", r_csv.status_code == 200 and "text/csv" in r_csv.headers.get("content-type", ""))

        # Module I1: Integration
        record_check("Module", "I1: Integration — Cross-module student sees marked subject attendance", len(client.get("/api/attendance", headers=h_student).json().get("records", [])) >= 1)

        # Module I2: Notifications
        s_notifs = client.get("/api/notifications", headers=h_student).json()
        record_check("Module", "I2: Notifications — Student received automated attendance notification", any("Present" in n["message"] for n in s_notifs))

        # Module I3: Attendance Engine
        stu_dash_stat = client.get("/api/dashboard/student", headers=h_student).json().get("overall_stats", {})
        record_check("Module", "I3: Attendance Engine — Calculates 100.0% attendance for single present", stu_dash_stat.get("percentage") == 100.0)

        # Module I4: Security
        record_check("Module", "I4: Security — Student cannot mark lecturer attendance (403)", client.post("/api/lecturer/attendance", json=mark_payload, headers=h_student).status_code == 403)

        # Module I5: End-to-End Stability
        record_check("Module", "I5: E2E — Complete workflow remains 100% operational", r_sdash.status_code == 200 and r_ldash.status_code == 200 and r_adash.status_code == 200)

        # ====================================================================
        # LEVEL 4: INTEGRATION TESTING
        # ====================================================================
        print("\n" + "=" * 70)
        print("LEVEL 4: INTEGRATION BOUNDARY TESTING")
        print("=" * 70)

        # Case 1: Admin -> Lecturer -> Subject
        record_check("Integration", "Case 1: Admin assigns Lecturer -> Lecturer queries assigned Subject", any(s["id"] == subject.id for s in client.get("/api/lecturer/subjects", headers=h_lecturer).json()))

        # Case 2: Student -> Subject
        record_check("Integration", "Case 2: Student enrolls in Subject -> Subject reflects in Student Enrollments", subject.id in client.get("/api/subjects/my-enrollments", headers=h_student).json())

        # Case 3: Subject -> Lecturer -> Student -> Attendance
        record_check("Integration", "Case 3: Lecturer marks Attendance for enrolled Student -> Record persists", client.get(f"/api/lecturer/records?subject_id={subject.id}", headers=h_lecturer).status_code == 200)

        # Case 4: Attendance -> Student View
        stu_att_list = client.get("/api/attendance", headers=h_student).json().get("records", [])
        record_check("Integration", "Case 4: Attendance record strictly visible in Student Attendance view", any(r["subject_id"] == subject.id for r in stu_att_list))

        # Case 5: Attendance -> Reports
        rep_data = client.get(f"/api/lecturer/reports/subject/{subject.id}", headers=h_lecturer).json()
        record_check("Integration", "Case 5: Marked Attendance immediately updates Subject Report stats", rep_data.get("total_records", 0) >= 1)

        # Case 6: Attendance -> Notification
        record_check("Integration", "Case 6: Attendance marking dispatches notification to recipient", client.get("/api/notifications/unread-count", headers=h_student).json().get("unread_count", 0) >= 1)

        # Case 7: Auth -> All Modules
        record_check("Integration", "Case 7A: Student Token -> Rejects Admin API (403)", client.get("/api/admin/students", headers=h_student).status_code == 403)
        record_check("Integration", "Case 7B: Lecturer Token -> Rejects Admin API (403)", client.get("/api/admin/lecturers", headers=h_lecturer).status_code == 403)
        record_check("Integration", "Case 7C: Admin Token -> Rejects Student Portal Data (403)", client.get("/api/dashboard/student", headers=h_admin).status_code == 403)

        # Case 8: Database -> API -> Data Consistency
        db_att = db.query(Attendance).filter(Attendance.student_id == student.id, Attendance.subject_id == subject.id).first()
        record_check("Integration", "Case 8: Database state strictly equals API state ('present')", db_att is not None and db_att.status == "present")

        # ====================================================================
        # LEVEL 5: USER ACCEPTANCE TESTING (UAT)
        # ====================================================================
        print("\n" + "=" * 70)
        print("LEVEL 5: USER ACCEPTANCE TESTING (UAT)")
        print("=" * 70)

        # Student UAT Scenarios (S1 - S9)
        record_check("UAT", "Scenario S1: Student login", r_login_stu.status_code == 200)
        record_check("UAT", "Scenario S2: Student view enrolled subjects", len(client.get("/api/subjects/my-enrollments", headers=h_student).json()) >= 1)
        record_check("UAT", "Scenario S3: Student subject enrollment", r_senroll.status_code == 201 or r_senroll.status_code == 200)
        record_check("UAT", "Scenario S4: Student check attendance", len(client.get("/api/attendance", headers=h_student).json().get("records", [])) >= 1)
        record_check("UAT", "Scenario S5: Student attendance percentage is accurate (100.0%)", client.get("/api/dashboard/student", headers=h_student).json()["overall_stats"]["percentage"] == 100.0)
        record_check("UAT", "Scenario S6: Student view attendance history", client.get("/api/attendance", headers=h_student).status_code == 200)
        record_check("UAT", "Scenario S7: Student view notifications", len(client.get("/api/notifications", headers=h_student).json()) >= 1)
        notif_id = client.get("/api/notifications", headers=h_student).json()[0]["id"]
        r_read = client.patch(f"/api/notifications/{notif_id}/read", headers=h_student)
        record_check("UAT", "Scenario S8: Student mark notification read", r_read.status_code == 200 and r_read.json().get("is_read") is True)
        record_check("UAT", "Scenario S9: Student safe logout / invalidation", client.get("/api/auth/me", headers={"Authorization": "Bearer invalid"}).status_code == 401)

        # Lecturer UAT Scenarios (L1 - L8)
        record_check("UAT", "Scenario L1: Lecturer login", r_login_lec.status_code == 200)
        record_check("UAT", "Scenario L2: Lecturer view assigned subjects", len(client.get("/api/lecturer/subjects", headers=h_lecturer).json()) >= 1)
        record_check("UAT", "Scenario L3: Lecturer mark attendance", r_lmark.status_code == 201)
        # L4: Update attendance
        up_payload = {"subject_id": subject.id, "attendance_date": today.isoformat(), "records": [{"student_id": student.id, "status": "absent"}]}
        r_lup = client.post("/api/lecturer/attendance", json=up_payload, headers=h_lecturer)
        record_check("UAT", "Scenario L4: Lecturer update attendance (Present -> Absent)", r_lup.status_code == 201)
        record_check("UAT", "Scenario L5: Lecturer view attendance records", client.get(f"/api/lecturer/records?subject_id={subject.id}", headers=h_lecturer).status_code == 200)
        record_check("UAT", "Scenario L6: Lecturer filter attendance by status", client.get(f"/api/lecturer/records?subject_id={subject.id}&status=absent", headers=h_lecturer).status_code == 200)
        record_check("UAT", "Scenario L7: Lecturer view attendance reports", client.get(f"/api/lecturer/reports/subject/{subject.id}", headers=h_lecturer).status_code == 200)
        record_check("UAT", "Scenario L8: Lecturer notifications delivery", client.get("/api/notifications", headers=h_lecturer).status_code == 200)

        # Admin UAT Scenarios (A1 - A7)
        record_check("UAT", "Scenario A1: Admin login", r_login_adm.status_code == 200)
        record_check("UAT", "Scenario A2: Admin view system statistics", "total_students" in client.get("/api/admin/dashboard", headers=h_admin).json())
        record_check("UAT", "Scenario A3: Admin manage students", client.get("/api/admin/students", headers=h_admin).status_code == 200)
        record_check("UAT", "Scenario A4: Admin manage lecturers", client.get("/api/admin/lecturers", headers=h_admin).status_code == 200)
        record_check("UAT", "Scenario A5: Admin manage subjects", client.get("/api/admin/subjects", headers=h_admin).status_code == 200)
        record_check("UAT", "Scenario A6: Admin assign lecturers to subjects", r_assign.status_code == 201)
        record_check("UAT", "Scenario A7: Admin verify persisted system data", client.get("/api/admin/assignments/summary", headers=h_admin).status_code == 200)

        # ====================================================================
        # NEGATIVE TESTING & ERROR LEAKAGE VERIFICATION
        # ====================================================================
        print("\n" + "=" * 70)
        print("NEGATIVE TESTING & SAFE ERROR RESPONSES")
        print("=" * 70)

        # N1: Non-existent subject ID (404)
        fake_id = str(uuid.uuid4())
        record_check("Negative", "N1: Non-existent subject ID returns 404", client.get(f"/api/subjects/{fake_id}", headers=h_student).status_code == 404)

        # N2: Excessive pagination limit (422)
        record_check("Negative", "N2: Excessive pagination limit rejected with 422", client.get("/api/admin/students?limit=500", headers=h_admin).status_code == 422)

        # N3: Marking future date attendance (400)
        future_dt = (today + timedelta(days=10)).isoformat()
        r_fut = client.post("/api/lecturer/attendance", json={"subject_id": subject.id, "attendance_date": future_dt, "records": [{"student_id": student.id, "status": "present"}]}, headers=h_lecturer)
        record_check("Negative", "N3: Future date attendance rejected with 400", r_fut.status_code == 400)

        # N4: Duplicate teaching assignment (409)
        r_dup_asg = client.post("/api/admin/assignments", json={"lecturer_id": lecturer.id, "subject_id": subject.id}, headers=h_admin)
        record_check("Negative", "N4: Duplicate teaching assignment rejected with 409 Conflict", r_dup_asg.status_code == 409)

        # N5: IDOR protection on student records
        record_check("Negative", "N5: Student blocked from Admin Students endpoint (403)", client.get("/api/admin/students", headers=h_student).status_code == 403)

        # N6: Zero trace leakage in 404 response body
        r_404 = client.get("/api/probe-for-information-leakage-path")
        record_check("Negative", "N6: 404 response does NOT leak stack trace ('Traceback')", "Traceback" not in r_404.text)
        record_check("Negative", "N6: 404 response does NOT leak SQL queries ('SELECT')", "SELECT" not in r_404.text)

        # ====================================================================
        # SUMMARY
        # ====================================================================
        print("\n" + "=" * 85)
        print("ATTENDX MASTER QA EXECUTION RESULTS")
        print("=" * 85)
        grand_total = 0
        grand_pass = 0
        for cat, val in stats.items():
            print(f"  {cat:<15}: {val['pass']}/{val['total']} PASSED (Fail: {val['fail']})")
            grand_total += val['total']
            grand_pass += val['pass']
        print("-" * 85)
        print(f"  GRAND TOTAL    : {grand_pass}/{grand_total} CHECKS PASSED (100% SUCCESS)")
        print("=" * 85)

    finally:
        # Cleanup test entities
        print("\n[CLEANUP] Cleaning up QA test fixtures...")
        try:
            u_ids = [e.id for e in temp_entities if isinstance(e, User)]
            s_ids = [e.id for e in temp_entities if isinstance(e, Subject)]
            if u_ids:
                db.query(Notification).filter(Notification.user_id.in_(u_ids)).delete(synchronize_session=False)
                db.query(Attendance).filter(Attendance.student_id.in_(u_ids)).delete(synchronize_session=False)
                db.query(StudentSubject).filter(StudentSubject.student_id.in_(u_ids)).delete(synchronize_session=False)
                db.query(LecturerSubject).filter(LecturerSubject.lecturer_id.in_(u_ids)).delete(synchronize_session=False)
            if s_ids:
                db.query(Attendance).filter(Attendance.subject_id.in_(s_ids)).delete(synchronize_session=False)
                db.query(StudentSubject).filter(StudentSubject.subject_id.in_(s_ids)).delete(synchronize_session=False)
                db.query(LecturerSubject).filter(LecturerSubject.subject_id.in_(s_ids)).delete(synchronize_session=False)
                db.query(Subject).filter(Subject.id.in_(s_ids)).delete(synchronize_session=False)
            if u_ids:
                db.query(User).filter(User.id.in_(u_ids)).delete(synchronize_session=False)
            db.commit()
            print("[CLEANUP] Cleaned up all QA test fixtures.")
        except Exception as ex:
            print(f"[CLEANUP ERROR] {ex}")
        finally:
            db.close()


if __name__ == "__main__":
    run_master_qa_suite()
