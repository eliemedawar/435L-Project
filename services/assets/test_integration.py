"""Real HTTP integration tests on an isolated DB. Developed by: Marc Bteich.

Run in a fresh process: python -m unittest services.assets.test_integration -v
No services need to be running. Never touches database/sidrms.db or local .env.
"""
import os
from contextlib import closing
from pathlib import Path
import secrets
import sqlite3
import tempfile
import threading
import unittest
from unittest.mock import patch

import requests
from werkzeug.serving import WSGIRequestHandler, make_server

ROOT = Path(__file__).resolve().parents[2]


class QuietHandler(WSGIRequestHandler):
    def log_request(self, *args, **kwargs):
        pass


class AssetsHTTPTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        (ROOT / ".local").mkdir(exist_ok=True)
        cls.temp = tempfile.TemporaryDirectory(dir=ROOT / ".local")
        cls.dbfile = Path(cls.temp.name) / "integration.db"
        cls.password = secrets.token_hex(12) + "Aa!1"
        cls.key = secrets.token_hex(32)
        cls.env = patch.dict(os.environ, {
            "DATABASE_URL": "sqlite:///" + cls.dbfile.as_posix(),
            "JWT_SECRET": secrets.token_hex(32), "SERVICE_KEY": cls.key, "FLASK_DEBUG": "0",
        })
        cls.env.start()
        cls.addClassCleanup(cls.env.stop)
        with closing(sqlite3.connect(cls.dbfile)) as connection:
            connection.executescript((ROOT / "database/schema.sql").read_text())

        # Import only after test configuration is established.
        from common.db import db
        from models.users import User
        from services.assets.app import app as assets
        from services.users.app import app as users
        from services.logs.app import app as logs
        cls.apps = (assets, users, logs)
        cls.orm = db
        cls.servers = []
        cls.urls = {}
        for name, app in (("logs", logs), ("users", users), ("assets", assets)):
            server = make_server("127.0.0.1", 0, app, threaded=True, request_handler=QuietHandler)
            thread = threading.Thread(target=server.serve_forever, daemon=True)
            thread.start()
            cls.servers.append((server, thread))
            cls.urls[name] = f"http://127.0.0.1:{server.server_port}"
            os.environ[f"{name.upper()}_URL"] = cls.urls[name]
        with users.app_context():
            admin = User(full_name="Integration Admin", username="test_admin", email="admin@example.test",
                         department="Security", role="admin")
            admin.set_password(cls.password)
            db.session.add(admin)
            db.session.commit()
            cls.owner = admin.id
        cls.tokens = {}
        response = requests.post(cls.urls['users'] + '/users/login',
                                 json={"username": "test_admin", "password": cls.password}, timeout=10)
        assert response.status_code == 200, response.text
        cls.tokens['admin'] = response.json()['data']['token']
        for role in ("analyst", "auditor", "user"):
            response = requests.post(cls.urls['users'] + '/users/register', headers=cls.headers('admin'), json={
                "full_name": f"Integration {role}", "username": f"test_{role}", "email": f"{role}@example.test",
                "password": cls.password, "department": "Security", "role": role,
            }, timeout=10)
            assert response.status_code == 201, response.text
            response = requests.post(cls.urls['users'] + '/users/login',
                                     json={"username": f"test_{role}", "password": cls.password}, timeout=10)
            assert response.status_code == 200, response.text
            cls.tokens[role] = response.json()['data']['token']

    @classmethod
    def tearDownClass(cls):
        for server, thread in cls.servers:
            server.shutdown()
            server.server_close()
            thread.join(timeout=5)
        for app in cls.apps:
            with app.app_context():
                cls.orm.session.remove()
                cls.orm.engine.dispose()
        cls.temp.cleanup()

    @classmethod
    def headers(cls, role):
        return {"Authorization": "Bearer " + cls.tokens[role]}

    def call(self, method, path, expected=200, role="admin", **kwargs):
        headers = kwargs.pop("headers", self.headers(role) if role else {})
        response = requests.request(method, self.urls['assets'] + path, headers=headers, timeout=10, **kwargs)
        self.assertEqual(response.status_code, expected, response.text)
        body = response.json()
        self.assertEqual(body['status'], 'success' if expected < 400 else 'error')
        self.assertIsInstance(body['message'], str)
        if expected < 400:
            self.assertIn('data', body)
        return body.get('data')

    def payload(self, **changes):
        data = {"asset_name": "Lab Server", "asset_type": "Server", "ip_address": "192.0.2.10",
                "owner_id": self.owner, "department": "Security", "criticality": "High"}
        data.update(changes)
        return data

    def create(self, **changes):
        return self.call('POST', '/assets', expected=201, json=self.payload(**changes))

    def sql(self, statement, args=()):
        with closing(sqlite3.connect(self.dbfile)) as connection, connection:
            connection.execute('PRAGMA foreign_keys=ON')
            cursor = connection.execute(statement, args)
            return cursor.fetchall()

    def test_01_create_update_delete_records_and_audit(self):
        asset = self.create(operating_system="Linux", location="Lab", criticality="Critical")
        aid = asset['id']
        self.assertEqual(asset['status'], 'Active')
        self.assertEqual(self.sql('SELECT asset_name,criticality FROM assets WHERE id=?', (aid,)),
                         [('Lab Server', 'Critical')])
        self.call('PUT', f'/assets/{aid}', json={"asset_name": "Updated Server", "owner_id": self.owner,
                  "department": "IT", "criticality": "Low", "status": "Under Maintenance"})
        self.assertEqual(self.call('GET', f'/assets/{aid}')['asset_name'], 'Updated Server')
        self.assertEqual(self.sql('SELECT department,status FROM assets WHERE id=?', (aid,)), [('IT', 'Under Maintenance')])
        self.call('DELETE', f'/assets/{aid}')
        self.assertEqual(self.sql('SELECT id FROM assets WHERE id=?', (aid,)), [])
        logs = self.sql("SELECT action,username,related_service FROM logs WHERE description LIKE ? ORDER BY id", (f'%asset {aid}%',))
        for action in ('ASSET_CREATED', 'ASSET_UPDATED', 'ASSET_DELETED'):
            self.assertIn((action, 'test_admin', 'assets'), logs)

    def test_02_complete_role_matrix(self):
        aid = self.create()['id']
        for role in ('admin', 'analyst', 'auditor', 'user'):
            with self.subTest(role=role):
                self.call('GET', '/assets', expected=200 if role in ('admin', 'auditor') else 403, role=role)
                for path in (f'/assets/{aid}', '/assets/search?name=Lab'):
                    self.call('GET', path, expected=403 if role == 'user' else 200, role=role)
                expected = 201 if role == 'admin' else 403
                self.call('POST', '/assets', expected=expected, role=role, json=self.payload())
                self.call('PUT', f'/assets/{aid}', expected=200 if role == 'admin' else 403,
                          role=role, json={'status': 'Inactive'})
                # Separate asset per role to exercise actual authorized deletion too.
                target = self.create()['id']
                self.call('DELETE', f'/assets/{target}', expected=200 if role == 'admin' else 403, role=role)
        self.assertGreaterEqual(self.sql("SELECT COUNT(*) FROM logs WHERE action='UNAUTHORIZED_ACCESS' AND related_service='assets'")[0][0], 11)

    def test_03_authentication_all_public_endpoints(self):
        for method, path in (('POST', '/assets'), ('PUT', '/assets/1'), ('DELETE', '/assets/1'),
                             ('GET', '/assets'), ('GET', '/assets/1'), ('GET', '/assets/search?name=Lab')):
            with self.subTest(method=method, path=path):
                self.call(method, path, expected=401, role=None)
                self.call(method, path, expected=401, headers={'Authorization': 'Bearer invalid'})
                self.call(method, path, expected=401, headers={'X-Service-Key': self.key})

    def test_04_validation_and_atomic_updates(self):
        bad = [dict(asset_name=' '), dict(asset_name=12), dict(asset_name='x'*151), dict(asset_type='Laptop'),
               dict(asset_type=[]), dict(ip_address='999.1.2.3'), dict(ip_address=1), dict(ip_address='fe80::1%eth0'),
               dict(criticality='Urgent'), dict(criticality={}), dict(status='Broken'), dict(status=None),
               dict(owner_id=True), dict(owner_id='1'), dict(owner_id=0), dict(owner_id=999999), dict(owner_id=10**30),
               dict(department=''), dict(department=[]), dict(location=10), dict(operating_system=False),
               dict(unexpected='x')]
        before = self.sql('SELECT COUNT(*) FROM assets')[0][0]
        for values in bad:
            with self.subTest(values=values):
                self.call('POST', '/assets', expected=400, json=self.payload(**values))
        for field in ('asset_name','asset_type','ip_address','owner_id','department','criticality'):
            data = self.payload()
            del data[field]
            self.call('POST', '/assets', expected=400, json=data)
        for body in ({}, [], None):
            self.call('POST', '/assets', expected=400, json=body)
        self.call('POST', '/assets', expected=400, data='{invalid', headers={**self.headers('admin'), 'Content-Type':'application/json'})
        self.assertEqual(self.sql('SELECT COUNT(*) FROM assets')[0][0], before)
        aid = self.create()['id']
        for values in ({}, {'asset_type':'Database'}, {'ip_address':'192.0.2.2'}, {'owner_id':999999},
                       {'asset_name':'Should roll back', 'status':'bad'}):
            self.call('PUT', f'/assets/{aid}', expected=400, json=values)
        self.assertEqual(self.call('GET', f'/assets/{aid}')['asset_name'], 'Lab Server')

    def test_05_search_all_filters_and_literal_input(self):
        aid = self.create(asset_name='Unique_Search_Asset%', department='Research', criticality='Critical',
                          asset_type='Database', ip_address='2001:0db8:0000::1')['id']
        for params in ({'name':'unique_search'}, {'type':'Database'}, {'ip':'2001:db8::1'},
                       {'department':'research'}, {'criticality':'Critical'},
                       {'name':'Unique_Search', 'type':'Database', 'department':'Research', 'criticality':'Critical'}):
            result = self.call('GET', '/assets/search', params=params)
            self.assertIn(aid, [a['id'] for a in result['assets']])
        self.assertEqual(self.call('GET', '/assets/search?name=Unique_Search&type=Server')['count'], 0)
        self.assertEqual(self.call('GET', '/assets/search', params={'name': "' OR 1=1 --"})['count'], 0)
        # SQL LIKE wildcard characters must be treated as literal search text.
        literal = self.call('GET', '/assets/search', params={'name': '%'})
        self.assertTrue(all('%' in a['asset_name'] for a in literal['assets']))
        for query in ('', '?name=', '?type=bad', '?criticality=bad', '?ip=invalid', '?unknown=x', '?name=a&name=b'):
            self.call('GET', '/assets/search'+query, expected=400)
        self.call('GET', '/assets?unknown=x', expected=400)

    def test_06_missing_records_and_internal_access(self):
        self.call('GET', '/assets/999999999999999999999999999999', expected=404)
        for method in ('GET','PUT','DELETE'):
            kwargs = {'json':{'status':'Active'}} if method == 'PUT' else {}
            self.call(method, '/assets/999999', expected=404, **kwargs)
        aid = self.create()['id']
        for path in ('/internal/stats', f'/internal/assets/{aid}'):
            self.call('GET', path, expected=401, role=None)
            self.call('GET', path, expected=401)
            self.call('GET', path, expected=401, headers={'X-Service-Key':'invalid'})
            self.call('GET', path, headers={'X-Service-Key':self.key})
        self.call('GET', '/internal/assets/999999', expected=404, headers={'X-Service-Key':self.key})

    def test_07_stats_match_database_and_all_types(self):
        from models.assets import ASSET_TYPES
        for kind in ASSET_TYPES:
            self.create(asset_type=kind, status='Inactive', criticality='Medium')
        stats = self.call('GET', '/internal/stats', headers={'X-Service-Key':self.key})
        self.assertEqual(stats['total_assets'], self.sql('SELECT COUNT(*) FROM assets')[0][0])
        self.assertEqual(stats['critical_assets'], self.sql("SELECT COUNT(*) FROM assets WHERE criticality='Critical'")[0][0])
        self.assertEqual(stats['by_type'], dict(self.sql('SELECT asset_type,COUNT(*) FROM assets GROUP BY asset_type')))

    def test_08_foreign_key_conflict_rollback_and_incident_preservation(self):
        aid = self.create()['id']
        self.sql("INSERT INTO vulnerabilities VALUES (1,'Title','Description','CVE-2026-1234',9.8,'Critical',?,'Lab','Open','2026-01-01',NULL)", (aid,))
        self.call('DELETE', f'/assets/{aid}', expected=409)
        self.assertEqual(self.call('GET', f'/assets/{aid}')['id'], aid)
        self.assertEqual(self.sql("SELECT COUNT(*) FROM logs WHERE action='ASSET_DELETED' AND description=?", (f'Deleted asset {aid}',))[0][0], 0)
        self.sql('DELETE FROM vulnerabilities WHERE id=1')
        self.sql("INSERT INTO incidents VALUES (1,'Title','Description','Malware','High',?,?,NULL,'Open','2026-01-01',NULL)", (self.owner, aid))
        self.call('DELETE', f'/assets/{aid}')
        self.assertEqual(self.sql('SELECT asset_id FROM incidents WHERE id=1'), [(None,)])

    def test_09_user_service_unavailable(self):
        aid = self.create()['id']
        before = self.sql('SELECT COUNT(*) FROM assets')[0][0]
        with patch.dict(os.environ, {'USERS_URL':'http://127.0.0.1:1'}):
            self.call('POST', '/assets', expected=503, json=self.payload())
            self.call('PUT', f'/assets/{aid}', expected=503, json={'owner_id':self.owner, 'asset_name':'Uncommitted'})
        self.assertEqual(self.sql('SELECT COUNT(*) FROM assets')[0][0], before)
        self.assertEqual(self.call('GET', f'/assets/{aid}')['asset_name'], 'Lab Server')
        self.create()

    def test_10_schema_matches_existing_models(self):
        from sqlalchemy import inspect
        with self.apps[0].app_context():
            inspector = inspect(self.orm.engine)
            for name in ('users','assets','incidents','investigation_notes','logs','notifications'):
                model = self.orm.metadata.tables[name]
                actual = {c['name']: c for c in inspector.get_columns(name)}
                self.assertEqual(set(actual), set(model.columns.keys()), name)
                for column in model.columns:
                    self.assertEqual(str(actual[column.name]['type']), str(column.type), (name, column.name))
                    if not column.primary_key:
                        self.assertEqual(actual[column.name]['nullable'], column.nullable, (name, column.name))
                expected_fk = {(f.parent.name, f.column.table.name, f.column.name, f.ondelete)
                               for f in model.foreign_keys}
                # SQLite PRAGMA reports actual actions even when SQLAlchemy's
                # reflection parser misses ON DELETE on inline REFERENCES.
                actual_fk = {(f[3], f[2], f[4], None if f[6] == 'NO ACTION' else f[6])
                             for f in self.sql(f'PRAGMA foreign_key_list({name})')}
                self.assertEqual(actual_fk, expected_fk, name)
        self.assertEqual(self.sql('PRAGMA foreign_key_check'), [])
        self.assertEqual(self.sql('PRAGMA integrity_check'), [('ok',)])

    def test_11_expired_token_and_audit_outage_behavior(self):
        from datetime import datetime, timedelta, timezone
        import jwt
        from common.config import Config
        token = jwt.encode({'user_id':self.owner, 'username':'test_admin', 'role':'admin',
                            'exp':datetime.now(timezone.utc)-timedelta(seconds=10)},
                           Config.JWT_SECRET, algorithm='HS256')
        self.call('GET', '/assets', expected=401, headers={'Authorization':'Bearer '+token})
        # Shared log_event intentionally never raises when Logs is unreachable.
        with patch.dict(os.environ, {'LOGS_URL':'http://127.0.0.1:1'}):
            aid = self.create()['id']
        self.assertEqual(self.call('GET', f'/assets/{aid}')['id'], aid)
        self.assertEqual(self.sql("SELECT COUNT(*) FROM logs WHERE action='ASSET_CREATED' AND description=?",
                                  (f'Created asset {aid}',))[0][0], 0)


if __name__ == '__main__':
    unittest.main()
