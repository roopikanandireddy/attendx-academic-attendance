"""
AttendX — Level 2 Comprehensive Unit Testing Suite
Tests individual functions, calculation engines, security utilities,
service methods, schema validators, and database constraints across all 7 test cases:
1. Valid Input
2. Invalid Input
3. Boundary Input
4. Missing Input
5. Unauthorized Input
6. Duplicate Input
7. Failure / Exception Condition
"""
import sys
import os
from datetime import date, timedelta, datetime, timezone
import uuid
from fastapi import HTTPException
from pydantic import ValidationError

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__))))

from app.core.security import (
    hash_password,
    verify_password,
    create_access_token,
    decode_token,
)
from app.core.database import SessionLocal, Base, engine
from app.models.user import User
from app.models.subject import Subject
from app.models.student_subject import StudentSubject
from app.models.lecturer_subject import LecturerSubject
from app.models.attendance import Attendance
from app.models.notification import Notification

from app.api.dashboard import calculate_classes_needed
from app.api.students import calculate_student_attendance, get_students_summary_data
from app.api.lecturers import get_lecturers_summary_data
from app.api.subjects import get_subjects_summary_data
from app.api.assignments import get_assignments_summary_data
from app.schemas.attendance import (
    AttendanceMark,
    AttendanceUpdate,
    AttendanceBulkCreate,
)
from app.schemas.user import AdminCreateStudent, AdminCreateLecturer
from app.schemas.subject import SubjectCreate
from app.services.notification_service import (
    create_notification,
    create_enrollment_notification,
    create_attendance_notification,
)
from app.services.lecturer_report_service import LecturerReportService


