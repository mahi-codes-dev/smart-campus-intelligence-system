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

            // ✅ Store user info
            localStorage.setItem("user_email", data.user.email);
            localStorage.setItem("role_id", data.user.role_id);

            // 🔥 ROLE BASED REDIRECT
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

function loadDashboard() {
    const token = localStorage.getItem("token");

    if (!token) {
        window.location.href = "/";
        return;
    }

    const studentId = 4;

    fetch(`/readiness/${studentId}`, {
        headers: { "Authorization": "Bearer " + token }
    })
    .then(res => res.json())
    .then(data => {

        document.getElementById("readinessScore").innerText = data.final_score;
        document.getElementById("status").innerText = data.status;
        document.getElementById("userEmail").innerText = localStorage.getItem("user_email");

        const risk = document.getElementById("risk");
        risk.innerText = data.risk_status;
        risk.className = data.risk_status === "At Risk" ? "danger" : "success";

        document.getElementById("progressFill").style.width = data.final_score + "%";

        // 🔥 CHART
        const ctx = document.getElementById("performanceChart");

        if (window.myChart) {
            window.myChart.destroy();
        }

        window.myChart = new Chart(ctx, {
            type: "bar",
            data: {
                labels: ["Attendance", "Marks", "Skills", "Mock"],
                datasets: [{
                    label: "Performance",
                    data: [
                        data.attendance,
                        data.marks,
                        data.skills_score,
                        data.mock_score
                    ]
                }]
            }
        });
    });

    fetch("/top-students", {
        headers: { "Authorization": "Bearer " + token }
    })
    .then(res => res.json())
    .then(data => {
        const list = document.getElementById("topStudents");
        list.innerHTML = "";

        data.forEach((student, index) => {
            const li = document.createElement("li");

            let medal = "";
            if (index === 0) medal = "🥇";
            else if (index === 1) medal = "🥈";
            else if (index === 2) medal = "🥉";

            li.innerHTML = `
                <div class="leaderboard-item">
                    <span><b>${medal} ${student.name}</b></span>
                    <span class="score">${student.score}</span>
                </div>
            `;

            list.appendChild(li);
        });
    });
}

function logout() {
    localStorage.removeItem("token");
    window.location.href = "/";
}