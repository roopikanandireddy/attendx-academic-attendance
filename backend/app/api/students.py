import math
from fastapi import APIRouter, Depends, HTTPException, status, Query, Response
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import Optional, List, Dict, Any
from app.core.database import get_db
from app.core.security import get_current_admin, hash_password, get_current_user
from app.models.user import User
from app.models.subject import Subject
from app.models.attendance import Attendance
from app.models.student_subject import StudentSubject
from app.schemas.user import (
    AdminCreateStudent,
    AdminUpdateStudent,
    StudentStatusUpdate,
    UserResponse,
)
import uuid
from app.services.token_service import create_activation_token
from app.services.email_service import email_service
from app.core.observability import log_structured_event

router = APIRouter(prefix="/api/students", tags=["Students"])
admin_router = APIRouter(prefix="/api/admin/students", tags=["Admin Students"])


def calculate_student_attendance(db: Session, student_id: str) -> tuple[int, int, int, float]:
    """Calculate attendance metrics (total_classes, present, absent, percentage) for a student."""
    total = db.query(func.count(Attendance.id)).filter(Attendance.student_id == student_id).scalar() or 0
    present = db.query(func.count(Attendance.id)).filter(
        Attendance.student_id == student_id,
        Attendance.status == "present",
    ).scalar() or 0
    absent = total - present
    pct = round((present / total * 100), 1) if total > 0 else 0.0
    return total, present, absent, pct


def get_students_summary_data(db: Session) -> dict:
    """Calculate real database summary statistics for students."""
    total_students = db.query(func.count(User.id)).filter(User.role == "student").scalar() or 0
    active_students = db.query(func.count(User.id)).filter(
        User.role == "student", User.is_active == True
    ).scalar() or 0
    inactive_students = total_students - active_students

    # Active students below 75% threshold
    students = db.query(User).filter(User.role == "student", User.is_active == True).all()
    below_threshold_count = 0
    for st in students:
        tot, _, _, pct = calculate_student_attendance(db, st.id)
        if tot > 0 and pct < 75.0:
            below_threshold_count += 1

    return {
        "total_students": total_students,
        "active_students": active_students,
        "inactive_students": inactive_students,
        "below_threshold_students": below_threshold_count,
    }


def list_students_data(
    db: Session,
    search: Optional[str] = None,
    status_filter: Optional[str] = None,
    department: Optional[str] = None,
    year: Optional[str] = None,
    section: Optional[str] = None,
    attendance_filter: Optional[str] = None,
    page: int = 1,
    limit: int = 10,
) -> dict:
    """List students with combined real-database filters and pagination."""
    query = db.query(User).filter(User.role == "student")

    # Search filter
    if search and search.strip():
        search_term = f"%{search.strip()}%"
        query = query.filter(
            (User.full_name.ilike(search_term))
            | (User.email.ilike(search_term))
            | (User.student_id.ilike(search_term))
        )

    # Status filter
    if status_filter and status_filter.strip().lower() in ("active", "inactive", "invited", "disabled"):
        sf = status_filter.strip().lower()
        if sf == "active":
            query = query.filter((User.account_status == "ACTIVE") & (User.is_active == True))
        elif sf == "invited":
            query = query.filter(User.account_status == "INVITED")
        elif sf in ("inactive", "disabled"):
            query = query.filter((User.account_status == "DISABLED") | (User.is_active == False))

    # Department filter
    if department and department.strip():
        query = query.filter(User.department == department.strip())

    # Year filter
    if year and year.strip():
        try:
            y_val = int(year.strip())
            query = query.filter(User.year == y_val)
        except ValueError:
            pass

    # Section filter
    if section and section.strip():
        query = query.filter(User.section == section.strip())

    all_matched = query.order_by(User.full_name.asc()).all()

    # Pre-calculate attendance for filtering & display
    student_records = []
    for student in all_matched:
        total_classes, present_classes, absent_classes, percentage = calculate_student_attendance(db, student.id)

        # Attendance filter check
        if attendance_filter == "above_75" and percentage < 75.0:
            continue
        if attendance_filter == "below_75" and (total_classes == 0 or percentage >= 75.0):
            continue

        student_records.append({
            "id": student.id,
            "full_name": student.full_name,
            "email": student.email,
            "student_id": student.student_id or "",
            "department": student.department or "",
            "year": student.year or 0,
            "section": student.section or "",
            "is_active": student.is_active,
            "account_status": student.account_status or ("ACTIVE" if student.is_active else "DISABLED"),
            "status": student.account_status.capitalize() if student.account_status else ("Active" if student.is_active else "Inactive"),
            "role": student.role,
            "attendance_percentage": percentage,
            "total_classes": total_classes,
            "present_classes": present_classes,
            "absent_classes": absent_classes,
            "created_at": student.created_at.isoformat() if student.created_at else None,
            "updated_at": student.updated_at.isoformat() if student.updated_at else None,
        })

    total_count = len(student_records)
    total_pages = max(1, math.ceil(total_count / limit))
    offset = (page - 1) * limit
    paged_items = student_records[offset : offset + limit]

    return {
        "items": paged_items,
        "total": total_count,
        "page": page,
        "limit": limit,
        "pages": total_pages,
    }


