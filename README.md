# Student Course Registration System (Multi-Tier Docker Compose)
## Cloud Computing Lab 4 — Part 2 Assignment

[![Docker](https://img.shields.io/badge/Docker-Compose_v2-2496ED?logo=docker&logoColor=white)](https://www.docker.com/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.110.0-009688?logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com/)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-16--alpine-4169E1?logo=postgresql&logoColor=white)](https://www.postgresql.org/)
[![Nginx](https://img.shields.io/badge/Nginx-Alpine-009639?logo=nginx&logoColor=white)](https://nginx.org/)

A production-grade, three-tier containerized web application deployed using **Docker Compose**. The system manages students, courses, seat capacity limits, and course registrations with strict transactional concurrency control and relational integrity.

---

## 1. Architecture & Technology Stack

| Tier | Component | Technology | Role |
|---|---|---|---|
| **Presentation** | `frontend` | HTML5, CSS3, JavaScript ES6, Nginx Alpine | Responsive Single-Page Application (SPA); reverse-proxies `/api/` to backend. |
| **Application** | `backend` | Python 3.12, FastAPI, SQLAlchemy 2.0, Uvicorn | RESTful API, Pydantic validation, business rules, and row-locking concurrency control. |
| **Database** | `db` | PostgreSQL 16 Alpine | Relational schema (`students`, `courses`, `registrations`), ACID guarantees, healthcheck. |

- **Assigned Host Port**: **`8072`** (Student ID Suffix `72` -> `http://localhost:8072`).
- **Network Isolation**: Two private bridge networks (`frontend-network` and `database-network`). Frontend has **zero direct access** to the database. Only the frontend publishes a host port.

---

## 2. Quick Start Guide

### Step 1: Clone or Navigate to the Repository
```bash
cd "/mnt/d/study/year 5/Cloud/AGY_assing"
```

### Step 2: Environment Configuration
A `.env` file is pre-configured. To create or adjust your own local configuration:
```bash
cp .env.example .env
```
*(The `.env` file is excluded from Git to keep secrets safe.)*

### Step 3: Build and Start Containers
```bash
docker compose up -d --build
```
This builds custom backend and frontend images, starts PostgreSQL, waits for it to become healthy, initializes tables, and seeds initial sample records.

### Step 4: Access the Application
Open your web browser and navigate to:
```text
http://localhost:8072
```

---

## 3. Management and Operations

### Check Service Status
```bash
docker compose ps
```
You should see all three containers:
- `registration-frontend`: Up (`0.0.0.0:8072->80/tcp`)
- `registration-backend`: Up (`8000/tcp` internal only)
- `registration-db`: Up (`5432/tcp` internal only, `healthy`)

### View Service Logs
```bash
# All services
docker compose logs -f

# Specific service
docker compose logs -f backend
docker compose logs -f db
docker compose logs -f frontend
```

### Run Automated Backend Unit Tests
```bash
docker run --rm registration-backend:latest pytest -v
```

### Run Live Functional API Tests
```bash
bash docs/test_live.sh
```

### Inspect Database Directly via psql
```bash
docker exec -it registration-db psql -U postgres_user -d course_registration_db -c "\dt"
docker exec -it registration-db psql -U postgres_user -d course_registration_db -c "SELECT * FROM registrations;"
```

---

## 4. Teardown and Data Persistence

### Safe Shutdown (Preserves Data)
```bash
docker compose down
```
> **Note**: This stops and removes containers and networks, but **preserves** the named volume `registration_postgres_data`. When you run `docker compose up -d` again, all courses, students, and registrations will be fully restored.

### Complete Removal (Destructive)
> ⚠️ **Warning**: Deletes all persistent data and database volumes!
```bash
docker compose down -v
```

---

## 5. Documentation Directory

- **`docs/architecture.md`**: Complete system architecture, database schema, concurrency locking design, and network topology.
- **`docs/testing-and-troubleshooting.md`**: Detailed pass/fail test matrix, network isolation proofs, volume persistence experiment, and fault-injection findings.
- **`docs/evidence-checklist.md`**: Numbered checklist and instructions for capturing all 13 required screenshots.
- **`docs/demo-script.md`**: Timed script for the 5-minute live oral demonstration.
- **`docs/progress-log.md`**: Continuous engineering execution log across all implementation phases.
- **`report/lab4-final-report.md`**: Complete assignment report ready for submission.
- **`report/report-outline.md`**: Structural report outline.
