# Architecture and System Design Document
## Student Course Registration System (Multi-Tier Docker Compose)

### 1. Architectural Overview

The application follows a classic three-tier architecture containerized with Docker Compose:
- **Presentation Tier (`frontend`)**: Lightweight Nginx web server serving a responsive single-page application (HTML5, CSS3, JavaScript ES6) and acting as a reverse proxy for all API calls.
- **Application Tier (`backend`)**: High-performance Python FastAPI REST API enforcing validation, relational business logic, concurrency control, and database interactions.
- **Database Tier (`db`)**: PostgreSQL 16 relational database with ACID guarantees, constraints, and named persistent volume storage.

```
                  +-------------------------------------------------+
                  |                   HOST MACHINE                  |
                  |                Browser / Client                 |
                  +-------------------------------------------------+
                                           |
                                  Port 8072:80 (HTTP)
                                           v
+-----------------------------------------------------------------------------------+
| DOCKER COMPOSE ENVIRONMENT                                                        |
|                                                                                   |
|  +-----------------------------+                                                  |
|  |       frontend (Nginx)      |                                                  |
|  |  - Serves static HTML/JS/CSS|                                                  |
|  |  - Reverse proxy /api/      |                                                  |
|  +-----------------------------+                                                  |
|                 |                                                                 |
|                 | (frontend-network: bridge)                                      |
|                 v                                                                 |
|  +-----------------------------+                                                  |
|  |       backend (FastAPI)     |                                                  |
|  |  - REST API & Validation    |                                                  |
|  |  - Concurrency Locking      |                                                  |
|  +-----------------------------+                                                  |
|                 |                                                                 |
|                 | (database-network: bridge)                                      |
|                 v                                                                 |
|  +-----------------------------+          +------------------------------------+  |
|  |          db (PostgreSQL 16) | <=====>  | Named Volume: postgres_data        |  |
|  |  - Relational Schema        |          | (Persistent relational data)       |  |
|  |  - Foreign Keys & Uniques   |          +------------------------------------+  |
|  +-----------------------------+                                                  |
+-----------------------------------------------------------------------------------+
```

---

### 2. Network Topology and Isolation

To adhere to security best practices and assignment requirements:
1. **`frontend-network`**: Connects `frontend` and `backend`.
2. **`database-network`**: Connects `backend` and `db`.
3. **Isolation Guarantee**: The `frontend` container is NOT connected to `database-network`. It is physically unable to resolve or reach PostgreSQL container IP or port 5432.
4. **Single Ingress**: Only `frontend` publishes a port to the host machine (`8072:80`). The backend and database containers do not publish any ports to the host (`0.0.0.0` or otherwise).

---

### 3. Database Schema Design

#### `students`
| Column | Type | Constraints | Description |
|---|---|---|---|
| `id` | SERIAL / INTEGER | PRIMARY KEY | Unique student identifier |
| `name` | VARCHAR(120) | NOT NULL | Full name of the student |
| `email` | VARCHAR(160) | NOT NULL, UNIQUE | Student email address |
| `created_at` | TIMESTAMP | DEFAULT CURRENT_TIMESTAMP | Record creation time |

#### `courses`
| Column | Type | Constraints | Description |
|---|---|---|---|
| `id` | SERIAL / INTEGER | PRIMARY KEY | Unique course identifier |
| `code` | VARCHAR(30) | NOT NULL, UNIQUE | Unique course code (e.g., CS101) |
| `title` | VARCHAR(160) | NOT NULL | Descriptive course title |
| `seats` | INTEGER | NOT NULL, CHECK (seats >= 0) | Maximum registration capacity |
| `created_at` | TIMESTAMP | DEFAULT CURRENT_TIMESTAMP | Record creation time |

#### `registrations`
| Column | Type | Constraints | Description |
|---|---|---|---|
| `id` | SERIAL / INTEGER | PRIMARY KEY | Unique registration identifier |
| `student_id` | INTEGER | NOT NULL, REFERENCES students(id) ON DELETE CASCADE | Student reference |
| `course_id` | INTEGER | NOT NULL, REFERENCES courses(id) ON DELETE CASCADE | Course reference |
| `registered_at` | TIMESTAMP | DEFAULT CURRENT_TIMESTAMP | Registration timestamp |
| *Constraint* | UNIQUE(student_id, course_id) | UNIQUE | Prevents duplicate student registration |

#### Course Deletion Policy
- When a course is deleted, associated registrations are removed automatically via `ON DELETE CASCADE`. This ensures referential integrity without leaving orphaned registration records.

---

### 4. Concurrency and Capacity Control

To eliminate race conditions when multiple users attempt to register simultaneously for the last available seat:
1. Registration requests are handled inside an explicit SQL transaction.
2. The transaction executes:
   ```sql
   SELECT id, code, title, seats FROM courses WHERE id = :course_id FOR UPDATE;
   ```
3. `FOR UPDATE` acquires a row-level exclusive lock on the specific course record for the duration of the transaction.
4. Any concurrent registration attempt for the same course will wait until the first transaction commits or rolls back.
5. While holding the lock:
   - Check if student is already registered:
     ```sql
     SELECT 1 FROM registrations WHERE student_id = :student_id AND course_id = :course_id;
     ```
   - Check current registration count:
     ```sql
     SELECT COUNT(*) FROM registrations WHERE course_id = :course_id;
     ```
   - If `count >= seats`, raise HTTP 409 Conflict ("Course capacity reached; no seats remaining").
   - If valid, execute `INSERT INTO registrations ...` and commit.

---

### 5. REST API Specifications

| Method | Path | Request Body | Status Codes | Description |
|---|---|---|---|---|
| `GET` | `/api/health` | None | `200 OK`, `503 Service Unavailable` | Health check verifying DB connectivity |
| `GET` | `/api/courses` | None | `200 OK` | List all courses with enrolled & remaining seats |
| `POST` | `/api/courses` | `{"code": str, "title": str, "seats": int}` | `201 Created`, `400 Bad Request`, `409 Conflict` | Create new course (unique code enforced) |
| `DELETE`| `/api/courses/{id}`| None | `200 OK`, `404 Not Found` | Delete course and cascade its registrations |
| `GET` | `/api/students` | None | `200 OK` | List all students |
| `POST` | `/api/students` | `{"name": str, "email": str}` | `201 Created`, `400 Bad Request`, `409 Conflict` | Create student (unique email enforced) |
| `GET` | `/api/courses/{id}/students` | None | `200 OK`, `404 Not Found` | List students registered in a course |
| `POST` | `/api/registrations` | `{"student_id": int, "course_id": int}` | `201 Created`, `400 Bad Request`, `404 Not Found`, `409 Conflict` | Register a student in a course with atomic capacity check |
| `DELETE`| `/api/registrations/{id}`| None | `200 OK`, `404 Not Found` | Cancel registration |

---

### 6. Idempotent Database Seeding

On startup, the backend automatically creates tables if not present and verifies whether sample data exists.
Initial seed dataset:
- **Students**:
  1. `Alice Johnson` (`alice@example.com`)
  2. `Bob Smith` (`bob@example.com`)
  3. `Charlie Brown` (`charlie@example.com`)
- **Courses**:
  1. `CS101` — `Introduction to Computer Science` (Capacity: 3 seats)
  2. `NET202` — `Computer Networks & Cloud Infrastructure` (Capacity: 2 seats)
  3. `SEC303` — `Cybersecurity Fundamentals` (Capacity: 1 seat)
- **Registrations**:
  - Alice in `CS101`
  - Bob in `CS101`
  - Charlie in `SEC303` (Filling `SEC303` to demonstrate full capacity limit)
