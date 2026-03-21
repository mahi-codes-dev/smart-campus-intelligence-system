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
            message.innerText = "Login successful ✅";
            window.location.href = "/dashboard";
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

    // Readiness
    fetch("/readiness/4", {
        headers: {
            "Authorization": "Bearer " + token
        }
    })
    .then(res => res.json())
    .then(data => {
    document.getElementById("readinessScore").innerText = data.final_score;
    document.getElementById("status").innerText = data.status;

    const riskElement = document.getElementById("risk");
    riskElement.innerText = data.risk_status;

    if (data.risk_status === "At Risk") {
        riskElement.className = "danger";
    } else {
        riskElement.className = "success";
    }
});

    // Top Students
    fetch("/top-students", {
        headers: {
            "Authorization": "Bearer " + token
        }
    })
    .then(res => res.json())
    .then(data => {
    document.getElementById("readinessScore").innerText = data.final_score;
    document.getElementById("status").innerText = data.status;

    const riskElement = document.getElementById("risk");
    riskElement.innerText = data.risk_status;

    if (data.risk_status === "At Risk") {
        riskElement.className = "danger";
    } else {
        riskElement.className = "success";
    }
});
}


function logout() {
    localStorage.removeItem("token");
    window.location.href = "/";
}