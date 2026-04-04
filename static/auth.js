// ================= HELPER FUNCTIONS =================

/**
 * Toggle password visibility
 */
function togglePassword(element) {
    const input = element.previousElementSibling;
    if (input.type === "password") {
        input.type = "text";
        element.classList.remove("fa-eye");
        element.classList.add("fa-eye-slash");
    } else {
        input.type = "password";
        element.classList.remove("fa-eye-slash");
        element.classList.add("fa-eye");
    }
}

/**
 * Validate email format
 */
function isValidEmail(email) {
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    return emailRegex.test(email);
}

/**
 * Validate password strength
 */
function isStrongPassword(password) {
    return password.length >= 6;
}

/**
 * Clear all error messages
 */
function clearErrors() {
    document.querySelectorAll('.error-message').forEach(el => el.textContent = '');
}

/**
 * Display error message
 */
function showError(elementId, message) {
    const element = document.getElementById(elementId);
    if (element) {
        element.textContent = message;
    }
}

/**
 * Show/hide message with animation
 */
function showMessage(message, type = 'error') {
    const messageEl = document.getElementById('message');
    if (!messageEl) return;

    messageEl.textContent = message;
    messageEl.className = `message ${type}`;
    messageEl.style.display = 'block';

    // Scroll into view
    messageEl.scrollIntoView({ behavior: 'smooth', block: 'nearest' });

    // Auto hide success messages
    if (type === 'success') {
        setTimeout(() => {
            messageEl.className = 'message';
            messageEl.style.display = 'none';
        }, 4000);
    }
}

/**
 * Get selected role option
 */
function getSelectedRoleOption() {
    const roleSelect = document.getElementById("role");
    return roleSelect ? roleSelect.options[roleSelect.selectedIndex] : null;
}

function populateRegistrationDepartments(departments) {
    const departmentSelect = document.getElementById("department");
    if (!departmentSelect) {
        return;
    }

    departmentSelect.innerHTML = '<option value="">Select your department</option>';

    (departments || []).forEach((department) => {
        const option = document.createElement("option");
        option.value = department;
        option.innerText = department;
        departmentSelect.appendChild(option);
    });

    if (!(departments || []).length) {
        const option = document.createElement("option");
        option.value = "";
        option.innerText = "No departments available yet";
        departmentSelect.appendChild(option);
    }
}

/**
 * Toggle department field visibility
 */
function toggleDepartmentField() {
    const departmentField = document.getElementById("departmentField");
    const departmentInput = document.getElementById("department");
    const rollNumberField = document.getElementById("rollNumberField");
    const rollNumberInput = document.getElementById("rollNumber");
    const selectedRole = getSelectedRoleOption();
    const isStudent = (selectedRole?.dataset.roleName || "").toLowerCase() === "student";

    if (departmentField) {
        departmentField.style.display = isStudent ? 'block' : 'none';
    }

    if (rollNumberField) {
        rollNumberField.style.display = isStudent ? 'block' : 'none';
    }

    if (departmentInput) {
        if (isStudent) {
            departmentInput.disabled = false;
        } else {
            departmentInput.value = "";
            departmentInput.disabled = true;
        }
    }

    if (rollNumberInput) {
        if (isStudent) {
            rollNumberInput.placeholder = "Enter your student roll number";
        } else {
            rollNumberInput.value = "";
        }
    }
}

// ================= REGISTRATION =================

/**
 * Load registration form with available roles
 */
async function loadRegistrationForm() {
    const roleSelect = document.getElementById("role");
    if (!roleSelect) return;

    try {
        const [roles, departments] = await Promise.all([
            fetchJson("/auth/roles"),
            fetchJson("/auth/departments"),
        ]);
        roleSelect.innerHTML = '<option value="">Choose your role...</option>';

        roles.forEach((role) => {
            const option = document.createElement("option");
            option.value = role.id;
            option.dataset.roleName = role.name;
            option.innerText = role.name.charAt(0).toUpperCase() + role.name.slice(1);
            roleSelect.appendChild(option);
        });

        populateRegistrationDepartments(departments);
        roleSelect.removeEventListener("change", toggleDepartmentField);
        roleSelect.addEventListener("change", toggleDepartmentField);
        toggleDepartmentField();
    } catch (error) {
        console.error(error);
        showMessage(error.message || "Unable to load registration roles.", "error");
    }
}

/**
 * Validate registration form
 */
function validateRegistration() {
    clearErrors();

    const name = document.getElementById("name").value.trim();
    const email = document.getElementById("email").value.trim();
    const password = document.getElementById("password").value;
    const role = document.getElementById("role").value;
    const terms = document.getElementById("terms").checked;
    const departmentInput = document.getElementById("department");
    const department = departmentInput ? departmentInput.value.trim() : "";
    const rollNumberInput = document.getElementById("rollNumber");
    const rollNumber = rollNumberInput ? rollNumberInput.value.trim() : "";
    const roleOption = getSelectedRoleOption();
    const roleName = (roleOption?.dataset.roleName || "").toLowerCase();

    let isValid = true;

    // Validate name
    if (!name) {
        showError("nameError", "Full name is required");
        isValid = false;
    } else if (name.length < 2) {
        showError("nameError", "Name must be at least 2 characters");
        isValid = false;
    }

    // Validate email
    if (!email) {
        showError("emailError", "Email is required");
        isValid = false;
    } else if (!isValidEmail(email)) {
        showError("emailError", "Please enter a valid email address");
        isValid = false;
    }

    // Validate password
    if (!password) {
        showError("passwordError", "Password is required");
        isValid = false;
    } else if (!isStrongPassword(password)) {
        showError("passwordError", "Password must be at least 6 characters");
        isValid = false;
    }

    // Validate role
    if (!role) {
        showError("roleError", "Please select a role");
        isValid = false;
    }

    // Validate department for students
    if (roleName === "student" && !department) {
        showError("departmentError", "Department is required for students");
        isValid = false;
    }

    if (roleName === "student" && !rollNumber) {
        showError("rollNumberError", "Roll number is required for students");
        isValid = false;
    }

    // Validate terms
    if (!terms) {
        showError("termsError", "You must accept the terms and conditions");
        isValid = false;
    }

    return isValid;
}

