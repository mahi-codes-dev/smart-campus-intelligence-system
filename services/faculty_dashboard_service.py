from services.attendance_service import get_attendance
from services.marks_service import get_marks_by_student, get_subject_wise_marks
from services.mock_service import get_mock_scores, get_mock_trend
from services.readiness_service import get_all_scored_students
from services.student_dashboard_service import get_student_dashboard_data
from services.student_service import get_all_departments, get_student_profile


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
