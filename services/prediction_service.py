
def predict_placement_from_score(student_id,final_score):

    # 🔥 Placement Logic
    if final_score >= 80:
        placement = "Likely Placed"
    elif final_score >= 60:
        placement = "Needs Improvement"
    else:
        placement = "At Risk"

    return {
        "student_id": student_id,
        "final_score": final_score,
        "placement_status": placement
    }