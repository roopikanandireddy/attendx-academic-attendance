import math
from fastapi import APIRouter, Depends, HTTPException, status, Query, Response
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import Optional, List, Dict, Any
from datetime import date
from app.core.database import get_db
from app.core.security import get_current_admin, get_current_lecturer, hash_password
from app.models.user import User
from app.models.subject import Subject
from app.models.lecturer_subject import LecturerSubject
from app.models.student_subject import StudentSubject
from app.models.attendance import Attendance
from app.schemas.user import (
    AdminCreateLecturer,
    AdminUpdateLecturer,
    LecturerStatusUpdate,
    UserResponse,
)
from app.schemas.dashboard import LecturerDashboardResponse
from app.schemas.attendance import (
    AttendanceBulkCreate,
    AttendanceUpdate,
    LecturerAssignedSubjectItem,
    LecturerSessionStudentItem,
    LecturerAttendanceSessionResponse,
    LecturerAttendanceBulkResult,
    LecturerRecordsResponse,
    LecturerStudentReportResponse,
    LecturerSubjectReportResponse,
)
from app.services.notification_service import (
    create_attendance_notification,
    check_and_create_low_attendance_warning,
    create_faculty_welcome_notification,
)
from app.services.lecturer_report_service import LecturerReportService
from app.api.dashboard import get_lecturer_dashboard_data

router = APIRouter(prefix="/api/lecturers", tags=["Lecturers"])
admin_router = APIRouter(prefix="/api/admin/lecturers", tags=["Admin Lecturers"])
lecturer_router = APIRouter(prefix="/api/lecturer", tags=["Lecturer Portal"])



def get_lecturers_summary_data(db: Session) -> dict:
    """Calculate real database summary statistics for lecturers."""
    total_lecturers = db.query(func.count(User.id)).filter(User.role == "lecturer").scalar() or 0
    active_lecturers = db.query(func.count(User.id)).filter(
        User.role == "lecturer", User.is_active == True
    ).scalar() or 0
    inactive_lecturers = total_lecturers - active_lecturers

    lecturers_with_assignments = (
        db.query(func.count(func.distinct(LecturerSubject.lecturer_id))).scalar() or 0
    )

    return {
        "total_lecturers": total_lecturers,
        "active_lecturers": active_lecturers,
        "inactive_lecturers": inactive_lecturers,
        "lecturers_with_assignments": lecturers_with_assignments,
    }


def list_lecturers_data(
    db: Session,
    search: Optional[str] = None,
    status_filter: Optional[str] = None,
    department: Optional[str] = None,
    assignment_status: Optional[str] = None,
    page: int = 1,
    limit: int = 10,
) -> dict:
    """List lecturers with real database filters and pagination."""
    query = db.query(User).filter(User.role == "lecturer")

    # Search filter: Employee ID, Name, Email
    if search and search.strip():
        term = f"%{search.strip()}%"
        query = query.filter(
            (User.full_name.ilike(term))
            | (User.email.ilike(term))
            | (User.employee_id.ilike(term))
        )

    # Status filter: active / inactive
    if status_filter and status_filter.lower() != "all":
        if status_filter.lower() == "active":
            query = query.filter(User.is_active == True)
        elif status_filter.lower() == "inactive":
            query = query.filter(User.is_active == False)

    # Department filter
    if department and department.strip() and department.lower() != "all":
        query = query.filter(User.department.ilike(f"%{department.strip()}%"))

    # Assignment status filter: all / assigned / unassigned
    if assignment_status and assignment_status.lower() != "all":
        assigned_subquery = db.query(LecturerSubject.lecturer_id).distinct()
        if assignment_status.lower() == "assigned":
            query = query.filter(User.id.in_(assigned_subquery))
        elif assignment_status.lower() == "unassigned":
            query = query.filter(User.id.not_in(assigned_subquery))

    total = query.count()
    pages = max(1, math.ceil(total / limit))
    offset = (page - 1) * limit

    lecturers = query.order_by(User.full_name.asc()).offset(offset).limit(limit).all()

    items = []
    for l in lecturers:
        sub_count = (
            db.query(func.count(LecturerSubject.id))
            .filter(LecturerSubject.lecturer_id == l.id)
            .scalar()
            or 0
        )
        items.append({
            "id": l.id,
            "employee_id": l.employee_id or "",
            "full_name": l.full_name,
            "email": l.email,
            "department": l.department or "",
            "role": l.role,
            "is_active": l.is_active,
            "status": "Active" if l.is_active else "Inactive",
            "assigned_subjects_count": sub_count,
            "created_at": l.created_at.isoformat() if l.created_at else None,
            "updated_at": l.updated_at.isoformat() if l.updated_at else None,
        })

    return {
        "items": items,
        "total": total,
        "page": page,
        "limit": limit,
        "pages": pages,
    }


