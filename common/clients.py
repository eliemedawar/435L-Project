"""HTTP calls from one service to another.

These helpers never raise: if the target service is down, the original request
still succeeds and the helper just returns False/None.
"""
import requests
from flask import current_app, has_app_context

from common.config import Config, service_url


def _service_headers():
    return {"X-Service-Key": Config.SERVICE_KEY}


def _current_service_name():
    return current_app.config.get("SERVICE_NAME", "unknown") if has_app_context() else "unknown"


def log_event(user_id, action, description, severity="Information", service=None):
    """Write an audit log record through the Audit Logging Service (POST /logs)."""
    payload = {
        "user_id": user_id,
        "action": action,
        "description": description,
        "severity": severity,
        "related_service": service or _current_service_name(),
    }
    try:
        response = requests.post(f"{service_url('logs')}/logs", json=payload,
                                 headers=_service_headers(), timeout=Config.HTTP_TIMEOUT)
        return response.ok
    except requests.RequestException:
        return False


def send_notification(user_id, title, message, ntype, severity):
    """Create a notification for a user through the Notification Service (POST /notifications)."""
    payload = {"user_id": user_id, "title": title, "message": message,
               "notification_type": ntype, "severity": severity}
    try:
        response = requests.post(f"{service_url('notifications')}/notifications", json=payload,
                                 headers=_service_headers(), timeout=Config.HTTP_TIMEOUT)
        return response.ok
    except requests.RequestException:
        return False


def fetch_service(service_name, path, params=None):
    """GET another service's endpoint with the service key.
    Returns (status_code, data): status_code is None when the service could not be reached."""
    try:
        response = requests.get(f"{service_url(service_name)}{path}", params=params,
                                headers=_service_headers(), timeout=Config.HTTP_TIMEOUT)
        return response.status_code, response.json().get("data")
    except (requests.RequestException, ValueError):
        return None, None


def get_service(service_name, path, params=None):
    """Like fetch_service, but only returns the "data" of a successful response (None otherwise)."""
    status, data = fetch_service(service_name, path, params)
    return data if status == 200 else None
