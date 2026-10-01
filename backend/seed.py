"""
AttendX — Database Seed Script
Populates initial admin, sample students, sample subjects, enrollments, and attendance records.
"""
import sys
import os
from datetime import date, timedelta
import random

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__))))

from app.core.database import SessionLocal, engine, Base
from app.core.security import hash_password
from app.models.user import User
from app.models.subject import Subject
from app.models.student_subject import StudentSubject
from app.models.attendance import Attendance
from app.models.lecturer_subject import LecturerSubject


def seed_database():
    print("Creating all tables in database...")
    Base.metadata.create_all(bind=engine)

    db = SessionLocal()
    try:
        # Check if already seeded
        existing_admin = db.query(User).filter(User.email == "admin@attendx.com").first()
        if existing_admin:
            existing_lec = db.query(User).filter(User.email == "dr.alan@lecturer.com").first()
            if not existing_lec:
                existing_lec = User(
                    email="dr.alan@lecturer.com",
                    full_name="Dr. Alan Turing",
                    password_hash=hash_password("LecturerPassword123!"),
                    role="lecturer",
                    employee_id="EMP-CS-001",
                    department="Computer Science",
                    is_active=True,
                )
                db.add(existing_lec)
                db.commit()
                db.refresh(existing_lec)
                print("Created missing sample lecturer: dr.alan@lecturer.com")

            # Ensure teaching assignments for dr.alan@lecturer.com
            iai = db.query(Subject).filter(Subject.code == "IAI").first()
            se = db.query(Subject).filter(Subject.code == "SE").first()
            if existing_lec and iai:
                if not db.query(LecturerSubject).filter(LecturerSubject.lecturer_id == existing_lec.id, LecturerSubject.subject_id == iai.id).first():
                    db.add(LecturerSubject(lecturer_id=existing_lec.id, subject_id=iai.id))
            if existing_lec and se:
                if not db.query(LecturerSubject).filter(LecturerSubject.lecturer_id == existing_lec.id, LecturerSubject.subject_id == se.id).first():
                    db.add(LecturerSubject(lecturer_id=existing_lec.id, subject_id=se.id))

            # Ensure teaching assignment for Dr. Katherine Johnson if exists
            kj_lec = db.query(User).filter(User.email == "katherine.johnson@attendx.com").first()
            isc = db.query(Subject).filter(Subject.code == "ISC").first()
            if kj_lec and isc:
                if not db.query(LecturerSubject).filter(LecturerSubject.lecturer_id == kj_lec.id, LecturerSubject.subject_id == isc.id).first():
                    db.add(LecturerSubject(lecturer_id=kj_lec.id, subject_id=isc.id))

            db.commit()
            print("Database already contains seed data. Teaching assignments synchronized.")
            return

        print("Seeding database with initial data...")

        # 1. Create Admin
        admin = User(
            email="admin@attendx.com",
            full_name="System Administrator",
            password_hash=hash_password("AdminPassword123!"),
            role="admin",
            department="Administration",
        )
        db.add(admin)
        db.flush()
        print(f"Created Admin: {admin.email}")

        # 1b. Create Sample Lecturer
        sample_lecturer = User(
            email="dr.alan@lecturer.com",
            full_name="Dr. Alan Turing",
            password_hash=hash_password("LecturerPassword123!"),
            role="lecturer",
            employee_id="EMP-CS-001",
            department="Computer Science",
            is_active=True,
        )
        db.add(sample_lecturer)
        db.flush()
        print(f"Created Lecturer: {sample_lecturer.email}")


        # 2. Create Sample Students
        students_data = [
            {
                "full_name": "John Doe",
                "email": "john.doe@student.com",
                "password": "StudentPassword123!",
                "student_id": "2024CS001",
                "department": "Computer Science",
                "year": 3,
                "section": "A",
            },
            {
                "full_name": "Jane Smith",
                "email": "jane.smith@student.com",
                "password": "StudentPassword123!",
                "student_id": "2024CS002",
                "department": "Computer Science",
                "year": 3,
                "section": "A",
            },
            {
                "full_name": "Alex Kumar",
                "email": "alex.kumar@student.com",
                "password": "StudentPassword123!",
                "student_id": "2024CS003",
                "department": "Computer Science",
                "year": 3,
                "section": "B",
            },
            {
                "full_name": "Sarah Lee",
                "email": "sarah.lee@student.com",
                "password": "StudentPassword123!",
                "student_id": "2024EC001",
                "department": "Electronics",
                "year": 2,
                "section": "A",
            },
            {
                "full_name": "David Wilson",
                "email": "david.wilson@student.com",
                "password": "StudentPassword123!",
                "student_id": "2024IT001",
                "department": "Information Technology",
                "year": 4,
                "section": "A",
            },
        ]

        created_students = []
        for s in students_data:
            student = User(
                email=s["email"],
                full_name=s["full_name"],
                password_hash=hash_password(s["password"]),
                role="student",
                student_id=s["student_id"],
                department=s["department"],
                year=s["year"],
                section=s["section"],
            )
            db.add(student)
            created_students.append(student)

        db.flush()
        print(f"Created {len(created_students)} students.")

        # 3. Create Sample Subjects
        # 3. Create Sample Subjects (AttendX 6-Subject Catalog)
        subjects_data = [
            {"name": "Introduction to Artificial Intelligence", "code": "IAI", "department": "Computer Science", "year": 3, "semester": 5},
            {"name": "Software Engineering", "code": "SE", "department": "Computer Science", "year": 3, "semester": 5},
            {"name": "Intelligent Control Systems", "code": "ISC", "department": "Computer Science", "year": 3, "semester": 5},
            {"name": "Business Economics & Financial Analysis", "code": "BEFA", "department": "Computer Science", "year": 3, "semester": 5},
            {"name": "Environmental Science", "code": "ES", "department": "Computer Science", "year": 3, "semester": 5},
            {"name": "Advanced Engineering Laboratory-3", "code": "AE-3 LAB", "department": "Computer Science", "year": 3, "semester": 5},
        ]

        created_subjects = []
        for sub in subjects_data:
            subject = Subject(
                name=sub["name"],
                code=sub["code"],
                department=sub["department"],
                year=sub["year"],
                semester=sub["semester"],
            )
            db.add(subject)
            created_subjects.append(subject)

        db.flush()
        print(f"Created {len(created_subjects)} subjects.")

        # 4. Enroll Students
        # Enrol CS students (John, Jane, Alex) in core CS subjects (IAI, SE, ISC, BEFA)
        cs_subjects = created_subjects[:4]
        cs_students = created_students[:3]
        for s in cs_students:
            for sub in cs_subjects:
                enrollment = StudentSubject(student_id=s.id, subject_id=sub.id)
                db.add(enrollment)

        # Enrol Sarah in ES
        db.add(StudentSubject(student_id=created_students[3].id, subject_id=created_subjects[4].id))
        db.flush()
        print("Enrolled students in subjects.")

        # 5. Generate Past Attendance (Past 10 instructional days)
        # Dates (skip weekends)
        today = date.today()
        dates = []
        current = today - timedelta(days=14)
        while current <= today:
            if current.weekday() < 5:  # Mon-Fri
                dates.append(current)
            current += timedelta(days=1)

        attendance_count = 0
        for d in dates:
            for sub in cs_subjects:
                for s in cs_students:
                    # John has ~85% attendance, Jane has ~95%, Alex has ~60% (low attendance warning)
                    if s.full_name == "Jane Smith":
                        status = "present" if random.random() < 0.95 else "absent"
                    elif s.full_name == "John Doe":
                        status = "present" if random.random() < 0.85 else "absent"
                    else:  # Alex Kumar
                        status = "present" if random.random() < 0.60 else "absent"

                    att = Attendance(
                        student_id=s.id,
                        subject_id=sub.id,
                        attendance_date=d,
                        status=status,
                        marked_by=admin.id,
                    )
                    db.add(att)
                    attendance_count += 1

            # Sarah Lee in EC201
            status = "present" if random.random() < 0.90 else "absent"
            att = Attendance(
                student_id=created_students[3].id,
                subject_id=created_subjects[4].id,
                attendance_date=d,
                status=status,
                marked_by=admin.id,
            )
            db.add(att)
            attendance_count += 1

        db.commit()
        print(f"Generated {attendance_count} attendance records.")

        # Seed initial sample notifications
        from app.models.notification import Notification
        db.add(Notification(
            user_id=created_students[0].id, # John Doe
            title="Welcome to AttendX",
            message="Your AttendX student portal is ready to use.",
            type="system",
            related_entity_type="system",
            related_entity_id="welcome",
            is_read=True
        ))
        db.add(Notification(
            user_id=created_students[0].id,
            title="Subject Enrollment Successful",
            message="You successfully enrolled in 6 subjects.",
            type="enrollment",
            related_entity_type="enrollment",
            is_read=False
        ))
        db.add(Notification(
            user_id=created_students[0].id,
            title="Attendance Updated",
            message="Your attendance for IAI was marked Present.",
            type="attendance",
            related_entity_type="attendance",
            is_read=False
        ))

        db.add(Notification(
            user_id=created_students[2].id, # Alex Kumar
            title="Welcome to AttendX",
            message="Your AttendX student portal is ready to use.",
            type="system",
            related_entity_type="system",
            related_entity_id="welcome",
            is_read=True
        ))
        db.add(Notification(
            user_id=created_students[2].id,
            title="Low Attendance Warning",
            message="Your attendance in Software Engineering is 60%, which is below the 75% threshold.",
            type="low_attendance",
            related_entity_type="low_attendance",
            is_read=False
        ))
        db.add(Notification(
            user_id=created_students[2].id,
            title="Attendance Updated",
            message="Your attendance for SE was marked Absent.",
            type="attendance",
            related_entity_type="attendance",
            is_read=False
        ))
        db.commit()
        print("Generated initial sample notifications for test accounts.")

        print("\nDatabase seeded successfully!")
        print("--------------------------------------------------")
        print("Admin Login:")
        print("  Email:    admin@attendx.com")
        print("  Password: AdminPassword123!")
        print("\nStudent Login (John Doe):")
        print("  Email:    john.doe@student.com")
        print("  Password: StudentPassword123!")
        print("\nStudent Login (Alex Kumar - Low Attendance Demo):")
        print("  Email:    alex.kumar@student.com")
        print("  Password: StudentPassword123!")
        print("\nLecturer Login (Dr. Alan Turing):")
        print("  Email:    dr.alan@lecturer.com")
        print("  Password: LecturerPassword123!")
        print("--------------------------------------------------")

    except Exception as e:
        db.rollback()
        print(f"Error seeding database: {e}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    seed_database()
