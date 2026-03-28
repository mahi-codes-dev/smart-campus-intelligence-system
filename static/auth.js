function getSelectedRoleOption() {
    const roleSelect = document.getElementById("role");
    return roleSelect ? roleSelect.options[roleSelect.selectedIndex] : null;
}

function toggleDepartmentField() {
    const departmentField = document.getElementById("departmentField");
    const departmentInput = document.getElementById("department");
    const selectedRole = getSelectedRoleOption();
    const isStudent = (selectedRole?.dataset.roleName || "").toLowerCase() === "student";

    if (departmentField) {
        departmentField.hidden = !isStudent;
    }

    if (departmentInput) {
        if (isStudent) {
            departmentInput.placeholder = "Enter Department";
        } else {
            departmentInput.value = "";
        }
    }
}

async function loadRegistrationForm() {
    const roleSelect = document.getElementById("role");
    if (!roleSelect) {
        return;
    }

    const message = document.getElementById("message");

    try {
        const roles = await fetchJson("/auth/roles");
        roleSelect.innerHTML = "";

        roles.forEach((role) => {
            const option = document.createElement("option");
            option.value = role.id;
            option.dataset.roleName = role.name;
            option.innerText = role.name;
            roleSelect.appendChild(option);
        });

        roleSelect.removeEventListener("change", toggleDepartmentField);
        roleSelect.addEventListener("change", toggleDepartmentField);
        toggleDepartmentField();
    } catch (error) {
        console.error(error);
        if (message) {
            message.innerText = error.message || "Unable to load registration roles.";
        }
    }
}

async function register() {
    const name = document.getElementById("name").value.trim();
    const email = document.getElementById("email").value.trim();
    const password = document.getElementById("password").value;
    const departmentInput = document.getElementById("department");
    const department = departmentInput ? departmentInput.value.trim() : "";
    const role = document.getElementById("role").value;
    const roleOption = getSelectedRoleOption();
    const roleName = (roleOption?.dataset.roleName || "").toLowerCase();
    const message = document.getElementById("message");

    message.innerText = "Creating account...";

    if (!name || !email || !password || !role) {
        message.innerText = "Name, email, password, and role are required.";
        return;
    }

    if (roleName === "student" && !department) {
        message.innerText = "Department is required for student registration.";
        return;
    }

    try {
        const data = await fetchJson("/auth/register", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
                name,
                email,
                password,
                role_id: parseInt(role, 10),
                department,
            })
        });

        message.innerText = data.message || "Account created successfully.";
        showToast(data.message || "Registration completed.");
        setTimeout(() => window.location.href = "/", 1200);
    } catch (error) {
        console.error(error);
        message.innerText = error.message || "Registration failed.";
        showToast(error.message || "Registration failed.", "error");
    }
}

async function login() {
    const email = document.getElementById("email").value.trim();
    const password = document.getElementById("password").value;
    const message = document.getElementById("message");

    message.innerText = "Logging in...";

    try {
        const data = await fetchJson("/auth/login", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ email, password })
        });

        if (!data.token || !data.user) {
            throw new Error(data.error || "Login failed.");
        }

        localStorage.setItem("token", data.token);
        localStorage.setItem("user_email", data.user.email);
        localStorage.setItem("role_id", data.user.role_id);
        localStorage.setItem("role_name", data.user.role_name || "");
        showToast(data.message || "Login successful.");
        window.location.href = data.user.dashboard_path || "/";
    } catch (error) {
        console.error(error);
        message.innerText = error.message || "Login failed.";
        showToast(error.message || "Login failed.", "error");
    }
}
