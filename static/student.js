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

function renderWeeklySummary(summary) {
    if (!summary) {
        return;
    }

    setText("weeklyPrimaryFocus", summary.primary_focus || "--");
    setText("weeklyUnreadNotifications", formatValue(summary.unread_notifications || 0));
    setText("weeklyActiveGoals", formatValue(summary.active_goals || 0));
    setText("weeklyGoalCompletion", formatValue(summary.goal_completion_rate || 0) + "%");
    setText("weeklyHeadline", summary.headline || "Your weekly summary is ready.");
}

function renderActionPlan(actions) {
    const list = document.getElementById("studentActionPlan");
    if (!list) {
        return;
    }

    list.innerHTML = "";

    if (!Array.isArray(actions) || !actions.length) {
        list.innerHTML = '<li class="insight-item">No action items right now. Keep your current routine steady.</li>';
        return;
    }

    actions.forEach((action) => {
        const li = document.createElement("li");
        li.className = "insight-item";
        li.innerHTML = `
            <div class="action-plan-copy">
                <strong>${action.title || "Next Step"}</strong>
                <p>${action.message || ""}</p>
            </div>
            <span class="card-badge">${action.priority || "medium"}</span>
        `;
        list.appendChild(li);
    });
}

function renderGoalSnapshot(goalSummary, dueGoals) {
    setText("goalSummaryActive", formatValue(goalSummary?.active || 0));
    setText("goalSummaryCompleted", formatValue(goalSummary?.completed || 0));
    setText("goalSummaryDueSoon", formatValue((dueGoals || []).length));

    const list = document.getElementById("dueGoalsList");
    if (!list) {
        return;
    }

    list.innerHTML = "";

    if (!Array.isArray(dueGoals) || !dueGoals.length) {
        list.innerHTML = '<li class="insight-item">No upcoming goal deadlines right now. Use this time to push current goals forward.</li>';
        return;
    }

    dueGoals.forEach((goal) => {
        const li = document.createElement("li");
        li.className = "insight-item";
        li.innerHTML = `
            <div class="action-plan-copy">
                <strong>${goal.title || "Goal"}</strong>
                <p>Due by ${goal.target_date || "No date"} • Progress ${formatValue(goal.progress_pct || 0)}%</p>
            </div>
        `;
        list.appendChild(li);
    });
}

function renderNotificationSummary(summary) {
    setText("notificationDigestStatus", summary?.digest_enabled ? "Enabled" : "Disabled");
    setText("notificationDigestFrequency", summary?.digest_frequency || "--");
    setText("notificationUnreadCount", formatValue(summary?.unread_count || 0));
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
        renderWeeklySummary(data.weekly_summary);
        renderActionPlan(data.action_plan || []);
        renderGoalSnapshot(data.goal_summary || {}, data.due_goals || []);
        renderNotificationSummary(data.notification_summary || {});
        renderSubjectPerformance(data.subject_performance || []);
        renderSubjectPerformanceChart(data.subject_performance || []);
        renderInsights(data.insights || []);
        renderChart(data);
        renderLeaderboard(data.top_students || []);

        // NEW: Render placement score breakdown
        if (data.placement_breakdown) {
            renderPlacementBreakdown(data.placement_breakdown, "placementBreakdownContainer");
        }

        // NEW: Render growth tracking
        if (data.marks_timeline && data.marks_timeline.length > 0) {
            renderGrowthTimeline(data.marks_timeline, "growthTimelineChart");
        }

        // NEW: Render subject trends
        if (data.subject_trends && data.subject_trends.length > 0) {
            renderSubjectTrends(data.subject_trends, "subjectTrendsContainer");
        }
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
