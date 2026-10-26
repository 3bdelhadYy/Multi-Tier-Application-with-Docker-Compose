# Report Outline — Lab 4 Multi-Tier Application
## Student Course Registration System (Docker Compose)

### I. Cover Page & Student Information
- Title: Lab 4 — Multi-Tier Student Course Registration System
- Course: Cloud Computing
- Student Name: `[Your Full Name]`
- Student ID: `[Your Student ID]` (Suffix: `72`)
- Host Port: `8072`

### II. Executive Summary & Objective
- Project objective: Deliver a 3-tier containerized course registration system.
- Chosen technology stack: HTML/CSS/JS (Nginx), Python FastAPI, PostgreSQL 16.
- Comparison with Part 1 (Flask + MySQL -> FastAPI + PostgreSQL).

### III. System Architecture & Network Topology
- High-level architecture diagram (Student hand-drawn or diagramming tool version).
- Network isolation: `frontend-network` vs `database-network`.
- Single ingress point: Only port `8072` published to host.
- Verification commands and outputs.

### IV. Relational Database Design
- Schema specification: `students`, `courses`, `registrations`.
- Constraints: Primary keys, foreign keys with `CASCADE`, unique email, unique course code, composite unique `(student_id, course_id)`.
- Capacity enforcement & concurrency safety using `FOR UPDATE` row-level locks.
- Idempotent seed data design.

### V. Application & REST API Implementation
- FastAPI endpoints, validation with Pydantic v2, and status codes.
- Responsive frontend interface, health monitoring, roster modal, and alerts.
- Nginx reverse-proxy routing rules.

### VI. Docker Configuration & Service Orchestration
- Backend `Dockerfile` details (Python 3.12 slim, non-root best practices).
- `compose.yaml` specification: health checks, dependency conditions, restart policies (`unless-stopped`), named volumes.
- Environment variables and secret hygiene (`.env` vs `.env.example`).

### VII. Verification & Experimental Results
- Automated unit tests with Pytest (8/8 passed).
- Live API functional testing (12 scenarios passed).
- Named volume persistence experiment (`down` then `up`).
- Fault injection and recovery experiment (stopping `db`, observing 503, self-healing).

### VIII. Screenshots and Evidence
- Complete set of 13 screenshots matching `docs/evidence-checklist.md`.

### IX. Conclusion & Learnings
- Container orchestration insights, network security perimeter, ACID persistence in Docker.

### X. Appendix: Key Source Code Excerpts
- `compose.yaml` (passwords omitted)
- `backend/app/routes.py`
- `backend/app/database.py`
- `frontend/nginx.conf`
