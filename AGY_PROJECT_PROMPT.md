# Agy CLI Master Prompt — Cloud Computing Lab 4
## Student Course Registration System (Docker Compose)

> **Instructions for Agy:** Read this entire prompt before making changes. Treat the assignment PDF as the source of truth, especially Part 2 on pages 17–19. Work in the user's actual project workspace, inspect the existing environment and files first, and implement the project incrementally. Do not merely provide advice or code snippets: create the working project files, run the checks that are available, fix problems, and leave the project ready for the student to inspect, document, and demo.

---

## 1. Your role and working style

Act as a careful senior software engineer and teaching assistant helping complete an individual Cloud Computing assignment.

Follow these working rules:

1. **Execute autonomously from start to finish. Do not stop to ask the user for confirmation or wait for a reply between phases.** Run the phases sequentially in one continuous work session. At the end of each phase, run relevant checks, inspect the actual results, fix any issues you can, and then automatically continue to the next phase.
2. **Checkpoint means self-verification, not a pause for the user.** Verify each checkpoint yourself and record its status in a progress log (for example, `docs/progress-log.md`). Do not ask the user to approve a checkpoint or provide output unless an essential blocker genuinely cannot be resolved without user input.
3. **Handle nonessential uncertainty with safe defaults.** If a detail is unspecified, choose a reasonable, reversible default consistent with the assignment, document the choice, and continue. Ask the user only if proceeding would require a destructive action, incur a cost, expose a secret, or depend on an essential piece of information that cannot safely be inferred.
4. **Work in phases and checkpoints.** Use the phase plan below. At the end of each phase, run relevant checks and report what passed, what failed, and what remains. Do not mark a check as passed unless you actually verified it.
2. **Inspect before editing.** Identify the current working directory, operating system, Docker/Compose status, and existing files. Preserve unrelated files. If a project already exists, inspect it before changing anything.
3. **Use the real environment.** The target environment is Ubuntu on WSL2 in Windows. Docker Engine and Docker Compose are believed to be installed and working, but verify them. Do not reinstall Docker unnecessarily.
4. **Do not fabricate evidence.** Never invent command output, screenshots, successful tests, database records, or a running deployment. If you cannot run a command or capture a screenshot, state that clearly and give the student exact steps to do it.
5. **Avoid destructive actions.** Do not run `docker compose down -v`, delete volumes, remove user files, overwrite unrelated files, or perform irreversible cleanup without explicit permission. A normal `docker compose down` is allowed when needed for the persistence test, provided the named volume is preserved.
6. **Keep secrets safe.** Put credentials in `.env`; include `.env` in `.gitignore`; create a safe `.env.example` with placeholder values. Never put real passwords in source code, reports, screenshots, or Git.
7. **Make the implementation understandable.** Use clear names, comments where helpful, a concise README, and documented commands. Do not overengineer the application.
8. **Do not silently skip requirements.** Maintain a requirement-to-file/test/evidence checklist and explicitly report any uncompleted requirement.
9. **The assignment is individual.** Produce an implementation the student can understand, test, explain, and demonstrate. Do not fabricate a claim that the student personally performed an action.
10. **Do not stop after writing files.** Run syntax/configuration checks and, where Docker is available, build and test the actual deployment. Diagnose errors and fix them before declaring completion.

## 2. Assignment source and purpose

The source is the provided PDF `4_5951944500313071685.pdf`, titled **Lab 4 — Deploying a Multi-Tier Application with Docker Compose**.

The requested work is **Part 2 — Assignment: Student Course Registration System**, described on PDF pages 17–19 (sections 19.1–19.6). Follow that assignment's terminology and requirements. The original lab's architecture and learning goals are useful context, but this project must implement the new Student Course Registration System.

The assignment is an individual task. Submission is due one week after the lab (the exact date is not filled in on the PDF).

### Required application features

The application must provide:

- **Courses:** add, list, and delete courses. Each course has a course code, title, and number of seats.
- **Students:** add and list students. Each student has a name and email.
- **Registration:** register a student in a course, cancel a registration, and list the students registered in each course.
- **Business rules:**
  - A student cannot register twice in the same course.
  - A course cannot accept more registrations than its seat capacity.
  - Student emails must be unique.
  - Course codes must be unique.
- **Database:** at least three related tables named or equivalent to `students`, `courses`, and `registrations`, with foreign keys and sample data.

### Technology constraint

The stack must differ from the original lab in at least one tier. The original lab uses HTML/JavaScript + Nginx, Python Flask, and MySQL 8.4. Use the following preferred stack:

- **Frontend:** plain HTML, CSS, and JavaScript, served by Nginx.
- **Backend:** Python FastAPI.
- **Database:** PostgreSQL.

This changes the backend and database while keeping a simple Nginx frontend. Do not change the stack without a compelling compatibility issue; if a change is necessary, explain it first.

## 3. Fixed environment and individual port

- **Host environment:** Windows with Ubuntu running under WSL2.
- **Docker Engine and Docker Compose:** reported as installed and working; verify rather than reinstall.
- **Student ID suffix:** `72`.
- **Required host port:** **8072**.
- **Expected URL:** `http://localhost:8072`.

The frontend port mapping must be equivalent to:

```yaml
ports:
  - "8072:80"
```

Only the frontend may publish a host port. Do **not** publish the backend API or PostgreSQL port to the host.

## 4. Required architecture

Deploy the three core services with one `compose.yaml`:

1. `frontend`: Nginx serves the static web interface and reverse-proxies `/api/` requests to the backend.
2. `backend`: FastAPI implements the REST API, validation, business rules, and database access.
3. `db`: PostgreSQL stores the relational data.

### Networking requirements

Create at least two private Docker networks:

- `frontend-network`: connect `frontend` and `backend`.
- `database-network`: connect `backend` and `db`.

The frontend must **not** be attached to `database-network`; therefore, it must not be able to reach the database directly. The backend is the only application service connected to both networks.

Nginx must proxy `/api/` to the backend using the Compose service name and internal port. The browser should call same-origin paths such as `/api/courses`; it must not connect directly to the backend or database.

### Persistence and service reliability

- Use a named Docker volume for PostgreSQL's data directory.
- Add a PostgreSQL health check.
- Configure a restart policy on **all three services**.
- Configure the backend to wait for the database to become healthy, not merely for its container to start. The backend should also handle transient database readiness safely.
- Use environment variables for database configuration.
- Normal `docker compose down` must preserve data. `docker compose down -v` would delete the named volume and must not be used during ordinary testing or cleanup.

## 5. Database design and correctness

Implement at least these related tables:

### `students`
- Primary key.
- `name`, required and nonblank.
- `email`, required and unique.