def get_single_lecturer_data(db: Session, lecturer_id: str) -> dict:
    """Retrieve full details for a single lecturer."""
    lecturer = db.query(User).filter(User.id == lecturer_id, User.role == "lecturer").first()
    if not lecturer:
        raise HTTPException(status_code=404, detail="Lecturer not found")

    assignments = db.query(LecturerSubject).filter(LecturerSubject.lecturer_id == lecturer_id).all()
    assigned_subjects = []
    for a in assignments:
        sub = db.query(Subject).filter(Subject.id == a.subject_id).first()
        if sub:
            assigned_subjects.append({
                "id": sub.id,
                "assignment_id": a.id,
                "name": sub.name,
                "code": sub.code,
                "department": sub.department,
                "year": sub.year,
                "semester": sub.semester,
                "status": "Active",
            })

    return {
        "id": lecturer.id,
        "employee_id": lecturer.employee_id or "",
        "full_name": lecturer.full_name,
        "email": lecturer.email,
        "department": lecturer.department or "",
        "role": lecturer.role,
        "is_active": lecturer.is_active,
        "status": "Active" if lecturer.is_active else "Inactive",
        "assigned_subjects_count": len(assigned_subjects),
        "assigned_subjects": assigned_subjects,
        "created_at": lecturer.created_at.isoformat() if lecturer.created_at else None,
        "updated_at": lecturer.updated_at.isoformat() if lecturer.updated_at else None,
    }


def create_lecturer_record(db: Session, data: AdminCreateLecturer) -> dict:
    """Validate and create a new lecturer account."""
    # Email uniqueness check
    normalized_email = data.email.lower().strip()
    if db.query(User).filter(User.email == normalized_email).first():
        raise HTTPException(status_code=409, detail="An account with this email already exists")

    # Employee ID uniqueness check
    clean_emp_id = data.employee_id.strip()
    if db.query(User).filter(User.employee_id == clean_emp_id).first():
        raise HTTPException(status_code=409, detail="A lecturer with this Employee ID already exists")

    lecturer = User(
        full_name=data.full_name.strip(),
        email=normalized_email,
        password_hash=hash_password(data.password),
        role="lecturer",
        employee_id=clean_emp_id,
        department=data.department.strip(),
        is_active=True,
    )
    db.add(lecturer)
    db.commit()
    db.refresh(lecturer)

    create_faculty_welcome_notification(
        db=db,
        user_id=lecturer.id,
        full_name=lecturer.full_name,
    )

    return {
        "id": lecturer.id,
        "employee_id": lecturer.employee_id,
        "full_name": lecturer.full_name,
        "email": lecturer.email,
        "department": lecturer.department,
        "role": lecturer.role,
        "is_active": lecturer.is_active,
        "status": "Active",
        "assigned_subjects_count": 0,
        "created_at": lecturer.created_at.isoformat() if lecturer.created_at else None,
        "updated_at": lecturer.updated_at.isoformat() if lecturer.updated_at else None,
    }


def update_lecturer_record(db: Session, lecturer_id: str, data: AdminUpdateLecturer) -> dict:
    """Update lecturer profile details."""
    lecturer = db.query(User).filter(User.id == lecturer_id, User.role == "lecturer").first()
    if not lecturer:
        raise HTTPException(status_code=404, detail="Lecturer not found")

    if data.full_name is not None:
        lecturer.full_name = data.full_name.strip()

    if data.email is not None:
        new_email = data.email.lower().strip()
        existing = db.query(User).filter(User.email == new_email, User.id != lecturer_id).first()
        if existing:
            raise HTTPException(status_code=409, detail="An account with this email already exists")
        lecturer.email = new_email

    if data.employee_id is not None:
        new_emp_id = data.employee_id.strip()
        existing = db.query(User).filter(User.employee_id == new_emp_id, User.id != lecturer_id).first()
        if existing:
            raise HTTPException(status_code=409, detail="A lecturer with this Employee ID already exists")
        lecturer.employee_id = new_emp_id

    if data.department is not None:
        lecturer.department = data.department.strip()

    if data.is_active is not None:
        lecturer.is_active = data.is_active

    db.commit()
    db.refresh(lecturer)

    return {
        "id": lecturer.id,
        "employee_id": lecturer.employee_id,
        "full_name": lecturer.full_name,
        "email": lecturer.email,
        "department": lecturer.department,
        "role": lecturer.role,
        "is_active": lecturer.is_active,
        "status": "Active" if lecturer.is_active else "Inactive",
        "assigned_subjects_count": 0,
        "created_at": lecturer.created_at.isoformat() if lecturer.created_at else None,
        "updated_at": lecturer.updated_at.isoformat() if lecturer.updated_at else None,
    }


