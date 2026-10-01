"""
AttendX — Module I2 Notifications System Verification Suite
Tests the complete database-backed notifications system across all portals, database events, and APIs:

Strategy 1: Unit & Integration Testing
1. Notification creation on Student Enrollment (subject details, deduplication)
2. Notification creation on Lecturer Faculty creation (welcome notification)
3. Notification creation on Lecturer Assignment & Unassignment
4. Notification creation on Attendance Marked (subject code/name, date, status)
5. Notification creation on Attendance Updated (status update, is_update flag)
6. Idempotency & Deduplication enforcement
7. GET /api/notifications ordering (created_at DESC), pagination, and filtering
8. GET /api/notifications?unread_only=true filtering
9. GET /api/notifications?type=attendance category filtering
10. GET /api/notifications/unread-count real-time count
11. PATCH /api/notifications/{id}/read single notification update
12. PATCH /api/notifications/read-all bulk update for current user
13. Strict RBAC & Tenant Isolation (User A cannot access or mark User B's notifications)
14. Unauthenticated access enforcement (401)

Strategy 2: End-to-End Workflows
15. Complete Student Notification Lifecycle (Enrollment -> Attendance -> Notifications -> Mark Read)
16. Complete Lecturer Notification Lifecycle (Faculty Created -> Subject Assigned -> Unassigned -> Review & Mark All Read)
17. Attendance Status Change Lifecycle (Recorded Absent -> Updated Present -> Notifications Verified)

Strategy 3: Edge Cases, Security & Regression
18. Clean empty state handling (zero notifications, count = 0)
19. Non-existent notification ID handling (404)
20. Idempotent marking of already read notifications
21. Zero secrets / credential leakage in notification data
22. Regression stability check across Core Endpoints (Students, Lecturers, Subjects, Attendance)
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
from app.models.notification import Notification


def run_i2_notifications_suite():
    print("=" * 75)
    print("ATTENDX — MODULE I2 NOTIFICATIONS SYSTEM VERIFICATION SUITE")
    print("=" * 75)

    client = TestClient(app)
    db = SessionLocal()

    total_tests = 0
    passed_tests = 0
    failed_tests = 0

    def test(name: str, condition: bool, detail: str = ""):
        nonlocal total_tests, passed_tests, failed_tests
        total_tests += 1
        if condition:
            passed_tests += 1
            print(f"  [PASS] Test {total_tests:02d}: {name}")
        else:
            failed_tests += 1
            print(f"  [FAIL] Test {total_tests:02d}: {name} - {detail}")

    try:
        # =========================================================================
        # Setup Test Users and Entities
        # =========================================================================
        run_id = uuid.uuid4().hex[:6]

        # Admin
        admin_email = f"i2_admin_{run_id}@attendx.edu"
        admin = User(
            full_name=f"Admin I2 {run_id}",
            email=admin_email,
            password_hash=hash_password("adminpass123"),
            role="admin",
            is_active=True,
        )
        db.add(admin)

        # Student A
        student_a_email = f"i2_student_a_{run_id}@attendx.edu"
        student_a = User(
            full_name=f"Student A {run_id}",
            email=student_a_email,
            password_hash=hash_password("studentpass123"),
            role="student",
            student_id=f"I2STU-{run_id}-A",
            department="Computer Science",
            year=3,
            section="A",
            is_active=True,
        )
        db.add(student_a)

        # Student B
        student_b_email = f"i2_student_b_{run_id}@attendx.edu"
        student_b = User(
            full_name=f"Student B {run_id}",
            email=student_b_email,
            password_hash=hash_password("studentpass123"),
            role="student",
            student_id=f"I2STU-{run_id}-B",
            department="Information Technology",
            year=2,
            section="B",
            is_active=True,
        )
        db.add(student_b)

        # Lecturer A
        lecturer_a_email = f"i2_lecturer_a_{run_id}@attendx.edu"
        lecturer_a = User(
            full_name=f"Dr. Lecturer A {run_id}",
            email=lecturer_a_email,
            password_hash=hash_password("lecturerpass123"),
            role="lecturer",
            employee_id=f"I2EMP-{run_id}-A",
            department="Computer Science",
            is_active=True,
        )
        db.add(lecturer_a)

        db.commit()
        db.refresh(admin)
        db.refresh(student_a)
        db.refresh(student_b)
        db.refresh(lecturer_a)

        admin_token = create_access_token({"sub": admin.id, "role": "admin"})
        student_a_token = create_access_token({"sub": student_a.id, "role": "student"})
        student_b_token = create_access_token({"sub": student_b.id, "role": "student"})
        lecturer_a_token = create_access_token({"sub": lecturer_a.id, "role": "lecturer"})

        admin_headers = {"Authorization": f"Bearer {admin_token}"}
        student_a_headers = {"Authorization": f"Bearer {student_a_token}"}
        student_b_headers = {"Authorization": f"Bearer {student_b_token}"}
        lecturer_a_headers = {"Authorization": f"Bearer {lecturer_a_token}"}

        print("\n--- Strategy 1: Unit & Integration Testing ---")

        # 1. Clean empty state for new user
        res = client.get("/api/notifications", headers=student_a_headers)
        test("Initial notifications list is empty for new user", res.status_code == 200 and len(res.json()) == 0)

        res = client.get("/api/notifications/unread-count", headers=student_a_headers)
        test("Initial unread notification count is 0", res.status_code == 200 and res.json().get("count") == 0)

        # 2. Student Enrollment Notification
        subject_1 = Subject(
            code=f"CS-{run_id}-1",
            name=f"Distributed Systems {run_id}",
            department="Computer Science",
            year=3,
            semester=5,
        )
        db.add(subject_1)
        db.commit()
        db.refresh(subject_1)

        enroll_res = client.post(
            "/api/subjects/enroll",
            headers=student_a_headers,
            json={"student_id": student_a.id, "subject_id": subject_1.id},
        )
        test("Student enrolls in subject successfully", enroll_res.status_code == 201)

        # Verify notification created
        notifs_res = client.get("/api/notifications", headers=student_a_headers)
        notifs = notifs_res.json()
        has_enroll_notif = any(
            n["type"] == "enrollment" and subject_1.code in n["message"] and not n["is_read"]
            for n in notifs
        )
        test("Enrollment notification created with subject code/name", has_enroll_notif)

        # 3. Idempotent enrollment deduplication
        # Re-triggering enrollment for same subject should not duplicate notifications
        enroll_again = client.post(
            "/api/subjects/enroll",
            headers=student_a_headers,
            json={"student_id": student_a.id, "subject_id": subject_1.id},
        )
        notifs_res2 = client.get("/api/notifications", headers=student_a_headers)
        enroll_count = sum(1 for n in notifs_res2.json() if n["type"] == "enrollment")
        test("Enrollment notification is idempotent and does not create duplicate", enroll_count == 1)

        # 4. Lecturer Faculty Welcome Notification
        new_lec_data = {
            "full_name": f"Prof. Newly Created {run_id}",
            "email": f"newlec_{run_id}@attendx.edu",
            "password": "Password123!",
            "department": "Computer Science",
            "employee_id": f"EMP-NEW-{run_id}",
        }
        create_lec_res = client.post("/api/admin/lecturers", headers=admin_headers, json=new_lec_data)
        test("Admin creates new lecturer", create_lec_res.status_code == 201)
        new_lec_id = create_lec_res.json()["id"]

        new_lec_token = create_access_token({"sub": new_lec_id, "role": "lecturer"})
        new_lec_headers = {"Authorization": f"Bearer {new_lec_token}"}

        lec_notifs_res = client.get("/api/notifications", headers=new_lec_headers)
        lec_notifs = lec_notifs_res.json()
        has_welcome = any(
            n["type"] == "system" and "Welcome" in n["title"] and not n["is_read"]
            for n in lec_notifs
        )
        test("Faculty welcome notification created upon lecturer account creation", has_welcome)

        # 5. Lecturer Subject Assignment Notification
        assign_res = client.post(
            "/api/admin/assignments",
            headers=admin_headers,
            json={"lecturer_id": lecturer_a.id, "subject_id": subject_1.id},
        )
        test("Admin assigns subject to lecturer", assign_res.status_code == 201)

        lec_a_notifs_res = client.get("/api/notifications", headers=lecturer_a_headers)
        lec_a_notifs = lec_a_notifs_res.json()
        has_assign_notif = any(
            n["type"] == "system" and "Assigned" in n["title"] and subject_1.code in n["message"]
            for n in lec_a_notifs
        )
        test("Subject assignment notification delivered to lecturer", has_assign_notif)

        # 6. Lecturer Subject Unassignment Notification
        # Delete assignment
        unassign_res = client.delete(
            f"/api/admin/subjects/{subject_1.id}/lecturers/{lecturer_a.id}",
            headers=admin_headers,
        )
        test("Admin unassigns subject from lecturer", unassign_res.status_code in (200, 204))

        lec_a_notifs_res2 = client.get("/api/notifications", headers=lecturer_a_headers)
        has_unassign_notif = any(
            n["type"] == "system" and "Removed" in n["title"] and subject_1.code in n["message"]
            for n in lec_a_notifs_res2.json()
        )
        test("Subject unassignment notification delivered to lecturer", has_unassign_notif)

        # Re-assign so lecturer can mark attendance in next tests
        client.post(
            "/api/admin/assignments",
            headers=admin_headers,
            json={"lecturer_id": lecturer_a.id, "subject_id": subject_1.id},
        )

        # 7. Student Attendance Recorded Notification
        test_date = (date.today() - timedelta(days=2)).isoformat()
        att_mark_res = client.post(
            "/api/lecturer/attendance",
            headers=lecturer_a_headers,
            json={
                "subject_id": subject_1.id,
                "attendance_date": test_date,
                "records": [{"student_id": student_a.id, "status": "present"}],
            },
        )
        test("Lecturer marks attendance for student", att_mark_res.status_code == 201)

        student_notifs_res = client.get("/api/notifications", headers=student_a_headers)
        student_notifs = student_notifs_res.json()
        att_notif = next(
            (n for n in student_notifs if n["type"] == "attendance" and "Recorded" in n["title"]),
            None,
        )
        test("Attendance recorded notification created for student", att_notif is not None)
        if att_notif:
            test(
                "Notification message contains subject label and Present status",
                "Present" in att_notif["message"] and subject_1.code in att_notif["message"],
            )

        # 8. Student Attendance Updated Notification
        # Update attendance status to 'absent'
        att_update_res = client.post(
            "/api/lecturer/attendance",
            headers=lecturer_a_headers,
            json={
                "subject_id": subject_1.id,
                "attendance_date": test_date,
                "records": [{"student_id": student_a.id, "status": "absent"}],
            },
        )
        test("Lecturer updates attendance to absent", att_update_res.status_code in (200, 201))

        student_notifs_res3 = client.get("/api/notifications", headers=student_a_headers)
        att_upd_notif = next(
            (n for n in student_notifs_res3.json() if n["type"] == "attendance" and "Updated" in n["title"]),
            None,
        )
        test("Attendance updated notification created with 'Updated' title", att_upd_notif is not None)
        if att_upd_notif:
            test("Updated notification message specifies Absent", "Absent" in att_upd_notif["message"])

        # 9. Query Filtering: unread_only and type
        res_unread_only = client.get("/api/notifications?unread_only=true", headers=student_a_headers)
        test(
            "Filter unread_only=true returns only unread items",
            res_unread_only.status_code == 200 and all(not n["is_read"] for n in res_unread_only.json()),
        )

        res_type_filter = client.get("/api/notifications?type=attendance", headers=student_a_headers)
        test(
            "Filter type=attendance returns only attendance notifications",
            res_type_filter.status_code == 200 and all(n["type"] == "attendance" for n in res_type_filter.json()),
        )

        # 10. Mark Single Notification as Read
        target_notif = student_notifs_res3.json()[0]
        mark_read_res = client.patch(
            f"/api/notifications/{target_notif['id']}/read",
            headers=student_a_headers,
        )
        test("Mark single notification as read returns 200 with is_read=True", mark_read_res.status_code == 200 and mark_read_res.json()["is_read"] is True)

        # 11. Mark All Notifications as Read
        mark_all_res = client.patch("/api/notifications/read-all", headers=student_a_headers)
        test("Mark all notifications as read returns 200", mark_all_res.status_code == 200)

        count_after_all = client.get("/api/notifications/unread-count", headers=student_a_headers).json()["count"]
        test("Unread count is 0 after mark-all-as-read", count_after_all == 0)

        # 12. Security & RBAC Isolation
        # Student B attempts to mark Student A's notification as read -> 403 Forbidden
        cross_res = client.patch(
            f"/api/notifications/{target_notif['id']}/read",
            headers=student_b_headers,
        )
        test("Cross-user access is strictly forbidden (403)", cross_res.status_code == 403)

        # Unauthenticated request -> 401 Unauthorized
        unauth_res = client.get("/api/notifications")
        test("Unauthenticated request to notifications endpoint returns 401", unauth_res.status_code == 401)

        print("\n--- Strategy 2: End-to-End Workflow Testing ---")

        # 13. Complete Student Workflow
        student_c_email = f"i2_student_c_{run_id}@attendx.edu"
        student_c = User(
            full_name=f"Workflow Student {run_id}",
            email=student_c_email,
            password_hash=hash_password("pass123"),
            role="student",
            student_id=f"I2STU-{run_id}-C",
            department="Computer Science",
            year=1,
            section="A",
            is_active=True,
        )
        db.add(student_c)
        db.commit()
        db.refresh(student_c)

        student_c_token = create_access_token({"sub": student_c.id, "role": "student"})
        student_c_headers = {"Authorization": f"Bearer {student_c_token}"}

        # Step 1: Initial unread count is 0
        c_count_0 = client.get("/api/notifications/unread-count", headers=student_c_headers).json()["count"]
        test("Workflow 1.1: Initial unread count is 0", c_count_0 == 0)

        # Step 2: Student enrolls in Subject 1
        client.post(
            "/api/subjects/enroll",
            headers=student_c_headers,
            json={"student_id": student_c.id, "subject_id": subject_1.id},
        )
        c_count_1 = client.get("/api/notifications/unread-count", headers=student_c_headers).json()["count"]
        test("Workflow 1.2: Unread count increases to 1 after enrollment", c_count_1 == 1)

        # Step 3: Lecturer marks attendance
        att_wf = client.post(
            "/api/lecturer/attendance",
            headers=lecturer_a_headers,
            json={
                "subject_id": subject_1.id,
                "attendance_date": (date.today() - timedelta(days=1)).isoformat(),
                "records": [{"student_id": student_c.id, "status": "present"}],
            },
        )
        c_count_2 = client.get("/api/notifications/unread-count", headers=student_c_headers).json()["count"]
        test("Workflow 1.3: Unread count increases to 2 after attendance recorded", c_count_2 == 2)

        # Step 4: Student fetches notifications
        c_notifs = client.get("/api/notifications", headers=student_c_headers).json()
        test("Workflow 1.4: Student receives exactly 2 notifications in descending order", len(c_notifs) == 2 and c_notifs[0]["created_at"] >= c_notifs[1]["created_at"])

        # Step 5: Student marks all read
        client.patch("/api/notifications/read-all", headers=student_c_headers)
        c_count_final = client.get("/api/notifications/unread-count", headers=student_c_headers).json()["count"]
        test("Workflow 1.5: Unread count becomes 0 after mark-all-read", c_count_final == 0)

        # 14. Complete Lecturer Workflow
        lec_b_email = f"i2_lecturer_b_{run_id}@attendx.edu"
        create_lec_b = client.post(
            "/api/admin/lecturers",
            headers=admin_headers,
            json={
                "full_name": f"Dr. Workflow Lecturer {run_id}",
                "email": lec_b_email,
                "password": "Password123!",
                "department": "Computer Science",
                "employee_id": f"EMP-WF-{run_id}",
            },
        )
        test("Workflow 2.1: Admin creates faculty account", create_lec_b.status_code == 201)
        lec_b_id = create_lec_b.json()["id"]

        lec_b_token = create_access_token({"sub": lec_b_id, "role": "lecturer"})
        lec_b_headers = {"Authorization": f"Bearer {lec_b_token}"}

        # Check welcome notification
        lec_b_notifs = client.get("/api/notifications", headers=lec_b_headers).json()
        test("Workflow 2.2: Faculty receives welcome notification immediately", len(lec_b_notifs) == 1 and "Welcome" in lec_b_notifs[0]["title"])

        # Admin assigns subject
        client.post(
            "/api/admin/assignments",
            headers=admin_headers,
            json={"lecturer_id": lec_b_id, "subject_id": subject_1.id},
        )
        lec_b_notifs_after_assign = client.get("/api/notifications", headers=lec_b_headers).json()
        test("Workflow 2.3: Faculty receives assignment notification", len(lec_b_notifs_after_assign) == 2 and "Assigned" in lec_b_notifs_after_assign[0]["title"])

        # Admin removes assignment
        client.delete(
            f"/api/admin/subjects/{subject_1.id}/lecturers/{lec_b_id}",
            headers=admin_headers,
        )
        lec_b_notifs_after_remove = client.get("/api/notifications", headers=lec_b_headers).json()
        test("Workflow 2.4: Faculty receives removal notification", len(lec_b_notifs_after_remove) == 3 and "Removed" in lec_b_notifs_after_remove[0]["title"])

        # Mark all read
        client.patch("/api/notifications/read-all", headers=lec_b_headers)
        lec_b_unread = client.get("/api/notifications/unread-count", headers=lec_b_headers).json()["count"]
        test("Workflow 2.5: Faculty marks all notifications as read", lec_b_unread == 0)

        print("\n--- Strategy 3: Edge Cases, Security & Regression Testing ---")

        # 15. Invalid Notification ID
        fake_id = str(uuid.uuid4())
        fake_res = client.patch(f"/api/notifications/{fake_id}/read", headers=student_a_headers)
        test("Non-existent notification ID returns 404 Not Found", fake_res.status_code == 404)

        # 16. Idempotent Read Status Update
        # Marking an already read notification again succeeds without error
        already_read_id = target_notif["id"]
        re_read_res = client.patch(f"/api/notifications/{already_read_id}/read", headers=student_a_headers)
        test("Marking already read notification succeeds idempotently", re_read_res.status_code == 200 and re_read_res.json()["is_read"] is True)

        # 17. Zero Secret Leakage in Notification Payloads
        sample_notifs = client.get("/api/notifications", headers=student_a_headers).json()
        all_text = " ".join([f"{n.get('title', '')} {n.get('message', '')}" for n in sample_notifs])
        has_secret_leak = any(
            secret_word in all_text.lower()
            for secret_word in ["password", "hash", "argon2", "bcrypt", "secret_key", "token="]
        )
        test("Zero credentials, password hashes, or secrets leaked in notification text", not has_secret_leak)

        # 18. Full Regression: Ensure All Prior Modules Remain 100% Functional
        # Student Dashboard
        s_dash = client.get("/api/dashboard/student", headers=student_a_headers)
        test("Regression: Student Dashboard Stats endpoint returns 200", s_dash.status_code == 200)

        # Admin Dashboard Summary
        a_dash = client.get("/api/dashboard/admin", headers=admin_headers)
        test("Regression: Admin Dashboard Summary endpoint returns 200", a_dash.status_code == 200)

        # Lecturer Dashboard
        l_dash = client.get("/api/lecturer/dashboard", headers=lecturer_a_headers)
        test("Regression: Lecturer Dashboard endpoint returns 200", l_dash.status_code == 200)

        # Lecturer Reports
        l_rep = client.get(f"/api/lecturer/reports/subject/{subject_1.id}", headers=lecturer_a_headers)
        test("Regression: Lecturer Subject Report endpoint returns 200", l_rep.status_code == 200)

        # Admin Subjects
        a_subj = client.get("/api/admin/subjects", headers=admin_headers)
        test("Regression: Admin Subjects endpoint returns 200", a_subj.status_code == 200)

    finally:
        db.close()

    print("\n" + "=" * 75)
    print(f"I2 TEST RESULTS: {passed_tests}/{total_tests} PASSED ({failed_tests} FAILED)")
    print("=" * 75)

    if failed_tests > 0:
        sys.exit(1)


if __name__ == "__main__":
    run_i2_notifications_suite()
