from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import Optional, List
from datetime import date
from app.core.database import get_db
from app.core.security import get_current_user, get_current_admin
from app.models.user import User
from app.models.subject import Subject
from app.models.student_subject import StudentSubject
from app.models.attendance import Attendance
from app.schemas.attendance import (
    AttendanceBulkCreate,
    AttendanceUpdate,
    AttendanceResponse,
)

router = APIRouter(prefix="/api/attendance", tags=["Attendance"])


@router.post("", status_code=status.HTTP_201_CREATED, summary="Mark attendance for students")
def mark_attendance(
    data: AttendanceBulkCreate,
    current_user: User = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    """Bulk mark attendance for a subject on a given date. Admin only.
    Prevents duplicate submissions for the same student-subject-date combo."""
    # Validate subject
    subject = db.query(Subject).filter(Subject.id == data.subject_id).first()
    if not subject:
        raise HTTPException(status_code=404, detail="Subject not found")

    created = []
    skipped = []
    for record in data.records:
        # Validate student
        student = db.query(User).filter(User.id == record.student_id, User.role == "student").first()
        if not student:
            skipped.append({"student_id": record.student_id, "reason": "Student not found"})
            continue

        # Check for duplicate
        existing = db.query(Attendance).filter(
            Attendance.student_id == record.student_id,
            Attendance.subject_id == data.subject_id,
            Attendance.attendance_date == data.attendance_date,
        ).first()

        if existing:
            # Update existing record instead of failing
            existing.status = record.status
            existing.marked_by = current_user.id
            db.commit()
            db.refresh(existing)
            created.append({
                "id": existing.id,
                "student_id": existing.student_id,
                "status": existing.status,
                "updated": True,
            })
        else:
            attendance = Attendance(
                student_id=record.student_id,
                subject_id=data.subject_id,
                attendance_date=data.attendance_date,
                status=record.status,
                marked_by=current_user.id,
            )
            db.add(attendance)
            db.commit()
            db.refresh(attendance)
            created.append({
                "id": attendance.id,
                "student_id": attendance.student_id,
                "status": attendance.status,
                "updated": False,
            })

    return {
        "message": "Attendance marked successfully",
        "created": len(created),
        "skipped": len(skipped),
        "records": created,
        "skipped_details": skipped,
    }


@router.get("", summary="List attendance records")
def list_attendance(
    student_id: Optional[str] = Query(None),
    subject_id: Optional[str] = Query(None),
    date_from: Optional[date] = Query(None),
    date_to: Optional[date] = Query(None),
    status_filter: Optional[str] = Query(None, alias="status"),
    page: int = Query(1, ge=1),
    limit: int = Query(50, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """List attendance records with filters.
    Students can only see their own records. Admins can see all."""
    query = db.query(Attendance)

    # Students can only view their own attendance
    if current_user.role == "student":
        query = query.filter(Attendance.student_id == current_user.id)
    elif student_id:
        query = query.filter(Attendance.student_id == student_id)

    if subject_id:
        query = query.filter(Attendance.subject_id == subject_id)
    if date_from:
        query = query.filter(Attendance.attendance_date >= date_from)
    if date_to:
        query = query.filter(Attendance.attendance_date <= date_to)
    if status_filter and status_filter in ("present", "absent"):
        query = query.filter(Attendance.status == status_filter)

    total = query.count()
    records = query.order_by(Attendance.attendance_date.desc(), Attendance.created_at.desc()).offset(
        (page - 1) * limit
    ).limit(limit).all()

    result = []
    for r in records:
        student = db.query(User).filter(User.id == r.student_id).first()
        subject = db.query(Subject).filter(Subject.id == r.subject_id).first()
        marker = db.query(User).filter(User.id == r.marked_by).first()
        result.append({
            "id": r.id,
            "student_id": r.student_id,
            "subject_id": r.subject_id,
            "attendance_date": r.attendance_date.isoformat(),
            "status": r.status,
            "marked_by": r.marked_by,
            "created_at": r.created_at.isoformat() if r.created_at else None,
            "student_name": student.full_name if student else None,
            "student_sid": student.student_id if student else None,
            "subject_name": subject.name if subject else None,
            "subject_code": subject.code if subject else None,
            "marker_name": marker.full_name if marker else None,
        })

    return {"total": total, "page": page, "limit": limit, "records": result}


@router.get("/{attendance_id}", summary="Get a single attendance record")
def get_attendance(
    attendance_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    record = db.query(Attendance).filter(Attendance.id == attendance_id).first()
    if not record:
        raise HTTPException(status_code=404, detail="Attendance record not found")

    if current_user.role == "student" and record.student_id != current_user.id:
        raise HTTPException(status_code=403, detail="Access denied")

    student = db.query(User).filter(User.id == record.student_id).first()
    subject = db.query(Subject).filter(Subject.id == record.subject_id).first()

    return {
        "id": record.id,
        "student_id": record.student_id,
        "subject_id": record.subject_id,
        "attendance_date": record.attendance_date.isoformat(),
        "status": record.status,
        "marked_by": record.marked_by,
        "created_at": record.created_at.isoformat() if record.created_at else None,
        "student_name": student.full_name if student else None,
        "subject_name": subject.name if subject else None,
        "subject_code": subject.code if subject else None,
    }


@router.put("/{attendance_id}", summary="Update an attendance record")
def update_attendance(
    attendance_id: str,
    data: AttendanceUpdate,
    current_user: User = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    """Update attendance status. Admin only."""
    record = db.query(Attendance).filter(Attendance.id == attendance_id).first()
    if not record:
        raise HTTPException(status_code=404, detail="Attendance record not found")

    record.status = data.status
    record.marked_by = current_user.id
    db.commit()
    db.refresh(record)

    return {
        "id": record.id,
        "student_id": record.student_id,
        "subject_id": record.subject_id,
        "attendance_date": record.attendance_date.isoformat(),
        "status": record.status,
        "marked_by": record.marked_by,
        "message": "Attendance updated successfully",
    }


@router.delete("/{attendance_id}", status_code=status.HTTP_204_NO_CONTENT,
               summary="Delete an attendance record")
def delete_attendance(
    attendance_id: str,
    current_user: User = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    """Delete an attendance record. Admin only."""
    record = db.query(Attendance).filter(Attendance.id == attendance_id).first()
    if not record:
        raise HTTPException(status_code=404, detail="Attendance record not found")
    db.delete(record)
    db.commit()
    return None
