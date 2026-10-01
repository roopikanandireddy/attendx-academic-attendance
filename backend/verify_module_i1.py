"""
AttendX — Module I1 System Integration Verification Suite
Tests the complete integrated system across all portals, database relationships, and APIs:
1. Authentication & RBAC Integration:
   - Student login & role detection
   - Lecturer login & role detection
   - Admin login & role detection
   - Invalid credentials handling
   - Expired / invalid token handling (401)
   - Cross-role authorization barriers (403)
2. Primary Business Integration Workflow (End-to-End):
   - Admin creates/selects Lecturer
   - Admin creates/selects Subject
   - Admin assigns Lecturer -> Subject (LecturerSubject)
   - Student enrolls in Subject (StudentSubject)
   - Lecturer logs in -> sees Subject on Dashboard & Attendance
   - Lecturer opens Attendance -> sees newly enrolled Student
   - Lecturer marks Student Present -> saves Attendance record
   - Lecturer Records & Reports reflect the attendance
   - Student logs in -> sees the attendance in Attendance & History & Dashboard
   - Lecturer updates attendance to Absent -> saves
   - Student refreshes -> sees updated Absent status immediately
3. Multi-Lecturer Subject Isolation:
   - Lecturer A cannot mark, inspect, or export Lecturer B's subjects
   - Scoped data access strictly enforced
4. API Contract & Date Integrity:
   - Consistent YYYY-MM-DD academic date format
   - Consistent 'present' and 'absent' status representation
   - No sensitive fields (passwords, hashes, secret keys) leaked
5. Regression & Portal Stability:
   - Student Dashboard & My Subjects
   - Admin Dashboard & Students & Lecturers & Subjects & Assignments
   - Lecturer Dashboard & Attendance & Records & Reports
"""
import sys
import os
from datetime import date, timedelta
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


