from pydantic import BaseModel, field_validator
from typing import Optional
from datetime import datetime


class SubjectCreate(BaseModel):
    name: str
    code: str
    department: str
    year: int
    semester: int

    @field_validator("name")
    @classmethod
    def validate_name(cls, v: str) -> str:
        v = v.strip()
        if len(v) < 2:
            raise ValueError("Subject name must be at least 2 characters")
        return v

    @field_validator("code")
    @classmethod
    def validate_code(cls, v: str) -> str:
        v = v.strip().upper()
        if len(v) < 2:
            raise ValueError("Subject code must be at least 2 characters")
        return v

    @field_validator("year")
    @classmethod
    def validate_year(cls, v: int) -> int:
        if v < 1 or v > 6:
            raise ValueError("Year must be between 1 and 6")
        return v

    @field_validator("semester")
    @classmethod
    def validate_semester(cls, v: int) -> int:
        if v < 1 or v > 12:
            raise ValueError("Semester must be between 1 and 12")
        return v


class SubjectUpdate(BaseModel):
    name: Optional[str] = None
    code: Optional[str] = None
    department: Optional[str] = None
    year: Optional[int] = None
    semester: Optional[int] = None


class SubjectResponse(BaseModel):
    id: str
    name: str
    code: str
    department: str
    year: int
    semester: int
    created_at: datetime

    class Config:
        from_attributes = True


class EnrollmentCreate(BaseModel):
    student_id: str
    subject_id: str


class EnrollmentResponse(BaseModel):
    id: str
    student_id: str
    subject_id: str
    created_at: datetime

    class Config:
        from_attributes = True


class BatchEnrollmentRequest(BaseModel):
    subject_ids: list[str]


class BatchEnrollmentResponse(BaseModel):
    message: str
    enrolled_count: int
    enrolled_subject_ids: list[str]


class SubjectSummaryMetrics(BaseModel):
    total_subjects: int
    assigned_subjects: int
    unassigned_subjects: int
    total_enrollments: int


class AssignedLecturerInfo(BaseModel):
    id: str
    full_name: str
    email: str
    employee_id: Optional[str] = None
    department: Optional[str] = None
    assignment_id: Optional[str] = None


class SubjectListItem(BaseModel):
    id: str
    name: str
    code: str
    department: str
    year: int
    semester: int
    assigned_lecturers: list[AssignedLecturerInfo] = []
    assigned_lecturers_count: int = 0
    enrolled_students_count: int = 0
    created_at: datetime

    class Config:
        from_attributes = True


class SubjectListResponse(BaseModel):
    items: list[SubjectListItem]
    total: int
    page: int
    limit: int
    pages: int


class EnrolledStudentInfo(BaseModel):
    id: str
    full_name: str
    email: str
    student_id: Optional[str] = None
    department: Optional[str] = None
    year: Optional[int] = None
    section: Optional[str] = None
    enrollment_id: str


class SubjectDetailResponse(BaseModel):
    id: str
    name: str
    code: str
    department: str
    year: int
    semester: int
    assigned_lecturers: list[AssignedLecturerInfo] = []
    assigned_lecturers_count: int = 0
    enrolled_students: list[EnrolledStudentInfo] = []
    enrolled_students_count: int = 0
    created_at: datetime

    class Config:
        from_attributes = True


class LecturerAssignmentCreate(BaseModel):
    lecturer_id: str
    subject_id: str


class LecturerAssignmentResponse(BaseModel):
    id: str
    lecturer_id: str
    subject_id: str
    lecturer_name: str
    lecturer_email: str
    lecturer_employee_id: Optional[str] = None
    lecturer_department: Optional[str] = None
    subject_name: str
    subject_code: str
    subject_department: str
    subject_year: int
    subject_semester: int
    created_at: datetime

    class Config:
        from_attributes = True


class AssignmentSummaryMetrics(BaseModel):
    total_assignments: int
    assigned_lecturers: int
    assigned_subjects: int
    unassigned_subjects: int


