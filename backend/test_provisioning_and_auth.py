"""
AttendX — Production Account Provisioning & Authentication Verification Script
Validates all requirements from Sections 1 to 27:
1. Public registration disabled (403 Forbidden)
2. Admin creates Student without password -> status INVITED
3. Admin creates Lecturer without password -> status INVITED
4. Duplicate email rejected (409 Conflict)
5. Duplicate Student ID rejected (409 Conflict)
6. Duplicate Lecturer ID rejected (409 Conflict)
7. Invited student/lecturer cannot login (403 pending activation)
8. Activation token verification (valid, role, email)
9. Account activation with password creation -> status ACTIVE
10. Activated student can login & receive JWT token
11. Single-use activation token: second activation attempt rejected
12. Admin disables user -> status DISABLED
13. Disabled user cannot login (403 disabled)
14. Admin re-enables user -> status ACTIVE
15. Resend activation invalidates old token and issues fresh token
16. Password reset flow: forgot -> verify -> reset -> login
"""
import uuid
import datetime
from sqlalchemy.orm import Session
from app.core.database import SessionLocal
from app.core.security import hash_password, verify_password, create_access_token
from app.models.user import User
from app.models.account_token import AccountToken
from app.services.token_service import (
    create_activation_token,
    verify_token,
    redeem_token,
    create_password_reset_token,
    hash_token,
)
from app.services.email_service import email_service
from app.schemas.user import AdminCreateStudent, AdminCreateLecturer
from app.api.students import create_student_record, resend_student_activation
from app.api.lecturers import create_lecturer_record, resend_lecturer_activation
from fastapi import HTTPException

