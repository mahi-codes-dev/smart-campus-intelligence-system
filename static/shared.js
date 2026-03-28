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