def run_unit_tests():
    print("=" * 80)
    print("ATTENDX — LEVEL 2 COMPREHENSIVE UNIT TESTING SUITE")
    print("=" * 80)

    db = SessionLocal()
    total_checks = 0
    passed_checks = 0

    def check(title: str, condition: bool, details: str = ""):
        nonlocal total_checks, passed_checks
        total_checks += 1
        if condition:
            passed_checks += 1
            print(f"  [PASS] {title}")
        else:
            print(f"  [FAIL] {title} — {details}")
            assert False, f"Check Failed: {title} — {details}"

    temp_entities = []

    try:
        # ====================================================================
        # UNIT GROUP 1: AUTHENTICATION & SECURITY UNITS
        # ====================================================================
        print("\n--- 1. Authentication & Security Units ---")
        raw_pw = "SecureTestPassword123!"
        hashed = hash_password(raw_pw)

        # 1.1 Valid input: Hash and verify password
        check("1.1 Valid password hashes to bcrypt string", hashed.startswith("$2b$") or hashed.startswith("$2a$"))
        check("1.1 Valid password verifies true against hash", verify_password(raw_pw, hashed) is True)

        # 1.2 Invalid input: Wrong password
        check("1.2 Wrong password verifies false", verify_password("WrongPassword!", hashed) is False)

        # 1.3 Boundary input: Empty password verification
        check("1.3 Empty string verifies false", verify_password("", hashed) is False)

        # 1.4 Valid token generation & decoding
        user_payload = {"sub": "user_unit_test_id", "email": "test@attendx.com", "role": "student"}
        token = create_access_token(user_payload)
        decoded = decode_token(token)
        check("1.4 Access token decodes correct subject claim", decoded.get("sub") == user_payload["sub"])
        check("1.4 Access token contains expiration claim", "exp" in decoded)

        # 1.5 Expired token handling
        expired_token = create_access_token(user_payload, expires_delta=timedelta(seconds=-10))
        expired_rejected = False
        try:
            decode_token(expired_token)
        except HTTPException as e:
            expired_rejected = (e.status_code == 401)
        check("1.5 Expired token safely rejected with HTTP 401", expired_rejected)

        # 1.6 Malformed token handling
        malformed_rejected = False
        try:
            decode_token("this.is.a.malformed.jwt.token")
        except HTTPException as e:
            malformed_rejected = (e.status_code == 401)
        check("1.6 Malformed token safely rejected with HTTP 401", malformed_rejected)

        # ====================================================================
        # UNIT GROUP 2: ATTENDANCE ENGINE MATHEMATICS
        # ====================================================================
        print("\n--- 2. Attendance Engine Math Units ---")

        # 2.1 Boundary: Zero classes held
        check("2.1 Zero classes attended/total -> 0 classes needed", calculate_classes_needed(0, 0, 75.0) == 0)

        # 2.2 Boundary: Exactly 75% attendance
        check("2.2 Exactly 75% (3/4) -> 0 classes needed", calculate_classes_needed(3, 4, 75.0) == 0)

        # 2.3 Above threshold: 80% (8/10)
        check("2.3 Above 75% (8/10 = 80%) -> 0 classes needed", calculate_classes_needed(8, 10, 75.0) == 0)

        # 2.4 Below threshold: 50% (5/10) -> Needs 10 classes
        # Formula: (0.75 * 10 - 5) / (1 - 0.75) = 2.5 / 0.25 = 10
        check("2.4 Below 75% (5/10 = 50%) -> Exactly 10 classes needed", calculate_classes_needed(5, 10, 75.0) == 10)

        # 2.5 Below threshold: 50% (2/4) -> Needs 4 classes
        # Formula: (0.75 * 4 - 2) / 0.25 = 1 / 0.25 = 4
        check("2.5 Below 75% (2/4 = 50%) -> Exactly 4 classes needed", calculate_classes_needed(2, 4, 75.0) == 4)

        # 2.6 Fractional round up: 2/5 (40%) -> (3.75 - 2)/0.25 = 7
        check("2.6 Fractional threshold correctly rounded up with ceil", calculate_classes_needed(2, 5, 75.0) == 7)

        # ====================================================================
        # UNIT GROUP 3: SCHEMA VALIDATORS (ATTENDANCE & USERS)
        # ====================================================================
        print("\n--- 3. Schema Validator Units ---")

        # 3.1 AttendanceMark valid statuses
        m_present = AttendanceMark(student_id="stu_1", status="present")
        m_absent = AttendanceMark(student_id="stu_2", status="ABSENT  ")
        check("3.1 Valid 'present' status parsed", m_present.status == "present")
        check("3.1 Normalized uppercase/whitespace 'absent' status parsed", m_absent.status == "absent")

        # 3.2 Invalid status rejection
        invalid_status_caught = False
        try:
            AttendanceMark(student_id="stu_3", status="late")
        except ValidationError:
            invalid_status_caught = True
        check("3.2 Invalid status 'late' raises ValidationError", invalid_status_caught)

        # 3.3 AttendanceBulkCreate missing records rejection
        empty_bulk_caught = False
        try:
            AttendanceBulkCreate(subject_id="sub_1", attendance_date=date.today(), records=[])
        except ValidationError:
            empty_bulk_caught = True
        check("3.3 Empty records list in AttendanceBulkCreate raises ValidationError", empty_bulk_caught)

        # 3.4 AttendanceUpdate valid and invalid status
        u_present = AttendanceUpdate(status="present")
        check("3.4 Valid status in AttendanceUpdate parsed", u_present.status == "present")
        invalid_update_caught = False
        try:
            AttendanceUpdate(status="excused")
        except ValidationError:
            invalid_update_caught = True
        check("3.4 Invalid status 'excused' in AttendanceUpdate raises ValidationError", invalid_update_caught)

        # 3.5 AdminCreateStudent valid & missing fields
        valid_stu = AdminCreateStudent(
            email="valid_student@attendx.com",
            full_name="Valid Student",
            password="Password123!",
            student_id="STU-VAL-01",
            department="Computer Science",
            year=2,
            section="A",
        )
        check("3.5 Valid AdminCreateStudent instantiated", valid_stu.email == "valid_student@attendx.com")

        missing_email_caught = False
        try:
            AdminCreateStudent(
                full_name="No Email",
                password="Password123!",
                student_id="STU-02",
                department="CS",
                year=1,
            )
        except ValidationError:
            missing_email_caught = True
        check("3.5 Missing required email in AdminCreateStudent raises ValidationError", missing_email_caught)

        # ====================================================================
        # UNIT GROUP 4: NOTIFICATION SERVICE UNITS
        # ====================================================================
        print("\n--- 4. Notification Service Units ---")
        suffix = uuid.uuid4().hex[:6]
        test_student = User(
            full_name=f"Unit Student {suffix}",
            email=f"unit_student_{suffix}@attendx.com",
            password_hash=hashed,
            role="student",
            is_active=True,
        )
        db.add(test_student)
        db.commit()
        db.refresh(test_student)
        temp_entities.append(test_student)

        # 4.1 Valid notification creation
        n1 = create_notification(
            db=db,
            user_id=test_student.id,
            title="Unit Notification",
            message="This is a unit notification test message.",
            type="system",
            related_entity_type="system",
            related_entity_id=f"sys_{suffix}",
        )
        check("4.1 Notification successfully persisted", n1.id is not None)
        check("4.1 Notification recipient matches student ID", n1.user_id == test_student.id)
        check("4.1 Notification initial is_read is False", n1.is_read is False)

        # 4.2 Duplicate notification idempotency
        n2 = create_notification(
            db=db,
            user_id=test_student.id,
            title="Unit Notification Duplicate Attempt",
            message="Should not create a second row due to idempotency.",
            type="system",
            related_entity_type="system",
            related_entity_id=f"sys_{suffix}",
            check_duplicate=True,
        )
        check("4.2 Duplicate notification returns existing row without spamming DB", n1.id == n2.id)

        # 4.3 Enrollment notification helper
        n_enroll = create_enrollment_notification(
            db=db,
            user_id=test_student.id,
            count=1,
            subject_name="Unit Algorithms",
            subject_code="UA-101",
            subject_id=f"sub_{suffix}",
        )
        check("4.3 Enrollment notification generated", n_enroll is not None)
        check("4.3 Enrollment message mentions subject code", "UA-101" in n_enroll.message)

        # 4.4 Attendance notification helper
        n_att = create_attendance_notification(
            db=db,
            student_id=test_student.id,
            status="present",
            attendance_id=f"att_{suffix}",
            subject_name="Unit Operating Systems",
            subject_code="UOS-201",
            attendance_date=date.today(),
            is_update=False,
        )
        check("4.4 Attendance notification created with 'Present'", "Present" in n_att.message)

        # ====================================================================
        # UNIT GROUP 5: LECTURER REPORT SERVICE UNITS
        # ====================================================================
        print("\n--- 5. Lecturer Report Service Units ---")
        test_lecturer = User(
            full_name=f"Unit Lecturer {suffix}",
            email=f"unit_lecturer_{suffix}@attendx.com",
            password_hash=hashed,
            role="lecturer",
            employee_id=f"EMP-U-{suffix}",
            is_active=True,
        )
        test_subject = Subject(
            name=f"Unit Database Systems {suffix}",
            code=f"UDB-{suffix.upper()}",
            department="Computer Science",
            year=3,
            semester=5,
        )
        unassigned_subject = Subject(
            name=f"Unit Unassigned Subject {suffix}",
            code=f"UUN-{suffix.upper()}",
            department="Electrical",
            year=1,
            semester=1,
        )
        db.add_all([test_lecturer, test_subject, unassigned_subject])
        db.commit()
        db.refresh(test_lecturer)
        db.refresh(test_subject)
        db.refresh(unassigned_subject)
        temp_entities.extend([test_lecturer, test_subject, unassigned_subject])

        # Assign test_subject to test_lecturer
        lec_sub = LecturerSubject(lecturer_id=test_lecturer.id, subject_id=test_subject.id)
        db.add(lec_sub)
        db.commit()

        # 5.1 verify_lecturer_subject_access on assigned subject
        subj_acc = LecturerReportService.verify_lecturer_subject_access(db, test_lecturer, test_subject.id)
        check("5.1 Authorized lecturer verifies access to assigned subject", subj_acc.id == test_subject.id)

        # 5.2 verify_lecturer_subject_access on unassigned subject raises 403
        unassigned_forbidden = False
        try:
            LecturerReportService.verify_lecturer_subject_access(db, test_lecturer, unassigned_subject.id)
        except HTTPException as e:
            unassigned_forbidden = (e.status_code == 403)
        check("5.2 Unassigned subject access raises HTTP 403 Forbidden", unassigned_forbidden)

        # 5.3 verify_lecturer_subject_access on non-existent subject raises 404
        nonexistent_notfound = False
        try:
            LecturerReportService.verify_lecturer_subject_access(db, test_lecturer, str(uuid.uuid4()))
        except HTTPException as e:
            nonexistent_notfound = (e.status_code == 404)
        check("5.3 Non-existent subject access raises HTTP 404 Not Found", nonexistent_notfound)

        # 5.4 Date range filter validation in get_attendance_records
        invalid_range_rejected = False
        try:
            LecturerReportService.get_attendance_records(
                db=db,
                current_lecturer=test_lecturer,
                subject_id=test_subject.id,
                date_from=date.today(),
                date_to=date.today() - timedelta(days=5),
            )
        except HTTPException as e:
            invalid_range_rejected = (e.status_code == 400)
        check("5.4 Inverted date range (date_from > date_to) raises HTTP 400 Bad Request", invalid_range_rejected)

        # 5.5 CSV export sanitization check
        csv_content, filename = LecturerReportService.export_attendance_csv(
            db=db,
            current_lecturer=test_lecturer,
            export_type="records",
            subject_id=test_subject.id,
        )
        check("5.5 CSV export generates non-empty content", len(csv_content) > 0)
        check("5.5 CSV does NOT contain password hashes", "$2b$" not in csv_content and "password_hash" not in csv_content.lower())
        check("5.5 CSV does NOT contain bearer tokens", "bearer " not in csv_content.lower())

        # ====================================================================
        # UNIT GROUP 6: DATABASE CONSTRAINT & INTEGRITY UNITS
        # ====================================================================
        print("\n--- 6. Database Constraint Units ---")

        # 6.1 Duplicate LecturerSubject constraint violation
        duplicate_assignment_caught = False
        try:
            dup_assign = LecturerSubject(lecturer_id=test_lecturer.id, subject_id=test_subject.id)
            db.add(dup_assign)
            db.commit()
        except Exception:
            db.rollback()
            duplicate_assignment_caught = True
        check("6.1 Duplicate LecturerSubject violates UniqueConstraint", duplicate_assignment_caught)

        # 6.2 Duplicate StudentSubject constraint violation
        enr1 = StudentSubject(student_id=test_student.id, subject_id=test_subject.id)
        db.add(enr1)
        db.commit()

        duplicate_enrollment_caught = False
        try:
            enr2 = StudentSubject(student_id=test_student.id, subject_id=test_subject.id)
            db.add(enr2)
            db.commit()
        except Exception:
            db.rollback()
            duplicate_enrollment_caught = True
        check("6.2 Duplicate StudentSubject violates UniqueConstraint", duplicate_enrollment_caught)

        # 6.3 Duplicate Attendance constraint violation (same student, subject, date)
        att1 = Attendance(
            student_id=test_student.id,
            subject_id=test_subject.id,
            attendance_date=date.today(),
            status="present",
            marked_by=test_lecturer.id,
        )
        db.add(att1)
        db.commit()

        duplicate_attendance_caught = False
        try:
            att2 = Attendance(
                student_id=test_student.id,
                subject_id=test_subject.id,
                attendance_date=date.today(),
                status="absent",
                marked_by=test_lecturer.id,
            )
            db.add(att2)
            db.commit()
        except Exception:
            db.rollback()
            duplicate_attendance_caught = True
        check("6.3 Duplicate Attendance violates UniqueConstraint uq_attendance_record", duplicate_attendance_caught)

        # ====================================================================
        # SUMMARY
        # ====================================================================
        print("\n" + "=" * 80)
        print(f"LEVEL 2 UNIT TESTING COMPLETE: {passed_checks}/{total_checks} CHECKS PASSED (100% SUCCESS)")
        print("=" * 80)

    finally:
        # Cleanup unit test entities
        print("\n[CLEANUP] Cleaning up unit test entities...")
        try:
            u_ids = [e.id for e in temp_entities if isinstance(e, User)]
            s_ids = [e.id for e in temp_entities if isinstance(e, Subject)]
            if u_ids:
                db.query(Notification).filter(Notification.user_id.in_(u_ids)).delete(synchronize_session=False)
                db.query(Attendance).filter(Attendance.student_id.in_(u_ids)).delete(synchronize_session=False)
                db.query(StudentSubject).filter(StudentSubject.student_id.in_(u_ids)).delete(synchronize_session=False)
                db.query(LecturerSubject).filter(LecturerSubject.lecturer_id.in_(u_ids)).delete(synchronize_session=False)
            if s_ids:
                db.query(Attendance).filter(Attendance.subject_id.in_(s_ids)).delete(synchronize_session=False)
                db.query(StudentSubject).filter(StudentSubject.subject_id.in_(s_ids)).delete(synchronize_session=False)
                db.query(LecturerSubject).filter(LecturerSubject.subject_id.in_(s_ids)).delete(synchronize_session=False)
                db.query(Subject).filter(Subject.id.in_(s_ids)).delete(synchronize_session=False)
            if u_ids:
                db.query(User).filter(User.id.in_(u_ids)).delete(synchronize_session=False)
            db.commit()
            print("[CLEANUP] Cleaned up all unit test entities.")
        except Exception as ex:
            print(f"[CLEANUP ERROR] {ex}")
        finally:
            db.close()


if __name__ == "__main__":
    run_unit_tests()
