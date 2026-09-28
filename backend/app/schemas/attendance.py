from pydantic import BaseModel, field_validator
from typing import Optional, List
from datetime import date, datetime


class AttendanceMark(BaseModel):
    student_id: str
    status: str

    @field_validator("status")
    @classmethod
    def validate_status(cls, v: str) -> str:
        v = v.lower().strip()
        if v not in ("present", "absent"):
            raise ValueError("Status must be 'present' or 'absent'")
        return v


class AttendanceBulkCreate(BaseModel):
    subject_id: str
    attendance_date: date
    records: List[AttendanceMark]

    @field_validator("records")
    @classmethod
    def validate_records(cls, v: List[AttendanceMark]) -> List[AttendanceMark]:
        if len(v) == 0:
            raise ValueError("At least one attendance record is required")
        return v


class AttendanceUpdate(BaseModel):
    status: str

    @field_validator("status")
    @classmethod
    def validate_status(cls, v: str) -> str:
        v = v.lower().strip()
        if v not in ("present", "absent"):
            raise ValueError("Status must be 'present' or 'absent'")
        return v


class AttendanceResponse(BaseModel):
    id: str
    student_id: str
    subject_id: str
    attendance_date: date
    status: str
    marked_by: str
    created_at: datetime
    student_name: Optional[str] = None
    subject_name: Optional[str] = None
    subject_code: Optional[str] = None
    marker_name: Optional[str] = None

    class Config:
        from_attributes = True


class AttendanceStats(BaseModel):
    subject_id: str
    subject_name: str
    subject_code: str
    total_classes: int
    present: int
    absent: int
    percentage: float


class OverallStats(BaseModel):
    total_classes: int
    present: int
    absent: int
    percentage: float
    subjects: List[AttendanceStats]


class StudentDashboard(BaseModel):
    user: dict
    overall_stats: OverallStats
    recent_attendance: List[dict]
    low_attendance_subjects: List[dict]


class AdminDashboard(BaseModel):
    total_students: int
    total_subjects: int
    todays_attendance: dict
    average_attendance: float
    recent_attendance: List[dict]
    low_attendance_students: List[dict]
    subject_stats: List[dict]
    attendance_trend: List[dict]
