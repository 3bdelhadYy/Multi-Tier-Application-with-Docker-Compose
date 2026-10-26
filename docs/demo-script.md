# Five-Minute Live Demo Script
## Student Course Registration System (Port 8072)

This script gives you an exact, minute-by-minute walkthrough for delivering an impressive, confident 5-minute presentation and live demonstration.

---

### Phase 1: Architecture & Service Inspection (0:00 – 0:40)
- **What to say**:
  > *"Good morning/afternoon. Today I am presenting my multi-tier Student Course Registration System deployed with Docker Compose. To fulfill the technology change constraint, I selected Python FastAPI for the application tier and PostgreSQL 16 for the database tier, served through an Nginx reverse proxy. My assigned individual student ID suffix is 72, which maps to host port 8072."*
- **What to show in terminal**:
  ```bash
  docker compose ps
  ```
- **What to point out**:
  - Show the three running services: `registration-frontend`, `registration-backend`, and `registration-db`.
  - Point out that `registration-db` reports `(healthy)` via its built-in PostgreSQL health check.
  - Emphasize that **only** `registration-frontend` publishes a host port (`8072:80`). Neither the backend nor the database are accessible from the host network.

---

### Phase 2: Web Interface & Core Operations (0:40 – 1:50)
- **What to say**:
  > *"Now let's open the web application running on port 8072."*
- **What to show in browser (`http://localhost:8072`)**:
  - Point out the top status bar: the green indicator reading `Online • DB: connected` and the badge confirming `Host Port: 8072`.
  - **Action 1 — Add a Course**:
    - Code: `AI505`
    - Title: `Artificial Intelligence & Cloud Systems`
    - Seats: `2`
    - Click **Add Course**. Show it appear in the course table with `2 remaining`.
  - **Action 2 — Add a Student**:
    - Name: `Emily Clark`
    - Email: `emily@example.com`
    - Click **Add Student**. Show it immediately appear in the student list.

---

### Phase 3: Registration, Concurrency Safety & Business Rules (1:50 – 2:40)
- **What to say**:
  > *"Next, we demonstrate business rules, capacity limits, and concurrency control."*
- **What to show in browser**:
  - **Enrollment**: Select `Emily Clark` and course `AI505`. Click **Register Student**.
    - Show registration appear in Active Registrations.
    - Show `AI505` available seats decrement from 2 to 1.
  - **Duplicate Registration Check**: Try registering `Emily Clark` in `AI505` again.
    - Point out the red error alert: *"Student 'Emily Clark' is already registered in course 'AI505'."*
  - **Capacity Limit Enforcement**:
    - Select course `SEC303` (which is already at 1/1 capacity).
    - Try to register any student into `SEC303`.
    - Point out the immediate rejection: *"Course 'SEC303' is full (1/1 seats taken)."*
    - Explain: *"In the backend, this is enforced with a database row lock using `FOR UPDATE` so concurrent requests cannot race to oversubscribe seats."*
  - **View Roster**: Click the **Roster** button on `CS101` to show the popup listing enrolled students (Alice Johnson and Bob Smith).

---

### Phase 4: Database Inspection & Referential Integrity (2:40 – 3:20)
- **What to say**:
  > *"Let's look directly inside PostgreSQL to verify referential integrity and the three related tables."*
- **What to show in terminal**:
  ```bash
  docker exec -it registration-db psql -U postgres_user -d course_registration_db -c "\dt"
  docker exec -it registration-db psql -U postgres_user -d course_registration_db -c "SELECT id, name, email FROM students;"
  docker exec -it registration-db psql -U postgres_user -d course_registration_db -c "SELECT id, code, title, seats FROM courses;"
  docker exec -it registration-db psql -U postgres_user -d course_registration_db -c "SELECT id, student_id, course_id, registered_at FROM registrations;"
  ```
- **What to explain**:
  - Point out foreign keys linking `registrations` to `students` and `courses`.
  - Point out that deleting a course triggers `ON DELETE CASCADE` to maintain database consistency without orphaned rows.

---

### Phase 5: Network Isolation & Security Proof (3:20 – 4:10)
- **What to say**:
  > *"Security is a core focus of this architecture. We use two isolated Docker networks."*
- **What to show in terminal**:
  ```bash
  # Test connection from frontend to database container
  docker exec registration-frontend ping -c 1 -W 2 registration-db
  docker exec registration-frontend nc -z -w 2 registration-db 5432
  ```
- **What to explain**:
  - Both commands fail with `bad address 'registration-db'`.
  - Explain: *"The frontend container only lives on `registration_frontend_network`. The database container only lives on `registration_database_network`. Only the FastAPI backend is attached to both networks to act as a secure intermediary."*

---

### Phase 6: Volume Persistence Across Teardown (4:10 – 4:40)
- **What to say**:
  > *"All application state is stored in a named Docker volume so data persists across container lifecycles."*
- **What to show in terminal**:
  ```bash
  docker compose down
  docker volume ls | grep postgres_data
  docker compose up -d
  curl -s http://localhost:8072/api/courses
  ```
- **What to explain**:
  - Point out that after tearing down containers with `docker compose down`, `registration_postgres_data` remained untouched.
  - When brought back up with `docker compose up -d`, our course `AI505` and student `Emily Clark` are still preserved.

---

### Phase 7: Fault Injection & Self-Healing Recovery (4:40 – 5:00)
- **What to say**:
  > *"Finally, we simulate a failure by stopping the database tier."*
- **What to show**:
  ```bash
  docker compose stop db
  curl -i http://localhost:8072/api/health
  ```
  - Show HTTP `503 Service Unavailable` returned by the backend and the UI badge turning red.
  - Now restore the database:
  ```bash
  docker compose start db
  sleep 4
  curl -s http://localhost:8072/api/health
  ```
  - Show immediate recovery with HTTP 200 `{"status":"ok","database":"connected"}`.
- **Concluding sentence**:
  > *"This concludes the demonstration of a robust, production-grade, three-tier course registration system running on Docker Compose at port 8072. Thank you."*
