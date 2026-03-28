from services.mock_service import get_mock_trend
from services.marks_service import get_subject_wise_marks
from services.prediction_service import predict_placement_from_score
from services.readiness_service import calculate_readiness, get_top_students
from services.student_service import get_student_profile


def _get_status_and_risk(final_score):
    if final_score >= 80:
        return "Excellent", "Safe"
    if final_score >= 60:
        return "Moderate", "Warning"
    return "At Risk", "Critical"


def _build_alerts(attendance, marks, mock_score):
    alerts = []

    if attendance < 75:
        alerts.append({
            "severity": "warning",
            "title": "Attendance Warning",
            "message": "Attendance is below 75%. Lower classroom engagement can reduce placement readiness.",
        })

    if marks < 60:
        alerts.append({
            "severity": "danger",
            "title": "Marks Need Attention",
            "message": "Average marks are below 60. Focus on core subjects to improve academic consistency.",
        })

    if mock_score < 60:
        alerts.append({
            "severity": "warning",
            "title": "Practice Suggestion",
            "message": "Mock score is below 60. Regular practice tests can improve placement performance.",
        })

    return alerts


def _build_smart_insights(attendance, marks, mock_score, skills_score, subject_performance):
    insights = []

    if attendance < 75:
        insights.append(
            "Your attendance is below 75%, and continued absenteeism may reduce placement chances and internal performance."
        )

    if marks < 60:
        insights.append(
            "Your academic average is below 60, so strengthening your weakest subjects should be the top priority this term."
        )

    if mock_score < 60:
        insights.append(
            "Mock performance is currently low, which can affect placement readiness unless aptitude practice becomes more regular."
        )

    if skills_score >= 50 and marks < 60:
        insights.append(
            "Your skill profile is improving, but balancing it with stronger academic marks will make your overall profile more competitive."
        )

    if subject_performance:
        strongest_subject = max(subject_performance, key=lambda item: float(item.get("average_marks") or 0))
        weakest_subject = min(subject_performance, key=lambda item: float(item.get("average_marks") or 0))

        if float(strongest_subject.get("average_marks") or 0) > 0:
            insights.append(
                f"Your strongest subject right now is {strongest_subject.get('subject_name')}, which is a good area to keep building confidence."
            )

        if float(weakest_subject.get("average_marks") or 0) < 60:
            insights.append(
                f"{weakest_subject.get('subject_name')} needs more attention because its average is pulling down your overall academic readiness."
            )

    if not insights:
        insights.append(
            "You are maintaining a balanced performance across academics, attendance, mock tests, and skills."
        )

    return insights[:5]


def _build_performance_breakdown(attendance, marks, mock_score, skills_score):
    metrics = {
        "Attendance": attendance,
        "Marks": marks,
        "Mock Tests": mock_score,
        "Skills": skills_score,
    }

    return {
        "strength": max(metrics, key=metrics.get),
        "weakness": min(metrics, key=metrics.get),
    }


def _build_profile_summary(profile, readiness_score, status, subject_performance):
    strongest_subject = None
    weakest_subject = None

    if subject_performance:
        strongest_subject = max(subject_performance, key=lambda item: float(item.get("average_marks") or 0))
        weakest_subject = min(subject_performance, key=lambda item: float(item.get("average_marks") or 0))

    return {
        "name": profile.get("name") if profile else "--",
        "email": profile.get("email") if profile else "--",
        "department": profile.get("department") if profile else "--",
        "readiness_score": readiness_score,
        "status": status,
        "best_subject": strongest_subject.get("subject_name") if strongest_subject else None,
        "weakest_subject": weakest_subject.get("subject_name") if weakest_subject else None,
    }


def get_student_dashboard_data(student_id):
    readiness = calculate_readiness(student_id)
    profile = get_student_profile(student_id)
    subject_performance = get_subject_wise_marks(student_id)

    attendance = float(readiness["attendance"])
    marks = float(readiness["marks"])
    mock_score = float(readiness["mock_score"])
    skills_score = float(readiness["skills_score"])
    skills_count = int(readiness.get("skills_count", round(skills_score / 10)))
    final_score = float(readiness["final_score"])

    status, risk_level = _get_status_and_risk(final_score)
    trend = get_mock_trend(student_id)
    alerts = _build_alerts(attendance, marks, mock_score)
    insights = _build_smart_insights(attendance, marks, mock_score, skills_score, subject_performance)
    breakdown = _build_performance_breakdown(attendance, marks, mock_score, skills_score)
    prediction = predict_placement_from_score(
        student_id,
        final_score,
        metrics={
            "attendance": attendance,
            "marks": marks,
            "mock_score": mock_score,
            "skills_score": skills_score,
        },
    )

    return {
        "attendance": round(attendance, 2),
        "marks": round(marks, 2),
        "mock_score": round(mock_score, 2),
        "skills_score": round(skills_score, 2),
        "skills_count": skills_count,
        "readiness_score": round(final_score, 2),
        "status": status,
        "risk_level": risk_level,
        "trend": trend,
        "alerts": alerts,
        "insights": insights,
        "strength": breakdown["strength"],
        "weakness": breakdown["weakness"],
        "performance_breakdown": breakdown,
        "placement_status": prediction["placement_status"],
        "placement_reasons": prediction["reasons"],
        "profile": profile,
        "profile_summary": _build_profile_summary(profile, round(final_score, 2), status, subject_performance),
        "subject_performance": subject_performance,
        "top_students": get_top_students(),
    }
