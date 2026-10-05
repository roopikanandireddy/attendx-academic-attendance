"""
AttendX — Token Service
Manages cryptographically secure, single-use, time-limited tokens for account activation
and password resets. Stores only SHA-256 hashes of tokens.
"""
import hashlib
import secrets
from datetime import datetime, timedelta, timezone
from typing import Optional, Tuple
from sqlalchemy.orm import Session
from app.core.config import get_settings
from app.models.account_token import AccountToken
from app.models.user import User

settings = get_settings()


def utcnow():
    return datetime.now(timezone.utc)


def hash_token(raw_token: str) -> str:
    """Compute SHA-256 digest of raw token."""
    return hashlib.sha256(raw_token.strip().encode("utf-8")).hexdigest()


def generate_secure_token() -> str:
    """Generate 256 bits of URL-safe cryptographically random entropy."""
    return secrets.token_urlsafe(32)


def create_activation_token(db: Session, user: User) -> Tuple[str, AccountToken]:
    """
    Generate a new activation token for an invited user, invalidate any
    previous unused activation tokens, and persist the hashed record.
    Returns (raw_token, token_record).
    """
    # Invalidate previous unused activation tokens for this user
    existing_tokens = (
        db.query(AccountToken)
        .filter(
            AccountToken.user_id == user.id,
            AccountToken.token_type == "activation",
            AccountToken.used_at.is_(None),
        )
        .all()
    )
    for t in existing_tokens:
        t.used_at = utcnow()

    raw_token = generate_secure_token()
    token_h = hash_token(raw_token)
    expires_at = utcnow() + timedelta(hours=settings.ACCOUNT_ACTIVATION_TOKEN_EXPIRE_HOURS)

    token_record = AccountToken(
        user_id=user.id,
        token_hash=token_h,
        token_type="activation",
        expires_at=expires_at,
        used_at=None,
    )
    db.add(token_record)
    db.commit()
    db.refresh(token_record)

    return raw_token, token_record


def create_password_reset_token(db: Session, user: User) -> Tuple[str, AccountToken]:
    """
    Generate a new password reset token for an active user, invalidate any
    previous unused reset tokens, and persist the hashed record.
    Returns (raw_token, token_record).
    """
    existing_tokens = (
        db.query(AccountToken)
        .filter(
            AccountToken.user_id == user.id,
            AccountToken.token_type == "password_reset",
            AccountToken.used_at.is_(None),
        )
        .all()
    )
    for t in existing_tokens:
        t.used_at = utcnow()

    raw_token = generate_secure_token()
    token_h = hash_token(raw_token)
    expires_at = utcnow() + timedelta(hours=settings.PASSWORD_RESET_TOKEN_EXPIRE_HOURS)

    token_record = AccountToken(
        user_id=user.id,
        token_hash=token_h,
        token_type="password_reset",
        expires_at=expires_at,
        used_at=None,
    )
    db.add(token_record)
    db.commit()
    db.refresh(token_record)

    return raw_token, token_record


def verify_token(
    db: Session,
    raw_token: str,
    token_type: str = "activation",
) -> Tuple[bool, Optional[User], str]:
    """
    Verify a raw token against stored hash, expiration, and used state.
    Returns (is_valid, user, error_reason).
    """
    if not raw_token or not raw_token.strip():
        return False, None, "Token is required."

    token_h = hash_token(raw_token)
    token_record = (
        db.query(AccountToken)
        .filter(
            AccountToken.token_hash == token_h,
            AccountToken.token_type == token_type,
        )
        .first()
    )

    if not token_record:
        return False, None, "Invalid or unrecognized token."

    if token_record.used_at is not None:
        return False, None, "This token has already been used."

    now = utcnow()
    # Normalize tzinfo if needed
    record_expires = token_record.expires_at
    if record_expires.tzinfo is None:
        record_expires = record_expires.replace(tzinfo=timezone.utc)

    if now > record_expires:
        return False, None, "This token has expired. Please request a new link."

    user = db.query(User).filter(User.id == token_record.user_id).first()
    if not user:
        return False, None, "Associated user account was not found."

    return True, user, ""


def redeem_token(db: Session, raw_token: str, token_type: str = "activation") -> bool:
    """Mark a token as consumed."""
    token_h = hash_token(raw_token)
    token_record = (
        db.query(AccountToken)
        .filter(
            AccountToken.token_hash == token_h,
            AccountToken.token_type == token_type,
            AccountToken.used_at.is_(None),
        )
        .first()
    )
    if token_record:
        token_record.used_at = utcnow()
        db.commit()
        return True
    return False
