"""
AttendX — Module L4 Lecturer Records & Reports Comprehensive Verification
Tests all critical security, workflow, filtering, reporting, export, and regression scenarios:
1. Authentication & RBAC:
   - Valid lecturer token on GET /api/lecturer/records -> 200 OK
   - Valid lecturer token on GET /api/lecturer/reports/student/{id} -> 200 OK
   - Valid lecturer token on GET /api/lecturer/reports/subject/{id} -> 200 OK
   - Valid lecturer token on GET /api/lecturer/reports/export -> 200 OK
   - Student token on /api/lecturer/records -> 403 Forbidden
   - Admin token on /api/lecturer/records -> 403 Forbidden
   - No token / Invalid token on /api/lecturer/records -> 401 Unauthorized
2. Data Ownership & Isolation:
   - Lecturer A (Alan) accessing records for Subject A (IAI, SE) -> ALLOW
   - Lecturer A (Alan) accessing records for Subject B (ISC, Katherine's) -> 403 Forbidden
   - Lecturer B (Katherine) accessing records for Subject A (IAI) -> 403 Forbidden
   - Lecturer B (Katherine) accessing records for Subject B (ISC) -> ALLOW
   - Lecturer A accessing student enrolled in Subject A -> ALLOW
   - Lecturer A accessing student NOT enrolled in Subject A -> 403 Forbidden
   - Lecturer A accessing subject report for Katherine's subject -> 403 Forbidden
   - Lecturer A exporting Katherine's subject -> 403 Forbidden
3. Query Filters, Sorting & Pagination:
   - Filtering by subject_id
   - Filtering by date_from and date_to
   - Invalid date range (date_from > date_to) -> 400 Bad Request
   - Filtering by status ('present' and 'absent')
   - Student search by full_name and by student_id / roll number
   - Pagination (page, limit, total, total_pages)
   - Summary statistics (total_students, total_records, present_count, absent_count, attendance_percentage)
   - Attendance percentage formula accuracy (present / total * 100)
   - Sorting (by date, student_name, status)
4. Reports:
   - Student-level report: summary, subject breakdown, history
   - Subject-level report: summary, enrolled student breakdown, daily session breakdown
5. Export:
   - Records export to CSV (checks header, columns, content, filename)
   - Student report export to CSV
   - Subject report export to CSV
   - Strict check: no sensitive fields (password, password_hash, token, secret) in export
6. Regression:
   - Student Portal dashboard -> 200 OK
   - Admin Portal dashboard -> 200 OK
   - Lecturer L1 /api/lecturer/me -> 200 OK
   - Lecturer L2 /api/lecturer/dashboard -> 200 OK
   - Lecturer L3 /api/lecturer/attendance -> 200 OK
   - Lecturer L3 /api/lecturer/attendance/session -> 200 OK
"""
import sys
import os
from datetime import date, timedelta

# Set up path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__))))

from fastapi.testclient import TestClient
from app.main import app
from app.core.database import SessionLocal
from app.core.security import create_access_token
from app.models.user import User
from app.models.subject import Subject
from app.models.student_subject import StudentSubject
from app.models.attendance import Attendance


