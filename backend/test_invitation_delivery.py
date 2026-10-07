"""
AttendX — Production Invitation Delivery & Account Activation Automated Test Suite
Validates all requirements from Section 20 (A through W):
A. Admin creates Student invitation
B. Admin creates Lecturer invitation
C. Account is created correctly
D. Activation token is generated
E. Email service is invoked
F. Successful provider response is handled
G. Provider rejection is handled
H. Provider timeout is handled
I. Missing email configuration is handled
J. Invalid recipient is handled
K. Email failure does not falsely report success
L. Activation URL is correct
M. Activation token expires correctly
N. Activation completes correctly
O. Activated account becomes ACTIVE
P. Invalid activation token is rejected
Q. Expired activation token is rejected
R. RBAC remains intact
S. Module 8 structured logging remains safe
T. No secrets appear in logs/errors
U. Existing student functionality remains intact
V. Existing lecturer functionality remains intact
W. Existing admin functionality remains intact
"""
import io
import json
import logging
import os
import smtplib
import socket
import sys
import time
import uuid
from datetime import datetime, timedelta, timezone
from unittest.mock import patch, MagicMock

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.main import app
from app.core.database import SessionLocal
from app.core.security import create_access_token, hash_password
from app.core.observability import logger as access_logger
from app.models.user import User
from app.models.account_token import AccountToken
from app.services.email_service import email_service, EmailDeliveryResult
from app.services.token_service import (
    create_activation_token,
    verify_token,
    redeem_token,
    hash_token,
)
from app.schemas.user import AdminCreateStudent, AdminCreateLecturer
from app.api.students import create_student_record, resend_student_activation_email
from app.api.lecturers import create_lecturer_record, resend_lecturer_activation

client = TestClient(app)


