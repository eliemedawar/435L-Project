"""REST endpoints of the Security Audit Logging Service (port 5005).

There is deliberately no PUT/PATCH endpoint: audit logs are immutable.
"""
from flask import Blueprint, g, request

from common.auth import is_service_call, require_auth, require_service
from common.errors import success
from common.roles import ADMIN, ANALYST, AUDITOR
from common.validators import get_json_body
from services.logs.service import LogService

logs_bp = Blueprint("logs", __name__)


def _list_response(logs, message):
    return success({"count": len(logs), "logs": [log.to_dict() for log in logs]}, message)


# Developed by: Elie Medawar
@logs_bp.route("/logs", methods=["POST"])
@require_auth(roles=[ADMIN], allow_service=True)
def create_log():
    log = LogService.create(get_json_body(), from_service=is_service_call())
    return success(log.to_dict(), "Log record created successfully", 201)


# Developed by: Elie Medawar
@logs_bp.route("/logs", methods=["GET"])
@require_auth(roles=[ADMIN, AUDITOR])
def get_all_logs():
    return _list_response(LogService.list_all(), "Logs retrieved successfully")


# Developed by: Elie Medawar
@logs_bp.route("/logs/search", methods=["GET"])
@require_auth(roles=[ADMIN, AUDITOR, ANALYST])
def search_logs():
    logs = LogService.search(request.args.to_dict())
    return _list_response(logs, f"{len(logs)} log(s) match the search criteria")


# Developed by: Elie Medawar
@logs_bp.route("/logs/user/<int:user_id>", methods=["GET"])
@require_auth(roles=[ADMIN, AUDITOR])
def get_logs_by_user(user_id):
    logs = LogService.by_user(user_id)
    message = f"{len(logs)} log(s) found for user {user_id}" if logs else f"No logs found for user {user_id}"
    return _list_response(logs, message)


# Developed by: Elie Medawar
@logs_bp.route("/logs/<int:log_id>", methods=["GET"])
@require_auth(roles=[ADMIN, AUDITOR, ANALYST])
def get_log(log_id):
    return success(LogService.get(log_id).to_dict(), "Log retrieved successfully")


# Developed by: Elie Medawar
@logs_bp.route("/logs/<int:log_id>", methods=["DELETE"])
@require_auth(roles=[ADMIN])
def delete_log(log_id):
    LogService.delete(log_id, g.user)
    return success(None, f"Log {log_id} deleted successfully")


# Developed by: Elie Medawar
@logs_bp.route("/internal/stats", methods=["GET"])
@require_service
def internal_stats():
    return success(LogService.stats())
