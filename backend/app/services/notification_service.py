from typing import Optional, List
from datetime import date
from sqlalchemy.orm import Session
from sqlalchemy import func
from app.models.notification import Notification
from app.models.subject import Subject
from app.models.attendance import Attendance


def create_notification(
    db: Session,
    user_id: str,
    title: str,
    message: str,
    type: str,
    related_entity_type: Optional[str] = None,
    related_entity_id: Optional[str] = None,
    check_duplicate: bool = True,
) -> Notification:
    """Create a notification for a user, optionally checking for duplicates.
    Enforces idempotency when related_entity_type and related_entity_id are provided.
    """
    if check_duplicate and related_entity_type and related_entity_id:
        existing = db.query(Notification).filter(
            Notification.user_id == user_id,
            Notification.type == type,
            Notification.related_entity_type == related_entity_type,
            Notification.related_entity_id == related_entity_id,
        ).first()
        if existing:
            return existing

    notif = Notification(
        user_id=user_id,
        title=title,
        message=message,
        type=type,
        related_entity_type=related_entity_type,
        related_entity_id=related_entity_id,
        is_read=False,
    )
    db.add(notif)
    db.commit()
    db.refresh(notif)
    return notif


def create_enrollment_notification(
    db: Session,
    user_id: str,
    count: int,
    subject_name: Optional[str] = None,
    subject_code: Optional[str] = None,
    subject_id: Optional[str] = None,
) -> Optional[Notification]:
    """Create notification when student enrolls in subjects."""
    if count <= 0:
        return None

    if count == 1 and subject_name:
        title = "Subject Enrolled"
        subj_label = f"{subject_name} ({subject_code})" if subject_code else subject_name
        message = f"You have successfully enrolled in {subj_label}."
        related_id = f"enroll_{subject_id}_{user_id}" if subject_id else None
    else:
        title = "Subject Enrollment Successful"
        plural = "s" if count != 1 else ""
        message = f"You have successfully enrolled in {count} subject{plural}."
        related_id = None

    return create_notification(
        db=db,
        user_id=user_id,
        title=title,
        message=message,
        type="enrollment",
        related_entity_type="subject" if subject_id else "enrollment",
        related_entity_id=related_id,
        check_duplicate=True if related_id else False,
    )


def create_attendance_notification(
    db: Session,
    student_id: str,
    status: str,
    attendance_id: str,
    subject_name: Optional[str] = None,
    subject_code: Optional[str] = None,
    attendance_date: Optional[date] = None,
    is_update: bool = False,
    subject_code_or_name: Optional[str] = None,
) -> Notification:
    """Create notification when attendance is marked or updated for a student.
    Formats academic date and subject details cleanly.
    """
    capitalized_status = status.capitalize()

    # Determine subject label
    if subject_name and subject_code:
        subj_label = f"{subject_name} ({subject_code})"
    elif subject_name:
        subj_label = subject_name
    elif subject_code_or_name:
        subj_label = subject_code_or_name
    else:
        subj_label = "your subject"

    # Date string representation
    if attendance_date and hasattr(attendance_date, "strftime"):
        date_display = attendance_date.strftime("%d %B %Y")
    elif attendance_date:
        date_display = str(attendance_date)
    else:
        date_display = "today"

    if is_update:
        title = "Attendance Updated"
        message = f"Your attendance for {subj_label} on {date_display} has been updated to {capitalized_status}."
        tag = "upd"
    else:
        title = "Attendance Recorded"
        message = f"Your attendance for {subj_label} on {date_display} has been recorded as {capitalized_status}."
        tag = "rec"

    # Stable unique key prevents duplicate notifications for identical retries
    related_id = f"{attendance_id}_{tag}_{status.lower()}"

    return create_notification(
        db=db,
        user_id=student_id,
        title=title,
        message=message,
        type="attendance",
        related_entity_type="attendance",
        related_entity_id=related_id,
        check_duplicate=True,
    )


