from database import get_db_connection
from services.attendance_service import (
    ensure_attendance_table_consistency,
    get_attendance,
    save_attendance_percentage,
)
from services.marks_service import (
    ensure_marks_table_consistency,
    get_marks_by_student,
    get_subject_wise_marks,
    save_marks,
)
from services.mock_service import get_mock_scores, get_mock_trend
from services.readiness_service import get_all_scored_students
from services.student_dashboard_service import get_student_dashboard_data
from services.student_service import get_all_departments, get_student_profile
from services.subject_service import get_subject_by_id


def calculate_student_dashboard(student_id):
    dashboard = get_student_dashboard_data(student_id)

    return {
        "attendance": dashboard["attendance"],
        "marks": dashboard["marks"],
        "mock_score": dashboard["mock_score"],
        "skills_count": dashboard["skills_count"],
        "final_score": dashboard["readiness_score"],
        "status": dashboard["status"],
        "trend": dashboard["trend"],
        "risk_status": dashboard["risk_level"],
    }


def get_all_students_dashboard(filter_status=None, sort_order=None, search=None, department=None):
    students = get_all_scored_students(
        search=search,
        department=department,
        status=filter_status,
        sort_order=sort_order or "desc",
    )

    results = []
    for student in students:
        results.append({
            "id": student["student_id"],
            "student_id": student["student_id"],
            "name": student["name"],
            "email": student["email"],
            "roll_number": student.get("roll_number"),
            "department": student["department"],
            "attendance": student["attendance"],
            "marks": student["marks"],
            "mock_score": student["mock_score"],
            "skills_count": student["skills_count"],
            "final_score": student["final_score"],
            "status": student["status"],
            "risk_status": student["risk_status"],
            "trend": get_mock_trend(student["student_id"]),
        })

    return results


def get_faculty_dashboard_summary(search=None, department=None, filter_status=None, sort_order=None):
    """
    Get faculty dashboard summary with enhanced insights.
    Includes: total students, average marks, at-risk count, students needing attention.
    """
    students = get_all_students_dashboard(
        filter_status=filter_status,
        sort_order=sort_order,
        search=search,
        department=department,
    )

    total_students = len(students)
    average_marks = round(
        sum(float(student["marks"] or 0) for student in students) / total_students,
        2,
    ) if total_students else 0

    at_risk_students = [
        student for student in students
        if float(student["final_score"] or 0) < 60 or student["risk_status"] == "At Risk"
    ]
    
    # Students needing attention: those with warning status or specific metric issues
    students_needing_attention = [
        student for student in students
        if (float(student["attendance"] or 0) < 75 or 
            float(student["marks"] or 0) < 60 or
            float(student["mock_score"] or 0) < 60)
    ]

    return {
        "summary": {
            "total_students": total_students,
            "average_marks": average_marks,
            "at_risk_count": len(at_risk_students),
            "students_needing_attention_count": len(students_needing_attention),
            "departments": get_all_departments(),
        },
        "at_risk_students": at_risk_students[:10],
        "students_needing_attention": students_needing_attention[:10],
    }


def get_student_detail(student_id):
    dashboard = get_student_dashboard_data(student_id)

    return {
        "profile": get_student_profile(student_id),
        "overview": {
            "attendance": dashboard["attendance"],
            "marks": dashboard["marks"],
            "mock_score": dashboard["mock_score"],
            "readiness_score": dashboard["readiness_score"],
            "status": dashboard["status"],
            "risk_level": dashboard["risk_level"],
        },
        "subject_performance": get_subject_wise_marks(student_id),
        "marks_history": get_marks_by_student(student_id),
        "attendance_history": get_attendance(student_id),
        "mock_scores": get_mock_scores(student_id),
        "placement_reasons": dashboard["placement_reasons"],
        "insights": dashboard["insights"],
        "alerts": dashboard["alerts"],
        "profile_summary": dashboard["profile_summary"],
        "subject_trends": dashboard.get("subject_trends", []),
        "marks_timeline": dashboard.get("marks_timeline", []),
    }


