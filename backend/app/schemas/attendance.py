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


class LecturerAssignedSubjectItem(BaseModel):
    id: str
    name: str
    code: str
    department: str
    year: int
    semester: int
    enrolled_students_count: int


class LecturerSessionStudentItem(BaseModel):
    student_id: str
    full_name: str
    student_sid: Optional[str] = None
    department: Optional[str] = None
    status: Optional[str] = None
    attendance_id: Optional[str] = None


class LecturerAttendanceSessionResponse(BaseModel):
    subject_id: str
    subject_code: str
    subject_name: str
    department: str
    attendance_date: str
    has_existing_records: bool
    total_students: int
    present_count: int
    absent_count: int
    unmarked_count: int
    students: List[LecturerSessionStudentItem]


class LecturerAttendanceBulkResult(BaseModel):
    message: str
    subject_id: str
    subject_code: str
    attendance_date: str
    total_processed: int
    created_count: int
    updated_count: int
    present_count: int
    absent_count: int



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


# ==========================================
# MODULE L4 — LECTURER RECORDS & REPORTS SCHEMAS
# ==========================================

class LecturerRecordsSummary(BaseModel):
    total_students: int
    total_records: int
    present_count: int
    absent_count: int
    attendance_percentage: float


class LecturerRecordItem(BaseModel):
    id: str
    student_id: str
    student_name: str
    student_sid: Optional[str] = ""
    student_department: Optional[str] = ""
    subject_id: str
    subject_name: str
    subject_code: str
    attendance_date: str
    status: str
    marked_by: str
    created_at: Optional[str] = None


class LecturerRecordsResponse(BaseModel):
    summary: LecturerRecordsSummary
    records: List[LecturerRecordItem]
    page: int
    limit: int
    total: int
    total_pages: int


class LecturerStudentSessionItem(BaseModel):
    id: str
    attendance_date: str
    subject_id: str
    subject_name: str
    subject_code: str
    status: str
    created_at: Optional[str] = None


class LecturerStudentSubjectBreakdown(BaseModel):
    subject_id: str
    subject_name: str
    subject_code: str
    total_classes: int
    present: int
    absent: int
    percentage: float


class LecturerStudentReportResponse(BaseModel):
    student_id: str
    student_name: str
    student_sid: Optional[str] = ""
    email: str
    department: Optional[str] = ""
    year: Optional[int] = None
    section: Optional[str] = ""
    total_classes: int
    present: int
    absent: int
    percentage: float
    subject_breakdown: List[LecturerStudentSubjectBreakdown]
    history: List[LecturerStudentSessionItem]


class LecturerSubjectStudentBreakdown(BaseModel):
    student_id: str
    student_name: str
    student_sid: Optional[str] = ""
    email: str
    department: Optional[str] = ""
    year: Optional[int] = None
    section: Optional[str] = ""
    total_classes: int
    present: int
    absent: int
    percentage: float
    attendance_percentage: Optional[float] = None


class LecturerSubjectDailySession(BaseModel):
    attendance_date: str
    total_students: int
    present: int
    absent: int
    percentage: float


class LecturerSubjectReportResponse(BaseModel):
    subject_id: str
    subject_name: str
    subject_code: str
    department: str
    year: int
    semester: int
    total_students: int
    total_records: int
    total_sessions: int
    present: int
    absent: int
    percentage: float
    students: List[LecturerSubjectStudentBreakdown]
    enrolled_students: Optional[List[LecturerSubjectStudentBreakdown]] = None
    sessions: List[LecturerSubjectDailySession]

