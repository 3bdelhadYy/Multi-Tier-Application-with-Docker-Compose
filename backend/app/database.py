import os
import time
import logging
from sqlalchemy import create_engine, text
from sqlalchemy.orm import declarative_base, sessionmaker

logger = logging.getLogger("course_reg_backend")
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")

# Environment variables with sensible defaults
DB_USER = os.getenv("POSTGRES_USER", "postgres_user")
DB_PASSWORD = os.getenv("POSTGRES_PASSWORD", "postgres_secure_pass_72")
DB_HOST = os.getenv("POSTGRES_HOST", "db")
DB_PORT = os.getenv("POSTGRES_PORT", "5432")
DB_NAME = os.getenv("POSTGRES_DB", "course_registration_db")

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
)

# SQLite fallback for testing environments
if DATABASE_URL.startswith("sqlite"):
    engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
else:
    engine = create_engine(
        DATABASE_URL,
        pool_pre_ping=True,
        pool_size=10,
        max_overflow=20
    )

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def wait_for_db(max_retries: int = 30, delay_seconds: float = 2.0):
    """Wait for database server readiness on startup."""
    logger.info("Connecting to database at %s:%s...", DB_HOST, DB_PORT)
    for attempt in range(1, max_retries + 1):
        try:
            with engine.connect() as conn:
                conn.execute(text("SELECT 1"))
            logger.info("Successfully connected to database on attempt %d.", attempt)
            return True
        except Exception as exc:
            logger.warning("Database not ready yet (attempt %d/%d): %s", attempt, max_retries, exc)
            time.sleep(delay_seconds)
    raise RuntimeError(f"Could not connect to database after {max_retries} attempts.")

def init_db():
    """Create tables and seed initial data idempotently."""
    from app.models import Student, Course, Registration
    Base.metadata.create_all(bind=engine)
    logger.info("Database tables verified/created.")

    # Seed data idempotently
    with SessionLocal() as db:
        if db.query(Student).count() == 0 and db.query(Course).count() == 0:
            logger.info("Database is empty. Seeding initial courses, students, and registrations...")
            
            # 3 Courses
            c1 = Course(code="CS101", title="Introduction to Computer Science", seats=3)
            c2 = Course(code="NET202", title="Computer Networks & Cloud Infrastructure", seats=2)
            c3 = Course(code="SEC303", title="Cybersecurity Fundamentals", seats=1)
            db.add_all([c1, c2, c3])
            db.flush()

            # 3 Students
            s1 = Student(name="Alice Johnson", email="alice@example.com")
            s2 = Student(name="Bob Smith", email="bob@example.com")
            s3 = Student(name="Charlie Brown", email="charlie@example.com")
            db.add_all([s1, s2, s3])
            db.flush()

            # Seed sample registrations:
            # Alice and Bob in CS101 (2 of 3 seats filled)
            # Charlie in SEC303 (1 of 1 seat filled -> course full for test)
            r1 = Registration(student_id=s1.id, course_id=c1.id)
            r2 = Registration(student_id=s2.id, course_id=c1.id)
            r3 = Registration(student_id=s3.id, course_id=c3.id)
            db.add_all([r1, r2, r3])
            
            db.commit()
            logger.info("Initial seed data successfully committed.")
        else:
            logger.info("Existing records detected in database. Seeding skipped.")