def get_classroom_roster(subject_id, department=None, search=None):
    subject = get_subject_by_id(subject_id)

    if not subject:
        raise ValueError("Subject not found")

    effective_department = (department or "").strip()
    if not effective_department or effective_department.lower() == "all":
        effective_department = subject["department"]

    students = get_all_scored_students(
        search=search,
        department=effective_department,
        sort_order="desc",
    )

    conn = get_db_connection()
    cur = conn.cursor()
    ensure_attendance_table_consistency(conn)
    ensure_marks_table_consistency(conn)

    cur.execute(
        """
        SELECT
            student_id,
            COUNT(*) FILTER (WHERE status = 'Present') * 100.0 / NULLIF(COUNT(*), 0) AS attendance_percentage
        FROM attendance
        WHERE subject_id = %s
        GROUP BY student_id
        """,
        (subject_id,),
    )
    attendance_map = {
        row[0]: round(float(row[1] or 0), 2)
        for row in cur.fetchall()
    }

    cur.execute(
        """
        SELECT DISTINCT ON (student_id)
            student_id,
            marks,
            exam_type
        FROM marks
        WHERE subject_id = %s
        ORDER BY student_id, created_at DESC NULLS LAST, id DESC
        """,
        (subject_id,),
    )
    marks_map = {
        row[0]: {
            "marks": float(row[1]) if row[1] is not None else None,
            "exam_type": row[2],
        }
        for row in cur.fetchall()
    }

    cur.close()
    conn.close()

    roster = []
    for student in students:
        latest_marks = marks_map.get(student["student_id"], {})
        roster.append({
            "student_id": student["student_id"],
            "name": student["name"],
            "email": student["email"],
            "roll_number": student["roll_number"],
            "department": student["department"],
            "attendance_percentage": attendance_map.get(student["student_id"]),
            "latest_marks": latest_marks.get("marks"),
            "latest_exam_type": latest_marks.get("exam_type"),
            "readiness_score": student["final_score"],
            "status": student["status"],
            "risk_status": student["risk_status"],
        })

    attendance_values = [
        row["attendance_percentage"]
        for row in roster
        if row["attendance_percentage"] is not None
    ]
    mark_values = [
        row["latest_marks"]
        for row in roster
        if row["latest_marks"] is not None
    ]

    return {
        "subject": subject,
        "department": effective_department,
        "count": len(roster),
        "summary": {
            "students_with_attendance": len(attendance_values),
            "students_with_marks": len(mark_values),
            "average_attendance": round(sum(attendance_values) / len(attendance_values), 2) if attendance_values else 0,
            "average_marks": round(sum(mark_values) / len(mark_values), 2) if mark_values else 0,
        },
        "roster": roster,
    }


def save_classroom_attendance(subject_id, entries):
    subject = get_subject_by_id(subject_id)

    if not subject:
        raise ValueError("Subject not found")

    saved_count = 0

    for entry in entries or []:
        attendance_value = entry.get("attendance_percentage")
        if attendance_value in (None, ""):
            continue

        save_attendance_percentage(
            int(entry["student_id"]),
            int(subject_id),
            attendance_value,
        )
        saved_count += 1

    if saved_count == 0:
        raise ValueError("Provide at least one attendance value to save")

    return {
        "subject": subject,
        "saved_count": saved_count,
    }


def save_classroom_marks(subject_id, exam_type, entries):
    subject = get_subject_by_id(subject_id)

    if not subject:
        raise ValueError("Subject not found")

    cleaned_exam_type = (exam_type or "").strip()
    if not cleaned_exam_type:
        raise ValueError("Exam type is required for class marks entry")

    saved_count = 0

    for entry in entries or []:
        marks_value = entry.get("marks")
        if marks_value in (None, ""):
            continue

        save_marks(
            int(entry["student_id"]),
            int(subject_id),
            marks_value,
            cleaned_exam_type,
        )
        saved_count += 1

    if saved_count == 0:
        raise ValueError("Provide at least one marks value to save")

    return {
        "subject": subject,
        "exam_type": cleaned_exam_type,
        "saved_count": saved_count,
    }
