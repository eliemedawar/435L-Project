"""Business logic of the Users and Identity Management Service. Owner: Elie Medawar.

Routes stay thin: they check the role, then call UserService, which validates,
talks to the database and writes audit logs.
"""
import re

from sqlalchemy import func
from sqlalchemy.exc import IntegrityError

from common.auth import create_token
from common.clients import log_event
from common.db import db, utcnow
from common.enums import ACCOUNT_STATUSES
from common.errors import AuthError, ConflictError, ForbiddenError, NotFoundError, ValidationError
from common.roles import ADMIN, ALL_ROLES, USER
from common.validators import clean_string, reject_unknown_fields, require_fields, validate_email, validate_enum
from models.users import User


class PasswordValidator:
    """Password rules: 8-64 characters with an uppercase letter, a lowercase letter, a digit and a symbol."""
    MIN_LENGTH = 8
    MAX_LENGTH = 64   # bcrypt only uses the first 72 bytes

    @classmethod
    def validate(cls, password):
        if not isinstance(password, str):
            raise ValidationError("'password' must be a string")
        problems = []
        if not cls.MIN_LENGTH <= len(password) <= cls.MAX_LENGTH:
            problems.append(f"{cls.MIN_LENGTH}-{cls.MAX_LENGTH} characters")
        if not re.search(r"[A-Z]", password):
            problems.append("an uppercase letter")
        if not re.search(r"[a-z]", password):
            problems.append("a lowercase letter")
        if not re.search(r"\d", password):
            problems.append("a digit")
        if not re.search(r"[^A-Za-z0-9]", password):
            problems.append("a special character")
        if problems:
            raise ValidationError("Password must contain " + ", ".join(problems))


class UserValidator:
    USERNAME_RE = re.compile(r"^[A-Za-z0-9_.]{3,30}$")
    REGISTER_FIELDS = ("full_name", "username", "email", "password", "department", "role")
    SELF_UPDATE_FIELDS = ("full_name", "email", "department")
    ADMIN_UPDATE_FIELDS = SELF_UPDATE_FIELDS + ("role", "account_status")

    @classmethod
    def username(cls, value):
        if not isinstance(value, str) or not cls.USERNAME_RE.match(value.strip()):
            raise ValidationError("Username must be 3-30 characters: letters, digits, '_' or '.'")
        return value.strip()


