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
        document.getElementById("readiness").innerHTML =
            `<strong>Score:</strong> ${data.final_score} <br>
            <strong>Status:</strong> ${data.status} <br>
            <strong>Risk:</strong> ${data.risk_status}`;
    });

    // Top Students
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
            li.innerHTML = `<strong>${student.name}</strong> — ${student.score}`;
            list.appendChild(li);
        });
    });
}


function logout() {
    localStorage.removeItem("token");
    window.location.href = "/";
}