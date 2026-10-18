"""REST endpoints of the Notification and Alert Management Service (port 5008)."""
from flask import Blueprint, g, request

from common.auth import require_auth
from common.errors import success
from common.roles import ADMIN, ANALYST, AUDITOR, USER
from common.validators import get_json_body
from services.notifications.service import NotificationService

notifications_bp = Blueprint("notifications", __name__)


def _list_response(notifications, message):
    return success({"count": len(notifications), "notifications": [n.to_dict() for n in notifications]}, message)


# Developed by: Elie Medawar
@notifications_bp.route("/notifications", methods=["POST"])
@require_auth(roles=[ADMIN], allow_service=True)
def create_notification():
    notification = NotificationService.create(get_json_body(), g.user)
    return success(notification.to_dict(), "Notification created successfully", 201)


# Developed by: Elie Medawar
@notifications_bp.route("/notifications/user/<int:user_id>", methods=["GET"])
@require_auth(roles=[ADMIN, ANALYST, USER, AUDITOR])
def get_user_notifications(user_id):
    notifications = NotificationService.for_user(user_id, g.user, status=request.args.get("status"))
    message = (f"{len(notifications)} notification(s) found for user {user_id}" if notifications
               else f"No notifications found for user {user_id}")
    return _list_response(notifications, message)


# Developed by: Elie Medawar
@notifications_bp.route("/notifications/search", methods=["GET"])
@require_auth(roles=[ADMIN, ANALYST, AUDITOR])
def search_notifications():
    notifications = NotificationService.search(request.args.to_dict(), g.user)
    return _list_response(notifications, f"{len(notifications)} notification(s) match the search criteria")


# Developed by: Elie Medawar
@notifications_bp.route("/notifications/<int:notification_id>", methods=["GET"])
@require_auth(roles=[ADMIN, ANALYST, USER, AUDITOR])
def get_notification(notification_id):
    notification = NotificationService.get_for(notification_id, g.user)
    return success(notification.to_dict(), "Notification retrieved successfully")


# Developed by: Elie Medawar
@notifications_bp.route("/notifications/<int:notification_id>/read", methods=["PUT"])
@require_auth(roles=[ADMIN, ANALYST, USER])
def mark_notification_read(notification_id):
    notification, changed = NotificationService.mark_read(notification_id, g.user)
    message = "Notification marked as read" if changed else "Notification was already marked as read"
    return success(notification.to_dict(), message)


# Developed by: Elie Medawar
@notifications_bp.route("/notifications/<int:notification_id>", methods=["DELETE"])
@require_auth(roles=[ADMIN])
def delete_notification(notification_id):
    NotificationService.delete(notification_id, g.user)
    return success(None, f"Notification {notification_id} deleted successfully")
