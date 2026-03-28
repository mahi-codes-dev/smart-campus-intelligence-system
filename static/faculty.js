function getFacultyState() {
    if (!window.facultyState) {
        window.facultyState = {
            students: [],
            subjects: [],
            selectedStudentId: null,
        };
    }

    return window.facultyState;
}

function focusFacultySection(sectionId) {
    const section = document.getElementById(sectionId);
    if (section) {
        section.scrollIntoView({ behavior: "smooth", block: "start" });
    }
}

function setFacultyActionState(text) {
    setText("facultyActionState", text || "Waiting");
}

function showFacultyMessage(message, type = "success") {
    const card = document.getElementById("facultyMessageCard");
    const text = document.getElementById("facultyMessageText");

    if (card && text) {
        card.hidden = false;
        card.classList.remove("faculty-message-card--success", "faculty-message-card--error");
        card.classList.add(type === "error" ? "faculty-message-card--error" : "faculty-message-card--success");
        text.innerText = message;
    }

    setFacultyActionState(type === "error" ? "Failed" : "Saved");
    showToast(message, type);
}

function populateFacultySubjectOptions(subjects) {
    ["attendanceSubject", "marksSubject"].forEach((selectId) => {
        const select = document.getElementById(selectId);
        if (!select) {
            return;
        }

        select.innerHTML = "";

        const placeholder = document.createElement("option");
        placeholder.value = "";
        placeholder.innerText = subjects.length ? "Select Subject" : "No Subjects Available";
        select.appendChild(placeholder);

        subjects.forEach((subject) => {
            const option = document.createElement("option");
            option.value = subject.id;
            option.innerText = subject.name + " (" + subject.code + ")";
            select.appendChild(option);
        });
    });
}

function setFacultyStudentSelection(student) {
    const state = getFacultyState();
    state.selectedStudentId = student ? student.student_id : null;

    const label = student ? student.name + " (" + student.department + ")" : "None";
    setText("facultySelectedStudent", label);

    const mappings = [
        ["attendanceStudent", "attendanceStudentId"],
        ["marksStudent", "marksStudentId"],
        ["mockStudent", "mockStudentId"],
    ];

    mappings.forEach(([nameId, hiddenId]) => {
        const input = document.getElementById(nameId);
        const hidden = document.getElementById(hiddenId);

        if (input) {
            input.value = student ? student.name + " - " + student.email : "";
        }

        if (hidden) {
            hidden.value = student ? student.student_id : "";
        }
    });
}

function renderFacultyStudents(students) {
    const body = document.getElementById("facultyStudentsTable");
    if (!body) {
        return;
    }

    body.innerHTML = "";

    if (!students.length) {
        const row = document.createElement("tr");
        const cell = document.createElement("td");
        cell.colSpan = 4;
        cell.innerText = "No students found.";
        row.appendChild(cell);
        body.appendChild(row);
        return;
    }

    students.forEach((student) => {
        const row = document.createElement("tr");
        const nameCell = document.createElement("td");
        const emailCell = document.createElement("td");
        const departmentCell = document.createElement("td");
        const actionCell = document.createElement("td");
        const actionGroup = document.createElement("div");

        nameCell.innerText = student.name || "--";
        emailCell.innerText = student.email || "--";
        departmentCell.innerText = student.department || "--";

        actionGroup.className = "faculty-action-group";

        [
            ["Manage Attendance", "attendanceSection"],
            ["Manage Marks", "marksSection"],
            ["Manage Mock Tests", "mockSection"],
        ].forEach(([label, sectionId]) => {
            const button = document.createElement("button");
            button.type = "button";
            button.className = "primary-button faculty-table-button";
            button.innerText = label;
            button.onclick = () => selectFacultyStudent(student.student_id, sectionId);
            actionGroup.appendChild(button);
        });

        actionCell.appendChild(actionGroup);
        row.appendChild(nameCell);
        row.appendChild(emailCell);
        row.appendChild(departmentCell);
        row.appendChild(actionCell);
        body.appendChild(row);
    });
}

function renderFacultyDetailSummary(detail) {
    const list = document.getElementById("facultyDetailSummary");
    if (!list) {
        return;
    }

    list.innerHTML = "";

    [
        "Attendance: " + formatPercent(detail.overview?.attendance),
        "Average Marks: " + formatValue(detail.overview?.marks),
        "Mock Score: " + formatValue(detail.overview?.mock_score),
        "Status: " + (detail.overview?.status || "--"),
    ].forEach((text) => {
        const li = document.createElement("li");
        li.innerText = text;
        list.appendChild(li);
    });
}

function renderFacultyDetailList(items, listId, formatter, emptyText) {
    const list = document.getElementById(listId);
    if (!list) {
        return;
    }

    list.innerHTML = "";

    if (!Array.isArray(items) || !items.length) {
        const li = document.createElement("li");
        li.innerText = emptyText;
        list.appendChild(li);
        return;
    }

    items.forEach((item) => {
        const li = document.createElement("li");
        li.innerText = formatter(item);
        list.appendChild(li);
    });
}

async function loadFacultyStudentDetail(studentId) {
    try {
        const detail = await fetchJson("/faculty/student/" + studentId);
        const profile = detail.profile || {};

        setText("facultyDetailName", profile.name || "--");
        setText("facultyDetailEmail", profile.email || "--");
        setText("facultyDetailDepartment", profile.department || "--");
        setText("facultyDetailReadiness", formatPercent(detail.overview?.readiness_score || 0));
        setText("facultyDetailStatus", detail.overview?.status || "Loaded");

        renderFacultyDetailSummary(detail);
        renderSubjectPerformance(detail.subject_performance || [], "facultyDetailMarksTable");
        renderFacultyDetailList(
            detail.attendance_history || [],
            "facultyDetailAttendanceList",
            (item) => `${item.subject} - ${item.status} - ${item.date}`,
            "No attendance records available."
        );
        renderFacultyDetailList(
            detail.mock_scores || [],
            "facultyDetailMockList",
            (item) => `${item.test_name}: ${formatValue(item.score)} (${item.date || "No date"})`,
            "No mock scores available."
        );
    } catch (error) {
        console.error(error);
        showFacultyMessage(error.message || "Unable to load student detail.", "error");
    }
}

