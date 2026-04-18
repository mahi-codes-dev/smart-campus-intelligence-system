def _auth_header(token):
    return {"Authorization": f"Bearer {token}"}


def test_admin_can_fetch_students(client, mock_db, monkeypatch, valid_admin_token):
    import routes.student_routes as student_routes

    expected_students = [
        {
            "id": 1,
            "name": "Asha Rao",
            "email": "asha@example.com",
            "roll_number": "CSE001",
            "department": "CSE",
        }
    ]
    monkeypatch.setattr(student_routes, "fetch_all_students", lambda: expected_students)

    response = client.get("/students", headers=_auth_header(valid_admin_token))

    assert response.status_code == 200
    assert response.get_json() == expected_students


def test_student_dashboard_returns_current_student_data(client, mock_db, monkeypatch, valid_student_token):
    import routes.student_routes as student_routes

    monkeypatch.setattr(
        student_routes,
        "get_student_record_by_user_id",
        lambda user_id: {
            "id": 7,
            "user_id": user_id,
            "name": "Test Student",
            "email": "student@example.com",
            "roll_number": "CSE007",
            "department": "CSE",
        },
    )
    monkeypatch.setattr(
        student_routes,
        "get_student_dashboard_data",
        lambda student_id: {
            "student_id": student_id,
            "readiness_score": 82.5,
            "status": "Excellent",
        },
    )

    response = client.get("/student/dashboard", headers=_auth_header(valid_student_token))

    assert response.status_code == 200
    assert response.get_json()["readiness_score"] == 82.5


def test_student_dashboard_returns_404_when_student_record_missing(
    client,
    mock_db,
    monkeypatch,
    valid_student_token,
):
    import routes.student_routes as student_routes

    monkeypatch.setattr(student_routes, "get_student_record_by_user_id", lambda user_id: None)

    response = client.get("/student/dashboard", headers=_auth_header(valid_student_token))

    assert response.status_code == 404
    assert response.get_json()["error"] == "Student not found"
