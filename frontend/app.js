// Student Course Registration System - Frontend JavaScript
// All requests are routed through Nginx reverse proxy via relative path /api/

const API_BASE = "/api";

document.addEventListener("DOMContentLoaded", () => {
    // Initial data load and health check
    checkHealth();
    refreshAllData();

    // Event listeners for forms
    document.getElementById("form-add-course").addEventListener("submit", handleAddCourse);
    document.getElementById("form-add-student").addEventListener("submit", handleAddStudent);
    document.getElementById("form-enroll").addEventListener("submit", handleRegisterStudent);

    // Manual database health re-check button
    const btnCheckDb = document.getElementById("btn-check-db");
    if (btnCheckDb) {
        btnCheckDb.addEventListener("click", () => {
            btnCheckDb.textContent = "⏳ Checking...";
            checkHealth().finally(() => {
                setTimeout(() => { btnCheckDb.textContent = "🔄 Check"; }, 800);
            });
        });
    }

    // Modal close listeners
    document.getElementById("modal-close").addEventListener("click", closeModal);
    document.getElementById("modal-close-btn").addEventListener("click", closeModal);

    // Polling health check every 15 seconds
    setInterval(checkHealth, 15000);
});

// ----------------- ALERTS / NOTIFICATIONS -----------------

function showAlert(message, type = "info", section = null) {
    let container = null;

    if (section === "course") {
        container = document.getElementById("course-alert-container");
    } else if (section === "student") {
        container = document.getElementById("student-alert-container");
    } else if (section === "enroll" || section === "registration") {
        container = document.getElementById("enroll-alert-container");
    }

    // Fallback to top-level alert container if section is not specified or container not found
    if (!container) {
        container = document.getElementById("alert-container");
    }

    // Clear previous alert in this section to keep interface clean
    container.innerHTML = "";

    const alert = document.createElement("div");
    alert.className = `alert alert-${type}`;

    const textSpan = document.createElement("span");
    textSpan.textContent = message;

    const closeBtn = document.createElement("button");
    closeBtn.className = "alert-close";
    closeBtn.innerHTML = "&times;";
    closeBtn.onclick = () => alert.remove();

    alert.appendChild(textSpan);
    alert.appendChild(closeBtn);
    container.appendChild(alert);

    // Scroll into view if alert is outside current visible viewport
    alert.scrollIntoView({ behavior: "smooth", block: "nearest" });

    setTimeout(() => {
        if (alert.parentNode) {
            alert.remove();
        }
    }, 7000);
}

// ----------------- HEALTH CHECK & DATABASE STATUS -----------------

async function checkHealth() {
    const dot = document.getElementById("status-dot");
    const statusText = document.getElementById("status-text");
    const dbStat = document.getElementById("stat-db");
    const dbStatSub = document.getElementById("stat-db-sub");

    try {
        const res = await fetch(`${API_BASE}/health?t=${Date.now()}`);
        if (res.ok) {
            const data = await res.json();
            if (dot) dot.className = "status-dot online";
            if (statusText) statusText.textContent = `Online • DB: ${data.database}`;
            if (dbStat) {
                dbStat.innerHTML = `<span class="badge-status online">🟢 Connected</span>`;
            }
            if (dbStatSub) {
                dbStatSub.textContent = `Engine: PostgreSQL 16 • db:5432 (Healthy)`;
                dbStatSub.style.color = "#059669";
            }
        } else {
            throw new Error(`HTTP ${res.status}`);
        }
    } catch (err) {
        if (dot) dot.className = "status-dot offline";
        if (statusText) statusText.textContent = "Offline • Backend unreachable";
        if (dbStat) {
            dbStat.innerHTML = `<span class="badge-status offline">🔴 Disconnected</span>`;
        }
        if (dbStatSub) {
            dbStatSub.textContent = `Database unreachable (${err.message})`;
            dbStatSub.style.color = "#ef4444";
        }
    }
}