class UserService:

    # ---------- helpers ----------
    @staticmethod
    def get_by_id(user_id):
        user = db.session.get(User, user_id)
        if user is None:
            raise NotFoundError(f"User with id {user_id} not found")
        return user

    @staticmethod
    def _ensure_unique(username=None, email=None, exclude_id=None):
        if username is not None:
            query = User.query.filter(func.lower(User.username) == username.lower())
            if exclude_id:
                query = query.filter(User.id != exclude_id)
            if query.first():
                raise ConflictError(f"Username '{username}' already exists")
        if email is not None:
            query = User.query.filter(User.email == email)
            if exclude_id:
                query = query.filter(User.id != exclude_id)
            if query.first():
                raise ConflictError(f"Email '{email}' is already registered")

    @staticmethod
    def _deny(actor, message, description):
        """Reject a permission violation that is decided inside the service, and audit-log it."""
        log_event(actor["user_id"] if actor else None, "UNAUTHORIZED_ACCESS", description, severity="Warning")
        raise ForbiddenError(message)

    # ---------- registration & login ----------
    @classmethod
    def register(cls, data, actor=None):
        """actor = the logged-in user (admin creating an account) or None (public self-registration)."""
        reject_unknown_fields(data, UserValidator.REGISTER_FIELDS)
        require_fields(data, ("full_name", "username", "email", "password", "department"))

        full_name = clean_string(data, "full_name", 100)
        username = UserValidator.username(data["username"])
        email = validate_email(data["email"])
        department = clean_string(data, "department", 100)
        PasswordValidator.validate(data["password"])
        role = validate_enum(data.get("role") or USER, ALL_ROLES, "role")

        is_admin = actor is not None and actor["role"] == ADMIN
        if role != USER and not is_admin:
            cls._deny(actor, f"Only a Security Administrator can create accounts with the '{role}' role",
                      f"Attempt to self-register username '{username}' with role '{role}'")

        cls._ensure_unique(username=username, email=email)

        user = User(full_name=full_name, username=username, email=email, department=department, role=role)
        user.set_password(data["password"])
        db.session.add(user)
        try:
            db.session.commit()
        except IntegrityError:   # two requests registering the same username at the same moment
            db.session.rollback()
            raise ConflictError("Username or email already exists")

        creator = f"admin '{actor['username']}'" if is_admin else "self-registration"
        log_event(actor["user_id"] if is_admin else user.id, "USER_CREATED",
                  f"User '{user.username}' (id {user.id}, role {user.role}) created by {creator}")
        return user

    @classmethod
    def login(cls, data):
        reject_unknown_fields(data, ("username", "email", "password"))
        identifier = data.get("username") or data.get("email")
        if not identifier or not data.get("password"):
            raise ValidationError("Provide 'username' (or 'email') and 'password'")
        if not isinstance(identifier, str) or not isinstance(data["password"], str):
            raise ValidationError("'username'/'email' and 'password' must be strings")

        identifier = identifier.strip()
        user = User.query.filter(
            (func.lower(User.username) == identifier.lower()) | (User.email == identifier.lower())
        ).first()

        if user is None or not user.check_password(data["password"]):
            log_event(user.id if user else None, "LOGIN_FAILED",
                      f"Failed login attempt for '{identifier}'", severity="Warning")
            raise AuthError("Invalid username/email or password")

        if not user.can_authenticate:
            log_event(user.id, "LOGIN_BLOCKED",
                      f"Login refused for '{user.username}': account is {user.account_status}", severity="Warning")
            raise ForbiddenError(f"Account is {user.account_status}. Contact a Security Administrator")

        user.last_login = utcnow()
        db.session.commit()
        log_event(user.id, "LOGIN_SUCCESS", f"User '{user.username}' logged in")
        return create_token(user.id, user.username, user.role), user

    # ---------- update & delete ----------
    @classmethod
    def update(cls, user_id, data, actor):
        is_admin = actor["role"] == ADMIN
        if not is_admin and actor["user_id"] != user_id:
            cls._deny(actor, "You can only update your own information",
                      f"'{actor['username']}' tried to update user id {user_id}")

        allowed = UserValidator.ADMIN_UPDATE_FIELDS if is_admin else UserValidator.SELF_UPDATE_FIELDS
        forbidden = {"role", "account_status"} & set(data)
        if forbidden and not is_admin:
            cls._deny(actor, "Only a Security Administrator can change roles or account status",
                      f"'{actor['username']}' tried to change {', '.join(sorted(forbidden))} of user id {user_id}")
        reject_unknown_fields(data, allowed)

        user = cls.get_by_id(user_id)
        changes = []

        if "full_name" in data:
            user.full_name = clean_string(data, "full_name", 100)
            changes.append("full_name")
        if "email" in data:
            email = validate_email(data["email"])
            cls._ensure_unique(email=email, exclude_id=user.id)
            user.email = email
            changes.append("email")
        if "department" in data:
            user.department = clean_string(data, "department", 100)
            changes.append("department")

        old_role = user.role
        if "role" in data:
            user.role = validate_enum(data["role"], ALL_ROLES, "role")
        if "account_status" in data:
            user.account_status = validate_enum(data["account_status"], ACCOUNT_STATUSES, "account_status")
            changes.append("account_status")

        db.session.commit()

        if changes:
            log_event(actor["user_id"], "USER_UPDATED",
                      f"User '{user.username}' (id {user.id}) updated fields: {', '.join(changes)}")
        if user.role != old_role:
            log_event(actor["user_id"], "ROLE_CHANGED",
                      f"Role of '{user.username}' (id {user.id}) changed from {old_role} to {user.role}",
                      severity="Warning")
        return user

    @classmethod
    def delete(cls, user_id, actor):
        if actor["user_id"] == user_id:
            raise ValidationError("Administrators cannot delete their own account")
        user = cls.get_by_id(user_id)
        username = user.username
        db.session.delete(user)
        try:
            db.session.commit()
        except IntegrityError:
            db.session.rollback()
            raise ConflictError("User is linked to other records (incidents, assets, ...). "
                                "Set account_status to 'Inactive' instead of deleting")
        log_event(actor["user_id"], "USER_DELETED", f"User '{username}' (id {user_id}) deleted", severity="Warning")

    # ---------- queries ----------
    @staticmethod
    def list_all(role=None):
        query = User.query.order_by(User.id)
        if role:
            query = query.filter_by(role=validate_enum(role, ALL_ROLES, "role"))
        return query.all()

    @classmethod
    def get_by_username(cls, username, actor):
        if actor["role"] == USER and actor["username"].lower() != username.lower():
            cls._deny(actor, "You can only view your own information",
                      f"'{actor['username']}' tried to view user '{username}'")
        user = User.query.filter(func.lower(User.username) == username.lower()).first()
        if user is None:
            raise NotFoundError(f"User '{username}' not found")
        return user

    @staticmethod
    def stats():
        by_role = dict(db.session.query(User.role, func.count(User.id)).group_by(User.role).all())
        by_status = dict(db.session.query(User.account_status, func.count(User.id))
                         .group_by(User.account_status).all())
        return {
            "total_users": User.query.count(),
            "by_role": {role: by_role.get(role, 0) for role in ALL_ROLES},
            "by_status": {status: by_status.get(status, 0) for status in ACCOUNT_STATUSES},
        }
