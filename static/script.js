function login() {
    const email = document.getElementById("email").value;
    const password = document.getElementById("password").value;

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

            document.getElementById("message").innerText = "Login successful";

            window.location.href = "/dashboard";
        } else {
            document.getElementById("message").innerText = data.error;
        }
    })
    .catch(err => {
        document.getElementById("message").innerText = "Server error";
    });
}

function loadDashboard() {
    const token = localStorage.getItem("token");

    // 🔹 Readiness (use a test student id for now)
    fetch("/readiness/4", {
        headers: {
            "Authorization": "Bearer " + token
        }
    })
    .then(res => res.json())
    .then(data => {
        document.getElementById("readiness").innerText =
            "Score: " + data.final_score +
            " | Status: " + data.status +
            " | Risk: " + data.risk_status;
    });

    // 🔹 Top Students
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
            li.innerText = student.name + " - " + student.score;
            list.appendChild(li);
        });
    });
}