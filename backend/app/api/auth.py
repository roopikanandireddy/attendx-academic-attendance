from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.security import hash_password, verify_password, create_access_token, get_current_user
from app.models.user import User
from app.schemas.user import (
    UserRegister,
    UserLogin,
    UserUpdate,
    UserResponse,
    TokenResponse,
)

router = APIRouter(prefix="/api/auth", tags=["Authentication"])


@router.post("/register", response_model=TokenResponse, status_code=status.HTTP_201_CREATED,
             summary="Register a new student account")
def register(data: UserRegister, db: Session = Depends(get_db)):
    """Register a new student. Only student role is allowed via registration."""
    # Check email uniqueness
    existing = db.query(User).filter(User.email == data.email).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="An account with this email already exists",
        )

    # Check student_id uniqueness if provided
    if data.student_id:
        existing_sid = db.query(User).filter(User.student_id == data.student_id).first()
        if existing_sid:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="This student ID is already registered",
            )

    user = User(
        full_name=data.full_name.strip(),
        email=data.email.lower().strip(),
        password_hash=hash_password(data.password),
        role="student",
        student_id=data.student_id,
        department=data.department,
        year=data.year,
        section=data.section,
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    from app.services.notification_service import create_welcome_notification
    create_welcome_notification(db=db, user_id=user.id)

    token = create_access_token({"sub": user.id, "role": user.role})
    return TokenResponse(
        access_token=token,
        user=UserResponse.model_validate(user),
    )


@router.post("/login", response_model=TokenResponse, summary="Login with email and password")
def login(data: UserLogin, db: Session = Depends(get_db)):
    """Authenticate user and return JWT token."""
    user = db.query(User).filter(User.email == data.email.lower().strip()).first()
    if not user or not verify_password(data.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account is disabled. Please contact an administrator.",
        )

    token = create_access_token({"sub": user.id, "role": user.role})
    return TokenResponse(
        access_token=token,
        user=UserResponse.model_validate(user),
    )


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
