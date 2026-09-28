from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import Optional, List
from app.core.database import get_db
from app.core.security import get_current_admin, hash_password, get_current_user
from app.models.user import User
from app.models.attendance import Attendance
from app.models.student_subject import StudentSubject
from app.schemas.user import (
    AdminCreateStudent,
    AdminUpdateStudent,
    UserResponse,
)

router = APIRouter(prefix="/api/students", tags=["Students"])


@router.get("", response_model=List[dict], summary="List all students")
def list_students(
    search: Optional[str] = Query(None, description="Search by name, email, or student ID"),
    department: Optional[str] = Query(None),
    year: Optional[int] = Query(None),
    section: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    limit: int = Query(50, ge=1, le=100),
    current_user: User = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    """List students with optional filters. Admin only."""
    query = db.query(User).filter(User.role == "student")

    if search:
        search_term = f"%{search}%"
        query = query.filter(
            (User.full_name.ilike(search_term))
            | (User.email.ilike(search_term))
            | (User.student_id.ilike(search_term))
        )
    if department:
        query = query.filter(User.department == department)
    if year:
        query = query.filter(User.year == year)
    if section:
        query = query.filter(User.section == section)

    total = query.count()
    students = query.order_by(User.full_name).offset((page - 1) * limit).limit(limit).all()

    result = []
    for student in students:
        # Calculate overall attendance for this student
        total_classes = db.query(func.count(Attendance.id)).filter(
            Attendance.student_id == student.id
        ).scalar() or 0
        present_classes = db.query(func.count(Attendance.id)).filter(
            Attendance.student_id == student.id,
            Attendance.status == "present",
        ).scalar() or 0
        percentage = round((present_classes / total_classes * 100), 1) if total_classes > 0 else 0.0

        result.append({
            "id": student.id,
            "full_name": student.full_name,
            "email": student.email,
            "student_id": student.student_id,
            "department": student.department,
            "year": student.year,
            "section": student.section,
            "role": student.role,
            "attendance_percentage": percentage,
            "total_classes": total_classes,
            "present_classes": present_classes,
            "created_at": student.created_at.isoformat() if student.created_at else None,
            "updated_at": student.updated_at.isoformat() if student.updated_at else None,
        })

    return result


@router.get("/count", summary="Get total student count")
def student_count(
    current_user: User = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    total = db.query(func.count(User.id)).filter(User.role == "student").scalar()
    return {"total": total}


@router.get("/{student_id}", summary="Get student details")
def get_student(
    student_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get a single student's details. Admin can view any, student can view self."""
    student = db.query(User).filter(User.id == student_id, User.role == "student").first()
    if not student:
        raise HTTPException(status_code=404, detail="Student not found")

    if current_user.role != "admin" and current_user.id != student_id:
        raise HTTPException(status_code=403, detail="Access denied")

    # Get enrolled subjects
    enrollments = db.query(StudentSubject).filter(StudentSubject.student_id == student_id).all()

    return {
        **UserResponse.model_validate(student).model_dump(),
        "enrollments": [
            {"id": e.id, "subject_id": e.subject_id, "created_at": e.created_at.isoformat() if e.created_at else None}
            for e in enrollments
        ],
    }


@router.post("", status_code=status.HTTP_201_CREATED, summary="Add a new student")
def create_student(
    data: AdminCreateStudent,
    current_user: User = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    """Create a new student account. Admin only."""
    # Check email uniqueness
    if db.query(User).filter(User.email == data.email.lower()).first():
        raise HTTPException(status_code=409, detail="Email already in use")
    # Check student_id uniqueness
    if db.query(User).filter(User.student_id == data.student_id).first():
        raise HTTPException(status_code=409, detail="Student ID already in use")

    student = User(
        full_name=data.full_name.strip(),
        email=data.email.lower().strip(),
        password_hash=hash_password(data.password),
        role="student",
        student_id=data.student_id.strip(),
        department=data.department.strip(),
        year=data.year,
        section=data.section.strip(),
    )
    db.add(student)
    db.commit()
    db.refresh(student)
    return UserResponse.model_validate(student)


@router.put("/{student_id}", summary="Update a student")
def update_student(
    student_id: str,
    data: AdminUpdateStudent,
    current_user: User = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    """Update student details. Admin only."""
    student = db.query(User).filter(User.id == student_id, User.role == "student").first()
    if not student:
        raise HTTPException(status_code=404, detail="Student not found")

    if data.full_name is not None:
        student.full_name = data.full_name.strip()
    if data.email is not None:
        existing = db.query(User).filter(User.email == data.email.lower(), User.id != student_id).first()
        if existing:
            raise HTTPException(status_code=409, detail="Email already in use")
        student.email = data.email.lower().strip()
    if data.student_id is not None:
        existing = db.query(User).filter(User.student_id == data.student_id, User.id != student_id).first()
        if existing:
            raise HTTPException(status_code=409, detail="Student ID already in use")
        student.student_id = data.student_id.strip()
    if data.department is not None:
        student.department = data.department.strip()
    if data.year is not None:
        student.year = data.year
    if data.section is not None:
        student.section = data.section.strip()

    db.commit()
    db.refresh(student)
    return UserResponse.model_validate(student)


@router.delete("/{student_id}", status_code=status.HTTP_204_NO_CONTENT, summary="Delete a student")
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
    return None
