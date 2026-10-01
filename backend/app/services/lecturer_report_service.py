import csv
import io
import math
from datetime import date
from typing import Optional, List, Dict, Any, Tuple
from fastapi import HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import func, case, or_

from app.models.user import User
from app.models.subject import Subject
from app.models.lecturer_subject import LecturerSubject
from app.models.student_subject import StudentSubject
from app.models.attendance import Attendance


class LecturerReportService:
    """Service handling attendance records querying, aggregation, reporting, and export
    with strict lecturer data isolation.
    """

    @staticmethod
    def verify_lecturer_subject_access(db: Session, current_lecturer: User, subject_id: str) -> Subject:
        """Verifies that the subject exists and is assigned to the authenticated lecturer.
        Raises 404 if subject does not exist, and 403 Forbidden if lecturer is not assigned.
        """
        subject = db.query(Subject).filter(Subject.id == subject_id).first()
        if not subject:
            raise HTTPException(status_code=404, detail="Subject not found")

        assignment = (
            db.query(LecturerSubject)
            .filter(
                LecturerSubject.lecturer_id == current_lecturer.id,
                LecturerSubject.subject_id == subject_id,
            )
            .first()
        )
        if not assignment:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You are not authorized to access records for this subject",
            )
        return subject

    @staticmethod
    def get_lecturer_assigned_subject_ids(db: Session, current_lecturer: User) -> List[str]:
        """Returns list of subject IDs assigned to the authenticated lecturer."""
        assignments = (
            db.query(LecturerSubject.subject_id)
            .filter(LecturerSubject.lecturer_id == current_lecturer.id)
            .all()
        )
        return [a[0] for a in assignments]

    @classmethod
    def get_attendance_records(
        cls,
        db: Session,
        current_lecturer: User,
        subject_id: Optional[str] = None,
        date_from: Optional[date] = None,
        date_to: Optional[date] = None,
        status_filter: Optional[str] = None,
        search: Optional[str] = None,
        page: int = 1,
        limit: int = 20,
        sort_by: str = "date",
        sort_order: str = "desc",
    ) -> Dict[str, Any]:
        """Query attendance records filtered by lecturer assigned subjects, date range, status, and student search.
        Includes full server-side summary statistics, sorting, and pagination.
        """
        assigned_subject_ids = cls.get_lecturer_assigned_subject_ids(db, current_lecturer)
        if not assigned_subject_ids:
            return {
                "summary": {
                    "total_students": 0,
                    "total_records": 0,
                    "present_count": 0,
                    "absent_count": 0,
                    "attendance_percentage": 0.0,
                },
                "records": [],
                "page": page,
                "limit": limit,
                "total": 0,
                "total_pages": 1,
            }

        # Validate subject_id if provided
        if subject_id and subject_id.strip():
            cls.verify_lecturer_subject_access(db, current_lecturer, subject_id.strip())
            target_subject_ids = [subject_id.strip()]
        else:
            target_subject_ids = assigned_subject_ids

        # Validate date range
        if date_from and date_to and date_from > date_to:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Date From cannot be after Date To",
            )

        # Base query joined with User (student) and Subject
        query = (
            db.query(Attendance, User, Subject)
            .join(User, Attendance.student_id == User.id)
            .join(Subject, Attendance.subject_id == Subject.id)
            .filter(Attendance.subject_id.in_(target_subject_ids))
        )

        if date_from:
            query = query.filter(Attendance.attendance_date >= date_from)
        if date_to:
            query = query.filter(Attendance.attendance_date <= date_to)

        if status_filter and status_filter.strip():
            clean_status = status_filter.lower().strip()
            if clean_status in ("present", "absent"):
                query = query.filter(Attendance.status == clean_status)

        if search and search.strip():
            term = f"%{search.strip()}%"
            query = query.filter(
                or_(
                    User.full_name.ilike(term),
                    User.student_id.ilike(term),
                )
            )

        # Calculate Summary Metrics
        # 1. Total records
        total_records = query.count()

        # 2. Present and Absent tallies
        present_count = 0
        absent_count = 0
        distinct_students_in_records = 0

        if total_records > 0:
            stats = (
                query.with_entities(
                    func.sum(case((Attendance.status == "present", 1), else_=0)),
                    func.sum(case((Attendance.status == "absent", 1), else_=0)),
                    func.count(func.distinct(Attendance.student_id)),
                ).first()
            )
            if stats:
                present_count = int(stats[0] or 0)
                absent_count = int(stats[1] or 0)
                distinct_students_in_records = int(stats[2] or 0)

        # Determine total students count context:
        # If a single subject is filtered, show its total enrolled students if search is not active
        if subject_id and subject_id.strip() and not (search and search.strip()):
            enrolled_count = (
                db.query(func.count(StudentSubject.id))
                .filter(StudentSubject.subject_id == subject_id.strip())
                .scalar()
                or 0
            )
            total_students_display = enrolled_count
        else:
            total_students_display = distinct_students_in_records

        attendance_percentage = (
            round((present_count / total_records) * 100, 1)
            if total_records > 0
            else 0.0
        )

        # Sorting
        sort_order_lower = sort_order.lower() if sort_order else "desc"
        is_asc = sort_order_lower == "asc"

        sort_col = sort_by.lower() if sort_by else "date"
        if sort_col == "student_name":
            order_exp = User.full_name.asc() if is_asc else User.full_name.desc()
            query = query.order_by(order_exp, Attendance.attendance_date.desc())
        elif sort_col == "student_sid":
            order_exp = User.student_id.asc() if is_asc else User.student_id.desc()
            query = query.order_by(order_exp, Attendance.attendance_date.desc())
        elif sort_col == "status":
            order_exp = Attendance.status.asc() if is_asc else Attendance.status.desc()
            query = query.order_by(order_exp, Attendance.attendance_date.desc())
        elif sort_col == "subject_code":
            order_exp = Subject.code.asc() if is_asc else Subject.code.desc()
            query = query.order_by(order_exp, Attendance.attendance_date.desc())
        else:  # default "date"
            order_exp = Attendance.attendance_date.asc() if is_asc else Attendance.attendance_date.desc()
            query = query.order_by(order_exp, User.full_name.asc(), Attendance.created_at.desc())

        # Pagination
        total_pages = max(1, math.ceil(total_records / limit))
        offset = (page - 1) * limit
        rows = query.offset(offset).limit(limit).all()

        records_list = []
        for att, stu, sub in rows:
            att_date_str = (
                att.attendance_date.isoformat()
                if hasattr(att.attendance_date, "isoformat")
                else str(att.attendance_date)
            )
            created_str = (
                att.created_at.isoformat()
                if att.created_at and hasattr(att.created_at, "isoformat")
                else (str(att.created_at) if att.created_at else None)
            )
            records_list.append({
                "id": att.id,
                "student_id": stu.id,
                "student_name": stu.full_name,
                "student_sid": stu.student_id or "",
                "student_department": stu.department or "",
                "subject_id": sub.id,
                "subject_name": sub.name,
                "subject_code": sub.code,
                "attendance_date": att_date_str,
                "status": att.status,
                "marked_by": att.marked_by,
                "created_at": created_str,
            })

        return {
            "summary": {
                "total_students": total_students_display,
                "total_records": total_records,
                "present_count": present_count,
                "absent_count": absent_count,
                "attendance_percentage": attendance_percentage,
            },
            "records": records_list,
            "page": page,
            "limit": limit,
            "total": total_records,
            "total_pages": total_pages,
        }

    @classmethod
    def get_student_report(
        cls,
        db: Session,
        current_lecturer: User,
        student_id: str,
        subject_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Retrieve detailed attendance report for an individual student.
        Strictly enforces that the student is enrolled in a subject taught by the authenticated lecturer.
        """
        student = db.query(User).filter(User.id == student_id, User.role == "student").first()
        if not student:
            raise HTTPException(status_code=404, detail="Student not found")

        assigned_subject_ids = cls.get_lecturer_assigned_subject_ids(db, current_lecturer)
        if not assigned_subject_ids:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You have no assigned subjects to view student records",
            )

        if subject_id and subject_id.strip():
            cls.verify_lecturer_subject_access(db, current_lecturer, subject_id.strip())
            # Check student enrollment in this subject
            enrollment = (
                db.query(StudentSubject)
                .filter(
                    StudentSubject.student_id == student_id,
                    StudentSubject.subject_id == subject_id.strip(),
                )
                .first()
            )
            if not enrollment:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Student is not enrolled in this assigned subject",
                )
            target_subject_ids = [subject_id.strip()]
        else:
            # Find all subjects taught by this lecturer in which the student is enrolled
            enrollments = (
                db.query(StudentSubject.subject_id)
                .filter(
                    StudentSubject.student_id == student_id,
                    StudentSubject.subject_id.in_(assigned_subject_ids),
                )
                .all()
            )
            if not enrollments:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="You are not authorized to view attendance records for this student",
                )
            target_subject_ids = [e[0] for e in enrollments]

        # Fetch attendance history
        history_rows = (
            db.query(Attendance, Subject)
            .join(Subject, Attendance.subject_id == Subject.id)
            .filter(
                Attendance.student_id == student_id,
                Attendance.subject_id.in_(target_subject_ids),
            )
            .order_by(Attendance.attendance_date.desc(), Attendance.created_at.desc())
            .all()
        )

        total_classes = len(history_rows)
        present_count = sum(1 for att, _ in history_rows if att.status == "present")
        absent_count = sum(1 for att, _ in history_rows if att.status == "absent")
        percentage = round((present_count / total_classes) * 100, 1) if total_classes > 0 else 0.0

        # Per-subject breakdown
        subject_breakdown_dict: Dict[str, Dict[str, Any]] = {}
        # Prepopulate with all target subjects
        target_subjects = db.query(Subject).filter(Subject.id.in_(target_subject_ids)).all()
        for sub in target_subjects:
            subject_breakdown_dict[sub.id] = {
                "subject_id": sub.id,
                "subject_name": sub.name,
                "subject_code": sub.code,
                "total_classes": 0,
                "present": 0,
                "absent": 0,
                "percentage": 0.0,
            }

        history_list = []
        for att, sub in history_rows:
            att_date_str = (
                att.attendance_date.isoformat()
                if hasattr(att.attendance_date, "isoformat")
                else str(att.attendance_date)
            )
            created_str = (
                att.created_at.isoformat()
                if att.created_at and hasattr(att.created_at, "isoformat")
                else (str(att.created_at) if att.created_at else None)
            )
            history_list.append({
                "id": att.id,
                "attendance_date": att_date_str,
                "subject_id": sub.id,
                "subject_name": sub.name,
                "subject_code": sub.code,
                "status": att.status,
                "created_at": created_str,
            })

            # Update breakdown
            if sub.id in subject_breakdown_dict:
                subject_breakdown_dict[sub.id]["total_classes"] += 1
                if att.status == "present":
                    subject_breakdown_dict[sub.id]["present"] += 1
                elif att.status == "absent":
                    subject_breakdown_dict[sub.id]["absent"] += 1

        for sub_id, b_data in subject_breakdown_dict.items():
            t = b_data["total_classes"]
            p = b_data["present"]
            b_data["percentage"] = round((p / t) * 100, 1) if t > 0 else 0.0

        return {
            "student_id": student.id,
            "student_name": student.full_name,
            "student_sid": student.student_id or "",
            "email": student.email,
            "department": student.department or "",
            "year": student.year,
            "section": student.section or "",
            "total_classes": total_classes,
            "present": present_count,
            "absent": absent_count,
            "percentage": percentage,
            "subject_breakdown": list(subject_breakdown_dict.values()),
            "history": history_list,
        }

    @classmethod
    def get_subject_report(
        cls,
        db: Session,
        current_lecturer: User,
        subject_id: str,
        date_from: Optional[date] = None,
        date_to: Optional[date] = None,
    ) -> Dict[str, Any]:
        """Generate comprehensive subject-level attendance report with enrolled student breakdowns
        and chronological session stats.
        """
        subject = cls.verify_lecturer_subject_access(db, current_lecturer, subject_id)

        if date_from and date_to and date_from > date_to:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Date From cannot be after Date To",
            )

        # 1. Enrolled students
        enrollments = (
            db.query(StudentSubject, User)
            .join(User, StudentSubject.student_id == User.id)
            .filter(StudentSubject.subject_id == subject_id, User.role == "student")
            .order_by(User.full_name.asc())
            .all()
        )
        total_students = len(enrollments)

        # 2. Query attendance records in date range
        att_query = db.query(Attendance).filter(Attendance.subject_id == subject_id)
        if date_from:
            att_query = att_query.filter(Attendance.attendance_date >= date_from)
        if date_to:
            att_query = att_query.filter(Attendance.attendance_date <= date_to)

        attendance_rows = att_query.all()
        total_records = len(attendance_rows)
        present_count = sum(1 for a in attendance_rows if a.status == "present")
        absent_count = sum(1 for a in attendance_rows if a.status == "absent")
        percentage = round((present_count / total_records) * 100, 1) if total_records > 0 else 0.0

        distinct_dates = set(a.attendance_date for a in attendance_rows)
        total_sessions = len(distinct_dates)

        # 3. Student breakdown
        student_records_map: Dict[str, List[Attendance]] = {u.id: [] for _, u in enrollments}
        for a in attendance_rows:
            if a.student_id in student_records_map:
                student_records_map[a.student_id].append(a)

        student_breakdowns = []
        for _, u in enrollments:
            stu_records = student_records_map.get(u.id, [])
            stu_total = len(stu_records)
            stu_present = sum(1 for a in stu_records if a.status == "present")
            stu_absent = sum(1 for a in stu_records if a.status == "absent")
            stu_pct = round((stu_present / stu_total) * 100, 1) if stu_total > 0 else 0.0

            student_breakdowns.append({
                "student_id": u.id,
                "student_name": u.full_name,
                "student_sid": u.student_id or "",
                "email": u.email,
                "department": u.department or "",
                "year": u.year,
                "section": u.section or "",
                "total_classes": stu_total,
                "present": stu_present,
                "absent": stu_absent,
                "percentage": stu_pct,
                "attendance_percentage": stu_pct,
            })

        # 4. Daily session breakdown
        sessions_map: Dict[date, Dict[str, Any]] = {}
        for a in attendance_rows:
            d = a.attendance_date
            if d not in sessions_map:
                sessions_map[d] = {"date": d, "total": 0, "present": 0, "absent": 0}
            sessions_map[d]["total"] += 1
            if a.status == "present":
                sessions_map[d]["present"] += 1
            elif a.status == "absent":
                sessions_map[d]["absent"] += 1

        daily_sessions = []
        for d in sorted(sessions_map.keys(), reverse=True):
            s_data = sessions_map[d]
            s_tot = s_data["total"]
            s_pres = s_data["present"]
            s_abs = s_data["absent"]
            s_pct = round((s_pres / s_tot) * 100, 1) if s_tot > 0 else 0.0
            daily_sessions.append({
                "attendance_date": d.isoformat() if hasattr(d, "isoformat") else str(d),
                "total_students": s_tot,
                "present": s_pres,
                "absent": s_abs,
                "percentage": s_pct,
            })

        return {
            "subject_id": subject.id,
            "subject_name": subject.name,
            "subject_code": subject.code,
            "department": subject.department,
            "year": subject.year,
            "semester": subject.semester,
            "total_students": total_students,
            "total_records": total_records,
            "total_sessions": total_sessions,
            "present": present_count,
            "absent": absent_count,
            "percentage": percentage,
            "students": student_breakdowns,
            "enrolled_students": student_breakdowns,
            "sessions": daily_sessions,
        }

    @classmethod
    def export_attendance_csv(
        cls,
        db: Session,
        current_lecturer: User,
        export_type: str = "records",
        subject_id: Optional[str] = None,
        student_id: Optional[str] = None,
        date_from: Optional[date] = None,
        date_to: Optional[date] = None,
        status_filter: Optional[str] = None,
        search: Optional[str] = None,
    ) -> Tuple[str, str]:
        """Export attendance records or reports to academic CSV format.
        Strictly enforces lecturer ownership and sanitizes all exported data.
        Returns a tuple of (csv_content_string, suggested_filename).
        """
        output = io.StringIO()
        writer = csv.writer(output)
        today_stamp = date.today().isoformat()

        if export_type == "student":
            if not student_id:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="student_id is required for student report export",
                )
            report_data = cls.get_student_report(
                db=db,
                current_lecturer=current_lecturer,
                student_id=student_id,
                subject_id=subject_id,
            )

            # Metadata header rows
            writer.writerow(["ATTENDX — INDIVIDUAL STUDENT ATTENDANCE REPORT"])
            writer.writerow(["Student Name", report_data["student_name"]])
            writer.writerow(["Roll Number / Student ID", report_data["student_sid"]])
            writer.writerow(["Email", report_data["email"]])
            writer.writerow(["Department", report_data["department"]])
            writer.writerow(["Total Classes", report_data["total_classes"]])
            writer.writerow(["Present", report_data["present"]])
            writer.writerow(["Absent", report_data["absent"]])
            writer.writerow(["Overall Percentage", f"{report_data['percentage']}%"])
            writer.writerow(["Exported On", today_stamp])
            writer.writerow([])

            # Detailed history table
            writer.writerow(["Date", "Subject Code", "Subject Name", "Status"])
            for h in report_data["history"]:
                writer.writerow([
                    h["attendance_date"],
                    h["subject_code"],
                    h["subject_name"],
                    h["status"].capitalize(),
                ])

            stu_roll_clean = (report_data["student_sid"] or report_data["student_name"]).replace(" ", "_")
            filename = f"student_report_{stu_roll_clean}_{today_stamp}.csv"
            return output.getvalue(), filename

        elif export_type == "subject":
            if not subject_id:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="subject_id is required for subject report export",
                )
            report_data = cls.get_subject_report(
                db=db,
                current_lecturer=current_lecturer,
                subject_id=subject_id,
                date_from=date_from,
                date_to=date_to,
            )

            # Metadata header rows
            writer.writerow(["ATTENDX — SUBJECT ATTENDANCE REPORT"])
            writer.writerow(["Subject Code", report_data["subject_code"]])
            writer.writerow(["Subject Name", report_data["subject_name"]])
            writer.writerow(["Department", report_data["department"]])
            writer.writerow(["Enrolled Students", report_data["total_students"]])
            writer.writerow(["Total Attendance Records", report_data["total_records"]])
            writer.writerow(["Total Sessions", report_data["total_sessions"]])
            writer.writerow(["Overall Attendance", f"{report_data['percentage']}%"])
            if date_from or date_to:
                writer.writerow(["Date Range", f"{date_from or 'Start'} to {date_to or 'End'}"])
            writer.writerow(["Exported On", today_stamp])
            writer.writerow([])

            # Enrolled student attendance breakdown
            writer.writerow([
                "Roll Number",
                "Student Name",
                "Department",
                "Total Classes",
                "Present",
                "Absent",
                "Attendance %",
            ])
            for s in report_data["students"]:
                writer.writerow([
                    s["student_sid"],
                    s["student_name"],
                    s["department"],
                    s["total_classes"],
                    s["present"],
                    s["absent"],
                    f"{s['percentage']}%",
                ])

            subj_code_clean = report_data["subject_code"].replace(" ", "_")
            filename = f"subject_report_{subj_code_clean}_{today_stamp}.csv"
            return output.getvalue(), filename

        else:
            # Default "records" export
            # Fetch all records without pagination limit (up to 5000)
            res = cls.get_attendance_records(
                db=db,
                current_lecturer=current_lecturer,
                subject_id=subject_id,
                date_from=date_from,
                date_to=date_to,
                status_filter=status_filter,
                search=search,
                page=1,
                limit=5000,
            )

            writer.writerow(["ATTENDX — LECTURER ATTENDANCE RECORDS"])
            writer.writerow(["Total Records", res["summary"]["total_records"]])
            writer.writerow(["Present Count", res["summary"]["present_count"]])
            writer.writerow(["Absent Count", res["summary"]["absent_count"]])
            writer.writerow(["Attendance %", f"{res['summary']['attendance_percentage']}%"])
            writer.writerow(["Exported On", today_stamp])
            writer.writerow([])

            writer.writerow([
                "Date",
                "Subject Code",
                "Subject Name",
                "Student Roll No",
                "Student Name",
                "Department",
                "Status",
            ])

            for r in res["records"]:
                writer.writerow([
                    r["attendance_date"],
                    r["subject_code"],
                    r["subject_name"],
                    r["student_sid"],
                    r["student_name"],
                    r["student_department"],
                    r["status"].capitalize(),
                ])

            filename = f"attendance_records_{today_stamp}.csv"
            return output.getvalue(), filename
