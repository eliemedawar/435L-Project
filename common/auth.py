"""Authentication (JWT) and role-based access control for every service.

Usage in a route:
    @bp.route("/assets", methods=["POST"])
    @require_auth(roles=[ADMIN])
    def add_asset():
        g.user["user_id"], g.user["role"] ...
"""
import hmac
from datetime import datetime, timedelta, timezone
from functools import wraps

import jwt
from flask import current_app, g, request

from common.clients import log_event
from common.config import Config
from common.errors import AuthError, ForbiddenError

SERVICE_ROLE = "service"   # role given to trusted service-to-service calls


def create_token(user_id, username, role):
    payload = {
        "user_id": user_id,
        "username": username,
        "role": role,
        "exp": datetime.now(timezone.utc) + timedelta(minutes=Config.JWT_EXPIRES_MIN),
    }
    return jwt.encode(payload, Config.JWT_SECRET, algorithm=Config.JWT_ALGORITHM)


def decode_token(token):
    try:
        payload = jwt.decode(token, Config.JWT_SECRET, algorithms=[Config.JWT_ALGORITHM])
    except jwt.ExpiredSignatureError:
        raise AuthError("Authentication token has expired, please log in again")
    except jwt.InvalidTokenError:
        raise AuthError("Invalid authentication token")
    return {"user_id": payload["user_id"], "username": payload["username"], "role": payload["role"]}


def _bearer_token():
    header = request.headers.get("Authorization", "")
    if not header.startswith("Bearer ") or not header[7:].strip():
        return None
    return header[7:].strip()


def _valid_service_key(key):
    return hmac.compare_digest(key.encode(), Config.SERVICE_KEY.encode())


def optional_user():
    """Return the token's user if a valid Bearer token was sent, otherwise None (for public endpoints)."""
    token = _bearer_token()
    return decode_token(token) if token else None


def is_service_call():
    return g.get("user", {}).get("role") == SERVICE_ROLE


def require_auth(roles=None, allow_service=False):
    """Protect a route.

    roles=None        -> any logged-in user
    roles=[...]       -> only these roles; others get 403 and the attempt is audit-logged
    allow_service     -> also accept trusted calls from other services (X-Service-Key header)
    """
    def decorator(view):
        @wraps(view)
        def wrapper(*args, **kwargs):
            service_key = request.headers.get("X-Service-Key")
            if service_key is not None:
                if not allow_service or not _valid_service_key(service_key):
                    raise AuthError("Invalid or unauthorized service key")
                g.user = {"user_id": None, "username": "internal-service", "role": SERVICE_ROLE}
                return view(*args, **kwargs)

            token = _bearer_token()
            if token is None:
                raise AuthError("Missing authentication token (use 'Authorization: Bearer <token>')")
            g.user = decode_token(token)

            if roles is not None and g.user["role"] not in roles:
                log_event(
                    g.user["user_id"],
                    "UNAUTHORIZED_ACCESS",
                    f"{g.user['role']} '{g.user['username']}' was denied {request.method} {request.path}",
                    severity="Warning",
                    service=current_app.config.get("SERVICE_NAME"),
                )
                raise ForbiddenError("User does not have permission to perform this operation")
            return view(*args, **kwargs)
        return wrapper
    return decorator


def require_service(view):
    """Only other services (valid X-Service-Key) may call this route. Used for /internal/* endpoints."""
    @wraps(view)
    def wrapper(*args, **kwargs):
        service_key = request.headers.get("X-Service-Key")
        if service_key is None or not _valid_service_key(service_key):
            raise AuthError("This endpoint is only available to internal services")
        g.user = {"user_id": None, "username": "internal-service", "role": SERVICE_ROLE}
        return view(*args, **kwargs)
    return wrapper
