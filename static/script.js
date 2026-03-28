/* Student Module Client Script */

function go(path) {
    window.location.href = path;
}

/* ================= AUTH ================= */

function logout() {
    localStorage.removeItem("token");
    localStorage.removeItem("user_email");
    localStorage.removeItem("role_id");
    localStorage.removeItem("role_name");
    window.location.href = "/";
}

function setUser() {
    const email = localStorage.getItem("user_email");
    if (document.getElementById("userEmail")) {
        document.getElementById("userEmail").innerText = email;
    }
}

/* ================= REGISTER ================= */
function register() {
    const name = document.getElementById("name").value.trim();
    const email = document.getElementById("email").value.trim();
    const password = document.getElementById("password").value;
    const role = document.getElementById("role").value;
    const department = (document.getElementById("department")?.value || "").trim();
    const selectedRole = document.getElementById("role")?.selectedOptions?.[0];
    const roleName = (selectedRole?.dataset.roleName || "").toLowerCase();
    const message = document.getElementById("message");

    message.innerText = "Creating account...";

    if (!name || !email || !password || !role) {
        message.innerText = "Name, email, password, and role are required.";
        return;
    }

    if (roleName === "student" && !department) {
        message.innerText = "Department is required for student registration.";
        return;
    }

    fetch("/auth/register", {
        method: "POST",
        headers: {
            "Content-Type": "application/json"
        },
        body: JSON.stringify({
            name,
            email,
            password,
            role_id: parseInt(role, 10),
            department
        })
    })
    .then(res => res.json())
    .then(data => {
        console.log("Register response:", data);
        if (data.message || data.success) {
            message.innerText = data.message || "Account created successfully.";
            setTimeout(() => {
                window.location.href = "/";
            }, 1500);
        } else {
            message.innerText = data.error || data.message || "Registration failed.";
        }
    })
    .catch((error) => {
        console.error(error);
        message.innerText = error.message || "Registration failed.";
    });
}

/* ================= LOGIN ================= */

function login() {
    const email = document.getElementById("email").value.trim();
    const password = document.getElementById("password").value;
    const message = document.getElementById("message");

    message.innerText = "Logging in...";

    fetch("/auth/login", {
        method: "POST",
        headers: {"Content-Type": "application/json"},
        body: JSON.stringify({ email, password })
    })
    .then(res => res.json())
    .then(data => {
        console.log("Login response:", data);
        if (data.token && data.user) {
            localStorage.setItem("token", data.token);
            localStorage.setItem("user_email", data.user.email);
            localStorage.setItem("role_id", data.user.role_id);
            localStorage.setItem("role_name", data.user.role_name || "");
            window.location.href = data.user.dashboard_path || "/";
        } else {
            message.innerText = data.error || data.message || "Login failed.";
        }
    })
    .catch((error) => {
        console.error(error);
        message.innerText = error.message || "Login failed.";
    });
}
/* ================= DASHBOARD ================= */

async function loadDashboard() {
    setUser();

    const token = localStorage.getItem("token");

    try {
        const res = await fetch("/student/dashboard", {
            headers: { "Authorization": "Bearer " + token }
        });

        const data = await res.json();
        console.log("Dashboard:", data);

        document.getElementById("readinessScore").innerText =
            data.readiness_score + "%";

        const progress = document.getElementById("progressFill");
        progress.style.width = data.readiness_score + "%";

        // Dynamic color
        if (data.readiness_score >= 80) progress.style.background = "#16a34a";
        else if (data.readiness_score >= 60) progress.style.background = "#eab308";
        else progress.style.background = "#dc2626";

        document.getElementById("status").innerText = data.status;
        document.getElementById("risk").innerText = data.risk_level;

        document.getElementById("placement").innerText =
            data.placement_status || "Not Available";

        renderChart(data);
        renderInsights(data);
        loadLeaderboard();

    } catch (e) {
        console.error(e);
    }
}

/* ================= PROGRESS PAGE ================= */

