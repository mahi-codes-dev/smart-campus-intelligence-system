function renderLeaderboard(students) {
    const list = document.getElementById("topStudents");
    if (!list) {
        return;
    }

    list.innerHTML = "";

    if (!Array.isArray(students) || !students.length) {
        const li = document.createElement("li");
        li.innerText = "No leaderboard data available yet.";
        list.appendChild(li);
        return;
    }

    students.forEach((student, index) => {
        const badge = ["#1", "#2", "#3"][index] || "#" + (index + 1);
        const score = student.final_score ?? student.score ?? "--";
        const li = document.createElement("li");

        li.innerHTML = `
            <div class="leaderboard-item">
                <span>${badge} ${student.name}</span>
                <span>${formatValue(score)}</span>
            </div>
        `;

        list.appendChild(li);
    });
}

async function getStudentDashboardSnapshot() {
    return fetchJson("/student/dashboard");
}

async function loadDashboard() {
    if (!requireAuth(["Student"])) {
        return;
    }

    setUser();

    try {
        const data = await getStudentDashboardSnapshot();
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
        renderProfileSummary(data.profile_summary);
        renderAlerts(data.alerts || []);
        renderPlacementReasons(data.placement_reasons || []);
        renderStrengthWeakness(data);
        renderSubjectPerformance(data.subject_performance || []);
        renderSubjectPerformanceChart(data.subject_performance || []);
        renderInsights(data.insights || []);
        renderChart(data);
        renderLeaderboard(data.top_students || []);
    } catch (error) {
        console.error(error);
        showToast(error.message || "Unable to load dashboard.", "error");
    }
}

async function loadProgress() {
    if (!requireAuth(["Student"])) {
        return;
    }

    setUser();

    try {
        const data = await getStudentDashboardSnapshot();

        setText("attendance", formatPercent(data.attendance));
        setText("marks", formatValue(data.marks));
        setText("mock", formatValue(data.mock_score));
        setText("skills", formatValue(data.skills_score));

        highlightProgressMetrics(data);
        renderChart(data);
    } catch (error) {
        console.error(error);
        showToast(error.message || "Unable to load progress.", "error");
    }
}

async function loadSkills() {
    if (!requireAuth(["Student"])) {
        return;
    }

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
            const level = (skill.skill_level || "Intermediate").toLowerCase();
            chip.className = `skill-chip skill-chip--${level}`;
            chip.innerHTML = `
                <span>${skill.skill_name}</span>
                <small>${skill.skill_level || "Intermediate"}</small>
            `;
            list.appendChild(chip);
        });
    } catch (error) {
        console.error(error);
        showToast(error.message || "Unable to load skills.", "error");
    }
}

async function addSkill() {
    const input = document.getElementById("skillInput");
    const levelInput = document.getElementById("skillLevel");
    const skill = (input ? input.value : "").trim();
    const skillLevel = levelInput ? levelInput.value : "Intermediate";

    if (!skill) {
        showToast("Enter a skill before adding.", "error");
        return;
    }

    try {
        const data = await fetchJson("/student/skills", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ skill_name: skill, skill_level: skillLevel })
        });

        input.value = "";
        if (levelInput) {
            levelInput.value = "Intermediate";
        }
        showToast(data.message || "Skill saved successfully.");
        loadSkills();
    } catch (error) {
        console.error(error);
        showToast(error.message || "Unable to add skill.", "error");
    }
}

async function loadProfile() {
    if (!requireAuth(["Student"])) {
        return;
    }

    setUser();

    try {
        const data = await getStudentDashboardSnapshot();

        renderProfile(data.profile);
        renderProfileSummary(data.profile_summary, "profileSummaryList");
        renderAlerts(data.alerts || [], "profileAlerts");
        renderSubjectPerformance(data.subject_performance || [], "profileSubjectPerformanceTable");
        renderSubjectPerformanceChart(data.subject_performance || [], "profileSubjectPerformanceChart");

        setText("profileReadiness", formatPercent(data.readiness_score || 0));
        setText("profileStatus", data.status || "--");
        setText("profileRisk", data.risk_level || "--");
        setText("profilePlacement", data.placement_status || "--");
        renderPlacementReasons(data.placement_reasons || []);
    } catch (error) {
        console.error(error);
        showToast(error.message || "Unable to load profile.", "error");
    }
}

async function loadLeaderboard() {
    try {
        const data = await fetchJson("/top-students");
        renderLeaderboard(data);
    } catch (error) {
        console.error(error);
        showToast(error.message || "Unable to load leaderboard.", "error");
    }
}
