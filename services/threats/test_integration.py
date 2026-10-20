"""Real threat API integration tests. Developed by: Marc Bteich."""
from unittest.mock import patch
from database.testing import LiveBackend


class ThreatTests(LiveBackend):
    def body(self, **changes):
        import secrets
        data = dict(threat_type='Domain', threat_value=secrets.token_hex(8)+'.example.test',
                    description='Lab indicator', severity='High', source='Lab')
        data.update(changes)
        return data

    def create(self, **changes):
        return self.call('threats','POST','/threats',201,json=self.body(**changes))

    def test_crud_notifications_and_audit(self):
        item = self.create(severity='Critical')
        tid = item['id']
        self.assertEqual(self.sql("SELECT count(*) FROM notifications WHERE notification_type='Threat Alert' AND title=?", (f'Critical threat #{tid}',)), [(2,)])
        self.call('threats','PUT',f'/threats/{tid}',json={'description':'Updated','severity':'Low','source':'Updated feed'})
        self.assertEqual(self.call('threats','GET',f'/threats/{tid}')['description'], 'Updated')
        self.call('threats','DELETE',f'/threats/{tid}')
        self.call('threats','GET',f'/threats/{tid}',404)
        for action in ('CREATED','UPDATED','DELETED'):
            self.assertTrue(self.sql('SELECT id FROM logs WHERE action=? AND description LIKE ?', ('THREAT_'+action,f'%threat {tid}%')))

    def test_formats_duplicates_search_and_stats(self):
        cases = [('IP Address','2001:0db8::1'),('IP Address','192.0.2.11'),('Domain','Case.Example.Test.'),
                 ('File Hash','A'*32),('File Hash','B'*40),('File Hash','C'*64),('Malware Signature','lab-signature'),('Other','lab-other')]
        for kind,value in cases:
            item = self.create(threat_type=kind,threat_value=value)
            self.call('threats','POST','/threats',409,json=self.body(threat_type=kind,threat_value=item['threat_value']))
        for params in ({'type':'Domain'}, {'value':'example'}, {'severity':'High'}, {'source':'Lab'}, {'type':'Domain','source':'Lab'}):
            result = self.call('threats','GET','/threats/search',params=params)
            self.assertGreater(result['count'],0)
        self.assertEqual(self.call('threats','GET','/threats/search',params={'value':"' OR 1=1 --"})['count'],0)
        stats = self.call('threats','GET','/internal/stats',headers={'X-Service-Key':self.key})
        self.assertEqual(stats['total_threats'],self.sql('SELECT count(*) FROM threats')[0][0])
        for column,key in [('severity','by_severity'),('threat_type','by_type')]:
            counts = dict(self.sql(f'SELECT {column},count(*) FROM threats GROUP BY {column}'))
            self.assertEqual(sum(stats[key].values()),stats['total_threats'])
            self.assertTrue(all(stats[key][k]==v for k,v in counts.items()))
        self.assertLessEqual(len(stats['recently_added']),5)

    def test_role_matrix(self):
        tid=self.create()['id']
        for role in ('admin','analyst','auditor','user'):
            for method,path,body,allowed in [
                ('GET','/threats',None,('admin','analyst','auditor')),
                ('GET',f'/threats/{tid}',None,('admin','analyst','auditor')),
                ('GET','/threats/search?source=Lab',None,('admin','analyst')),
                ('POST','/threats',self.body(),('admin',)),
                ('PUT',f'/threats/{tid}',{'severity':'Medium'},('admin',))]:
                self.call('threats',method,path,201 if method=='POST' and role in allowed else 200 if role in allowed else 403,role=role,**({'json':body} if body else {}))
            target=self.create()['id']
            self.call('threats','DELETE',f'/threats/{target}',200 if role=='admin' else 403,role=role)

    def test_invalid_inputs_missing_ids_and_auth(self):
        for values in ({'threat_type':'bad'}, {'threat_value':12}, {'threat_type':'IP Address','threat_value':'999.1.1.1'},
                       {'threat_value':'https://example.test'}, {'threat_value':'bad..domain'},
                       {'threat_type':'File Hash','threat_value':'z'*32}, {'severity':[]}, {'source':''}, {'unknown':1}):
            self.call('threats','POST','/threats',400,json=self.body(**values))
        for body in ({},[],None):
            self.call('threats','POST','/threats',400,json=body)
        for method in ('GET','PUT','DELETE'):
            self.call('threats',method,'/threats/999999',404,**({'json':{'source':'Lab'}} if method=='PUT' else {}))
        for method,path in [('POST','/threats'),('GET','/threats'),('GET','/threats/1'),('GET','/threats/search'),('PUT','/threats/1'),('DELETE','/threats/1')]:
            self.call('threats',method,path,401,role=None)
        for query in ('','?type=bad','?severity=bad','?value=','?foo=bar','?value=a&value=b'):
            self.call('threats','GET','/threats/search'+query,400)
        self.call('threats','GET','/internal/stats',401)
        self.call('threats','GET','/internal/stats',401,headers={'X-Service-Key':'bad'})
        with patch.dict('os.environ',{'USERS_URL':'http://127.0.0.1:1'}):
            self.call('threats','POST','/threats',503,json=self.body(severity='Critical'))
