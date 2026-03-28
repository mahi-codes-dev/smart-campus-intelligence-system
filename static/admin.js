function getAdminState() {
    if (!window.adminState) {
        window.adminState = {
            users: [],
            subjects: [],
            userSearch: "",
            subjectSearch: "",
            userPage: 1,
            subjectPage: 1,
            pageSize: 5,
            initialized: false,
        };
    }

    return window.adminState;
}

function showAdminMessage(message, type = "success") {
    const card = document.getElementById("adminMessageCard");
    const text = document.getElementById("adminMessageText");

    if (card && text) {
        card.hidden = false;
        card.classList.remove("faculty-message-card--success", "faculty-message-card--error");
        card.classList.add(type === "error" ? "faculty-message-card--error" : "faculty-message-card--success");
        text.innerText = message;
    }

    showToast(message, type);
}

function setAdminLastSync() {
    const now = new Date();
    setText("adminLastSync", now.toLocaleTimeString());
}

function renderAdminTopStudentsByDepartment(groups) {
    const container = document.getElementById("adminTopStudentsByDepartment");
    if (!container) {
        return;
    }

    container.innerHTML = "";

    if (!Array.isArray(groups) || !groups.length) {
        container.innerHTML = '<p class="empty-state">No department toppers available yet.</p>';
        return;
    }

    groups.forEach((group) => {
        const wrapper = document.createElement("div");
        wrapper.className = "profile-row";
        const topStudent = group.students && group.students.length
            ? group.students[0].name + " (" + formatValue(group.students[0].score) + ")"
            : "No students";

        wrapper.innerHTML = `
            <span>${group.department}</span>
            <strong>${topStudent}</strong>
        `;
        container.appendChild(wrapper);
    });
}

function renderAdminLowPerformers(users) {
    const list = document.getElementById("adminLowPerformers");
    if (!list) {
        return;
    }

    list.innerHTML = "";

    if (!Array.isArray(users) || !users.length) {
        const li = document.createElement("li");
        li.innerText = "No low performers right now.";
        list.appendChild(li);
        return;
    }

    users.forEach((user) => {
        const li = document.createElement("li");
        li.innerText = `${user.name} - ${user.department} - Score ${formatValue(user.score)}`;
        list.appendChild(li);
    });
}

function filterAdminUsers() {
    const state = getAdminState();
    const term = state.userSearch.toLowerCase();

    return state.users.filter((user) =>
        [user.name, user.email, user.role]
            .filter(Boolean)
            .some((value) => value.toLowerCase().includes(term))
    );
}

function filterAdminSubjects() {
    const state = getAdminState();
    const term = state.subjectSearch.toLowerCase();

    return state.subjects.filter((subject) =>
        [subject.name, subject.code, subject.department]
            .filter(Boolean)
            .some((value) => value.toLowerCase().includes(term))
    );
}

function paginateItems(items, page, pageSize) {
    const totalPages = Math.max(1, Math.ceil(items.length / pageSize));
    const safePage = Math.min(Math.max(page, 1), totalPages);
    const start = (safePage - 1) * pageSize;

    return {
        items: items.slice(start, start + pageSize),
        page: safePage,
        totalPages,
    };
}

function updatePaginationControls(prefix, page, totalPages, totalItems) {
    setText(prefix + "PageInfo", `Page ${page} of ${totalPages}`);
    setText(prefix + "CountInfo", `${totalItems} total`);

    const prevButton = document.getElementById(prefix + "Prev");
    const nextButton = document.getElementById(prefix + "Next");

    if (prevButton) {
        prevButton.disabled = page <= 1;
    }
    if (nextButton) {
        nextButton.disabled = page >= totalPages;
    }
}

