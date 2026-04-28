from auth.auth_middleware import _build_current_user
from services.institution_service import extract_institution_code_from_host, normalize_institution_code


def test_extract_institution_code_from_host_uses_subdomain():
    assert extract_institution_code_from_host("campus-a.smartcampus.com") == "CAMPUS-A"
    assert extract_institution_code_from_host("localhost:5000") is None


def test_build_current_user_preserves_institution_payload():
    user = _build_current_user(
        {
            "user_id": 7,
            "name": "Tenant Admin",
            "role_id": 1,
            "institution_id": 12,
            "institution_code": normalize_institution_code("north"),
            "institution_name": "North Campus",
            "is_super_admin": True,
        }
    )

    assert user["institution_id"] == 12
    assert user["institution_code"] == "NORTH"
    assert user["institution_name"] == "North Campus"
    assert user["is_super_admin"] is True
