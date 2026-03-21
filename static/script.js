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
        localStorage.setItem("token", data.token);

        // 🔥 ADD THIS (important)
        localStorage.setItem("user_email", email);

        window.location.href = "/dashboard";
    }else {
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

    // 🔥 Temporary dynamic (later backend-based)
    const studentId = 4;  // will replace later

    fetch(`/readiness/${studentId}`, {
        headers: {
            "Authorization": "Bearer " + token
        }
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
    });

    fetch("/top-students", {
        headers: {
            "Authorization": "Bearer " + token
        }
    })
    .then(res => res.json())
    .then(data => {
        const list = document.getElementById("topStudents");
        list.innerHTML = "";

        data.forEach(student => {
            const li = document.createElement("li");
            li.innerHTML = `
                <span style="font-weight: bold;">🏆 ${student.name}</span>
                <span style="float:right;">${student.score}</span>`;
        });
    });
}


function logout() {
    localStorage.removeItem("token");
    window.location.href = "/";
}