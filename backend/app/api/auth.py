from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.security import hash_password, verify_password, create_access_token, get_current_user
from app.models.user import User
from typing import Optional
from fastapi import Query
from app.services.token_service import (
    verify_token,
    redeem_token,
    create_password_reset_token,
)
from app.services.email_service import email_service
from app.schemas.user import (
    UserRegister,
    UserLogin,
    UserUpdate,
    UserResponse,
    TokenResponse,
    AccountActivationRequest,
    TokenVerificationResponse,
    PasswordForgotRequest,
    PasswordResetRequest,
)
from app.services.notification_service import (
    create_welcome_notification,
    create_faculty_welcome_notification,
)

router = APIRouter(prefix="/api/auth", tags=["Authentication"])


@router.post(
    "/register",
    status_code=status.HTTP_403_FORBIDDEN,
    summary="Public registration is disabled",
)
def register(data: UserRegister, db: Session = Depends(get_db)):
    """
    Public registration is strictly disabled in AttendX production provisioning model.
    Student and Lecturer accounts must be provisioned by institution administrators.
    """
    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail="Public registration is disabled. Student and Lecturer accounts are created by your institution administrator.",
    )


@router.post("/login", response_model=TokenResponse, summary="Login with email and password")
def login(data: UserLogin, db: Session = Depends(get_db)):
    """Authenticate user and return JWT token."""
    user = db.query(User).filter(User.email == data.email.lower().strip()).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
        )

    # Check if user account is in INVITED state
    if user.account_status and user.account_status.upper() == "INVITED":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Your account is pending activation. Please check your email for the activation link.",
        )

    if not verify_password(data.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
        )

    if not user.is_active or (user.account_status and user.account_status.upper() in ("DISABLED", "SUSPENDED")):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account is disabled. Please contact an administrator.",
        )

    token = create_access_token({"sub": user.id, "role": user.role})
    return TokenResponse(
        access_token=token,
        user=UserResponse.model_validate(user),
    )


@router.get(
    "/verify-activation-token",
    response_model=TokenVerificationResponse,
    summary="Verify an account activation token",
)
def verify_activation(
    token: str = Query(..., description="Activation token to verify"),
    db: Session = Depends(get_db),
):
    """Verify single-use, unexpired activation token and return associated account details."""
    is_valid, user, reason = verify_token(db, token, token_type="activation")
    if not is_valid or not user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=reason or "Invalid or expired activation link.",
        )
    return TokenVerificationResponse(
        valid=True,
        email=user.email,
        full_name=user.full_name,
        role=user.role,
        message="Token is valid",
    )


@router.post("/activate", summary="Activate account and set initial password")
def activate_account(
    data: AccountActivationRequest,
    db: Session = Depends(get_db),
):
    """Activate invited account, set password, mark token redeemed, and transition status to ACTIVE."""
    is_valid, user, reason = verify_token(db, data.token, token_type="activation")
    if not is_valid or not user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=reason or "Invalid or expired activation link.",
        )

    # Redeem token (single-use)
    redeem_token(db, data.token, token_type="activation")

    # Set new password & transition status
    user.password_hash = hash_password(data.password)
    user.account_status = "ACTIVE"
    user.is_active = True
    db.commit()
    db.refresh(user)

    # Dispatch welcome & security notifications
    if user.role == "student":
        create_welcome_notification(db=db, user_id=user.id)
    elif user.role == "lecturer":
        create_faculty_welcome_notification(db=db, user_id=user.id, full_name=user.full_name)

    email_service.send_security_notification(
        to_email=user.email,
        full_name=user.full_name,
        action="Account Activated",
        details="Your AttendX account password was set and your account is now active.",
    )

    return {
        "message": "Your account has been activated successfully. You can now log in.",
        "role": user.role,
        "email": user.email,
    }


@router.post("/forgot-password", summary="Request password reset link")
def forgot_password(
    data: PasswordForgotRequest,
    db: Session = Depends(get_db),
):
    """Send secure one-time password reset link if account exists and is active."""
    normalized_email = data.email.lower().strip()
    user = db.query(User).filter(User.email == normalized_email).first()
    if user and user.is_active and user.account_status != "INVITED":
        raw_token, _ = create_password_reset_token(db, user)
        email_service.send_password_reset_email(
            to_email=user.email,
            full_name=user.full_name,
            reset_token=raw_token,
        )

    # Constant time / generic response to prevent email harvesting
    return {
        "message": "If an account with that email exists, password reset instructions have been sent."
    }


@router.get(
    "/verify-reset-token",
    response_model=TokenVerificationResponse,
    summary="Verify a password reset token",
)
def verify_reset(
    token: str = Query(..., description="Reset token to verify"),
    db: Session = Depends(get_db),
):
    """Verify single-use, unexpired password reset token."""
    is_valid, user, reason = verify_token(db, token, token_type="password_reset")
    if not is_valid or not user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=reason or "Invalid or expired password reset link.",
        )
    return TokenVerificationResponse(
        valid=True,
        email=user.email,
        full_name=user.full_name,
        role=user.role,
        message="Token is valid",
    )


@router.post("/reset-password", summary="Reset password using reset token")
def reset_password(
    data: PasswordResetRequest,
    db: Session = Depends(get_db),
):
    """Reset password using verified one-time token."""
    is_valid, user, reason = verify_token(db, data.token, token_type="password_reset")
    if not is_valid or not user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=reason or "Invalid or expired password reset link.",
        )

    redeem_token(db, data.token, token_type="password_reset")

    user.password_hash = hash_password(data.password)
    db.commit()
    db.refresh(user)

    email_service.send_security_notification(
        to_email=user.email,
        full_name=user.full_name,
        action="Password Changed",
        details="Your AttendX account password was successfully reset.",
    )

    return {
        "message": "Password has been reset successfully. You can now log in.",
        "role": user.role,
    }


@router.get("/me", response_model=UserResponse, summary="Get current authenticated user")
def get_me(current_user: User = Depends(get_current_user)):
    """Return the currently authenticated user's profile."""
    return UserResponse.model_validate(current_user)


@router.put("/profile", response_model=UserResponse, summary="Update user profile")
def update_profile(
    data: UserUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Update the authenticated user's profile fields."""
    if data.full_name is not None:
        current_user.full_name = data.full_name.strip()
    if data.department is not None:
        current_user.department = data.department.strip()
    if data.year is not None:
        current_user.year = data.year
    if data.section is not None:
        current_user.section = data.section.strip()

    db.commit()
    db.refresh(current_user)
    return UserResponse.model_validate(current_user)
