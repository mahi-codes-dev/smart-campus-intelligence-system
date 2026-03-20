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