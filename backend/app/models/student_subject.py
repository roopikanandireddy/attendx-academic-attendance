import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, DateTime, ForeignKey, UniqueConstraint
from sqlalchemy.orm import relationship
from app.core.database import Base


def utcnow():
    return datetime.now(timezone.utc)


class StudentSubject(Base):
    __tablename__ = "student_subjects"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    student_id = Column(String, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    subject_id = Column(String, ForeignKey("subjects.id", ondelete="CASCADE"), nullable=False)
    created_at = Column(DateTime(timezone=True), default=utcnow, nullable=False)

    __table_args__ = (UniqueConstraint("student_id", "subject_id", name="uq_student_subject"),)

    # Relationships
    student = relationship("User", back_populates="enrollments")
    subject = relationship("Subject", back_populates="enrollments")