function renderAdminUsers() {
    const state = getAdminState();
    const body = document.getElementById("adminUsersTable");
    if (!body) {
        return;
    }

    const filtered = filterAdminUsers();
    const paginated = paginateItems(filtered, state.userPage, state.pageSize);
    state.userPage = paginated.page;

    body.innerHTML = "";

    if (!filtered.length) {
        const row = document.createElement("tr");
        const cell = document.createElement("td");
        cell.colSpan = 4;
        cell.innerText = "No users found.";
        row.appendChild(cell);
        body.appendChild(row);
        updatePaginationControls("adminUsers", 1, 1, 0);
        return;
    }

    paginated.items.forEach((user) => {
        const row = document.createElement("tr");
        const nameCell = document.createElement("td");
        const emailCell = document.createElement("td");
        const roleCell = document.createElement("td");
        const actionCell = document.createElement("td");
        const actionGroup = document.createElement("div");
        const button = document.createElement("button");

        nameCell.innerText = user.name || "--";
        emailCell.innerText = user.email || "--";
        roleCell.innerText = user.role || "--";

        actionGroup.className = "faculty-action-group";
        button.type = "button";
        button.className = "logout-button faculty-table-button";
        button.innerText = "Delete User";
        button.onclick = () => deleteUser(user.id);
        actionGroup.appendChild(button);
        actionCell.appendChild(actionGroup);

        row.appendChild(nameCell);
        row.appendChild(emailCell);
        row.appendChild(roleCell);
        row.appendChild(actionCell);
        body.appendChild(row);
    });

    updatePaginationControls("adminUsers", paginated.page, paginated.totalPages, filtered.length);
}

function renderAdminSubjects() {
    const state = getAdminState();
    const body = document.getElementById("adminSubjectsTable");
    if (!body) {
        return;
    }

    const filtered = filterAdminSubjects();
    const paginated = paginateItems(filtered, state.subjectPage, state.pageSize);
    state.subjectPage = paginated.page;

    body.innerHTML = "";

    if (!filtered.length) {
        const row = document.createElement("tr");
        const cell = document.createElement("td");
        cell.colSpan = 4;
        cell.innerText = "No subjects found.";
        row.appendChild(cell);
        body.appendChild(row);
        updatePaginationControls("adminSubjects", 1, 1, 0);
        return;
    }

    paginated.items.forEach((subject) => {
        const row = document.createElement("tr");
        const nameCell = document.createElement("td");
        const codeCell = document.createElement("td");
        const departmentCell = document.createElement("td");
        const actionCell = document.createElement("td");
        const actionGroup = document.createElement("div");
        const button = document.createElement("button");

        nameCell.innerText = subject.name || "--";
        codeCell.innerText = subject.code || "--";
        departmentCell.innerText = subject.department || "--";

        actionGroup.className = "faculty-action-group";
        button.type = "button";
        button.className = "logout-button faculty-table-button";
        button.innerText = "Delete Subject";
        button.onclick = () => deleteSubject(subject.id);
        actionGroup.appendChild(button);
        actionCell.appendChild(actionGroup);

        row.appendChild(nameCell);
        row.appendChild(codeCell);
        row.appendChild(departmentCell);
        row.appendChild(actionCell);
        body.appendChild(row);
    });

    updatePaginationControls("adminSubjects", paginated.page, paginated.totalPages, filtered.length);
}

function initializeAdminControls() {
    const state = getAdminState();
    if (state.initialized) {
        return;
    }

    const userSearch = document.getElementById("adminUsersSearch");
    const subjectSearch = document.getElementById("adminSubjectsSearch");
    const userPrev = document.getElementById("adminUsersPrev");
    const userNext = document.getElementById("adminUsersNext");
    const subjectPrev = document.getElementById("adminSubjectsPrev");
    const subjectNext = document.getElementById("adminSubjectsNext");

    if (userSearch) {
        userSearch.addEventListener("input", (event) => {
            state.userSearch = event.target.value.trim();
            state.userPage = 1;
            renderAdminUsers();
        });
    }

    if (subjectSearch) {
        subjectSearch.addEventListener("input", (event) => {
            state.subjectSearch = event.target.value.trim();
            state.subjectPage = 1;
            renderAdminSubjects();
        });
    }

    if (userPrev) {
        userPrev.addEventListener("click", () => {
            state.userPage -= 1;
            renderAdminUsers();
        });
    }

    if (userNext) {
        userNext.addEventListener("click", () => {
            state.userPage += 1;
            renderAdminUsers();
        });
    }

    if (subjectPrev) {
        subjectPrev.addEventListener("click", () => {
            state.subjectPage -= 1;
            renderAdminSubjects();
        });
    }

    if (subjectNext) {
        subjectNext.addEventListener("click", () => {
            state.subjectPage += 1;
            renderAdminSubjects();
        });
    }

    state.initialized = true;
}

