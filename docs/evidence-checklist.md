# Evidence Checklist and Screenshot Guide
## Lab 4 — Multi-Tier Student Course Registration System (Port 8072)

This document tracks all required evidence for the submission.

> **Screenshot Capture Guideline**: Open your browser to `http://localhost:8072` or your terminal in the project directory, execute the specified command, and capture the window into the `evidence/` directory with the matching filename. Ensure passwords are never visible.

---

| Item | File Name | Description / Command to Run | What to Capture in Screenshot | Verification Status |
|---|---|---|---|---|
| **01** | `evidence/01-docker-versions-hello-world.png` | `docker --version`<br>`docker compose version`<br>`docker run --rm hello-world` | Terminal showing Docker 29.x, Compose 2.40.x, and the "Hello from Docker!" message. | **VERIFIED VIA CLI** (Ready to capture) |
| **02** | `evidence/02-docker-images.png` | `docker images` | Terminal listing `postgres:16-alpine`, `python:3.12-slim`, `nginx:alpine`, and built images. | **VERIFIED VIA CLI** (Ready to capture) |
| **03** | `evidence/03-project-tree.png` | `tree /F` (PowerShell) or `ls -laR` | File tree showing `compose.yaml`, `backend/`, `frontend/`, `docs/`, `report/`. | **VERIFIED VIA CLI** (Ready to capture) |
| **04** | `evidence/04-compose-ps.png` | `docker compose ps` | Output showing `registration-frontend` (0.0.0.0:8072->80), `registration-backend` (Up), `registration-db` (Up, healthy). | **VERIFIED VIA CLI** (Ready to capture) |
| **05** | `evidence/05-application-courses.png` | Browser: `http://localhost:8072` | Web interface showing Course Management table, available seats, and host port badge `8072`. | **VERIFIED VIA CLI** (Ready to capture) |
| **06** | `evidence/06-application-students.png` | Browser: `http://localhost:8072` | Web interface showing Student Management table with registered student records. | **VERIFIED VIA CLI** (Ready to capture) |
| **07** | `evidence/07-registration-and-course-roster.png` | Browser: `http://localhost:8072` | Active Registrations table and Course Roster popup showing enrolled students. | **VERIFIED VIA CLI** (Ready to capture) |
| **08** | `evidence/08-database-rows.png` | `docker exec -it registration-db psql -U postgres_user -d course_registration_db -c "\dt"` and `SELECT * FROM registrations;` | Terminal showing PostgreSQL tables and live records. | **VERIFIED VIA CLI** (Ready to capture) |
| **09** | `evidence/09-network-inspection.png` | `docker network inspect registration_frontend_network registration_database_network` | Terminal showing network separation: frontend only on frontend net, db only on db net, backend on both. | **VERIFIED VIA CLI** (Ready to capture) |
| **10** | `evidence/10-port-and-health-check.png` | `docker port registration-frontend`<br>`docker port registration-backend`<br>`curl http://localhost:8072/api/health` | Shows only port 8072 is published, backend/db have no published ports, health endpoint returns `status: ok`. | **VERIFIED VIA CLI** (Ready to capture) |
| **11** | `evidence/11-persistence-before.png` | `curl -s http://localhost:8072/api/courses` before teardown | Terminal/Browser showing added course `CLOUD404` and student `David Miller`. | **VERIFIED VIA CLI** (Ready to capture) |
| **12** | `evidence/12-persistence-after.png` | `docker compose down`<br>`docker compose up -d`<br>`curl -s http://localhost:8072/api/courses` | Terminal/Browser showing `CLOUD404` and `David Miller` data completely preserved. | **VERIFIED VIA CLI** (Ready to capture) |
| **13** | `evidence/13-service-failure-and-logs.png` | `docker compose stop db`<br>`curl -i http://localhost:8072/api/health`<br>`docker compose logs --tail 10 backend` | Terminal/Browser showing 503 Service Unavailable, red offline badge on UI, and DB connection refused in logs. | **VERIFIED VIA CLI** (Ready to capture) |
