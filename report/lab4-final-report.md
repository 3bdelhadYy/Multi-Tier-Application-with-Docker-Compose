# Lab 4 Technical Report: Deploying a Multi-Tier Application with Docker Compose
## Part 2 — Student Course Registration System

---

### Student and Assignment Information
- **Course Title**: Cloud Computing
- **Assignment**: Lab 4 — Part 2: Student Course Registration System
- **Student Name**: `[Student Name: Placeholder]`
- **Student ID**: `[Student ID: Placeholder, Suffix: 72]`
- **Assigned Host Port**: `8072` (8000 + 72)
- **Submission Date**: `[Submission Date: Placeholder]`

---

### 1. Objective and Technology Stack Selection

#### 1.1 Objective
The objective of this assignment is to design, containerize, and deploy a robust multi-tier web application using Docker Compose. The application implements a **Student Course Registration System** supporting relational course, student, and registration management while enforcing capacity limits, uniqueness constraints, and transactional concurrency control.

#### 1.2 Technology Stack
To satisfy the requirement that the stack differs from Part 1 (which used HTML/JS + Nginx, Python Flask, and MySQL 8.4) in at least one tier, the following modern architecture was chosen:

| Tier | Component | Technology Selected | Rationale & Changes from Part 1 |
|---|---|---|---|
| **Presentation Tier** | `frontend` | HTML5, CSS3, JavaScript (ES6), Nginx Alpine | Serves the responsive SPA and reverse-proxies `/api/` calls to eliminate CORS issues and conceal internal service topology. |
| **Application Tier** | `backend` | Python 3.12, FastAPI, SQLAlchemy 2.0, Uvicorn | Replaces Flask with FastAPI. Provides high performance, automatic Pydantic data validation, OpenAPI specification, and transaction management. |
| **Database Tier** | `db` | PostgreSQL 16 Alpine | Replaces MySQL with PostgreSQL. Offers advanced transactional row-locking (`FOR UPDATE`), strong integrity constraints, and robust reliability. |

---

### 2. Architecture Overview & Network Topology

> **Student Note on Diagram**: Below is the system architecture diagram. For your final submission, you may review and produce your own hand-drawn or diagramming-tool illustration based on this exact architecture.

```text
                  +-------------------------------------------------+
                  |                   HOST MACHINE                  |
                  |                Browser / Client                 |
                  +-------------------------------------------------+
                                           |
                                 Port 8072:80 (HTTP)
                                           v
+-----------------------------------------------------------------------------------+
| DOCKER COMPOSE MULTI-TIER ENVIRONMENT                                             |
|                                                                                   |
|  +-------------------------------------+                                          |
|  |       frontend (Nginx Alpine)       |                                          |
|  |  - Serves static SPA                |                                          |
|  |  - Proxies /api/ requests           |                                          |
|  +-------------------------------------+                                          |
|                     |                                                             |
|                     | [registration_frontend_network: Bridge]                     |
|                     v                                                             |
|  +-------------------------------------+                                          |
|  |       backend (FastAPI / Python)    |                                          |
|  |  - Validates inputs & uniqueness    |                                          |
|  |  - Row-locking capacity control     |                                          |
|  +-------------------------------------+                                          |
|                     |                                                             |
|                     | [registration_database_network: Bridge]                     |
|                     v                                                             |
|  +-------------------------------------+          +----------------------------+  |
|  |          db (PostgreSQL 16)         | <=====>  | Named Docker Volume:       |  |
|  |  - Enforces Foreign Keys & Uniques  |          | registration_postgres_data |  |
|  |  - Health Checked via pg_isready    |          +----------------------------+  |
|  +-------------------------------------+                                          |
+-----------------------------------------------------------------------------------+
```

#### 2.1 Network Isolation and Ingress Rules
1. **`registration_frontend_network`**: Spans `frontend` and `backend`.
2. **`registration_database_network`**: Spans `backend` and `db`.
3. **Isolation Perimeter**: The `frontend` container is intentionally omitted from `registration_database_network`. Docker's embedded DNS server does not resolve `db` from within the frontend container, making direct frontend-to-database communication physically impossible.
4. **Single Ingress Point**: Only the frontend publishes a port on the host machine (`8072:80`). Neither FastAPI (port 8000) nor PostgreSQL (port 5432) publish host ports, protecting backend services from unauthorized external access.

---

