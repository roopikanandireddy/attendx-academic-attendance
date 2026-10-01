from pydantic import BaseModel
from typing import Optional, List


class LecturerProfileSummary(BaseModel):
    id: str
    full_name: str
    name: Optional[str] = None
    email: str
    employee_id: Optional[str] = None
    department: Optional[str] = None
    role: str


class LecturerDashboardMetrics(BaseModel):
    total_subjects: int
    total_students: int
    total_attendance_records: int
    attendance_records: Optional[int] = None
    average_attendance: float


class LecturerSubjectItem(BaseModel):
    id: str
    name: str
    code: str
    department: str
    year: int
    semester: int
    enrolled_students: int
    total_classes: int
    present: int
    absent: int
    attendance_percentage: float
    has_attendance: bool


class LecturerAttendanceOverview(BaseModel):
    total_classes: int
    present: int
    absent: int
    percentage: float
    has_data: bool


class LecturerRecentActivityItem(BaseModel):
    id: str
    student_name: str
    student_sid: Optional[str] = None
    subject_name: str
    subject_code: str
    attendance_date: str
    status: str
    created_at: Optional[str] = None


class LecturerDashboardResponse(BaseModel):
    lecturer: LecturerProfileSummary
    summary: LecturerDashboardMetrics
    subjects: List[LecturerSubjectItem]
    attendance_overview: LecturerAttendanceOverview
    recent_activity: List[LecturerRecentActivityItem]
    unread_notifications_count: int = 0
