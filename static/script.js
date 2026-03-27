/* ================= NAVIGATION ================= */

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