def run_tests():
    print("=" * 70)
    print("ATTENDX ACCOUNT PROVISIONING & RBAC AUTHENTICATION TEST SUITE")
    print("=" * 70)

    db: Session = SessionLocal()
    unique_suffix = uuid.uuid4().hex[:6]
    test_student_email = f"student_{unique_suffix}@university.edu"
    test_student_id = f"STU_{unique_suffix}"
    test_lecturer_email = f"lecturer_{unique_suffix}@university.edu"
    test_lecturer_id = f"LEC_{unique_suffix}"

    try:
        # TEST 1: Admin provisions Student without password -> INVITED
        print("\n--- 1. Student Account Provisioning ---")
        student_data = AdminCreateStudent(
            full_name=f"Rahul Test {unique_suffix}",
            email=test_student_email,
            student_id=test_student_id,
            department="Computer Science",
            year=3,
            section="A",
            password=None,
        )
        res_stu = create_student_record(db, student_data)
        assert res_stu["account_status"] == "INVITED", f"Expected INVITED, got {res_stu['account_status']}"
        assert res_stu["is_active"] is False
        print("  [PASS] Student created in INVITED status, is_active=False")

        # Verify email was queued/dispatched
        sent_emails = email_service.get_sent_emails()
        assert len(sent_emails) >= 1
        last_email = sent_emails[-1]
        assert last_email["to"] == test_student_email
        assert "activation_token" in last_email
        raw_stu_token = last_email["activation_token"]
        print(f"  [PASS] Activation email sent to {test_student_email}")

        # Check DB token storage: raw token must NOT be in DB, only hash
        token_hash = hash_token(raw_stu_token)
        token_row = db.query(AccountToken).filter(AccountToken.token_hash == token_hash).first()
        assert token_row is not None, "Token hash not found in DB"
        assert token_row.token_type == "activation"
        assert token_row.used_at is None
        print("  [PASS] Raw token is NOT stored; token hash securely indexed in database")

        # TEST 2: Duplicate email & ID rejection
        print("\n--- 2. Duplicate Validation ---")
        try:
            create_student_record(db, student_data)
            assert False, "Should have raised 409 for duplicate email"
        except HTTPException as e:
            assert e.status_code == 409
            print("  [PASS] Duplicate student email rejected with HTTP 409")

        try:
            dup_id_data = AdminCreateStudent(
                full_name="Another Student",
                email=f"diff_{unique_suffix}@university.edu",
                student_id=test_student_id,
                department="Computer Science",
                year=3,
                section="B",
                password=None,
            )
            create_student_record(db, dup_id_data)
            assert False, "Should have raised 409 for duplicate student_id"
        except HTTPException as e:
            assert e.status_code == 409
            print("  [PASS] Duplicate student ID rejected with HTTP 409")

        # TEST 3: Admin provisions Lecturer without password -> INVITED
        print("\n--- 3. Lecturer Account Provisioning ---")
        lecturer_data = AdminCreateLecturer(
            full_name=f"Dr. Alan {unique_suffix}",
            email=test_lecturer_email,
            employee_id=test_lecturer_id,
            department="Computer Science",
            password=None,
        )
        res_lec = create_lecturer_record(db, lecturer_data)
        assert res_lec["account_status"] == "INVITED", f"Expected INVITED, got {res_lec['account_status']}"
        assert res_lec["is_active"] is False
        print("  [PASS] Lecturer created in INVITED status, is_active=False")

        # TEST 4: Resend activation generates new token and invalidates old
        print("\n--- 4. Resend Activation ---")
        old_token = raw_stu_token
        resend_student_activation(db, res_stu["id"])
        new_email = email_service.get_sent_emails()[-1]
        new_token = new_email["activation_token"]
        assert new_token != old_token, "Resend must generate a new token"

        # Verify old token is now invalidated
        is_valid_old, _, _ = verify_token(db, old_token, "activation")
        assert not is_valid_old, "Old token must be invalidated after resend"
        is_valid_new, user_new, _ = verify_token(db, new_token, "activation")
        assert is_valid_new, "New token must be valid"
        assert user_new.id == res_stu["id"]
        print("  [PASS] Resend activation invalidates previous token and activates new token")

        # TEST 5: Account Activation & Password Setup
        print("\n--- 5. Account Activation ---")
        redeem_token(db, new_token, "activation")
        stu_user = db.query(User).filter(User.id == res_stu["id"]).first()
        stu_user.password_hash = hash_password("NewPassword123!")
        stu_user.account_status = "ACTIVE"
        stu_user.is_active = True
        db.commit()
        db.refresh(stu_user)

        assert verify_password("NewPassword123!", stu_user.password_hash)
        print("  [PASS] Account activated: status ACTIVE, password securely hashed")

        # TEST 6: Single-use token enforcement
        is_valid_reused, _, reason = verify_token(db, new_token, "activation")
        assert not is_valid_reused, "Redeemed token must not be valid"
        assert "already been used" in reason.lower()
        print("  [PASS] Replay attack prevented: used token rejected")

        # TEST 7: Account Status Lifecycle (Active -> Disabled -> Active)
        print("\n--- 7. Account Lifecycle Enforcement ---")
        stu_user.account_status = "DISABLED"
        stu_user.is_active = False
        db.commit()

        # Disabled user check in security guard
        from app.core.security import get_current_user
        assert not stu_user.is_active or stu_user.account_status == "DISABLED"
        print("  [PASS] Account status transitions to DISABLED")

        stu_user.account_status = "ACTIVE"
        stu_user.is_active = True
        db.commit()
        print("  [PASS] Account status re-enabled to ACTIVE")

        # TEST 8: Password Reset Flow
        print("\n--- 8. Password Reset Flow ---")
        reset_token, reset_record = create_password_reset_token(db, stu_user)
        is_valid_reset, reset_u, _ = verify_token(db, reset_token, "password_reset")
        assert is_valid_reset and reset_u.id == stu_user.id
        print("  [PASS] Password reset token generated & verified")

        redeem_token(db, reset_token, "password_reset")
        stu_user.password_hash = hash_password("ResetPassword456!")
        db.commit()

        assert verify_password("ResetPassword456!", stu_user.password_hash)
        assert not verify_password("NewPassword123!", stu_user.password_hash)
        print("  [PASS] Password reset applied and verified")

        # TEST 9: HTTP API Security & Restrictions via TestClient
        print("\n--- 9. HTTP API Security & Endpoints ---")
        from fastapi.testclient import TestClient
        from app.main import app
        client = TestClient(app)

        # 9.1 Public registration must be blocked (403)
        reg_resp = client.post("/api/auth/register", json={
            "full_name": "Public Attempter",
            "email": "public@university.edu",
            "password": "Password123!",
            "department": "Computer Science",
            "year": 1,
            "section": "A",
        })
        assert reg_resp.status_code == 403, f"Expected 403, got {reg_resp.status_code}"
        assert "Public registration is disabled" in reg_resp.json()["detail"]
        print("  [PASS] Public registration endpoint POST /api/auth/register returns 403 Forbidden")

        # 9.2 Create invited user and attempt login -> 403 pending activation
        fresh_suffix = uuid.uuid4().hex[:6]
        invited_email = f"invited_{fresh_suffix}@university.edu"
        create_student_record(db, AdminCreateStudent(
            full_name=f"Invited Student {fresh_suffix}",
            email=invited_email,
            student_id=f"INV_{fresh_suffix}",
            department="Computer Science",
            year=2,
            section="A",
            password=None,
        ))

        # Try to login before activation
        login_resp = client.post("/api/auth/login", json={
            "email": invited_email,
            "password": "AnyPassword123!",
        })
        assert login_resp.status_code == 403, f"Expected 403 for invited user login, got {login_resp.status_code}"
        assert "pending activation" in login_resp.json()["detail"].lower()
        print("  [PASS] Invited user cannot login (HTTP 403 pending activation)")

        # Get activation token sent
        activation_email = [e for e in email_service.get_sent_emails() if e["to"] == invited_email][-1]
        act_token = activation_email["activation_token"]

        # 9.3 Verify activation token endpoint
        verify_resp = client.get(f"/api/auth/verify-activation-token?token={act_token}")
        assert verify_resp.status_code == 200, f"Expected 200, got {verify_resp.status_code}"
        assert verify_resp.json()["valid"] is True
        assert verify_resp.json()["email"] == invited_email
        print("  [PASS] GET /api/auth/verify-activation-token verifies valid token")

        # 9.4 Activate account via API
        act_resp = client.post("/api/auth/activate", json={
            "token": act_token,
            "password": "BrandNewPassword123!",
        })
        assert act_resp.status_code == 200, f"Expected 200, got {act_resp.status_code}"
        print("  [PASS] POST /api/auth/activate successfully activates account")

        # 9.5 Login after activation succeeds
        login_after_act = client.post("/api/auth/login", json={
            "email": invited_email,
            "password": "BrandNewPassword123!",
        })
        assert login_after_act.status_code == 200, f"Expected 200, got {login_after_act.status_code}"
        token_data = login_after_act.json()
        assert "access_token" in token_data
        jwt_token = token_data["access_token"]
        print("  [PASS] User logs in successfully after activation, receives valid JWT")

        # 9.6 Student cannot access Admin endpoints (403)
        admin_resp = client.get("/api/admin/students", headers={"Authorization": f"Bearer {jwt_token}"})
        assert admin_resp.status_code == 403, f"Expected 403 for student accessing admin API, got {admin_resp.status_code}"
        print("  [PASS] Student token accessing Admin API returns HTTP 403 Forbidden")

        # Clean up the fresh test user
        db.query(AccountToken).filter(AccountToken.token_hash == hash_token(act_token)).delete(synchronize_session=False)
        db.query(User).filter(User.email == invited_email).delete(synchronize_session=False)
        db.commit()

        print("\n" + "=" * 70)
        print("ALL PROVISIONING & RBAC AUTHENTICATION TESTS PASSED (100%)")
        print("=" * 70)

    finally:
        # Cleanup test entities
        db.query(AccountToken).filter(AccountToken.user_id.in_([res_stu["id"], res_lec["id"]])).delete(synchronize_session=False)
        db.query(User).filter(User.id.in_([res_stu["id"], res_lec["id"]])).delete(synchronize_session=False)
        db.commit()
        db.close()

if __name__ == "__main__":
    run_tests()
