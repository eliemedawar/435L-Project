"""Real response workflow tests. Developed by: Marc Bteich."""
import json
from unittest.mock import patch
from database.testing import LiveBackend


class PlaybookTests(LiveBackend):
    SERVICES=LiveBackend.SERVICES+('playbooks',)

    def create(self):
        return self.call('playbooks','POST','/playbooks',201,json=dict(name='Lab response',description='Investigate lab event',incident_category='Malware',severity='High'))

    def add(self,pid,number=1,**values):
        return self.call('playbooks','POST',f'/playbooks/{pid}/actions',201,role='analyst',
                         json=dict(description='Contain lab host',step_number=number,**values))

    def test_order_lifecycle_completion_durable_history_and_cascade(self):
        pid=self.create()['id']
        self.add(pid,2)
        action=self.add(pid,1)
        aid=action['id']
        detail=self.call('playbooks','GET',f'/playbooks/{pid}')
        self.assertEqual([a['step_number'] for a in detail['actions']],[1,2])
        self.call('playbooks','PUT',f'/actions/{aid}/status',400,json={'status':'Completed'})
        self.call('playbooks','PUT',f'/actions/{aid}/status',400,json={'status':'In Progress'})
        self.call('playbooks','PUT',f'/actions/{aid}/status',json={'assigned_user_id':self.ids['analyst']})
        self.call('playbooks','PUT',f'/actions/{aid}/status',json={'status':'In Progress'})
        with patch.dict('os.environ',{'LOGS_URL':'http://127.0.0.1:1'}):
            completed=self.call('playbooks','PUT',f'/actions/{aid}/status',role='analyst',json={'status':'Completed'})
        self.assertIsNotNone(completed['completion_date'])
        history=json.loads(self.sql('SELECT execution_history FROM response_actions WHERE id=?',(aid,))[0][0])
        self.assertEqual([event['to_status'] for event in history],['Pending','Pending','In Progress','Completed'])
        self.assertEqual(history[-1]['actor_id'],self.ids['analyst'])
        self.call('playbooks','PUT',f'/actions/{aid}/status',400,json={'status':'In Progress'})
        with patch.dict('os.environ',{'LOGS_URL':'http://127.0.0.1:1'}):
            self.call('playbooks','DELETE',f'/playbooks/{pid}',503)
        self.call('playbooks','GET',f'/playbooks/{pid}')
        self.call('playbooks','DELETE',f'/playbooks/{pid}')
        self.assertEqual(self.sql('SELECT id FROM response_actions WHERE playbook_id=?',(pid,)),[])
        self.assertTrue(self.sql("SELECT id FROM logs WHERE action='PLAYBOOK_DELETED'"))
        archived=[json.loads(row[0]) for row in self.sql("SELECT description FROM logs WHERE action='ACTION_HISTORY_ARCHIVED'")]
        self.assertTrue(any(row['action_id']==aid and row['event']['to_status']=='Completed' for row in archived))

    def test_uniqueness_validation_and_missing_resources(self):
        pid=self.create()['id']
        action=self.add(pid)
        self.call('playbooks','POST',f'/playbooks/{pid}/actions',409,json={'description':'Duplicate','step_number':1})
        self.add(self.create()['id'],1)
        for body in ({'description':'x','step_number':0},{'description':'x','step_number':True},
                     {'description':'x','step_number':3,'assigned_user_id':999999},{'description':'','step_number':3},
                     {'description':'x','step_number':3,'execution_history':[]}):
            self.call('playbooks','POST',f'/playbooks/{pid}/actions',400,json=body)
        for body in ({},{'status':'bad'},{'status':'Pending'},{'completion_date':'fake'},{'assigned_user_id':True}):
            self.call('playbooks','PUT',f"/actions/{action['id']}/status",400,json=body)
        for method,path,body in [('GET','/playbooks/999999',None),('DELETE','/playbooks/999999',None),
                                 ('POST','/playbooks/999999/actions',{'description':'x','step_number':1}),
                                 ('PUT','/actions/999999/status',{'status':'In Progress'})]:
            self.call('playbooks',method,path,404,**({'json':body} if body else {}))
        for body in ({},[],None,{'name':'x','description':'x','incident_category':'bad','severity':'High'}):
            self.call('playbooks','POST','/playbooks',400,json=body)
        with patch.dict('os.environ',{'USERS_URL':'http://127.0.0.1:1'}):
            self.call('playbooks','PUT',f"/actions/{action['id']}/status",503,json={'assigned_user_id':self.ids['analyst']})

    def test_complete_role_and_auth_matrix(self):
        for role in ('admin','analyst','auditor','user'):
            pid=self.create()['id']
            aid=self.add(pid)['id']
            for method,path,body,allowed,ok in [
                ('POST','/playbooks',dict(name='Test',description='Test',incident_category='Malware',severity='Low'),('admin',),201),
                ('GET','/playbooks',None,('admin','analyst','auditor'),200),
                ('GET',f'/playbooks/{pid}',None,('admin','analyst','auditor'),200),
                ('POST',f'/playbooks/{pid}/actions',dict(description='Next',step_number=2),('admin','analyst'),201),
                ('PUT',f'/actions/{aid}/status',dict(assigned_user_id=self.ids['analyst']),('admin','analyst'),200),
                ('DELETE',f'/playbooks/{pid}',None,('admin',),200)]:
                self.call('playbooks',method,path,ok if role in allowed else 403,role=role,**({'json':body} if body else {}))
                self.call('playbooks',method,path,401,role=None)

    def test_history_column_migration_is_idempotent(self):
        from database.migrate import upgrade_action_history
        from common.db import db
        # A separate old-shape SQLite DB verifies the real upgrade, not a mock.
        from flask import Flask
        app=Flask('old-action-schema')
        app.config['SQLALCHEMY_DATABASE_URI']='sqlite:///'+(self.dbfile.parent/'old.db').as_posix()
        db.init_app(app)
        with app.app_context():
            from sqlalchemy import text, inspect
            with db.engine.begin() as c:
                c.execute(text('CREATE TABLE response_actions (id INTEGER PRIMARY KEY)'))
                c.execute(text('INSERT INTO response_actions VALUES (1)'))
            upgrade_action_history()
            upgrade_action_history()
            with db.engine.connect() as c:
                self.assertEqual(c.execute(text('SELECT execution_history FROM response_actions')).scalar(),'[]')
            self.assertIn('execution_history',[c['name'] for c in inspect(db.engine).get_columns('response_actions')])
            db.engine.dispose()