def get_single_student_data(db: Session, student_id: str) -> dict:
    """Retrieve full details of a student including attendance summary and subject breakdown."""
    student = db.query(User).filter(User.id == student_id, User.role == "student").first()
    if not student:
        raise HTTPException(status_code=404, detail="Student not found")

    total_classes, present_classes, absent_classes, percentage = calculate_student_attendance(db, student.id)

    # Subject-wise attendance
    enrollments = db.query(StudentSubject).filter(StudentSubject.student_id == student.id).all()
    subjects_attendance = []
    for enr in enrollments:
        subj = db.query(Subject).filter(Subject.id == enr.subject_id).first()
        if not subj:
            continue
        sub_total = db.query(func.count(Attendance.id)).filter(
            Attendance.student_id == student.id,
            Attendance.subject_id == subj.id,
        ).scalar() or 0
        sub_present = db.query(func.count(Attendance.id)).filter(
            Attendance.student_id == student.id,
            Attendance.subject_id == subj.id,
            Attendance.status == "present",
        ).scalar() or 0
        sub_absent = sub_total - sub_present
        sub_pct = round((sub_present / sub_total * 100), 1) if sub_total > 0 else 0.0
        subjects_attendance.append({
            "subject_id": subj.id,
            "subject_name": subj.name,
            "subject_code": subj.code,
            "department": subj.department,
            "year": subj.year,
            "semester": subj.semester,
            "total_classes": sub_total,
            "present": sub_present,
            "absent": sub_absent,
            "percentage": sub_pct,
        })

    return {
        "id": student.id,
        "student_id": student.student_id or "",
        "full_name": student.full_name,
        "email": student.email,
        "role": student.role,
        "department": student.department or "",
        "year": student.year or 0,
        "section": student.section or "",
        "is_active": student.is_active,
        "account_status": student.account_status or ("ACTIVE" if student.is_active else "DISABLED"),
        "status": student.account_status.capitalize() if student.account_status else ("Active" if student.is_active else "Inactive"),
        "attendance_summary": {
            "total_classes": total_classes,
            "present": present_classes,
            "absent": absent_classes,
            "percentage": percentage,
        },
        "subjects_attendance": subjects_attendance,
        "enrollments": [
            {"id": e.id, "subject_id": e.subject_id, "created_at": e.created_at.isoformat() if e.created_at else None}
            for e in enrollments
        ],
        "created_at": student.created_at.isoformat() if student.created_at else None,
        "updated_at": student.updated_at.isoformat() if student.updated_at else None,
    }


