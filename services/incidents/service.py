"""Business logic of the Incident Management Service. Owner: Elie Medawar."""
from sqlalchemy import func

from common.clients import fetch_service, log_event, send_notification
from common.db import db, utcnow
from common.enums import INCIDENT_CATEGORIES, INCIDENT_FLOW, SEVERITIES, next_status
from common.errors import APIError, ForbiddenError, NotFoundError, ValidationError
from common.roles import ADMIN, ANALYST, AUDITOR, USER
from common.validators import clean_string, reject_unknown_fields, require_fields, validate_enum
from models.incidents import Incident, InvestigationNote

OPEN_STATUSES = ("Open", "Under Investigation", "Mitigated")    # not yet Resolved/Closed


class ServiceUnavailableError(APIError):
    status_code = 503


def _require_int(value, field):
    if isinstance(value, bool) or not isinstance(value, int) or value < 1:
        raise ValidationError(f"'{field}' must be a positive integer")
    return value


class IncidentWorkflow:
    """Enforces the lifecycle Open -> Under Investigation -> Mitigated -> Resolved -> Closed."""

    @staticmethod
    def transition(incident, new_status):
        validate_enum(new_status, INCIDENT_FLOW, "status")
        allowed = next_status(INCIDENT_FLOW, incident.status)
        if allowed is None:
            raise ValidationError(f"Incident {incident.id} is Closed; its status can no longer change")
        if new_status != allowed:
            raise ValidationError(f"Invalid status transition: {incident.status} -> {new_status}. "
                                  f"The next allowed status is '{allowed}'")
        if new_status == "Under Investigation" and incident.assigned_analyst_id is None:
            raise ValidationError("Assign the incident to a Security Analyst before starting the investigation")
        incident.status = new_status
        if new_status == "Resolved":
            incident.resolved_at = utcnow()