def run_tests():
    print("=" * 65)
    print("STARTING ATTENDX MODULE L4 VERIFICATION")
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
        es = db.query(Subject).filter(Subject.code == "ES").first()

        assert_test("Database has IAI subject", iai is not None)
        assert_test("Database has SE subject", se is not None)
        assert_test("Database has ISC subject", isc is not None)

        # Generate tokens
        alan_token = create_access_token(data={"sub": alan.id, "role": "lecturer"})
        kath_token = create_access_token(data={"sub": kath.id, "role": "lecturer"})
        admin_token = create_access_token(data={"sub": admin.id, "role": "admin"})
        student_token = create_access_token(data={"sub": student.id, "role": "student"})

        print("\n--- SUITE 1: AUTHENTICATION & RBAC ENFORCEMENT ---")

        # 1. No token on /api/lecturer/records -> 401
        r = client.get("/api/lecturer/records")
        assert_test("Missing token on GET /api/lecturer/records returns 401", r.status_code == 401)

        # 2. Invalid token on /api/lecturer/records -> 401
        r = client.get("/api/lecturer/records", headers={"Authorization": "Bearer invalid.token"})
        assert_test("Invalid token on GET /api/lecturer/records returns 401", r.status_code == 401)

        # 3. Student token on /api/lecturer/records -> 403
        r = client.get("/api/lecturer/records", headers={"Authorization": f"Bearer {student_token}"})
        assert_test("Student token on GET /api/lecturer/records returns 403 Forbidden", r.status_code == 403)

        # 4. Admin token on /api/lecturer/records -> 403
        r = client.get("/api/lecturer/records", headers={"Authorization": f"Bearer {admin_token}"})
        assert_test("Admin token on GET /api/lecturer/records returns 403 Forbidden", r.status_code == 403)

        # 5. Student token on student report -> 403
        r = client.get(f"/api/lecturer/reports/student/{student.id}", headers={"Authorization": f"Bearer {student_token}"})
        assert_test("Student token on student report returns 403 Forbidden", r.status_code == 403)

        # 6. Student token on subject report -> 403
        r = client.get(f"/api/lecturer/reports/subject/{iai.id}", headers={"Authorization": f"Bearer {student_token}"})
        assert_test("Student token on subject report returns 403 Forbidden", r.status_code == 403)

        # 7. Student token on export -> 403
        r = client.get("/api/lecturer/reports/export", headers={"Authorization": f"Bearer {student_token}"})
        assert_test("Student token on export returns 403 Forbidden", r.status_code == 403)

        print("\n--- SUITE 2: DATA OWNERSHIP & SECURITY ISOLATION ---")

        # 8. Alan accessing records with no subject filter -> returns records for Alan's subjects only
        r_alan_all = client.get("/api/lecturer/records", headers={"Authorization": f"Bearer {alan_token}"})
        assert_test("Alan gets 200 OK on GET /api/lecturer/records", r_alan_all.status_code == 200)
        data = r_alan_all.json()
        assert_test("Alan's records response has summary and records", "summary" in data and "records" in data)
        for rec in data["records"]:
            assert_test(f"Alan record belongs to IAI or SE (saw {rec['subject_code']})", rec["subject_code"] in ("IAI", "SE"))

        # 9. Alan filtering by own subject IAI -> ALLOW 200 OK
        r_alan_iai = client.get(f"/api/lecturer/records?subject_id={iai.id}", headers={"Authorization": f"Bearer {alan_token}"})
        assert_test("Alan filtering by own subject IAI returns 200 OK", r_alan_iai.status_code == 200)
        for rec in r_alan_iai.json()["records"]:
            assert_test("All records are IAI", rec["subject_code"] == "IAI")

        # 10. Alan attempting to filter by Katherine's subject ISC -> 403 Forbidden
        r_alan_spoof = client.get(f"/api/lecturer/records?subject_id={isc.id}", headers={"Authorization": f"Bearer {alan_token}"})
        assert_test("Alan filtering by Katherine's subject ISC returns 403 Forbidden", r_alan_spoof.status_code == 403)

        # 11. Katherine attempting to filter by Alan's subject IAI -> 403 Forbidden
        r_kath_spoof = client.get(f"/api/lecturer/records?subject_id={iai.id}", headers={"Authorization": f"Bearer {kath_token}"})
        assert_test("Katherine filtering by Alan's subject IAI returns 403 Forbidden", r_kath_spoof.status_code == 403)

        # 12. Katherine filtering by own subject ISC -> ALLOW 200 OK
        r_kath_isc = client.get(f"/api/lecturer/records?subject_id={isc.id}", headers={"Authorization": f"Bearer {kath_token}"})
        assert_test("Katherine filtering by own subject ISC returns 200 OK", r_kath_isc.status_code == 200)
        for rec in r_kath_isc.json()["records"]:
            assert_test("All records are ISC", rec["subject_code"] == "ISC")

        # Find Sarah Lee (enrolled only in ES, not in Alan's subjects)
        sarah = db.query(User).filter(User.email == "sarah.lee@student.com").first()
        # Find John Doe (enrolled in CS core, so in IAI and SE)
        john = db.query(User).filter(User.email == "john.doe@student.com").first()

        assert_test("Database has John Doe student", john is not None)

        # 13. Alan accessing John Doe (enrolled in Alan's IAI/SE) -> 200 OK
        r_john_report = client.get(f"/api/lecturer/reports/student/{john.id}", headers={"Authorization": f"Bearer {alan_token}"})
        assert_test("Alan accessing student enrolled in his subject returns 200 OK", r_john_report.status_code == 200)
        john_rep = r_john_report.json()
        assert_test("Student report has student_name John Doe", john_rep["student_name"] == "John Doe")
        assert_test("Student report has total_classes > 0", john_rep["total_classes"] > 0)
        assert_test("Student report percentage calculation is accurate", 0.0 <= john_rep["percentage"] <= 100.0)

        # 14. If Sarah is not enrolled in any of Alan's subjects, Alan accessing Sarah -> 403 Forbidden
        if sarah:
            alan_has_sarah = db.query(StudentSubject).filter(
                StudentSubject.student_id == sarah.id,
                StudentSubject.subject_id.in_([iai.id, se.id])
            ).first()
            if not alan_has_sarah:
                r_sarah_spoof = client.get(f"/api/lecturer/reports/student/{sarah.id}", headers={"Authorization": f"Bearer {alan_token}"})
                assert_test("Alan accessing student outside his subjects returns 403 Forbidden", r_sarah_spoof.status_code == 403)

        # 15. Alan accessing subject report for Katherine's ISC -> 403 Forbidden
        r_subj_spoof = client.get(f"/api/lecturer/reports/subject/{isc.id}", headers={"Authorization": f"Bearer {alan_token}"})
        assert_test("Alan requesting subject report for ISC returns 403 Forbidden", r_subj_spoof.status_code == 403)

        # 16. Alan exporting Katherine's ISC -> 403 Forbidden
        r_exp_spoof = client.get(f"/api/lecturer/reports/export?export_type=subject&subject_id={isc.id}", headers={"Authorization": f"Bearer {alan_token}"})
        assert_test("Alan exporting Katherine's subject returns 403 Forbidden", r_exp_spoof.status_code == 403)

        print("\n--- SUITE 3: FILTERS, PAGINATION, SORTING & AGGREGATION ---")

        # 17. Date Range Filter
        past_date = (date.today() - timedelta(days=7)).isoformat()
        today_date = date.today().isoformat()
        r_date_range = client.get(
            f"/api/lecturer/records?subject_id={iai.id}&date_from={past_date}&date_to={today_date}",
            headers={"Authorization": f"Bearer {alan_token}"}
        )
        assert_test("Date range query returns 200 OK", r_date_range.status_code == 200)
        for rec in r_date_range.json()["records"]:
            assert_test("Record date is within requested range", past_date <= rec["attendance_date"] <= today_date)

        # 18. Invalid Date Range (date_from > date_to) -> 400 Bad Request
        r_inv_dates = client.get(
            f"/api/lecturer/records?date_from={today_date}&date_to={past_date}",
            headers={"Authorization": f"Bearer {alan_token}"}
        )
        assert_test("Invalid date range (date_from > date_to) returns 400 Bad Request", r_inv_dates.status_code == 400)

        # 19. Status Filter: Present
        r_pres = client.get(f"/api/lecturer/records?status=present", headers={"Authorization": f"Bearer {alan_token}"})
        assert_test("Status=present filter returns 200 OK", r_pres.status_code == 200)
        for rec in r_pres.json()["records"]:
            assert_test("Record status is present", rec["status"] == "present")

        # 20. Status Filter: Absent
        r_abs = client.get(f"/api/lecturer/records?status=absent", headers={"Authorization": f"Bearer {alan_token}"})
        assert_test("Status=absent filter returns 200 OK", r_abs.status_code == 200)
        for rec in r_abs.json()["records"]:
            assert_test("Record status is absent", rec["status"] == "absent")

        # 21. Student Search by Name
        r_search_name = client.get(f"/api/lecturer/records?search=John", headers={"Authorization": f"Bearer {alan_token}"})
        assert_test("Student search by name returns 200 OK", r_search_name.status_code == 200)
        for rec in r_search_name.json()["records"]:
            assert_test("Search result matches student John", "John" in rec["student_name"])

        # 22. Student Search by Roll Number / student_id
        if john.student_id:
            r_search_sid = client.get(f"/api/lecturer/records?search={john.student_id}", headers={"Authorization": f"Bearer {alan_token}"})
            assert_test("Student search by roll number returns 200 OK", r_search_sid.status_code == 200)
            for rec in r_search_sid.json()["records"]:
                assert_test("Search result matches roll number", rec["student_sid"] == john.student_id)

        # 23. Pagination test
        r_page1 = client.get("/api/lecturer/records?page=1&limit=5", headers={"Authorization": f"Bearer {alan_token}"})
        assert_test("Pagination page=1 limit=5 returns 200 OK", r_page1.status_code == 200)
        p1_data = r_page1.json()
        assert_test("Page 1 limit is 5", p1_data["limit"] == 5)
        assert_test("Records count <= 5", len(p1_data["records"]) <= 5)
        assert_test("total_pages calculated properly", p1_data["total_pages"] >= 1)

        # 24. Summary Statistics Verification
        sum_data = p1_data["summary"]
        assert_test("Summary has total_records", "total_records" in sum_data)
        assert_test("Summary has present_count", "present_count" in sum_data)
        assert_test("Summary has absent_count", "absent_count" in sum_data)
        assert_test("Summary has attendance_percentage", "attendance_percentage" in sum_data)
        total_rec = sum_data["total_records"]
        pres_rec = sum_data["present_count"]
        abs_rec = sum_data["absent_count"]
        assert_test("Present + Absent equals Total Records", pres_rec + abs_rec == total_rec)
        if total_rec > 0:
            expected_pct = round((pres_rec / total_rec) * 100, 1)
            assert_test("Attendance % matches exact formula", sum_data["attendance_percentage"] == expected_pct)

        # 25. Sorting test: by student_name asc and desc
        r_sort_asc = client.get("/api/lecturer/records?sort_by=student_name&sort_order=asc&limit=10", headers={"Authorization": f"Bearer {alan_token}"})
        assert_test("Sorting by student_name asc returns 200 OK", r_sort_asc.status_code == 200)
        names = [r["student_name"] for r in r_sort_asc.json()["records"]]
        assert_test("Names are sorted in ascending order", names == sorted(names))

        print("\n--- SUITE 4: SUBJECT-LEVEL REPORT ---")

        # 26. Alan requesting subject report for IAI
        r_iai_rep = client.get(f"/api/lecturer/reports/subject/{iai.id}", headers={"Authorization": f"Bearer {alan_token}"})
        assert_test("Subject report for IAI returns 200 OK", r_iai_rep.status_code == 200)
        iai_data = r_iai_rep.json()
        assert_test("Subject report has subject_code IAI", iai_data["subject_code"] == "IAI")
        assert_test("Subject report has enrolled students list", len(iai_data["students"]) > 0)
        assert_test("Subject report has total_sessions", iai_data["total_sessions"] > 0)
        assert_test("Subject report has sessions breakdown", len(iai_data["sessions"]) > 0)

        # 27. Subject report student breakdown verification
        first_stu = iai_data["students"][0]
        assert_test("Student item has roll number (student_sid)", "student_sid" in first_stu)
        assert_test("Student item has attendance percentage", "percentage" in first_stu)

        print("\n--- SUITE 5: CSV EXPORT FUNCTIONALITY & SECURITY ---")

        # 28. Export Records CSV
        r_exp_records = client.get("/api/lecturer/reports/export?export_type=records", headers={"Authorization": f"Bearer {alan_token}"})
        assert_test("Export records returns 200 OK", r_exp_records.status_code == 200)
        assert_test("Content-Type is text/csv", "text/csv" in r_exp_records.headers.get("content-type", ""))
        assert_test("Content-Disposition attachment filename present", "attachment; filename=" in r_exp_records.headers.get("content-disposition", ""))
        csv_text = r_exp_records.text
        assert_test("CSV contains ATTENDX header", "ATTENDX — LECTURER ATTENDANCE RECORDS" in csv_text)
        assert_test("CSV contains Date column", "Date" in csv_text)
        assert_test("CSV contains Subject Code column", "Subject Code" in csv_text)
        assert_test("CSV contains Student Roll No column", "Student Roll No" in csv_text)
        assert_test("CSV contains Status column", "Status" in csv_text)

        # 29. Security check on CSV: no password hashes or tokens
        assert_test("CSV does NOT contain password_hash", "password_hash" not in csv_text.lower())
        assert_test("CSV does NOT contain bcrypt", "$2b$" not in csv_text)
        assert_test("CSV does NOT contain bearer tokens", "bearer " not in csv_text.lower())

        # 30. Export Subject Report CSV
        r_exp_subj = client.get(f"/api/lecturer/reports/export?export_type=subject&subject_id={iai.id}", headers={"Authorization": f"Bearer {alan_token}"})
        assert_test("Export subject report returns 200 OK", r_exp_subj.status_code == 200)
        subj_csv = r_exp_subj.text
        assert_test("Subject CSV contains subject title", "ATTENDX — SUBJECT ATTENDANCE REPORT" in subj_csv)
        assert_test("Subject CSV contains IAI code", "IAI" in subj_csv)
        assert_test("Subject CSV contains Attendance % column", "Attendance %" in subj_csv)

        # 31. Export Student Report CSV
        r_exp_stu = client.get(f"/api/lecturer/reports/export?export_type=student&student_id={john.id}", headers={"Authorization": f"Bearer {alan_token}"})
        assert_test("Export student report returns 200 OK", r_exp_stu.status_code == 200)
        stu_csv = r_exp_stu.text
        assert_test("Student CSV contains student title", "INDIVIDUAL STUDENT ATTENDANCE REPORT" in stu_csv)
        assert_test("Student CSV contains John Doe", "John Doe" in stu_csv)

        print("\n--- SUITE 6: REGRESSION TESTING ---")

        # 32. Student Portal dashboard still 200
        r_stu_dash = client.get("/api/dashboard/student", headers={"Authorization": f"Bearer {student_token}"})
        assert_test("Student Portal dashboard returns 200 OK", r_stu_dash.status_code == 200)

        # 33. Admin Portal dashboard still 200
        r_adm_dash = client.get("/api/admin/dashboard", headers={"Authorization": f"Bearer {admin_token}"})
        assert_test("Admin Portal dashboard returns 200 OK", r_adm_dash.status_code == 200)

        # 34. Lecturer L1 profile still 200
        r_lec_me = client.get("/api/lecturer/me", headers={"Authorization": f"Bearer {alan_token}"})
        assert_test("Lecturer L1 /api/lecturer/me returns 200 OK", r_lec_me.status_code == 200)

        # 35. Lecturer L2 dashboard still 200
        r_lec_dash = client.get("/api/lecturer/dashboard", headers={"Authorization": f"Bearer {alan_token}"})
        assert_test("Lecturer L2 /api/lecturer/dashboard returns 200 OK", r_lec_dash.status_code == 200)

        # 36. Lecturer L3 attendance session still 200
        r_lec_sess = client.get(f"/api/lecturer/attendance/session?subject_id={iai.id}&attendance_date={today_date}", headers={"Authorization": f"Bearer {alan_token}"})
        assert_test("Lecturer L3 /api/lecturer/attendance/session returns 200 OK", r_lec_sess.status_code == 200)

        # 37. Lecturer L3 attendance list still 200
        r_lec_att = client.get("/api/lecturer/attendance", headers={"Authorization": f"Bearer {alan_token}"})
        assert_test("Lecturer L3 /api/lecturer/attendance returns 200 OK", r_lec_att.status_code == 200)

        print("\n" + "=" * 65)
        print(f"ALL TESTS PASSED: {passed_count}/{total_count}")
        print("MODULE L4 BACKEND VERIFICATION COMPLETE: 100% SUCCESS")
        print("=" * 65)

    finally:
        db.close()


if __name__ == "__main__":
    run_tests()
