"""
AttendX — Secure Production Administrator Account Provisioning Service
Provisions required institutional administrators using secure bcrypt password hashing.
Never exposes plaintext passwords or password hashes.
"""
import os
import sys
from pathlib import Path
from sqlalchemy.orm import Session
from app.core.security import hash_password
from app.models.user import User

ADMIN_ACCOUNTS = [
    {
        "email": "roopikanandireddy@gmail.com",
        "full_name": "Roopika Nandi Reddy",
        "env_var": "ADMIN_ROOPIKA_PASSWORD",
        "fallback_env_var": "ADMIN_1_PASSWORD",
    },
    {
        "email": "srikanthkuruva06@gmail.com",
        "full_name": "Srikanth Kuruva",
        "env_var": "ADMIN_SRIKANTH_PASSWORD",
        "fallback_env_var": "ADMIN_2_PASSWORD",
    },
]


def get_admin_credentials_from_env() -> dict:
    """
    Retrieve configured runtime secrets from backend environment or local .env
    without printing, logging, or exposing them.
    """
    env_path = Path(__file__).resolve().parent.parent.parent / ".env"
    file_vars = {}
    if env_path.exists():
        with open(env_path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    k, v = line.split("=", 1)
                    file_vars[k.strip()] = v.strip().strip("'\"")

    creds = {}
    for acc in ADMIN_ACCOUNTS:
        email = acc["email"].strip().lower()
        pwd = (
            os.getenv(acc["env_var"])
            or os.getenv(acc["fallback_env_var"])
            or file_vars.get(acc["env_var"])
            or file_vars.get(acc["fallback_env_var"])
        )
        if pwd:
            creds[email] = pwd
    return creds


def verify_existing_admins(db: Session) -> list:
    """
    Read-only inspection of required administrator accounts.
    Returns status without modifying any data or exposing secrets.
    """
    status_list = []
    for acc in ADMIN_ACCOUNTS:
        email = acc["email"].strip().lower()
        user = db.query(User).filter(User.email == email).first()
        if user:
            status_list.append({
                "email": email,
                "exists": True,
                "id": user.id,
                "role": user.role,
                "account_status": user.account_status,
                "is_active": user.is_active,
                "has_password_hash": bool(user.password_hash),
            })
        else:
            status_list.append({
                "email": email,
                "exists": False,
                "id": None,
                "role": None,
                "account_status": None,
                "is_active": None,
                "has_password_hash": False,
            })
    return status_list


def provision_admin_accounts(db: Session, passwords: dict = None) -> list:
    """
    Safely provisions or updates the required administrator accounts.
    - Idempotent: avoids duplicates and preserves existing account IDs
    - Preserves existing student and lecturer records
    - Stores ONLY bcrypt password_hash
    - Never logs or exposes raw passwords or password hashes
    """
    passwords = passwords or {}
    env_passwords = get_admin_credentials_from_env()
    results = []

    for acc in ADMIN_ACCOUNTS:
        email = acc["email"].strip().lower()
        full_name = acc["full_name"]

        # Check provided dict, then environment variables
        raw_pwd = passwords.get(email) or env_passwords.get(email)

        existing = db.query(User).filter(User.email == email).first()

        if existing:
            # Preserve existing ID, ensure admin role and ACTIVE state
            existing.role = "admin"
            existing.account_status = "ACTIVE"
            existing.is_active = True
            if raw_pwd:
                existing.password_hash = hash_password(raw_pwd)
            db.commit()
            db.refresh(existing)
            results.append({
                "email": email,
                "action": "preserved_and_verified",
                "id": existing.id,
                "role": existing.role,
                "account_status": existing.account_status,
                "is_active": existing.is_active,
            })
        else:
            if not raw_pwd:
                raise ValueError(
                    f"Password required to provision new admin account: {email}. "
                    f"Supply via environment variable {acc['env_var']} or interactive input."
                )

            new_admin = User(
                email=email,
                full_name=full_name,
                password_hash=hash_password(raw_pwd),
                role="admin",
                account_status="ACTIVE",
                is_active=True,
                department="Administration",
            )
            db.add(new_admin)
            db.commit()
            db.refresh(new_admin)
            results.append({
                "email": email,
                "action": "created",
                "id": new_admin.id,
                "role": new_admin.role,
                "account_status": new_admin.account_status,
                "is_active": new_admin.is_active,
            })

    return results