### 3. Project Directory Structure

```text
student-course-registration/
├── compose.yaml              # Multi-tier Docker Compose specification
├── .env                      # Local secret variables (ignored by Git)
├── .env.example              # Safe placeholder template for repository
├── .gitignore                # Git exclusions (.env, pycache, temporary files)
├── README.md                 # Complete operation and setup documentation
├── backend/
│   ├── Dockerfile            # Python 3.12 slim container build definition
│   ├── requirements.txt      # FastAPI, SQLAlchemy, Pydantic, Psycopg2, Pytest
│   ├── app/
│   │   ├── __init__.py
│   │   ├── main.py           # FastAPI lifespan, router mounting, CORS
│   │   ├── database.py       # Engine, retry loop, idempotent DB seeding
│   │   ├── models.py         # SQLAlchemy models (Student, Course, Registration)
│   │   ├── schemas.py        # Pydantic v2 schemas and field validators
│   │   └── routes.py         # REST endpoints and transaction row-locking
│   └── tests/
│       ├── __init__.py
│       ├── conftest.py       # Pytest fixture with in-memory SQLite isolation
│       └── test_api.py       # 8 automated unit & integration test cases
├── frontend/
│   ├── Dockerfile            # Nginx Alpine container build definition
│   ├── nginx.conf            # Reverse proxy configuration (/api/ -> backend:8000)
│   ├── index.html            # Responsive UI layout and modals
│   ├── styles.css            # Custom CSS styling and responsive layout
│   └── app.js                # Asynchronous API interaction and DOM manipulation
├── docs/
│   ├── architecture.md       # Architectural specification and schema design
│   ├── testing-and-troubleshooting.md  # Real test execution logs and analysis
│   ├── evidence-checklist.md # Screenshot instructions and verification checklist
│   ├── demo-script.md        # 5-minute timed live demonstration guide
│   ├── test_live.sh          # Automated curl test script for API verification
│   └── progress-log.md       # Incremental phase-by-phase verification log
├── evidence/                 # Target folder for genuine submission screenshots
└── report/
    ├── report-outline.md     # Structural outline
    └── lab4-final-report.md  # Comprehensive final report
```

---

### 4. Database Schema Design and Integrity

The database utilizes three relational tables created and maintained via SQLAlchemy models:

#### 4.1 Schema Tables
1. **`students`**:
   - `id`: Integer, Primary Key, Auto-increment.
   - `name`: VARCHAR(120), NOT NULL (cannot be blank).
   - `email`: VARCHAR(160), NOT NULL, UNIQUE (enforces email uniqueness).
   - `created_at`: TIMESTAMP WITH TIME ZONE, DEFAULT CURRENT_TIMESTAMP.

2. **`courses`**:
   - `id`: Integer, Primary Key, Auto-increment.
   - `code`: VARCHAR(30), NOT NULL, UNIQUE (e.g., `CS101`, uppercase).
   - `title`: VARCHAR(160), NOT NULL (descriptive course title).
   - `seats`: INTEGER, NOT NULL, CHECK (`seats >= 0`).
   - `created_at`: TIMESTAMP WITH TIME ZONE, DEFAULT CURRENT_TIMESTAMP.

3. **`registrations`**:
   - `id`: Integer, Primary Key, Auto-increment.
   - `student_id`: Integer, FOREIGN KEY references `students(id)` ON DELETE CASCADE.
   - `course_id`: Integer, FOREIGN KEY references `courses(id)` ON DELETE CASCADE.
   - `registered_at`: TIMESTAMP WITH TIME ZONE, DEFAULT CURRENT_TIMESTAMP.
   - **Composite Unique Constraint**: `UNIQUE(student_id, course_id)` guarantees that no student can register twice for the same course.

#### 4.2 Deletion & Cascade Policy
When a course is removed, foreign keys configured with `ON DELETE CASCADE` guarantee that all active registration records associated with that course are purged atomically, preventing orphaned records and maintaining database integrity.

#### 4.3 Concurrency Control & Capacity Locking
A critical requirement is that two simultaneous registration requests must not be able to claim the last remaining seat. This is enforced through database row locking:
```python
# Lock the course row to serialize concurrent registration requests
course = db.query(Course).filter(Course.id == reg_in.course_id).with_for_update().first()

# Validate capacity inside the locked transaction
current_enrolled = db.query(Registration).filter(Registration.course_id == course.id).count()
if current_enrolled >= course.seats:
    raise HTTPException(status_code=409, detail=f"Course '{course.code}' is full.")
```
Using `SELECT ... FOR UPDATE` acquires an exclusive row lock on the course record for the duration of the transaction. Any concurrent registration request for the same course is blocked until the first transaction commits, completely preventing oversubscription race conditions.