def create_student_record(db: Session, data: AdminCreateStudent) -> dict:
    """Validate and create a new student account in INVITED state (or ACTIVE if password supplied)."""
    # Check email uniqueness
    normalized_email = data.email.lower().strip()
    if db.query(User).filter(User.email == normalized_email).first():
        raise HTTPException(status_code=409, detail="An account with this email already exists")

    # Check student_id uniqueness
    clean_sid = data.student_id.strip()
    if db.query(User).filter(User.student_id == clean_sid).first():
        raise HTTPException(status_code=409, detail="A student with this ID already exists")

    is_invited = not bool(data.password)
    account_status = "ACTIVE" if not is_invited else "INVITED"
    is_active = not is_invited
    pw_hash = hash_password(data.password) if data.password else f"!INVITED!{uuid.uuid4().hex}"

    student = User(
        full_name=data.full_name.strip(),
        email=normalized_email,
        password_hash=pw_hash,
        role="student",
        student_id=clean_sid,
        department=data.department.strip(),
        year=data.year,
        section=data.section.strip(),
        is_active=is_active,
        account_status=account_status,
    )
    db.add(student)
    db.commit()
    db.refresh(student)

    if is_invited:
        log_structured_event(
            event="invitation_created",
            level="INFO",
            role="student",
            category="INVITATION",
            details={"email": student.email, "student_id": student.student_id},
        )
        raw_token, _ = create_activation_token(db, student)
        log_structured_event(
            event="activation_token_created",
            level="INFO",
            role="student",
            category="TOKEN_GENERATED",
            details={"email": student.email},
        )
        email_result = email_service.send_account_activation_email(
            to_email=student.email,
            full_name=student.full_name,
            activation_token=raw_token,
            role="Student",
        )
        email_delivery_info = email_result.to_dict()
    else:
        from app.services.notification_service import create_welcome_notification
        create_welcome_notification(db=db, user_id=student.id)
        email_delivery_info = None

    response_data = {
        "id": student.id,
        "student_id": student.student_id,
        "full_name": student.full_name,
        "email": student.email,
        "department": student.department,
        "year": student.year,
        "section": student.section,
        "role": student.role,
        "is_active": student.is_active,
        "account_status": student.account_status,
        "status": student.account_status.capitalize(),
        "created_at": student.created_at.isoformat() if student.created_at else None,
        "updated_at": student.updated_at.isoformat() if student.updated_at else None,
    }
    if email_delivery_info:
        response_data["email_delivery"] = email_delivery_info

    return response_data


def update_student_record(db: Session, student_id: str, data: AdminUpdateStudent) -> dict:
    """Update student profile details."""
    student = db.query(User).filter(User.id == student_id, User.role == "student").first()
    if not student:
        raise HTTPException(status_code=404, detail="Student not found")

    if data.full_name is not None:
        student.full_name = data.full_name.strip()
    if data.email is not None:
        new_email = data.email.lower().strip()
        existing = db.query(User).filter(User.email == new_email, User.id != student_id).first()
        if existing:
            raise HTTPException(status_code=409, detail="An account with this email already exists")
        student.email = new_email
    if data.student_id is not None:
        new_sid = data.student_id.strip()
        existing = db.query(User).filter(User.student_id == new_sid, User.id != student_id).first()
        if existing:
            raise HTTPException(status_code=409, detail="A student with this ID already exists")
        student.student_id = new_sid
    if data.department is not None:
        student.department = data.department.strip()
    if data.year is not None:
        student.year = data.year
    if data.section is not None:
        student.section = data.section.strip()
    if data.is_active is not None:
        student.is_active = data.is_active
        if not data.is_active and student.account_status != "INVITED":
            student.account_status = "DISABLED"
        elif data.is_active and student.account_status == "DISABLED":
            student.account_status = "ACTIVE"
    if data.account_status is not None:
        new_status = data.account_status.strip().upper()
        student.account_status = new_status
        if new_status == "DISABLED":
            student.is_active = False
        elif new_status == "ACTIVE":
            student.is_active = True

    db.commit()
    db.refresh(student)

    return {
        "id": student.id,
        "student_id": student.student_id,
        "full_name": student.full_name,
        "email": student.email,
        "department": student.department,
        "year": student.year,
        "section": student.section,
        "role": student.role,
        "is_active": student.is_active,
        "account_status": student.account_status,
        "status": student.account_status.capitalize() if student.account_status else ("Active" if student.is_active else "Inactive"),
        "created_at": student.created_at.isoformat() if student.created_at else None,
        "updated_at": student.updated_at.isoformat() if student.updated_at else None,
    }


def set_student_active_status(db: Session, student_id: str, is_active: bool) -> dict:
    """Set active or disabled state for student account."""
    student = db.query(User).filter(User.id == student_id, User.role == "student").first()
    if not student:
        raise HTTPException(status_code=404, detail="Student not found")

    student.is_active = is_active
    student.account_status = "ACTIVE" if is_active else "DISABLED"
    db.commit()
    db.refresh(student)

    action_label = "enabled" if is_active else "disabled"
    return {
        "id": student.id,
        "student_id": student.student_id,
        "full_name": student.full_name,
        "is_active": student.is_active,
        "account_status": student.account_status,
        "status": student.account_status.capitalize(),
        "message": f"Student account {action_label} successfully",
    }