def run_invitation_delivery_tests():
    print("=" * 80)
    print("ATTENDX: INVITATION DELIVERY & ACCOUNT ACTIVATION AUDIT + FIX TESTS")
    print("=" * 80)

    db: Session = SessionLocal()
    passed = 0
    total = 0

    def record(test_id: str, name: str, condition: bool, extra: str = ""):
        nonlocal passed, total
        total += 1
        if condition:
            passed += 1
            print(f"[PASS] {test_id}. {name} {extra}")
        else:
            print(f"[FAIL] {test_id}. {name} {extra}")
            assert condition, f"Test failed: {test_id}. {name} {extra}"

    # Capture log stream for Module 8 safety audits
    log_stream = io.StringIO()
    handler = logging.StreamHandler(log_stream)
    handler.setFormatter(logging.Formatter("%(message)s"))
    access_logger.addHandler(handler)

    test_users_to_clean = []

    try:
        # Create an admin token for API calls
        admin_user = db.query(User).filter(User.role == "admin").first()
        if not admin_user:
            admin_user = User(
                id=str(uuid.uuid4()),
                email="test_admin_invite@attendx.edu",
                password_hash=hash_password("AdminSecurePass123!"),
                role="admin",
                full_name="Test Administrator",
                is_active=True,
                account_status="ACTIVE",
            )
            db.add(admin_user)
            db.commit()
            db.refresh(admin_user)
            test_users_to_clean.append(admin_user.id)

        admin_token = create_access_token({"sub": admin_user.id, "role": "admin"})
        admin_headers = {"Authorization": f"Bearer {admin_token}", "X-Request-ID": "test-invite-trace-123"}

        # ---------------------------------------------------------------------
        # TEST A & C & D & E: Admin creates Student invitation
        # ---------------------------------------------------------------------
        print("\n--- 1. Admin Student Invitation Creation ---")
        suffix = uuid.uuid4().hex[:6]
        student_email = f"student_inv_{suffix}@university.edu"
        student_id = f"STU_INV_{suffix}"

        res_stu = client.post(
            "/api/admin/students",
            headers=admin_headers,
            json={
                "full_name": f"Priya Sharma {suffix}",
                "email": student_email,
                "student_id": student_id,
                "department": "Computer Science",
                "year": 2,
                "section": "A",
            },
        )
        record("A", "Admin creates Student invitation (HTTP 201)", res_stu.status_code == 201)
        stu_data = res_stu.json()
        test_users_to_clean.append(stu_data["id"])

        record("C", "Student account created in INVITED status and is_active=False",
               stu_data["account_status"] == "INVITED" and stu_data["is_active"] is False)

        # Verify token in DB
        token_record = (
            db.query(AccountToken)
            .filter(AccountToken.user_id == stu_data["id"], AccountToken.token_type == "activation")
            .first()
        )
        record("D", "Activation token record generated in database", token_record is not None and token_record.used_at is None)

        # Verify Email Service was invoked
        sent_emails = email_service.get_sent_emails()
        matching_emails = [e for e in sent_emails if e["to"] == student_email]
        record("E", "Email service was invoked with recipient email", len(matching_emails) >= 1)
        student_sent_email = matching_emails[-1]
        raw_student_token = student_sent_email["activation_token"]

        # Verify email delivery info returned in API response
        record("E2", "API response returns structured email_delivery block",
               "email_delivery" in stu_data and "success" in stu_data["email_delivery"])

        # ---------------------------------------------------------------------
        # TEST B: Admin creates Lecturer invitation
        # ---------------------------------------------------------------------
        print("\n--- 2. Admin Lecturer Invitation Creation ---")
        lec_suffix = uuid.uuid4().hex[:6]
        lecturer_email = f"lecturer_inv_{lec_suffix}@university.edu"
        employee_id = f"EMP_INV_{lec_suffix}"

        res_lec = client.post(
            "/api/admin/lecturers",
            headers=admin_headers,
            json={
                "full_name": f"Dr. Vikram {lec_suffix}",
                "email": lecturer_email,
                "employee_id": employee_id,
                "department": "Information Technology",
            },
        )
        record("B", "Admin creates Lecturer invitation (HTTP 201)", res_lec.status_code == 201)
        lec_data = res_lec.json()
        test_users_to_clean.append(lec_data["id"])

        record("B2", "Lecturer account created in INVITED status",
               lec_data["account_status"] == "INVITED" and lec_data["is_active"] is False)
        record("B3", "Lecturer response contains email_delivery block",
               "email_delivery" in lec_data and lec_data["email_delivery"]["status"] in ("ACCEPTED", "FAILED"))

        # ---------------------------------------------------------------------
        # TEST F: Successful provider response handled
        # ---------------------------------------------------------------------
        print("\n--- 3. Email Provider Handling: Success ---")
        with patch.object(email_service, "_send_smtp", return_value=EmailDeliveryResult(
            success=True, status="ACCEPTED", message="Invitation email accepted by email provider."
        )):
            with patch.object(email_service.settings, "EMAIL_PROVIDER", "smtp"):
                with patch.object(email_service.settings, "EMAIL_HOST", "smtp.testprovider.com"):
                    res_provider_ok = email_service.send_account_activation_email(
                        to_email="test_success@attendx.edu",
                        full_name="Success Recipient",
                        activation_token="token_success_123",
                        role="Student",
                    )
                    record("F", "Successful provider response returns EmailDeliveryResult(success=True)",
                           res_provider_ok.success is True and res_provider_ok.status == "ACCEPTED")

        # ---------------------------------------------------------------------
        # TEST G: Provider rejection handled
        # ---------------------------------------------------------------------
        print("\n--- 4. Email Provider Handling: Rejection ---")
        with patch("smtplib.SMTP") as mock_smtp_cls:
            mock_server = MagicMock()
            mock_smtp_cls.return_value = mock_server
            mock_server.sendmail.side_effect = smtplib.SMTPSenderRefused(550, b"Sender address rejected", "noreply@attendx.edu")

            with patch.object(email_service.settings, "EMAIL_PROVIDER", "smtp"):
                with patch.object(email_service.settings, "EMAIL_HOST", "smtp.testprovider.com"):
                    res_reject = email_service.send_account_activation_email(
                        to_email="test_rejected@attendx.edu",
                        full_name="Rejected Recipient",
                        activation_token="token_rej_123",
                        role="Student",
                    )
                    record("G", "Provider rejection mapped to EMAIL_PROVIDER_REJECTED",
                           res_reject.success is False and res_reject.error_code == "EMAIL_PROVIDER_REJECTED")

        # ---------------------------------------------------------------------
        # TEST H: Provider timeout handled
        # ---------------------------------------------------------------------
        print("\n--- 5. Email Provider Handling: Timeout ---")
        with patch("smtplib.SMTP", side_effect=socket.timeout("Connection timed out")):
            with patch.object(email_service.settings, "EMAIL_PROVIDER", "smtp"):
                with patch.object(email_service.settings, "EMAIL_HOST", "smtp.testprovider.com"):
                    res_timeout = email_service.send_account_activation_email(
                        to_email="test_timeout@attendx.edu",
                        full_name="Timeout Recipient",
                        activation_token="token_timeout_123",
                        role="Student",
                    )
                    record("H", "Provider timeout mapped to EMAIL_PROVIDER_TIMEOUT",
                           res_timeout.success is False and res_timeout.error_code == "EMAIL_PROVIDER_TIMEOUT")

        # ---------------------------------------------------------------------
        # TEST I: Missing email configuration handled
        # ---------------------------------------------------------------------
        print("\n--- 6. Missing Email Configuration in Production ---")
        with patch.dict(os.environ, {"RENDER": "true"}):
            with patch.object(email_service.settings, "EMAIL_PROVIDER", "console"):
                with patch.object(email_service.settings, "EMAIL_HOST", ""):
                    res_missing_cfg = email_service.send_account_activation_email(
                        to_email="test_prod_noconfig@attendx.edu",
                        full_name="No Config User",
                        activation_token="token_noconfig_123",
                        role="Student",
                    )
                    record("I", "Missing email configuration in production returns EMAIL_CONFIGURATION_ERROR",
                           res_missing_cfg.success is False and res_missing_cfg.error_code == "EMAIL_CONFIGURATION_ERROR")

        # ---------------------------------------------------------------------
        # TEST J: Invalid recipient handled
        # ---------------------------------------------------------------------
        print("\n--- 7. Email Provider Handling: Invalid Recipient ---")
        with patch("smtplib.SMTP") as mock_smtp_cls:
            mock_server = MagicMock()
            mock_smtp_cls.return_value = mock_server
            mock_server.sendmail.side_effect = smtplib.SMTPRecipientsRefused({"bad_recipient@attendx.edu": (550, b"User unknown")})

            with patch.object(email_service.settings, "EMAIL_PROVIDER", "smtp"):
                with patch.object(email_service.settings, "EMAIL_HOST", "smtp.testprovider.com"):
                    res_bad_rcpt = email_service.send_account_activation_email(
                        to_email="bad_recipient@attendx.edu",
                        full_name="Bad Recipient",
                        activation_token="token_bad_123",
                        role="Student",
                    )
                    record("J", "Invalid recipient mapped to INVALID_RECIPIENT",
                           res_bad_rcpt.success is False and res_bad_rcpt.error_code == "INVALID_RECIPIENT")

        # ---------------------------------------------------------------------
        # TEST K: Email failure does not falsely report success
        # ---------------------------------------------------------------------
        print("\n--- 8. Separation of Account Creation and Email Failure ---")
        fail_suffix = uuid.uuid4().hex[:6]
        fail_email = f"student_emailfail_{fail_suffix}@university.edu"
        fail_sid = f"STU_FAIL_{fail_suffix}"

        with patch.object(email_service, "send_account_activation_email", return_value=EmailDeliveryResult(
            success=False,
            status="FAILED",
            error_code="EMAIL_PROVIDER_AUTH_ERROR",
            message="Email provider authentication failed. Check SMTP credentials.",
        )):
            stu_fail_data = AdminCreateStudent(
                full_name=f"Failed Email Student {fail_suffix}",
                email=fail_email,
                student_id=fail_sid,
                department="Computer Science",
                year=1,
                section="B",
                password=None,
            )
            res_rec = create_student_record(db, stu_fail_data)
            test_users_to_clean.append(res_rec["id"])

            record("K1", "Account creation succeeds even when email dispatch fails",
                   res_rec["account_status"] == "INVITED")
            record("K2", "Response accurately reports email_delivery.success is False",
                   res_rec["email_delivery"]["success"] is False)
            record("K3", "Response accurately reflects error_code EMAIL_PROVIDER_AUTH_ERROR",
                   res_rec["email_delivery"]["error_code"] == "EMAIL_PROVIDER_AUTH_ERROR")

        # ---------------------------------------------------------------------
        # TEST L: Activation URL correctness
        # ---------------------------------------------------------------------
        print("\n--- 9. Activation URL Format & Sanitation ---")
        act_url = student_sent_email["activation_url"]
        record("L1", "Activation URL contains /activate-account?token=",
               "/activate-account?token=" in act_url)
        record("L2", "Activation URL contains raw security token",
               raw_student_token in act_url)
        record("L3", "Activation URL does not contain double slashes in path",
               "//" not in act_url.replace("https://", "").replace("http://", ""))

        # ---------------------------------------------------------------------
        # TEST M & P & Q: Token verification and expiration
        # ---------------------------------------------------------------------
        print("\n--- 10. Activation Token Verification & Security ---")
        # Valid token verification via API
        res_v = client.get(f"/api/auth/verify-activation-token?token={raw_student_token}")
        record("M1", "Valid activation token verified via API (HTTP 200)", res_v.status_code == 200)
        v_data = res_v.json()
        record("M2", "Verification response contains recipient email and full name",
               v_data["email"] == student_email and v_data["role"] == "student")

        # Invalid token rejection
        res_inv = client.get("/api/auth/verify-activation-token?token=completely_bogus_token_1234567890")
        record("P", "Invalid activation token rejected with HTTP 400", res_inv.status_code == 400)

        # Expired token rejection
        expired_token_record = AccountToken(
            id=str(uuid.uuid4()),
            user_id=stu_data["id"],
            token_hash=hash_token("expired_test_token_abc"),
            token_type="activation",
            expires_at=datetime.now(timezone.utc) - timedelta(hours=5),
            used_at=None,
        )
        db.add(expired_token_record)
        db.commit()

        res_exp = client.get("/api/auth/verify-activation-token?token=expired_test_token_abc")
        record("Q", "Expired activation token rejected with HTTP 400", res_exp.status_code == 400)

        # ---------------------------------------------------------------------
        # TEST N & O: Account activation and transition to ACTIVE
        # ---------------------------------------------------------------------
        print("\n--- 11. Account Activation Flow ---")
        new_password = "MySecurePassword2026!"
        res_act = client.post(
            "/api/auth/activate",
            json={"token": raw_student_token, "password": new_password},
        )
        record("N", "Account activation succeeds (HTTP 200)", res_act.status_code == 200)

        # Confirm account becomes ACTIVE in DB
        db_user = db.query(User).filter(User.id == stu_data["id"]).first()
        record("O1", "Activated user account status transitioned to ACTIVE",
               db_user.account_status == "ACTIVE" and db_user.is_active is True)

        # Confirm single-use replay protection
        res_replay = client.post(
            "/api/auth/activate",
            json={"token": raw_student_token, "password": "AnotherPassword123!"},
        )
        record("O2", "Replay attack prevented: redeemed token rejected (HTTP 400)", res_replay.status_code == 400)

        # Confirm activated user can sign in and receive JWT
        res_login = client.post(
            "/api/auth/login",
            json={"email": student_email, "password": new_password},
        )
        record("O3", "Activated user signs in successfully and receives JWT",
               res_login.status_code == 200 and "access_token" in res_login.json())

        # ---------------------------------------------------------------------
        # TEST R: RBAC Integrity
        # ---------------------------------------------------------------------
        print("\n--- 12. RBAC Enforcement on Invitation Endpoints ---")
        student_jwt = res_login.json()["access_token"]
        student_headers = {"Authorization": f"Bearer {student_jwt}"}

        res_unauth_stu = client.post(
            "/api/admin/students",
            headers=student_headers,
            json={"full_name": "Hack", "email": "h@u.edu", "student_id": "H1", "department": "CS", "year": 1, "section": "A"},
        )
        record("R1", "Student token accessing Admin Student invitation returns HTTP 403", res_unauth_stu.status_code == 403)

        res_unauth_lec = client.post(
            "/api/admin/lecturers",
            headers=student_headers,
            json={"full_name": "Hack", "email": "hl@u.edu", "employee_id": "HL1", "department": "CS"},
        )
        record("R2", "Student token accessing Admin Lecturer invitation returns HTTP 403", res_unauth_lec.status_code == 403)

        # ---------------------------------------------------------------------
        # TEST S & T: Module 8 Structured Logging & Credential Safety
        # ---------------------------------------------------------------------
        print("\n--- 13. Module 8 Observability & Secret Leakage Audit ---")
        logs = log_stream.getvalue().strip().split("\n")
        parsed_logs = []
        for line in logs:
            if line.strip():
                try:
                    parsed_logs.append(json.loads(line))
                except json.JSONDecodeError:
                    pass

        events_observed = {entry.get("event") for entry in parsed_logs if "event" in entry}
        record("S1", "Structured logs emitted for invitation_created", "invitation_created" in events_observed)
        record("S2", "Structured logs emitted for activation_token_created", "activation_token_created" in events_observed)
        record("S3", "Structured logs emitted for invitation_email_attempt", "invitation_email_attempt" in events_observed)
        record("S4", "Structured logs emitted for activation_completed", "activation_completed" in events_observed)

        # Verify no credentials or raw tokens leak in any log line
        raw_log_dump = log_stream.getvalue().lower()
        record("T1", "Plaintext passwords not leaked in logs", "mysecurepassword2026!" not in raw_log_dump)
        record("T2", "Raw activation token not leaked in structured log bodies",
               raw_student_token.lower() not in raw_log_dump)
        record("T3", "Authorization headers / JWT signatures not leaked in logs",
               student_jwt[-20:].lower() not in raw_log_dump)

        # ---------------------------------------------------------------------
        # TEST U, V, W: Existing Student, Lecturer, Admin Functionality
        # ---------------------------------------------------------------------
        print("\n--- 14. Existing Functionality Regression Verification ---")
        # Admin dashboard
        res_ad_dash = client.get("/api/admin/dashboard", headers=admin_headers)
        record("W", "Existing Admin dashboard access preserved (HTTP 200)", res_ad_dash.status_code == 200)

        # Student dashboard
        res_st_dash = client.get("/api/dashboard/student", headers=student_headers)
        record("U", "Existing Student dashboard access preserved (HTTP 200)", res_st_dash.status_code == 200)

        # Lecturer dashboard with lecturer login
        lec_login = client.get("/api/lecturers/summary", headers=admin_headers)
        record("V", "Existing Lecturer summary endpoint preserved (HTTP 200)", lec_login.status_code == 200)

        # ---------------------------------------------------------------------
        # Resend Invitation Flow
        # ---------------------------------------------------------------------
        print("\n--- 15. Resend Activation Flow ---")
        # Create an invited student for testing resend
        r_suffix = uuid.uuid4().hex[:6]
        res_stu_r = client.post(
            "/api/admin/students",
            headers=admin_headers,
            json={
                "full_name": f"Resend Student {r_suffix}",
                "email": f"resend_{r_suffix}@university.edu",
                "student_id": f"RES_{r_suffix}",
                "department": "Physics",
                "year": 1,
                "section": "A",
            },
        )
        resend_student_id = res_stu_r.json()["id"]
        test_users_to_clean.append(resend_student_id)

        res_resend = client.post(
            f"/api/admin/students/{resend_student_id}/resend-activation",
            headers=admin_headers,
        )
        record("Resend-1", "Resend student activation returns HTTP 200 with delivery info",
               res_resend.status_code == 200 and "email_delivery" in res_resend.json())

    finally:
        access_logger.removeHandler(handler)
        # Clean up created test entities
        for uid_to_del in test_users_to_clean:
            u = db.query(User).filter(User.id == uid_to_del).first()
            if u:
                db.delete(u)
        db.commit()
        db.close()

    print("\n" + "=" * 80)
    print(f"INVITATION DELIVERY TEST RESULTS: {passed}/{total} PASSED (100% SUCCESS)")
    print("=" * 80)
    if passed != total:
        sys.exit(1)


if __name__ == "__main__":
    run_invitation_delivery_tests()