def check_and_create_low_attendance_warning(
    db: Session,
    student_id: str,
    subject_id: str,
    attendance_date: date,
    threshold: float = 75.0,
) -> Optional[Notification]:
    """Check if student's attendance in a subject is below threshold and create warning if so."""
    sub_total = db.query(func.count(Attendance.id)).filter(
        Attendance.student_id == student_id,
        Attendance.subject_id == subject_id,
    ).scalar() or 0

    if sub_total == 0:
        return None

    sub_present = db.query(func.count(Attendance.id)).filter(
        Attendance.student_id == student_id,
        Attendance.subject_id == subject_id,
        Attendance.status == "present",
    ).scalar() or 0

    percentage = round((sub_present / sub_total * 100), 1)

    if percentage < threshold:
        subject = db.query(Subject).filter(Subject.id == subject_id).first()
        subject_name = subject.name if subject else "your subject"
        display_pct = int(percentage) if percentage.is_integer() else percentage
        threshold_display = int(threshold) if threshold.is_integer() else threshold

        title = "Low Attendance Warning"
        message = f"Your attendance in {subject_name} is {display_pct}%, which is below the {threshold_display}% threshold."

        # Avoid duplicate warning for the same subject on the same attendance date
        date_str = attendance_date.isoformat() if hasattr(attendance_date, "isoformat") else str(attendance_date)
        related_id = f"{subject_id}_{date_str}"
        return create_notification(
            db=db,
            user_id=student_id,
            title=title,
            message=message,
            type="low_attendance",
            related_entity_type="low_attendance",
            related_entity_id=related_id,
            check_duplicate=True,
        )

    return None


def create_assignment_notification(
    db: Session,
    lecturer_id: str,
    subject_id: str,
    subject_name: str,
    subject_code: str,
    is_removal: bool = False,
) -> Notification:
    """Create notification when admin assigns or removes a lecturer teaching assignment."""
    subj_label = f"{subject_name} ({subject_code})" if subject_code else subject_name

    if is_removal:
        title = "Subject Assignment Removed"
        message = f"Your assignment to teach {subj_label} has been removed."
        related_id = f"assign_rm_{subject_id}_{lecturer_id}"
    else:
        title = "New Subject Assigned"
        message = f"You have been assigned to teach {subj_label}."
        related_id = f"assign_add_{subject_id}_{lecturer_id}"

    return create_notification(
        db=db,
        user_id=lecturer_id,
        title=title,
        message=message,
        type="system",
        related_entity_type="subject",
        related_entity_id=related_id,
        check_duplicate=True,
    )


def create_faculty_welcome_notification(
    db: Session,
    user_id: str,
    full_name: str,
) -> Notification:
    """Create in-app welcome notification when admin creates a lecturer account."""
    title = "Welcome to AttendX Faculty"
    message = f"Welcome, {full_name}! Your faculty account has been created. You can now view your assigned teaching schedule and manage student attendance."
    return create_notification(
        db=db,
        user_id=user_id,
        title=title,
        message=message,
        type="system",
        related_entity_type="faculty",
        related_entity_id=f"welcome_faculty_{user_id}",
        check_duplicate=True,
    )


def create_welcome_notification(db: Session, user_id: str) -> Notification:
    """Create system welcome notification on student registration."""
    return create_notification(
        db=db,
        user_id=user_id,
        title="Welcome to AttendX",
        message="Your AttendX student portal is ready to use.",
        type="system",
        related_entity_type="system",
        related_entity_id=f"welcome_student_{user_id}",
        check_duplicate=True,
    )


class NotificationService:
    create_notification = staticmethod(create_notification)
    create_enrollment_notification = staticmethod(create_enrollment_notification)
    create_attendance_notification = staticmethod(create_attendance_notification)
    check_and_create_low_attendance_warning = staticmethod(check_and_create_low_attendance_warning)
    create_assignment_notification = staticmethod(create_assignment_notification)
    create_faculty_welcome_notification = staticmethod(create_faculty_welcome_notification)
    create_welcome_notification = staticmethod(create_welcome_notification)
