"""Incidents and Investigation Notes tables. Owner: Elie Medawar."""
from common.db import db, iso, utcnow
from common.enums import INCIDENT_CATEGORIES, INCIDENT_FLOW, SEVERITIES

if "assets" not in db.metadata.tables:
    # Marc's Asset model (models/assets.py) is not merged yet. Declare just the key of the
    # "assets" table so the foreign key below can be defined. app_factory never creates
    # placeholder tables; once models/assets.py exists it is imported first and used instead.
    db.Table("assets", db.metadata, db.Column("id", db.Integer, primary_key=True), info={"placeholder": True})


class Incident(db.Model):
    __tablename__ = "incidents"

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(150), nullable=False)
    description = db.Column(db.String(2000), nullable=False)
    category = db.Column(db.String(30), nullable=False)
    severity = db.Column(db.String(10), nullable=False)
    reporter_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False, index=True)
    asset_id = db.Column(db.Integer, db.ForeignKey("assets.id", ondelete="SET NULL"), index=True)
    assigned_analyst_id = db.Column(db.Integer, db.ForeignKey("users.id", ondelete="SET NULL"), index=True)
    status = db.Column(db.String(25), nullable=False, default="Open")
    created_at = db.Column(db.DateTime, nullable=False, default=utcnow)
    resolved_at = db.Column(db.DateTime)     # resolution date, set when the incident reaches "Resolved"

    notes = db.relationship("InvestigationNote", backref="incident", cascade="all, delete-orphan",
                            order_by="InvestigationNote.created_at")

    __table_args__ = (
        db.CheckConstraint(f"severity IN {SEVERITIES}", name="ck_incidents_severity"),
        db.CheckConstraint(f"status IN {INCIDENT_FLOW}", name="ck_incidents_status"),
        db.CheckConstraint(f"category IN {INCIDENT_CATEGORIES}", name="ck_incidents_category"),
    )

    def to_dict(self, with_notes=False):
        data = {
            "id": self.id,
            "title": self.title,
            "description": self.description,
            "category": self.category,
            "severity": self.severity,
            "reporter_id": self.reporter_id,
            "asset_id": self.asset_id,
            "assigned_analyst_id": self.assigned_analyst_id,
            "status": self.status,
            "created_at": iso(self.created_at),
            "resolved_at": iso(self.resolved_at),
        }
        if with_notes:
            data["investigation_notes"] = [note.to_dict() for note in self.notes]
        return data


class InvestigationNote(db.Model):
    __tablename__ = "investigation_notes"

    id = db.Column(db.Integer, primary_key=True)
    incident_id = db.Column(db.Integer, db.ForeignKey("incidents.id", ondelete="CASCADE"), nullable=False, index=True)
    analyst_id = db.Column(db.Integer, db.ForeignKey("users.id", ondelete="SET NULL"))   # author of the note
    content = db.Column(db.String(2000), nullable=False)
    created_at = db.Column(db.DateTime, nullable=False, default=utcnow)

    def to_dict(self):
        return {
            "id": self.id,
            "incident_id": self.incident_id,
            "analyst_id": self.analyst_id,
            "content": self.content,
            "created_at": iso(self.created_at),
        }
