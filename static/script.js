/* Student Module Client Script */

function go(path) {
    window.location.href = path;
}

/* ================= AUTH ================= */

function logout() {
    localStorage.removeItem("token");
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
    const name = document.getElementById("name").value;
    const email = document.getElementById("email").value;
    const password = document.getElementById("password").value;
    const role = document.getElementById("role").value;
    const message = document.getElementById("message");

    message.innerText = "Creating account...";

    fetch("/auth/register", {
        method: "POST",
        headers: {"Content-Type": "application/json"},
        body: JSON.stringify({
            name, email, password,
            role_id: parseInt(role)
        })
    })
    .then(res => res.json())
    .then(data => {
        if (data.message || data.success) {
            message.innerText = "Account created ✅";
            setTimeout(() => window.location.href = "/", 1500);
        } else {
            message.innerText = data.error || "Failed ❌";
        }
    })
    .catch(() => message.innerText = "Server error ❌");
}

/* ================= LOGIN ================= */

function login() {
    const email = document.getElementById("email").value;
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
        if (data.token) {
            localStorage.setItem("token", data.token);
            localStorage.setItem("user_email", data.user.email);
            localStorage.setItem("role_id", data.user.role_id);

            if (data.user.role_id === 3)
                window.location.href = "/student-dashboard";
            else if (data.user.role_id === 2)
                window.location.href = "/faculty-dashboard";
            else
                window.location.href = "/dashboard";
        } else {
            message.innerText = data.error || "Login failed ❌";
        }
    })
    .catch(() => message.innerText = "Server error ❌");
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
    window.location.href = "/";
}

function setUser() {
    const email = localStorage.getItem("user_email");
    const emailNode = document.getElementById("userEmail");

    if (emailNode) {
        emailNode.innerText = email || "Student";
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

    if (!response.ok) {
        throw new Error(data.error || "Request failed");
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

function register() {
    const name = document.getElementById("name").value;
    const email = document.getElementById("email").value;
    const password = document.getElementById("password").value;
    const role = document.getElementById("role").value;
    const message = document.getElementById("message");

    message.innerText = "Creating account...";

    fetch("/auth/register", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
            name,
            email,
            password,
            role_id: parseInt(role, 10)
        })
    })
    .then((res) => res.json())
    .then((data) => {
        if (data.message || data.success) {
            message.innerText = "Account created successfully.";
            setTimeout(() => window.location.href = "/", 1500);
        } else {
            message.innerText = data.error || "Failed to register.";
        }
    })
    .catch(() => {
        message.innerText = "Server error.";
    });
}

function login() {
    const email = document.getElementById("email").value;
    const password = document.getElementById("password").value;
    const message = document.getElementById("message");

    message.innerText = "Logging in...";

    fetch("/auth/login", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ email, password })
    })
    .then((res) => res.json())
    .then((data) => {
        if (data.token) {
            localStorage.setItem("token", data.token);
            localStorage.setItem("user_email", data.user.email);
            localStorage.setItem("role_id", data.user.role_id);

            if (data.user.role_id === 3) {
                window.location.href = "/student-dashboard";
            } else if (data.user.role_id === 2) {
                window.location.href = "/faculty-dashboard";
            } else {
                window.location.href = "/dashboard";
            }
        } else {
            message.innerText = data.error || "Login failed.";
        }
    })
    .catch(() => {
        message.innerText = "Server error.";
    });
}

function toggleTheme() {
    document.body.classList.toggle("dark");
    localStorage.setItem(
        "theme",
        document.body.classList.contains("dark") ? "dark" : "light"
    );
}
