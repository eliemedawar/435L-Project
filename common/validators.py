"""Reusable input validation helpers. They raise ValidationError (HTTP 400) on bad input."""
import re

from flask import request

from common.errors import ValidationError

EMAIL_RE = re.compile(r"^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$")


def get_json_body():
    """Return the request body as a dict. Rejects missing, invalid or empty JSON."""
    data = request.get_json(silent=True)
    if not isinstance(data, dict):
        raise ValidationError("Request body must be a valid JSON object")
    if not data:
        raise ValidationError("Request body cannot be empty")
    return data


def reject_unknown_fields(data, allowed):
    unknown = sorted(set(data) - set(allowed))
    if unknown:
        raise ValidationError(f"Unexpected field(s): {', '.join(unknown)}")


def require_fields(data, fields):
    missing = [f for f in fields if data.get(f) is None or (isinstance(data.get(f), str) and not data[f].strip())]
    if missing:
        raise ValidationError(f"Missing required field(s): {', '.join(missing)}")


def clean_string(data, field, max_length=255, required=True):
    """Return a trimmed string value, checking its type and length."""
    value = data.get(field)
    if value is None:
        if required:
            raise ValidationError(f"Missing required field(s): {field}")
        return None
    if not isinstance(value, str):
        raise ValidationError(f"'{field}' must be a string")
    value = value.strip()
    if required and not value:
        raise ValidationError(f"'{field}' cannot be empty")
    if len(value) > max_length:
        raise ValidationError(f"'{field}' must be at most {max_length} characters")
    return value


def validate_enum(value, allowed, field):
    if value not in allowed:
        raise ValidationError(f"Invalid {field} '{value}'. Allowed values: {', '.join(allowed)}")
    return value


def validate_email(value):
    if not isinstance(value, str) or not EMAIL_RE.match(value.strip()):
        raise ValidationError("Invalid email format")
    return value.strip().lower()
