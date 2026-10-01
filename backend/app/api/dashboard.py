import math
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func, case
from datetime import date, timedelta, datetime, timezone
from app.core.database import get_db
from app.core.security import get_current_user, get_current_admin, get_current_lecturer
from app.models.user import User
from app.models.subject import Subject
from app.models.student_subject import StudentSubject
from app.models.attendance import Attendance
from app.models.lecturer_subject import LecturerSubject
from app.models.notification import Notification
from app.schemas.dashboard import LecturerDashboardResponse

router = APIRouter(prefix="/api/dashboard", tags=["Dashboard"])
admin_router = APIRouter(prefix="/api/admin", tags=["Admin Dashboard"])

LOW_ATTENDANCE_THRESHOLD = 75.0


def calculate_classes_needed(present: int, total: int, threshold: float = 75.0) -> int:
    """Calculate how many consecutive classes a student needs to attend to reach threshold.
    Returns 0 if already at or above threshold, -1 if mathematically impossible (always possible with enough classes)."""
    if total == 0:
        return 0
    current = (present / total) * 100
    if current >= threshold:
        return 0
    denominator = 1 - threshold / 100
    if denominator <= 0:
        return -1  # threshold is 100%, mathematically impossible once absent
    needed = (threshold * total / 100 - present) / denominator
    return max(0, math.ceil(round(needed, 9)))



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

    catalog_order = ["IAI", "SE", "ISC", "BEFA", "ES", "AE-3 LAB"]
    subjects_stats.sort(key=lambda s: catalog_order.index(s["subject_code"]) if s["subject_code"] in catalog_order else 999)

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