async function loadProgress() {
    setUser();

    const token = localStorage.getItem("token");

    try {
        const res = await fetch("/student/dashboard", {
            headers: { "Authorization": "Bearer " + token }
        });

        const data = await res.json();

        document.getElementById("attendance").innerText = data.attendance + "%";
        document.getElementById("marks").innerText = data.marks;
        document.getElementById("mock").innerText = data.mock_score;
        document.getElementById("skills").innerText = data.skills_score;

        renderChart(data);

    } catch (e) {
        console.error(e);
    }
}

/* ================= SKILLS ================= */

async function loadSkills() {
    setUser();

    const token = localStorage.getItem("token");

    try {
        const res = await fetch("/student/skills", {
            headers: { "Authorization": "Bearer " + token }
        });

        const data = await res.json();

        const list = document.getElementById("skillsList");
        list.innerHTML = "";

        data.forEach(skill => {
            const li = document.createElement("li");
            li.innerText = "✅ " + skill.skill_name;
            list.appendChild(li);
        });

    } catch (e) {
        console.error(e);
    }
}

async function addSkill() {
    const skill = document.getElementById("skillInput").value;
    const token = localStorage.getItem("token");

    if (!skill) return alert("Enter skill!");

    await fetch("/student/skills", {
        method: "POST",
        headers: {
            "Content-Type": "application/json",
            "Authorization": "Bearer " + token
        },
        body: JSON.stringify({ skill_name: skill })
    });

    document.getElementById("skillInput").value = "";
    loadSkills();
}

/* ================= LEADERBOARD ================= */

function loadLeaderboard() {
    const token = localStorage.getItem("token");

    fetch("/top-students", {
        headers: { "Authorization": "Bearer " + token }
    })
    .then(res => res.json())
    .then(data => {
        const list = document.getElementById("topStudents");
        if (!list) return;

        list.innerHTML = "";

        data.forEach((student, i) => {
            const medal = ["🥇","🥈","🥉"][i] || "";

            const li = document.createElement("li");
            li.innerHTML = `
                <div class="leaderboard-item">
                    <span>${medal} ${student.name}</span>
                    <span>${student.final_score || "--"}</span>
                </div>
            `;
            list.appendChild(li);
        });
    });
}

/* ================= CHART ================= */

function renderChart(data) {
    const ctx = document.getElementById("performanceChart");
    if (!ctx) return;

    if (window.myChart) window.myChart.destroy();

    window.myChart = new Chart(ctx, {
        type: "bar",
        data: {
            labels: ["Attendance", "Marks", "Mock", "Skills"],
            datasets: [{
                data: [
                    data.attendance,
                    data.marks,
                    data.mock_score,
                    data.skills_score * 10
                ]
            }]
        },
        options: {
            plugins: { legend: { display: false } }
        }
    });
}

/* ================= INSIGHTS ================= */

function renderInsights(data) {
    const list = document.getElementById("insightsList");
    if (!list) return;

    list.innerHTML = [];

    const insights = [];

    if (data.attendance < 75) insights.push("⚠ Improve attendance");
    else insights.push("✅ Good attendance");

    if (data.marks < 60) insights.push("📉 Improve marks");
    else insights.push("💪 Strong marks");

    if (data.mock_score < 60) insights.push("📊 Practice mocks");
    else insights.push("🚀 Good mock performance");

    insights.forEach(text => {
        const li = document.createElement("li");
        li.innerText = text;
        list.appendChild(li);
    });
}

/* ================= THEME ================= */

function toggleTheme() {
    document.body.classList.toggle("dark");
    localStorage.setItem("theme",
        document.body.classList.contains("dark") ? "dark" : "light"
    );
}

(function () {
    if (localStorage.getItem("theme") === "dark") {
        document.body.classList.add("dark");
    }
})();

/* ================= STUDENT MODULE OVERRIDES ================= */

function logout() {
    localStorage.removeItem("token");
    localStorage.removeItem("user_email");
    localStorage.removeItem("role_id");
    localStorage.removeItem("role_name");
    window.location.href = "/";
}

