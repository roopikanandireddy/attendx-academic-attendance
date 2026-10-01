from fastapi import APIRouter, Depends, HTTPException, status, Query, Response
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import Optional, List
from datetime import date
from app.core.database import get_db
from app.core.security import get_current_user, get_current_admin
from app.models.user import User
from app.models.subject import Subject
from app.models.student_subject import StudentSubject
from app.models.lecturer_subject import LecturerSubject
from app.models.attendance import Attendance

from app.schemas.attendance import (
    AttendanceBulkCreate,
    AttendanceUpdate,
    AttendanceResponse,
)
from app.services.notification_service import (
    create_attendance_notification,
    check_and_create_low_attendance_warning,
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

        record_id = None
        if existing:
            # Update existing record instead of failing
            existing.status = record.status
            existing.marked_by = current_user.id
            db.commit()
            db.refresh(existing)
            record_id = existing.id
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
            record_id = attendance.id
            created.append({
                "id": attendance.id,
                "student_id": attendance.student_id,
                "status": attendance.status,
                "updated": False,
            })

        # Generate attendance notification
        if record_id:
            create_attendance_notification(
                db=db,
                student_id=record.student_id,
                status=record.status,
                attendance_id=record_id,
                subject_name=subject.name if subject else None,
                subject_code=subject.code if subject else None,
                attendance_date=data.attendance_date,
                is_update=bool(existing),
            )
            # Check low attendance threshold (75%)
            check_and_create_low_attendance_warning(
                db=db,
                student_id=record.student_id,
                subject_id=data.subject_id,
                attendance_date=data.attendance_date,
                threshold=75.0,
            )

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
    date_from: Optional[str] = Query(None),
    date_to: Optional[str] = Query(None),
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
    elif current_user.role == "lecturer":
        assignments = (
            db.query(LecturerSubject)
            .filter(LecturerSubject.lecturer_id == current_user.id)
            .all()
        )
        assigned_subject_ids = [a.subject_id for a in assignments]
        if not assigned_subject_ids:
            return {"total": 0, "page": page, "limit": limit, "records": []}

        if subject_id and subject_id.strip():
            clean_sub = subject_id.strip()
            if clean_sub not in assigned_subject_ids:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Access denied. You are not assigned to this subject.",
                )
            query = query.filter(Attendance.subject_id == clean_sub)
        else:
            query = query.filter(Attendance.subject_id.in_(assigned_subject_ids))

        if student_id and student_id.strip():
            query = query.filter(Attendance.student_id == student_id.strip())
    elif student_id and student_id.strip():
        query = query.filter(Attendance.student_id == student_id.strip())

    if current_user.role != "lecturer" and subject_id and subject_id.strip():
        query = query.filter(Attendance.subject_id == subject_id.strip())

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
    records = query.order_by(Attendance.attendance_date.desc(), Attendance.created_at.desc()).offset(
        (page - 1) * limit
    ).limit(limit).all()

    # Pre-fetch relations to avoid N+1 queries
    student_ids = {r.student_id for r in records}
    subject_ids = {r.subject_id for r in records}
    marker_ids = {r.marked_by for r in records}

    students_map = {u.id: u for u in db.query(User).filter(User.id.in_(student_ids)).all()} if student_ids else {}
    subjects_map = {s.id: s for s in db.query(Subject).filter(Subject.id.in_(subject_ids)).all()} if subject_ids else {}
    markers_map = {u.id: u for u in db.query(User).filter(User.id.in_(marker_ids)).all()} if marker_ids else {}

    result = []
    for r in records:
        student = students_map.get(r.student_id)
        subject = subjects_map.get(r.subject_id)
        marker = markers_map.get(r.marked_by)
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
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")

    if current_user.role == "lecturer":
        is_assigned = db.query(LecturerSubject).filter(
            LecturerSubject.lecturer_id == current_user.id,
            LecturerSubject.subject_id == record.subject_id,
        ).first()
        if not is_assigned:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied. You are not assigned to this subject.",
            )


    student = db.query(User).filter(User.id == record.student_id).first()
    subject = db.query(Subject).filter(Subject.id == record.subject_id).first()
    att_date_str = record.attendance_date.isoformat() if hasattr(record.attendance_date, "isoformat") else str(record.attendance_date)

    return {
        "id": record.id,
        "student_id": record.student_id,
        "subject_id": record.subject_id,
        "attendance_date": att_date_str,
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

    old_status = record.status
    record.status = data.status
    record.marked_by = current_user.id
    db.commit()
    db.refresh(record)

    if old_status != data.status:
        subject = db.query(Subject).filter(Subject.id == record.subject_id).first()
        subj_name = subject.name if subject else None
        subj_code = subject.code if subject else None
        create_attendance_notification(
            db=db,
            student_id=record.student_id,
            status=record.status,
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

    att_date_str = record.attendance_date.isoformat() if hasattr(record.attendance_date, "isoformat") else str(record.attendance_date)
    return {
        "id": record.id,
        "student_id": record.student_id,
        "subject_id": record.subject_id,
        "attendance_date": att_date_str,
        "status": record.status,
        "marked_by": record.marked_by,
        "message": "Attendance updated successfully",
    }


@router.delete("/{attendance_id}", status_code=status.HTTP_204_NO_CONTENT,
               response_class=Response, summary="Delete an attendance record")
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
    return Response(status_code=status.HTTP_204_NO_CONTENT)