class IncidentService:

    # ---------- helpers ----------
    @staticmethod
    def get(incident_id):
        incident = db.session.get(Incident, incident_id)
        if incident is None:
            raise NotFoundError(f"Incident with id {incident_id} not found")
        return incident

    @staticmethod
    def _deny(actor, message, description):
        log_event(actor["user_id"], "UNAUTHORIZED_ACCESS", description, severity="Warning")
        raise ForbiddenError(message)

    @classmethod
    def _check_access(cls, incident, actor, action):
        """Admins and auditors see every incident; analysts only the ones assigned to them;
        regular users only the ones they reported."""
        role, uid = actor["role"], actor["user_id"]
        if role in (ADMIN, AUDITOR):
            return
        if role == ANALYST and incident.assigned_analyst_id == uid:
            return
        if role == USER and incident.reporter_id == uid:
            return
        cls._deny(actor, "You do not have access to this incident",
                  f"{role} '{actor['username']}' tried to {action} incident {incident.id}")

    @staticmethod
    def _verify_asset(asset_id):
        """Ask the Asset Management Service whether the asset exists (service-to-service API call)."""
        status, _ = fetch_service("assets", f"/internal/assets/{asset_id}")
        if status is None:
            raise ServiceUnavailableError("Asset Management Service is unavailable; cannot verify the affected asset")
        if status == 404:
            raise ValidationError(f"Asset with id {asset_id} does not exist")
        if status != 200:
            raise ServiceUnavailableError("Could not verify the affected asset")

    @staticmethod
    def _verify_analyst(analyst_id):
        """Ask the Users Service for the user and check it is an active Security Analyst."""
        status, user = fetch_service("users", f"/internal/users/{analyst_id}")
        if status is None:
            raise ServiceUnavailableError("Users Service is unavailable; cannot verify the analyst")
        if status == 404:
            raise ValidationError(f"User with id {analyst_id} does not exist")
        if status != 200 or user is None:
            raise ServiceUnavailableError("Could not verify the analyst")
        if user["role"] != ANALYST:
            raise ValidationError(f"User '{user['username']}' is not a Security Analyst (role: {user['role']})")
        if user["account_status"] != "Active":
            raise ValidationError(f"Analyst '{user['username']}' account is {user['account_status']}")
        return user

    # ---------- operations ----------
    @classmethod
    def create(cls, data, actor):
        reject_unknown_fields(data, ("title", "description", "category", "severity", "asset_id"))
        require_fields(data, ("title", "description", "category", "severity", "asset_id"))

        incident = Incident(
            title=clean_string(data, "title", 150),
            description=clean_string(data, "description", 2000),
            category=validate_enum(data["category"], INCIDENT_CATEGORIES, "category"),
            severity=validate_enum(data["severity"], SEVERITIES, "severity"),
            asset_id=_require_int(data["asset_id"], "asset_id"),
            reporter_id=actor["user_id"],      # the reporter is always the logged-in user
        )
        cls._verify_asset(incident.asset_id)
        db.session.add(incident)
        db.session.commit()

        log_event(actor["user_id"], "INCIDENT_CREATED",
                  f"Incident {incident.id} '{incident.title}' ({incident.severity}, {incident.category}) "
                  f"reported by '{actor['username']}' on asset {incident.asset_id}",
                  severity="Critical" if incident.severity == "Critical" else "Information")
        return incident

    @staticmethod
    def list_all(params):
        reject_unknown_fields(params, ("status", "severity"))
        query = Incident.query
        if params.get("status"):
            query = query.filter_by(status=validate_enum(params["status"], INCIDENT_FLOW, "status"))
        if params.get("severity"):
            query = query.filter_by(severity=validate_enum(params["severity"], SEVERITIES, "severity"))
        return query.order_by(Incident.created_at.desc(), Incident.id.desc()).all()

    @classmethod
    def get_for(cls, incident_id, actor):
        incident = cls.get(incident_id)
        cls._check_access(incident, actor, "view")
        return incident

    @classmethod
    def assign(cls, incident_id, data, actor):
        reject_unknown_fields(data, ("analyst_id",))
        require_fields(data, ("analyst_id",))
        analyst_id = _require_int(data["analyst_id"], "analyst_id")

        incident = cls.get(incident_id)
        if incident.status in ("Resolved", "Closed"):
            raise ValidationError(f"Incident {incident.id} is {incident.status} and cannot be reassigned")
        analyst = cls._verify_analyst(analyst_id)

        previous = incident.assigned_analyst_id
        incident.assigned_analyst_id = analyst_id
        db.session.commit()

        change = f"reassigned from user {previous} to" if previous else "assigned to"
        log_event(actor["user_id"], "INCIDENT_ASSIGNED",
                  f"Incident {incident.id} {change} analyst '{analyst['username']}' (id {analyst_id})")
        send_notification(analyst_id, f"New incident assigned: #{incident.id}",
                          f"You have been assigned incident #{incident.id} '{incident.title}' "
                          f"({incident.severity}).", "Incident Assignment", incident.severity)
        return incident

    @classmethod
    def update_status(cls, incident_id, data, actor):
        reject_unknown_fields(data, ("status",))
        require_fields(data, ("status",))
        incident = cls.get(incident_id)
        cls._check_access(incident, actor, "change the status of")

        old_status = incident.status
        IncidentWorkflow.transition(incident, data["status"])
        db.session.commit()

        log_event(actor["user_id"], "INCIDENT_STATUS_CHANGED",
                  f"Incident {incident.id} status changed from {old_status} to {incident.status} "
                  f"by '{actor['username']}'")
        send_notification(incident.reporter_id, f"Incident #{incident.id} is now {incident.status}",
                          f"The status of your reported incident '{incident.title}' changed from "
                          f"{old_status} to {incident.status}.", "System Notification", incident.severity)
        return incident

    @classmethod
    def add_note(cls, incident_id, data, actor):
        reject_unknown_fields(data, ("content",))
        require_fields(data, ("content",))
        incident = cls.get(incident_id)
        cls._check_access(incident, actor, "add a note to")
        if incident.status == "Closed":
            raise ValidationError(f"Incident {incident.id} is Closed; notes can no longer be added")

        note = InvestigationNote(incident_id=incident.id, analyst_id=actor["user_id"],
                                 content=clean_string(data, "content", 2000))
        db.session.add(note)
        db.session.commit()
        log_event(actor["user_id"], "INVESTIGATION_NOTE_ADDED",
                  f"Note {note.id} added to incident {incident.id} by '{actor['username']}'")
        return incident

    @staticmethod
    def stats():
        def grouped(column, keys):
            counts = dict(db.session.query(column, func.count(Incident.id)).group_by(column).all())
            return {key: counts.get(key, 0) for key in keys}

        return {
            "total_incidents": Incident.query.count(),
            "open_incidents": Incident.query.filter(Incident.status.in_(OPEN_STATUSES)).count(),
            "unassigned_incidents": Incident.query.filter(Incident.assigned_analyst_id.is_(None),
                                                          Incident.status.in_(OPEN_STATUSES)).count(),
            "by_severity": grouped(Incident.severity, SEVERITIES),
            "by_status": grouped(Incident.status, INCIDENT_FLOW),
            "by_category": grouped(Incident.category, INCIDENT_CATEGORIES),
        }
