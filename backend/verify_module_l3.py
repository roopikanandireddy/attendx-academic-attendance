"""
AttendX — Module L3 Lecturer Attendance Comprehensive Verification
Tests all critical security, workflow, edge case, and regression scenarios:
1. Authentication & RBAC:
   - Valid lecturer token on GET /api/lecturer/subjects -> 200 OK
   - Valid lecturer token on GET /api/lecturer/attendance/session -> 200 OK
   - Valid lecturer token on POST /api/lecturer/attendance -> 201 Created
   - Student token on /api/lecturer/attendance -> 403 Forbidden
   - Admin token on /api/lecturer/attendance -> 403 Forbidden
   - No token / Invalid token on /api/lecturer/attendance -> 401 Unauthorized
2. Data Ownership & Isolation:
   - Lecturer A can ONLY mark attendance for subjects assigned to Lecturer A
   - Lecturer A attempting to view session for Lecturer B's subject -> 403 Forbidden
   - Lecturer A attempting to POST attendance for Lecturer B's subject -> 403 Forbidden
   - Lecturer B attempting to POST attendance for Lecturer A's subject -> 403 Forbidden
   - Lecturer B attempting to PUT / update an attendance record belonging to Lecturer A's subject -> 403 Forbidden
   - GET /api/lecturer/attendance only returns records for lecturer's assigned subjects
3. Attendance Workflow & Deduplication:
   - Mark attendance for multiple students (batch session submission)
   - Read back session details: reflects correct present/absent/unmarked tallies
   - Re-submitting for the same date updates in-place and prevents duplicates
   - Marking future dates rejected with 400 Bad Request
   - Single record PUT update works and updates status
4. Regression Tests:
   - Student Portal /api/dashboard/student -> 200 OK
   - Admin Portal /api/admin/dashboard -> 200 OK
   - Admin attendance POST /api/attendance still rejects lecturer -> 403 Forbidden
   - Lecturer L1 /api/lecturer/me -> 200 OK
   - Lecturer L2 /api/lecturer/dashboard -> 200 OK
"""
import sys
import os
from datetime import date, timedelta
import uuid

# Set up path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__))))

from fastapi.testclient import TestClient
from app.main import app
from app.core.database import SessionLocal
from app.core.security import create_access_token, hash_password
from app.models.user import User
from app.models.subject import Subject
from app.models.lecturer_subject import LecturerSubject
from app.models.student_subject import StudentSubject
from app.models.attendance import Attendance


