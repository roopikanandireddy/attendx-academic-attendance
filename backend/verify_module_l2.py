"""
AttendX — Module L2 Lecturer Dashboard Comprehensive Verification
Tests all 3 strategies:
1. Unit/Integration:
   - Valid lecturer token -> 200 OK
   - Response schema matches LecturerDashboardResponse
   - Lecturer with assigned subjects (Dr. Alan Turing -> IAI, SE)
   - Lecturer with single assigned subject (Dr. Katherine Johnson -> ISC)
   - Lecturer with 0 subjects (dummy lecturer) -> clean zeroes, no division-by-zero
   - Lecturer with subjects but 0 attendance -> clean zeroes, has_attendance: false
   - Student token -> 403 Forbidden
   - Admin token -> 403 Forbidden
   - Missing token -> 401 Unauthorized
   - Invalid token -> 401 Unauthorized
   - Query param spoofing (e.g. ?lecturer_id=other) is completely ignored
   - Data Isolation: Alan cannot see Katherine's subjects, Katherine cannot see Alan's subjects
   - Distinct student counting: no double-counting for students enrolled in multiple subjects
2. Failure / Edge cases:
   - Division-by-zero handling
   - Empty activity and empty subjects
3. Regression:
   - Student Portal dashboard endpoint -> 200 OK
   - Admin Portal dashboard endpoint -> 200 OK
   - Admin Lecturers summary -> 200 OK
   - Admin Assignments summary -> 200 OK
   - Lecturer L1 /api/lecturer/me -> 200 OK
"""
import sys
import os
from datetime import date, datetime, timezone
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
from app.schemas.dashboard import LecturerDashboardResponse


