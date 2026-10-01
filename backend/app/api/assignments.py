import math
from fastapi import APIRouter, Depends, HTTPException, status, Query, Response
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import Optional, List, Dict, Any
from app.core.database import get_db
from app.core.security import get_current_admin
from app.models.user import User
from app.models.subject import Subject
from app.models.lecturer_subject import LecturerSubject
from app.schemas.subject import (
    LecturerAssignmentCreate,
    LecturerAssignmentResponse,
    AssignmentSummaryMetrics,
)

router = APIRouter(prefix="/api/assignments", tags=["Assignments"])
admin_router = APIRouter(prefix="/api/admin/assignments", tags=["Admin Assignments"])


def get_assignments_summary_data(db: Session) -> dict:
    """Calculate real database summary metrics for lecturer-subject teaching assignments."""
    total_assignments = db.query(func.count(LecturerSubject.id)).scalar() or 0
    assigned_lecturers = (
        db.query(func.count(func.distinct(LecturerSubject.lecturer_id))).scalar() or 0
    )
    assigned_subjects = (
        db.query(func.count(func.distinct(LecturerSubject.subject_id))).scalar() or 0
    )
    total_subjects = db.query(func.count(Subject.id)).scalar() or 0
    unassigned_subjects = max(0, total_subjects - assigned_subjects)

    return {
        "total_assignments": total_assignments,
        "assigned_lecturers": assigned_lecturers,
        "assigned_subjects": assigned_subjects,
        "unassigned_subjects": unassigned_subjects,
    }


def list_assignments_data(
    db: Session,
    search: Optional[str] = None,
    department: Optional[str] = None,
    lecturer_id: Optional[str] = None,
    subject_id: Optional[str] = None,
    page: int = 1,
    limit: int = 10,
) -> dict:
    """List teaching assignments with search, department filtering, and pagination."""
    query = (
        db.query(LecturerSubject, User, Subject)
        .join(User, LecturerSubject.lecturer_id == User.id)
        .join(Subject, LecturerSubject.subject_id == Subject.id)
    )

    if search and search.strip():
        term = f"%{search.strip()}%"
        query = query.filter(
            (User.full_name.ilike(term))
            | (User.email.ilike(term))
            | (User.employee_id.ilike(term))
            | (Subject.name.ilike(term))
            | (Subject.code.ilike(term))
        )

    if department and department.strip() and department.lower() != "all":
        d_term = f"%{department.strip()}%"
        query = query.filter(
            (User.department.ilike(d_term)) | (Subject.department.ilike(d_term))
        )

    if lecturer_id and lecturer_id.strip():
        query = query.filter(LecturerSubject.lecturer_id == lecturer_id.strip())

    if subject_id and subject_id.strip():
        query = query.filter(LecturerSubject.subject_id == subject_id.strip())

    total = query.count()
    pages = max(1, math.ceil(total / limit))
    offset = (page - 1) * limit

    rows = query.order_by(Subject.code.asc(), User.full_name.asc()).offset(offset).limit(limit).all()

    items = []
    for ls, u, s in rows:
        items.append({
            "id": ls.id,
            "lecturer_id": u.id,
            "subject_id": s.id,
            "lecturer_name": u.full_name,
            "lecturer_email": u.email,
            "lecturer_employee_id": u.employee_id or "",
            "lecturer_department": u.department or "",
            "subject_name": s.name,
            "subject_code": s.code,
            "subject_department": s.department,
            "subject_year": s.year,
            "subject_semester": s.semester,
            "created_at": ls.created_at.isoformat() if ls.created_at else None,
        })

    return {
        "items": items,
        "total": total,
        "page": page,
        "limit": limit,
        "pages": pages,
    }


