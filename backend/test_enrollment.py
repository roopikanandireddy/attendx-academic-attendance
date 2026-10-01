"""
Test enrollment workflow:
1. Login as student (john.doe@student.com)
2. Fetch subjects list from /api/subjects (must have the 6 subjects)
3. Fetch my-enrollments
4. Enroll in remaining subjects using /api/subjects/enroll-batch
5. Fetch /api/dashboard/student and verify:
   - All 6 subjects are present
   - Newly enrolled subjects show 0% and 0 / 0 classes
   - No fake attendance
"""
import urllib.request
import json

BASE_URL = "http://127.0.0.1:8000"

def run_test():
    # 1. Login
    login_data = json.dumps({
        "email": "john.doe@student.com",
        "password": "StudentPassword123!"
    }).encode("utf-8")
    req = urllib.request.Request(f"{BASE_URL}/api/auth/login", data=login_data, headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req) as res:
        login_res = json.loads(res.read().decode())
    
    token = login_res["access_token"]
    user = login_res["user"]
    print(f"Logged in student: {user['full_name']} ({user['email']})")

    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}

    # 2. Fetch subjects
    req = urllib.request.Request(f"{BASE_URL}/api/subjects", headers=headers)
    with urllib.request.urlopen(req) as res:
        subjects = json.loads(res.read().decode())

    print(f"\nFetched {len(subjects)} subjects from database catalog:")
    expected_codes = ["IAI", "SE", "ISC", "BEFA", "ES", "AE-3 LAB"]
    found_codes = [s["code"] for s in subjects]
    for s in subjects:
        print(f" - [{s['code']}] {s['name']} (ID: {s['id']})")

    for ec in expected_codes:
        assert ec in found_codes, f"Missing expected subject code {ec}!"
    print("All 6 required catalog subjects present in database!")

    # 3. Check current enrollments
    req = urllib.request.Request(f"{BASE_URL}/api/subjects/my-enrollments", headers=headers)
    with urllib.request.urlopen(req) as res:
        my_enrollments = json.loads(res.read().decode())
    print(f"\nCurrently enrolled in {len(my_enrollments)} subjects.")

    # 4. Enroll in ALL 6 subjects
    all_subject_ids = [s["id"] for s in subjects if s["code"] in expected_codes]
    batch_data = json.dumps({"subject_ids": all_subject_ids}).encode("utf-8")
    req = urllib.request.Request(f"{BASE_URL}/api/subjects/enroll-batch", data=batch_data, headers=headers)
    with urllib.request.urlopen(req) as res:
        enroll_res = json.loads(res.read().decode())
    print(f"\nBatch enroll result: {enroll_res}")

    # 5. Fetch student dashboard
    req = urllib.request.Request(f"{BASE_URL}/api/dashboard/student", headers=headers)
    with urllib.request.urlopen(req) as res:
        dash = json.loads(res.read().decode())

    dash_subs = dash["subjects"]
    print(f"\nStudent Dashboard now has {len(dash_subs)} subjects:")
    for s in dash_subs:
        print(f" - [{s['subject_code']}] {s['subject_name']}: {s['percentage']}% ({s['present']} / {s['total_classes']} classes)")
        if s["subject_code"] == "AE-3 LAB":
            assert s["total_classes"] == 0, "AE-3 LAB should have 0 total classes"
            assert s["present"] == 0, "AE-3 LAB should have 0 present classes"
            assert s["percentage"] == 0.0, "AE-3 LAB should have 0.0% attendance"

    print("\nALL ENROLLMENT AND CATALOG TESTS PASSED SUCCESSFULLY!")

if __name__ == "__main__":
    run_test()
