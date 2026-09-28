import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, Integer, DateTime
from sqlalchemy.orm import relationship
from app.core.database import Base


def utcnow():
    return datetime.now(timezone.utc)


class Subject(Base):
    __tablename__ = "subjects"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String(255), nullable=False)
    code = Column(String(50), nullable=False, unique=True, index=True)
    department = Column(String(100), nullable=False)
    year = Column(Integer, nullable=False)
    semester = Column(Integer, nullable=False)
    created_at = Column(DateTime(timezone=True), default=utcnow, nullable=False)

    # Relationships
    enrollments = relationship("StudentSubject", back_populates="subject", cascade="all, delete-orphan")
    attendance_records = relationship("Attendance", back_populates="subject", cascade="all, delete-orphan")