// ----------------- DATA REFRESH -----------------

async function refreshAllData() {
    await Promise.all([
        loadCourses(),
        loadStudents(),
        loadRegistrations()
    ]);
}

// ----------------- COURSES -----------------

let cachedCourses = [];

async function loadCourses() {
    try {
        const res = await fetch(`${API_BASE}/courses?t=${Date.now()}`);
        if (!res.ok) throw new Error("Failed to load courses");
        const courses = await res.json();
        cachedCourses = courses;

        // Update stats
        document.getElementById("stat-courses").textContent = courses.length;

        // Render table
        const tbody = document.getElementById("courses-tbody");
        if (courses.length === 0) {
            tbody.innerHTML = `<tr><td colspan="6" class="text-center">No courses found. Add one above!</td></tr>`;
        } else {
            tbody.innerHTML = courses.map(c => `
                <tr>
                    <td><strong>${escapeHtml(c.code)}</strong></td>
                    <td>${escapeHtml(c.title)}</td>
                    <td>${c.seats}</td>
                    <td>${c.enrolled_count}</td>
                    <td>
                        <span class="badge-tag ${c.available_seats === 0 ? 'badge-full' : 'badge-open'}">
                            ${c.available_seats === 0 ? 'FULL (0)' : `${c.available_seats} remaining`}
                        </span>
                    </td>
                    <td>
                        <div class="actions-cell">
                            <button class="btn btn-secondary btn-sm" onclick="viewRoster(${c.id}, '${escapeHtml(c.code)}', '${escapeHtml(c.title)}')">Roster</button>
                            <button class="btn btn-danger btn-sm" onclick="handleDeleteCourse(${c.id}, '${escapeHtml(c.code)}')">Delete</button>
                        </div>
                    </td>
                </tr>
            `).join("");
        }

        // Update enrollment course dropdown
        updateCourseDropdown(courses);
    } catch (err) {
        console.error("Error loading courses:", err);
    }
}

function updateCourseDropdown(courses) {
    const select = document.getElementById("enroll-course");
    const currentVal = select.value;
    select.innerHTML = `<option value="">-- Choose Course --</option>` +
        courses.map(c => `
            <option value="${c.id}" ${c.available_seats === 0 ? 'disabled' : ''}>
                ${escapeHtml(c.code)}: ${escapeHtml(c.title)} (${c.available_seats} seat${c.available_seats === 1 ? '' : 's'} left)
            </option>
        `).join("");
    select.value = currentVal;
}

async function handleAddCourse(e) {
    e.preventDefault();
    const code = document.getElementById("course-code").value.trim();
    const title = document.getElementById("course-title").value.trim();
    const seats = parseInt(document.getElementById("course-seats").value, 10);

    if (!code || !title || isNaN(seats) || seats < 1) {
        showAlert("Please provide valid course details (seats must be at least 1).", "error", "course");
        return;
    }

    try {
        const res = await fetch(`${API_BASE}/courses`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ code, title, seats })
        });

        const data = await res.json();
        if (res.ok) {
            showAlert(`Course '${data.code}' created successfully!`, "success", "course");
            document.getElementById("form-add-course").reset();
            refreshAllData();
        } else {
            showAlert(data.detail || "Failed to create course.", "error", "course");
        }
    } catch (err) {
        showAlert(`Error creating course: ${err.message}`, "error", "course");
    }
}

async function handleDeleteCourse(id, code) {
    if (!confirm(`Are you sure you want to delete course ${code}? All existing registrations for this course will be cancelled.`)) {
        return;
    }

    try {
        const res = await fetch(`${API_BASE}/courses/${id}`, { method: "DELETE" });
        const data = await res.json();
        if (res.ok) {
            showAlert(data.message || `Course ${code} deleted.`, "success", "course");
            refreshAllData();
        } else {
            showAlert(data.detail || "Failed to delete course.", "error", "course");
        }
    } catch (err) {
        showAlert(`Error deleting course: ${err.message}`, "error", "course");
    }
}

