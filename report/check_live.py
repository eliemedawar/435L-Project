"""Read-only verification of the seeded nine-service backend. Developed by: Marc Bteich."""
from contextlib import closing
from datetime import datetime, timezone
import json
from pathlib import Path
import sqlite3
import time
import requests
from dotenv import dotenv_values

ROOT=Path(__file__).resolve().parents[1]


def main():
    secrets=dotenv_values(ROOT/'.env')
    accounts=json.loads((ROOT/'.local/seed-credentials.json').read_text())
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
                raise RuntimeError(f'Service {port} did not start')
            time.sleep(.2)
    response=requests.post('http://127.0.0.1:5001/users/login',json=dict(
        username='admin',password=accounts['admin']['password']),timeout=10)
    assert response.status_code==200,response.status_code
    token=response.json()['data']['token']
    uid=response.json()['data']['user']['id']
    headers={'Authorization':'Bearer '+token}
    services=[]
    paths=['/users','/assets','/incidents','/threats','/logs','/reports/summary',
           '/vulnerabilities',f'/notifications/user/{uid}','/playbooks']
    for port,path in zip(range(5001,5010),paths):
        response=requests.get(f'http://127.0.0.1:{port}'+path,headers=headers,timeout=10)
        assert response.status_code==200,(port,response.status_code)
        services.append(dict(port=port,path=path,status=response.status_code))
    reports={}
    for name in ('summary','incidents','activity','assets','threats','vulnerabilities'):
        response=requests.get('http://127.0.0.1:5006/reports/'+name,headers=headers,timeout=10)
        assert response.status_code==200,(name,response.status_code)
        reports[name]=response.json()['data']
    with closing(sqlite3.connect(ROOT/'database/sidrms.db')) as c:
        assert c.execute('PRAGMA integrity_check').fetchone()[0]=='ok'
        assert c.execute('PRAGMA foreign_key_check').fetchall()==[]
        counts={table:c.execute('SELECT count(*) FROM '+table).fetchone()[0]
                for table in ('users','assets','incidents','threats','logs','vulnerabilities','notifications','playbooks','response_actions')}
    assert reports['assets']['total_assets']==counts['assets']
    assert reports['threats']['total_threats']==counts['threats']
    assert reports['vulnerabilities']['total_vulnerabilities']==counts['vulnerabilities']
    result=dict(checked_at=datetime.now(timezone.utc).isoformat(),services=services,reports=reports,
                database_counts=counts,integrity='ok',foreign_key_violations=0)
    (ROOT/'report/evidence/live-backend.json').write_text(json.dumps(result,indent=2)+'\n')
    print('Nine services authenticated successfully; six reports returned 200; source totals match actual SQL; integrity and FKs OK')


if __name__=='__main__':
    main()
