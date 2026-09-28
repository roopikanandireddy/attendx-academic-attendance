import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, Date, DateTime, ForeignKey, UniqueConstraint
from sqlalchemy.orm import relationship
from app.core.database import Base


def utcnow():
    return datetime.now(timezone.utc)


class Attendance(Base):
    __tablename__ = "attendance"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    student_id = Column(String, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    subject_id = Column(String, ForeignKey("subjects.id", ondelete="CASCADE"), nullable=False)
    attendance_date = Column(Date, nullable=False)
    status = Column(String(10), nullable=False)  # 'present' or 'absent'
    marked_by = Column(String, ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime(timezone=True), default=utcnow, nullable=False)

    __table_args__ = (
        UniqueConstraint("student_id", "subject_id", "attendance_date", name="uq_attendance_record"),
    )

    # Relationships
    student = relationship("User", back_populates="attendance_records", foreign_keys=[student_id])
    subject = relationship("Subject", back_populates="attendance_records")
    marker = relationship("User", foreign_keys=[marked_by])