def run_tests():
    print("=" * 65)
    print("STARTING ATTENDX MODULE L2 VERIFICATION")
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
        # Step 0: Fetch or create test entities
        admin = db.query(User).filter(User.role == "admin").first()
        student = db.query(User).filter(User.role == "student").first()
        alan = db.query(User).filter(User.email == "dr.alan@lecturer.com").first()
        kath = db.query(User).filter(User.email == "katherine.johnson@attendx.com").first()

        assert_test("Database has admin account", admin is not None)
        assert_test("Database has student account", student is not None)
        assert_test("Database has Dr. Alan Turing account", alan is not None)

        if not kath:
            kath = User(
                email="katherine.johnson@attendx.com",
                full_name="Dr. Katherine Johnson",
                password_hash=hash_password("LecturerPassword123!"),
                role="lecturer",
                employee_id="EMP-CS-002",
                department="Computer Science",
                is_active=True,
            )
            db.add(kath)
            db.commit()
            db.refresh(kath)

        assert_test("Database has Dr. Katherine Johnson account", kath is not None)

        # Generate tokens
        alan_token = create_access_token(data={"sub": alan.id, "role": "lecturer"})
        kath_token = create_access_token(data={"sub": kath.id, "role": "lecturer"})
        admin_token = create_access_token(data={"sub": admin.id, "role": "admin"})
        student_token = create_access_token(data={"sub": student.id, "role": "student"})

        print("\n--- STRATEGY 1: AUTHENTICATION & RBAC ---")

        # 1. No token -> 401
        r = client.get("/api/lecturer/dashboard")
        assert_test("Missing token returns 401 Unauthorized", r.status_code == 401)

        # 2. Invalid token -> 401
        r = client.get("/api/lecturer/dashboard", headers={"Authorization": "Bearer invalid.token.value"})
        assert_test("Invalid token returns 401 Unauthorized", r.status_code == 401)

        # 3. Student token -> 403
        r = client.get("/api/lecturer/dashboard", headers={"Authorization": f"Bearer {student_token}"})
        assert_test("Student token returns 403 Forbidden", r.status_code == 403, f"Got: {r.status_code}")

        # 4. Admin token -> 403
        r = client.get("/api/lecturer/dashboard", headers={"Authorization": f"Bearer {admin_token}"})
        assert_test("Admin token returns 403 Forbidden", r.status_code == 403, f"Got: {r.status_code}")

        # 5. Lecturer token -> 200 OK on /api/lecturer/dashboard
        r = client.get("/api/lecturer/dashboard", headers={"Authorization": f"Bearer {alan_token}"})
        assert_test("Valid lecturer token returns 200 OK", r.status_code == 200, f"Got: {r.status_code}")

        # 6. Alias endpoint /api/dashboard/lecturer -> 200 OK
        r_alias = client.get("/api/dashboard/lecturer", headers={"Authorization": f"Bearer {alan_token}"})
        assert_test("Alias endpoint /api/dashboard/lecturer returns 200 OK", r_alias.status_code == 200)

        # 7. Response Schema Validation
        payload = r.json()
        validated = LecturerDashboardResponse.model_validate(payload)
        assert_test("Response matches LecturerDashboardResponse schema", validated is not None)
        assert_test("Lecturer identity in payload matches token", validated.lecturer.id == alan.id)
        assert_test("Lecturer email matches", validated.lecturer.email == alan.email)

        print("\n--- STRATEGY 2: DATA ISOLATION & ACCURACY ---")

        # 8. Query parameter spoofing test
        r_spoof = client.get(
            f"/api/lecturer/dashboard?lecturer_id={kath.id}",
            headers={"Authorization": f"Bearer {alan_token}"}
        )
        assert_test("Spoofed lecturer_id query param is ignored", r_spoof.status_code == 200)
        spoof_data = r_spoof.json()
        assert_test("Identity returned is still authenticated lecturer", spoof_data["lecturer"]["id"] == alan.id)

        # 9. Verify Dr. Alan Turing data
        alan_data = client.get("/api/lecturer/dashboard", headers={"Authorization": f"Bearer {alan_token}"}).json()
        alan_subject_codes = [s["code"] for s in alan_data["subjects"]]
        assert_test("Alan has assigned subjects IAI and SE", "IAI" in alan_subject_codes and "SE" in alan_subject_codes)
        assert_test("Alan does NOT have Katherine's subject ISC", "ISC" not in alan_subject_codes)

        # 10. Verify Dr. Katherine Johnson data
        kath_data = client.get("/api/lecturer/dashboard", headers={"Authorization": f"Bearer {kath_token}"}).json()
        kath_subject_codes = [s["code"] for s in kath_data["subjects"]]
        assert_test("Katherine has assigned subject ISC", "ISC" in kath_subject_codes)
        assert_test("Katherine does NOT have Alan's subjects IAI or SE", "IAI" not in kath_subject_codes and "SE" not in kath_subject_codes)

        # 11. Multi-subject distinct student count
        # In CS subjects, John, Jane, Alex are enrolled in both IAI and SE.
        # They must be counted ONCE in total_students, NOT 3 + 3 = 6!
        iai_sub = db.query(Subject).filter(Subject.code == "IAI").first()
        se_sub = db.query(Subject).filter(Subject.code == "SE").first()
        iai_students = set(e.student_id for e in db.query(StudentSubject).filter(StudentSubject.subject_id == iai_sub.id).all())
        se_students = set(e.student_id for e in db.query(StudentSubject).filter(StudentSubject.subject_id == se_sub.id).all())
        expected_unique_students = len(iai_students.union(se_students))

        assert_test(
            f"Unique student count deduplicates across multiple subjects ({alan_data['summary']['total_students']} == {expected_unique_students})",
            alan_data["summary"]["total_students"] == expected_unique_students
        )

        # 12. Attendance metrics validation
        assert_test("Attendance records count > 0", alan_data["summary"]["total_attendance_records"] > 0)
        assert_test("Average attendance is numeric and between 0 and 100", 0.0 <= alan_data["summary"]["average_attendance"] <= 100.0)
        assert_test("attendance_overview has_data is True", alan_data["attendance_overview"]["has_data"] is True)

        # 13. Recent activity validation
        assert_test("Recent activity list is populated", len(alan_data["recent_activity"]) > 0)
        for act in alan_data["recent_activity"]:
            assert_test(f"Activity subject {act['subject_code']} belongs to lecturer's assigned subjects", act["subject_code"] in alan_subject_codes)

        print("\n--- STRATEGY 3: EDGE CASES & ZERO-DIVISION SAFETY ---")

        # 14. Lecturer with 0 subjects assigned
        unassigned_lec = db.query(User).filter(User.email == "unassigned.lec@attendx.com").first()
        if not unassigned_lec:
            unassigned_lec = User(
                email="unassigned.lec@attendx.com",
                full_name="Prof. Unassigned",
                password_hash=hash_password("LecturerPassword123!"),
                role="lecturer",
                employee_id="EMP-EMPTY-001",
                department="Mathematics",
                is_active=True,
            )
            db.add(unassigned_lec)
            db.commit()
            db.refresh(unassigned_lec)

        unassigned_token = create_access_token(data={"sub": unassigned_lec.id, "role": "lecturer"})
        r_unassigned = client.get("/api/lecturer/dashboard", headers={"Authorization": f"Bearer {unassigned_token}"})
        assert_test("Unassigned lecturer request succeeds with 200 OK", r_unassigned.status_code == 200)

        empty_data = r_unassigned.json()
        assert_test("Unassigned lecturer has 0 subjects", empty_data["summary"]["total_subjects"] == 0)
        assert_test("Unassigned lecturer has 0 students", empty_data["summary"]["total_students"] == 0)
        assert_test("Unassigned lecturer has 0 attendance records", empty_data["summary"]["total_attendance_records"] == 0)
        assert_test("Unassigned lecturer average_attendance is 0.0 (no div by zero)", empty_data["summary"]["average_attendance"] == 0.0)
        assert_test("Unassigned lecturer has_data is False", empty_data["attendance_overview"]["has_data"] is False)
        assert_test("Unassigned lecturer subjects is empty list", empty_data["subjects"] == [])
        assert_test("Unassigned lecturer recent_activity is empty list", empty_data["recent_activity"] == [])

        # 15. Lecturer with assigned subject that has 0 attendance records
        # Create a new test subject with 0 attendance records
        zero_att_sub = db.query(Subject).filter(Subject.code == "ZERO-ATT").first()
        if not zero_att_sub:
            zero_att_sub = Subject(
                name="Zero Attendance Test Subject",
                code="ZERO-ATT",
                department="Testing",
                year=1,
                semester=1,
            )
            db.add(zero_att_sub)
            db.commit()
            db.refresh(zero_att_sub)

        # Assign ZERO-ATT to unassigned_lec
        test_assign = db.query(LecturerSubject).filter(
            LecturerSubject.lecturer_id == unassigned_lec.id,
            LecturerSubject.subject_id == zero_att_sub.id,
        ).first()
        if not test_assign:
            test_assign = LecturerSubject(lecturer_id=unassigned_lec.id, subject_id=zero_att_sub.id)
            db.add(test_assign)
            db.commit()

        r_zero_att = client.get("/api/lecturer/dashboard", headers={"Authorization": f"Bearer {unassigned_token}"})
        assert_test("Lecturer with 0-attendance subject returns 200 OK", r_zero_att.status_code == 200)
        zero_data = r_zero_att.json()
        assert_test("total_subjects is 1", zero_data["summary"]["total_subjects"] == 1)
        assert_test("total_attendance_records is 0", zero_data["summary"]["total_attendance_records"] == 0)
        assert_test("average_attendance handles total=0 correctly (0.0)", zero_data["summary"]["average_attendance"] == 0.0)
        assert_test("subject attendance_percentage is 0.0", zero_data["subjects"][0]["attendance_percentage"] == 0.0)
        assert_test("subject has_attendance is False", zero_data["subjects"][0]["has_attendance"] is False)
        assert_test("attendance_overview has_data is False", zero_data["attendance_overview"]["has_data"] is False)

        # Cleanup test assignment
        db.delete(test_assign)
        db.delete(zero_att_sub)
        db.delete(unassigned_lec)
        db.commit()

        print("\n--- STRATEGY 4: REGRESSION TESTING ---")

        # 16. Lecturer Foundation L1 /api/lecturer/me
        r_l1 = client.get("/api/lecturer/me", headers={"Authorization": f"Bearer {alan_token}"})
        assert_test("Lecturer L1 /api/lecturer/me returns 200 OK", r_l1.status_code == 200)
        assert_test("L1 me response has full_name", r_l1.json()["full_name"] == alan.full_name)

        # 17. Student Portal /api/dashboard/student
        r_stu_dash = client.get("/api/dashboard/student", headers={"Authorization": f"Bearer {student_token}"})
        assert_test("Student Portal /api/dashboard/student returns 200 OK", r_stu_dash.status_code == 200)

        # 18. Admin Portal /api/admin/dashboard
        r_adm_dash = client.get("/api/admin/dashboard", headers={"Authorization": f"Bearer {admin_token}"})
        assert_test("Admin Portal /api/admin/dashboard returns 200 OK", r_adm_dash.status_code == 200)

        # 19. Admin Students Summary
        r_adm_stu = client.get("/api/admin/students/summary", headers={"Authorization": f"Bearer {admin_token}"})
        assert_test("Admin Students summary returns 200 OK", r_adm_stu.status_code == 200)

        # 20. Admin Lecturers Summary
        r_adm_lec = client.get("/api/admin/lecturers/summary", headers={"Authorization": f"Bearer {admin_token}"})
        assert_test("Admin Lecturers summary returns 200 OK", r_adm_lec.status_code == 200)

        # 21. Admin Assignments Summary
        r_adm_asn = client.get("/api/admin/assignments/summary", headers={"Authorization": f"Bearer {admin_token}"})
        assert_test("Admin Assignments summary returns 200 OK", r_adm_asn.status_code == 200)

        print("\n" + "=" * 65)
        print(f"ALL TESTS PASSED: {passed_count}/{total_count}")
        print("MODULE L2 VERIFICATION COMPLETE: 100% SUCCESS")
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
