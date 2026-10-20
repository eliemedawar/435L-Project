"""All-nine-service integration and report regression. Developed by: Marc Bteich."""
from unittest.mock import patch
from database.testing import LiveBackend


class ReportsTests(LiveBackend):
    SERVICES=('users','logs','notifications','assets','threats','vulnerabilities','incidents','playbooks','reports')

    def test_reports_real_sources_and_roles(self):
        asset=self.asset()
        self.call('threats','POST','/threats',201,json=dict(threat_type='Domain',threat_value='reports.example.test',description='Lab',severity='Critical',source='Lab'))
        self.call('vulnerabilities','POST','/vulnerabilities',201,json=dict(title='Lab',description='Lab',cve_id='CVE-2026-1234',cvss_score=9.8,severity='Critical',asset_id=asset['id'],discovery_source='Lab'))
        for path,table,key in [('assets','assets','total_assets'),('threats','threats','total_threats'),('vulnerabilities','vulnerabilities','total_vulnerabilities')]:
            for role in ('admin','auditor','analyst','user'):
                body=self.call('reports','GET','/reports/'+path,200 if role in ('admin','auditor') else 403,role=role)
                if body:
                    self.assertEqual(body[key],self.sql('SELECT count(*) FROM '+table)[0][0])
                    self.assertIn('generated_at',body)
            self.call('reports','GET','/reports/'+path,401,role=None)
            with patch.dict('os.environ',{path.upper()+'_URL':'http://127.0.0.1:1'}):
                self.call('reports','GET','/reports/'+path,503)

    def test_elie_incident_notification_and_report_regression(self):
        asset=self.asset()
        incident=self.call('incidents','POST','/incidents',201,role='user',json=dict(title='Integration incident',description='Lab event',category='Malware',severity='High',asset_id=asset['id']))
        iid=incident['id']
        self.call('incidents','PUT',f'/incidents/{iid}/assign',json={'analyst_id':self.ids['analyst']})
        for status in ('Under Investigation','Mitigated','Resolved','Closed'):
            self.call('incidents','PUT',f'/incidents/{iid}/status',role='analyst',json={'status':status})
        self.assertTrue(self.sql('SELECT id FROM notifications WHERE user_id=?',(self.ids['analyst'],)))
        for path in ('summary','incidents','activity'):
            body=self.call('reports','GET','/reports/'+path,role='auditor')
            self.assertIn('report_type',body)
        summary=self.call('reports','GET','/reports/summary')
        self.assertEqual(summary['assets'],self.sql('SELECT count(*) FROM assets')[0][0])
        self.assertEqual(summary['users'],5)
        self.assertEqual(self.sql('PRAGMA foreign_key_check'),[])
        self.assertEqual(self.sql('PRAGMA integrity_check'),[('ok',)])