function setUser() {
    const email = localStorage.getItem("user_email");
    const emailNode = document.getElementById("userEmail");

    if (emailNode) {
        emailNode.innerText = email || "Student";
    }
}

function getSelectedRoleOption() {
    const roleSelect = document.getElementById("role");
    return roleSelect ? roleSelect.options[roleSelect.selectedIndex] : null;
}

function toggleDepartmentField() {
    const departmentField = document.getElementById("departmentField");
    const departmentInput = document.getElementById("department");
    const selectedRole = getSelectedRoleOption();
    const isStudent = (selectedRole?.dataset.roleName || "").toLowerCase() === "student";

    if (departmentField) {
        departmentField.hidden = !isStudent;
    }

    if (departmentInput) {
        if (isStudent) {
            departmentInput.placeholder = "Enter Department";
        } else {
            departmentInput.value = "";
        }
    }
}

async function loadRegistrationForm() {
    const roleSelect = document.getElementById("role");
    if (!roleSelect) {
        return;
    }

    const message = document.getElementById("message");

    try {
        const roles = await fetchJson("/auth/roles");
        roleSelect.innerHTML = "";

        roles.forEach((role) => {
            const option = document.createElement("option");
            option.value = role.id;
            option.dataset.roleName = role.name;
            option.dataset.dashboardPath = role.dashboard_path || "/";
            option.innerText = role.name;
            roleSelect.appendChild(option);
        });

        roleSelect.removeEventListener("change", toggleDepartmentField);
        roleSelect.addEventListener("change", toggleDepartmentField);
        toggleDepartmentField();
    } catch (error) {
        console.error(error);
        if (message) {
            message.innerText = error.message || "Unable to load registration roles.";
        }
    }
}

async function fetchJson(path, options = {}) {
    const token = localStorage.getItem("token");
    const headers = { ...(options.headers || {}) };

    if (token) {
        headers.Authorization = "Bearer " + token;
    }

    const response = await fetch(path, {
        ...options,
        headers,
    });

    const data = await response.json().catch(() => ({}));
    console.log("API response:", {
        path,
        status: response.status,
        ok: response.ok,
        data,
    });

    if (!response.ok) {
        throw new Error(data.error || data.message || "Request failed");
    }

    return data;
}

function formatValue(value) {
    const numericValue = Number(value || 0);
    return Number.isInteger(numericValue)
        ? String(numericValue)
        : numericValue.toFixed(2).replace(/\.00$/, "");
}

function formatPercent(value) {
    return formatValue(value) + "%";
}

function setText(id, value) {
    const node = document.getElementById(id);
    if (node) {
        node.innerText = value;
    }
}

function setHtml(id, value) {
    const node = document.getElementById(id);
    if (node) {
        node.innerHTML = value;
    }
}

function getMetricMeta(data) {
    return [
        {
            label: "Attendance",
            value: Number(data.attendance || 0),
            cardId: "attendanceCard",
            noteId: "attendanceNote",
        },
        {
            label: "Marks",
            value: Number(data.marks || 0),
            cardId: "marksCard",
            noteId: "marksNote",
        },
        {
            label: "Mock Tests",
            value: Number(data.mock_score || 0),
            cardId: "mockCard",
            noteId: "mockNote",
        },
        {
            label: "Skills",
            value: Number(data.skills_score || 0),
            cardId: "skillsCard",
            noteId: "skillsNote",
        },
    ];
}

function getMetricExtremes(data) {
    const metrics = getMetricMeta(data);
    const best = metrics.reduce((top, metric) => (metric.value > top.value ? metric : top), metrics[0]);
    const worst = metrics.reduce((low, metric) => (metric.value < low.value ? metric : low), metrics[0]);
    return { best, worst };
}

function applyKpiColor(node, type) {
    if (!node) {
        return;
    }

    node.classList.remove("green", "yellow", "red");

    if (type === "success") {
        node.classList.add("green");
    } else if (type === "warning") {
        node.classList.add("yellow");
    } else if (type === "danger") {
        node.classList.add("red");
    }
}

