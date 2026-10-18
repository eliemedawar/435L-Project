"""Logs table (security audit records). Owner: Elie Medawar."""
from sqlalchemy import event

from common.db import db, iso, utcnow
from common.enums import LOG_SEVERITIES


class Log(db.Model):
    __tablename__ = "logs"

    id = db.Column(db.Integer, primary_key=True)
    # ON DELETE SET NULL: deleting a user must not delete (or block because of) their audit history.
    user_id = db.Column(db.Integer, db.ForeignKey("users.id", ondelete="SET NULL"), index=True)
    username = db.Column(db.String(30))     # copy of the username at the time of the action, kept if the user is deleted
    action = db.Column(db.String(50), nullable=False, index=True)
    description = db.Column(db.String(500), nullable=False)
    severity = db.Column(db.String(20), nullable=False, default="Information")
    related_service = db.Column(db.String(30), nullable=False)
    timestamp = db.Column(db.DateTime, nullable=False, default=utcnow, index=True)

    __table_args__ = (
        db.CheckConstraint(f"severity IN {LOG_SEVERITIES}", name="ck_logs_severity"),
    )

    def to_dict(self):
        return {
            "id": self.id,
            "user_id": self.user_id,
            "username": self.username,
            "action": self.action,
            "description": self.description,
            "severity": self.severity,
            "related_service": self.related_service,
            "timestamp": iso(self.timestamp),
        }


@event.listens_for(Log, "before_update")
def _logs_are_immutable(mapper, connection, target):
    """Audit logs must never change after creation (only an admin may delete them)."""
    raise ValueError("Audit log records cannot be modified")
