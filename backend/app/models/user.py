import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, Integer, DateTime
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import relationship
from app.core.database import Base


def utcnow():
    return datetime.now(timezone.utc)


class User(Base):
    __tablename__ = "users"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    full_name = Column(String(255), nullable=False)
    email = Column(String(255), nullable=False, unique=True, index=True)
    password_hash = Column(String(255), nullable=False)
    role = Column(String(20), nullable=False, default="student")
    student_id = Column(String(50), unique=True, nullable=True)
    department = Column(String(100), nullable=True)
    year = Column(Integer, nullable=True)
    section = Column(String(10), nullable=True)
    created_at = Column(DateTime(timezone=True), default=utcnow, nullable=False)
    updated_at = Column(DateTime(timezone=True), default=utcnow, onupdate=utcnow, nullable=False)

    # Relationships
    enrollments = relationship("StudentSubject", back_populates="student", cascade="all, delete-orphan")
    attendance_records = relationship(
        "Attendance",
        back_populates="student",
        foreign_keys="Attendance.student_id",
        cascade="all, delete-orphan",
    )
