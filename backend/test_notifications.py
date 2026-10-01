"""
Complete Notification Lifecycle & Security Test Suite for AttendX
Tests all 12 lifecycle requirements:
1. System welcome notification on new student registration
2. Dynamic enrollment notification upon subject enrollment
3. Fetch notifications for user (newest first, correct fields)
4. Mark single notification as read
5. Unread count decreases accurately
6. Mark all notifications as read
7. Attendance notification created upon marking attendance
8. Low-attendance warning (< 75%) triggered upon attendance mark
9. Notifications persist in database across requests
10. Notification isolation: Student A cannot see Student B's notifications
11. Security & authorization: Student cannot mark or read another student's notification (403/404)
12. Duplicate prevention: repeated attendance or rendering does not spam duplicate notifications
"""
import urllib.request
import urllib.error
import json
import uuid
import datetime

BASE_URL = "http://127.0.0.1:8000"


def make_request(url, method="GET", data=None, token=None):
    headers = {"Content-Type": "application/json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    body = json.dumps(data).encode("utf-8") if data is not None else None
    req = urllib.request.Request(url, data=body, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req) as res:
            res_body = res.read().decode("utf-8")
            return res.status, json.loads(res_body) if res_body else None
    except urllib.error.HTTPError as e:
        err_body = e.read().decode("utf-8")
        try:
            return e.code, json.loads(err_body)
        except Exception:
            return e.code, err_body


def run_tests():
    print("=" * 60)
    print("ATTENDX NOTIFICATION SYSTEM — FULL VERIFICATION SUITE")
    print("=" * 60)

    # Login as Admin first
    status, admin_auth = make_request(
        f"{BASE_URL}/api/auth/login",
        method="POST",
        data={"email": "admin@attendx.com", "password": "AdminPassword123!"}
    )
    assert status == 200, f"Admin login failed: {admin_auth}"
    admin_token = admin_auth["access_token"]
    print(" Admin logged in successfully.")

    # Fetch subjects catalog
    status, subjects = make_request(f"{BASE_URL}/api/subjects", token=admin_token)
    assert status == 200 and len(subjects) >= 2, "Subjects not found"
    sub_1 = subjects[0]
    sub_2 = subjects[1]
    print(f" Catalog subjects available: {sub_1['code']}, {sub_2['code']}")

    # ----------------------------------------------------
    # TEST 1: New Student Registration & Welcome Notification
    # ----------------------------------------------------
    unique_suffix = str(uuid.uuid4())[:8]
    student_a_email = f"student_a_{unique_suffix}@student.com"
    reg_data = {
        "full_name": f"Alice Student {unique_suffix}",
        "email": student_a_email,
        "password": "Password123!",
        "student_id": f"SID_{unique_suffix}",
        "department": "Computer Science",
        "year": 3,
        "section": "A"
    }
    status, reg_res = make_request(f"{BASE_URL}/api/auth/register", method="POST", data=reg_data)
    assert status == 201, f"Student A registration failed: {reg_res}"
    student_a_token = reg_res["access_token"]
    student_a_id = reg_res["user"]["id"]
    print(f" TEST 1 Passed: Student A registered ({student_a_email})")

    # Check unread count for Student A (should be 1 from Welcome notification)
    status, count_res = make_request(f"{BASE_URL}/api/notifications/unread-count", token=student_a_token)
    assert status == 200 and count_res["count"] == 1, f"Expected 1 unread welcome notification, got: {count_res}"

    status, notifs = make_request(f"{BASE_URL}/api/notifications", token=student_a_token)
    assert status == 200 and len(notifs) == 1, f"Expected 1 notification, got: {len(notifs)}"
    welcome_notif = notifs[0]
    assert welcome_notif["type"] == "system", f"Expected system type, got: {welcome_notif['type']}"
    assert "Welcome to AttendX" in welcome_notif["title"], f"Expected welcome title, got: {welcome_notif['title']}"
    print(f"   Welcome notification verified: '{welcome_notif['title']}'")

    # ----------------------------------------------------
    # TEST 2: Student Enrolls in Subjects -> Dynamic Enrollment Notification
    # ----------------------------------------------------
    enroll_data = {"subject_ids": [sub_1["id"], sub_2["id"]]}
    status, enroll_res = make_request(
        f"{BASE_URL}/api/subjects/enroll-batch",
        method="POST",
        data=enroll_data,
        token=student_a_token
    )
    assert status == 201, f"Enrollment failed: {enroll_res}"
    print(f" TEST 2 Passed: Student A enrolled in 2 subjects: {enroll_res['message']}")

    # ----------------------------------------------------
    # TEST 3: Student Opens Bell -> Notifications Appear
    # ----------------------------------------------------
    status, notifs = make_request(f"{BASE_URL}/api/notifications", token=student_a_token)
    assert status == 200 and len(notifs) == 2, f"Expected 2 notifications, got {len(notifs)}"
    enroll_notif = notifs[0]  # Newest first
    assert enroll_notif["type"] == "enrollment", f"Expected enrollment type, got {enroll_notif['type']}"
    assert "2 subjects" in enroll_notif["message"], f"Expected dynamic count in message: {enroll_notif['message']}"
    assert enroll_notif["is_read"] is False, "New notification should be unread"
    print(f" TEST 3 Passed: Bell dropdown receives latest notifications: '{enroll_notif['title']}' - '{enroll_notif['message']}'")

    # ----------------------------------------------------
    # TEST 4 & 5: Student Clicks Notification -> Read State & Count Update
    # ----------------------------------------------------
    status, read_res = make_request(
        f"{BASE_URL}/api/notifications/{enroll_notif['id']}/read",
        method="PATCH",
        token=student_a_token
    )
    assert status == 200 and read_res["is_read"] is True, f"Failed to mark as read: {read_res}"

    status, count_res = make_request(f"{BASE_URL}/api/notifications/unread-count", token=student_a_token)
    assert status == 200 and count_res["count"] == 1, f"Expected unread count 1, got {count_res['count']}"
    print(f" TEST 4 & 5 Passed: Single notification marked read. Unread count decreased to {count_res['count']}.")

    # ----------------------------------------------------
    # TEST 6: Mark All as Read
    # ----------------------------------------------------
    status, read_all_res = make_request(
        f"{BASE_URL}/api/notifications/read-all",
        method="PATCH",
        token=student_a_token
    )
    assert status == 200, f"Mark all failed: {read_all_res}"

    status, count_res = make_request(f"{BASE_URL}/api/notifications/unread-count", token=student_a_token)
    assert status == 200 and count_res["count"] == 0, f"Expected 0 unread, got {count_res['count']}"
    print(f" TEST 6 Passed: Mark all as read cleared badge to {count_res['count']}.")

    # ----------------------------------------------------
    # TEST 7 & 8: Attendance Marked & Low Attendance Warning Trigger
    # ----------------------------------------------------
    today_str = datetime.date.today().isoformat()
    # Mark absent for sub_1 -> 0 / 1 = 0% (< 75% threshold)
    att_data = {
        "subject_id": sub_1["id"],
        "attendance_date": today_str,
        "records": [{"student_id": student_a_id, "status": "absent"}]
    }
    status, mark_res = make_request(f"{BASE_URL}/api/attendance", method="POST", data=att_data, token=admin_token)
    assert status == 201, f"Mark attendance failed: {mark_res}"

    # Student A fetches notifications now
    status, notifs = make_request(f"{BASE_URL}/api/notifications", token=student_a_token)
    assert status == 200, "Failed to get notifications"
    types = [n["type"] for n in notifs]
    assert "attendance" in types, f"Expected attendance notification in {types}"
    assert "low_attendance" in types, f"Expected low_attendance warning in {types}"

    att_notif = next(n for n in notifs if n["type"] == "attendance")
    low_notif = next(n for n in notifs if n["type"] == "low_attendance")
    assert "Absent" in att_notif["message"] and sub_1["code"] in att_notif["message"], f"Unexpected message: {att_notif['message']}"
    assert "below the 75% threshold" in low_notif["message"], f"Unexpected low attendance message: {low_notif['message']}"
    print(f" TEST 7 Passed: Attendance notification received: '{att_notif['message']}'")
    print(f" TEST 8 Passed: Low attendance warning received: '{low_notif['message']}'")

    # ----------------------------------------------------
    # TEST 9: Persistence Test Across Separate Requests
    # ----------------------------------------------------
    status, notifs_second_call = make_request(f"{BASE_URL}/api/notifications", token=student_a_token)
    assert status == 200 and len(notifs_second_call) == len(notifs), "Notifications did not persist identically"
    print(" TEST 9 Passed: Notifications persist accurately in database.")

    # ----------------------------------------------------
    # TEST 10: Isolation: Student B Cannot See Student A's Notifications
    # ----------------------------------------------------
    student_b_email = f"student_b_{unique_suffix}@student.com"
    reg_b = {
        "full_name": f"Bob Student {unique_suffix}",
        "email": student_b_email,
        "password": "Password123!",
        "student_id": f"SID_B_{unique_suffix}",
    }
    status, reg_b_res = make_request(f"{BASE_URL}/api/auth/register", method="POST", data=reg_b)
    assert status == 201, "Student B registration failed"
    student_b_token = reg_b_res["access_token"]

    status, b_notifs = make_request(f"{BASE_URL}/api/notifications", token=student_b_token)
    assert status == 200, "Failed to get Student B notifications"
    for bn in b_notifs:
        assert bn["user_id"] == reg_b_res["user"]["id"], "Student B received someone else's notification!"
        assert bn["id"] != enroll_notif["id"], "Student B sees Student A's enrollment notification!"
    print(f" TEST 10 Passed: Student B is completely isolated from Student A's {len(notifs)} notifications.")

    # ----------------------------------------------------
    # TEST 11: Security & Ownership: Student B Cannot Read Student A's Notification
    # ----------------------------------------------------
    status, bad_read = make_request(
        f"{BASE_URL}/api/notifications/{enroll_notif['id']}/read",
        method="PATCH",
        token=student_b_token
    )
    assert status in (403, 404), f"Security violation: Student B was able to access Student A's notification! Status: {status}"
    print(f" TEST 11 Passed: Unauthorized access to another user's notification correctly rejected with HTTP {status}.")

    # ----------------------------------------------------
    # TEST 12: Duplicate Prevention
    # ----------------------------------------------------
    count_before = len(notifs)
    # Marking the exact same attendance record again should not duplicate the attendance notification
    status, mark_again = make_request(f"{BASE_URL}/api/attendance", method="POST", data=att_data, token=admin_token)
    assert status == 201
    status, notifs_after = make_request(f"{BASE_URL}/api/notifications", token=student_a_token)
    assert len(notifs_after) == count_before, f"Duplicate notification was created! Before: {count_before}, After: {len(notifs_after)}"
    print(f" TEST 12 Passed: Duplicate notifications properly prevented on re-marking existing attendance.")

    print("=" * 60)
    print("ALL 12 NOTIFICATION TESTS PASSED SUCCESSFULLY! ")
    print("=" * 60)


if __name__ == "__main__":
    run_tests()
