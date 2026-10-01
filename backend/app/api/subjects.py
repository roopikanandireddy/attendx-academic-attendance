import math
from fastapi import APIRouter, Depends, HTTPException, status, Query, Response
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import Optional, List, Dict, Any
from app.core.database import get_db
from app.core.security import get_current_admin, get_current_user
from app.models.user import User
from app.models.subject import Subject
from app.models.student_subject import StudentSubject
from app.models.lecturer_subject import LecturerSubject
from app.schemas.subject import (
    SubjectCreate,
    SubjectUpdate,
    SubjectResponse,
    SubjectSummaryMetrics,
    SubjectListResponse,
    SubjectDetailResponse,
    EnrollmentCreate,
    EnrollmentResponse,
    BatchEnrollmentRequest,
    BatchEnrollmentResponse,
)

router = APIRouter(prefix="/api/subjects", tags=["Subjects"])
admin_router = APIRouter(prefix="/api/admin/subjects", tags=["Admin Subjects"])


def get_subjects_summary_data(db: Session) -> dict:
    """Calculate real database summary statistics for subjects."""
    total_subjects = db.query(func.count(Subject.id)).scalar() or 0
    assigned_subjects = (
        db.query(func.count(func.distinct(LecturerSubject.subject_id))).scalar() or 0
    )
    unassigned_subjects = max(0, total_subjects - assigned_subjects)
    total_enrollments = db.query(func.count(StudentSubject.id)).scalar() or 0

    return {
        "total_subjects": total_subjects,
        "assigned_subjects": assigned_subjects,
        "unassigned_subjects": unassigned_subjects,
        "total_enrollments": total_enrollments,
    }


def list_admin_subjects_data(
    db: Session,
    search: Optional[str] = None,
    department: Optional[str] = None,
    year: Optional[str] = None,
    semester: Optional[str] = None,
    assignment_status: Optional[str] = None,
    page: int = 1,
    limit: int = 10,
) -> dict:
    """List subjects with assigned faculty, enrolled student counts, and filters."""
    query = db.query(Subject)

    if search and search.strip():
        term = f"%{search.strip()}%"
        query = query.filter(
            (Subject.name.ilike(term)) | (Subject.code.ilike(term))
        )
    if department and department.strip() and department.lower() != "all":
        query = query.filter(Subject.department.ilike(f"%{department.strip()}%"))
    if year and year.strip() and year.lower() != "all":
        try:
            query = query.filter(Subject.year == int(year.strip()))
        except ValueError:
            pass
    if semester and semester.strip() and semester.lower() != "all":
        try:
            query = query.filter(Subject.semester == int(semester.strip()))
        except ValueError:
            pass

    if assignment_status and assignment_status.lower() != "all":
        assigned_subquery = db.query(LecturerSubject.subject_id).distinct()
        if assignment_status.lower() == "assigned":
            query = query.filter(Subject.id.in_(assigned_subquery))
        elif assignment_status.lower() == "unassigned":
            query = query.filter(Subject.id.not_in(assigned_subquery))

    total = query.count()
    pages = max(1, math.ceil(total / limit))
    offset = (page - 1) * limit

    subjects = query.order_by(Subject.code.asc()).offset(offset).limit(limit).all()

    items = []
    for s in subjects:
        # Assigned lecturers
        assignments = (
            db.query(LecturerSubject, User)
            .join(User, LecturerSubject.lecturer_id == User.id)
            .filter(LecturerSubject.subject_id == s.id)
            .all()
        )
        assigned_lecturers = [
            {
                "id": u.id,
                "full_name": u.full_name,
                "email": u.email,
                "employee_id": u.employee_id,
                "department": u.department,
                "assignment_id": ls.id,
            }
            for ls, u in assignments
        ]

        # Enrolled student count
        enrolled_count = (
            db.query(func.count(StudentSubject.id))
            .filter(StudentSubject.subject_id == s.id)
            .scalar()
            or 0
        )

        items.append({
            "id": s.id,
            "name": s.name,
            "code": s.code,
            "department": s.department,
            "year": s.year,
            "semester": s.semester,
            "assigned_lecturers": assigned_lecturers,
            "assigned_lecturers_count": len(assigned_lecturers),
            "enrolled_students_count": enrolled_count,
            "created_at": s.created_at.isoformat() if s.created_at else None,
        })

    return {
        "items": items,
        "total": total,
        "page": page,
        "limit": limit,
        "pages": pages,
    }