function getReadinessColor(score) {
    if (score >= 80) {
        return "#16a34a";
    }
    if (score >= 60) {
        return "#eab308";
    }
    return "#dc2626";
}

function renderChart(data) {
    const ctx = document.getElementById("performanceChart");
    if (!ctx || typeof Chart === "undefined") {
        return;
    }

    if (window.myChart) {
        window.myChart.destroy();
    }

    window.myChart = new Chart(ctx, {
        type: "bar",
        data: {
            labels: ["Attendance", "Marks", "Mock Tests", "Skills"],
            datasets: [{
                data: [
                    Number(data.attendance || 0),
                    Number(data.marks || 0),
                    Number(data.mock_score || 0),
                    Number(data.skills_score || 0),
                ],
                backgroundColor: ["#4f46e5", "#06b6d4", "#eab308", "#16a34a"],
                borderRadius: 8,
            }]
        },
        options: {
            responsive: true,
            plugins: {
                legend: { display: false }
            },
            scales: {
                y: {
                    beginAtZero: true,
                    max: 100
                }
            }
        }
    });
}

function renderInsights(insights) {
    const list = document.getElementById("insightsList");
    if (!list) {
        return;
    }

    list.innerHTML = "";

    (insights || []).forEach((text) => {
        const li = document.createElement("li");
        li.innerText = text;
        list.appendChild(li);
    });
}

function renderPlacementReasons(reasons) {
    const list = document.getElementById("placementReasons");
    if (!list) {
        return;
    }

    list.innerHTML = "";

    (reasons || []).forEach((reason) => {
        const li = document.createElement("li");
        li.innerText = reason;
        list.appendChild(li);
    });
}

function renderProfile(profile) {
    if (!profile) {
        return;
    }

    setText("profileName", profile.name || "--");
    setText("profileEmail", profile.email || "--");
    setText("profileDepartment", profile.department || "--");
}

function renderStrengthWeakness(data, options = {}) {
    const strengthLabel = data.strength || "Not available";
    const weaknessLabel = data.weakness || "Not available";

    setHtml(options.strengthId || "strengthText", "&#127919; Strength: " + strengthLabel);
    setHtml(options.weaknessId || "weaknessText", "&#9888; Weak Area: " + weaknessLabel);
}

function renderDashboardMetrics(data) {
    setText("attendance", formatPercent(data.attendance));
    setText("marks", formatValue(data.marks));
    setText("mock", formatValue(data.mock_score));
    setText("skills", formatValue(data.skills_score));
}

function highlightProgressMetrics(data) {
    const metrics = getMetricMeta(data);
    const extremes = getMetricExtremes(data);

    metrics.forEach((metric) => {
        const card = document.getElementById(metric.cardId);
        const note = document.getElementById(metric.noteId);

        if (!card || !note) {
            return;
        }

        card.classList.remove("metric-card--best", "metric-card--worst");
        note.innerText = "";

        if (metric.cardId === extremes.best.cardId) {
            card.classList.add("metric-card--best");
            note.innerText = "Best Area";
        }

        if (metric.cardId === extremes.worst.cardId && metric.cardId !== extremes.best.cardId) {
            card.classList.add("metric-card--worst");
            note.innerText = "Needs Improvement";
        }
    });

    setText("progressStrengthText", "Best Area: " + extremes.best.label);
    setText("progressWeaknessText", "Needs Improvement: " + extremes.worst.label);
}