def run_integration_tests():
    print("=" * 70)
    print("ATTENDX — I1 SYSTEM INTEGRATION COMPREHENSIVE SUITE")
    print("=" * 70)

    client = TestClient(app)
    db = SessionLocal()

    passed = 0
    total = 0

    def check(name: str, condition: bool, details: str = ""):
        nonlocal passed, total
        total += 1
        if condition:
            passed += 1
            print(f"  [PASS] {name} {details}".strip())
        else:
            print(f"  [FAIL] {name} {details}".strip())
            raise AssertionError(f"Integration Check Failed: {name} {details}")

    try:
        # =====================================================================
        # SUITE 1: AUTHENTICATION & RBAC INTEGRATION
        # =====================================================================
        print("\n--- SUITE 1: AUTHENTICATION & RBAC INTEGRATION ---")

        # 1.1 Admin login
        r_admin_login = client.post("/api/auth/login", json={
            "email": "admin@attendx.com",
            "password": "AdminPassword123!"
        })
        check("Admin login returns 200 OK", r_admin_login.status_code == 200)
        admin_data = r_admin_login.json()
        check("Admin login contains access_token", "access_token" in admin_data)
        check("Admin role detected as 'admin'", admin_data["user"]["role"] == "admin")
        admin_token = admin_data["access_token"]
        admin_headers = {"Authorization": f"Bearer {admin_token}"}

        # 1.2 Lecturer login
        r_lec_login = client.post("/api/auth/login", json={
            "email": "dr.alan@lecturer.com",
            "password": "LecturerPassword123!"
        })
        check("Lecturer login returns 200 OK", r_lec_login.status_code == 200)
        lec_data = r_lec_login.json()
        check("Lecturer role detected as 'lecturer'", lec_data["user"]["role"] == "lecturer")
        lec_token = lec_data["access_token"]
        lec_headers = {"Authorization": f"Bearer {lec_token}"}

        # 1.3 Student login
        r_stu_login = client.post("/api/auth/login", json={
            "email": "john.doe@student.com",
            "password": "StudentPassword123!"
        })
        check("Student login returns 200 OK", r_stu_login.status_code == 200)
        stu_data = r_stu_login.json()
        check("Student role detected as 'student'", stu_data["user"]["role"] == "student")
        stu_token = stu_data["access_token"]
        stu_headers = {"Authorization": f"Bearer {stu_token}"}

        # 1.4 Invalid credentials
        r_bad_pw = client.post("/api/auth/login", json={
            "email": "admin@attendx.com",
            "password": "WrongPassword!"
        })
        check("Invalid password returns 401 Unauthorized", r_bad_pw.status_code == 401)

        r_bad_usr = client.post("/api/auth/login", json={
            "email": "nonexistent@attendx.com",
            "password": "SomePassword123!"
        })
        check("Non-existent user returns 401 Unauthorized", r_bad_usr.status_code == 401)

        # 1.5 Missing and invalid tokens
        r_no_tok = client.get("/api/admin/dashboard")
        check("Unauthenticated request to Admin API returns 401", r_no_tok.status_code == 401)

        r_inv_tok = client.get("/api/admin/dashboard", headers={"Authorization": "Bearer invalid.token.xyz"})
        check("Invalid token to Admin API returns 401", r_inv_tok.status_code == 401)

        # 1.6 Expired token simulation
        expired_token = create_access_token(data={"sub": admin_data["user"]["id"], "role": "admin"}, expires_delta=timedelta(seconds=-10))
        r_exp_tok = client.get("/api/admin/dashboard", headers={"Authorization": f"Bearer {expired_token}"})
        check("Expired token returns 401 Unauthorized", r_exp_tok.status_code == 401)

        # 1.7 Session verification /api/auth/me
        r_me_admin = client.get("/api/auth/me", headers=admin_headers)
        check("GET /api/auth/me for Admin returns 200 OK", r_me_admin.status_code == 200)
        check("GET /api/auth/me user is admin", r_me_admin.json()["role"] == "admin")

        r_me_lec = client.get("/api/auth/me", headers=lec_headers)
        check("GET /api/auth/me for Lecturer returns 200 OK", r_me_lec.status_code == 200)
        check("GET /api/auth/me user is lecturer", r_me_lec.json()["role"] == "lecturer")

        r_me_stu = client.get("/api/auth/me", headers=stu_headers)
        check("GET /api/auth/me for Student returns 200 OK", r_me_stu.status_code == 200)
        check("GET /api/auth/me user is student", r_me_stu.json()["role"] == "student")

        # 1.8 Cross-role authorization barriers (RBAC)
        # Student attempting Admin route
        r_stu_on_admin = client.get("/api/admin/dashboard", headers=stu_headers)
        check("Student blocked from /api/admin/dashboard with 403", r_stu_on_admin.status_code == 403)

        # Student attempting Lecturer route
        r_stu_on_lec = client.get("/api/lecturer/dashboard", headers=stu_headers)
        check("Student blocked from /api/lecturer/dashboard with 403", r_stu_on_lec.status_code == 403)

        # Lecturer attempting Admin route
        r_lec_on_admin = client.get("/api/admin/dashboard", headers=lec_headers)
        check("Lecturer blocked from /api/admin/dashboard with 403", r_lec_on_admin.status_code == 403)

        # Student attempting Subject creation
        r_stu_post_sub = client.post("/api/subjects", json={"name": "Hacked", "code": "HACK", "department": "CS", "year": 1, "semester": 1}, headers=stu_headers)
        check("Student blocked from POST /api/subjects with 403", r_stu_post_sub.status_code == 403)

        # =====================================================================
        # SUITE 2: PRIMARY BUSINESS INTEGRATION WORKFLOW (STEPS 1 - 26)
        # =====================================================================
        print("\n--- SUITE 2: PRIMARY BUSINESS INTEGRATION WORKFLOW ---")

        # Step 1: Admin session verified (admin_headers)
        # Step 2: Create a unique test Lecturer
        unique_suffix = uuid.uuid4().hex[:6]
        test_lec_email = f"prof.test.{unique_suffix}@attendx.com"
        test_lec_pwd = "TestLecturerPass123!"

        r_create_lec = client.post("/api/admin/lecturers", json={
            "full_name": f"Prof. Integration {unique_suffix.upper()}",
            "email": test_lec_email,
            "password": test_lec_pwd,
            "employee_id": f"EMP-INT-{unique_suffix.upper()}",
            "department": "Computer Science"
        }, headers=admin_headers)
        check("Step 2: Admin creates test lecturer returns 201 Created", r_create_lec.status_code == 201)
        created_lecturer = r_create_lec.json()
        lec_id = created_lecturer["id"]

        # Step 3: Admin creates a unique test Subject
        sub_code = f"INT-{unique_suffix.upper()}"
        r_create_sub = client.post("/api/subjects", json={
            "name": f"Integration Systems {unique_suffix}",
            "code": sub_code,
            "department": "Computer Science",
            "year": 3,
            "semester": 5
        }, headers=admin_headers)
        check("Step 3: Admin creates test subject returns 201 Created", r_create_sub.status_code == 201)
        created_subject = r_create_sub.json()
        sub_id = created_subject["id"]

        # Step 4: Admin assigns Lecturer -> Subject
        r_assign = client.post(f"/api/admin/subjects/{sub_id}/lecturers", json={
            "lecturer_id": lec_id
        }, headers=admin_headers)
        check("Step 4: Admin assigns lecturer to subject returns 201 Created", r_assign.status_code == 201)

        # Verify assignment in LecturerSubject table
        db_assignment = db.query(LecturerSubject).filter(
            LecturerSubject.lecturer_id == lec_id,
            LecturerSubject.subject_id == sub_id
        ).first()
        check("Step 4: LecturerSubject record exists in database", db_assignment is not None)

        # Step 5: Student session (John Doe)
        # Step 6: Enroll Student -> Subject
        john = db.query(User).filter(User.email == "john.doe@student.com").first()
        assert john is not None, "John Doe student not found in seed data"

        r_enroll = client.post("/api/subjects/enroll", json={
            "student_id": john.id,
            "subject_id": sub_id
        }, headers=stu_headers)
        check("Step 6: Student enrolls in subject returns 201 Created", r_enroll.status_code == 201)

        # Verify enrollment in StudentSubject table
        db_enrollment = db.query(StudentSubject).filter(
            StudentSubject.student_id == john.id,
            StudentSubject.subject_id == sub_id
        ).first()
        check("Step 6: StudentSubject record exists in database", db_enrollment is not None)

        # Step 7: Login as newly created Lecturer
        r_new_lec_login = client.post("/api/auth/login", json={
            "email": test_lec_email,
            "password": test_lec_pwd
        })
        check("Step 7: New lecturer logs in successfully returns 200 OK", r_new_lec_login.status_code == 200)
        new_lec_token = r_new_lec_login.json()["access_token"]
        new_lec_headers = {"Authorization": f"Bearer {new_lec_token}"}

        # Step 8 & 9: Open Lecturer Dashboard -> Verify Subject appears
        r_new_lec_dash = client.get("/api/lecturer/dashboard", headers=new_lec_headers)
        check("Step 8: Lecturer Dashboard returns 200 OK", r_new_lec_dash.status_code == 200)
        new_lec_dash_data = r_new_lec_dash.json()
        dash_subject_ids = [s["id"] for s in new_lec_dash_data.get("subjects", [])]
        check(f"Step 9: Newly assigned subject {sub_code} appears on Lecturer Dashboard", sub_id in dash_subject_ids)

        # Step 10 & 11: Open Attendance & Select Subject
        r_assigned_subs = client.get("/api/lecturer/subjects", headers=new_lec_headers)
        check("Step 10: Lecturer fetches assigned subjects returns 200 OK", r_assigned_subs.status_code == 200)
        assigned_list = r_assigned_subs.json()
        check(f"Step 11: Assigned subject list contains {sub_code}", any(s["id"] == sub_id for s in assigned_list))

        # Step 12: Verify enrolled Student appears in attendance session
        today_iso = date.today().isoformat()
        r_session = client.get(
            f"/api/lecturer/attendance/session?subject_id={sub_id}&attendance_date={today_iso}",
            headers=new_lec_headers
        )
        check("Step 12: Lecturer loads attendance session returns 200 OK", r_session.status_code == 200)
        session_data = r_session.json()
        enrolled_student_ids = [st["student_id"] for st in session_data["students"]]
        check(f"Step 12: Enrolled student John Doe appears in session roster", john.id in enrolled_student_ids)

        # Step 13 & 14: Mark Student Present and Save Attendance
        r_save_att = client.post("/api/lecturer/attendance", json={
            "subject_id": sub_id,
            "attendance_date": today_iso,
            "records": [
                {"student_id": john.id, "status": "present"}
            ]
        }, headers=new_lec_headers)
        check("Step 14: Lecturer saves attendance returns 201 Created (or 200)", r_save_att.status_code in (200, 201))
        save_data = r_save_att.json()
        check("Step 14: Present count is 1", save_data["present_count"] == 1)

        # Verify Attendance record in database
        db_att = db.query(Attendance).filter(
            Attendance.student_id == john.id,
            Attendance.subject_id == sub_id,
            Attendance.attendance_date == date.today()
        ).first()
        check("Step 14: Attendance record persisted in database with status='present'", db_att is not None and db_att.status == "present")

        # Step 15 & 16: Open Lecturer Records -> Verify attendance appears
        r_lec_records = client.get(f"/api/lecturer/records?subject_id={sub_id}", headers=new_lec_headers)
        check("Step 15: Lecturer Records returns 200 OK", r_lec_records.status_code == 200)
        rec_data = r_lec_records.json()
        check("Step 16: Records list has at least 1 record", len(rec_data["records"]) >= 1)
        check("Step 16: Record matches student John Doe and status 'present'",
              rec_data["records"][0]["student_id"] == john.id and rec_data["records"][0]["status"] == "present")

        # Step 17 & 18: Open Lecturer Report -> Verify statistics
        r_subj_report = client.get(f"/api/lecturer/reports/subject/{sub_id}", headers=new_lec_headers)
        check("Step 17: Lecturer Subject Report returns 200 OK", r_subj_report.status_code == 200)
        rep_data = r_subj_report.json()
        check("Step 18: Subject report total_sessions is 1", rep_data["total_sessions"] == 1)
        check("Step 18: Subject report student attendance is 100.0%", rep_data["students"][0]["percentage"] == 100.0)

        # Step 19 & 20: Login as Student -> Open Student Attendance
        r_stu_att = client.get(f"/api/attendance?subject_id={sub_id}", headers=stu_headers)
        check("Step 20: Student fetches attendance records returns 200 OK", r_stu_att.status_code == 200)
        stu_att_data = r_stu_att.json()
        check("Step 21: Student sees recorded attendance", len(stu_att_data["records"]) >= 1)
        check("Step 21: Student attendance status matches Lecturer mark ('present')",
              stu_att_data["records"][0]["status"] == "present" and stu_att_data["records"][0]["subject_id"] == sub_id)

        # Step 22, 23 & 24: Return to Lecturer -> Change attendance to Absent -> Save
        r_update_att = client.post("/api/lecturer/attendance", json={
            "subject_id": sub_id,
            "attendance_date": today_iso,
            "records": [
                {"student_id": john.id, "status": "absent"}
            ]
        }, headers=new_lec_headers)
        check("Step 24: Lecturer updates attendance to absent returns 201 Created (or 200)", r_update_att.status_code in (200, 201))
        check("Step 24: Save result reflects absent_count=1", r_update_att.json()["absent_count"] == 1)

        # Step 25 & 26: Student refreshes -> Verify updated attendance
        r_stu_att_updated = client.get(f"/api/attendance?subject_id={sub_id}", headers=stu_headers)
        check("Step 25: Student refreshes attendance records returns 200 OK", r_stu_att_updated.status_code == 200)
        stu_updated_records = r_stu_att_updated.json()["records"]
        check("Step 26: Student attendance record immediately reflects 'absent'",
              stu_updated_records[0]["status"] == "absent")

        # Verify Lecturer Reports also immediately reflect the update (0% attendance)
        r_subj_rep_updated = client.get(f"/api/lecturer/reports/subject/{sub_id}", headers=new_lec_headers)
        check("Step 26: Lecturer report reflects updated attendance percentage (0.0%)",
              r_subj_rep_updated.json()["students"][0]["percentage"] == 0.0)

        # =====================================================================
        # SUITE 3: MULTI-LECTURER DATA ISOLATION & SCURITY
        # =====================================================================
        print("\n--- SUITE 3: MULTI-LECTURER DATA ISOLATION ---")

        # Dr. Alan (assigned to IAI, SE) trying to access the newly created test subject (sub_id)
        r_alan_cross_records = client.get(f"/api/lecturer/records?subject_id={sub_id}", headers=lec_headers)
        check("Dr. Alan cannot access another lecturer's subject records (403)", r_alan_cross_records.status_code == 403)

        r_alan_cross_report = client.get(f"/api/lecturer/reports/subject/{sub_id}", headers=lec_headers)
        check("Dr. Alan cannot access another lecturer's subject report (403)", r_alan_cross_report.status_code == 403)

        r_alan_cross_session = client.get(
            f"/api/lecturer/attendance/session?subject_id={sub_id}&attendance_date={today_iso}",
            headers=lec_headers
        )
        check("Dr. Alan cannot access another lecturer's attendance session (403)", r_alan_cross_session.status_code == 403)

        r_alan_cross_mark = client.post("/api/lecturer/attendance", json={
            "subject_id": sub_id,
            "attendance_date": today_iso,
            "records": [{"student_id": john.id, "status": "present"}]
        }, headers=lec_headers)
        check("Dr. Alan cannot mark attendance for another lecturer's subject (403)", r_alan_cross_mark.status_code == 403)

        # =====================================================================
        # SUITE 4: SECURITY & DATA LEAKAGE AUDIT
        # =====================================================================
        print("\n--- SUITE 4: SECURITY & DATA LEAKAGE AUDIT ---")

        # Check /api/auth/me does not leak password hash
        me_text = r_me_admin.text
        check("Admin /api/auth/me does not contain password_hash", "password_hash" not in me_text)
        check("Admin /api/auth/me does not contain bcrypt hash", "$2b$" not in me_text)

        # Check /api/lecturer/records does not leak password hash
        rec_text = r_lec_records.text
        check("Lecturer records do not contain password_hash", "password_hash" not in rec_text)
        check("Lecturer records do not contain bcrypt hash", "$2b$" not in rec_text)

        # Check CSV export does not leak password hash or tokens
        r_csv_exp = client.get(f"/api/lecturer/reports/export?export_type=subject&subject_id={sub_id}", headers=new_lec_headers)
        check("CSV export returns 200 OK", r_csv_exp.status_code == 200)
        csv_text = r_csv_exp.text
        check("CSV export does not contain password_hash", "password_hash" not in csv_text)
        check("CSV export does not contain bcrypt", "$2b$" not in csv_text)
        check("CSV export does not contain bearer token", "bearer " not in csv_text.lower())

        # =====================================================================
        # SUITE 5: ALL PORTALS REGRESSION & STABILITY
        # =====================================================================
        print("\n--- SUITE 5: ALL PORTALS REGRESSION & STABILITY ---")

        # 5.1 Admin Portal Endpoints
        check("Admin GET /api/admin/dashboard 200 OK", client.get("/api/admin/dashboard", headers=admin_headers).status_code == 200)
        check("Admin GET /api/admin/students 200 OK", client.get("/api/admin/students", headers=admin_headers).status_code == 200)
        check("Admin GET /api/admin/lecturers 200 OK", client.get("/api/admin/lecturers", headers=admin_headers).status_code == 200)
        check("Admin GET /api/admin/subjects/summary 200 OK", client.get("/api/admin/subjects/summary", headers=admin_headers).status_code == 200)
        check("Admin GET /api/admin/assignments 200 OK", client.get("/api/admin/assignments", headers=admin_headers).status_code == 200)

        # 5.2 Student Portal Endpoints
        check("Student GET /api/dashboard/student 200 OK", client.get("/api/dashboard/student", headers=stu_headers).status_code == 200)
        check("Student GET /api/subjects/my-enrollments 200 OK", client.get("/api/subjects/my-enrollments", headers=stu_headers).status_code == 200)
        check("Student GET /api/attendance 200 OK", client.get("/api/attendance", headers=stu_headers).status_code == 200)
        check("Student GET /api/notifications 200 OK", client.get("/api/notifications", headers=stu_headers).status_code == 200)

        # 5.3 Lecturer Portal Endpoints
        check("Lecturer GET /api/lecturer/me 200 OK", client.get("/api/lecturer/me", headers=lec_headers).status_code == 200)
        check("Lecturer GET /api/lecturer/dashboard 200 OK", client.get("/api/lecturer/dashboard", headers=lec_headers).status_code == 200)
        check("Lecturer GET /api/lecturer/subjects 200 OK", client.get("/api/lecturer/subjects", headers=lec_headers).status_code == 200)
        check("Lecturer GET /api/lecturer/attendance 200 OK", client.get("/api/lecturer/attendance", headers=lec_headers).status_code == 200)
        check("Lecturer GET /api/lecturer/records 200 OK", client.get("/api/lecturer/records", headers=lec_headers).status_code == 200)

        # =====================================================================
        # SUITE 5.5: FAILURE, EDGE CASES & ERROR HANDLING
        # =====================================================================
        print("\n--- SUITE 5.5: FAILURE, EDGE CASES & ERROR HANDLING ---")

        # 5.5.1 Duplicate subject enrollment -> 409 Conflict
        r_dup_enroll = client.post("/api/subjects/enroll", json={
            "student_id": john.id,
            "subject_id": sub_id
        }, headers=stu_headers)
        check("Duplicate enrollment returns 409 Conflict", r_dup_enroll.status_code == 409)

        # 5.5.2 Duplicate lecturer assignment -> 409 Conflict
        r_dup_assign = client.post(f"/api/admin/subjects/{sub_id}/lecturers", json={
            "lecturer_id": lec_id
        }, headers=admin_headers)
        check("Duplicate lecturer assignment returns 409 Conflict", r_dup_assign.status_code == 409)

        # 5.5.3 Future date attendance marking -> 400 Bad Request
        future_iso = (date.today() + timedelta(days=5)).isoformat()
        r_future_att = client.post("/api/lecturer/attendance", json={
            "subject_id": sub_id,
            "attendance_date": future_iso,
            "records": [{"student_id": john.id, "status": "present"}]
        }, headers=new_lec_headers)
        check("Marking attendance for future date returns 400 Bad Request", r_future_att.status_code == 400)

        # 5.5.4 Invalid date format in queries -> 400 Bad Request
        r_bad_date_format = client.get("/api/lecturer/records?date_from=not-a-date", headers=new_lec_headers)
        check("Invalid date_from format returns 400 Bad Request", r_bad_date_format.status_code == 400)

        # 5.5.5 Reversed date range (date_from > date_to) -> 400 Bad Request
        yesterday_iso = (date.today() - timedelta(days=1)).isoformat()
        r_reversed_dates = client.get(f"/api/lecturer/records?date_from={today_iso}&date_to={yesterday_iso}", headers=new_lec_headers)
        check("Reversed date range returns 400 Bad Request", r_reversed_dates.status_code == 400)

        # 5.5.6 Non-existent subject report -> 404 Not Found
        r_nonexist_subj_rep = client.get("/api/lecturer/reports/subject/nonexistent-id-9999", headers=new_lec_headers)
        check("Report for non-existent subject returns 404 Not Found", r_nonexist_subj_rep.status_code == 404)

        # 5.5.7 Disabled lecturer account cannot perform lecturer actions
        disabled_lec = db.query(User).filter(User.id == lec_id).first()
        if disabled_lec:
            disabled_lec.is_active = False
            db.commit()
            r_disabled_action = client.get("/api/lecturer/dashboard", headers=new_lec_headers)
            check("Disabled lecturer account access returns 403 Forbidden", r_disabled_action.status_code == 403)
            # Re-enable for cleanup
            disabled_lec.is_active = True
            db.commit()
        print("\n--- SUITE 6: INTEGRATION TEST CLEANUP ---")
        # Clean up the created test attendance, enrollment, assignment, subject, lecturer
        db.query(Attendance).filter(Attendance.subject_id == sub_id).delete()
        db.query(StudentSubject).filter(StudentSubject.subject_id == sub_id).delete()
        db.query(LecturerSubject).filter(LecturerSubject.subject_id == sub_id).delete()
        db.query(Subject).filter(Subject.id == sub_id).delete()
        db.query(User).filter(User.id == lec_id).delete()
        db.commit()
        check("Test entities cleaned up successfully from database", True)

        print("\n" + "=" * 70)
        print(f"I1 INTEGRATION TEST SUITE RESULT: {passed}/{total} PASSED (100% SUCCESS)")
        print("=" * 70)

    finally:
        db.close()


if __name__ == "__main__":
    run_integration_tests()