def get_subject_full_details(db: Session, subject_id: str) -> dict:
    """Retrieve complete subject details including assigned faculty and student roster."""
    subject = db.query(Subject).filter(Subject.id == subject_id).first()
    if not subject:
        raise HTTPException(status_code=404, detail="Subject not found")

    # Lecturers
    assignments = (
        db.query(LecturerSubject, User)
        .join(User, LecturerSubject.lecturer_id == User.id)
        .filter(LecturerSubject.subject_id == subject.id)
        .all()
    )
    assigned_lecturers = [
        {
            "id": u.id,
            "full_name": u.full_name,
            "email": u.email,
            "employee_id": u.employee_id,
            "department": u.department,
            "assignment_id": ls.id,
        }
        for ls, u in assignments
    ]

    # Enrolled students
    enrollments = (
        db.query(StudentSubject, User)
        .join(User, StudentSubject.student_id == User.id)
        .filter(StudentSubject.subject_id == subject.id)
        .order_by(User.full_name.asc())
        .all()
    )
    enrolled_students = [
        {
            "id": u.id,
            "full_name": u.full_name,
            "email": u.email,
            "student_id": u.student_id,
            "department": u.department,
            "year": u.year,
            "section": u.section,
            "enrollment_id": ss.id,
        }
        for ss, u in enrollments
    ]

    return {
        "id": subject.id,
        "name": subject.name,
        "code": subject.code,
        "department": subject.department,
        "year": subject.year,
        "semester": subject.semester,
        "assigned_lecturers": assigned_lecturers,
        "assigned_lecturers_count": len(assigned_lecturers),
        "enrolled_students": enrolled_students,
        "enrolled_students_count": len(enrolled_students),
        "created_at": subject.created_at.isoformat() if subject.created_at else None,
    }


def create_subject_record(db: Session, data: SubjectCreate) -> dict:
    """Create a new subject ensuring unique subject code."""
    clean_code = data.code.strip().upper()
    existing = db.query(Subject).filter(Subject.code == clean_code).first()
    if existing:
        raise HTTPException(status_code=409, detail="A subject with this code already exists")

    subject = Subject(
        name=data.name.strip(),
        code=clean_code,
        department=data.department.strip(),
        year=data.year,
        semester=data.semester,
    )
    db.add(subject)
    db.commit()
    db.refresh(subject)

    return {
        "id": subject.id,
        "name": subject.name,
        "code": subject.code,
        "department": subject.department,
        "year": subject.year,
        "semester": subject.semester,
        "assigned_lecturers": [],
        "assigned_lecturers_count": 0,
        "enrolled_students_count": 0,
        "created_at": subject.created_at.isoformat() if subject.created_at else None,
    }


def update_subject_record(db: Session, subject_id: str, data: SubjectUpdate) -> dict:
    """Update subject details."""
    subject = db.query(Subject).filter(Subject.id == subject_id).first()
    if not subject:
        raise HTTPException(status_code=404, detail="Subject not found")

    if data.code is not None:
        clean_code = data.code.strip().upper()
        existing = db.query(Subject).filter(Subject.code == clean_code, Subject.id != subject_id).first()
        if existing:
            raise HTTPException(status_code=409, detail="A subject with this code already exists")
        subject.code = clean_code

    if data.name is not None:
        subject.name = data.name.strip()
    if data.department is not None:
        subject.department = data.department.strip()
    if data.year is not None:
        subject.year = data.year
    if data.semester is not None:
        subject.semester = data.semester

    db.commit()
    db.refresh(subject)
    return get_subject_full_details(db, subject.id)