function ensureSkillsLayout() {
    const skillsList = document.getElementById("skillsList");
    const skillInput = document.getElementById("skillInput");

    if (!skillsList || !skillInput) {
        return;
    }

    skillsList.classList.add("skills-chip-list");
    skillInput.classList.add("text-input");

    const addButton = document.querySelector("button[onclick='addSkill()']");
    if (addButton) {
        addButton.classList.add("primary-button");
    }

    if (!document.getElementById("skillsCount")) {
        const addSkillCard = skillInput.closest(".card");
        if (addSkillCard && addSkillCard.parentElement) {
            const summaryCard = document.createElement("div");
            summaryCard.className = "card skill-summary-card";
            summaryCard.innerHTML = `
                <div class="section-heading">
                    <h3>Total Skills</h3>
                    <span class="subtle-text" id="skillsCount">0 skills added</span>
                </div>
                <p class="empty-state" id="skillsSummaryMessage">
                    Add your skills to make your student profile more complete.
                </p>
            `;
            addSkillCard.parentElement.insertBefore(summaryCard, addSkillCard);
        }
    }

    if (!document.getElementById("skillsEmptyState") && skillsList.parentElement) {
        const emptyState = document.createElement("p");
        emptyState.id = "skillsEmptyState";
        emptyState.className = "empty-state";
        emptyState.hidden = true;
        emptyState.innerText = "No skills added yet. Start by adding your first skill.";
        skillsList.parentElement.insertBefore(emptyState, skillsList);
    }
}

function normalizeSkillsResponse(data) {
    if (!Array.isArray(data)) {
        return [];
    }

    return data.map((skill) => {
        if (typeof skill === "string") {
            return { skill_name: skill };
        }

        return skill;
    });
}

async function loadDashboard() {
    setUser();

    try {
        const data = await fetchJson("/student/dashboard");
        const readinessScore = Number(data.readiness_score || 0);
        const progress = document.getElementById("progressFill");
        const statusNode = document.getElementById("status");
        const riskNode = document.getElementById("risk");

        setText("readinessScore", formatPercent(readinessScore));
        setText("placement", data.placement_status || "Not Available");

        if (progress) {
            progress.style.width = readinessScore + "%";
            progress.style.background = getReadinessColor(readinessScore);
        }

        if (statusNode) {
            statusNode.innerText = data.status || "--";
            applyKpiColor(
                statusNode,
                readinessScore >= 80 ? "success" : readinessScore >= 60 ? "warning" : "danger"
            );
        }

        if (riskNode) {
            riskNode.innerText = data.risk_level || "--";
            applyKpiColor(
                riskNode,
                data.risk_level === "Safe"
                    ? "success"
                    : data.risk_level === "Warning"
                    ? "warning"
                    : "danger"
            );
        }

        renderDashboardMetrics(data);
        renderProfile(data.profile);
        renderPlacementReasons(data.placement_reasons || []);
        renderStrengthWeakness(data);
        renderInsights(data.insights || []);
        renderChart(data);
        loadLeaderboard();
    } catch (error) {
        console.error(error);
    }
}

async function loadProgress() {
    setUser();

    try {
        const data = await fetchJson("/student/dashboard");

        setText("attendance", formatPercent(data.attendance));
        setText("marks", formatValue(data.marks));
        setText("mock", formatValue(data.mock_score));
        setText("skills", formatValue(data.skills_score));

        highlightProgressMetrics(data);
        renderChart(data);
    } catch (error) {
        console.error(error);
    }
}

async function loadSkills() {
    setUser();
    ensureSkillsLayout();

    try {
        const data = normalizeSkillsResponse(await fetchJson("/student/skills"));
        const list = document.getElementById("skillsList");
        const emptyState = document.getElementById("skillsEmptyState");
        const summaryMessage = document.getElementById("skillsSummaryMessage");
        const count = data.length;

        setText("skillsCount", count + (count === 1 ? " skill added" : " skills added"));

        if (!list) {
            return;
        }

        list.innerHTML = "";

        if (!count) {
            if (emptyState) {
                emptyState.hidden = false;
            }
            if (summaryMessage) {
                summaryMessage.innerText = "No skills added yet. Start by adding your first skill.";
            }
            return;
        }

        if (emptyState) {
            emptyState.hidden = true;
        }
        if (summaryMessage) {
            summaryMessage.innerText = "Your skills are strengthening your student profile.";
        }

        data.forEach((skill) => {
            const chip = document.createElement(list.tagName === "UL" ? "li" : "span");
            chip.className = "skill-chip";
            chip.innerText = skill.skill_name;
            list.appendChild(chip);
        });
    } catch (error) {
        console.error(error);
    }
}

