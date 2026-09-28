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
