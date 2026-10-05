"""
AttendX — Automated Verification Suite for Secure Administrator Accounts
Executes comprehensive testing of:
1. Authentication (valid, invalid, nonexistent)
2. JWT tokens and claims
3. Role-based authorization & endpoint isolation
4. Data leak prevention (no passwords, no hashes)
5. Session renewal & auth persistence (/api/auth/me)
6. Regression verification across Student, Lecturer, and Admin systems
"""
import sys
import os
import json
import urllib.request
import urllib.error

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__))))

from app.services.admin_provisioning import get_admin_credentials_from_env, ADMIN_ACCOUNTS
from app.core.security import decode_token

BASE_URL = "http://127.0.0.1:8000"


def make_request(method, path, data=None, token=None):
    url = f"{BASE_URL}{path}"
    headers = {"Content-Type": "application/json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    
    encoded_data = json.dumps(data).encode("utf-8") if data else None
    req = urllib.request.Request(url, data=encoded_data, headers=headers, method=method)
    
    try:
        with urllib.request.urlopen(req) as resp:
            body = resp.read().decode("utf-8")
            return resp.status, json.loads(body) if body else {}
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8")
        try:
            return e.code, json.loads(body)
        except Exception:
            return e.code, {"raw": body}


def run_tests():
    print("=" * 70)
    print("ATTENDX SECURE ADMINISTRATOR VERIFICATION SUITE")
    print("=" * 70)

    creds = get_admin_credentials_from_env()
    assert len(creds) >= 2, f"Expected 2 admin credentials in environment, found {len(creds)}"

    target_admins = [acc["email"] for acc in ADMIN_ACCOUNTS]

    for idx, email in enumerate(target_admins, 1):
        print(f"\n--- Testing Admin Account {idx}: {email} ---")
        pwd = creds.get(email)
        assert pwd, f"Password not found for {email}"

        # 1. Valid email + valid password -> HTTP 200
        status, data = make_request("POST", "/api/auth/login", {"email": email, "password": pwd})
        assert status == 200, f"Expected 200, got {status}: {data}"
        print("  [PASS] 1. Valid email + password returns HTTP 200")

        # 2. JWT generated successfully
        assert "access_token" in data and len(data["access_token"]) > 30
        token = data["access_token"]
        print("  [PASS] 2. JWT access token generated successfully")

        # 3. JWT role = admin
        claims = decode_token(token)
        assert claims.get("role") == "admin", f"Expected role admin in JWT, got {claims.get('role')}"
        assert data.get("user", {}).get("role") == "admin"
        assert data.get("user", {}).get("account_status") == "ACTIVE"
        assert data.get("user", {}).get("is_active") is True
        print("  [PASS] 3. JWT role claims & user object confirmed: role='admin', status='ACTIVE'")

        # 4. Admin dashboard access succeeds
        status, dash_data = make_request("GET", "/api/admin/dashboard", token=token)
        assert status == 200, f"Expected 200 on admin dashboard, got {status}"
        assert "total_students" in dash_data or "metrics" in dash_data
        print("  [PASS] 4. Admin dashboard access succeeds (HTTP 200)")

        # 5. Admin-only API access succeeds
        s_status, _ = make_request("GET", "/api/admin/students/summary", token=token)
        l_status, _ = make_request("GET", "/api/admin/lecturers/summary", token=token)
        sub_status, _ = make_request("GET", "/api/admin/subjects/summary", token=token)
        assert s_status == 200 and l_status == 200 and sub_status == 200
        print("  [PASS] 5. Admin-only API access succeeds (/admin/students, /admin/lecturers, /admin/subjects)")

        # 6. Student-only endpoints are not incorrectly granted (HTTP 403)
        stu_status, _ = make_request("GET", "/api/dashboard/student", token=token)
        assert stu_status == 403, f"Expected 403 for admin on student-only endpoint, got {stu_status}"
        print("  [PASS] 6. Student-only endpoint correctly forbidden to Admin (HTTP 403)")

        # 7. Lecturer-only endpoints are not incorrectly granted (HTTP 403)
        lec_status, _ = make_request("GET", "/api/dashboard/lecturer", token=token)
        assert lec_status == 403, f"Expected 403 for admin on lecturer-only endpoint, got {lec_status}"
        print("  [PASS] 7. Lecturer-only endpoint correctly forbidden to Admin (HTTP 403)")

        # 8. Wrong password -> HTTP 401
        status, err_data = make_request("POST", "/api/auth/login", {"email": email, "password": "WrongPassword123!"})
        assert status == 401, f"Expected 401 for wrong password, got {status}"
        assert err_data.get("detail") == "Invalid email or password"
        print("  [PASS] 8. Wrong password returns generic HTTP 401 ('Invalid email or password')")

        # 9. Unknown email -> HTTP 401
        status, err_data = make_request("POST", "/api/auth/login", {"email": "unknown_admin@attendx.com", "password": "AnyPassword123!"})
        assert status == 401, f"Expected 401 for unknown email, got {status}"
        assert err_data.get("detail") == "Invalid email or password"
        print("  [PASS] 9. Unknown email returns identical generic HTTP 401 (prevents user enumeration)")

        # 10. Password is NOT present in response
        data_str = json.dumps(data)
        assert pwd not in data_str, "CRITICAL: Plaintext password found in login response!"
        assert "password" not in data.get("user", {})
        print("  [PASS] 10. Password is NOT present in API response")

        # 11 & 12. Password hash is NOT present in API response
        assert "password_hash" not in data.get("user", {})
        assert "$2b$" not in data_str
        print("  [PASS] 11 & 12. Password hash ($2b$) is NOT present in API response")

        # 13. Refreshing Admin dashboard preserves authentication correctly
        me_status, me_data = make_request("GET", "/api/auth/me", token=token)
        assert me_status == 200, f"Expected 200 on /api/auth/me, got {me_status}"
        assert me_data.get("email") == email
        assert me_data.get("role") == "admin"
        print("  [PASS] 13. Identity persistence (/api/auth/me) succeeds and preserves admin identity")

        # 14. Unauthenticated request without token rejected
        unauth_status, _ = make_request("GET", "/api/admin/dashboard")
        assert unauth_status in (401, 403), f"Expected 401/403 for missing token, got {unauth_status}"
        print("  [PASS] 14. Protected admin endpoints reject unauthenticated requests")

    # REGRESSION TESTS
    print("\n" + "=" * 70)
    print("ATTENDX REGRESSION TEST SUITE (Student, Lecturer, Admin & Operations)")
    print("=" * 70)

    # Student Login & Dashboard
    s_status, s_data = make_request("POST", "/api/auth/login", {"email": "john.doe@student.com", "password": "StudentPassword123!"})
    assert s_status == 200, f"Student login failed: {s_status}"
    s_token = s_data["access_token"]
    assert s_data["user"]["role"] == "student"
    s_dash_status, _ = make_request("GET", "/api/dashboard/student", token=s_token)
    assert s_dash_status == 200
    print("  [PASS] Student login & student dashboard operational")

    # Lecturer Login & Dashboard
    l_status, l_data = make_request("POST", "/api/auth/login", {"email": "dr.alan@lecturer.com", "password": "LecturerPassword123!"})
    assert l_status == 200, f"Lecturer login failed: {l_status}"
    l_token = l_data["access_token"]
    assert l_data["user"]["role"] == "lecturer"
    l_dash_status, _ = make_request("GET", "/api/dashboard/lecturer", token=l_token)
    assert l_dash_status == 200
    print("  [PASS] Lecturer login & lecturer dashboard operational")

    # Student / Lecturer blocked from Admin endpoints
    s_on_admin, _ = make_request("GET", "/api/admin/dashboard", token=s_token)
    assert s_on_admin == 403
    l_on_admin, _ = make_request("GET", "/api/admin/dashboard", token=l_token)
    assert l_on_admin == 403
    print("  [PASS] Students and Lecturers strictly blocked from Admin API (HTTP 403)")

    # System operations: Notifications, Subjects
    notif_status, _ = make_request("GET", "/api/notifications/unread-count", token=s_token)
    assert notif_status == 200
    subj_status, _ = make_request("GET", "/api/subjects", token=s_token)
    assert subj_status == 200
    print("  [PASS] Core system operations (Notifications, Subjects) operational")

    print("\n" + "=" * 70)
    print("ALL ADMINISTRATOR PROVISIONING & REGRESSION TESTS PASSED (100%)")
    print("=" * 70)

if __name__ == "__main__":
    run_tests()
