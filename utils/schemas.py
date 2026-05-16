"""
Marshmallow schemas for request validation, response serialization, and pagination.
Provides reusable schemas for consistent API request/response handling.
"""

from marshmallow import Schema, fields, validate, ValidationError, pre_load
from datetime import datetime
import bleach


# ============================================================================
# PAGINATION SCHEMAS
# ============================================================================

class PaginationQuerySchema(Schema):
    """Schema for pagination query parameters."""
    page = fields.Int(
        load_default=1,
        validate=validate.Range(min=1),
        description="Page number (1-indexed)"
    )
    per_page = fields.Int(
        load_default=20,
        validate=validate.Range(min=1, max=100),
        description="Items per page (1-100)"
    )
    sort_by = fields.Str(
        load_default="created_at",
        description="Field to sort by"
    )
    sort_order = fields.Str(
        load_default="desc",
        validate=validate.OneOf(["asc", "desc"]),
        description="Sort order (asc or desc)"
    )

    class Meta:
        """Meta options."""
        ordered = True


class PaginatedResponseSchema(Schema):
    """Generic schema for paginated responses."""
    status = fields.Str(required=True)
    data = fields.List(fields.Dict(), required=True)
    meta = fields.Dict(default=dict)
    pagination = fields.Dict(
        keys=fields.Str(),
        values=fields.Int(),
        default=dict
    )
    timestamp = fields.DateTime(default=datetime.utcnow)

    class Meta:
        """Meta options."""
        ordered = True


# ============================================================================
# SANITIZATION UTILITIES
# ============================================================================

