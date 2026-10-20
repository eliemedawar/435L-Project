"""Run original and merged Postman requests on isolated live services.
Developed by: Marc Bteich. Requires local Newman tools (see report/TOOLS.md).
"""
from contextlib import closing
import json
import os
from pathlib import Path
import secrets
import sqlite3
import subprocess
import sys
import tempfile
import time
import requests

ROOT=Path(__file__).resolve().parents[1]


class RuntimeDirectory(tempfile.TemporaryDirectory):
    def cleanup(self):
        # Windows can retain recently terminated process handles briefly.
        for attempt in range(20):
            try:
                return super().cleanup()
            except PermissionError:
                if attempt==19:
                    raise
                time.sleep(.2)


def run(mode='combined'):
    (ROOT/'.local').mkdir(exist_ok=True)
    node=next((ROOT/'.local').glob('node-*-win-x64/node.exe'))
    with RuntimeDirectory(dir=ROOT/'.local') as temporary:
        folder=Path(temporary)
        dbfile=folder/'runtime.db'
        key=secrets.token_hex(32)
        env=dict(os.environ,DATABASE_URL='sqlite:///'+dbfile.as_posix(),JWT_SECRET=secrets.token_hex(32),SERVICE_KEY=key,FLASK_DEBUG='0')
        with closing(sqlite3.connect(dbfile)) as c:
            c.executescript((ROOT/'database/schema.sql').read_text())
        # Seed only admin for the merged run; original Users requests create
        # the remaining accounts. A seeded DB is used for standalone B runs.
        account_passwords={role:secrets.token_urlsafe(24)+'Aa!1' for role in ('admin','analyst','auditor','user')}
        if mode=='combined':
            code="""
import os
from common.app_factory import create_service_app
from common.db import db
from models.users import User
app=create_service_app('users')
with app.app_context():
    user=User(username='admin',full_name='Local test admin',email='admin@example.test',department='Lab',role='admin')
    user.set_password(os.environ['LOCAL_TEST_PASSWORD'])
    db.session.add(user);db.session.commit()
"""
            setup=subprocess.run([sys.executable,'-c',code],cwd=ROOT,env=dict(env,LOCAL_TEST_PASSWORD=account_passwords['admin']),capture_output=True,text=True,timeout=30)
            if setup.returncode:
                raise RuntimeError(setup.stderr)
        else:
            credentials=folder/'credentials.json'
            code="from common.app_factory import create_service_app; from database.seed import seed; from pathlib import Path; app=create_service_app('users');\nwith app.app_context(): seed(Path(__import__('sys').argv[1]))"
            setup=subprocess.run([sys.executable,'-c',code,str(credentials)],cwd=ROOT,env=env,capture_output=True,text=True,timeout=60)
            if setup.returncode:
                raise RuntimeError(setup.stderr)
            accounts=json.loads(credentials.read_text())
            for role,name in [('admin','admin'),('analyst','lara'),('auditor','nadia'),('user','rami')]:
                account_passwords[role]=accounts[name]['password']
        runtime=dict(service_key=key,admin_username='admin',analyst_username='lara',auditor_username='nadia',user_username='rami')
        runtime.update({role+'_password':password for role,password in account_passwords.items()})
        private=folder/'environment.json'
        private.write_text(json.dumps(runtime))
        processes=[]
        failures=[]
        with (folder/'services.log').open('w') as log:
            try:
                for name in ('users','assets','incidents','threats','logs','reports','vulnerabilities','notifications','playbooks'):
                    process=subprocess.Popen([sys.executable,'-m',f'services.{name}.app'],cwd=ROOT,env=env,
                        stdout=log,stderr=log,creationflags=getattr(subprocess,'CREATE_NO_WINDOW',0))
                    processes.append(process)
                for port in range(5001,5010):
                    deadline=time.monotonic()+30
                    while True:
                        try:
                            response=requests.get(f'http://127.0.0.1:{port}/',timeout=1)
                            if response.status_code==404:
                                break
                        except requests.ConnectionError:
                            pass
                        if time.monotonic()>deadline:
                            raise RuntimeError(f'Service on {port} failed to start')
                        time.sleep(.2)
                names=['SIDRMS'] if mode=='combined' else ['assets','threats','vulnerabilities','playbooks','reports_b']
                for name in names:
                    output='newman-'+('combined' if name=='SIDRMS' else name)
                    result=subprocess.run([str(node),str(ROOT/'postman/run_collection.cjs'),
                        str(ROOT/f'postman/{name}.postman_collection.json'),str(private),output],cwd=ROOT,
                        capture_output=True,text=True,timeout=180)
                    print(result.stdout)
                    if result.returncode:
                        failures.append(name)
                        print(result.stderr)
                with closing(sqlite3.connect(dbfile)) as c:
                    assert c.execute('PRAGMA foreign_key_check').fetchall()==[]
                    assert c.execute('PRAGMA integrity_check').fetchone()[0]=='ok'
            finally:
                for process in processes:
                    process.terminate()
                for process in processes:
                    process.wait(timeout=15)
        if failures:
            raise SystemExit('Postman assertions failed: '+', '.join(failures))


if __name__=='__main__':
    run(sys.argv[1] if len(sys.argv)>1 else 'combined')
