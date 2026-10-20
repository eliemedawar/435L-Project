"""Idempotent, additive sample data. Developed by: Marc Bteich.

Run python -m database.seed. Generated account passwords are written ONLY to
.local/seed-credentials.json (locally excluded), never printed or committed.
All indicators, CVEs and scenarios are labelled laboratory examples, not claims
about real attacks or vulnerabilities. Seeded lifecycle states are snapshots.
"""
import json
from pathlib import Path
import secrets
from datetime import timedelta
from common.app_factory import create_service_app
from common.config import ROOT_DIR
from common.db import db, iso, utcnow
from common.enums import (ACTION_STATUSES, ACCOUNT_STATUSES, ASSET_STATUSES, INCIDENT_CATEGORIES,
                          INCIDENT_FLOW, LOG_SEVERITIES, NOTIFICATION_TYPES, SEVERITIES, VULNERABILITY_FLOW)
from database.migrate import upgrade_action_history
from models.assets import ASSET_TYPES, Asset
from models.incidents import Incident, InvestigationNote
from models.logs import Log
from models.notifications import Notification
from models.playbooks import Playbook, ResponseAction
from models.threats import Threat
from models.users import User
from models.vulnerabilities import Vulnerability


def seed(credentials_path=None):
    path=Path(credentials_path or ROOT_DIR/'.local/seed-credentials.json').resolve()
    if not path.is_relative_to((ROOT_DIR/'.local').resolve()):
        raise ValueError('Credentials must remain in the locally excluded .local directory')
    path.parent.mkdir(parents=True,exist_ok=True)
    credentials=json.loads(path.read_text()) if path.exists() else {}
    upgrade_action_history()
    users={}
    accounts=[('admin','admin','Active'),('admin2','admin','Active'),('lara','analyst','Active'),
              ('nadia','auditor','Active'),('rami','user','Active'),
              ('inactive_lab','user','Inactive'),('suspended_lab','user','Suspended')]
    for username,role,status in accounts:
        user=User.query.filter_by(username=username).first()
        if user is None:
            user=User(username=username,full_name='Lab '+username.title(),email=username+'@example.test',
                      department='Security Lab',role=role,account_status=status)
            password=secrets.token_urlsafe(24)+'Aa!1'
            user.set_password(password)
            db.session.add(user)
            credentials[username]=dict(username=username,password=password,role=role)
        users[username]=user
    db.session.flush()
    # Save recovery credentials before committing user creation. A failed seed
    # can be retried without resetting any pre-existing account's password.
    temporary=path.with_suffix('.tmp')
    temporary.write_text(json.dumps(credentials,indent=2)+'\n',encoding='utf-8')
    temporary.replace(path)
    assets=[]
    for i,kind in enumerate(ASSET_TYPES):
        name='Seed '+kind
        asset=Asset.query.filter_by(asset_name=name).first()
        if asset is None:
            asset=Asset(asset_name=name,asset_type=kind,ip_address=f'192.0.2.{100+i}',owner_id=users['admin'].id,
                        department='Security Lab' if i%2==0 else 'Research Lab',location='University lab',
                        operating_system='Lab Linux' if i<2 else None,criticality=SEVERITIES[i%4],status=ASSET_STATUSES[i%3])
            db.session.add(asset)
        assets.append(asset)
    db.session.flush()
    indicators=[('IP Address','192.0.2.200'),('IP Address','2001:db8::200'),('Domain','indicator.example.test'),
                ('File Hash','a'*32),('File Hash','b'*40),('File Hash','c'*64),
                ('Malware Signature','LAB-SIGNATURE-EXAMPLE'),('Other','LAB-INDICATOR-EXAMPLE')]
    for i,(kind,value) in enumerate(indicators):
        if not Threat.query.filter_by(threat_type=kind,threat_value=value).first():
            db.session.add(Threat(threat_type=kind,threat_value=value,description='Synthetic lab indicator for demonstrations',
                                 severity=SEVERITIES[i%4],source='University lab dataset'))
    now=utcnow()
    for i,status in enumerate(VULNERABILITY_FLOW):
        title=f'Seed remediation scenario {i+1}'
        if not Vulnerability.query.filter_by(title=title).first():
            db.session.add(Vulnerability(title=title,description='Synthetic CVE-format lab example; no real CVE claim',
                cve_id=f'CVE-2026-{9000+i}',cvss_score=(2.1,5.5,8.1,9.8,7.5)[i],severity=SEVERITIES[i%4],
                asset_id=assets[i%len(assets)].id,discovery_source='Lab scanner simulation dataset',status=status,
                created_at=now-timedelta(days=7),resolution_date=now if status in ('Resolved','Closed') else None))
    for i,category in enumerate(INCIDENT_CATEGORIES):
        title='Seed '+category+' incident'
        incident=Incident.query.filter_by(title=title).first()
        if incident is None:
            status=INCIDENT_FLOW[i%5]
            incident=Incident(title=title,description='Synthetic lab incident snapshot',category=category,
                severity=SEVERITIES[i%4],reporter_id=users['rami'].id,asset_id=assets[i%len(assets)].id,
                assigned_analyst_id=users['lara'].id,status=status,created_at=now-timedelta(days=5),
                resolved_at=now if status in ('Resolved','Closed') else None)
            db.session.add(incident)
            db.session.flush()
            db.session.add(InvestigationNote(incident_id=incident.id,analyst_id=users['lara'].id,
                                             content='Seed note: review lab telemetry; scenario data only'))
        name='Seed '+category+' response'
        playbook=Playbook.query.filter_by(name=name).first()
        if playbook is None:
            playbook=Playbook(name=name,description='Ordered laboratory response procedure',incident_category=category,
                              severity=SEVERITIES[i%4],created_by=users['admin'].id)
            db.session.add(playbook)
            db.session.flush()
            for step,status in enumerate(ACTION_STATUSES,1):
                history=[dict(actor_id=users['lara'].id,at=iso(now),from_status=ACTION_STATUSES[j-1] if j else None,
                              to_status=s,assigned_user_id=users['lara'].id,
                              completion_date=iso(now) if s=='Completed' else None,source='seed snapshot')
                         for j,s in enumerate(ACTION_STATUSES[:step])]
                db.session.add(ResponseAction(playbook_id=playbook.id,description=('Collect lab evidence','Contain lab host','Verify recovery')[step-1],
                    step_number=step,status=status,assigned_user_id=users['lara'].id,
                    completion_date=now if status=='Completed' else None,execution_history=history))
    for i,kind in enumerate(NOTIFICATION_TYPES):
        title='Seed '+kind
        if not Notification.query.filter_by(title=title).first():
            db.session.add(Notification(user_id=users['admin'].id,title=title,message='Synthetic sample notification',
                notification_type=kind,severity=SEVERITIES[i%4],status='Read' if i%2 else 'Unread',read_at=now if i%2 else None))
    for severity in LOG_SEVERITIES:
        description='Seed audit example '+severity
        if not Log.query.filter_by(description=description).first():
            db.session.add(Log(user_id=users['admin'].id,username='admin',action='SEED_SAMPLE',description=description,
                              severity=severity,related_service='users'))
    db.session.commit()
    return {table:db.session.query(model).count() for table,model in (
        ('users',User),('assets',Asset),('incidents',Incident),('investigation_notes',InvestigationNote),('threats',Threat),
        ('logs',Log),('vulnerabilities',Vulnerability),('notifications',Notification),('playbooks',Playbook),('response_actions',ResponseAction))}


if __name__=='__main__':
    app=create_service_app('users')
    with app.app_context():
        print(json.dumps(seed(),indent=2))
    print('Seed complete. Private generated credentials: .local/seed-credentials.json')
