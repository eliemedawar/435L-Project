"""Isolated real-HTTP test harness for Marc's services. Developed by: Marc Bteich."""
from contextlib import closing
import importlib
import os
from pathlib import Path
import secrets
import sqlite3
import tempfile
import threading
import unittest
from unittest.mock import patch
import requests
from werkzeug.serving import make_server, WSGIRequestHandler

ROOT = Path(__file__).resolve().parents[1]


class QuietHandler(WSGIRequestHandler):
    def log_request(self, *args, **kwargs):
        pass


class LiveBackend(unittest.TestCase):
    SERVICES = ('users', 'logs', 'notifications', 'assets', 'threats')

    @classmethod
    def setUpClass(cls):
        (ROOT/'.local').mkdir(exist_ok=True)
        cls.temp = tempfile.TemporaryDirectory(dir=ROOT/'.local')
        cls.dbfile = Path(cls.temp.name)/'test.db'
        cls.key, cls.password = secrets.token_hex(32), secrets.token_hex(16)+'Aa!1'
        cls.env = patch.dict(os.environ, DATABASE_URL='sqlite:///'+cls.dbfile.as_posix(),
                             JWT_SECRET=secrets.token_hex(32), SERVICE_KEY=cls.key)
        cls.env.start()
        cls.addClassCleanup(cls.env.stop)
        from common.config import Config
        cls.config = patch.multiple(Config, DATABASE_URL=os.environ['DATABASE_URL'],
                                    JWT_SECRET=os.environ['JWT_SECRET'], SERVICE_KEY=cls.key)
        cls.config.start()
        cls.addClassCleanup(cls.config.stop)
        with closing(sqlite3.connect(cls.dbfile)) as c:
            c.executescript((ROOT/'database/schema.sql').read_text())
        from common.app_factory import create_service_app
        from common.db import db
        from models.users import User
        cls.orm = db
        cls.servers, cls.apps, cls.urls = [], [], {}
        for name in cls.SERVICES:
            if name == 'reports':
                from services.reports.routes_a import reports_a_bp
                from services.reports.routes_b import reports_b_bp
                blueprints = (reports_a_bp, reports_b_bp)
            else:
                module = importlib.import_module(f'services.{name}.routes')
                blueprints = (getattr(module, name+'_bp'),)
            app = create_service_app(name, *blueprints)
            server = make_server('127.0.0.1', 0, app, threaded=True, request_handler=QuietHandler)
            thread = threading.Thread(target=server.serve_forever, daemon=True)
            thread.start()
            cls.apps.append(app)
            cls.servers.append((server, thread))
            cls.urls[name] = f'http://127.0.0.1:{server.server_port}'
            os.environ[name.upper()+'_URL'] = cls.urls[name]
        cls.ids = {}
        with cls.apps[0].app_context():
            for name, role in [('admin','admin'),('admin2','admin'),('analyst','analyst'),('auditor','auditor'),('user','user')]:
                user = User(full_name='Test '+name, username='live_'+name, email=name+'@example.test', department='Security', role=role)
                user.set_password(cls.password)
                db.session.add(user)
                db.session.flush()
                cls.ids[name] = user.id
            db.session.commit()
        cls.tokens = {}
        for name in cls.ids:
            r = requests.post(cls.urls['users']+'/users/login', json={'username':'live_'+name,'password':cls.password}, timeout=10)
            assert r.status_code == 200, r.text
            cls.tokens[name] = r.json()['data']['token']

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

    def call(self, service, method, path, status=200, role='admin', **kwargs):
        headers = kwargs.pop('headers', {'Authorization':'Bearer '+self.tokens[role]} if role else {})
        r = requests.request(method, self.urls[service]+path, headers=headers, timeout=15, **kwargs)
        self.assertEqual(r.status_code, status, r.text)
        body = r.json()
        self.assertEqual(body['status'], 'success' if status < 400 else 'error')
        self.assertIsInstance(body['message'], str)
        return body.get('data')

    def sql(self, sql, args=()):
        with closing(sqlite3.connect(self.dbfile)) as c, c:
            c.execute('PRAGMA foreign_keys=ON')
            return c.execute(sql, args).fetchall()

    def asset(self):
        return self.call('assets','POST','/assets',201,json=dict(asset_name='HTTP Lab',asset_type='Server',
            ip_address='192.0.2.25',owner_id=self.ids['admin'],department='Security',criticality='High'))
