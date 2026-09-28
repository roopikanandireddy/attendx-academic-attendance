from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func, case
from datetime import date, timedelta, datetime, timezone
from app.core.database import get_db
from app.core.security import get_current_user
from app.models.user import User
from app.models.subject import Subject
from app.models.student_subject import StudentSubject
from app.models.attendance import Attendance

router = APIRouter(prefix="/api/dashboard", tags=["Dashboard"])

LOW_ATTENDANCE_THRESHOLD = 75.0


def calculate_classes_needed(present: int, total: int, threshold: float = 75.0) -> int:
    """Calculate how many consecutive classes a student needs to attend to reach threshold.
    Returns 0 if already at or above threshold, -1 if mathematically impossible (always possible with enough classes)."""
    if total == 0:
        return 0
    current = (present / total) * 100
    if current >= threshold:
        return 0
    # Need: (present + x) / (total + x) >= threshold/100
    # present + x >= (threshold/100) * (total + x)
    # present + x >= threshold*total/100 + threshold*x/100
    # x - threshold*x/100 >= threshold*total/100 - present
    # x * (1 - threshold/100) >= threshold*total/100 - present
    # x >= (threshold*total/100 - present) / (1 - threshold/100)
    denominator = 1 - threshold / 100
    if denominator <= 0:
        return -1  # threshold is 100%, mathematically impossible once absent
    needed = (threshold * total / 100 - present) / denominator
    return max(0, int(needed) + (1 if needed != int(needed) else 0))


