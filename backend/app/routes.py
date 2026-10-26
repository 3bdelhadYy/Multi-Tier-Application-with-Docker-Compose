from datetime import datetime, timezone
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import text, func

from app.database import get_db
from app.models import Student, Course, Registration
from app.schemas import (
    StudentCreate, StudentOut,
    CourseCreate, CourseOut,
    RegistrationCreate, RegistrationOut,
    CourseRosterItem, HealthResponse
)

router = APIRouter(prefix="/api", tags=["Course Registration System"])

@router.get("/health", response_model=HealthResponse)
def health_check(db: Session = Depends(get_db)):
    """Check API and database connectivity."""
    try:
        db.execute(text("SELECT 1"))
        db_status = "connected"
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Database unreachable: {str(exc)}"
        )
    return HealthResponse(
        status="ok",
        database=db_status,
        timestamp=datetime.now(timezone.utc)
    )

# ----------------- COURSES -----------------

@router.get("/courses", response_model=List[CourseOut])
def list_courses(db: Session = Depends(get_db)):
    """List all courses with enrollment statistics."""
    courses = db.query(Course).order_by(Course.code.asc()).all()
    results = []
    for c in courses:
        enrolled = db.query(Registration).filter(Registration.course_id == c.id).count()
        results.append(CourseOut(
            id=c.id,
            code=c.code,
            title=c.title,
            seats=c.seats,
            enrolled_count=enrolled,
            available_seats=max(0, c.seats - enrolled),
            created_at=c.created_at
        ))
    return results

@router.post("/courses", response_model=CourseOut, status_code=status.HTTP_201_CREATED)
def create_course(course_in: CourseCreate, db: Session = Depends(get_db)):
    """Add a new course with unique code validation."""
    existing = db.query(Course).filter(Course.code == course_in.code).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Course with code '{course_in.code}' already exists."
        )

    new_course = Course(
        code=course_in.code,
        title=course_in.title,
        seats=course_in.seats
    )
    db.add(new_course)
    db.commit()
    db.refresh(new_course)
    return CourseOut(
        id=new_course.id,
        code=new_course.code,
        title=new_course.title,
        seats=new_course.seats,
        enrolled_count=0,
        available_seats=new_course.seats,
        created_at=new_course.created_at
    )

@router.delete("/courses/{course_id}", status_code=status.HTTP_200_OK)
def delete_course(course_id: int, db: Session = Depends(get_db)):
    """Delete a course. Cascades and cleans up associated registrations."""
    course = db.query(Course).filter(Course.id == course_id).first()
    if not course:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Course with ID {course_id} not found."
        )

    code = course.code
    title = course.title
    db.delete(course)
    db.commit()
    return {"message": f"Course '{code} - {title}' and its associated registrations were deleted successfully."}

# ----------------- STUDENTS -----------------

@router.get("/students", response_model=List[StudentOut])
def list_students(db: Session = Depends(get_db)):
    """List all students."""
    return db.query(Student).order_by(Student.name.asc()).all()

@router.post("/students", response_model=StudentOut, status_code=status.HTTP_201_CREATED)
def create_student(student_in: StudentCreate, db: Session = Depends(get_db)):
    """Add a student with unique email validation."""
    existing = db.query(Student).filter(Student.email == student_in.email).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Student with email '{student_in.email}' already exists."
        )

    new_student = Student(
        name=student_in.name,
        email=student_in.email
    )
    db.add(new_student)
    db.commit()
    db.refresh(new_student)
    return new_student

@router.delete("/students/{student_id}", status_code=status.HTTP_200_OK)
def delete_student(student_id: int, db: Session = Depends(get_db)):
    """Delete a student. Cascades and cleans up associated registrations."""
    student = db.query(Student).filter(Student.id == student_id).first()
    if not student:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Student with ID {student_id} not found."
        )

    name = student.name
    email = student.email
    db.delete(student)
    db.commit()
    return {"message": f"Student '{name}' ({email}) and their associated registrations were deleted successfully."}