def get_admin_dashboard_data(current_user: User, db: Session) -> dict:
    """Calculate and return comprehensive database-driven metrics for the Admin Dashboard."""
    total_students = db.query(func.count(User.id)).filter(User.role == "student").scalar() or 0
    total_lecturers = db.query(func.count(User.id)).filter(User.role == "lecturer").scalar() or 0
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
    todays_percentage = round((todays_present / todays_total * 100), 1) if todays_total > 0 else 0.0

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
        att_date_str = r.attendance_date.isoformat() if hasattr(r.attendance_date, "isoformat") else str(r.attendance_date)
        recent_attendance.append({
            "id": r.id,
            "student_name": student.full_name if student else "Unknown",
            "student_sid": student.student_id if student else "",
            "subject_name": subject.name if subject else "Unknown",
            "subject_code": subject.code if subject else "",
            "attendance_date": att_date_str,
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
            # Determine lowest/primary subject
            enrollments = db.query(StudentSubject).filter(StudentSubject.student_id == student.id).all()
            lowest_subject_code = ""
            lowest_sub_pct = 100.0
            for enr in enrollments:
                sub_tot = db.query(func.count(Attendance.id)).filter(
                    Attendance.student_id == student.id,
                    Attendance.subject_id == enr.subject_id
                ).scalar() or 0
                if sub_tot > 0:
                    sub_pres = db.query(func.count(Attendance.id)).filter(
                        Attendance.student_id == student.id,
                        Attendance.subject_id == enr.subject_id,
                        Attendance.status == "present"
                    ).scalar() or 0
                    sub_pct = round((sub_pres / sub_tot * 100), 1)
                    if sub_pct < lowest_sub_pct:
                        lowest_sub_pct = sub_pct
                        sub_obj = db.query(Subject).filter(Subject.id == enr.subject_id).first()
                        if sub_obj:
                            lowest_subject_code = sub_obj.code if sub_obj.code else sub_obj.name

            low_attendance_students.append({
                "id": student.id,
                "full_name": student.full_name,
                "student_id": student.student_id or "",
                "department": student.department or "",
                "year": student.year or 0,
                "section": student.section or "",
                "subject": lowest_subject_code or "All Subjects",
                "attendance_percentage": s_percentage,
                "total_classes": s_total,
                "present": s_present,
                "status": "Low",
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

    catalog_order = ["IAI", "SE", "ISC", "BEFA", "ES", "AE-3 LAB"]
    subject_stats.sort(key=lambda s: catalog_order.index(s["subject_code"]) if s["subject_code"] in catalog_order else 999)

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

    # Real recent system activity from database
    raw_activities = []
    recent_att_records = db.query(Attendance).order_by(Attendance.created_at.desc()).limit(8).all()
    for ra in recent_att_records:
        st = db.query(User).filter(User.id == ra.student_id).first()
        sb = db.query(Subject).filter(Subject.id == ra.subject_id).first()
        st_name = st.full_name if st else "Student"
        sb_name = sb.code if sb and sb.code else (sb.name if sb else "Subject")
        att_date_str = ra.attendance_date.isoformat() if hasattr(ra.attendance_date, "isoformat") else str(ra.attendance_date)
        created_str = ra.created_at.isoformat() if hasattr(ra.created_at, "isoformat") else str(ra.created_at)
        raw_activities.append({
            "id": f"att_{ra.id}",
            "title": f"Attendance marked: {st_name}",
            "description": f"{sb_name} — Marked {ra.status.capitalize()} for session {att_date_str}",
            "type": "attendance",
            "status": ra.status,
            "timestamp": created_str,
            "_sort_key": ra.created_at,
        })

    recent_enrollments = db.query(StudentSubject).order_by(StudentSubject.created_at.desc()).limit(6).all()
    for re in recent_enrollments:
        st = db.query(User).filter(User.id == re.student_id).first()
        sb = db.query(Subject).filter(Subject.id == re.subject_id).first()
        st_name = st.full_name if st else "Student"
        sb_name = sb.name if sb else "Subject"
        created_str = re.created_at.isoformat() if hasattr(re.created_at, "isoformat") else str(re.created_at)
        raw_activities.append({
            "id": f"enr_{re.id}",
            "title": f"Subject enrollment: {st_name}",
            "description": f"Enrolled in {sb_name}",
            "type": "enrollment",
            "status": "enrolled",
            "timestamp": created_str,
            "_sort_key": re.created_at,
        })

    raw_activities.sort(key=lambda x: x["_sort_key"] if x["_sort_key"] else datetime.min.replace(tzinfo=timezone.utc), reverse=True)
    recent_activity = [{k: v for k, v in a.items() if k != "_sort_key"} for a in raw_activities[:10]]

    return {
        "total_students": total_students,
        "total_lecturers": total_lecturers,
        "total_subjects": total_subjects,
        "metrics": {
            "total_students": total_students,
            "total_lecturers": total_lecturers,
            "total_subjects": total_subjects,
        },
        "todays_attendance": {
            "total": todays_total,
            "present": todays_present,
            "absent": todays_absent,
            "percentage": todays_percentage,
        },
        "average_attendance": avg_attendance,
        "recent_attendance": recent_attendance,
        "low_attendance_students": low_attendance_students,
        "subject_stats": subject_stats,
        "attendance_overview": subject_stats,
        "attendance_trend": attendance_trend,
        "recent_activity": recent_activity,
    }


@router.get("/admin", summary="Get admin dashboard data")
def admin_dashboard(
    current_user: User = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    """Return comprehensive dashboard data for admin (/api/dashboard/admin)."""
    return get_admin_dashboard_data(current_user, db)


@admin_router.get("/dashboard", summary="Get admin dashboard data")
def admin_dashboard_alias(
    current_user: User = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    """Return comprehensive dashboard data for admin (/api/admin/dashboard)."""
    return get_admin_dashboard_data(current_user, db)


def get_lecturer_dashboard_data(current_user: User, db: Session) -> dict:
    """Calculate and return comprehensive database-driven metrics for the Lecturer Dashboard.
    Enforces strict data isolation: only subjects assigned to the authenticated lecturer,
    unique students enrolled in those subjects, and attendance records for those subjects
    are returned.
    """
    # 1. Fetch assigned subjects for the authenticated lecturer
    assignments = (
        db.query(LecturerSubject)
        .filter(LecturerSubject.lecturer_id == current_user.id)
        .all()
    )
    assigned_subject_ids = [a.subject_id for a in assignments]

    lecturer_info = {
        "id": current_user.id,
        "name": current_user.full_name,
        "full_name": current_user.full_name,
        "email": current_user.email,
        "employee_id": current_user.employee_id,
        "department": current_user.department,
        "role": current_user.role,
    }

    # Unread notifications count
    unread_notifications = (
        db.query(func.count(Notification.id))
        .filter(Notification.user_id == current_user.id, Notification.is_read == False)
        .scalar()
        or 0
    )

    if not assigned_subject_ids:
        return {
            "lecturer": lecturer_info,
            "summary": {
                "total_subjects": 0,
                "total_students": 0,
                "total_attendance_records": 0,
                "attendance_records": 0,
                "average_attendance": 0.0,
            },
            "subjects": [],
            "attendance_overview": {
                "total_classes": 0,
                "present": 0,
                "absent": 0,
                "percentage": 0.0,
                "has_data": False,
            },
            "recent_activity": [],
            "unread_notifications_count": unread_notifications,
        }

    # 2. Get assigned Subject models with deterministic ordering (code asc, name asc)
    subjects = (
        db.query(Subject)
        .filter(Subject.id.in_(assigned_subject_ids))
        .order_by(Subject.code.asc(), Subject.name.asc())
        .all()
    )

    # 3. Unique students enrolled in any of the lecturer's assigned subjects
    # DISTINCT student_id across all assigned subjects ensures no double counting
    total_unique_students = (
        db.query(func.count(func.distinct(StudentSubject.student_id)))
        .filter(StudentSubject.subject_id.in_(assigned_subject_ids))
        .scalar()
        or 0
    )

    # 4. Subject-wise metrics
    subjects_list = []
    total_attendance_records = 0
    total_present_records = 0

    for subject in subjects:
        # Enrolled students for this specific subject
        enrolled_count = (
            db.query(func.count(StudentSubject.id))
            .filter(StudentSubject.subject_id == subject.id)
            .scalar()
            or 0
        )

        # Attendance stats for this subject
        sub_total = (
            db.query(func.count(Attendance.id))
            .filter(Attendance.subject_id == subject.id)
            .scalar()
            or 0
        )
        sub_present = (
            db.query(func.count(Attendance.id))
            .filter(Attendance.subject_id == subject.id, Attendance.status == "present")
            .scalar()
            or 0
        )
        sub_absent = sub_total - sub_present
        sub_percentage = round((sub_present / sub_total * 100), 1) if sub_total > 0 else 0.0

        total_attendance_records += sub_total
        total_present_records += sub_present

        subjects_list.append({
            "id": subject.id,
            "name": subject.name,
            "code": subject.code,
            "department": subject.department,
            "year": subject.year,
            "semester": subject.semester,
            "enrolled_students": enrolled_count,
            "total_classes": sub_total,
            "present": sub_present,
            "absent": sub_absent,
            "attendance_percentage": sub_percentage,
            "has_attendance": sub_total > 0,
        })

    total_absent_records = total_attendance_records - total_present_records
    overall_percentage = (
        round((total_present_records / total_attendance_records * 100), 1)
        if total_attendance_records > 0
        else 0.0
    )

    # 5. Recent activity (last 10 attendance records in the lecturer's subjects)
    recent_records = (
        db.query(Attendance)
        .filter(Attendance.subject_id.in_(assigned_subject_ids))
        .order_by(Attendance.attendance_date.desc(), Attendance.created_at.desc())
        .limit(10)
        .all()
    )

    recent_activity = []
    for r in recent_records:
        student = db.query(User).filter(User.id == r.student_id).first()
        subj = db.query(Subject).filter(Subject.id == r.subject_id).first()
        att_date_str = (
            r.attendance_date.isoformat()
            if hasattr(r.attendance_date, "isoformat")
            else str(r.attendance_date)
        )
        created_str = (
            r.created_at.isoformat()
            if hasattr(r.created_at, "isoformat")
            else str(r.created_at)
        )
        recent_activity.append({
            "id": r.id,
            "student_name": student.full_name if student else "Unknown Student",
            "student_sid": student.student_id if student else "",
            "subject_name": subj.name if subj else "Unknown Subject",
            "subject_code": subj.code if subj else "",
            "attendance_date": att_date_str,
            "status": r.status,
            "created_at": created_str,
        })

    return {
        "lecturer": lecturer_info,
        "summary": {
            "total_subjects": len(subjects),
            "total_students": total_unique_students,
            "total_attendance_records": total_attendance_records,
            "attendance_records": total_attendance_records,
            "average_attendance": overall_percentage,
        },
        "subjects": subjects_list,
        "attendance_overview": {
            "total_classes": total_attendance_records,
            "present": total_present_records,
            "absent": total_absent_records,
            "percentage": overall_percentage,
            "has_data": total_attendance_records > 0,
        },
        "recent_activity": recent_activity,
        "unread_notifications_count": unread_notifications,
    }


@router.get("/lecturer", response_model=LecturerDashboardResponse, summary="Get lecturer dashboard data")
def lecturer_dashboard(
    current_user: User = Depends(get_current_lecturer),
    db: Session = Depends(get_db),
):
    """Return comprehensive dashboard data for authenticated lecturer (/api/dashboard/lecturer)."""
    return get_lecturer_dashboard_data(current_user, db)


