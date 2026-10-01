"""
Update database subjects catalog to the 6 required subjects:
IAI, SE, ISC, BEFA, ES, AE-3 LAB
"""
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__))))

from app.core.database import SessionLocal, engine, Base
from app.models.subject import Subject
from app.models.student_subject import StudentSubject
from app.models.attendance import Attendance

def update_catalog():
    db = SessionLocal()
    try:
        new_subjects = [
            {"code": "IAI", "name": "Introduction to Artificial Intelligence", "department": "Computer Science", "year": 3, "semester": 5},
            {"code": "SE", "name": "Software Engineering", "department": "Computer Science", "year": 3, "semester": 5},
            {"code": "ISC", "name": "Intelligent Control Systems", "department": "Computer Science", "year": 3, "semester": 5},
            {"code": "BEFA", "name": "Business Economics & Financial Analysis", "department": "Computer Science", "year": 3, "semester": 5},
            {"code": "ES", "name": "Environmental Science", "department": "Computer Science", "year": 3, "semester": 5},
            {"code": "AE-3 LAB", "name": "Advanced Engineering Laboratory-3", "department": "Computer Science", "year": 3, "semester": 5},
        ]

        print("Current subjects in database:")
        existing = db.query(Subject).all()
        for s in existing:
            print(f" - {s.code}: {s.name} ({s.id})")

        # Map old codes to new codes if applicable, or insert new subjects
        code_mapping = {
            "CS301": "IAI",
            "CS302": "SE",
            "CS303": "ISC",
            "CS304": "BEFA",
            "EC201": "ES",
        }

        for old_code, new_code in code_mapping.items():
            old_sub = db.query(Subject).filter(Subject.code == old_code).first()
            if old_sub:
                target_meta = next(x for x in new_subjects if x["code"] == new_code)
                old_sub.code = target_meta["code"]
                old_sub.name = target_meta["name"]
                old_sub.department = target_meta["department"]
                old_sub.year = target_meta["year"]
                old_sub.semester = target_meta["semester"]
                print(f"Updated subject {old_code} -> {target_meta['code']}: {target_meta['name']}")

        db.commit()

        # Ensure all 6 subjects exist
        for s_data in new_subjects:
            sub = db.query(Subject).filter(Subject.code == s_data["code"]).first()
            if not sub:
                sub = Subject(
                    name=s_data["name"],
                    code=s_data["code"],
                    department=s_data["department"],
                    year=s_data["year"],
                    semester=s_data["semester"],
                )
                db.add(sub)
                print(f"Inserted new subject {s_data['code']}: {s_data['name']}")
            else:
                sub.name = s_data["name"]
                sub.department = s_data["department"]
                sub.year = s_data["year"]
                sub.semester = s_data["semester"]

        db.commit()

        print("\nAll 6 subjects now in database:")
        all_subs = db.query(Subject).order_by(Subject.code).all()
        for s in all_subs:
            print(f" - {s.code}: {s.name} (dept={s.department}, yr={s.year}, sem={s.semester})")

    except Exception as e:
        db.rollback()
        print(f"Error: {e}")
        raise
    finally:
        db.close()

if __name__ == "__main__":
    update_catalog()