/**
 * Register user
 */
async function register() {
    // Validate form
    if (!validateRegistration()) {
        showMessage("Please fix the errors above", "error");
        return;
    }

    const name = document.getElementById("name").value.trim();
    const email = document.getElementById("email").value.trim();
    const password = document.getElementById("password").value;
    const role = document.getElementById("role").value;
    const departmentInput = document.getElementById("department");
    const department = departmentInput ? departmentInput.value.trim() : "";
    const rollNumberInput = document.getElementById("rollNumber");
    const rollNumber = rollNumberInput ? rollNumberInput.value.trim() : "";
    const registerBtn = event.target;

    registerBtn.disabled = true;
    registerBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Creating Account...';

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
                roll_number: rollNumber,
            })
        });

        showMessage("Account created successfully! Redirecting...", "success");
        showToast("Welcome to Smart Campus! 🎓");
        
        setTimeout(() => {
            window.location.href = "/";
        }, 2000);
    } catch (error) {
        console.error(error);
        showMessage(error.message || "Registration failed. Please try again.", "error");
        registerBtn.disabled = false;
        registerBtn.innerHTML = '<span>Create Account</span><i class="fas fa-arrow-right"></i>';
    }
}

// ================= LOGIN =================

/**
 * Validate login form
 */
function validateLogin() {
    clearErrors();

    const email = document.getElementById("email").value.trim();
    const password = document.getElementById("password").value;

    let isValid = true;

    if (!email) {
        showError("emailError", "Email is required");
        isValid = false;
    } else if (!isValidEmail(email)) {
        showError("emailError", "Please enter a valid email address");
        isValid = false;
    }

    if (!password) {
        showError("passwordError", "Password is required");
        isValid = false;
    }

    return isValid;
}

/**
 * Login user
 */
async function login() {
    // Validate form
    if (!validateLogin()) {
        showMessage("Please fill in all fields", "error");
        return;
    }

    const email = document.getElementById("email").value.trim();
    const password = document.getElementById("password").value;
    const rememberMe = document.getElementById("rememberMe")?.checked || false;
    const loginBtn = event.target;

    loginBtn.disabled = true;
    loginBtn.innerHTML = '<span><i class="fas fa-spinner fa-spin"></i> Signing In...</span>';

    try {
        const data = await fetchJson("/auth/login", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ email, password })
        });

        if (!data.token || !data.user) {
            throw new Error(data.error || "Login failed. Please try again.");
        }

        // Store credentials
        localStorage.setItem("token", data.token);
        localStorage.setItem("user_email", data.user.email);
        localStorage.setItem("role_id", data.user.role_id);
        localStorage.setItem("role_name", data.user.role_name || "");
        
        if (rememberMe) {
            localStorage.setItem("remember_email", email);
        }

        showMessage("Login successful! Redirecting...", "success");
        showToast("Welcome back! 👋");
        
        setTimeout(() => {
            window.location.href = data.user.dashboard_path || "/";
        }, 1500);
    } catch (error) {
        console.error(error);
        showMessage(error.message || "Login failed. Please check your credentials.", "error");
        loginBtn.disabled = false;
        loginBtn.innerHTML = '<span>Sign In</span><i class="fas fa-arrow-right"></i>';
    }
}

// ================= PAGE INITIALIZATION =================

/**
 * Initialize login page
 */
function initLoginPage() {
    // Restore remembered email
    const rememberedEmail = localStorage.getItem("remember_email");
    if (rememberedEmail) {
        const emailInput = document.getElementById("email");
        if (emailInput) {
            emailInput.value = rememberedEmail;
            const rememberCheckbox = document.getElementById("rememberMe");
            if (rememberCheckbox) {
                rememberCheckbox.checked = true;
            }
        }
    }

    // Handle Enter key
    const form = document.getElementById("loginForm");
    if (form) {
        form.addEventListener("keypress", (e) => {
            if (e.key === "Enter") {
                login.call({ target: form.querySelector("button") });
            }
        });
    }
}

/**
 * Initialize registration page
 */
function initRegisterPage() {
    loadRegistrationForm();

    // Handle Enter key
    const form = document.getElementById("registerForm");
    if (form) {
        form.addEventListener("keypress", (e) => {
            if (e.key === "Enter") {
                register.call({ target: form.querySelector("button") });
            }
        });
    }
}

// Initialize pages when DOM is ready
if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", () => {
        if (document.getElementById("loginForm")) {
            initLoginPage();
        }
        if (document.getElementById("registerForm")) {
            initRegisterPage();
        }
    });
} else {
    if (document.getElementById("loginForm")) {
        initLoginPage();
    }
    if (document.getElementById("registerForm")) {
        initRegisterPage();
    }
}