def run_tests():
    print("=" * 65)
    print("STARTING ATTENDX MODULE L3 VERIFICATION")
    print("=" * 65)

    client = TestClient(app)
    db = SessionLocal()

    passed_count = 0
    total_count = 0

    def assert_test(name, condition, extra=""):
        nonlocal passed_count, total_count
        total_count += 1
        if condition:
            passed_count += 1
            print(f"  [PASS] {name} {extra}")
        else:
            print(f"  [FAIL] {name} {extra}")
            raise AssertionError(f"Test failed: {name} {extra}")

    try:
        # Step 0: Fetch or ensure test entities
        admin = db.query(User).filter(User.role == "admin").first()
        student = db.query(User).filter(User.role == "student").first()
        alan = db.query(User).filter(User.email == "dr.alan@lecturer.com").first()
        kath = db.query(User).filter(User.email == "katherine.johnson@attendx.com").first()

        assert_test("Database has admin account", admin is not None)
        assert_test("Database has student account", student is not None)
        assert_test("Database has Dr. Alan Turing account", alan is not None)
        assert_test("Database has Dr. Katherine Johnson account", kath is not None)

        iai = db.query(Subject).filter(Subject.code == "IAI").first()
        se = db.query(Subject).filter(Subject.code == "SE").first()
        isc = db.query(Subject).filter(Subject.code == "ISC").first()

        assert_test("Database has IAI subject", iai is not None)
        assert_test("Database has SE subject", se is not None)
        assert_test("Database has ISC subject", isc is not None)

        # Generate tokens
        alan_token = create_access_token(data={"sub": alan.id, "role": "lecturer"})
        kath_token = create_access_token(data={"sub": kath.id, "role": "lecturer"})
        admin_token = create_access_token(data={"sub": admin.id, "role": "admin"})
        student_token = create_access_token(data={"sub": student.id, "role": "student"})

        print("\n--- SUITE 1: AUTHENTICATION & RBAC ENFORCEMENT ---")

        # 1. No token on /api/lecturer/attendance -> 401
        r = client.get("/api/lecturer/attendance")
        assert_test("Missing token on GET /api/lecturer/attendance returns 401", r.status_code == 401)

        # 2. Invalid token on /api/lecturer/attendance -> 401
        r = client.get("/api/lecturer/attendance", headers={"Authorization": "Bearer invalid.jwt"})
        assert_test("Invalid token on GET /api/lecturer/attendance returns 401", r.status_code == 401)

        # 3. Student token on /api/lecturer/attendance -> 403
        r = client.get("/api/lecturer/attendance", headers={"Authorization": f"Bearer {student_token}"})
        assert_test("Student token on GET /api/lecturer/attendance returns 403 Forbidden", r.status_code == 403)

        # 4. Admin token on /api/lecturer/attendance -> 403
        r = client.get("/api/lecturer/attendance", headers={"Authorization": f"Bearer {admin_token}"})
        assert_test("Admin token on GET /api/lecturer/attendance returns 403 Forbidden", r.status_code == 403)

        # 5. Student token on POST /api/lecturer/attendance -> 403
        r = client.post("/api/lecturer/attendance", json={"subject_id": iai.id, "attendance_date": str(date.today()), "records": []}, headers={"Authorization": f"Bearer {student_token}"})
        assert_test("Student token on POST /api/lecturer/attendance returns 403 Forbidden", r.status_code == 403)

        # 6. Admin token on POST /api/lecturer/attendance -> 403
        r = client.post("/api/lecturer/attendance", json={"subject_id": iai.id, "attendance_date": str(date.today()), "records": []}, headers={"Authorization": f"Bearer {admin_token}"})
        assert_test("Admin token on POST /api/lecturer/attendance returns 403 Forbidden", r.status_code == 403)

        print("\n--- SUITE 2: DATA OWNERSHIP & SECURITY ISOLATION ---")

        # 7. GET /api/lecturer/subjects returns only assigned subjects
        r_alan_subs = client.get("/api/lecturer/subjects", headers={"Authorization": f"Bearer {alan_token}"})
        assert_test("Alan gets 200 OK on /api/lecturer/subjects", r_alan_subs.status_code == 200)
        alan_subs = [s["code"] for s in r_alan_subs.json()]
        assert_test("Alan's subjects include IAI and SE", "IAI" in alan_subs and "SE" in alan_subs)
        assert_test("Alan's subjects do NOT include ISC", "ISC" not in alan_subs)

        r_kath_subs = client.get("/api/lecturer/subjects", headers={"Authorization": f"Bearer {kath_token}"})
        kath_subs = [s["code"] for s in r_kath_subs.json()]
        assert_test("Katherine's subjects include ISC", "ISC" in kath_subs)
        assert_test("Katherine's subjects do NOT include IAI or SE", "IAI" not in kath_subs and "SE" not in kath_subs)

        # 8. Lecturer A accessing Lecturer B's subject students -> 403
        r_spoof_students = client.get(f"/api/lecturer/subjects/{isc.id}/students", headers={"Authorization": f"Bearer {alan_token}"})
        assert_test("Alan accessing Katherine's subject students returns 403 Forbidden", r_spoof_students.status_code == 403)

        # 9. Lecturer A accessing Lecturer B's attendance session -> 403
        r_spoof_session = client.get(
            f"/api/lecturer/attendance/session?subject_id={isc.id}&attendance_date={date.today().isoformat()}",
            headers={"Authorization": f"Bearer {alan_token}"}
        )
        assert_test("Alan accessing Katherine's session returns 403 Forbidden", r_spoof_session.status_code == 403)

        # 10. Lecturer A attempting to POST attendance for Lecturer B's subject -> 403
        r_spoof_post = client.post(
            "/api/lecturer/attendance",
            json={
                "subject_id": isc.id,
                "attendance_date": date.today().isoformat(),
                "records": [{"student_id": student.id, "status": "present"}],
            },
            headers={"Authorization": f"Bearer {alan_token}"}
        )
        assert_test("Alan marking attendance for Katherine's subject returns 403 Forbidden", r_spoof_post.status_code == 403)

        # 11. Lecturer B attempting to POST attendance for Lecturer A's subject -> 403
        r_kath_spoof = client.post(
            "/api/lecturer/attendance",
            json={
                "subject_id": iai.id,
                "attendance_date": date.today().isoformat(),
                "records": [{"student_id": student.id, "status": "present"}],
            },
            headers={"Authorization": f"Bearer {kath_token}"}
        )
        assert_test("Katherine marking attendance for Alan's subject returns 403 Forbidden", r_kath_spoof.status_code == 403)

        print("\n--- SUITE 3: ATTENDANCE WORKFLOW & DEDUPLICATION ---")

        # Get enrolled students in IAI
        r_iai_sess = client.get(
            f"/api/lecturer/attendance/session?subject_id={iai.id}&attendance_date={date.today().isoformat()}",
            headers={"Authorization": f"Bearer {alan_token}"}
        )
        assert_test("Alan successfully accesses own IAI session", r_iai_sess.status_code == 200)
        session_json = r_iai_sess.json()
        enrolled_students = session_json["students"]
        assert_test("IAI session has enrolled students", len(enrolled_students) > 0)

        # 12. Future date restriction
        tomorrow = (date.today() + timedelta(days=1)).isoformat()
        r_future = client.post(
            "/api/lecturer/attendance",
            json={
                "subject_id": iai.id,
                "attendance_date": tomorrow,
                "records": [{"student_id": enrolled_students[0]["student_id"], "status": "present"}],
            },
            headers={"Authorization": f"Bearer {alan_token}"}
        )
        assert_test("Future date attendance is rejected with 400 Bad Request", r_future.status_code == 400)

        # 13. Mark attendance session for today:
        # student 0: present, student 1: absent (if >=2 students)
        st0 = enrolled_students[0]["student_id"]
        records_to_submit = [{"student_id": st0, "status": "present"}]
        if len(enrolled_students) > 1:
            st1 = enrolled_students[1]["student_id"]
            records_to_submit.append({"student_id": st1, "status": "absent"})

        r_mark = client.post(
            "/api/lecturer/attendance",
            json={
                "subject_id": iai.id,
                "attendance_date": date.today().isoformat(),
                "records": records_to_submit,
            },
            headers={"Authorization": f"Bearer {alan_token}"}
        )
        assert_test("Alan marks attendance successfully -> 201 Created", r_mark.status_code == 201)
        mark_res = r_mark.json()
        assert_test("Mark result has present_count >= 1", mark_res["present_count"] >= 1)

        # 14. Verify session state updated
        r_session_after = client.get(
            f"/api/lecturer/attendance/session?subject_id={iai.id}&attendance_date={date.today().isoformat()}",
            headers={"Authorization": f"Bearer {alan_token}"}
        )
        assert_test("Session returns 200 OK after marking", r_session_after.status_code == 200)
        s_after = r_session_after.json()
        assert_test("Session has_existing_records is now True", s_after["has_existing_records"] is True)
        st_statuses = {s["student_id"]: s["status"] for s in s_after["students"]}
        assert_test("Session student 0 is marked present", st_statuses.get(st0) == "present")
        if len(enrolled_students) > 1:
            assert_test("Session student 1 is marked absent", st_statuses.get(st1) == "absent")

        # 15. In-Place Update (Deduplication Check):
        # Update st0 from present to absent on the same date
        r_update_session = client.post(
            "/api/lecturer/attendance",
            json={
                "subject_id": iai.id,
                "attendance_date": date.today().isoformat(),
                "records": [{"student_id": st0, "status": "absent"}],
            },
            headers={"Authorization": f"Bearer {alan_token}"}
        )
        assert_test("In-place update session returns 201 Created", r_update_session.status_code == 201)
        up_res = r_update_session.json()
        assert_test("updated_count is 1 (in-place update)", up_res["updated_count"] == 1)
        assert_test("created_count is 0 (no duplicate created)", up_res["created_count"] == 0)

        # Count records in database for st0, iai, today
        count_recs = db.query(Attendance).filter(
            Attendance.student_id == st0,
            Attendance.subject_id == iai.id,
            Attendance.attendance_date == date.today(),
        ).count()
        assert_test("Database contains exactly 1 record for this student/subject/date", count_recs == 1)

        # 16. Single record update via PUT /api/lecturer/attendance/{id}
        created_record = db.query(Attendance).filter(
            Attendance.student_id == st0,
            Attendance.subject_id == iai.id,
            Attendance.attendance_date == date.today(),
        ).first()

        # Katherine attempts to update Alan's attendance record -> 403 Forbidden
        r_kath_put_spoof = client.put(
            f"/api/lecturer/attendance/{created_record.id}",
            json={"status": "present"},
            headers={"Authorization": f"Bearer {kath_token}"}
        )
        assert_test("Katherine updating Alan's record is blocked with 403 Forbidden", r_kath_put_spoof.status_code == 403)

        # Alan updates his own record to present
        r_alan_put = client.put(
            f"/api/lecturer/attendance/{created_record.id}",
            json={"status": "present"},
            headers={"Authorization": f"Bearer {alan_token}"}
        )
        assert_test("Alan updates his record -> 200 OK", r_alan_put.status_code == 200)
        assert_test("Status changed back to present", r_alan_put.json()["status"] == "present")

        # 17. GET /api/lecturer/attendance list
        r_list = client.get("/api/lecturer/attendance", headers={"Authorization": f"Bearer {alan_token}"})
        assert_test("Alan lists attendance records -> 200 OK", r_list.status_code == 200)
        list_json = r_list.json()
        assert_test("Records returned > 0", len(list_json["records"]) > 0)
        for rec in list_json["records"]:
            assert_test(f"Attendance subject {rec['subject_code']} belongs to Alan's subjects", rec["subject_code"] in alan_subs)

        # Katherine's attendance list should not contain Alan's subjects
        r_kath_list = client.get("/api/lecturer/attendance", headers={"Authorization": f"Bearer {kath_token}"})
        kath_list_json = r_kath_list.json()
        for rec in kath_list_json["records"]:
            assert_test(f"Katherine attendance subject {rec['subject_code']} is ISC", rec["subject_code"] == "ISC")

        # Cleanup test records created for today
        db.query(Attendance).filter(Attendance.attendance_date == date.today()).delete()
        db.commit()

        print("\n--- SUITE 4: REGRESSION TESTING ---")

        # 18. Student Portal Dashboard
        r_stu_dash = client.get("/api/dashboard/student", headers={"Authorization": f"Bearer {student_token}"})
        assert_test("Student Portal dashboard returns 200 OK", r_stu_dash.status_code == 200)

        # 19. Admin Portal Dashboard
        r_adm_dash = client.get("/api/admin/dashboard", headers={"Authorization": f"Bearer {admin_token}"})
        assert_test("Admin Portal dashboard returns 200 OK", r_adm_dash.status_code == 200)

        # 20. Admin attendance marking POST /api/attendance rejects lecturer
        r_lec_on_admin_att = client.post(
            "/api/attendance",
            json={
                "subject_id": iai.id,
                "attendance_date": (date.today() - timedelta(days=1)).isoformat(),
                "records": [{"student_id": st0, "status": "present"}],
            },
            headers={"Authorization": f"Bearer {alan_token}"}
        )
        assert_test("Admin endpoint POST /api/attendance blocks lecturer with 403 Forbidden", r_lec_on_admin_att.status_code == 403)

        # 21. Lecturer L1 Foundation (/api/lecturer/me)
        r_l1 = client.get("/api/lecturer/me", headers={"Authorization": f"Bearer {alan_token}"})
        assert_test("Lecturer L1 /api/lecturer/me returns 200 OK", r_l1.status_code == 200)

        # 22. Lecturer L2 Dashboard (/api/lecturer/dashboard)
        r_l2 = client.get("/api/lecturer/dashboard", headers={"Authorization": f"Bearer {alan_token}"})
        assert_test("Lecturer L2 /api/lecturer/dashboard returns 200 OK", r_l2.status_code == 200)
        assert_test("L2 summary total_subjects is 2", r_l2.json()["summary"]["total_subjects"] == 2)

        print("\n" + "=" * 65)
        print(f"ALL TESTS PASSED: {passed_count}/{total_count}")
        print("MODULE L3 VERIFICATION COMPLETE: 100% SUCCESS")
        print("=" * 65)

    except Exception as e:
        db.rollback()
        print(f"\n[ERROR ENCOUNTERED]: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
    finally:
        db.close()


if __name__ == "__main__":
    run_tests()
