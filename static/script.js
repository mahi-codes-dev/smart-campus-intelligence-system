function register() {
    const name = document.getElementById("name").value;
    const email = document.getElementById("email").value;
    const password = document.getElementById("password").value;
    const role = document.getElementById("role").value;
    const message = document.getElementById("message");

    message.innerText = "Creating account...";

    fetch("/auth/register", {
        method: "POST",
        headers: {
            "Content-Type": "application/json"
        },
        body: JSON.stringify({
            name: name,
            email: email,
            password: password,
            role_id: parseInt(role)
        })
    })
    .then(res => res.json())
    .then(data => {
        if (data.message || data.success) {
            message.innerText = "Account created successfully ✅";

            setTimeout(() => {
                window.location.href = "/";
            }, 1500);
        } else {
            message.innerText = data.error || "Registration failed ❌";
        }
    })
    .catch(() => {
        message.innerText = "Server error ❌";
    });
}


function login() {
    const email = document.getElementById("email").value;
    const password = document.getElementById("password").value;
    const message = document.getElementById("message");

    message.innerText = "Logging in...";

    fetch("/auth/login", {
        method: "POST",
        headers: {
            "Content-Type": "application/json"
        },
        body: JSON.stringify({
            email: email,
            password: password
        })
    })
    .then(res => res.json())
    .then(data => {
        if (data.token) {

            // ✅ Store token
            localStorage.setItem("token", data.token);
            localStorage.setItem("user_email", data.user.email);
            localStorage.setItem("role_id", data.user.role_id);

            // 🔥 Role-based redirect
            if (data.user.role_id === 3) {
                window.location.href = "/student-dashboard";
            }
            else if (data.user.role_id === 2) {
                window.location.href = "/faculty-dashboard";
            }
            else {
                window.location.href = "/dashboard";
            }

        } else {
            message.innerText = data.error || "Login failed ❌";
        }
    })
    .catch(() => {
        message.innerText = "Server error ❌";
    });
}

async function loadDashboard() {
    const token = localStorage.getItem("token");

    if (!token) {
        window.location.href = "/";
        return;
    }

    try {
        const response = await fetch("/student/dashboard", {
            headers: { "Authorization": "Bearer " + token }
        });

        const data = await response.json();
        console.log(data);

        document.getElementById("userEmail").innerText =
            localStorage.getItem("user_email");

        document.getElementById("readinessScore").innerText =
            data.readiness_score + "%";

        const progress = document.getElementById("progressFill");
        progress.style.width = data.readiness_score + "%";

        // Dynamic color
        if (data.readiness_score >= 80) progress.style.background = "#16a34a";
        else if (data.readiness_score >= 60) progress.style.background = "#eab308";
        else progress.style.background = "#dc2626";

        document.getElementById("attendance").innerText = data.attendance + "%";
        document.getElementById("marks").innerText = data.marks;
        document.getElementById("mock").innerText = data.mock_score;
        document.getElementById("skills").innerText = data.skills_score;

        // Status
        const statusEl = document.getElementById("status");
        statusEl.innerText = data.status;
        applyStatusStyle(statusEl, data.status);

        // Risk
        const riskEl = document.getElementById("risk");
        riskEl.innerText = data.risk_level;
        applyRiskStyle(riskEl, data.risk_level);

        document.getElementById("placement").innerText =
            data.placement_status || "Not Available";

        renderChart(data);
        renderInsights(data);

    } catch (e) {
        console.error(e);
    }

    // Leaderboard
    fetch("/top-students", {
        headers: { "Authorization": "Bearer " + token }
    })
    .then(res => res.json())
    .then(data => {
        const list = document.getElementById("topStudents");
        list.innerHTML = "";

        data.forEach((student, i) => {
            const li = document.createElement("li");
            const medal = ["🥇","🥈","🥉"][i] || "";

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

/* Status */
function applyStatusStyle(el, status) {
    el.className = "";

    if (status === "Excellent") el.classList.add("green");
    else if (status === "Moderate") el.classList.add("yellow");
    else el.classList.add("red");
}

/* Risk */
function applyRiskStyle(el, risk) {
    el.className = "";

    if (risk === "Safe") el.classList.add("green");
    else if (risk === "Warning") el.classList.add("yellow");
    else el.classList.add("red");
}

/* Chart */
function renderChart(data) {
    const ctx = document.getElementById("performanceChart");

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

/* Insights */
function renderInsights(data) {
    const list = document.getElementById("insightsList");
    list.innerHTML = "";

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

/* Theme */
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

/* Logout */
function logout() {
    localStorage.removeItem("token");
    window.location.href = "/";
}