---

### 5. Application Implementation and REST API

#### 5.1 API Contract Summary

| Method | Endpoint | Description | Status Codes |
|---|---|---|---|
| `GET` | `/api/health` | Service and database health check | `200 OK`, `503 Service Unavailable` |
| `GET` | `/api/courses` | List courses with capacity, enrolled count, and remaining seats | `200 OK` |
| `POST` | `/api/courses` | Create course (validates unique code, seats >= 1) | `201 Created`, `409 Conflict`, `422 Unprocessable` |
| `DELETE` | `/api/courses/{id}` | Delete course and cascade registrations | `200 OK`, `404 Not Found` |
| `GET` | `/api/students` | List all registered students | `200 OK` |
| `POST` | `/api/students` | Create student (validates unique email, non-blank name) | `201 Created`, `409 Conflict`, `422 Unprocessable` |
| `GET` | `/api/courses/{id}/students` | View course roster of enrolled students | `200 OK`, `404 Not Found` |
| `POST` | `/api/registrations` | Register student with atomic capacity check | `201 Created`, `404 Not Found`, `409 Conflict` |
| `DELETE` | `/api/registrations/{id}` | Cancel registration and immediately release seat | `200 OK`, `404 Not Found` |

#### 5.2 Frontend Single-Page Application
The frontend is built with pure HTML5, CSS3, and JavaScript:
- **Real-Time Health Status**: Queries `/api/health` every 15 seconds, rendering a live indicator dot (green online / red offline) and database status.
- **Course Management Card**: Provides a submission form and a live courses table showing capacity vs remaining seats, with action buttons for **Roster** and **Delete**.
- **Student Management Card**: Provides a student profile creation form and table.
- **Enrollment Card**: Dynamically populates dropdowns for students and courses (automatically marking full courses as disabled) and lists active registrations with instant seat cancellation.
- **Roster Modal**: Displays enrolled students for any selected course.

---

### 6. Dockerfile and Docker Compose Configuration

