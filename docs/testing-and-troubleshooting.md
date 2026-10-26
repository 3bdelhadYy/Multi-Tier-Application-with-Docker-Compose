# Testing and Troubleshooting Report
## Multi-Tier Student Course Registration System (Docker Compose)

### 1. Functional Test Results Matrix

| # | Test Scenario | Executed Command / Request | Expected Outcome | Actual Outcome | Status |
|---|---|---|---|---|---|
| 1 | Health Check | `GET /api/health` | HTTP 200, DB connected | `{"status":"ok","database":"connected"}` | **PASS** |
| 2 | Add Course | `POST /api/courses` (`CLOUD404`, 2 seats) | HTTP 201 Created | Created Course ID 4, 2 available seats | **PASS** |
| 3 | Duplicate Course Code | `POST /api/courses` (`CLOUD404`) | HTTP 409 Conflict | `{"detail":"Course with code 'CLOUD404' already exists."}` | **PASS** |
| 4 | Add Student | `POST /api/students` (`David Miller`, `david@example.com`) | HTTP 201 Created | Created Student ID 4 | **PASS** |
| 5 | Duplicate Student Email | `POST /api/students` (`david@example.com`) | HTTP 409 Conflict | `{"detail":"Student with email 'david@example.com' already exists."}` | **PASS** |
| 6 | Course Registration | `POST /api/registrations` (`student_id: 4`, `course_id: 4`) | HTTP 201 Created | Registered David Miller in CLOUD404 | **PASS** |
| 7 | Duplicate Registration | `POST /api/registrations` (`student_id: 4`, `course_id: 4`) | HTTP 409 Conflict | `{"detail":"Student 'David Miller' is already registered in course 'CLOUD404'."}` | **PASS** |
| 8 | Course Capacity Enforcement | `POST /api/registrations` into full `SEC303` (1/1) | HTTP 409 Conflict | `{"detail":"Course 'SEC303' is full (1/1 seats taken)."}` | **PASS** |
| 9 | Course Roster Query | `GET /api/courses/1/students` | HTTP 200 OK | Returns Alice Johnson & Bob Smith | **PASS** |
| 10 | Cancel Registration & Free Seat | `DELETE /api/registrations/3` | HTTP 200 OK | Charlie's seat in SEC303 released | **PASS** |
| 11 | Enroll into Freed Seat | `POST /api/registrations` (Alice into `SEC303`) | HTTP 201 Created | Registration succeeded immediately | **PASS** |
| 12 | Field Validation | `seats: 0`, `email: "not-an-email"` | HTTP 422 Unprocessable | Validation rejected invalid fields with specific field errors | **PASS** |
| 13 | Course Cascade Deletion | `DELETE /api/courses/{id}` | HTTP 200 OK | Course & associated registrations deleted cleanly | **PASS** |

---

### 2. Infrastructure & Security Tests

#### A. Host Port Exposure
- **Requirement**: Only `frontend` publishes host port `8072`. Backend (8000) and Database (5432) must NOT publish ports to the host.
- **Verification Command**:
  ```bash
  docker port registration-frontend
  docker port registration-backend
  docker port registration-db
  ```
- **Actual Evidence**:
  ```text
  Frontend ports:
  80/tcp -> 0.0.0.0:8072
  80/tcp -> [::]:8072

  Backend ports:
  (empty - no host binding)

  DB ports:
  (empty - no host binding)
  ```
- **Result**: **PASS**.

#### B. Network Isolation & Security Perimeter
- **Requirement**: `frontend` must NOT be connected to `database-network` and must not reach PostgreSQL directly.
- **Verification Commands**:
  ```bash
  docker exec registration-frontend ping -c 1 -W 2 registration-db
  docker exec registration-frontend nc -z -w 3 registration-db 5432
  ```
- **Actual Evidence**:
  ```text
  ping: bad address 'registration-db'
  nc: bad address 'registration-db'
  ```
- **Analysis**: Because Docker's embedded DNS server only resolves container names within connected networks, `registration-frontend` cannot resolve or route packets to `registration-db`.
- **Result**: **PASS**.

#### C. Database Volume & State Persistence
- **Requirement**: Relational data must survive complete container teardown (`docker compose down` followed by `docker compose up -d`).
- **Verification Procedure**:
  1. Verified user data (`CLOUD404`, `David Miller`, custom registrations) existed in database.
  2. Executed `docker compose down` (preserving volume `registration_postgres_data`).
  3. Confirmed volume `registration_postgres_data` remained present in `docker volume ls`.
  4. Executed `docker compose up -d`.
  5. Queried `/api/courses`, `/api/students`, and `/api/registrations`.
- **Actual Evidence**:
  - All 4 courses, 4 students, and their registrations were preserved and intact.
  - Initial seed script detected existing records and idempotently skipped re-seeding (`Existing records detected in database. Seeding skipped.`).
- **Result**: **PASS**.

---

### 3. Fault Injection and Troubleshooting Experiment

#### Scenario: Database Tier Outage
1. **Action**: Deliberately stopped the database container while the web application was running:
   ```bash
   docker compose stop db
   ```
2. **Observed Symptoms**:
   - HTTP Request: `curl -i http://localhost:8072/api/health` returned:
     ```http
     HTTP/1.1 503 Service Unavailable
     Content-Type: application/json

     {"detail":"Database unreachable: (psycopg2.OperationalError) could not translate host name \"db\" to address: Name or service not known"}
     ```
   - User Interface: The header health status badge turned red and displayed `Offline • Backend unreachable`, and the database indicator switched from green to red `Disconnected`.
   - Backend Logs:
     ```text
     registration-backend | INFO: 172.22.0.3:57590 - "GET /api/health HTTP/1.1" 503 Service Unavailable
     ```
3. **Recovery Action**:
   ```bash
   docker compose start db
   ```
4. **Post-Recovery Behavior**:
   - PostgreSQL completed internal startup and became healthy.
   - Subsequent `GET /api/health` immediately returned:
     ```http
     HTTP/1.1 200 OK
     {"status":"ok","database":"connected","timestamp":"2026-10-22T18:07:27.326079Z"}
     ```
   - UI status indicator automatically self-healed to green `Online • DB: connected`.
- **Result**: **PASS**.

---

### 4. Container Restart Policy Analysis

- All three services configure `restart: unless-stopped`.
- **Key Technical Distinction**:
  - **Manually Stopped Containers**: When a container is stopped using `docker compose stop <service>` or `docker stop <container>`, Docker treats this as an intentional administrator action. The daemon records the explicit stop state and will NOT restart the container automatically.
  - **Unexpected Process Failure / Crash**: When a container process exits unexpectedly with a non-zero exit code or receives an unexpected termination signal (e.g., killed by OOM killer or crash), the Docker daemon evaluates `unless-stopped`, sees that the container was not intentionally stopped, and immediately initiates an automatic container restart.
