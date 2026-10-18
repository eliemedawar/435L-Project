"""Business logic of the Security Audit Logging Service. Owner: Elie Medawar."""
import re
from datetime import date

from sqlalchemy import func

from common.clients import log_event
from common.config import SERVICE_PORTS
from common.db import db
from common.enums import LOG_SEVERITIES
from common.errors import NotFoundError, ValidationError
from common.validators import clean_string, reject_unknown_fields, require_fields, validate_enum
from models.logs import Log
from models.users import User


class LogValidator:
    ACTION_RE = re.compile(r"^[A-Z][A-Z0-9_]{2,49}$")      # e.g. LOGIN_FAILED, INCIDENT_CREATED
    CREATE_FIELDS = ("user_id", "action", "description", "severity", "related_service")
    SEARCH_PARAMS = ("user", "action", "severity", "service", "date", "date_from", "date_to")

    @classmethod
    def action(cls, value):
        if not isinstance(value, str) or not cls.ACTION_RE.match(value.strip().upper()):
            raise ValidationError("'action' must be 3-50 characters: letters, digits and '_' (e.g. LOGIN_FAILED)")
        return value.strip().upper()

    @staticmethod
    def service(value):
        return validate_enum(value, tuple(SERVICE_PORTS), "related_service")

    @staticmethod
    def parse_date(value, field):
        try:
            return date.fromisoformat(value)
        except (TypeError, ValueError):
            raise ValidationError(f"'{field}' must be a date in YYYY-MM-DD format")


class LogService:

    @staticmethod
    def _resolve_user(user_id):
        """Return the username for user_id, or raise 400 if it does not exist."""
        if isinstance(user_id, bool) or not isinstance(user_id, int):
            raise ValidationError("'user_id' must be an integer")
        user = db.session.get(User, user_id)
        if user is None:
            raise ValidationError(f"User with id {user_id} does not exist")
        return user.username

    @classmethod
    def create(cls, data, from_service):
        """from_service=True: trusted call from another service, user_id may be null (e.g. failed login of an unknown user)."""
        reject_unknown_fields(data, LogValidator.CREATE_FIELDS)
        required = ("action", "description", "severity", "related_service")
        require_fields(data, required if from_service else ("user_id",) + required)

        user_id = data.get("user_id")
        username = cls._resolve_user(user_id) if user_id is not None else None

        log = Log(
            user_id=user_id,
            username=username,
            action=LogValidator.action(data["action"]),
            description=clean_string(data, "description", 500),
            severity=validate_enum(data["severity"], LOG_SEVERITIES, "severity"),
            related_service=LogValidator.service(data["related_service"]),
        )
        db.session.add(log)
        db.session.commit()
        return log

    @staticmethod
    def get(log_id):
        log = db.session.get(Log, log_id)
        if log is None:
            raise NotFoundError(f"Log with id {log_id} not found")
        return log

    @staticmethod
    def list_all():
        return Log.query.order_by(Log.timestamp.desc(), Log.id.desc()).all()

    @staticmethod
    def by_user(user_id):
        return Log.query.filter_by(user_id=user_id).order_by(Log.timestamp.desc(), Log.id.desc()).all()

    @staticmethod
    def search(params):
        """Every filter given is combined with AND. `user` accepts a user id or a username."""
        reject_unknown_fields(params, LogValidator.SEARCH_PARAMS)
        if not any(v.strip() for v in params.values()):
            raise ValidationError(f"Provide at least one search criterion: {', '.join(LogValidator.SEARCH_PARAMS)}")

        query = Log.query
        if params.get("user"):
            user = params["user"].strip()
            query = query.filter(Log.user_id == int(user)) if user.isdigit() \
                else query.filter(func.lower(Log.username) == user.lower())
        if params.get("action"):
            query = query.filter(Log.action == params["action"].strip().upper())
        if params.get("severity"):
            query = query.filter(Log.severity == validate_enum(params["severity"], LOG_SEVERITIES, "severity"))
        if params.get("service"):
            query = query.filter(Log.related_service == LogValidator.service(params["service"]))
        if params.get("date"):
            day = LogValidator.parse_date(params["date"], "date")
            query = query.filter(func.date(Log.timestamp) == day.isoformat())
        if params.get("date_from"):
            start = LogValidator.parse_date(params["date_from"], "date_from")
            query = query.filter(func.date(Log.timestamp) >= start.isoformat())
        if params.get("date_to"):
            end = LogValidator.parse_date(params["date_to"], "date_to")
            query = query.filter(func.date(Log.timestamp) <= end.isoformat())
        return query.order_by(Log.timestamp.desc(), Log.id.desc()).all()

    @classmethod
    def delete(cls, log_id, actor):
        log = cls.get(log_id)
        summary = f"log {log.id} ({log.action} by {log.username or 'unknown'} at {log.timestamp:%Y-%m-%d %H:%M})"
        db.session.delete(log)
        db.session.commit()
        # Deleting audit evidence is itself an auditable event.
        log_event(actor["user_id"], "LOG_DELETED", f"Admin '{actor['username']}' deleted {summary}", severity="Warning")

    @staticmethod
    def stats(top=5):
        def grouped(column):
            return dict(db.session.query(column, func.count(Log.id)).group_by(column).all())

        top_actions = (db.session.query(Log.action, func.count(Log.id).label("n"))
                       .group_by(Log.action).order_by(func.count(Log.id).desc()).limit(top).all())
        by_severity = grouped(Log.severity)
        return {
            "total_activities": Log.query.count(),
            "login_attempts": Log.query.filter(Log.action.in_(("LOGIN_SUCCESS", "LOGIN_FAILED", "LOGIN_BLOCKED"))).count(),
            "successful_logins": Log.query.filter_by(action="LOGIN_SUCCESS").count(),
            "failed_logins": Log.query.filter(Log.action.in_(("LOGIN_FAILED", "LOGIN_BLOCKED"))).count(),
            "unauthorized_attempts": Log.query.filter_by(action="UNAUTHORIZED_ACCESS").count(),
            "by_severity": {s: by_severity.get(s, 0) for s in LOG_SEVERITIES},
            "by_service": grouped(Log.related_service),
            "most_performed_actions": [{"action": a, "count": n} for a, n in top_actions],
        }