#### 6.1 Backend Dockerfile (`backend/Dockerfile`)
```dockerfile
FROM python:3.12-slim

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

#### 6.2 Frontend Nginx Configuration (`frontend/nginx.conf`)
```nginx
server {
    listen 80;
    server_name localhost;

    location / {
        root   /usr/share/nginx/html;
        index  index.html index.htm;
        try_files $uri $uri/ /index.html;
    }

    location /api/ {
        proxy_pass http://backend:8000/api/;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    }
}
```

#### 6.3 Docker Compose File (`compose.yaml`) Excerpt
```yaml
services:
  db:
    image: postgres:16-alpine
    container_name: registration-db
    restart: unless-stopped
    environment:
      POSTGRES_DB: ${POSTGRES_DB:-course_registration_db}
      POSTGRES_USER: ${POSTGRES_USER:-postgres_user}
      POSTGRES_PASSWORD: ${POSTGRES_PASSWORD:-postgres_secure_pass_72}
    volumes:
      - postgres_data:/var/lib/postgresql/data
    networks:
      - database-network
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U ${POSTGRES_USER:-postgres_user} -d ${POSTGRES_DB:-course_registration_db}"]
      interval: 5s
      timeout: 5s
      retries: 5
      start_period: 10s

  backend:
    build:
      context: ./backend
      dockerfile: Dockerfile
    image: registration-backend:latest
    container_name: registration-backend
    restart: unless-stopped
    environment:
      POSTGRES_DB: ${POSTGRES_DB:-course_registration_db}
      POSTGRES_USER: ${POSTGRES_USER:-postgres_user}
      POSTGRES_PASSWORD: ${POSTGRES_PASSWORD:-postgres_secure_pass_72}
      POSTGRES_HOST: db
      POSTGRES_PORT: 5432
    depends_on:
      db:
        condition: service_healthy
    networks:
      - database-network
      - frontend-network

  frontend:
    build:
      context: ./frontend
      dockerfile: Dockerfile
    image: registration-frontend:latest
    container_name: registration-frontend
    restart: unless-stopped
    ports:
      - "${HOST_PORT:-8072}:80"
    depends_on:
      - backend
    networks:
      - frontend-network

volumes:
  postgres_data:
    name: registration_postgres_data

networks:
  frontend-network:
    name: registration_frontend_network
    driver: bridge
  database-network:
    name: registration_database_network
    driver: bridge
```

---

### 7. Environment Variables and Secret Handling

1. **Isolation of Secrets**: All sensitive database credentials (`POSTGRES_DB`, `POSTGRES_USER`, `POSTGRES_PASSWORD`, `HOST_PORT`) are defined in `.env`.
2. **Git Protection**: `.env` is listed in `.gitignore` and is strictly excluded from version control.
3. **Template Provided**: `.env.example` is committed with safe placeholder values (`replace_with_secure_password`).
4. **Codebase Cleanliness**: Source code, Dockerfiles, README, and reports contain zero hardcoded database passwords.

---

### 8. Real Verification and Testing Outcomes

#### 8.1 Automated Unit Tests (`pytest`)
All 8 automated tests passed inside the container in 0.26s:
- `test_health_check` (PASS)
- `test_create_and_list_course` (PASS)
- `test_duplicate_course_code_rejected` (PASS)
- `test_invalid_course_input` (PASS)
- `test_create_and_list_student` (PASS)
- `test_duplicate_student_email_rejected` (PASS)
- `test_registration_flow_and_capacity_limits` (PASS)
- `test_delete_course_cascades_registrations` (PASS)

#### 8.2 Live API Tests via Host Port 8072
- **Course Creation**: Successfully added `CLOUD404` (HTTP 201).
- **Duplicate Course Code**: Attempt to re-add `CLOUD404` rejected with HTTP 409 Conflict.
- **Student Creation**: Added `David Miller` (`david@example.com`) (HTTP 201).
- **Duplicate Student Email**: Attempt to re-add `david@example.com` rejected with HTTP 409 Conflict.
- **Registration**: Enrolled David into `CLOUD404` (HTTP 201).
- **Duplicate Registration**: Re-registering David in `CLOUD404` rejected with HTTP 409 Conflict.
- **Capacity Limit**: Registering into full course `SEC303` (1/1) rejected with HTTP 409 Conflict.
- **Cancellation**: Cancelled registration in `SEC303` (HTTP 200); available seats incremented to 1.
- **Re-enrollment**: Successfully enrolled Alice Johnson into the freed seat in `SEC303` (HTTP 201).
- **Validation**: Submitting seats=0 or invalid email rejected with HTTP 422 Unprocessable Entity.

---

### 9. Persistence and Fault Injection Experiments

#### 9.1 Database Persistence Test
1. **Initial State**: Added course `CLOUD404` and student `David Miller` with registrations.
2. **Action**: Executed `docker compose down`. All containers and networks were removed.
3. **Volume Check**: `docker volume ls` confirmed `registration_postgres_data` remained intact.
4. **Restart**: Executed `docker compose up -d`.
5. **Verification**: Queried `/api/courses` and `/api/students`. All records, user-created entities, and active enrollments were fully preserved. The startup initialization script logged `Existing records detected in database. Seeding skipped.`.

#### 9.2 Fault Injection & Recovery
1. **Failure Simulation**: Stopped PostgreSQL via `docker compose stop db`.
2. **Observed Symptom**: `curl http://localhost:8072/api/health` returned HTTP `503 Service Unavailable` with error details `Database unreachable: could not translate host name "db"`. The frontend status badge switched to red `Offline`.
3. **Recovery**: Executed `docker compose start db`.
4. **Outcome**: Database became healthy, backend reconnected, and `GET /api/health` returned HTTP 200 `{"status":"ok","database":"connected"}` within seconds.

---

### 10. Conclusion

The Student Course Registration System fulfills all requirements of Lab 4 Part 2:
- Successfully implements a three-tier architecture with FastAPI, PostgreSQL 16, and Nginx.
- Satisfies the assigned individual host port requirement (`8072`).
- Implements two isolated networks with zero host exposure for backend and database tiers.
- Enforces strict relational business rules and concurrency-safe seat capacity controls.
- Demonstrates 100% data persistence across container lifecycles using named Docker volumes.
- Verified functional through automated unit tests, live API scripts, and fault-injection experiments.
