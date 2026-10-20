"""Real vulnerability HTTP tests. Developed by: Marc Bteich."""
from unittest.mock import patch
from database.testing import LiveBackend


class VulnerabilityTests(LiveBackend):
    SERVICES = LiveBackend.SERVICES+('vulnerabilities',)

    def body(self, **changes):
        values=dict(title='Lab vulnerability',description='Lab test',cve_id='CVE-2026-12345',cvss_score=9.8,
                    severity='High',asset_id=self.asset()['id'],discovery_source='Lab scanner')
        values.update(changes)
        return values

    def create(self, **changes):
        return self.call('vulnerabilities','POST','/vulnerabilities',201,json=self.body(**changes))

    def test_lifecycle_resolution_atomicity_and_delete(self):
        item=self.create(severity='Critical')
        vid=item['id']
        self.assertEqual(self.sql("SELECT count(*) FROM notifications WHERE notification_type='Vulnerability Alert' AND title=?",(f'Critical vulnerability #{vid}',)),[(2,)])
        self.assertEqual(item['status'],'Open')
        for status in ('Closed','In Progress','Resolved','Open'):
            self.call('vulnerabilities','PUT',f'/vulnerabilities/{vid}',400,json={'status':status,'description':'Must not save'})
        self.assertEqual(self.call('vulnerabilities','GET',f'/vulnerabilities/{vid}')['description'],'Lab test')
        for status in ('Under Investigation','In Progress','Resolved','Closed'):
            current=self.call('vulnerabilities','PUT',f'/vulnerabilities/{vid}',role='analyst',json={'status':status,'cvss_score':8.1})
            self.assertEqual(current['status'],status)
            self.assertEqual(current['resolution_date'] is not None,status in ('Resolved','Closed'))
        self.call('vulnerabilities','PUT',f'/vulnerabilities/{vid}',400,json={'status':'Open'})
        self.call('assets','DELETE',f"/assets/{item['asset_id']}",409)
        self.call('vulnerabilities','DELETE',f'/vulnerabilities/{vid}')
        self.call('assets','DELETE',f"/assets/{item['asset_id']}")
        for action in ('CREATED','UPDATED','DELETED'):
            self.assertTrue(self.sql('SELECT id FROM logs WHERE action=? AND description LIKE ?',('VULNERABILITY_'+action,f'%vulnerability {vid}%')))

    def test_role_matrix_and_search_stats(self):
        item=self.create()
        vid=item['id']
        for role in ('admin','analyst','auditor','user'):
            for path in ('/vulnerabilities',f'/vulnerabilities/{vid}','/vulnerabilities/search?severity=High'):
                self.call('vulnerabilities','GET',path,403 if role=='user' else 200,role=role)
            self.call('vulnerabilities','PUT',f'/vulnerabilities/{vid}',200 if role in ('admin','analyst') else 403,role=role,json={'description':'Updated'})
            self.call('vulnerabilities','POST','/vulnerabilities',201 if role=='admin' else 403,role=role,json=self.body())
            target=self.create()['id']
            self.call('vulnerabilities','DELETE',f'/vulnerabilities/{target}',200 if role=='admin' else 403,role=role)
        for params in ({'cve':item['cve_id']},{'severity':'High'},{'asset':item['asset_id']},{'status':'Open'},
                       {'asset':item['asset_id'],'status':'Open'}):
            self.assertGreater(self.call('vulnerabilities','GET','/vulnerabilities/search',params=params)['count'],0)
        stats=self.call('vulnerabilities','GET','/internal/stats',headers={'X-Service-Key':self.key})
        self.assertEqual(stats['total_vulnerabilities'],self.sql('SELECT count(*) FROM vulnerabilities')[0][0])
        for key in ('by_status','by_severity'):
            self.assertEqual(sum(stats[key].values()),stats['total_vulnerabilities'])

    def test_validation_auth_and_missing_dependencies(self):
        base=self.body()
        for values in ({'cve_id':'bad'},{'cve_id':'CVE-2026-123'},{'cvss_score':-1},{'cvss_score':10.1},
                       {'cvss_score':True},{'cvss_score':'9.8'},{'cvss_score':9.85},{'asset_id':True},
                       {'asset_id':999999},{'severity':None},{'title':''},{'status':'Closed'}):
            self.call('vulnerabilities','POST','/vulnerabilities',400,json={**base,**values})
        for body in ({},[],None):
            self.call('vulnerabilities','POST','/vulnerabilities',400,json=body)
        for query in ('','?asset=bad','?asset=-1','?status=bad','?severity=bad','?cve=bad','?foo=1','?status=Open&status=Closed'):
            self.call('vulnerabilities','GET','/vulnerabilities/search'+query,400)
        for method,path in [('GET','/vulnerabilities'),('POST','/vulnerabilities'),('GET','/vulnerabilities/1'),
                            ('PUT','/vulnerabilities/1'),('DELETE','/vulnerabilities/1'),('GET','/vulnerabilities/search')]:
            self.call('vulnerabilities',method,path,401,role=None)
        for method in ('GET','PUT','DELETE'):
            self.call('vulnerabilities',method,'/vulnerabilities/999999',404,**({'json':{'description':'Lab'}} if method=='PUT' else {}))
        self.call('vulnerabilities','GET','/internal/stats',401)
        with patch.dict('os.environ',{'ASSETS_URL':'http://127.0.0.1:1'}):
            self.call('vulnerabilities','POST','/vulnerabilities',503,json=base)
        with patch.dict('os.environ',{'USERS_URL':'http://127.0.0.1:1'}):
            self.call('vulnerabilities','POST','/vulnerabilities',503,json={**base,'severity':'Critical'})
