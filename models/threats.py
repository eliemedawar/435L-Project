"""Threat indicators. Developed by: Marc Bteich."""
from common.db import db, iso, utcnow
from common.enums import SEVERITIES, THREAT_TYPES


class Threat(db.Model):
    __tablename__ = 'threats'
    id = db.Column(db.Integer, primary_key=True)
    threat_type = db.Column(db.String(30), nullable=False)
    threat_value = db.Column(db.String(255), nullable=False)
    description = db.Column(db.String(2000), nullable=False)
    severity = db.Column(db.String(10), nullable=False)
    source = db.Column(db.String(150), nullable=False)
    date_added = db.Column(db.DateTime, nullable=False, default=utcnow)
    __table_args__ = (
        db.UniqueConstraint('threat_type', 'threat_value', name='uq_threat_type_value'),
        db.CheckConstraint(f'threat_type IN {THREAT_TYPES}', name='ck_threats_type'),
        db.CheckConstraint(f'severity IN {SEVERITIES}', name='ck_threats_severity'),
    )

    def to_dict(self):
        return dict(id=self.id, threat_type=self.threat_type, threat_value=self.threat_value,
                    description=self.description, severity=self.severity, source=self.source,
                    date_added=iso(self.date_added))