async function loadUsers() {
    const body = document.getElementById("adminUsersTable");
    if (!body) {
        return;
    }

    body.innerHTML = `
        <tr>
            <td colspan="4">Loading users...</td>
        </tr>
    `;

    const state = getAdminState();
    state.users = await fetchJson("/admin/users");
    renderAdminUsers();
    return state.users;
}

async function loadAdminSubjects() {
    const body = document.getElementById("adminSubjectsTable");
    if (!body) {
        return [];
    }

    body.innerHTML = `
        <tr>
            <td colspan="4">Loading subjects...</td>
        </tr>
    `;

    const state = getAdminState();
    state.subjects = await fetchJson("/admin/subjects");
    renderAdminSubjects();
    return state.subjects;
}

async function loadAdminDashboard() {
    if (!document.getElementById("adminUsersTable")) {
        return;
    }

    setUser();
    initializeAdminControls();

    try {
        const [stats] = await Promise.all([
            fetchJson("/admin/stats"),
            loadUsers(),
            loadAdminSubjects(),
        ]);

        setText("adminTotalStudents", formatValue(stats.total_students));
        setText("adminTotalFaculty", formatValue(stats.total_faculty));
        setText("adminTotalUsers", formatValue(stats.total_users));
        renderAdminTopStudentsByDepartment(stats.top_students_by_department || []);
        renderAdminLowPerformers(stats.low_performers || []);
        setAdminLastSync();
    } catch (error) {
        console.error(error);
        showAdminMessage(error.message || "Unable to load admin dashboard.", "error");
    }
}

async function submitAdminSubject(event) {
    event.preventDefault();

    try {
        const nameInput = document.getElementById("adminSubjectName");
        const codeInput = document.getElementById("adminSubjectCode");
        const departmentInput = document.getElementById("adminSubjectDepartment");
        const name = nameInput ? nameInput.value.trim() : "";
        const code = codeInput ? codeInput.value.trim() : "";
        const department = departmentInput ? departmentInput.value.trim() : "";

        if (!name || !code || !department) {
            throw new Error("Subject name, code, and department are required.");
        }

        const data = await fetchJson("/admin/subject", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ name, code, department }),
        });

        if (nameInput) {
            nameInput.value = "";
        }
        if (codeInput) {
            codeInput.value = "";
        }
        if (departmentInput) {
            departmentInput.value = "";
        }

        showAdminMessage(data.message || "Subject added successfully.");
        await loadAdminDashboard();
    } catch (error) {
        console.error(error);
        showAdminMessage(error.message || "Unable to add subject.", "error");
    }
}

async function deleteSubject(id) {
    const confirmed = await confirmAction({
        title: "Delete Subject",
        message: "Delete this subject? Related marks and attendance records will also be removed.",
        confirmText: "Delete Subject",
        danger: true,
    });

    if (!confirmed) {
        return;
    }

    try {
        const data = await fetchJson("/admin/subject/" + id, {
            method: "DELETE",
        });

        showAdminMessage(data.message || "Subject deleted successfully.");
        await loadAdminDashboard();
    } catch (error) {
        console.error(error);
        showAdminMessage(error.message || "Unable to delete subject.", "error");
    }
}

async function deleteUser(id) {
    const confirmed = await confirmAction({
        title: "Delete User",
        message: "Delete this user account? This action cannot be undone.",
        confirmText: "Delete User",
        danger: true,
    });

    if (!confirmed) {
        return;
    }

    try {
        const data = await fetchJson("/admin/user/" + id, {
            method: "DELETE",
        });

        showAdminMessage(data.message || "User deleted successfully.");
        await loadAdminDashboard();
    } catch (error) {
        console.error(error);
        showAdminMessage(error.message || "Unable to delete user.", "error");
    }
}
