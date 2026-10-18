"""REST endpoints of the Incident Management Service (port 5003)."""
from flask import Blueprint, g, request

from common.auth import require_auth, require_service
from common.errors import success
from common.roles import ADMIN, ANALYST, AUDITOR, USER
from common.validators import get_json_body
from services.incidents.service import IncidentService

incidents_bp = Blueprint("incidents", __name__)


# Developed by: Elie Medawar
@incidents_bp.route("/incidents", methods=["POST"])
@require_auth(roles=[ADMIN, USER])
def create_incident():
    incident = IncidentService.create(get_json_body(), g.user)
    return success(incident.to_dict(), "Incident created successfully", 201)


# Developed by: Elie Medawar
@incidents_bp.route("/incidents", methods=["GET"])
@require_auth(roles=[ADMIN, AUDITOR])
def get_all_incidents():
    incidents = IncidentService.list_all(request.args.to_dict())
    return success({"count": len(incidents), "incidents": [i.to_dict() for i in incidents]},
                   "Incidents retrieved successfully")


# Developed by: Elie Medawar
@incidents_bp.route("/incidents/<int:incident_id>", methods=["GET"])
@require_auth(roles=[ADMIN, AUDITOR, ANALYST, USER])
def get_incident(incident_id):
    incident = IncidentService.get_for(incident_id, g.user)
    return success(incident.to_dict(with_notes=True), "Incident retrieved successfully")


# Developed by: Elie Medawar
@incidents_bp.route("/incidents/<int:incident_id>/assign", methods=["PUT"])
@require_auth(roles=[ADMIN])
def assign_incident(incident_id):
    incident = IncidentService.assign(incident_id, get_json_body(), g.user)
    return success(incident.to_dict(), "Incident assigned successfully")


# Developed by: Elie Medawar
@incidents_bp.route("/incidents/<int:incident_id>/status", methods=["PUT"])
@require_auth(roles=[ADMIN, ANALYST])
def update_incident_status(incident_id):
    incident = IncidentService.update_status(incident_id, get_json_body(), g.user)
    return success(incident.to_dict(), f"Incident status updated to '{incident.status}'")


# Developed by: Elie Medawar
@incidents_bp.route("/incidents/<int:incident_id>/notes", methods=["POST"])
@require_auth(roles=[ADMIN, ANALYST])
def add_investigation_note(incident_id):
    incident = IncidentService.add_note(incident_id, get_json_body(), g.user)
    return success(incident.to_dict(with_notes=True), "Investigation note added successfully", 201)


# Developed by: Elie Medawar
@incidents_bp.route("/internal/stats", methods=["GET"])
@require_service
def internal_stats():
    return success(IncidentService.stats())
