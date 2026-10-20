"""Organizational assets. Developed by: Marc Bteich."""
from common.db import db
from common.enums import ASSET_STATUSES, SEVERITIES

ASSET_TYPES = ("Server", "Workstation", "Database", "Application", "Network Device", "Cloud Resource")


class Asset(db.Model):
    __tablename__ = "assets"

    id = db.Column(db.Integer, primary_key=True)
    asset_name = db.Column(db.String(150), nullable=False)
    asset_type = db.Column(db.String(30), nullable=False)
    ip_address = db.Column(db.String(45), nullable=False)
    operating_system = db.Column(db.String(100))
    owner_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False, index=True)
    department = db.Column(db.String(100), nullable=False)
    location = db.Column(db.String(150))
    criticality = db.Column(db.String(10), nullable=False)
    status = db.Column(db.String(25), nullable=False, default="Active")

    __table_args__ = (
        db.CheckConstraint("length(trim(asset_name)) > 0", name="ck_assets_name"),
        db.CheckConstraint(f"asset_type IN {ASSET_TYPES}", name="ck_assets_type"),
        db.CheckConstraint(f"criticality IN {SEVERITIES}", name="ck_assets_criticality"),
        db.CheckConstraint(f"status IN {ASSET_STATUSES}", name="ck_assets_status"),
    )

    def to_dict(self):
        return {field: getattr(self, field) for field in (
            "id", "asset_name", "asset_type", "ip_address", "operating_system",
            "owner_id", "department", "location", "criticality", "status",
        )}
