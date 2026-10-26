# Implementation Progress Log — Student Course Registration System

## Project Information
- **Course**: Cloud Computing Lab 4 — Part 2 Assignment
- **Student ID Suffix**: `72`
- **Host Port**: `8072`
- **Stack**: Nginx (Frontend) + FastAPI (Backend) + PostgreSQL (Database)

---

## Phase 1 — Environment and Project Setup
- **Status**: PASSED
- **Verification Details**:
  - **Operating System / Kernel**: Ubuntu 26.04.1 LTS on WSL2 (`Linux DESKTOP-7EOR15R 6.6.114.1-microsoft-standard-WSL2 x86_64 GNU/Linux`)
  - **Docker Engine**: Version `29.1.3`, build `29.1.3-0ubuntu4.1`
  - **Docker Compose**: Version `2.40.3+ds1-0ubuntu1`
  - **Docker Daemon Connectivity**: Active and running under systemd; tested with `docker run --rm hello-world` (Passed).
  - **User Permissions**: Added `hady` to `docker` group; rootless Docker commands verified functional.
  - **Base Images Pulled**:
    - `nginx:alpine` (Present)
    - `python:3.12-slim` (Present)
    - `postgres:16-alpine` (Pulled successfully: `sha256:f4610795587492cd4fb887c2dc3de301b813278bb6f616992061141b5f15ac36`)
  - **Port Verification**: Port `8072` verified free and available on host.
  - **Directory & Secret Structure**:
    - Git initialized.
    - `.gitignore` configured to ignore `.env`, pycache, etc.
    - `.env.example` created with safe placeholders.
    - Local `.env` created with development variables (ignored by Git).


---

## Phase 2 — Database and API Design
- **Status**: PASSED
- **Verification Details**:
  - **Schema Design**: Tables `students`, `courses`, `registrations` designed with primary keys, foreign keys (`ON DELETE CASCADE`), timestamp fields, and unique constraints (`email`, `code`, `(student_id, course_id)`).
  - **Concurrency & Capacity Control**: Course row locking using `SELECT ... FOR UPDATE` inside an isolated transaction guarantees zero race conditions on concurrent seat claims.
  - **API Contract**: Defined all REST endpoints (`/api/health`, `/api/courses`, `/api/students`, `/api/registrations`, `/api/courses/{id}/students`) with strict status codes (200, 201, 400, 404, 409, 503).
  - **Documentation**: Generated `docs/architecture.md` with detailed architecture diagram, network topology, schema details, and concurrency specs.


---

## Phase 3 — Backend Implementation
- **Status**: PASSED
- **Verification Details**:
  - **Framework & Dependencies**: FastAPI, Uvicorn, SQLAlchemy 2.0, Pydantic v2, psycopg2-binary, email-validator.
  - **Models & Relationships**: `Student`, `Course`, `Registration` with foreign keys, cascade deletion, unique constraints, and check constraints.
  - **Concurrency & Transaction Safety**: `with_for_update()` course row lock applied before checking seat capacity and recording registration.
  - **Automated Tests**: Implemented test suite in `backend/tests/test_api.py` covering:
    - Health check endpoint
    - Course creation, duplicate code rejection (409), input validation (422)
    - Student creation, duplicate email rejection (409), input validation (422)
    - Registration workflow, duplicate registration rejection (409), capacity limit enforcement (409)
    - Course roster query and registration cancellation (seat freeing)
    - Course cascade deletion
  - **Execution Result**: All 8 automated test cases executed inside Docker container and passed (100% pass rate).


---

## Phase 4 — Frontend Implementation
- **Status**: PASSED
- **Verification Details**:
  - **Interface**: Designed and built responsive UI in `frontend/index.html`, `frontend/styles.css`, and `frontend/app.js`.
  - **Features Implemented**:
    - Course management (add course, view table, see seat capacity vs remaining seats, view roster modal, delete course with cascade warning).
    - Student management (add student, view table with ID, name, email, registration date).
    - Course enrollment (dynamic dropdowns displaying remaining seats, register button, active registrations table, cancellation button).
    - Real-time health badge and database status indicator querying `/api/health`.
    - User feedback notifications for duplicate email, duplicate code, duplicate enrollment, and full courses.
  - **Nginx Reverse Proxy**: Configured `frontend/nginx.conf` to serve static assets on port 80 and reverse-proxy `/api/` to `http://backend:8000/api/`. Verified `nginx -t` configuration syntax syntax is OK.


