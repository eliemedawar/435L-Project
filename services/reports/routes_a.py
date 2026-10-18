"""Security Reports Service (port 5006): summary, incident and activity reports. Owner: Elie Medawar.

Marc's reports app registers this blueprint:  create_service_app("reports", reports_a_bp, reports_b_bp)

Every report is built from the other services' GET /internal/stats endpoints (service-to-service
API calls with the X-Service-Key header); this service has no tables of its own.
"""
from flask import Blueprint, g

from common.auth import require_auth
from common.clients import get_service
from common.db import iso, utcnow
from common.errors import APIError, success
from common.roles import ADMIN, AUDITOR

reports_a_bp = Blueprint("reports_a", __name__)


class ReportSourceUnavailable(APIError):
    status_code = 503


class ReportBuilder:
    """Collects statistics from the source services and wraps them in a common report envelope."""

    def __init__(self, report_type):
        self.report_type = report_type
        self.unavailable = []

    def collect(self, service_name, required=False):
        stats = get_service(service_name, "/internal/stats")
        if stats is None:
            if required:
                raise ReportSourceUnavailable(f"Cannot generate the {self.report_type} report: "
                                              f"the {service_name} service is unavailable")
            self.unavailable.append(service_name)
        return stats or {}

    def build(self, body):
        report = {
            "report_type": self.report_type,
            "generated_at": iso(utcnow()),
            "generated_by": g.user["username"],
            **body,
        }
        if self.unavailable:
            report["unavailable_sources"] = self.unavailable
        return report


# Developed by: Elie Medawar
@reports_a_bp.route("/reports/summary", methods=["GET"])
@require_auth(roles=[ADMIN, AUDITOR])
def security_summary_report():
    builder = ReportBuilder("security summary")
    users = builder.collect("users")
    assets = builder.collect("assets")
    incidents = builder.collect("incidents")
    threats = builder.collect("threats")
    report = builder.build({
        "users": users.get("total_users"),
        "assets": assets.get("total_assets"),
        "incidents": incidents.get("total_incidents"),
        "open_incidents": incidents.get("open_incidents"),
        "critical_incidents": incidents.get("by_severity", {}).get("Critical"),
        "threats": threats.get("total_threats"),
        "critical_threats": threats.get("by_severity", {}).get("Critical"),
    })
    return success(report, "Security summary report generated")


# Developed by: Elie Medawar
@reports_a_bp.route("/reports/incidents", methods=["GET"])
@require_auth(roles=[ADMIN, AUDITOR])
def incident_report():
    builder = ReportBuilder("incident")
    stats = builder.collect("incidents", required=True)
    report = builder.build({
        "total_incidents": stats["total_incidents"],
        "open_incidents": stats["open_incidents"],
        "unassigned_open_incidents": stats["unassigned_incidents"],
        "incidents_by_severity": stats["by_severity"],
        "incidents_by_status": stats["by_status"],
        "incidents_by_category": stats["by_category"],
    })
    return success(report, "Incident report generated")


# Developed by: Elie Medawar
@reports_a_bp.route("/reports/activity", methods=["GET"])
@require_auth(roles=[ADMIN, AUDITOR])
def activity_report():
    builder = ReportBuilder("activity")
    stats = builder.collect("logs", required=True)
    attempts = stats["login_attempts"]
    report = builder.build({
        "total_user_activities": stats["total_activities"],
        "login_attempts": attempts,
        "successful_logins": stats["successful_logins"],
        "failed_login_attempts": stats["failed_logins"],
        "failed_login_rate_percent": round(100 * stats["failed_logins"] / attempts, 1) if attempts else 0.0,
        "unauthorized_access_attempts": stats["unauthorized_attempts"],
        "activities_by_severity": stats["by_severity"],
        "activities_by_service": stats["by_service"],
        "most_performed_actions": stats["most_performed_actions"],
    })
    return success(report, "Activity report generated")