async function addSkill() {
    const input = document.getElementById("skillInput");
    const skill = (input ? input.value : "").trim();

    if (!skill) {
        alert("Enter a skill.");
        return;
    }

    try {
        await fetchJson("/student/skills", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ skill_name: skill })
        });

        input.value = "";
        loadSkills();
    } catch (error) {
        console.error(error);
        alert(error.message || "Unable to add skill.");
    }
}

async function loadLeaderboard() {
    const list = document.getElementById("topStudents");
    if (!list) {
        return;
    }

    try {
        const data = await fetchJson("/top-students");
        list.innerHTML = "";

        data.forEach((student, index) => {
            const badge = ["#1", "#2", "#3"][index] || "#" + (index + 1);
            const score = student.final_score ?? student.score ?? "--";
            const li = document.createElement("li");

            li.innerHTML = `
                <div class="leaderboard-item">
                    <span>${badge} ${student.name}</span>
                    <span>${score}</span>
                </div>
            `;

            list.appendChild(li);
        });
    } catch (error) {
        console.error(error);
    }
}

async function register() {
    const name = document.getElementById("name").value.trim();
    const email = document.getElementById("email").value.trim();
    const password = document.getElementById("password").value;
    const departmentInput = document.getElementById("department");
    const department = departmentInput ? departmentInput.value.trim() : "";
    const role = document.getElementById("role").value;
    const roleOption = getSelectedRoleOption();
    const roleName = (roleOption?.dataset.roleName || "").toLowerCase();
    const message = document.getElementById("message");

    message.innerText = "Creating account...";

    if (!name || !email || !password || !role) {
        message.innerText = "Name, email, password, and role are required.";
        return;
    }

    if (roleName === "student" && !department) {
        message.innerText = "Department is required for student registration.";
        return;
    }

    try {
        const data = await fetchJson("/auth/register", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
                name,
                email,
                password,
                role_id: parseInt(role, 10),
                department,
            })
        });

        console.log("Register response:", data);
        message.innerText = data.message || "Account created successfully.";
        setTimeout(() => window.location.href = "/", 1500);
    } catch (error) {
        console.error(error);
        message.innerText = error.message || "Registration failed.";
    }
}

async function login() {
    const email = document.getElementById("email").value.trim();
    const password = document.getElementById("password").value;
    const message = document.getElementById("message");

    message.innerText = "Logging in...";

    try {
        const data = await fetchJson("/auth/login", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ email, password })
        });

        console.log("Login response:", data);

        if (!data.token || !data.user) {
            throw new Error(data.error || "Login failed.");
        }

        localStorage.setItem("token", data.token);
        localStorage.setItem("user_email", data.user.email);
        localStorage.setItem("role_id", data.user.role_id);
        localStorage.setItem("role_name", data.user.role_name || "");

        window.location.href = data.user.dashboard_path || "/";
    } catch (error) {
        console.error(error);
        message.innerText = error.message || "Login failed.";
    }
}

function toggleTheme() {
    document.body.classList.toggle("dark");
    localStorage.setItem(
        "theme",
        document.body.classList.contains("dark") ? "dark" : "light"
    );
}

function getFacultyState() {
    if (!window.facultyState) {
        window.facultyState = {
            students: [],
            subjects: [],
            selectedStudentId: null,
        };
    }

    return window.facultyState;
}

function focusFacultySection(sectionId) {
    const section = document.getElementById(sectionId);
    if (section) {
        section.scrollIntoView({ behavior: "smooth", block: "start" });
    }
}

function setFacultyActionState(text) {
    setText("facultyActionState", text || "Waiting");
}

function showFacultyMessage(message, type = "success") {
    const card = document.getElementById("facultyMessageCard");
    const text = document.getElementById("facultyMessageText");

    if (!card || !text) {
        return;
    }

    card.hidden = false;
    card.classList.remove("faculty-message-card--success", "faculty-message-card--error");
    card.classList.add(type === "error" ? "faculty-message-card--error" : "faculty-message-card--success");
    text.innerText = message;
    setFacultyActionState(type === "error" ? "Failed" : "Saved");
}