@router.get("/student", summary="Get student dashboard data")
def student_dashboard(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Return comprehensive dashboard data for the current student."""
    if current_user.role != "student":
        raise HTTPException(status_code=403, detail="Student access only")

    # Get enrolled subjects
    enrollments = db.query(StudentSubject).filter(
        StudentSubject.student_id == current_user.id
    ).all()
    subject_ids = [e.subject_id for e in enrollments]

    # Overall stats
    total_classes = 0
    total_present = 0
    total_absent = 0
    subjects_stats = []
    low_attendance_subjects = []

    for subject_id in subject_ids:
        subject = db.query(Subject).filter(Subject.id == subject_id).first()
        if not subject:
            continue

        sub_total = db.query(func.count(Attendance.id)).filter(
            Attendance.student_id == current_user.id,
            Attendance.subject_id == subject_id,
        ).scalar() or 0

        sub_present = db.query(func.count(Attendance.id)).filter(
            Attendance.student_id == current_user.id,
            Attendance.subject_id == subject_id,
            Attendance.status == "present",
        ).scalar() or 0

        sub_absent = sub_total - sub_present
        sub_percentage = round((sub_present / sub_total * 100), 1) if sub_total > 0 else 0.0

        total_classes += sub_total
        total_present += sub_present
        total_absent += sub_absent

        stat = {
            "subject_id": subject_id,
            "subject_name": subject.name,
            "subject_code": subject.code,
            "total_classes": sub_total,
            "present": sub_present,
            "absent": sub_absent,
            "percentage": sub_percentage,
        }
        subjects_stats.append(stat)

        if sub_total > 0 and sub_percentage < LOW_ATTENDANCE_THRESHOLD:
            classes_needed = calculate_classes_needed(sub_present, sub_total)
            low_attendance_subjects.append({
                **stat,
                "classes_needed": classes_needed,
            })

    overall_percentage = round((total_present / total_classes * 100), 1) if total_classes > 0 else 0.0

    # Recent attendance (last 10)
    recent = db.query(Attendance).filter(
        Attendance.student_id == current_user.id
    ).order_by(Attendance.attendance_date.desc()).limit(10).all()

    recent_attendance = []
    for r in recent:
        subject = db.query(Subject).filter(Subject.id == r.subject_id).first()
        recent_attendance.append({
            "id": r.id,
            "subject_name": subject.name if subject else "Unknown",
            "subject_code": subject.code if subject else "",
            "attendance_date": r.attendance_date.isoformat(),
            "status": r.status,
        })

    return {
        "user": {
            "id": current_user.id,
            "full_name": current_user.full_name,
            "email": current_user.email,
            "student_id": current_user.student_id,
            "department": current_user.department,
            "year": current_user.year,
            "section": current_user.section,
        },
        "overall_stats": {
            "total_classes": total_classes,
            "present": total_present,
            "absent": total_absent,
            "percentage": overall_percentage,
        },
        "subjects": subjects_stats,
        "recent_attendance": recent_attendance,
        "low_attendance_subjects": low_attendance_subjects,
    }


@router.get("/admin", summary="Get admin dashboard data")
def admin_dashboard(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Return comprehensive dashboard data for admin."""
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Admin access only")

    total_students = db.query(func.count(User.id)).filter(User.role == "student").scalar() or 0
    total_subjects = db.query(func.count(Subject.id)).scalar() or 0

    # Today's attendance
    today = date.today()
    todays_total = db.query(func.count(Attendance.id)).filter(
        Attendance.attendance_date == today
    ).scalar() or 0
    todays_present = db.query(func.count(Attendance.id)).filter(
        Attendance.attendance_date == today,
        Attendance.status == "present",
    ).scalar() or 0
    todays_absent = todays_total - todays_present

    # Overall average attendance
    all_total = db.query(func.count(Attendance.id)).scalar() or 0
    all_present = db.query(func.count(Attendance.id)).filter(
        Attendance.status == "present"
    ).scalar() or 0
    avg_attendance = round((all_present / all_total * 100), 1) if all_total > 0 else 0.0

    # Recent attendance records (last 10)
    recent = db.query(Attendance).order_by(
        Attendance.attendance_date.desc(), Attendance.created_at.desc()
    ).limit(10).all()

    recent_attendance = []
    for r in recent:
        student = db.query(User).filter(User.id == r.student_id).first()
        subject = db.query(Subject).filter(Subject.id == r.subject_id).first()
        recent_attendance.append({
            "id": r.id,
            "student_name": student.full_name if student else "Unknown",
            "student_sid": student.student_id if student else "",
            "subject_name": subject.name if subject else "Unknown",
            "subject_code": subject.code if subject else "",
            "attendance_date": r.attendance_date.isoformat(),
            "status": r.status,
        })

    # Low-attendance students (below 75%)
    students = db.query(User).filter(User.role == "student").all()
    low_attendance_students = []
    for student in students:
        s_total = db.query(func.count(Attendance.id)).filter(
            Attendance.student_id == student.id
        ).scalar() or 0
        if s_total == 0:
            continue
        s_present = db.query(func.count(Attendance.id)).filter(
            Attendance.student_id == student.id,
            Attendance.status == "present",
        ).scalar() or 0
        s_percentage = round((s_present / s_total * 100), 1)
        if s_percentage < LOW_ATTENDANCE_THRESHOLD:
            low_attendance_students.append({
                "id": student.id,
                "full_name": student.full_name,
                "student_id": student.student_id,
                "department": student.department,
                "year": student.year,
                "section": student.section,
                "attendance_percentage": s_percentage,
                "total_classes": s_total,
                "present": s_present,
                "classes_needed": calculate_classes_needed(s_present, s_total),
            })

    # Subject-wise stats
    subjects = db.query(Subject).all()
    subject_stats = []
    for subject in subjects:
        sub_total = db.query(func.count(Attendance.id)).filter(
            Attendance.subject_id == subject.id
        ).scalar() or 0
        sub_present = db.query(func.count(Attendance.id)).filter(
            Attendance.subject_id == subject.id,
            Attendance.status == "present",
        ).scalar() or 0
        sub_percentage = round((sub_present / sub_total * 100), 1) if sub_total > 0 else 0.0
        subject_stats.append({
            "subject_id": subject.id,
            "subject_name": subject.name,
            "subject_code": subject.code,
            "total_classes": sub_total,
            "present": sub_present,
            "absent": sub_total - sub_present,
            "percentage": sub_percentage,
        })

    # Attendance trend (last 14 days)
    attendance_trend = []
    for i in range(13, -1, -1):
        d = today - timedelta(days=i)
        d_total = db.query(func.count(Attendance.id)).filter(
            Attendance.attendance_date == d
        ).scalar() or 0
        d_present = db.query(func.count(Attendance.id)).filter(
            Attendance.attendance_date == d,
            Attendance.status == "present",
        ).scalar() or 0
        attendance_trend.append({
            "date": d.isoformat(),
            "total": d_total,
            "present": d_present,
            "absent": d_total - d_present,
            "percentage": round((d_present / d_total * 100), 1) if d_total > 0 else 0,
        })

    return {
        "total_students": total_students,
        "total_subjects": total_subjects,
        "todays_attendance": {
            "total": todays_total,
            "present": todays_present,
            "absent": todays_absent,
            "percentage": round((todays_present / todays_total * 100), 1) if todays_total > 0 else 0,
        },
        "average_attendance": avg_attendance,
        "recent_attendance": recent_attendance,
        "low_attendance_students": low_attendance_students,
        "subject_stats": subject_stats,
        "attendance_trend": attendance_trend,
    }
