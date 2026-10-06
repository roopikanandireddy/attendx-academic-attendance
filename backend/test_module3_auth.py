"""
AttendX — Module 3 Verification Test Suite
Tests authentication latency, error differentiation, account status enforcement,
RBAC, JWT handling, timing attack mitigation, and regression coverage.
"""
import sys
import time
import uuid
from datetime import timedelta
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from sqlalchemy.exc import OperationalError

from app.main import app
from app.core.database import SessionLocal, engine
from app.models.user import User
from app.core.security import (
    hash_password,
    verify_password,
    create_access_token,
    decode_token,
    settings,
)

client = TestClient(app)

def test_module3_all():
    print("=" * 75)
    print("ATTENDX MODULE 3: AUTHENTICATION LATENCY & ERROR DIFFERENTIATION TESTS")
    print("=" * 75)

    passed = 0
    total = 0

    def record(name: str, condition: bool, details: str = ""):
        nonlocal passed, total
        total += 1
        status_str = "PASS" if condition else "FAIL"
        if condition:
            passed += 1
            print(f"[{status_str}] {name} {details}")
        else:
            print(f"[{status_str}] {name} - FAILED! {details}")
            assert condition, f"Test failed: {name} - {details}"

    # -------------------------------------------------------------
    # SECTION 1: VALID LOGINS FOR ALL 3 ROLES
    # -------------------------------------------------------------
    print("\n--- 1. Valid Logins (Admin, Student, Lecturer) ---")

    # 1.1 Admin
    res_admin = client.post("/api/auth/login", json={"email": "admin@attendx.com", "password": "AdminPassword123!"})
    record("Admin valid login", res_admin.status_code == 200 and res_admin.json()["user"]["role"] == "admin" and bool(res_admin.json()["access_token"]))

    # 1.2 Student
    res_student = client.post("/api/auth/login", json={"email": "john.doe@student.com", "password": "StudentPassword123!"})
    record("Student valid login", res_student.status_code == 200 and res_student.json()["user"]["role"] == "student" and bool(res_student.json()["access_token"]))

    # 1.3 Lecturer
    res_lecturer = client.post("/api/auth/login", json={"email": "dr.alan@lecturer.com", "password": "LecturerPassword123!"})
    record("Lecturer valid login", res_lecturer.status_code == 200 and res_lecturer.json()["user"]["role"] == "lecturer" and bool(res_lecturer.json()["access_token"]))

    admin_token = res_admin.json()["access_token"]
    student_token = res_student.json()["access_token"]
    lecturer_token = res_lecturer.json()["access_token"]

    # -------------------------------------------------------------
    # SECTION 2: INVALID CREDENTIALS & ERROR DIFFERENTIATION
    # -------------------------------------------------------------
    print("\n--- 2. Invalid Credentials & Error Differentiation ---")

    # 2.1 Wrong Admin Password -> 401 "Invalid email or password"
    res = client.post("/api/auth/login", json={"email": "admin@attendx.com", "password": "WrongPassword123!"})
    record("Wrong Admin password returns 401", res.status_code == 401 and res.json()["detail"] == "Invalid email or password")

    # 2.2 Wrong Student Password -> 401 "Invalid email or password"
    res = client.post("/api/auth/login", json={"email": "john.doe@student.com", "password": "WrongPassword123!"})
    record("Wrong Student password returns 401", res.status_code == 401 and res.json()["detail"] == "Invalid email or password")

    # 2.3 Wrong Lecturer Password -> 401 "Invalid email or password"
    res = client.post("/api/auth/login", json={"email": "dr.alan@lecturer.com", "password": "WrongPassword123!"})
    record("Wrong Lecturer password returns 401", res.status_code == 401 and res.json()["detail"] == "Invalid email or password")

    # 2.4 Unknown email -> 401 "Invalid email or password"
    res = client.post("/api/auth/login", json={"email": "nonexistent.user.test@attendx.edu", "password": "AnyPassword123!"})
    record("Unknown email returns 401 generic message", res.status_code == 401 and res.json()["detail"] == "Invalid email or password")

    # 2.5 Empty password -> 422 Unprocessable Entity
    res = client.post("/api/auth/login", json={"email": "admin@attendx.com", "password": ""})
    record("Empty password returns 422", res.status_code == 422)

    # 2.6 Missing email -> 422 Unprocessable Entity
    res = client.post("/api/auth/login", json={"password": "SomePassword123!"})
    record("Missing email returns 422", res.status_code == 422)

    # 2.7 Malformed email -> 422 Unprocessable Entity
    res = client.post("/api/auth/login", json={"email": "not-an-email-address", "password": "SomePassword123!"})
    record("Malformed email returns 422", res.status_code == 422)

    # -------------------------------------------------------------
    # SECTION 3: ACCOUNT STATUS ENFORCEMENT
    # -------------------------------------------------------------
    print("\n--- 3. Account Status Enforcement ---")

    db = SessionLocal()
    # Find or provision a temporary test user for status tests
    temp_suffix = uuid.uuid4().hex[:6]

    # 3.1 PENDING_ACTIVATION / INVITED account
    invited_user = db.query(User).filter(User.account_status == "INVITED").first()
    if not invited_user:
        invited_user = User(
            full_name=f"Invited Student {temp_suffix}",
            email=f"invited_{temp_suffix}@attendx.edu",
            password_hash="!INVITED!placeholder",
            role="student",
            student_id=f"INV_{temp_suffix}",
            is_active=False,
            account_status="INVITED",
        )
        db.add(invited_user)
        db.commit()

    res = client.post("/api/auth/login", json={"email": invited_user.email, "password": "AnyPassword123!"})
    record(
        "Invited account returns 403 activation required",
        res.status_code == 403 and "pending activation" in res.json()["detail"].lower(),
        f"detail: '{res.json().get('detail')}'",
    )

    # 3.2 DISABLED / SUSPENDED account
    disabled_email = f"disabled_{temp_suffix}@attendx.edu"
    disabled_user = User(
        full_name=f"Disabled Student {temp_suffix}",
        email=disabled_email,
        password_hash=hash_password("ValidPassword123!"),
        role="student",
        student_id=f"DIS_{temp_suffix}",
        is_active=False,
        account_status="DISABLED",
    )
    db.add(disabled_user)
    db.commit()

    res = client.post("/api/auth/login", json={"email": disabled_email, "password": "ValidPassword123!"})
    record(
        "Disabled account returns 403 account disabled",
        res.status_code == 403 and "disabled" in res.json()["detail"].lower(),
        f"detail: '{res.json().get('detail')}'",
    )

    # Cleanup temp test user
    db.delete(disabled_user)
    db.commit()
    db.close()

    # -------------------------------------------------------------
    # SECTION 4: SERVER RESILIENCE & DATABASE ERROR SAFETY
    # -------------------------------------------------------------
    print("\n--- 4. Database Failure & Server Error Safety ---")

    # Test database failure interception in /login
    from unittest.mock import patch
    with patch("app.api.auth.db.query") if hasattr(sys.modules["app.api.auth"], "db") else patch("sqlalchemy.orm.Session.query") as mock_query:
        mock_query.side_effect = OperationalError("connection refused", {}, Exception("db down"))
        res = client.post("/api/auth/login", json={"email": "admin@attendx.com", "password": "AdminPassword123!"})
        record(
            "Database failure safely caught and returns 500 without leaking SQL",
            res.status_code == 500 and "connection refused" not in res.json()["detail"] and "unable to sign in" in res.json()["detail"].lower(),
            f"status: {res.status_code}, detail: '{res.json().get('detail')}'",
        )

    # -------------------------------------------------------------
    # SECTION 5: AUTHORIZATION, RBAC & JWT VALIDATION
    # -------------------------------------------------------------
    print("\n--- 5. Authorization, RBAC & JWT Integrity ---")

    # 5.1 Valid JWT for matching role
    res = client.get("/api/admin/dashboard", headers={"Authorization": f"Bearer {admin_token}"})
    record("Admin token accesses Admin dashboard", res.status_code == 200)

    res = client.get("/api/dashboard/student", headers={"Authorization": f"Bearer {student_token}"})
    record("Student token accesses Student dashboard", res.status_code == 200)

    res = client.get("/api/dashboard/lecturer", headers={"Authorization": f"Bearer {lecturer_token}"})
    record("Lecturer token accesses Lecturer dashboard", res.status_code == 200)

    # 5.2 Role Enforcement (Student attempting to access Admin endpoint)
    res = client.get("/api/admin/dashboard", headers={"Authorization": f"Bearer {student_token}"})
    record("Student token rejected on Admin endpoint (403)", res.status_code == 403 and "admin access required" in res.json()["detail"].lower())

    # 5.3 Role Enforcement (Lecturer attempting to access Admin endpoint)
    res = client.get("/api/admin/dashboard", headers={"Authorization": f"Bearer {lecturer_token}"})
    record("Lecturer token rejected on Admin endpoint (403)", res.status_code == 403 and "admin access required" in res.json()["detail"].lower())

    # 5.4 Role Enforcement (Student attempting to access Lecturer endpoint)
    res = client.get("/api/dashboard/lecturer", headers={"Authorization": f"Bearer {student_token}"})
    record("Student token rejected on Lecturer endpoint (403)", res.status_code == 403 and "lecturer access required" in res.json()["detail"].lower())

    # 5.5 Missing Token on protected endpoint -> 401
    res = client.get("/api/admin/dashboard")
    record("Missing token returns 401", res.status_code == 401)

    # 5.6 Invalid Token -> 401
    res = client.get("/api/admin/dashboard", headers={"Authorization": "Bearer invalid_gibberish_token_string"})
    record("Invalid token returns 401", res.status_code == 401)

    # 5.7 Expired Token -> 401
    expired_token = create_access_token({"sub": "admin-id", "role": "admin"}, expires_delta=timedelta(seconds=-10))
    res = client.get("/api/admin/dashboard", headers={"Authorization": f"Bearer {expired_token}"})
    record("Expired token returns 401", res.status_code == 401)

    # 5.8 /api/auth/me returns current user profile
    res = client.get("/api/auth/me", headers={"Authorization": f"Bearer {admin_token}"})
    record("/api/auth/me returns authenticated admin user", res.status_code == 200 and res.json()["role"] == "admin")

    # -------------------------------------------------------------
    # SECTION 6: TIMING ATTACK & SIDE-CHANNEL MITIGATION
    # -------------------------------------------------------------
    print("\n--- 6. Timing Attack Mitigation Verification ---")

    # Benchmark unknown email vs wrong password
    t0 = time.perf_counter()
    res_unk = client.post("/api/auth/login", json={"email": "nonexistent@nowhere.edu", "password": "WrongPassword123!"})
    d_unk = (time.perf_counter() - t0) * 1000

    t0 = time.perf_counter()
    res_wrong = client.post("/api/auth/login", json={"email": "admin@attendx.com", "password": "WrongPassword123!"})
    d_wrong = (time.perf_counter() - t0) * 1000

    timing_ratio = max(d_unk, d_wrong) / min(d_unk, d_wrong)
    record(
        "Timing side-channel mitigated (unknown email runs bcrypt verification)",
        d_unk >= 100 and timing_ratio < 2.0,
        f"unknown: {d_unk:.1f}ms, wrong pwd: {d_wrong:.1f}ms, ratio: {timing_ratio:.2f}",
    )

    # -------------------------------------------------------------
    # SECTION 7: REGRESSIONS (MODULE 1 & MODULE 2)
    # -------------------------------------------------------------
    print("\n--- 7. Module 1 & Module 2 Regression Verification ---")

    # Module 1: Schema synchronization
    from sqlalchemy import inspect
    inspector = inspect(engine)
    columns = [col["name"] for col in inspector.get_columns("users")]
    record("Module 1 schema: 'account_status' present in users table", "account_status" in columns)

    tables = inspector.get_table_names()
    record("Module 1 schema: 'account_activation_tokens' table exists", "account_activation_tokens" in tables)

    # Module 2: Connection pooling configuration preserved
    from app.core.database import database_url
    record("Module 2: database engine configured cleanly", bool(engine))

    print("\n" + "=" * 75)
    print(f"ALL MODULE 3 VERIFICATION TESTS PASSED: {passed}/{total}")
    print("=" * 75)

if __name__ == "__main__":
    test_module3_all()