# ----------------- REGISTRATIONS & ROSTER -----------------

@router.get("/courses/{course_id}/students", response_model=List[CourseRosterItem])
def get_course_roster(course_id: int, db: Session = Depends(get_db)):
    """List all students registered in a specific course."""
    course = db.query(Course).filter(Course.id == course_id).first()
    if not course:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Course with ID {course_id} not found."
        )

    regs = (
        db.query(Registration, Student)
        .join(Student, Registration.student_id == Student.id)
        .filter(Registration.course_id == course_id)
        .order_by(Registration.registered_at.asc())
        .all()
    )

    roster = []
    for reg, stu in regs:
        roster.append(CourseRosterItem(
            registration_id=reg.id,
            student_id=stu.id,
            name=stu.name,
            email=stu.email,
            registered_at=reg.registered_at
        ))
    return roster

@router.get("/registrations", response_model=List[RegistrationOut])
def list_all_registrations(db: Session = Depends(get_db)):
    """List all registrations across the system."""
    regs = (
        db.query(Registration, Student, Course)
        .join(Student, Registration.student_id == Student.id)
        .join(Course, Registration.course_id == Course.id)
        .order_by(Registration.registered_at.desc())
        .all()
    )

    out = []
    for r, s, c in regs:
        out.append(RegistrationOut(
            id=r.id,
            student_id=s.id,
            course_id=c.id,
            student_name=s.name,
            student_email=s.email,
            course_code=c.code,
            course_title=c.title,
            registered_at=r.registered_at
        ))
    return out

@router.post("/registrations", response_model=RegistrationOut, status_code=status.HTTP_201_CREATED)
def register_student(reg_in: RegistrationCreate, db: Session = Depends(get_db)):
    """
    Register a student in a course.
    Uses row-level locking on the course record to prevent concurrent oversubscription race conditions.
    """
    # 1. Lock the course record for update
    course_query = db.query(Course).filter(Course.id == reg_in.course_id)
    # SQLite does not support FOR UPDATE; handle gracefully if testing on SQLite
    if db.bind and db.bind.dialect.name != "sqlite":
        course = course_query.with_for_update().first()
    else:
        course = course_query.first()

    if not course:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Course with ID {reg_in.course_id} not found."
        )

    # 2. Check student existence
    student = db.query(Student).filter(Student.id == reg_in.student_id).first()
    if not student:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Student with ID {reg_in.student_id} not found."
        )

    # 3. Check duplicate registration
    existing_reg = db.query(Registration).filter(
        Registration.student_id == reg_in.student_id,
        Registration.course_id == reg_in.course_id
    ).first()
    if existing_reg:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Student '{student.name}' is already registered in course '{course.code}'."
        )

    # 4. Check seat capacity
    current_enrolled = db.query(Registration).filter(Registration.course_id == course.id).count()
    if current_enrolled >= course.seats:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Course '{course.code}' is full ({current_enrolled}/{course.seats} seats taken)."
        )

    # 5. Insert registration
    new_reg = Registration(student_id=student.id, course_id=course.id)
    db.add(new_reg)
    db.commit()
    db.refresh(new_reg)

    return RegistrationOut(
        id=new_reg.id,
        student_id=student.id,
        course_id=course.id,
        student_name=student.name,
        student_email=student.email,
        course_code=course.code,
        course_title=course.title,
        registered_at=new_reg.registered_at
    )

@router.delete("/registrations/{registration_id}", status_code=status.HTTP_200_OK)
def cancel_registration(registration_id: int, db: Session = Depends(get_db)):
    """Cancel a student's course registration."""
    reg = db.query(Registration).filter(Registration.id == registration_id).first()
    if not reg:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Registration with ID {registration_id} not found."
        )

    student_name = reg.student.name if reg.student else f"ID {reg.student_id}"
    course_code = reg.course.code if reg.course else f"ID {reg.course_id}"

    db.delete(reg)
    db.commit()
    return {"message": f"Registration for '{student_name}' in course '{course_code}' has been cancelled."}
