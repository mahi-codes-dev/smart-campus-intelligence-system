from services.mock_service import get_mock_trend
from services.prediction_service import predict_placement_from_score
from services.readiness_service import calculate_readiness
from services.student_service import get_student_profile


def _get_status_and_risk(final_score):
    if final_score >= 80:
        return "Excellent", "Safe"
    if final_score >= 60:
        return "Moderate", "Warning"
    return "At Risk", "Critical"


def _build_smart_insights(attendance, marks, mock_score, skills_score):
    insights = []

    if attendance < 75:
        insights.append(
            "Attendance is below 75%, so improving class participation will reduce academic risk."
        )

    if marks < 60:
        insights.append(
            "Average marks are below 60, so strengthening core academic subjects should be a priority."
        )

    if mock_score < 60:
        insights.append(
            "Mock performance is below 60, so regular aptitude practice can improve placement readiness."
        )

    if skills_score >= 70 and marks < 60:
        insights.append(
            "Your skill profile is strong, but balancing it with better academic performance will make your profile stronger."
        )

    if not insights:
        insights.append(
            "You are maintaining a balanced performance across academics, attendance, mock tests, and skills."
        )

    return insights


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


def get_student_dashboard_data(student_id):
    readiness = calculate_readiness(student_id)

    attendance = float(readiness["attendance"])
    marks = float(readiness["marks"])
    mock_score = float(readiness["mock_score"])
    skills_score = float(readiness["skills_score"])
    skills_count = int(readiness.get("skills_count", round(skills_score / 10)))
    final_score = float(readiness["final_score"])

    status, risk_level = _get_status_and_risk(final_score)
    trend = get_mock_trend(student_id)
    insights = _build_smart_insights(attendance, marks, mock_score, skills_score)
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
        "insights": insights,
        "strength": breakdown["strength"],
        "weakness": breakdown["weakness"],
        "performance_breakdown": breakdown,
        "placement_status": prediction["placement_status"],
        "placement_reasons": prediction["reasons"],
        "profile": get_student_profile(student_id),
    }
