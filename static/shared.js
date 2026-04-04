function go(path) {
    window.location.href = path;
}

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
        emailNode.innerText = email || "User";
    }
}

function requireAuth(expectedRoles = []) {
    const token = localStorage.getItem("token");

    if (!token) {
        window.location.href = "/";
        return false;
    }

    if (Array.isArray(expectedRoles) && expectedRoles.length) {
        const currentRole = (localStorage.getItem("role_name") || "").toLowerCase();
        const allowedRoles = expectedRoles.map((role) => String(role).toLowerCase());

        if (!allowedRoles.includes(currentRole)) {
            window.location.href = "/";
            return false;
        }
    }

    return true;
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

function renderInsights(insights, listId = "insightsList") {
    const list = document.getElementById(listId);
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
    setText("profileRollNumber", profile.roll_number || "--");
    setText("profileEmail", profile.email || "--");
    setText("profileDepartment", profile.department || "--");
}

function renderSubjectPerformance(subjects, tableId = "subjectPerformanceTable") {
    const body = document.getElementById(tableId);
    if (!body) {
        return;
    }

    body.innerHTML = "";

    if (!Array.isArray(subjects) || !subjects.length) {
        const row = document.createElement("tr");
        const cell = document.createElement("td");
        cell.colSpan = 4;
        cell.innerText = "No subject performance data available yet.";
        row.appendChild(cell);
        body.appendChild(row);
        return;
    }

    subjects.forEach((subject) => {
        const row = document.createElement("tr");
        const subjectCell = document.createElement("td");
        const codeCell = document.createElement("td");
        const averageCell = document.createElement("td");
        const latestCell = document.createElement("td");

        subjectCell.innerText = subject.subject_name || "--";
        codeCell.innerText = subject.subject_code || "--";
        averageCell.innerText = formatValue(subject.average_marks);
        latestCell.innerText = subject.latest_marks === null ? "--" : formatValue(subject.latest_marks);

        row.appendChild(subjectCell);
        row.appendChild(codeCell);
        row.appendChild(averageCell);
        row.appendChild(latestCell);
        body.appendChild(row);
    });
}

function renderSubjectPerformanceChart(subjects, canvasId = "subjectPerformanceChart") {
    const canvas = document.getElementById(canvasId);
    if (!canvas || typeof Chart === "undefined") {
        return;
    }

    const labels = Array.isArray(subjects) ? subjects.map((subject) => subject.subject_code || subject.subject_name || "--") : [];
    const values = Array.isArray(subjects) ? subjects.map((subject) => Number(subject.average_marks || 0)) : [];
    const chartKey = "__chart_" + canvasId;

    if (window[chartKey]) {
        window[chartKey].destroy();
    }

    window[chartKey] = new Chart(canvas, {
        type: "line",
        data: {
            labels,
            datasets: [{
                label: "Average Marks",
                data: values,
                borderColor: "#06b6d4",
                backgroundColor: "rgba(6, 182, 212, 0.18)",
                fill: true,
                tension: 0.3,
            }],
        },
        options: {
            responsive: true,
            plugins: {
                legend: {
                    display: false,
                },
            },
            scales: {
                y: {
                    beginAtZero: true,
                    max: 100,
                },
            },
        },
    });
}

function renderAlerts(alerts, containerId = "studentAlerts") {
    const container = document.getElementById(containerId);
    if (!container) {
        return;
    }

    container.innerHTML = "";

    if (!Array.isArray(alerts) || !alerts.length) {
        const empty = document.createElement("div");
        empty.className = "alert-card alert-card--success";
        empty.innerHTML = `
            <strong>No active alerts</strong>
            <p>Your current academic indicators look stable.</p>
        `;
        container.appendChild(empty);
        return;
    }

    alerts.forEach((alertItem) => {
        const card = document.createElement("div");
        const severity = (alertItem.severity || "warning").toLowerCase();
        card.className = `alert-card alert-card--${severity}`;
        card.innerHTML = `
            <strong>${alertItem.title || "Alert"}</strong>
            <p>${alertItem.message || ""}</p>
        `;
        container.appendChild(card);
    });
}

function renderProfileSummary(summary, listId = "profileSummaryList") {
    const list = document.getElementById(listId);
    if (!list) {
        return;
    }

    list.innerHTML = "";

    [
        `Readiness Score: ${formatPercent(summary?.readiness_score || 0)}`,
        `Current Status: ${summary?.status || "--"}`,
        `Best Subject: ${summary?.best_subject || "Not available"}`,
        `Needs Attention: ${summary?.weakest_subject || "Not available"}`,
    ].forEach((text) => {
        const li = document.createElement("li");
        li.innerText = text;
        list.appendChild(li);
    });
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

function ensureToastContainer() {
    let container = document.getElementById("toastContainer");
    if (!container) {
        container = document.createElement("div");
        container.id = "toastContainer";
        container.className = "toast-container";
        document.body.appendChild(container);
    }

    return container;
}

function showToast(message, type = "success") {
    const container = ensureToastContainer();
    const toast = document.createElement("div");

    toast.className = `toast toast--${type}`;
    toast.innerText = message;
    container.appendChild(toast);

    requestAnimationFrame(() => toast.classList.add("toast--visible"));

    setTimeout(() => {
        toast.classList.remove("toast--visible");
        setTimeout(() => toast.remove(), 250);
    }, 3200);
}

function ensureConfirmModal() {
    let overlay = document.getElementById("confirmModalOverlay");

    if (overlay) {
        return overlay;
    }

    overlay = document.createElement("div");
    overlay.id = "confirmModalOverlay";
    overlay.className = "modal-overlay";
    overlay.hidden = true;
    overlay.innerHTML = `
        <div class="modal-card">
            <h3 id="confirmModalTitle">Confirm Action</h3>
            <p id="confirmModalMessage">Are you sure?</p>
            <div class="modal-actions">
                <button class="toggle-button" type="button" id="confirmModalCancel">Cancel</button>
                <button class="logout-button" type="button" id="confirmModalConfirm">Confirm</button>
            </div>
        </div>
    `;
    document.body.appendChild(overlay);

    return overlay;
}

function confirmAction({ title = "Confirm Action", message = "Are you sure?", confirmText = "Confirm", danger = true } = {}) {
    const overlay = ensureConfirmModal();
    const titleNode = document.getElementById("confirmModalTitle");
    const messageNode = document.getElementById("confirmModalMessage");
    const cancelButton = document.getElementById("confirmModalCancel");
    const confirmButton = document.getElementById("confirmModalConfirm");

    titleNode.innerText = title;
    messageNode.innerText = message;
    confirmButton.innerText = confirmText;
    confirmButton.className = danger ? "logout-button" : "primary-button";

    overlay.hidden = false;

    return new Promise((resolve) => {
        const cleanup = (result) => {
            overlay.hidden = true;
            cancelButton.onclick = null;
            confirmButton.onclick = null;
            overlay.onclick = null;
            resolve(result);
        };

        cancelButton.onclick = () => cleanup(false);
        confirmButton.onclick = () => cleanup(true);
        overlay.onclick = (event) => {
            if (event.target === overlay) {
                cleanup(false);
            }
        };
    });
}

function toggleTheme() {
    document.body.classList.toggle("dark");
    localStorage.setItem(
        "theme",
        document.body.classList.contains("dark") ? "dark" : "light"
    );
}

(function () {
    if (localStorage.getItem("theme") === "dark") {
        document.body.classList.add("dark");
    }
})();

/* ================= NEW FUNCTIONS FOR UI/UX IMPROVEMENTS ================= */

/**
 * Show loading state in a container
 * @param {string} containerId - ID of the container
 * @param {string} message - Loading message (default: "Fetching data...")
 */
function showLoadingState(containerId, message = "Fetching data...") {
    const container = document.getElementById(containerId);
    if (!container) return;

    container.innerHTML = `
        <div class="loading-state">
            <div class="loading-spinner"></div>
            <span class="fetching-data">${message}</span>
        </div>
    `;
}

/**
 * Show empty state in a container
 * @param {string} containerId - ID of the container
 * @param {object} options - { title, message, icon }
 */
function showEmptyState(containerId, options = {}) {
    const container = document.getElementById(containerId);
    if (!container) return;

    const {
        title = "No Data Available",
        message = "There is no data to display at this moment.",
        icon = "📊"
    } = options;

    container.innerHTML = `
        <div class="empty-state-container">
            <div class="empty-state-icon">${icon}</div>
            <div class="empty-state-title">${title}</div>
            <div class="empty-state-message">${message}</div>
        </div>
    `;
}

/**
 * Show styled message instead of alert
 * @param {string} containerId - ID of the container
 * @param {object} options - { type, title, message, icon }
 */
function showStyledMessage(containerId, options = {}) {
    const container = document.getElementById(containerId);
    if (!container) return;

    const {
        type = "info",  // info, success, warning, danger
        title = "Message",
        message = "",
        icon = "ℹ️"
    } = options;

    const messageElement = document.createElement("div");
    messageElement.className = `styled-message styled-message--${type}`;
    messageElement.innerHTML = `
        <span>${icon}</span>
        <div>
            <strong>${title}</strong>
            ${message ? `<p>${message}</p>` : ""}
        </div>
    `;

    container.appendChild(messageElement);
}

/**
 * Render placement score breakdown
 * @param {object} breakdown - breakdown data from backend
 * @param {string} containerId - ID of the container
 */
function renderPlacementBreakdown(breakdown, containerId = "placementBreakdownContainer") {
    const container = document.getElementById(containerId);
    if (!container || !breakdown) return;

    const { components = [], calculation_formula = "" } = breakdown;

    let html = '<div class="placement-breakdown-card">';
    html += '<h3 class="placement-breakdown-title">📊 Placement Score Breakdown</h3>';
    html += '<div class="breakdown-components">';

    components.forEach(comp => {
        const statusClass = comp.status === "Good" ? "component-status--good" : "component-status--risk";
        html += `
            <div class="breakdown-component">
                <div class="component-metric">${comp.metric}</div>
                <div class="component-value">${formatValue(comp.value)}</div>
                <div class="component-weight">Weight: ${comp.weight}%</div>
                <div class="component-contribution">Contribution: ${formatValue(comp.contribution)}%</div>
                <span class="component-status ${statusClass}">${comp.status}</span>
            </div>
        `;
    });

    html += '</div>';
    
    if (calculation_formula) {
        html += `<div class="breakdown-formula">${calculation_formula}</div>`;
    }

    html += '</div>';
    container.innerHTML = html;
}

/**
 * Render growth tracking timeline
 * @param {array} marksTimeline - marks history data
 * @param {string} canvasId - Canvas ID for chart
 */
function renderGrowthTimeline(marksTimeline, canvasId = "growthTimelineChart") {
    const canvas = document.getElementById(canvasId);
    if (!canvas || typeof Chart === "undefined") return;

    const chartKey = "__chart_" + canvasId;

    if (window[chartKey]) {
        window[chartKey].destroy();
    }

    const labels = marksTimeline.map(m => m.date ? new Date(m.date).toLocaleDateString() : "N/A");
    const values = marksTimeline.map(m => Number(m.marks || 0));

    window[chartKey] = new Chart(canvas, {
        type: "line",
        data: {
            labels,
            datasets: [{
                label: "Performance Over Time",
                data: values,
                borderColor: "#4f46e5",
                backgroundColor: "rgba(79, 70, 229, 0.12)",
                fill: true,
                tension: 0.4,
                borderWidth: 2,
                pointRadius: 5,
                pointBackgroundColor: "#4f46e5",
                pointBorderColor: "#ffffff",
                pointBorderWidth: 2,
            }],
        },
        options: {
            responsive: true,
            maintainAspectRatio: true,
            plugins: {
                legend: { display: true, labels: { boxWidth: 12 } },
            },
            scales: {
                y: {
                    beginAtZero: true,
                    max: 100,
                    title: { display: true, text: "Marks" },
                },
            },
        },
    });
}

/**
 * Render subject-wise trends
 * @param {array} subjectTrends - trends data
 * @param {string} containerId - Container ID
 */
function renderSubjectTrends(subjectTrends, containerId = "subjectTrendsContainer") {
    const container = document.getElementById(containerId);
    if (!container) return;

    if (!Array.isArray(subjectTrends) || !subjectTrends.length) {
        showEmptyState(containerId, {
            title: "No Trend Data",
            message: "Insufficient data to analyze subject trends.",
            icon: "📈"
        });
        return;
    }

    let html = '<div class="subject-trends">';

    subjectTrends.forEach(trend => {
        const trendClass = trend.trend === "Improving" ? "trend-indicator--improving" :
                          trend.trend === "Declining" ? "trend-indicator--declining" :
                          "trend-indicator--stable";

        const emoji = trend.trend === "Improving" ? "📈" :
                     trend.trend === "Declining" ? "📉" : "→";

        html += `
            <div class="trend-badge">
                <div class="trend-subject">${trend.subject}</div>
                <div class="trend-value">${formatValue(trend.latest)}</div>
                <span class="trend-indicator ${trendClass}">${emoji} ${trend.trend}</span>
            </div>
        `;
    });

    html += '</div>';
    container.innerHTML = html;
}

/**
 * Render enhanced skills display
 * @param {object} skillsData - { count, score, skills_list }
 * @param {string} containerId - Container ID
 */
function renderEnhancedSkills(skillsData, containerId = "skillsContainer") {
    const container = document.getElementById(containerId);
    if (!container) return;

    const { count = 0, score = 0, skills_list = [] } = skillsData;

    let html = '<div class="skills-container">';
    html += '<div class="skills-summary">';
    html += `<div class="skills-count-badge">📚 ${count} ${count === 1 ? "Skill" : "Skills"} Added</div>`;
    html += `<div class="skills-count-badge">⭐ Skill Score: ${formatValue(score)}%</div>`;
    html += '</div>';

    if (!Array.isArray(skills_list) || !skills_list.length) {
        showEmptyState(containerId, {
            title: "No Skills Added Yet",
            message: "Add your first skill to showcase your abilities.",
            icon: "💡"
        });
        return;
    }

    html += '<div class="skills-list-enhanced">';
    skills_list.forEach(skill => {
        const level = (skill.skill_level || "Intermediate").toLowerCase();
        const skillName = skill.skill_name || skill.name || "Unknown Skill";

        html += `
            <div class="skill-badge-enhanced">
                <div class="skill-name-enhanced">${skillName}</div>
                <span class="skill-level-badge skill-level--${level}">${skill.skill_level || "Intermediate"}</span>
            </div>
        `;
    });
    html += '</div>';

    html += '</div>';
    container.innerHTML = html;
}

/**
 * Render at-risk students list with styled display
 * @param {array} students - Array of at-risk students
 * @param {string} containerId - Container ID
 */
function renderAtRiskStudents(students, containerId = "atRiskStudentsContainer") {
    const container = document.getElementById(containerId);
    if (!container) return;

    if (!Array.isArray(students) || !students.length) {
        showEmptyState(containerId, {
            title: "No At-Risk Students",
            message: "All students are performing satisfactorily.",
            icon: "✅"
        });
        return;
    }

    let html = '<div class="faculty-table-wrapper"><table class="faculty-table"><thead><tr>';
    html += '<th>Name</th><th>Department</th><th>Score</th><th>Risk Level</th><th>Action</th>';
    html += '</tr></thead><tbody>';

    students.forEach(student => {
        const riskColor = student.final_score < 40 ? "red" : student.final_score < 60 ? "yellow" : "green";
        const riskLabel = student.risk || (student.final_score < 60 ? "High Risk" : "Medium Risk");

        html += `
            <tr>
                <td>${student.name || "N/A"}</td>
                <td>${student.department || "N/A"}</td>
                <td>${formatValue(student.final_score || 0)}%</td>
                <td><span class="${riskColor}">${riskLabel}</span></td>
                <td><button class="faculty-table-button primary-button" onclick="viewStudent(${student.student_id || student.id})">View</button></td>
            </tr>
        `;
    });

    html += '</tbody></table></div>';
    container.innerHTML = html;
}
