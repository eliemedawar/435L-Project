"""Vulnerability records. Developed by: Marc Bteich."""
from common.db import db, iso, utcnow
from common.enums import SEVERITIES, VULNERABILITY_FLOW


class Vulnerability(db.Model):
    __tablename__ = 'vulnerabilities'
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(150), nullable=False)
    description = db.Column(db.String(2000), nullable=False)
    cve_id = db.Column(db.String(40), nullable=False)
    cvss_score = db.Column(db.Numeric(3, 1), nullable=False)
    severity = db.Column(db.String(10), nullable=False)
    asset_id = db.Column(db.Integer, db.ForeignKey('assets.id'), nullable=False, index=True)
    discovery_source = db.Column(db.String(150), nullable=False)
    status = db.Column(db.String(25), nullable=False, default='Open')
    created_at = db.Column(db.DateTime, nullable=False, default=utcnow)
    resolution_date = db.Column(db.DateTime)
    __table_args__ = (
        db.CheckConstraint('cvss_score BETWEEN 0 AND 10', name='ck_vulnerabilities_cvss'),
        db.CheckConstraint(f'severity IN {SEVERITIES}', name='ck_vulnerabilities_severity'),
        db.CheckConstraint(f'status IN {VULNERABILITY_FLOW}', name='ck_vulnerabilities_status'),
    )

    def to_dict(self):
        return dict(id=self.id, title=self.title, description=self.description, cve_id=self.cve_id,
                    cvss_score=float(self.cvss_score), severity=self.severity, asset_id=self.asset_id,
                    discovery_source=self.discovery_source, status=self.status, created_at=iso(self.created_at),
                    resolution_date=iso(self.resolution_date))