function populateFacultySubjectOptions(subjects) {
    ["attendanceSubject", "marksSubject"].forEach((selectId) => {
        const select = document.getElementById(selectId);
        if (!select) {
            return;
        }

        select.innerHTML = "";

        const placeholder = document.createElement("option");
        placeholder.value = "";
        placeholder.innerText = subjects.length ? "Select Subject" : "No Subjects Available";
        select.appendChild(placeholder);

        subjects.forEach((subject) => {
            const option = document.createElement("option");
            option.value = subject.id;
            option.innerText = subject.name + " (" + subject.code + ")";
            select.appendChild(option);
        });
    });
}

function setFacultyStudentSelection(student) {
    const state = getFacultyState();
    state.selectedStudentId = student ? student.student_id : null;

    const label = student ? student.name + " (" + student.department + ")" : "None";
    setText("facultySelectedStudent", label);

    const mappings = [
        ["attendanceStudent", "attendanceStudentId"],
        ["marksStudent", "marksStudentId"],
        ["mockStudent", "mockStudentId"],
    ];

    mappings.forEach(([nameId, hiddenId]) => {
        const input = document.getElementById(nameId);
        const hidden = document.getElementById(hiddenId);

        if (input) {
            input.value = student ? student.name + " - " + student.email : "";
        }

        if (hidden) {
            hidden.value = student ? student.student_id : "";
        }
    });
}

function selectFacultyStudent(studentId, sectionId) {
    const state = getFacultyState();
    const student = state.students.find((item) => Number(item.student_id) === Number(studentId));

    if (!student) {
        return;
    }

    setFacultyStudentSelection(student);
    setFacultyActionState("Student Selected");

    if (sectionId) {
        focusFacultySection(sectionId);
    }
}

function renderFacultyStudents(students) {
    const body = document.getElementById("facultyStudentsTable");
    if (!body) {
        return;
    }

    body.innerHTML = "";

    if (!students.length) {
        const row = document.createElement("tr");
        const cell = document.createElement("td");
        cell.colSpan = 4;
        cell.innerText = "No students found.";
        row.appendChild(cell);
        body.appendChild(row);
        return;
    }

    students.forEach((student) => {
        const row = document.createElement("tr");
        const nameCell = document.createElement("td");
        const emailCell = document.createElement("td");
        const departmentCell = document.createElement("td");
        const actionCell = document.createElement("td");
        const actionGroup = document.createElement("div");

        nameCell.innerText = student.name || "--";
        emailCell.innerText = student.email || "--";
        departmentCell.innerText = student.department || "--";

        actionGroup.className = "faculty-action-group";

        [
            ["Manage Attendance", "attendanceSection"],
            ["Manage Marks", "marksSection"],
            ["Manage Mock Tests", "mockSection"],
        ].forEach(([label, sectionId]) => {
            const button = document.createElement("button");
            button.type = "button";
            button.className = "primary-button faculty-table-button";
            button.innerText = label;
            button.onclick = () => selectFacultyStudent(student.student_id, sectionId);
            actionGroup.appendChild(button);
        });

        actionCell.appendChild(actionGroup);
        row.appendChild(nameCell);
        row.appendChild(emailCell);
        row.appendChild(departmentCell);
        row.appendChild(actionCell);
        body.appendChild(row);
    });
}

async function loadFacultyDashboard() {
    if (!document.getElementById("facultyStudentsTable")) {
        return;
    }

    setUser();

    try {
        const [students, subjects] = await Promise.all([
            fetchJson("/faculty/dashboard"),
            fetchJson("/subjects"),
        ]);
        const state = getFacultyState();

        state.students = Array.isArray(students) ? students : [];
        state.subjects = Array.isArray(subjects) ? subjects : [];

        setText("facultyStudentCount", state.students.length);
        setText("facultySubjectCount", state.subjects.length);

        populateFacultySubjectOptions(state.subjects);
        renderFacultyStudents(state.students);

        const selected = state.students.find(
            (student) => Number(student.student_id) === Number(state.selectedStudentId)
        );

        if (selected) {
            setFacultyStudentSelection(selected);
        } else if (state.students.length) {
            setFacultyStudentSelection(state.students[0]);
        } else {
            setFacultyStudentSelection(null);
        }

        setFacultyActionState("Ready");
    } catch (error) {
        console.error(error);
        showFacultyMessage(error.message || "Unable to load faculty dashboard.", "error");
    }
}