class SanitizedString(fields.Str):
    """String field that automatically sanitizes HTML."""
    def __init__(self, max_length=None, allowed_tags=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.max_length = max_length
        self.allowed_tags = allowed_tags or []

    def _deserialize(self, value, attr, data, **kwargs):
        value = super()._deserialize(value, attr, data, **kwargs)
        if value:
            # Clean HTML and limit length
            sanitized = bleach.clean(
                value,
                tags=self.allowed_tags,
                strip=True
            )
            if self.max_length:
                sanitized = sanitized[:self.max_length]
            return sanitized.strip()
        return value


class SanitizedEmail(fields.Email):
    """Email field that sanitizes input."""
    def _deserialize(self, value, attr, data, **kwargs):
        value = super()._deserialize(value, attr, data, **kwargs)
        return value.lower().strip() if value else value


# ============================================================================
# COMMON REQUEST SCHEMAS
# ============================================================================

class StudentCreateSchema(Schema):
    """Schema for creating a student."""
    name = SanitizedString(
        required=True,
        max_length=200,
        validate=validate.Length(min=2, max=200),
        error_messages={"required": "Name is required", "invalid": "Name must be a string"}
    )
    email = SanitizedEmail(
        required=True,
        error_messages={"required": "Email is required", "invalid": "Invalid email format"}
    )
    department = SanitizedString(
        required=True,
        max_length=100,
        validate=validate.Length(min=2, max=100),
        error_messages={"required": "Department is required"}
    )
    roll_number = SanitizedString(
        required=True,
        max_length=50,
        validate=validate.Length(min=1, max=50),
        error_messages={"required": "Roll number is required"}
    )
    phone = fields.Str(
        required=False,
        allow_none=True,
        validate=validate.Length(max=20)
    )
    date_of_birth = fields.Date(
        required=False,
        allow_none=True,
        format="%Y-%m-%d"
    )

    class Meta:
        """Meta options."""
        ordered = True


class StudentUpdateSchema(Schema):
    """Schema for updating a student."""
    name = SanitizedString(
        required=False,
        max_length=200,
        validate=validate.Length(min=2, max=200)
    )
    email = SanitizedEmail(required=False)
    department = SanitizedString(
        required=False,
        max_length=100,
        validate=validate.Length(min=2, max=100)
    )
    phone = fields.Str(
        required=False,
        allow_none=True,
        validate=validate.Length(max=20)
    )
    date_of_birth = fields.Date(
        required=False,
        allow_none=True,
        format="%Y-%m-%d"
    )

    class Meta:
        """Meta options."""
        ordered = True


class UserCreateSchema(Schema):
    """Schema for creating a user."""
    name = SanitizedString(
        required=True,
        max_length=200,
        validate=validate.Length(min=2, max=200)
    )
    email = SanitizedEmail(required=True)
    password = fields.Str(
        required=True,
        validate=validate.Length(min=8, max=128),
        error_messages={"required": "Password is required", "invalid": "Password must be 8-128 characters"}
    )
    role = fields.Str(
        required=True,
        validate=validate.OneOf(["Admin", "Faculty", "Student", "Super_Admin"]),
        error_messages={"required": "Role is required", "invalid": "Invalid role"}
    )
    phone = fields.Str(required=False, allow_none=True)

    class Meta:
        """Meta options."""
        ordered = True


class DepartmentCreateSchema(Schema):
    """Schema for creating a department."""
    name = SanitizedString(
        required=True,
        max_length=100,
        validate=validate.Length(min=2, max=100),
        error_messages={"required": "Department name is required"}
    )
    code = SanitizedString(
        required=True,
        max_length=10,
        validate=validate.Length(min=1, max=10),
        error_messages={"required": "Department code is required"}
    )
    description = SanitizedString(
        required=False,
        allow_none=True,
        max_length=500
    )

    class Meta:
        """Meta options."""
        ordered = True


class SubjectCreateSchema(Schema):
    """Schema for creating a subject."""
    name = SanitizedString(
        required=True,
        max_length=200,
        validate=validate.Length(min=2, max=200),
        error_messages={"required": "Subject name is required"}
    )
    code = SanitizedString(
        required=True,
        max_length=20,
        validate=validate.Length(min=1, max=20),
        error_messages={"required": "Subject code is required"}
    )
    department_id = fields.Int(
        required=False,
        allow_none=True,
        validate=validate.Range(min=1),
        description="Department ID (optional)"
    )
    credits = fields.Float(
        required=False,
        allow_none=True,
        validate=validate.Range(min=0, max=10),
        description="Subject credits (0-10)"
    )

    class Meta:
        """Meta options."""
        ordered = True


class MarkEntrySchema(Schema):
    """Schema for entering marks."""
    student_id = fields.Int(
        required=True,
        validate=validate.Range(min=1),
        error_messages={"required": "Student ID is required"}
    )
    subject_id = fields.Int(
        required=True,
        validate=validate.Range(min=1),
        error_messages={"required": "Subject ID is required"}
    )
    marks = fields.Float(
        required=True,
        validate=validate.Range(min=0, max=100),
        error_messages={"required": "Marks are required", "invalid": "Marks must be between 0 and 100"}
    )
    date = fields.Date(
        required=False,
        allow_none=True,
        format="%Y-%m-%d",
        default=datetime.today().date()
    )

    class Meta:
        """Meta options."""
        ordered = True


class GoalCreateSchema(Schema):
    """Schema for creating a goal."""
    title = SanitizedString(
        required=True,
        max_length=200,
        validate=validate.Length(min=3, max=200),
        error_messages={"required": "Goal title is required"}
    )
    description = SanitizedString(
        required=False,
        allow_none=True,
        max_length=1000
    )
    target_date = fields.Date(
        required=True,
        format="%Y-%m-%d",
        error_messages={"required": "Target date is required"}
    )
    priority = fields.Str(
        required=False,
        allow_none=True,
        validate=validate.OneOf(["low", "medium", "high"]),
        load_default="medium"
    )
    status = fields.Str(
        required=False,
        allow_none=True,
        validate=validate.OneOf(["not_started", "in_progress", "completed"]),
        load_default="not_started"
    )

    class Meta:
        """Meta options."""
        ordered = True


# ============================================================================
# ERROR RESPONSE SCHEMA
# ============================================================================

class ErrorResponseSchema(Schema):
    """Schema for error responses."""
    status = fields.Str(required=True)
    error = fields.Dict(required=True)
    meta = fields.Dict(default=dict)
    timestamp = fields.DateTime(default=datetime.utcnow)

    class Meta:
        """Meta options."""
        ordered = True


# ============================================================================
# SCHEMA FACTORY & HELPER FUNCTIONS
# ============================================================================

def get_paginated_response_data(data, page, per_page, total):
    """
    Format paginated response data.
    
    Args:
        data: List of items
        page: Current page number
        per_page: Items per page
        total: Total number of items
        
    Returns:
        Formatted response dict
    """
    total_pages = (total + per_page - 1) // per_page
    return {
        "status": "success",
        "data": data,
        "pagination": {
            "page": page,
            "per_page": per_page,
            "total": total,
            "total_pages": total_pages,
            "has_next": page < total_pages,
            "has_prev": page > 1
        },
        "meta": {
            "timestamp": datetime.utcnow().isoformat()
        }
    }


def validate_request(schema_class, data):
    """
    Validate request data against schema.
    
    Args:
        schema_class: Marshmallow schema class
        data: Data to validate
        
    Returns:
        Tuple of (is_valid, validated_data or errors)
    """
    schema = schema_class()
    try:
        result = schema.load(data)
        return True, result
    except ValidationError as err:
        return False, err.messages


def create_error_response(code, message, status_code=400, details=None):
    """
    Create standardized error response.
    
    Args:
        code: Error code identifier
        message: Error message
        status_code: HTTP status code
        details: Additional error details
        
    Returns:
        Tuple of (response_dict, status_code)
    """
    return {
        "status": "error",
        "error": {
            "code": code,
            "message": message,
            "details": details or {}
        },
        "meta": {
            "timestamp": datetime.utcnow().isoformat()
        }
    }, status_code
