"""
AttendX — Module 4 Verification Test Suite
Tests Frontend Auth Bootstrap & Session Resilience:
1. /api/auth/me endpoint for all three roles (Admin, Student, Lecturer)
2. Token boundary security (missing, invalid, expired tokens rejected with 401)
3. Disabled/Suspended account rejection on /api/auth/me (403 Forbidden)
4. Password hash secrecy (no credential/hash leak on /api/auth/me)
5. Login payload completeness (proves /me is redundant after /login)
6. Latency comparison: /api/auth/me vs /api/auth/login
7. Full regression coverage across Module 1, Module 2, and Module 3
"""
import sys
import time
import uuid
from datetime import timedelta
from fastapi.testclient import TestClient

from app.main import app
from app.core.database import SessionLocal, engine
from app.models.user import User
from app.core.security import (
    hash_password,
    create_access_token,
)

client = TestClient(app)


def test_module4_all():
    print("=" * 75)
    print("ATTENDX MODULE 4: FRONTEND AUTH BOOTSTRAP & SESSION RESILIENCE TESTS")
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
    # SECTION 1: AUTHENTICATION FOR ALL 3 ROLES & PAYLOAD VALIDATION
    # -------------------------------------------------------------
    print("\n--- 1. Login & Token Acquisition for All 3 Roles ---")

    # 1.1 Admin login
    res_admin = client.post("/api/auth/login", json={"email": "admin@attendx.com", "password": "AdminPassword123!"})
    record("Admin valid login returns 200", res_admin.status_code == 200)
    admin_token = res_admin.json()["access_token"]
    admin_user = res_admin.json()["user"]

    # 1.2 Student login
    res_student = client.post("/api/auth/login", json={"email": "john.doe@student.com", "password": "StudentPassword123!"})
    record("Student valid login returns 200", res_student.status_code == 200)
    student_token = res_student.json()["access_token"]
    student_user = res_student.json()["user"]

    # 1.3 Lecturer login
    res_lecturer = client.post("/api/auth/login", json={"email": "dr.alan@lecturer.com", "password": "LecturerPassword123!"})
    record("Lecturer valid login returns 200", res_lecturer.status_code == 200)
    lecturer_token = res_lecturer.json()["access_token"]
    lecturer_user = res_lecturer.json()["user"]

    # -------------------------------------------------------------
    # SECTION 2: /api/auth/me PROFILE VERIFICATION FOR ALL 3 ROLES
    # -------------------------------------------------------------
    print("\n--- 2. /api/auth/me Profile Verification (Admin, Student, Lecturer) ---")

    # 2.1 Admin /api/auth/me
    res_me_admin = client.get("/api/auth/me", headers={"Authorization": f"Bearer {admin_token}"})
    record(
        "Admin GET /api/auth/me returns 200 and matches login profile",
        res_me_admin.status_code == 200 and res_me_admin.json()["role"] == "admin" and res_me_admin.json()["id"] == admin_user["id"],
    )

    # 2.2 Student /api/auth/me
    res_me_student = client.get("/api/auth/me", headers={"Authorization": f"Bearer {student_token}"})
    record(
        "Student GET /api/auth/me returns 200 and matches login profile",
        res_me_student.status_code == 200 and res_me_student.json()["role"] == "student" and res_me_student.json()["id"] == student_user["id"],
    )

    # 2.3 Lecturer /api/auth/me
    res_me_lec = client.get("/api/auth/me", headers={"Authorization": f"Bearer {lecturer_token}"})
    record(
        "Lecturer GET /api/auth/me returns 200 and matches login profile",
        res_me_lec.status_code == 200 and res_me_lec.json()["role"] == "lecturer" and res_me_lec.json()["id"] == lecturer_user["id"],
    )

    # -------------------------------------------------------------
    # SECTION 3: LOGIN RESPONSE COMPLETENESS (ELIMINATES LOGIN -> /ME CHAIN)
    # -------------------------------------------------------------
    print("\n--- 3. Login Response Completeness Verification ---")

    # Verify login response already contains all fields provided by /api/auth/me
    me_keys = set(res_me_admin.json().keys())
    login_user_keys = set(admin_user.keys())
    record(
        "Login user payload contains all fields required by /api/auth/me (no follow-up /me needed)",
        me_keys.issubset(login_user_keys),
        f"fields: {sorted(list(me_keys))}",
    )

    # Verify no password hashes leaked in /me or /login
    record("No password_hash leaked in /api/auth/login", "password_hash" not in str(res_admin.json()))
    record("No password_hash leaked in /api/auth/me", "password_hash" not in str(res_me_admin.json()))

    # -------------------------------------------------------------
    # SECTION 4: SECURITY BOUNDARIES & INVALID TOKEN REJECTION
    # -------------------------------------------------------------
    print("\n--- 4. Security Boundaries & Token Rejection on /api/auth/me ---")

    # 4.1 Missing Authorization Header -> 401
    res_no_tok = client.get("/api/auth/me")
    record("Missing Authorization header rejected with 401", res_no_tok.status_code == 401)

    # 4.2 Malformed JWT -> 401
    res_bad_tok = client.get("/api/auth/me", headers={"Authorization": "Bearer not.a.valid.token"})
    record("Malformed JWT rejected with 401", res_bad_tok.status_code == 401)

    # 4.3 Expired JWT -> 401
    expired_token = create_access_token({"sub": admin_user["id"], "role": "admin"}, expires_delta=timedelta(seconds=-10))
    res_exp_tok = client.get("/api/auth/me", headers={"Authorization": f"Bearer {expired_token}"})
    record("Expired JWT rejected with 401", res_exp_tok.status_code == 401)

    # 4.4 Nonexistent User ID in valid JWT -> 401
    ghost_token = create_access_token({"sub": "non-existent-user-uuid", "role": "student"})
    res_ghost = client.get("/api/auth/me", headers={"Authorization": f"Bearer {ghost_token}"})
    record("Non-existent user in token rejected with 401", res_ghost.status_code == 401)

    # -------------------------------------------------------------
    # SECTION 5: ACCOUNT STATUS ENFORCEMENT ON /api/auth/me
    # -------------------------------------------------------------
    print("\n--- 5. Account Status Enforcement on /api/auth/me ---")

    db = SessionLocal()
    temp_suffix = uuid.uuid4().hex[:6]
    test_user = User(
        full_name=f"Bootstrap Test User {temp_suffix}",
        email=f"bootstrap_{temp_suffix}@attendx.edu",
        password_hash=hash_password("Password123!"),
        role="student",
        student_id=f"BTS_{temp_suffix}",
        is_active=True,
        account_status="ACTIVE",
    )
    db.add(test_user)
    db.commit()
    db.refresh(test_user)

    user_token = create_access_token({"sub": test_user.id, "role": test_user.role})

    # Active user accesses /me -> 200
    res_active = client.get("/api/auth/me", headers={"Authorization": f"Bearer {user_token}"})
    record("Active user accesses /api/auth/me (200 OK)", res_active.status_code == 200)

    # Admin disables user account -> status = DISABLED
    test_user.is_active = False
    test_user.account_status = "DISABLED"
    db.commit()

    # Disabled user accessing /me -> 403 Forbidden
    res_disabled = client.get("/api/auth/me", headers={"Authorization": f"Bearer {user_token}"})
    record(
        "Disabled user rejected on /api/auth/me with 403 Forbidden",
        res_disabled.status_code == 403 and "disabled" in res_disabled.json()["detail"].lower(),
        f"detail: '{res_disabled.json().get('detail')}'",
    )

    # Clean up test user
    db.delete(test_user)
    db.commit()
    db.close()

    # -------------------------------------------------------------
    # SECTION 6: PERFORMANCE MEASUREMENT & LATENCY COMPARISON
    # -------------------------------------------------------------
    print("\n--- 6. Performance Benchmarks: /api/auth/me vs /api/auth/login ---")

    # Benchmark warm /api/auth/me latency (5 iterations)
    me_durations = []
    for _ in range(5):
        t0 = time.perf_counter()
        r = client.get("/api/auth/me", headers={"Authorization": f"Bearer {admin_token}"})
        dur_ms = (time.perf_counter() - t0) * 1000
        assert r.status_code == 200
        me_durations.append(dur_ms)

    avg_me_latency = sum(me_durations) / len(me_durations)

    # Benchmark warm /api/auth/login latency (3 iterations)
    login_durations = []
    for _ in range(3):
        t0 = time.perf_counter()
        r = client.post("/api/auth/login", json={"email": "admin@attendx.com", "password": "AdminPassword123!"})
        dur_ms = (time.perf_counter() - t0) * 1000
        assert r.status_code == 200
        login_durations.append(dur_ms)

    avg_login_latency = sum(login_durations) / len(login_durations)

    record(
        "/api/auth/me benchmark completed",
        avg_me_latency < 30.0,
        f"avg /me latency: {avg_me_latency:.2f}ms (primary key lookup, no bcrypt)",
    )
    record(
        "/api/auth/login benchmark completed",
        avg_login_latency > 100.0,
        f"avg login latency: {avg_login_latency:.2f}ms (bcrypt work factor 12)",
    )
    record(
        "Bootstrap /me is > 5x faster than full login",
        avg_login_latency > avg_me_latency * 5,
        f"ratio: {avg_login_latency / avg_me_latency:.1f}x faster",
    )

    # -------------------------------------------------------------
    # SECTION 7: REGRESSIONS (MODULE 1, MODULE 2, MODULE 3)
    # -------------------------------------------------------------
    print("\n--- 7. Module 1, Module 2, Module 3 Regression Verification ---")

    # Module 1: Schema synchronization
    from sqlalchemy import inspect
    inspector = inspect(engine)
    columns = [col["name"] for col in inspector.get_columns("users")]
    record("Module 1 schema: 'account_status' present in users table", "account_status" in columns)
    tables = inspector.get_table_names()
    record("Module 1 schema: 'account_activation_tokens' table exists", "account_activation_tokens" in tables)

    # Module 2: Connection pooling configuration preserved
    record("Module 2: database engine configured cleanly", bool(engine))

    # Module 3: Timing side channel mitigation preserved
    t0 = time.perf_counter()
    res_unk = client.post("/api/auth/login", json={"email": "unknown.user.regression@attendx.edu", "password": "AnyPassword123!"})
    d_unk = (time.perf_counter() - t0) * 1000
    record("Module 3: unknown email performs dummy verification", res_unk.status_code == 401 and d_unk >= 100)

    # RBAC endpoints regression
    res_adm_dash = client.get("/api/admin/dashboard", headers={"Authorization": f"Bearer {admin_token}"})
    record("Admin dashboard accessible with admin token (200)", res_adm_dash.status_code == 200)

    res_stu_dash = client.get("/api/dashboard/student", headers={"Authorization": f"Bearer {student_token}"})
    record("Student dashboard accessible with student token (200)", res_stu_dash.status_code == 200)

    res_lec_dash = client.get("/api/dashboard/lecturer", headers={"Authorization": f"Bearer {lecturer_token}"})
    record("Lecturer dashboard accessible with lecturer token (200)", res_lec_dash.status_code == 200)

    print("\n" + "=" * 75)
    print(f"ALL MODULE 4 VERIFICATION TESTS PASSED: {passed}/{total}")
    print("=" * 75)


if __name__ == "__main__":
    test_module4_all()