### `courses`
- Primary key.
- `code`, required and unique.
- `title`, required and nonblank.
- `seats`, required and greater than or equal to zero (preferably positive unless the assignment's interpretation requires zero-seat courses).

### `registrations`
- Primary key, or a composite primary key.
- Foreign key to `students`.
- Foreign key to `courses`.
- Registration timestamp, if useful.
- Unique constraint across `(student_id, course_id)` to prevent duplicate registrations at the database level.

Use appropriate indexes and constraints. Seed sample data idempotently so restarting the application does not create duplicates. Include at least **three courses and two students** and enough valid sample data to demonstrate registration, capacity limits, and cancellation.

### Capacity and transaction safety

Enforce the course seat limit in the backend and database transaction flow. The capacity check must be safe under concurrent registration attempts: two requests must not be able to claim the last seat simultaneously. Use a suitable transaction/locking strategy (for example, lock the relevant course row while checking the current registration count and inserting). Handle duplicate registration, full course, unknown student, and unknown course with clear HTTP errors. Do not rely on frontend validation alone.

Use proper parameterized database operations or an appropriate ORM. Never construct SQL by concatenating user input.

## 6. Expected application/API behavior

Implement a coherent REST API. Exact endpoint naming may be chosen sensibly, but document it and use it consistently. A suitable baseline is:

- `GET /api/health` — reports API health and database connectivity.
- `GET /api/courses` — list courses, ideally including current enrollment count and available seats.
- `POST /api/courses` — add a course.
- `DELETE /api/courses/{id}` — delete a course safely; handle existing registrations predictably and document the policy.
- `GET /api/students` — list students.
- `POST /api/students` — add a student.
- `GET /api/courses/{id}/students` — list students registered in a specific course.
- `POST /api/registrations` — register a student in a course.
- `DELETE /api/registrations/{id}` or an equally clear route — cancel a registration.

Use appropriate HTTP status codes, validation, and readable error messages. Keep the API simple enough for the student to explain in a five-minute demo.

### Frontend behavior

Create a usable and reasonably polished interface with separate, clearly labeled areas for:

- Course management: add, list, and delete courses.
- Student management: add and list students.
- Registration: select a student and course, register them, cancel a registration, and view each course's registered students.
- Status and error messages: show success, validation, duplicate, and full-course errors clearly.
- Current enrollment and remaining seats should be visible if practical.

The UI must use the backend API; do not hard-code a fake interface or rely only on static sample records. The sample data must actually be stored in PostgreSQL. Ensure all API calls work through Nginx's `/api/` reverse proxy.

## 7. Project structure

Create a clear, maintainable structure similar to:

```text
student-course-registration/
├── compose.yaml
├── .env                  # local secrets; never commit
├── .env.example          # placeholders only
├── .gitignore
├── README.md
├── backend/
│   ├── Dockerfile
│   ├── requirements.txt
│   ├── app/               # FastAPI app, database access, schemas/routes
│   └── tests/
├── frontend/
│   ├── index.html
│   ├── styles.css
│   ├── app.js
│   └── nginx.conf
├── docs/
│   ├── architecture.md
│   ├── testing-and-troubleshooting.md
│   └── evidence-checklist.md
└── report/
    └── report-outline.md
```

You may adapt the exact backend substructure if there is a good reason, but keep it clear and avoid unnecessary complexity. Do not put passwords in `README.md`, source files, or report content.

## 8. Work plan — phases and checkpoints

Follow this phase order and record the status of every checkpoint. Execute all phases sequentially in one continuous session: verify each checkpoint, fix issues where possible, record results, and proceed automatically. Do not pause for the user between phases.

### Phase 1 — Environment and project setup
1. Inspect the current directory and existing files before creating anything.
2. Verify the Ubuntu/WSL environment.
3. Verify `docker --version`, `docker compose version`, Docker daemon connectivity, and `docker run --rm hello-world`.
4. Pull the required base images that will be used: Nginx, a Python image suitable for the backend, and PostgreSQL. Choose and document stable appropriate tags.
5. Create the project directory and file structure.
6. Set host port `8072`.
7. Create `.gitignore`, `.env.example`, and a local `.env` only if needed. Ensure `.env` is ignored by Git.
8. Capture or clearly instruct the student to capture genuine evidence for Task 1.

**Checkpoint:** environment verified, project structure exists, required images are present, and the host port is confirmed. Record the check results, resolve issues if possible, and then continue automatically to Phase 2 without waiting for user input.

### Phase 2 — Database and API design
1. Design the three related tables and constraints.
2. Define API endpoints and expected status codes.
3. Decide deletion behavior when a course has registrations.
4. Define capacity-safe registration transaction logic.
5. Create tests for business rules before or alongside implementation.

**Checkpoint:** schema, API contract, and test plan are documented.

### Phase 3 — Implement the backend
1. Implement FastAPI application, database connection management, schema initialization/migrations, and seed data.
2. Implement all required endpoints.
3. Enforce unique email/course code, duplicate registration prevention, capacity limits, foreign keys, and validation.
4. Implement health checking and useful logs.
5. Add automated tests for success cases and error cases.

**Checkpoint:** backend syntax/tests pass as far as the environment allows, and all endpoints are documented.

### Phase 4 — Implement the frontend
1. Create the actual HTML/CSS/JavaScript interface.
2. Implement all course, student, and registration operations.
3. Display server-side validation errors and success states.
4. Configure Nginx to serve static files and reverse-proxy `/api/` to FastAPI.
5. Verify frontend API paths are same-origin and do not expose internal service ports.

**Checkpoint:** frontend code is present and the API proxy configuration is checked.

### Phase 5 — Docker Compose deployment
1. Create the backend Dockerfile.
2. Create `compose.yaml` with the three core services.
3. Configure the named database volume, two private networks, environment variables, health check, dependency health condition, and restart policies.
4. Publish only host port `8072` from Nginx.
5. Ensure `.env` is not committed and no password is hard-coded in application code.
6. Validate the Compose configuration.
7. Build and start the services.
8. Inspect service status and logs; fix issues before proceeding.

**Checkpoint:** all three services run; database becomes healthy; application is reachable at `http://localhost:8072`.

### Phase 6 — Functional and infrastructure tests
Test and record the actual results for every case:

- Add/list/delete a course.
- Add/list a student.
- Register a student in a course.
- List the students registered in a course.
- Cancel a registration and verify the seat becomes available.
- Attempt duplicate student email — rejected.
- Attempt duplicate course code — rejected.
- Attempt duplicate registration — rejected.
- Fill a course and attempt one more registration — rejected without exceeding capacity.
- Try invalid or missing fields — rejected with clear feedback.
- Verify health endpoint and database connectivity.
- Verify only the frontend publishes a host port.
- Inspect both networks and verify frontend cannot directly reach the database.
- Verify named volume exists.
- Run `docker compose down` and then `docker compose up -d`; verify sample and user-created data persist.
- Stop one tier intentionally, document visible symptoms and relevant logs, then restore it.
- Verify restart behavior. Be precise about the distinction between a manually stopped container and a container killed unexpectedly; do not claim a restart policy restarts manually stopped services.
- Run `docker compose ps` and collect logs for each service.

Do not run `docker compose down -v` as part of normal persistence testing.

**Checkpoint:** test matrix includes pass/fail and evidence for every required behavior. Fix failures before preparing the report.

### Phase 7 — Documentation, evidence, and demo
1. Create an architecture diagram that the student can review and redraw/claim as their own work. A Mermaid source diagram may be supplied as a draft, but the assignment requests a diagram drawn by the student; clearly tell the student to review and produce their own final diagram.
2. Prepare a report outline and, if requested, a complete report based only on verified implementation details and real test results.
3. Organize screenshots with filenames and one-line captions.
4. Ensure screenshots show the required port `8072` and do not reveal passwords.
5. Prepare a short networking/volume/troubleshooting explanation (about one page).
6. Prepare a five-minute demo script.
7. Produce a final requirement-to-evidence checklist.
8. Provide exact commands to start, inspect, and stop the project safely.

**Checkpoint:** submission items are present or clearly marked for the student to complete, and the demo can be followed from a clean start.

## 9. Required assignment tasks and evidence mapping

The assignment PDF section 19.3 lists these tasks. Make sure every one is addressed.

| Assignment task | Required work | Evidence to capture |
|---|---|---|
| 1. Environment | Install/verify Docker and Compose, run `hello-world`, pull images, explain image vs container | Version output and `docker images` |
| 2. Build application | Own backend Dockerfile, frontend, and database configuration | Project tree, Dockerfile, application code |
| 3. Deploy with Compose | Three services in one Compose file; `.env`; DB health check; restart policy on all services | `compose.yaml` and `docker compose ps` |
| 4. Networking | At least two networks; frontend cannot reach DB; only frontend publishes port; Nginx proxies `/api/` | Network inspection, port configuration, explanation of service discovery |
| 5. Persistence | At least three courses and two students; register students; `down` then `up`; data remains | Before/after screenshots and volume explanation |
| 6. Monitoring/troubleshooting | Show `ps` and logs; deliberately stop one tier, diagnose and fix | Logs and short write-up |
| 7. Individual change | Host port equals 8000 plus the last two student-ID digits | Screenshot showing app on port **8072** |

### Deliverables required by section 19.5

- Architecture diagram drawn by the student, showing containers, networks, volume, and ports.
- Project structure and full contents of `compose.yaml`, Dockerfile(s), and main application code, with passwords removed.
- Screenshots of the running application and required command outputs.
- Persistence evidence before and after `down`/`up`.
- About one page explaining networking, volumes, and troubleshooting.
- A live demo of about five minutes: start the project, use the application, show database contents, and stop one tier to demonstrate the result.
- Report as PDF or Word.
- Project folder as ZIP or a Git link.

## 10. Bonus options — only after all core requirements pass

The assignment offers up to 10 bonus marks:

- **Admin tool (+3):** Add Adminer or phpMyAdmin as a fourth service, published only on `127.0.0.1` so it cannot be reached from other machines. Prefer Adminer for PostgreSQL. Do not expose it on `0.0.0.0`.
- **Cache (+3):** Add Redis in its own container and cache one API response. Demonstrate the effect rather than merely adding the service.
- **Cloud (+4):** Deploy the same project on one AWS EC2 Ubuntu instance, install Docker, copy the project, open only the required port in the security group, and provide the public URL and screenshots.

Do **not** begin bonus work until all core requirements are implemented, tested, and documented. Do not incur cloud charges or create cloud resources without asking the student first.

## 11. Marking scheme — prioritize effort accordingly

The assignment's section 19.6 gives:

| Component | Marks |
|---|---:|
| Docker installation and verification | 10 |
| Correct application configuration (Dockerfile, Compose, `.env`) | 20 |
| Successful deployment of all tiers and application features | 20 |
| Networking explanation and inspection | 15 |
| Database persistence test | 15 |
| Monitoring and troubleshooting | 10 |
| Report quality and evidence | 10 |
| **Total** | **100** |
| Bonus | **+10** |

Prioritize the required 100 marks before bonus features.

## 12. Evidence and screenshot policy

Create `docs/evidence-checklist.md` with one entry for every required screenshot or evidence item. Suggested organization:

- `evidence/01-docker-versions-hello-world.png`
- `evidence/02-docker-images.png`
- `evidence/03-project-tree.png`
- `evidence/04-compose-ps.png`
- `evidence/05-application-courses.png`
- `evidence/06-application-students.png`
- `evidence/07-registration-and-course-roster.png`
- `evidence/08-database-rows.png`
- `evidence/09-network-inspection.png`
- `evidence/10-port-and-health-check.png`
- `evidence/11-persistence-before.png`
- `evidence/12-persistence-after.png`
- `evidence/13-service-failure-and-logs.png`

These are suggested filenames, not permission to fabricate files. Only mark an item captured when the real screenshot exists. If you cannot capture a GUI screenshot from your execution environment, tell the student exactly what to display and capture manually. Do not use generated mock terminal images as evidence.

## 13. Report requirements

Create a report outline that follows the assignment's deliverables. It should include:

1. Title and student/course information (leave unknown fields as placeholders; do not invent them).
2. Objective and chosen technology stack.
3. Architecture diagram.
4. Project structure.
5. Database schema and relationships.
6. Explanation of API and application features.
7. Dockerfile and Compose configuration explanation.
8. Networking, reverse proxy, host port `8072`, and isolation.
9. Environment variables and secret handling (do not print actual secrets).
10. Testing results with real outputs/screenshots.
11. Persistence experiment.
12. Monitoring and troubleshooting experiment.
13. Conclusion.
14. Appendix with key configuration/code excerpts, with secrets removed.

The report must accurately distinguish between tests actually run and tests the student still needs to perform. Avoid claiming that the student drew a diagram or performed a demo if that has not happened.

## 14. Five-minute live demo plan

Prepare a concise script, timed approximately as follows:

- **0:00–0:40:** Show architecture and `docker compose ps`; identify the three services.
- **0:40–1:50:** Open `http://localhost:8072`; add/list a course and student.
- **1:50–2:40:** Register a student, show the course roster, and demonstrate duplicate/capacity validation.
- **2:40–3:20:** Show PostgreSQL records and explain the three related tables.
- **3:20–4:10:** Explain the two networks and show that only Nginx publishes a host port.
- **4:10–4:40:** Show persistence after `down`/`up`, using real prior evidence if needed.
- **4:40–5:00:** Stop one service briefly, show the symptom/logs, restore it, and conclude.

Adapt timing to the actual demo; do not claim a step was demonstrated if it was not.

## 15. Final response expected from you

At the end of your work, report:

1. **What you created:** key files and their purpose.
2. **What you ran:** exact commands and actual outcomes.
3. **Verification summary:** each requirement marked `PASS`, `FAIL`, or `NOT YET VERIFIED`, with evidence.
4. **How to run it:** exact commands from the project directory.
5. **How to test it:** core feature and infrastructure tests.
6. **Evidence still needed:** genuine screenshots and any manual actions.
7. **Known limitations:** honest and specific.
8. **Next steps:** the smallest set of actions for the student to finish.

Do not state “complete” if a required task remains unverified.

---

## 16. Autonomous execution requirement — critical

The user explicitly wants you to complete the project **without coming back to them between phases**.

- Do not end your response after a plan, setup, or an intermediate checkpoint.
- Do not ask “Should I continue?”, “May I proceed?”, or ask the user to paste command output when you can inspect/run the command yourself.
- Execute Phase 1, verify it, then proceed directly through Phases 2–7.
- After each phase, run its checks, inspect their actual results, fix failures where feasible, update `docs/progress-log.md`, and continue automatically.
- If one test is blocked, record the limitation and continue with independent tasks rather than abandoning the entire project.
- Use safe, reversible defaults for nonessential choices. Do not perform destructive cleanup, expose secrets, or create billable cloud resources without explicit permission.
- At the end, give one consolidated report with completed work, actual test outcomes, files created, run instructions, any genuine blockers, and tasks that still require the student's physical participation (such as taking real screenshots or delivering the live demo).
- You must never fabricate test results or claim to have captured screenshots or performed a live demo if you did not.

## Start now

Begin with **Phase 1, Checkpoint 1**:

- Inspect the current working directory and existing files.
- Verify the Ubuntu/WSL version.
- Verify Docker Engine, Compose, daemon access, and `hello-world`.
- Pull the intended base images only after checking what is already present.
- Confirm host port `8072` is available or report if it is occupied.
- Create the project directory and initial structure without deleting unrelated files.
- Create `.gitignore` and safe environment templates.
- Report the real output/status of each check.

Then continue phase by phase, verifying each checkpoint before proceeding. **Do not stop after Phase 1, do not ask the user to say 'continue', and do not wait for approval between phases.** Complete all phases from setup through implementation, deployment, testing, documentation, and final report preparation in one continuous run. At each checkpoint, verify results yourself, fix what you can, write the result to the progress log, and continue. If a command or feature cannot be verified, label it honestly as `NOT VERIFIED` and continue with other work. Pause only for a genuine blocker that cannot be resolved safely without user input, or for an action that would be destructive, expose secrets, or incur external costs. Do not simply print this plan back to the user; carry out the work in the available workspace.