def delete_subject_record(db: Session, subject_id: str) -> None:
    """Delete a subject and all related enrollments / assignments."""
    subject = db.query(Subject).filter(Subject.id == subject_id).first()
    if not subject:
        raise HTTPException(status_code=404, detail="Subject not found")
    db.delete(subject)
    db.commit()


# ==========================================
# /api/subjects ROUTES (Student & Shared)
# ==========================================

@router.get("/summary", summary="Get subject summary metrics")
def get_subjects_summary_alias(
    current_user: User = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    return get_subjects_summary_data(db)


@router.get("", summary="List all subjects")
def list_subjects(
    search: Optional[str] = Query(None),
    department: Optional[str] = Query(None),
    year: Optional[str] = Query(None),
    semester: Optional[str] = Query(None),
    assignment_status: Optional[str] = Query(None),
    page: Optional[int] = Query(None, ge=1),
    limit: Optional[int] = Query(None, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """List subjects. If paginated (page or limit provided), returns paged object; otherwise list for backward compatibility."""
    if page is not None or limit is not None:
        return list_admin_subjects_data(
            db=db,
            search=search,
            department=department,
            year=year,
            semester=semester,
            assignment_status=assignment_status,
            page=page or 1,
            limit=limit or 10,
        )

    # Standard list without pagination for existing student views
    query = db.query(Subject)
    if search and search.strip():
        search_term = f"%{search.strip()}%"
        query = query.filter((Subject.name.ilike(search_term)) | (Subject.code.ilike(search_term)))
    if department and department.strip() and department.lower() != "all":
        query = query.filter(Subject.department == department.strip())
    if year and year.strip() and year.lower() != "all":
        try:
            query = query.filter(Subject.year == int(year.strip()))
        except ValueError:
            pass
    if semester and semester.strip() and semester.lower() != "all":
        try:
            query = query.filter(Subject.semester == int(semester.strip()))
        except ValueError:
            pass

    subjects = query.order_by(Subject.code).all()
    return [SubjectResponse.model_validate(s) for s in subjects]


@router.get("/my-enrollments", response_model=List[str], summary="Get currently enrolled subject IDs for student")
def get_my_enrollments(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Return list of subject IDs the current student is enrolled in."""
    enrollments = db.query(StudentSubject.subject_id).filter(
        StudentSubject.student_id == current_user.id
    ).all()
    return [e[0] for e in enrollments]


@router.post("/enroll-batch", response_model=BatchEnrollmentResponse, status_code=status.HTTP_201_CREATED,
              summary="Batch enroll current student in selected subjects")
def enroll_student_batch(
    data: BatchEnrollmentRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Enroll the current student in multiple subjects."""
    if not data.subject_ids:
        raise HTTPException(status_code=400, detail="No subjects selected")

    subjects = db.query(Subject).filter(Subject.id.in_(data.subject_ids)).all()
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
        from app.services.notification_service import create_enrollment_notification
        create_enrollment_notification(db=db, user_id=current_user.id, count=added_count)

    all_enrolled = db.query(StudentSubject.subject_id).filter(
        StudentSubject.student_id == current_user.id
    ).all()

    return BatchEnrollmentResponse(
        message=f"Successfully enrolled in {added_count} new subject(s)",
        enrolled_count=added_count,
        enrolled_subject_ids=[e[0] for e in all_enrolled],
    )


@router.post("/enroll", response_model=EnrollmentResponse, status_code=status.HTTP_201_CREATED,
              summary="Enroll a student in a subject")
def enroll_student(
    data: EnrollmentCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if current_user.role != "admin" and current_user.id != data.student_id:
        raise HTTPException(status_code=403, detail="Not authorized to enroll another student")

    student = db.query(User).filter(User.id == data.student_id, User.role == "student").first()
    if not student:
        raise HTTPException(status_code=404, detail="Student not found")
    subject = db.query(Subject).filter(Subject.id == data.subject_id).first()
    if not subject:
        raise HTTPException(status_code=404, detail="Subject not found")

    existing = db.query(StudentSubject).filter(
        StudentSubject.student_id == data.student_id,
        StudentSubject.subject_id == data.subject_id,
    ).first()
    if existing:
        raise HTTPException(status_code=409, detail="Student already enrolled in this subject")

    enrollment = StudentSubject(student_id=data.student_id, subject_id=data.subject_id)
    db.add(enrollment)
    db.commit()
    db.refresh(enrollment)
    from app.services.notification_service import create_enrollment_notification
    create_enrollment_notification(
        db=db,
        user_id=data.student_id,
        count=1,
        subject_name=subject.name,
        subject_code=subject.code,
        subject_id=subject.id,
    )
    return EnrollmentResponse.model_validate(enrollment)


@router.delete("/enroll/{enrollment_id}", status_code=status.HTTP_204_NO_CONTENT,
               response_class=Response, summary="Remove student enrollment")
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
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get("/{subject_id}", summary="Get subject details")
def get_subject(
    subject_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    details = get_subject_full_details(db, subject_id)
    if current_user.role == "student":
        # Privacy protection: omit full student roster for students
        details["enrolled_students"] = []
    elif current_user.role == "lecturer":
        # If lecturer is not assigned to this subject, omit enrolled student roster
        assignment = db.query(LecturerSubject).filter(
            LecturerSubject.lecturer_id == current_user.id,
            LecturerSubject.subject_id == subject_id,
        ).first()
        if not assignment:
            details["enrolled_students"] = []
    return details


@router.post("", status_code=status.HTTP_201_CREATED, summary="Create a new subject")
def create_subject(
    data: SubjectCreate,
    current_user: User = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    return create_subject_record(db, data)


@router.put("/{subject_id}", summary="Update a subject")
def update_subject(
    subject_id: str,
    data: SubjectUpdate,
    current_user: User = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    return update_subject_record(db, subject_id, data)


@router.delete("/{subject_id}", status_code=status.HTTP_204_NO_CONTENT,
               response_class=Response, summary="Delete a subject")
def delete_subject(
    subject_id: str,
    current_user: User = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    delete_subject_record(db, subject_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get("/{subject_id}/students", summary="Get students enrolled in a subject")
def get_subject_students(
    subject_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    subject = db.query(Subject).filter(Subject.id == subject_id).first()
    if not subject:
        raise HTTPException(status_code=404, detail="Subject not found")

    if current_user.role == "student":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied. Students cannot view subject student rosters.",
        )

    if current_user.role == "lecturer":
        assignment = db.query(LecturerSubject).filter(
            LecturerSubject.lecturer_id == current_user.id,
            LecturerSubject.subject_id == subject_id,
        ).first()
        if not assignment:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied. You are not assigned to this subject.",
            )

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


# ==========================================
# /api/admin/subjects DEDICATED ROUTES
# ==========================================

@admin_router.get("/summary", summary="Get subject summary metrics")
def admin_get_subjects_summary(
    current_user: User = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    return get_subjects_summary_data(db)


@admin_router.get("", summary="List all subjects for admin")
def admin_list_subjects(
    search: Optional[str] = Query(None),
    department: Optional[str] = Query(None),
    year: Optional[str] = Query(None),
    semester: Optional[str] = Query(None),
    assignment_status: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    limit: int = Query(10, ge=1, le=100),
    current_user: User = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    return list_admin_subjects_data(
        db=db,
        search=search,
        department=department,
        year=year,
        semester=semester,
        assignment_status=assignment_status,
        page=page,
        limit=limit,
    )


@admin_router.get("/{subject_id}", summary="Get subject details for admin")
def admin_get_subject(
    subject_id: str,
    current_user: User = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    return get_subject_full_details(db, subject_id)


@admin_router.post("", status_code=status.HTTP_201_CREATED, summary="Create subject for admin")
def admin_create_subject(
    data: SubjectCreate,
    current_user: User = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    return create_subject_record(db, data)


@admin_router.put("/{subject_id}", summary="Update subject for admin")
def admin_update_subject(
    subject_id: str,
    data: SubjectUpdate,
    current_user: User = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    return update_subject_record(db, subject_id, data)


@admin_router.delete("/{subject_id}", status_code=status.HTTP_204_NO_CONTENT,
                    response_class=Response, summary="Delete subject for admin")
def admin_delete_subject(
    subject_id: str,
    current_user: User = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    delete_subject_record(db, subject_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


# Subject-Lecturer assignment convenience routes on /api/admin/subjects
@admin_router.get("/{subject_id}/lecturers", summary="Get lecturers assigned to a subject")
def admin_get_subject_lecturers(
    subject_id: str,
    current_user: User = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    subject = db.query(Subject).filter(Subject.id == subject_id).first()
    if not subject:
        raise HTTPException(status_code=404, detail="Subject not found")

    assignments = (
        db.query(LecturerSubject, User)
        .join(User, LecturerSubject.lecturer_id == User.id)
        .filter(LecturerSubject.subject_id == subject.id)
        .all()
    )
    return [
        {
            "id": u.id,
            "full_name": u.full_name,
            "email": u.email,
            "employee_id": u.employee_id,
            "department": u.department,
            "assignment_id": ls.id,
        }
        for ls, u in assignments
    ]


@admin_router.post("/{subject_id}/lecturers", status_code=status.HTTP_201_CREATED, summary="Assign lecturer to subject")
def admin_assign_lecturer_to_subject(
    subject_id: str,
    data: Dict[str, str],
    current_user: User = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    lecturer_id = data.get("lecturer_id")
    if not lecturer_id:
        raise HTTPException(status_code=400, detail="lecturer_id is required")

    subject = db.query(Subject).filter(Subject.id == subject_id).first()
    if not subject:
        raise HTTPException(status_code=404, detail="Subject not found")

    lecturer = db.query(User).filter(User.id == lecturer_id, User.role == "lecturer").first()
    if not lecturer:
        raise HTTPException(status_code=404, detail="Lecturer not found")

    if not lecturer.is_active:
        raise HTTPException(status_code=400, detail="Cannot assign an inactive lecturer")

    existing = db.query(LecturerSubject).filter(
        LecturerSubject.lecturer_id == lecturer_id,
        LecturerSubject.subject_id == subject_id,
    ).first()
    if existing:
        raise HTTPException(status_code=409, detail="Lecturer is already assigned to this subject")

    assignment = LecturerSubject(lecturer_id=lecturer_id, subject_id=subject_id)
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
        "subject_code": subject.code,
        "subject_name": subject.name,
        "message": f"Successfully assigned {lecturer.full_name} to {subject.code}",
    }


@admin_router.delete("/{subject_id}/lecturers/{lecturer_id}", status_code=status.HTTP_204_NO_CONTENT,
                     response_class=Response, summary="Unassign lecturer from subject")
def admin_unassign_lecturer_from_subject(
    subject_id: str,
    lecturer_id: str,
    current_user: User = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    assignment = db.query(LecturerSubject).filter(
        LecturerSubject.subject_id == subject_id,
        LecturerSubject.lecturer_id == lecturer_id,
    ).first()
    if not assignment:
        raise HTTPException(status_code=404, detail="Teaching assignment not found")

    subj = db.query(Subject).filter(Subject.id == subject_id).first()
    subj_name = subj.name if subj else "the subject"
    subj_code = subj.code if subj else ""

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

    return Response(status_code=status.HTTP_204_NO_CONTENT)
