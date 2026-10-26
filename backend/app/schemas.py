from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field, EmailStr, field_validator, ConfigDict

class StudentCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=120, description="Full student name")
    email: EmailStr = Field(..., max_length=160, description="Unique student email")

    @field_validator("name")
    @classmethod
    def name_must_not_be_blank(cls, v: str) -> str:
        trimmed = v.strip()
        if not trimmed:
            raise ValueError("Student name must not be blank.")
        return trimmed

class StudentOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    email: str
    created_at: datetime

class CourseCreate(BaseModel):
    code: str = Field(..., min_length=2, max_length=30, description="Course code (e.g., CS101)")
    title: str = Field(..., min_length=2, max_length=160, description="Course title")
    seats: int = Field(..., ge=1, description="Seat capacity (must be at least 1)")

    @field_validator("code")
    @classmethod
    def code_must_not_be_blank(cls, v: str) -> str:
        trimmed = v.strip().upper()
        if not trimmed:
            raise ValueError("Course code must not be blank.")
        return trimmed

    @field_validator("title")
    @classmethod
    def title_must_not_be_blank(cls, v: str) -> str:
        trimmed = v.strip()
        if not trimmed:
            raise ValueError("Course title must not be blank.")
        return trimmed

class CourseOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    code: str
    title: str
    seats: int
    enrolled_count: int = 0
    available_seats: int = 0
    created_at: datetime

class RegistrationCreate(BaseModel):
    student_id: int = Field(..., ge=1, description="ID of the student")
    course_id: int = Field(..., ge=1, description="ID of the course")

class RegistrationOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    student_id: int
    course_id: int
    student_name: str
    student_email: str
    course_code: str
    course_title: str
    registered_at: datetime

class CourseRosterItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    registration_id: int
    student_id: int
    name: str
    email: str
    registered_at: datetime

class HealthResponse(BaseModel):
    status: str
    database: str
    timestamp: datetime
