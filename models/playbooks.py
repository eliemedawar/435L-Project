"""Playbooks and response actions. Developed by: Marc Bteich."""
from common.db import db, iso, utcnow
from common.enums import ACTION_STATUSES, INCIDENT_CATEGORIES, SEVERITIES


class Playbook(db.Model):
    __tablename__ = 'playbooks'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(150), nullable=False)
    description = db.Column(db.String(2000), nullable=False)
    incident_category = db.Column(db.String(30), nullable=False)
    severity = db.Column(db.String(10), nullable=False)
    created_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    created_at = db.Column(db.DateTime, nullable=False, default=utcnow)
    actions = db.relationship('ResponseAction', backref='playbook', cascade='all, delete-orphan',
                              passive_deletes=True, order_by='ResponseAction.step_number')
    __table_args__ = (
        db.CheckConstraint(f'incident_category IN {INCIDENT_CATEGORIES}', name='ck_playbooks_category'),
        db.CheckConstraint(f'severity IN {SEVERITIES}', name='ck_playbooks_severity'),
    )

    def to_dict(self, include_actions=False):
        result=dict(id=self.id,name=self.name,description=self.description,incident_category=self.incident_category,
                    severity=self.severity,created_by=self.created_by,created_at=iso(self.created_at))
        if include_actions:
            result['actions']=[a.to_dict() for a in self.actions]
        return result


class ResponseAction(db.Model):
    __tablename__ = 'response_actions'
    id = db.Column(db.Integer, primary_key=True)
    playbook_id = db.Column(db.Integer, db.ForeignKey('playbooks.id',ondelete='CASCADE'),nullable=False,index=True)
    description = db.Column(db.String(2000),nullable=False)
    step_number = db.Column(db.Integer,nullable=False)
    status = db.Column(db.String(20),nullable=False,default='Pending')
    assigned_user_id = db.Column(db.Integer,db.ForeignKey('users.id',ondelete='SET NULL'),index=True)
    completion_date = db.Column(db.DateTime)
    execution_history = db.Column(db.JSON,nullable=False,default=list,server_default=db.text("'[]'"))
    __table_args__ = (
        db.UniqueConstraint('playbook_id','step_number',name='uq_action_step'),
        db.CheckConstraint('step_number > 0',name='ck_action_step'),
        db.CheckConstraint(f'status IN {ACTION_STATUSES}',name='ck_action_status'),
    )

    def to_dict(self):
        return dict(id=self.id,playbook_id=self.playbook_id,description=self.description,step_number=self.step_number,
                    status=self.status,assigned_user_id=self.assigned_user_id,completion_date=iso(self.completion_date),
                    execution_history=self.execution_history)
