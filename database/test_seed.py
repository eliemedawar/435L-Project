"""Seed idempotence, schema alignment, and enum coverage. Developed by: Marc Bteich."""
from contextlib import closing
import os
from pathlib import Path
import secrets
import sqlite3
import subprocess
import sys
import tempfile
import unittest

ROOT=Path(__file__).resolve().parents[1]


class SeedTests(unittest.TestCase):
    def test_additive_seed_full_coverage_and_schema_alignment(self):
        (ROOT/'.local').mkdir(exist_ok=True)
        with tempfile.TemporaryDirectory(dir=ROOT/'.local') as folder:
            folder=Path(folder)
            dbfile=folder/'seed.db'
            with closing(sqlite3.connect(dbfile)) as c:
                c.executescript((ROOT/'database/schema.sql').read_text())
            env=dict(os.environ,DATABASE_URL='sqlite:///'+dbfile.as_posix(),JWT_SECRET=secrets.token_hex(32),SERVICE_KEY=secrets.token_hex(32))
            credentials=folder/'credentials.json'
            # The subprocess checks all ten ORM tables against the SQL schema.
            code="""
from pathlib import Path
from common.app_factory import create_service_app
from common.db import db
from database.seed import seed
from sqlalchemy import inspect
app=create_service_app('users')
with app.app_context():
    first=seed(Path(__import__('sys').argv[1]))
    assert first==seed(Path(__import__('sys').argv[1])), 'Seed is not idempotent'
    inspector=inspect(db.engine)
    for table in db.metadata.sorted_tables:
        actual={c['name']:c for c in inspector.get_columns(table.name)}
        assert set(actual)==set(table.columns.keys()), table.name
        for column in table.columns:
            assert str(actual[column.name]['type'])==str(column.type), (table.name,column.name)
    print('Seed idempotence and all ten ORM column definitions verified')
"""
            result=subprocess.run([sys.executable,'-c',code,str(credentials)],cwd=ROOT,env=env,capture_output=True,text=True,timeout=60)
            self.assertEqual(result.returncode,0,result.stderr)
            self.assertTrue(credentials.exists())
            with closing(sqlite3.connect(dbfile)) as c:
                self.assertEqual(c.execute('PRAGMA foreign_key_check').fetchall(),[])
                for table,column,count in [('users','role',4),('users','account_status',3),('assets','asset_type',6),
                    ('assets','status',3),('threats','threat_type',5),('threats','severity',4),('incidents','status',5),
                    ('vulnerabilities','status',5),('vulnerabilities','severity',4),('notifications','notification_type',5),
                    ('notifications','status',2),('logs','severity',4),('response_actions','status',3)]:
                    self.assertEqual(c.execute(f'SELECT count(DISTINCT {column}) FROM {table}').fetchone()[0],count,(table,column))
