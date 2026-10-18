"""REST endpoints of the Users and Identity Management Service (port 5001)."""
from flask import Blueprint, g, request

from common.auth import optional_user, require_auth, require_service
from common.errors import success
from common.roles import ADMIN, AUDITOR, USER
from common.validators import get_json_body
from services.users.service import UserService

users_bp = Blueprint("users", __name__)


# Developed by: Elie Medawar
@users_bp.route("/users/register", methods=["POST"])
def register_user():
    """Public self-registration (role 'user'), or an admin creating any account when a token is sent."""
    user = UserService.register(get_json_body(), actor=optional_user())
    return success(user.to_dict(), "User registered successfully", 201)


# Developed by: Elie Medawar
@users_bp.route("/users/login", methods=["POST"])
def login():
    token, user = UserService.login(get_json_body())
    return success({"token": token, "token_type": "Bearer", "user": user.to_dict()}, "Login successful")


# Developed by: Elie Medawar
@users_bp.route("/users/<int:user_id>", methods=["PUT"])
@require_auth(roles=[ADMIN, USER])
def update_user(user_id):
    user = UserService.update(user_id, get_json_body(), g.user)
    return success(user.to_dict(), "User updated successfully")


# Developed by: Elie Medawar
@users_bp.route("/users/<int:user_id>", methods=["DELETE"])
@require_auth(roles=[ADMIN])
def delete_user(user_id):
    UserService.delete(user_id, g.user)
    return success(None, f"User {user_id} deleted successfully")


# Developed by: Elie Medawar
@users_bp.route("/users", methods=["GET"])
@require_auth(roles=[ADMIN, AUDITOR])
def get_all_users():
    users = UserService.list_all(role=request.args.get("role"))
    return success({"count": len(users), "users": [u.to_dict() for u in users]}, "Users retrieved successfully")


# Developed by: Elie Medawar
@users_bp.route("/users/<string:username>", methods=["GET"])
@require_auth(roles=[ADMIN, AUDITOR, USER])
def get_user_by_username(username):
    user = UserService.get_by_username(username, g.user)
    return success(user.to_dict(), "User retrieved successfully")


# ---------- internal endpoints (other services only, X-Service-Key) ----------

# Developed by: Elie Medawar
@users_bp.route("/internal/users/<int:user_id>", methods=["GET"])
@require_service
def internal_get_user(user_id):
    return success(UserService.get_by_id(user_id).to_dict())


# Developed by: Elie Medawar
@users_bp.route("/internal/users", methods=["GET"])
@require_service
def internal_list_users():
    users = UserService.list_all(role=request.args.get("role"))
    return success([u.to_dict() for u in users])


# Developed by: Elie Medawar
@users_bp.route("/internal/stats", methods=["GET"])
@require_service
def internal_stats():
    return success(UserService.stats())
