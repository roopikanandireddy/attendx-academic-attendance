# Schemas package
from app.schemas.user import UserRegister, UserLogin, UserUpdate, UserResponse, TokenResponse
from app.schemas.subject import SubjectCreate, SubjectUpdate, SubjectResponse, BatchEnrollmentRequest, BatchEnrollmentResponse
from app.schemas.attendance import (
    AttendanceBulkCreate,
    AttendanceUpdate,
    AttendanceResponse,
    LecturerAssignedSubjectItem,
    LecturerSessionStudentItem,
    LecturerAttendanceSessionResponse,
    LecturerAttendanceBulkResult,
    LecturerRecordsSummary,
    LecturerRecordItem,
    LecturerRecordsResponse,
    LecturerStudentSessionItem,
    LecturerStudentSubjectBreakdown,
    LecturerStudentReportResponse,
    LecturerSubjectStudentBreakdown,
    LecturerSubjectDailySession,
    LecturerSubjectReportResponse,
)
from app.schemas.notification import NotificationResponse, UnreadCountResponse
from app.schemas.dashboard import LecturerDashboardResponse

__all__ = [
    "UserRegister",
    "UserLogin",
    "UserUpdate",
    "UserResponse",
    "TokenResponse",
    "SubjectCreate",
    "SubjectUpdate",
    "SubjectResponse",
    "BatchEnrollmentRequest",
    "BatchEnrollmentResponse",
    "AttendanceBulkCreate",
    "AttendanceUpdate",
    "AttendanceResponse",
    "LecturerAssignedSubjectItem",
    "LecturerSessionStudentItem",
    "LecturerAttendanceSessionResponse",
    "LecturerAttendanceBulkResult",
    "LecturerRecordsSummary",
    "LecturerRecordItem",
    "LecturerRecordsResponse",
    "LecturerStudentSessionItem",
    "LecturerStudentSubjectBreakdown",
    "LecturerStudentReportResponse",
    "LecturerSubjectStudentBreakdown",
    "LecturerSubjectDailySession",
    "LecturerSubjectReportResponse",
    "NotificationResponse",
    "UnreadCountResponse",
    "LecturerDashboardResponse",
]