// ----------------- STUDENTS -----------------

let cachedStudents = [];

async function loadStudents() {
    try {
        const res = await fetch(`${API_BASE}/students?t=${Date.now()}`);
        if (!res.ok) throw new Error("Failed to load students");
        const students = await res.json();
        cachedStudents = students;

        document.getElementById("stat-students").textContent = students.length;

        const tbody = document.getElementById("students-tbody");
        if (students.length === 0) {
            tbody.innerHTML = `<tr><td colspan="5" class="text-center">No students registered yet.</td></tr>`;
        } else {
            tbody.innerHTML = students.map(s => `
                <tr>
                    <td><strong>#${s.id}</strong></td>
                    <td>${escapeHtml(s.name)}</td>
                    <td>${escapeHtml(s.email)}</td>
                    <td>${formatDate(s.created_at)}</td>
                    <td>
                        <button class="btn btn-danger btn-sm" onclick="handleDeleteStudent(${s.id}, '${escapeHtml(s.name)}')">Delete</button>
                    </td>
                </tr>
            `).join("");
        }

        updateStudentDropdown(students);
    } catch (err) {
        console.error("Error loading students:", err);
    }
}

function updateStudentDropdown(students) {
    const select = document.getElementById("enroll-student");
    const currentVal = select.value;
    select.innerHTML = `<option value="">-- Choose Student --</option>` +
        students.map(s => `
            <option value="${s.id}">${escapeHtml(s.name)} (${escapeHtml(s.email)})</option>
        `).join("");
    select.value = currentVal;
}

async function handleAddStudent(e) {
    e.preventDefault();
    const name = document.getElementById("student-name").value.trim();
    const email = document.getElementById("student-email").value.trim();

    if (!name || !email) {
        showAlert("Please fill in both student name and email.", "error", "student");
        return;
    }

    try {
        const res = await fetch(`${API_BASE}/students`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ name, email })
        });

        const data = await res.json();
        if (res.ok) {
            showAlert(`Student '${data.name}' added successfully!`, "success", "student");
            document.getElementById("form-add-student").reset();
            refreshAllData();
        } else {
            showAlert(data.detail || "Failed to add student.", "error", "student");
        }
    } catch (err) {
        showAlert(`Error adding student: ${err.message}`, "error", "student");
    }
}

async function handleDeleteStudent(id, name) {
    if (!confirm(`Are you sure you want to permanently delete student '${name}'? All course registrations for this student will be removed.`)) {
        return;
    }

    try {
        const res = await fetch(`${API_BASE}/students/${id}`, { method: "DELETE" });
        const data = await res.json();
        if (res.ok) {
            showAlert(data.message || `Student '${name}' deleted successfully.`, "success", "student");
            refreshAllData();
        } else {
            showAlert(data.detail || "Failed to delete student.", "error", "student");
        }
    } catch (err) {
        showAlert(`Error deleting student: ${err.message}`, "error", "student");
    }
}

// ----------------- REGISTRATIONS -----------------

async function loadRegistrations() {
    try {
        const res = await fetch(`${API_BASE}/registrations?t=${Date.now()}`);
        if (!res.ok) throw new Error("Failed to load registrations");
        const registrations = await res.json();

        document.getElementById("stat-registrations").textContent = registrations.length;

        const tbody = document.getElementById("registrations-tbody");
        if (registrations.length === 0) {
            tbody.innerHTML = `<tr><td colspan="5" class="text-center">No active course registrations.</td></tr>`;
        } else {
            tbody.innerHTML = registrations.map(r => `
                <tr>
                    <td>#${r.id}</td>
                    <td><strong>${escapeHtml(r.student_name)}</strong><br><small class="text-muted">${escapeHtml(r.student_email)}</small></td>
                    <td><strong>${escapeHtml(r.course_code)}</strong> &bull; ${escapeHtml(r.course_title)}</td>
                    <td>${formatDate(r.registered_at)}</td>
                    <td>
                        <button class="btn btn-danger btn-sm" onclick="handleCancelRegistration(${r.id})">Cancel</button>
                    </td>
                </tr>
            `).join("");
        }
    } catch (err) {
        console.error("Error loading registrations:", err);
    }
}