def resend_student_activation_email(db: Session, student_id: str) -> dict:
    """Resend account activation email to a student in INVITED status."""
    student = db.query(User).filter(User.id == student_id, User.role == "student").first()
    if not student:
        raise HTTPException(status_code=404, detail="Student not found")
    if student.account_status != "INVITED":
        raise HTTPException(
            status_code=400,
            detail=f"Cannot resend activation for account with status '{student.account_status}'. Only INVITED accounts can be activated.",
        )

    raw_token, _ = create_activation_token(db, student)
    log_structured_event(
        event="activation_token_created",
        level="INFO",
        role="student",
        category="TOKEN_GENERATED",
        details={"email": student.email, "action": "resend"},
    )
    email_result = email_service.send_account_activation_email(
        to_email=student.email,
        full_name=student.full_name,
        activation_token=raw_token,
        role="Student",
    )
    msg = (
        f"Activation email accepted by provider for {student.email}"
        if email_result.success
        else f"Failed to send activation email to {student.email}: {email_result.message}"
    )
    return {
        "message": msg,
        "email": student.email,
        "email_delivery": email_result.to_dict(),
    }


resend_student_activation = resend_student_activation_email


# ==========================================
# /api/students ROUTES
# ==========================================

@router.get("/summary", summary="Get student summary metrics")
def get_students_summary(
    current_user: User = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    """Return real-time student summary statistics for admin."""
    return get_students_summary_data(db)


@router.get("/count", summary="Get total student count")
def student_count(
    current_user: User = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    total = db.query(func.count(User.id)).filter(User.role == "student").scalar() or 0
    return {"total": total}


@router.get("", summary="List all students")
def list_students(
    search: Optional[str] = Query(None, description="Search by name, email, or student ID"),
    status: Optional[str] = Query(None, description="Filter by status (all, active, inactive)"),
    department: Optional[str] = Query(None),
    year: Optional[str] = Query(None),
    section: Optional[str] = Query(None),
    attendance: Optional[str] = Query(None, description="Filter by attendance (all, above_75, below_75)"),
    page: int = Query(1, ge=1),
    limit: int = Query(10, ge=1, le=100),
    current_user: User = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    """List students with optional filters and pagination. Admin only."""
    return list_students_data(
        db=db,
        search=search,
        status_filter=status,
        department=department,
        year=year,
        section=section,
        attendance_filter=attendance,
        page=page,
        limit=limit,
    )


@router.get("/{student_id}", summary="Get student details")
def get_student(
    student_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get a single student's details. Admin can view any, student can view self."""
    if current_user.role != "admin" and current_user.id != student_id:
        raise HTTPException(status_code=403, detail="Access denied")
    return get_single_student_data(db, student_id)


@router.post("", status_code=status.HTTP_201_CREATED, summary="Add a new student")
def create_student(
    data: AdminCreateStudent,
    current_user: User = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    """Create a new student account. Admin only."""
    return create_student_record(db, data)


@router.put("/{student_id}", summary="Update a student")
def update_student(
    student_id: str,
    data: AdminUpdateStudent,
    current_user: User = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    """Update student details. Admin only."""
    return update_student_record(db, student_id, data)


@router.patch("/{student_id}/status", summary="Update student status")
def update_status(
    student_id: str,
    data: StudentStatusUpdate,
    current_user: User = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    """Update student account status (enable/disable). Admin only."""
    return set_student_active_status(db, student_id, data.is_active)


@router.post("/{student_id}/disable", summary="Disable student account")
def disable_student_account(
    student_id: str,
    current_user: User = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    """Disable student account. Admin only."""
    return set_student_active_status(db, student_id, False)


@router.post("/{student_id}/enable", summary="Enable student account")
def enable_student_account(
    student_id: str,
    current_user: User = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    """Enable student account. Admin only."""
    return set_student_active_status(db, student_id, True)


@router.post("/{student_id}/resend-activation", summary="Resend activation email to student")
def resend_activation_email(
    student_id: str,
    current_user: User = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    """Resend activation email to a student in INVITED status. Admin only."""
    return resend_student_activation_email(db, student_id)


@router.delete("/{student_id}", status_code=status.HTTP_204_NO_CONTENT,
               response_class=Response, summary="Delete a student")
def delete_student(
    student_id: str,
    current_user: User = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    """Delete a student and all related records. Admin only."""
    student = db.query(User).filter(User.id == student_id, User.role == "student").first()
    if not student:
        raise HTTPException(status_code=404, detail="Student not found")

    db.delete(student)
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.post("/me/subjects", status_code=status.HTTP_201_CREATED, summary="Enroll current student in subjects")
def enroll_me_subjects(
    data: dict,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Enroll the current authenticated student in subjects."""
    if current_user.role != "student":
        raise HTTPException(status_code=403, detail="Students only")

    subject_ids = data.get("subject_ids", [])
    if not subject_ids and "subject_id" in data:
        subject_ids = [data["subject_id"]]

    if not subject_ids:
        raise HTTPException(status_code=400, detail="No subjects selected")

    from app.services.notification_service import create_enrollment_notification

    subjects = db.query(Subject).filter(Subject.id.in_(subject_ids)).all()
    valid_ids = [s.id for s in subjects]

    existing = db.query(StudentSubject.subject_id).filter(
        StudentSubject.student_id == current_user.id,
        StudentSubject.subject_id.in_(valid_ids),
    ).all()
    existing_ids = {e[0] for e in existing}

    added_count = 0
    for sid in valid_ids:
        if sid not in existing_ids:
            db.add(StudentSubject(student_id=current_user.id, subject_id=sid))
            added_count += 1

    db.commit()

    if added_count > 0:
        create_enrollment_notification(db=db, user_id=current_user.id, count=added_count)

    return {
        "message": f"Successfully enrolled in {added_count} subject(s)",
        "enrolled_count": added_count,
        "subject_ids": [s.id for s in subjects],
    }


# ==========================================
# /api/admin/students ALIAS ROUTES
# ==========================================

@admin_router.get("/summary", summary="Get student summary metrics")
def admin_get_students_summary(
    current_user: User = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    return get_students_summary_data(db)


@admin_router.get("/count", summary="Get total student count")
def admin_student_count(
    current_user: User = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    total = db.query(func.count(User.id)).filter(User.role == "student").scalar() or 0
    return {"total": total}


@admin_router.get("", summary="List all students")
def admin_list_students(
    search: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    department: Optional[str] = Query(None),
    year: Optional[str] = Query(None),
    section: Optional[str] = Query(None),
    attendance: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    limit: int = Query(10, ge=1, le=100),
    current_user: User = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    return list_students_data(
        db=db,
        search=search,
        status_filter=status,
        department=department,
        year=year,
        section=section,
        attendance_filter=attendance,
        page=page,
        limit=limit,
    )


@admin_router.get("/{student_id}", summary="Get student details")
def admin_get_student(
    student_id: str,
    current_user: User = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    return get_single_student_data(db, student_id)


@admin_router.post("", status_code=status.HTTP_201_CREATED, summary="Add a new student")
def admin_create_student(
    data: AdminCreateStudent,
    current_user: User = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    return create_student_record(db, data)


@admin_router.put("/{student_id}", summary="Update a student")
def admin_update_student(
    student_id: str,
    data: AdminUpdateStudent,
    current_user: User = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    return update_student_record(db, student_id, data)


@admin_router.patch("/{student_id}/status", summary="Update student status")
def admin_update_status(
    student_id: str,
    data: StudentStatusUpdate,
    current_user: User = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    return set_student_active_status(db, student_id, data.is_active)


@admin_router.post("/{student_id}/disable", summary="Disable student account")
def admin_disable_student(
    student_id: str,
    current_user: User = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    return set_student_active_status(db, student_id, False)


@admin_router.post("/{student_id}/enable", summary="Enable student account")
def admin_enable_student(
    student_id: str,
    current_user: User = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    return set_student_active_status(db, student_id, True)


@admin_router.post("/{student_id}/resend-activation", summary="Resend activation email to student")
def admin_resend_student_activation(
    student_id: str,
    current_user: User = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    """Resend activation email to a student in INVITED status. Admin only."""
    return resend_student_activation_email(db, student_id)


@admin_router.delete("/{student_id}", status_code=status.HTTP_204_NO_CONTENT,
                     response_class=Response, summary="Delete a student")
def admin_delete_student(
    student_id: str,
    current_user: User = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    student = db.query(User).filter(User.id == student_id, User.role == "student").first()
    if not student:
        raise HTTPException(status_code=404, detail="Student not found")

    db.delete(student)
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)