def set_lecturer_active_status(db: Session, lecturer_id: str, is_active: bool) -> dict:
    """Enable or disable a lecturer account."""
    lecturer = db.query(User).filter(User.id == lecturer_id, User.role == "lecturer").first()
    if not lecturer:
        raise HTTPException(status_code=404, detail="Lecturer not found")

    lecturer.is_active = is_active
    db.commit()
    db.refresh(lecturer)

    action_label = "enabled" if is_active else "disabled"
    return {
        "id": lecturer.id,
        "employee_id": lecturer.employee_id,
        "full_name": lecturer.full_name,
        "is_active": lecturer.is_active,
        "status": "Active" if lecturer.is_active else "Inactive",
        "message": f"Lecturer account {action_label} successfully",
    }


# ==========================================
# /api/admin/lecturers ROUTES
# ==========================================

@admin_router.get("/summary", summary="Get lecturer summary metrics")
def admin_get_lecturers_summary(
    current_user: User = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    """Return real-time database-driven lecturer summary metrics."""
    return get_lecturers_summary_data(db)


@admin_router.get("/count", summary="Get total lecturer count")
def admin_lecturer_count(
    current_user: User = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    total = db.query(func.count(User.id)).filter(User.role == "lecturer").scalar() or 0
    return {"total": total}


@admin_router.get("", summary="List all lecturers with search and filters")
def admin_list_lecturers(
    search: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    department: Optional[str] = Query(None),
    assignment_status: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    limit: int = Query(10, ge=1, le=100),
    current_user: User = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    return list_lecturers_data(
        db=db,
        search=search,
        status_filter=status,
        department=department,
        assignment_status=assignment_status,
        page=page,
        limit=limit,
    )


@admin_router.get("/{lecturer_id}", summary="Get lecturer details")
def admin_get_lecturer(
    lecturer_id: str,
    current_user: User = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    return get_single_lecturer_data(db, lecturer_id)


@admin_router.post("", status_code=status.HTTP_201_CREATED, summary="Create a new lecturer")
def admin_create_lecturer(
    data: AdminCreateLecturer,
    current_user: User = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    return create_lecturer_record(db, data)


@admin_router.put("/{lecturer_id}", summary="Update lecturer details")
def admin_update_lecturer(
    lecturer_id: str,
    data: AdminUpdateLecturer,
    current_user: User = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    return update_lecturer_record(db, lecturer_id, data)


@admin_router.patch("/{lecturer_id}/status", summary="Update lecturer status")
def admin_update_status(
    lecturer_id: str,
    data: LecturerStatusUpdate,
    current_user: User = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    return set_lecturer_active_status(db, lecturer_id, data.is_active)


@admin_router.post("/{lecturer_id}/disable", summary="Disable lecturer account")
def admin_disable_lecturer(
    lecturer_id: str,
    current_user: User = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    return set_lecturer_active_status(db, lecturer_id, False)


@admin_router.post("/{lecturer_id}/enable", summary="Enable lecturer account")
def admin_enable_lecturer(
    lecturer_id: str,
    current_user: User = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    return set_lecturer_active_status(db, lecturer_id, True)


@admin_router.delete("/{lecturer_id}", summary="Delete lecturer (for testing cleanup)")
def admin_delete_lecturer(
    lecturer_id: str,
    current_user: User = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    lecturer = db.query(User).filter(User.id == lecturer_id, User.role == "lecturer").first()
    if not lecturer:
        raise HTTPException(status_code=404, detail="Lecturer not found")
    db.delete(lecturer)
    db.commit()
    return {"message": "Lecturer deleted successfully"}


# ==========================================
# /api/lecturers ALIAS ROUTES
# ==========================================

@router.get("/summary", summary="Get lecturer summary metrics")
def get_lecturers_summary(
    current_user: User = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    return get_lecturers_summary_data(db)


@router.get("", summary="List all lecturers")
def list_lecturers(
    search: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    department: Optional[str] = Query(None),
    assignment_status: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    limit: int = Query(10, ge=1, le=100),
    current_user: User = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    return list_lecturers_data(
        db=db,
        search=search,
        status_filter=status,
        department=department,
        assignment_status=assignment_status,
        page=page,
        limit=limit,
    )


@router.get("/me", response_model=UserResponse, summary="Get current authenticated lecturer profile (alias)")
def get_lecturers_me_alias(
    current_user: User = Depends(get_current_lecturer),
):
    """Alias for /api/lecturer/me to retrieve current authenticated lecturer profile."""
    return UserResponse.model_validate(current_user)


# ==========================================
# /api/lecturer DEDICATED LECTURER ROUTES (MODULE L1)
# ==========================================

@lecturer_router.get("/me", response_model=UserResponse, summary="Get current authenticated lecturer profile")
def get_lecturer_me(
    current_user: User = Depends(get_current_lecturer),
):
    """Retrieve profile information for the authenticated lecturer."""
    return UserResponse.model_validate(current_user)


@lecturer_router.get("/dashboard", response_model=LecturerDashboardResponse, summary="Get current lecturer dashboard")
def get_lecturer_dashboard(
    current_user: User = Depends(get_current_lecturer),
    db: Session = Depends(get_db),
):
    """Retrieve full dashboard data scoped strictly to current authenticated lecturer."""
    return get_lecturer_dashboard_data(current_user, db)


# ==========================================
# /api/lecturer ATTENDANCE MANAGEMENT (MODULE L3)
# ==========================================

def verify_lecturer_assigned_to_subject(current_user: User, subject_id: str, db: Session) -> Subject:
    """Verifies that the authenticated lecturer is assigned to the specified subject.
    Raises 404 if subject doesn't exist, and 403 Forbidden if not assigned to this lecturer.
    """
    subject = db.query(Subject).filter(Subject.id == subject_id).first()
    if not subject:
        raise HTTPException(status_code=404, detail="Subject not found")

    assignment = db.query(LecturerSubject).filter(
        LecturerSubject.lecturer_id == current_user.id,
        LecturerSubject.subject_id == subject_id,
    ).first()
    if not assignment:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are not authorized to manage attendance for this subject",
        )
    return subject


@lecturer_router.get(
    "/subjects",
    response_model=List[LecturerAssignedSubjectItem],
    summary="Get subjects assigned to authenticated lecturer",
)
def get_lecturer_assigned_subjects(
    current_user: User = Depends(get_current_lecturer),
    db: Session = Depends(get_db),
):
    """List all subjects assigned to the authenticated lecturer with enrolled student counts."""
    assignments = (
        db.query(LecturerSubject)
        .filter(LecturerSubject.lecturer_id == current_user.id)
        .all()
    )
    assigned_subject_ids = [a.subject_id for a in assignments]
    if not assigned_subject_ids:
        return []

    subjects = (
        db.query(Subject)
        .filter(Subject.id.in_(assigned_subject_ids))
        .order_by(Subject.code.asc(), Subject.name.asc())
        .all()
    )

    result = []
    for s in subjects:
        enrolled_count = (
            db.query(func.count(StudentSubject.id))
            .filter(StudentSubject.subject_id == s.id)
            .scalar()
            or 0
        )
        result.append({
            "id": s.id,
            "name": s.name,
            "code": s.code,
            "department": s.department,
            "year": s.year,
            "semester": s.semester,
            "enrolled_students_count": enrolled_count,
        })
    return result


@lecturer_router.get(
    "/subjects/{subject_id}/students",
    summary="Get enrolled students for an assigned subject",
)
def get_lecturer_subject_students(
    subject_id: str,
    current_user: User = Depends(get_current_lecturer),
    db: Session = Depends(get_db),
):
    """List all students enrolled in a subject assigned to the authenticated lecturer."""
    verify_lecturer_assigned_to_subject(current_user, subject_id, db)

    enrollments = (
        db.query(StudentSubject, User)
        .join(User, StudentSubject.student_id == User.id)
        .filter(StudentSubject.subject_id == subject_id, User.role == "student")
        .order_by(User.full_name.asc())
        .all()
    )

    return [
        {
            "id": u.id,
            "student_id": u.id,
            "full_name": u.full_name,
            "student_sid": u.student_id or "",
            "email": u.email,
            "department": u.department or "",
            "year": u.year,
            "section": u.section or "",
            "enrollment_id": ss.id,
        }
        for ss, u in enrollments
    ]


@lecturer_router.get(
    "/attendance/session",
    response_model=LecturerAttendanceSessionResponse,
    summary="Get attendance session details for subject and date",
)
def get_lecturer_attendance_session(
    subject_id: str = Query(..., description="Assigned subject ID"),
    attendance_date: date = Query(..., description="Session date (YYYY-MM-DD)"),
    current_user: User = Depends(get_current_lecturer),
    db: Session = Depends(get_db),
):
    """Retrieve full class roster with marked attendance status for the given subject and date.
    Strictly verifies lecturer assignment.
    """
    subject = verify_lecturer_assigned_to_subject(current_user, subject_id, db)

    # Fetch enrolled students
    enrollments = (
        db.query(StudentSubject, User)
        .join(User, StudentSubject.student_id == User.id)
        .filter(StudentSubject.subject_id == subject_id, User.role == "student")
        .order_by(User.full_name.asc())
        .all()
    )

    # Fetch existing attendance records for this subject and date
    records = (
        db.query(Attendance)
        .filter(
            Attendance.subject_id == subject_id,
            Attendance.attendance_date == attendance_date,
        )
        .all()
    )
    records_by_student = {r.student_id: r for r in records}

    students_list = []
    present_count = 0
    absent_count = 0
    unmarked_count = 0

    for ss, u in enrollments:
        att = records_by_student.get(u.id)
        status_val = att.status if att else None
        att_id = att.id if att else None

        if status_val == "present":
            present_count += 1
        elif status_val == "absent":
            absent_count += 1
        else:
            unmarked_count += 1

        students_list.append({
            "student_id": u.id,
            "full_name": u.full_name,
            "student_sid": u.student_id or "",
            "department": u.department or "",
            "status": status_val,
            "attendance_id": att_id,
        })

    att_date_str = (
        attendance_date.isoformat()
        if hasattr(attendance_date, "isoformat")
        else str(attendance_date)
    )

    return {
        "subject_id": subject.id,
        "subject_code": subject.code,
        "subject_name": subject.name,
        "department": subject.department,
        "attendance_date": att_date_str,
        "has_existing_records": len(records) > 0,
        "total_students": len(enrollments),
        "present_count": present_count,
        "absent_count": absent_count,
        "unmarked_count": unmarked_count,
        "students": students_list,
    }


@lecturer_router.post(
    "/attendance",
    response_model=LecturerAttendanceBulkResult,
    status_code=status.HTTP_201_CREATED,
    summary="Mark or update attendance for an assigned subject session",
)
def mark_lecturer_attendance(
    data: AttendanceBulkCreate,
    current_user: User = Depends(get_current_lecturer),
    db: Session = Depends(get_db),
):
    """Mark attendance for students in an assigned subject on a specific date.
    Strictly verifies:
    1. Authenticated user is a lecturer.
    2. The subject is assigned to this lecturer.
    3. Attendance date is not in the future.
    4. Each student is actually enrolled in the subject.
    Updates existing records in-place without creating duplicates, respecting uq_attendance_record.
    """
    subject = verify_lecturer_assigned_to_subject(current_user, data.subject_id, db)

    # Date restriction: prevent marking future dates
    if data.attendance_date > date.today():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot mark attendance for future dates",
        )

    # Get set of all enrolled student IDs for this subject
    enrolled_ids = set(
        row[0]
        for row in db.query(StudentSubject.student_id)
        .filter(StudentSubject.subject_id == data.subject_id)
        .all()
    )

    created_count = 0
    updated_count = 0
    present_count = 0
    absent_count = 0

    subj_label = subject.code if subject.code else subject.name

    for record in data.records:
        # Check student enrollment
        if record.student_id not in enrolled_ids:
            continue

        clean_status = record.status.lower().strip()
        if clean_status not in ("present", "absent"):
            continue

        if clean_status == "present":
            present_count += 1
        else:
            absent_count += 1

        existing = (
            db.query(Attendance)
            .filter(
                Attendance.student_id == record.student_id,
                Attendance.subject_id == data.subject_id,
                Attendance.attendance_date == data.attendance_date,
            )
            .first()
        )

        record_id = None
        status_changed = False

        if existing:
            status_changed = existing.status != clean_status
            existing.status = clean_status
            existing.marked_by = current_user.id
            db.commit()
            db.refresh(existing)
            record_id = existing.id
            updated_count += 1
        else:
            new_att = Attendance(
                student_id=record.student_id,
                subject_id=data.subject_id,
                attendance_date=data.attendance_date,
                status=clean_status,
                marked_by=current_user.id,
            )
            db.add(new_att)
            db.commit()
            db.refresh(new_att)
            record_id = new_att.id
            created_count += 1
            status_changed = True

        if record_id and status_changed:
            create_attendance_notification(
                db=db,
                student_id=record.student_id,
                status=clean_status,
                attendance_id=record_id,
                subject_name=subject.name,
                subject_code=subject.code,
                attendance_date=data.attendance_date,
                is_update=bool(existing),
            )
            check_and_create_low_attendance_warning(
                db=db,
                student_id=record.student_id,
                subject_id=data.subject_id,
                attendance_date=data.attendance_date,
                threshold=75.0,
            )

    att_date_str = (
        data.attendance_date.isoformat()
        if hasattr(data.attendance_date, "isoformat")
        else str(data.attendance_date)
    )

    return {
        "message": "Attendance marked successfully",
        "subject_id": subject.id,
        "subject_code": subject.code,
        "attendance_date": att_date_str,
        "total_processed": created_count + updated_count,
        "created_count": created_count,
        "updated_count": updated_count,
        "present_count": present_count,
        "absent_count": absent_count,
    }


@lecturer_router.put(
    "/attendance/{attendance_id}",
    summary="Update single attendance record for an assigned subject",
)
def update_lecturer_attendance(
    attendance_id: str,
    data: AttendanceUpdate,
    current_user: User = Depends(get_current_lecturer),
    db: Session = Depends(get_db),
):
    """Update a single student's attendance record.
    Strictly verifies that the record's subject is assigned to the authenticated lecturer.
    """
    record = db.query(Attendance).filter(Attendance.id == attendance_id).first()
    if not record:
        raise HTTPException(status_code=404, detail="Attendance record not found")

    # Verify that the record belongs to a subject assigned to this lecturer
    verify_lecturer_assigned_to_subject(current_user, record.subject_id, db)

    clean_status = data.status.lower().strip()
    if clean_status not in ("present", "absent"):
        raise HTTPException(status_code=400, detail="Status must be 'present' or 'absent'")

    status_changed = record.status != clean_status
    record.status = clean_status
    record.marked_by = current_user.id
    db.commit()
    db.refresh(record)

    if status_changed:
        subject = db.query(Subject).filter(Subject.id == record.subject_id).first()
        subj_name = subject.name if subject else None
        subj_code = subject.code if subject else None
        create_attendance_notification(
            db=db,
            student_id=record.student_id,
            status=clean_status,
            attendance_id=record.id,
            subject_name=subj_name,
            subject_code=subj_code,
            attendance_date=record.attendance_date,
            is_update=True,
        )
        check_and_create_low_attendance_warning(
            db=db,
            student_id=record.student_id,
            subject_id=record.subject_id,
            attendance_date=record.attendance_date,
            threshold=75.0,
        )

    att_date_str = (
        record.attendance_date.isoformat()
        if hasattr(record.attendance_date, "isoformat")
        else str(record.attendance_date)
    )

    return {
        "id": record.id,
        "student_id": record.student_id,
        "subject_id": record.subject_id,
        "attendance_date": att_date_str,
        "status": record.status,
        "marked_by": record.marked_by,
        "message": "Attendance record updated successfully",
    }


@lecturer_router.get("/attendance", summary="List attendance records for lecturer's subjects")
def list_lecturer_attendance(
    subject_id: Optional[str] = Query(None),
    date_from: Optional[str] = Query(None),
    date_to: Optional[str] = Query(None),
    status_filter: Optional[str] = Query(None, alias="status"),
    page: int = Query(1, ge=1),
    limit: int = Query(50, ge=1, le=100),
    current_user: User = Depends(get_current_lecturer),
    db: Session = Depends(get_db),
):
    """List attendance records scoped strictly to subjects taught by the authenticated lecturer."""
    # Find all assigned subjects
    assignments = (
        db.query(LecturerSubject)
        .filter(LecturerSubject.lecturer_id == current_user.id)
        .all()
    )
    assigned_subject_ids = [a.subject_id for a in assignments]
    if not assigned_subject_ids:
        return {"total": 0, "page": page, "limit": limit, "records": []}

    query = db.query(Attendance)

    if subject_id and subject_id.strip():
        # Verify subject is assigned
        if subject_id.strip() not in assigned_subject_ids:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You are not authorized to view attendance for this subject",
            )
        query = query.filter(Attendance.subject_id == subject_id.strip())
    else:
        query = query.filter(Attendance.subject_id.in_(assigned_subject_ids))

    if date_from and date_from.strip():
        try:
            d_from = date.fromisoformat(date_from.strip())
            query = query.filter(Attendance.attendance_date >= d_from)
        except ValueError:
            pass

    if date_to and date_to.strip():
        try:
            d_to = date.fromisoformat(date_to.strip())
            query = query.filter(Attendance.attendance_date <= d_to)
        except ValueError:
            pass

    if status_filter and status_filter.strip():
        cleaned_status = status_filter.lower().strip()
        if cleaned_status in ("present", "absent"):
            query = query.filter(Attendance.status == cleaned_status)

    total = query.count()
    records = (
        query.order_by(Attendance.attendance_date.desc(), Attendance.created_at.desc())
        .offset((page - 1) * limit)
        .limit(limit)
        .all()
    )

    student_ids = {r.student_id for r in records}
    subject_ids = {r.subject_id for r in records}

    students_map = {u.id: u for u in db.query(User).filter(User.id.in_(student_ids)).all()} if student_ids else {}
    subjects_map = {s.id: s for s in db.query(Subject).filter(Subject.id.in_(subject_ids)).all()} if subject_ids else {}

    result = []
    for r in records:
        student = students_map.get(r.student_id)
        subject = subjects_map.get(r.subject_id)
        att_date_str = r.attendance_date.isoformat() if hasattr(r.attendance_date, "isoformat") else str(r.attendance_date)
        result.append({
            "id": r.id,
            "student_id": r.student_id,
            "subject_id": r.subject_id,
            "attendance_date": att_date_str,
            "status": r.status,
            "marked_by": r.marked_by,
            "created_at": r.created_at.isoformat() if r.created_at else None,
            "student_name": student.full_name if student else None,
            "student_sid": student.student_id if student else None,
            "subject_name": subject.name if subject else None,
            "subject_code": subject.code if subject else None,
        })

    return {"total": total, "page": page, "limit": limit, "records": result}


# ==========================================
# /api/lecturer RECORDS & REPORTS (MODULE L4)
# ==========================================

@lecturer_router.get(
    "/records",
    response_model=LecturerRecordsResponse,
    summary="List lecturer attendance records with summary stats and filters",
)
def get_lecturer_attendance_records(
    subject_id: Optional[str] = Query(None, description="Filter by assigned subject ID"),
    date_from: Optional[str] = Query(None, description="Start date (YYYY-MM-DD)"),
    date_to: Optional[str] = Query(None, description="End date (YYYY-MM-DD)"),
    status_filter: Optional[str] = Query(None, alias="status", description="Filter by status ('present' or 'absent')"),
    search: Optional[str] = Query(None, description="Search by student name or roll number"),
    page: int = Query(1, ge=1, description="Page number"),
    limit: int = Query(20, ge=1, le=100, description="Records per page"),
    sort_by: str = Query("date", description="Sort by field: date, student_name, student_sid, status, subject_code"),
    sort_order: str = Query("desc", description="Sort direction: asc or desc"),
    current_user: User = Depends(get_current_lecturer),
    db: Session = Depends(get_db),
):
    """Retrieve paginated attendance records strictly scoped to current lecturer's assigned subjects.
    Returns real-time summary statistics, filterable by subject, date range, status, and student search.
    """
    d_from: Optional[date] = None
    if date_from and date_from.strip():
        try:
            d_from = date.fromisoformat(date_from.strip())
        except ValueError:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid date_from format. Use YYYY-MM-DD")

    d_to: Optional[date] = None
    if date_to and date_to.strip():
        try:
            d_to = date.fromisoformat(date_to.strip())
        except ValueError:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid date_to format. Use YYYY-MM-DD")

    return LecturerReportService.get_attendance_records(
        db=db,
        current_lecturer=current_user,
        subject_id=subject_id,
        date_from=d_from,
        date_to=d_to,
        status_filter=status_filter,
        search=search,
        page=page,
        limit=limit,
        sort_by=sort_by,
        sort_order=sort_order,
    )


@lecturer_router.get(
    "/reports/student/{student_id}",
    response_model=LecturerStudentReportResponse,
    summary="Get individual student attendance report",
)
def get_lecturer_student_report(
    student_id: str,
    subject_id: Optional[str] = Query(None, description="Optional subject ID filter"),
    current_user: User = Depends(get_current_lecturer),
    db: Session = Depends(get_db),
):
    """Retrieve detailed student attendance report.
    Lecturer can only inspect students enrolled in their assigned subjects.
    """
    return LecturerReportService.get_student_report(
        db=db,
        current_lecturer=current_user,
        student_id=student_id,
        subject_id=subject_id,
    )


@lecturer_router.get(
    "/reports/subject/{subject_id}",
    response_model=LecturerSubjectReportResponse,
    summary="Get subject-level attendance report with student breakdown",
)
def get_lecturer_subject_report(
    subject_id: str,
    date_from: Optional[str] = Query(None, description="Start date (YYYY-MM-DD)"),
    date_to: Optional[str] = Query(None, description="End date (YYYY-MM-DD)"),
    current_user: User = Depends(get_current_lecturer),
    db: Session = Depends(get_db),
):
    """Retrieve comprehensive subject report with full roster breakdown and daily session statistics.
    Strictly verifies lecturer assignment.
    """
    d_from: Optional[date] = None
    if date_from and date_from.strip():
        try:
            d_from = date.fromisoformat(date_from.strip())
        except ValueError:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid date_from format. Use YYYY-MM-DD")

    d_to: Optional[date] = None
    if date_to and date_to.strip():
        try:
            d_to = date.fromisoformat(date_to.strip())
        except ValueError:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid date_to format. Use YYYY-MM-DD")

    return LecturerReportService.get_subject_report(
        db=db,
        current_lecturer=current_user,
        subject_id=subject_id,
        date_from=d_from,
        date_to=d_to,
    )


@lecturer_router.get(
    "/reports/export",
    summary="Export attendance records or reports to academic CSV",
)
def export_lecturer_report(
    export_type: str = Query("records", description="Export type: records, student, or subject"),
    subject_id: Optional[str] = Query(None, description="Subject ID filter"),
    student_id: Optional[str] = Query(None, description="Student ID (required for student export)"),
    date_from: Optional[str] = Query(None, description="Start date (YYYY-MM-DD)"),
    date_to: Optional[str] = Query(None, description="End date (YYYY-MM-DD)"),
    status_filter: Optional[str] = Query(None, alias="status", description="Status filter: present or absent"),
    search: Optional[str] = Query(None, description="Student name or roll number search"),
    current_user: User = Depends(get_current_lecturer),
    db: Session = Depends(get_db),
):
    """Export attendance data to academic CSV.
    Enforces identical authorization rules and data scoping as query APIs.
    """
    d_from: Optional[date] = None
    if date_from and date_from.strip():
        try:
            d_from = date.fromisoformat(date_from.strip())
        except ValueError:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid date_from format. Use YYYY-MM-DD")

    d_to: Optional[date] = None
    if date_to and date_to.strip():
        try:
            d_to = date.fromisoformat(date_to.strip())
        except ValueError:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid date_to format. Use YYYY-MM-DD")

    csv_content, filename = LecturerReportService.export_attendance_csv(
        db=db,
        current_lecturer=current_user,
        export_type=export_type,
        subject_id=subject_id,
        student_id=student_id,
        date_from=d_from,
        date_to=d_to,
        status_filter=status_filter,
        search=search,
    )

    return Response(
        content=csv_content,
        media_type="text/csv",
        headers={
            "Content-Disposition": f'attachment; filename="{filename}"',
            "Cache-Control": "no-cache, no-store, must-revalidate",
        },
    )