async function handleRegisterStudent(e) {
    e.preventDefault();
    const studentId = parseInt(document.getElementById("enroll-student").value, 10);
    const courseId = parseInt(document.getElementById("enroll-course").value, 10);

    if (!studentId || !courseId) {
        showAlert("Please select both a student and a course.", "error", "enroll");
        return;
    }

    try {
        const res = await fetch(`${API_BASE}/registrations`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ student_id: studentId, course_id: courseId })
        });

        const data = await res.json();
        if (res.ok) {
            showAlert(`Registered '${data.student_name}' into '${data.course_code}' successfully!`, "success", "enroll");
            document.getElementById("form-enroll").reset();
            refreshAllData();
        } else {
            showAlert(data.detail || "Registration rejected.", "error", "enroll");
        }
    } catch (err) {
        showAlert(`Registration error: ${err.message}`, "error", "enroll");
    }
}

async function handleCancelRegistration(registrationId) {
    if (!confirm("Are you sure you want to cancel this registration? The seat will be released immediately.")) {
        return;
    }

    try {
        const res = await fetch(`${API_BASE}/registrations/${registrationId}`, {
            method: "DELETE"
        });
        const data = await res.json();
        if (res.ok) {
            showAlert(data.message || "Registration cancelled successfully.", "success", "enroll");
            refreshAllData();
        } else {
            showAlert(data.detail || "Failed to cancel registration.", "error", "enroll");
        }
    } catch (err) {
        showAlert(`Error cancelling registration: ${err.message}`, "error", "enroll");
    }
}

// ----------------- COURSE ROSTER MODAL -----------------

async function viewRoster(courseId, code, title) {
    document.getElementById("modal-roster-title").textContent = `Roster for ${code}: ${title}`;
    const tbody = document.getElementById("roster-tbody");
    tbody.innerHTML = `<tr><td colspan="4" class="text-center">Loading roster...</td></tr>`;
    document.getElementById("roster-modal").classList.remove("hidden");

    try {
        const res = await fetch(`${API_BASE}/courses/${courseId}/students?t=${Date.now()}`);
        if (!res.ok) throw new Error("Failed to load roster");
        const roster = await res.json();

        if (roster.length === 0) {
            tbody.innerHTML = `<tr><td colspan="4" class="text-center">No students registered in this course.</td></tr>`;
        } else {
            tbody.innerHTML = roster.map(item => `
                <tr>
                    <td>#${item.student_id}</td>
                    <td><strong>${escapeHtml(item.name)}</strong></td>
                    <td>${escapeHtml(item.email)}</td>
                    <td>${formatDate(item.registered_at)}</td>
                </tr>
            `).join("");
        }
    } catch (err) {
        tbody.innerHTML = `<tr><td colspan="4" class="text-center" style="color:red">Failed to load roster: ${err.message}</td></tr>`;
    }
}

function closeModal() {
    document.getElementById("roster-modal").classList.add("hidden");
}

// Close modal on background click
window.addEventListener("click", (e) => {
    const modal = document.getElementById("roster-modal");
    if (e.target === modal) {
        closeModal();
    }
});

// ----------------- HELPERS -----------------

function escapeHtml(str) {
    if (!str) return "";
    return str
        .replace(/&/g, "&amp;")
        .replace(/</g, "&lt;")
        .replace(/>/g, "&gt;")
        .replace(/"/g, "&quot;")
        .replace(/'/g, "&#039;");
}

function formatDate(isoStr) {
    if (!isoStr) return "-";
    try {
        const d = new Date(isoStr);
        return d.toLocaleDateString() + " " + d.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
    } catch {
        return isoStr;
    }
}