function selectFacultyStudent(studentId, sectionId) {
    const state = getFacultyState();
    const student = state.students.find((item) => Number(item.student_id) === Number(studentId));

    if (!student) {
        return;
    }

    setFacultyStudentSelection(student);
    setFacultyActionState("Student Selected");
    loadFacultyStudentDetail(student.student_id);

    if (sectionId) {
        focusFacultySection(sectionId);
    }
}

async function loadFacultyDashboard() {
    if (!document.getElementById("facultyStudentsTable")) {
        return;
    }

    setUser();

    try {
        const [students, subjects] = await Promise.all([
            fetchJson("/faculty/dashboard"),
            fetchJson("/subjects"),
        ]);
        const state = getFacultyState();

        state.students = Array.isArray(students) ? students : [];
        state.subjects = Array.isArray(subjects) ? subjects : [];

        setText("facultyStudentCount", state.students.length);
        setText("facultySubjectCount", state.subjects.length);

        populateFacultySubjectOptions(state.subjects);
        renderFacultyStudents(state.students);

        const selected = state.students.find(
            (student) => Number(student.student_id) === Number(state.selectedStudentId)
        );

        if (selected) {
            setFacultyStudentSelection(selected);
            loadFacultyStudentDetail(selected.student_id);
        } else if (state.students.length) {
            setFacultyStudentSelection(state.students[0]);
            loadFacultyStudentDetail(state.students[0].student_id);
        } else {
            setFacultyStudentSelection(null);
        }

        setFacultyActionState("Ready");
    } catch (error) {
        console.error(error);
        showFacultyMessage(error.message || "Unable to load faculty dashboard.", "error");
    }
}

function getSelectedFacultyStudentId(hiddenInputId) {
    const value = document.getElementById(hiddenInputId)?.value;

    if (!value) {
        throw new Error("Select a student from the table first.");
    }

    return Number(value);
}

async function submitAttendance(event) {
    event.preventDefault();

    try {
        const studentId = getSelectedFacultyStudentId("attendanceStudentId");
        const subjectId = Number(document.getElementById("attendanceSubject")?.value || 0);
        const attendancePercentage = Number(document.getElementById("attendancePercentage")?.value || "");

        if (!subjectId) {
            throw new Error("Select a subject for attendance.");
        }

        if (Number.isNaN(attendancePercentage) || attendancePercentage < 0 || attendancePercentage > 100) {
            throw new Error("Enter attendance percentage between 0 and 100.");
        }

        const data = await fetchJson("/faculty/attendance", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
                student_id: studentId,
                subject_id: subjectId,
                attendance_percentage: attendancePercentage,
            }),
        });

        document.getElementById("attendancePercentage").value = "";
        await loadFacultyDashboard();
        showFacultyMessage(data.message || "Attendance saved successfully.");
    } catch (error) {
        console.error(error);
        showFacultyMessage(error.message || "Unable to save attendance.", "error");
    }
}

async function submitMarks(event) {
    event.preventDefault();

    try {
        const studentId = getSelectedFacultyStudentId("marksStudentId");
        const subjectId = Number(document.getElementById("marksSubject")?.value || 0);
        const marks = Number(document.getElementById("marksValue")?.value || "");
        const examTypeInput = document.getElementById("marksExamType");
        const examType = examTypeInput && examTypeInput.value.trim() ? examTypeInput.value.trim() : null;

        if (!subjectId) {
            throw new Error("Select a subject for marks.");
        }

        if (Number.isNaN(marks) || marks < 0 || marks > 100) {
            throw new Error("Enter marks between 0 and 100.");
        }

        const data = await fetchJson("/marks", {
            method: "PUT",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
                student_id: studentId,
                subject_id: subjectId,
                marks,
                exam_type: examType,
            }),
        });

        document.getElementById("marksValue").value = "";
        if (examTypeInput) {
            examTypeInput.value = "";
        }
        await loadFacultyDashboard();
        showFacultyMessage(data.message || "Marks saved successfully.");
    } catch (error) {
        console.error(error);
        showFacultyMessage(error.message || "Unable to save marks.", "error");
    }
}

async function submitMockTest(event) {
    event.preventDefault();

    try {
        const studentId = getSelectedFacultyStudentId("mockStudentId");
        const testNameInput = document.getElementById("mockTestName");
        const scoreInput = document.getElementById("mockScore");
        const testName = testNameInput ? testNameInput.value.trim() : "";
        const score = Number(scoreInput?.value || "");

        if (!testName) {
            throw new Error("Enter a mock test name.");
        }

        if (Number.isNaN(score) || score < 0 || score > 100) {
            throw new Error("Enter a mock score between 0 and 100.");
        }

        const data = await fetchJson("/mock-tests", {
            method: "PUT",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
                student_id: studentId,
                test_name: testName,
                score,
            }),
        });

        if (testNameInput) {
            testNameInput.value = "";
        }
        if (scoreInput) {
            scoreInput.value = "";
        }
        await loadFacultyDashboard();
        showFacultyMessage(data.message || "Mock test saved successfully.");
    } catch (error) {
        console.error(error);
        showFacultyMessage(error.message || "Unable to save mock test.", "error");
    }
}