function getSelectedFacultyStudentId(hiddenInputId) {
    const value = document.getElementById(hiddenInputId)?.value;

    if (!value) {
        throw new Error("Select a student from the table first.");
    }

    return Number(value);
}

async function submitAttendance(event) {
    event.preventDefault();

    try {
        const studentId = getSelectedFacultyStudentId("attendanceStudentId");
        const subjectId = Number(document.getElementById("attendanceSubject")?.value || 0);
        const attendancePercentage = Number(document.getElementById("attendancePercentage")?.value || "");

        if (!subjectId) {
            throw new Error("Select a subject for attendance.");
        }

        if (Number.isNaN(attendancePercentage) || attendancePercentage < 0 || attendancePercentage > 100) {
            throw new Error("Enter attendance percentage between 0 and 100.");
        }

        const data = await fetchJson("/faculty/attendance", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
                student_id: studentId,
                subject_id: subjectId,
                attendance_percentage: attendancePercentage,
            }),
        });

        document.getElementById("attendancePercentage").value = "";
        await loadFacultyDashboard();
        showFacultyMessage(data.message || "Attendance saved successfully.");
    } catch (error) {
        console.error(error);
        showFacultyMessage(error.message || "Unable to save attendance.", "error");
    }
}

async function submitMarks(event) {
    event.preventDefault();

    try {
        const studentId = getSelectedFacultyStudentId("marksStudentId");
        const subjectId = Number(document.getElementById("marksSubject")?.value || 0);
        const marks = Number(document.getElementById("marksValue")?.value || "");
        const examTypeInput = document.getElementById("marksExamType");
        const examType = examTypeInput && examTypeInput.value.trim() ? examTypeInput.value.trim() : null;

        if (!subjectId) {
            throw new Error("Select a subject for marks.");
        }

        if (Number.isNaN(marks) || marks < 0 || marks > 100) {
            throw new Error("Enter marks between 0 and 100.");
        }

        const data = await fetchJson("/marks", {
            method: "PUT",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
                student_id: studentId,
                subject_id: subjectId,
                marks,
                exam_type: examType,
            }),
        });

        document.getElementById("marksValue").value = "";
        if (examTypeInput) {
            examTypeInput.value = "";
        }
        await loadFacultyDashboard();
        showFacultyMessage(data.message || "Marks saved successfully.");
    } catch (error) {
        console.error(error);
        showFacultyMessage(error.message || "Unable to save marks.", "error");
    }
}

async function submitMockTest(event) {
    event.preventDefault();

    try {
        const studentId = getSelectedFacultyStudentId("mockStudentId");
        const testNameInput = document.getElementById("mockTestName");
        const scoreInput = document.getElementById("mockScore");
        const testName = testNameInput ? testNameInput.value.trim() : "";
        const score = Number(scoreInput?.value || "");

        if (!testName) {
            throw new Error("Enter a mock test name.");
        }

        if (Number.isNaN(score) || score < 0 || score > 100) {
            throw new Error("Enter a mock score between 0 and 100.");
        }

        const data = await fetchJson("/mock-tests", {
            method: "PUT",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
                student_id: studentId,
                test_name: testName,
                score,
            }),
        });

        if (testNameInput) {
            testNameInput.value = "";
        }
        if (scoreInput) {
            scoreInput.value = "";
        }
        await loadFacultyDashboard();
        showFacultyMessage(data.message || "Mock test saved successfully.");
    } catch (error) {
        console.error(error);
        showFacultyMessage(error.message || "Unable to save mock test.", "error");
    }
}