---

## Phase 5 — Docker Compose Deployment
- **Status**: PASSED
- **Verification Details**:
  - **Compose Configuration**: Created `compose.yaml` with 3 services (`frontend`, `backend`, `db`), 2 isolated networks (`registration_frontend_network`, `registration_database_network`), and 1 named volume (`registration_postgres_data`).
  - **Service Reliability**:
    - PostgreSQL health check configured using `pg_isready`.
    - Backend configured with `depends_on: db: condition: service_healthy`.
    - Restart policies set to `restart: unless-stopped` on all 3 services.
  - **Port Binding**: Only `frontend` publishes host port `8072:80`. Backend (8000) and Database (5432) have zero host port publications.
  - **Deployment Execution**: Executed `docker compose up -d --build`. All services created, db transitioned to `healthy`, backend initialized schema & seeded data, frontend began serving.
  - **Reachability Verification**:
    - Verified `curl.exe http://localhost:8072/` returns the application single-page interface with title `Student Course Registration System | Port 8072`.
    - Verified `curl.exe http://localhost:8072/api/health` returns `{"status":"ok","database":"connected","timestamp":"..."}`.


---

## Phase 6 — Functional and Infrastructure Tests
- **Status**: PASSED
- **Verification Details**:
  - **Functional Scenarios**: Executed comprehensive live test script (`docs/test_live.sh`) against `http://localhost:8072`:
    - Add/list courses: PASSED (HTTP 201, 200).
    - Unique course code rejection: PASSED (HTTP 409).
    - Add/list students: PASSED (HTTP 201, 200).
    - Unique student email rejection: PASSED (HTTP 409).
    - Registration workflow: PASSED (HTTP 201).
    - Duplicate registration rejection: PASSED (HTTP 409).
    - Seat capacity enforcement on full course: PASSED (HTTP 409).
    - Course roster query: PASSED (HTTP 200).
    - Registration cancellation & seat release: PASSED (HTTP 200).
    - Re-enrollment into released seat: PASSED (HTTP 201).
    - Invalid input validation (seats < 1, invalid email syntax): PASSED (HTTP 422).
    - Course cascade deletion: PASSED (HTTP 200).
  - **Infrastructure Scenarios**:
    - Port publication: Verified ONLY `registration-frontend` publishes `0.0.0.0:8072->80/tcp`. Backend and DB publish zero host ports (PASSED).
    - Network isolation: Verified `registration-frontend` cannot reach or resolve `registration-db` (PASSED).
    - Volume persistence: Teardown via `docker compose down` and restart via `docker compose up -d` verified 100% preservation of all student, course, and registration records (PASSED).
    - Fault injection: Deliberate stoppage of `db` verified 503 response and clear logs; recovery restored 200 OK (PASSED).
    - Full details recorded in `docs/testing-and-troubleshooting.md`.


---

## Phase 7 — Documentation, Evidence, and Demo Preparation
- **Status**: PASSED
- **Verification Details**:
  - **Architecture Documentation**: Finalized `docs/architecture.md` with full specifications, schema tables, concurrency strategy, and note for student to draw their own diagram.
  - **Evidence Checklist**: Created `docs/evidence-checklist.md` detailing the 13 required screenshot items, exact CLI commands, what to display, and verified status.
  - **Technical Report**: Created `report/lab4-final-report.md` following all assignment sections, deliverables, and real verified findings (no fabricated claims). Also created `report/report-outline.md`.
  - **Demo Script**: Created `docs/demo-script.md` with a minute-by-minute 5-minute walkthrough covering architecture, UI, concurrency validation, database inspection, network isolation, persistence, and fault injection.
  - **README.md**: Created comprehensive operational guide at project root with exact commands for startup, testing, inspection, and safe shutdown.
  - **Final Requirement-to-Evidence Matrix**: 100% of functional, architectural, networking, and persistence requirements have been implemented and self-verified against the running Docker deployment.
