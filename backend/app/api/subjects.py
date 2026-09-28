from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import Optional, List
from app.core.database import get_db
from app.core.security import get_current_admin, get_current_user
from app.models.user import User
from app.models.subject import Subject
from app.models.student_subject import StudentSubject
from app.schemas.subject import (
    SubjectCreate,
    SubjectUpdate,
    SubjectResponse,
    EnrollmentCreate,
    EnrollmentResponse,
)

router = APIRouter(prefix="/api/subjects", tags=["Subjects"])


@router.get("", response_model=List[SubjectResponse], summary="List all subjects")
def list_subjects(
    search: Optional[str] = Query(None),
    department: Optional[str] = Query(None),
    year: Optional[int] = Query(None),
    semester: Optional[int] = Query(None),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """List subjects with optional filters."""
    query = db.query(Subject)

    if search:
        search_term = f"%{search}%"
        query = query.filter(
            (Subject.name.ilike(search_term)) | (Subject.code.ilike(search_term))
        )
    if department:
        query = query.filter(Subject.department == department)
    if year:
        query = query.filter(Subject.year == year)
    if semester:
        query = query.filter(Subject.semester == semester)

    subjects = query.order_by(Subject.code).all()
    return [SubjectResponse.model_validate(s) for s in subjects]


@router.get("/{subject_id}", response_model=SubjectResponse, summary="Get subject details")
def get_subject(
    subject_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    subject = db.query(Subject).filter(Subject.id == subject_id).first()
    if not subject:
        raise HTTPException(status_code=404, detail="Subject not found")
    return SubjectResponse.model_validate(subject)


@router.post("", response_model=SubjectResponse, status_code=status.HTTP_201_CREATED,
             summary="Create a new subject")
def create_subject(
    data: SubjectCreate,
    current_user: User = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    """Create a new subject. Admin only."""
    existing = db.query(Subject).filter(Subject.code == data.code.upper()).first()
    if existing:
        raise HTTPException(status_code=409, detail="Subject code already exists")

    subject = Subject(
        name=data.name.strip(),
        code=data.code.strip().upper(),
        department=data.department.strip(),
        year=data.year,
        semester=data.semester,
    )
    db.add(subject)
    db.commit()
    db.refresh(subject)
    return SubjectResponse.model_validate(subject)


@router.put("/{subject_id}", response_model=SubjectResponse, summary="Update a subject")
def update_subject(
    subject_id: str,
    data: SubjectUpdate,
    current_user: User = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    """Update subject details. Admin only."""
    subject = db.query(Subject).filter(Subject.id == subject_id).first()
    if not subject:
        raise HTTPException(status_code=404, detail="Subject not found")

    if data.name is not None:
        subject.name = data.name.strip()
    if data.code is not None:
        existing = db.query(Subject).filter(Subject.code == data.code.upper(), Subject.id != subject_id).first()
        if existing:
            raise HTTPException(status_code=409, detail="Subject code already exists")
        subject.code = data.code.strip().upper()
    if data.department is not None:
        subject.department = data.department.strip()
    if data.year is not None:
        subject.year = data.year
    if data.semester is not None:
        subject.semester = data.semester

    db.commit()
    db.refresh(subject)
    return SubjectResponse.model_validate(subject)


@router.delete("/{subject_id}", status_code=status.HTTP_204_NO_CONTENT, summary="Delete a subject")
def delete_subject(
    subject_id: str,
    current_user: User = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    """Delete a subject and all related records. Admin only."""
    subject = db.query(Subject).filter(Subject.id == subject_id).first()
    if not subject:
        raise HTTPException(status_code=404, detail="Subject not found")
    db.delete(subject)
    db.commit()
    return None


# Enrollment endpoints
@router.post("/enroll", response_model=EnrollmentResponse, status_code=status.HTTP_201_CREATED,
              summary="Enroll a student in a subject")
def enroll_student(
    data: EnrollmentCreate,
    current_user: User = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    """Assign a student to a subject. Admin only."""
    # Validate student exists
    student = db.query(User).filter(User.id == data.student_id, User.role == "student").first()
    if not student:
        raise HTTPException(status_code=404, detail="Student not found")
    # Validate subject exists
    subject = db.query(Subject).filter(Subject.id == data.subject_id).first()
    if not subject:
        raise HTTPException(status_code=404, detail="Subject not found")
    # Check duplicate
    existing = db.query(StudentSubject).filter(
        StudentSubject.student_id == data.student_id,
        StudentSubject.subject_id == data.subject_id,
    ).first()
    if existing:
        raise HTTPException(status_code=409, detail="Student already enrolled in this subject")

    enrollment = StudentSubject(
        student_id=data.student_id,
        subject_id=data.subject_id,
    )
    db.add(enrollment)
    db.commit()
    db.refresh(enrollment)
    return EnrollmentResponse.model_validate(enrollment)


@router.delete("/enroll/{enrollment_id}", status_code=status.HTTP_204_NO_CONTENT,
               summary="Remove student enrollment")
def unenroll_student(
    enrollment_id: str,
    current_user: User = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    enrollment = db.query(StudentSubject).filter(StudentSubject.id == enrollment_id).first()
    if not enrollment:
        raise HTTPException(status_code=404, detail="Enrollment not found")
    db.delete(enrollment)
    db.commit()
    return None


@router.get("/{subject_id}/students", summary="Get students enrolled in a subject")
def get_subject_students(
    subject_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get all students enrolled in a specific subject."""
    subject = db.query(Subject).filter(Subject.id == subject_id).first()
    if not subject:
        raise HTTPException(status_code=404, detail="Subject not found")

    enrollments = db.query(StudentSubject).filter(StudentSubject.subject_id == subject_id).all()
    students = []
    for e in enrollments:
        student = db.query(User).filter(User.id == e.student_id).first()
        if student:
            students.append({
                "id": student.id,
                "full_name": student.full_name,
                "email": student.email,
                "student_id": student.student_id,
                "department": student.department,
                "year": student.year,
                "section": student.section,
                "enrollment_id": e.id,
            })
    return students