def create_assignment_record(db: Session, data: LecturerAssignmentCreate) -> dict:
    """Validate and create a teaching assignment linking a lecturer to a subject."""
    lecturer = db.query(User).filter(User.id == data.lecturer_id).first()
    if not lecturer:
        raise HTTPException(status_code=404, detail="Lecturer not found")

    if lecturer.role != "lecturer":
        raise HTTPException(status_code=400, detail="Only users with lecturer role can be assigned to subjects")

    if not lecturer.is_active:
        raise HTTPException(status_code=400, detail="Cannot assign an inactive lecturer")

    subject = db.query(Subject).filter(Subject.id == data.subject_id).first()
    if not subject:
        raise HTTPException(status_code=404, detail="Subject not found")

    existing = db.query(LecturerSubject).filter(
        LecturerSubject.lecturer_id == data.lecturer_id,
        LecturerSubject.subject_id == data.subject_id,
    ).first()
    if existing:
        raise HTTPException(status_code=409, detail="This lecturer is already assigned to this subject")

    assignment = LecturerSubject(lecturer_id=data.lecturer_id, subject_id=data.subject_id)
    db.add(assignment)
    db.commit()
    db.refresh(assignment)

    from app.services.notification_service import create_assignment_notification
    create_assignment_notification(
        db=db,
        lecturer_id=lecturer.id,
        subject_id=subject.id,
        subject_name=subject.name,
        subject_code=subject.code,
        is_removal=False,
    )

    return {
        "id": assignment.id,
        "lecturer_id": lecturer.id,
        "subject_id": subject.id,
        "lecturer_name": lecturer.full_name,
        "lecturer_email": lecturer.email,
        "lecturer_employee_id": lecturer.employee_id or "",
        "lecturer_department": lecturer.department or "",
        "subject_name": subject.name,
        "subject_code": subject.code,
        "subject_department": subject.department,
        "subject_year": subject.year,
        "subject_semester": subject.semester,
        "created_at": assignment.created_at.isoformat() if assignment.created_at else None,
    }


def delete_assignment_record(db: Session, assignment_id: str) -> None:
    """Delete a teaching assignment."""
    assignment = db.query(LecturerSubject).filter(LecturerSubject.id == assignment_id).first()
    if not assignment:
        raise HTTPException(status_code=404, detail="Teaching assignment not found")

    lecturer_id = assignment.lecturer_id
    subject_id = assignment.subject_id
    subject = db.query(Subject).filter(Subject.id == subject_id).first()
    subj_name = subject.name if subject else "the subject"
    subj_code = subject.code if subject else ""

    db.delete(assignment)
    db.commit()

    from app.services.notification_service import create_assignment_notification
    create_assignment_notification(
        db=db,
        lecturer_id=lecturer_id,
        subject_id=subject_id,
        subject_name=subj_name,
        subject_code=subj_code,
        is_removal=True,
    )


# ==========================================
# /api/admin/assignments ROUTES
# ==========================================

@admin_router.get("/summary", summary="Get teaching assignment summary metrics")
def admin_get_assignments_summary(
    current_user: User = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    return get_assignments_summary_data(db)


@admin_router.get("", summary="List all teaching assignments")
def admin_list_assignments(
    search: Optional[str] = Query(None),
    department: Optional[str] = Query(None),
    lecturer_id: Optional[str] = Query(None),
    subject_id: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    limit: int = Query(10, ge=1, le=100),
    current_user: User = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    return list_assignments_data(
        db=db,
        search=search,
        department=department,
        lecturer_id=lecturer_id,
        subject_id=subject_id,
        page=page,
        limit=limit,
    )


@admin_router.post("", status_code=status.HTTP_201_CREATED, summary="Create teaching assignment")
def admin_create_assignment(
    data: LecturerAssignmentCreate,
    current_user: User = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    return create_assignment_record(db, data)


@admin_router.delete("/{assignment_id}", status_code=status.HTTP_204_NO_CONTENT,
                    response_class=Response, summary="Delete teaching assignment")
def admin_delete_assignment(
    assignment_id: str,
    current_user: User = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    delete_assignment_record(db, assignment_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


# ==========================================
# /api/assignments ALIAS ROUTES
# ==========================================

@router.get("/summary", summary="Get assignment summary")
def get_assignments_summary_alias(
    current_user: User = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    return get_assignments_summary_data(db)


@router.get("", summary="List assignments")
def list_assignments_alias(
    search: Optional[str] = Query(None),
    department: Optional[str] = Query(None),
    lecturer_id: Optional[str] = Query(None),
    subject_id: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    limit: int = Query(10, ge=1, le=100),
    current_user: User = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    return list_assignments_data(
        db=db,
        search=search,
        department=department,
        lecturer_id=lecturer_id,
        subject_id=subject_id,
        page=page,
        limit=limit,
    )
