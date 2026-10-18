"""Notifications table. Owner: Elie Medawar."""
from common.db import db, iso, utcnow
from common.enums import NOTIFICATION_STATUSES, NOTIFICATION_TYPES, SEVERITIES


class Notification(db.Model):
    __tablename__ = "notifications"

    id = db.Column(db.Integer, primary_key=True)
    # A user's notifications are personal: they are removed together with the user account.
    user_id = db.Column(db.Integer, db.ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    title = db.Column(db.String(150), nullable=False)
    message = db.Column(db.String(1000), nullable=False)
    notification_type = db.Column(db.String(30), nullable=False)
    severity = db.Column(db.String(10), nullable=False)
    status = db.Column(db.String(10), nullable=False, default="Unread")
    created_at = db.Column(db.DateTime, nullable=False, default=utcnow)
    read_at = db.Column(db.DateTime)

    __table_args__ = (
        db.CheckConstraint(f"notification_type IN {NOTIFICATION_TYPES}", name="ck_notifications_type"),
        db.CheckConstraint(f"severity IN {SEVERITIES}", name="ck_notifications_severity"),
        db.CheckConstraint(f"status IN {NOTIFICATION_STATUSES}", name="ck_notifications_status"),
    )

    def to_dict(self):
        return {
            "id": self.id,
            "user_id": self.user_id,
            "title": self.title,
            "message": self.message,
            "notification_type": self.notification_type,
            "severity": self.severity,
            "status": self.status,
            "created_at": iso(self.created_at),
            "read_at": iso(self.read_at),
        }
