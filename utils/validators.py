def validate_required_fields(data, required_fields):
    missing = []

    for field in required_fields:
        if field not in data or data[field] is None:
            missing.append(field)

    if missing:
        return False, f"Missing fields: {', '.join(missing)}"

    return True, None