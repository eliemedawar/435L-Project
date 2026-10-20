"""Build Marc's collections and merge originals without editing Elie's files.
Developed by: Marc Bteich. Run python postman/build_collections.py.
"""
import copy
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
POSTMAN=ROOT/'postman'
SCHEMA='https://schema.getpostman.com/json/collection/v2.1.0/collection.json'
VARIABLES={f'base_{name}':f'http://127.0.0.1:{port}' for name,port in (
    ('users',5001),('assets',5002),('incidents',5003),('threats',5004),('logs',5005),
    ('reports',5006),('vulnerabilities',5007),('notifications',5008),('playbooks',5009))}
for role,username in [('admin','admin'),('analyst','lara'),('auditor','nadia'),('user','rami')]:
    VARIABLES.update({role+'_username':username,role+'_password':'','token_'+role:''})
VARIABLES.update(service_key='',owner_id='',analyst_id='',user_id='',auditor_id='',
                 threat_id='',vulnerability_id='',playbook_id='',action_id='',
                 vulnerability_asset_id='',indicator_domain='postman.example.test')


def req(name,service,method,path,status=200,body=None,role='admin',extra=(),service_key=False):
    headers=[]
    if role:
        headers.append(dict(key='Authorization',value='Bearer {{token_'+role+'}}'))
    if service_key:
        headers.append(dict(key='X-Service-Key',value='{{service_key}}'))
    request=dict(method=method,header=headers,url='{{base_'+service+'}}'+path,
        description=f'Developed by: Marc Bteich. {name}. Expected HTTP {status}. Input/body and authentication are defined in this request; successful responses use status/message/data and errors use status/message.')
    if body is not None:
        raw=body if isinstance(body,str) else json.dumps(body,indent=2)
        for field in ('owner_id','asset_id','assigned_user_id','step_number'):
            import re
            raw=re.sub(r'("'+field+r'"\s*:\s*)"(\{\{[^}]+\}\})"',r'\1\2',raw)
        request['body']=dict(mode='raw',raw=raw,options={'raw':{'language':'json'}})
        headers.append(dict(key='Content-Type',value='application/json'))
    script=[f'pm.test("HTTP {status}", () => pm.response.to.have.status({status}));',
            'const body=pm.response.json();',
            'pm.test("Response envelope", () => {pm.expect(body.status).to.eql("'+('success' if status<400 else 'error')+'");pm.expect(body.message).to.be.a("string");});',*extra]
    return dict(name=name,request=request,event=[dict(listen='test',script=dict(type='text/javascript',exec=script))])


def savevar(key,expression='body.data.id'):
    return f'if (pm.response.code < 300) pm.collectionVariables.set("{key}",{expression});'


def login():
    items=[]
    for role in ('admin','analyst','auditor','user'):
        extra=[savevar('token_'+role,'body.data.token'),savevar('owner_id' if role=='admin' else role+'_id','body.data.user.id')]
        items.append(req('Login '+role,'users','POST','/users/login',body=dict(username='{{'+role+'_username}}',password='{{'+role+'_password}}'),role=None,extra=extra))
    return dict(name='0. Login existing accounts',item=items)


def write(name,folders):
    collection=dict(info=dict(name=name+' (Marc Bteich)',schema=SCHEMA,
        description='Developed by: Marc Bteich. Start all services and provision accounts with database.seed or the combined Users folder. Private passwords/service_key must be set locally. Run folders in order; destructive test data is labelled.'),
        variable=[dict(key=k,value=v) for k,v in VARIABLES.items()],item=[login(),*folders])
    target=POSTMAN/(name+'.postman_collection.json')
    target.write_text(json.dumps(collection,indent=2)+'\n')
    return collection


def main():
    threat=dict(threat_type='Domain',threat_value='{{indicator_domain}}',description='Synthetic Postman lab indicator',severity='Critical',source='Postman lab')
    items=[req('Create Critical threat','threats','POST','/threats',201,threat,extra=[savevar('threat_id')]),
           req('Duplicate normalized threat','threats','POST','/threats',409,threat),
           req('List threats','threats','GET','/threats',role='auditor'),
           req('Get threat','threats','GET','/threats/{{threat_id}}',role='analyst')]
    for query in ('type=Domain','value=postman','severity=Critical','source=Postman','type=Domain&severity=Critical'):
        items.append(req('Search '+query,'threats','GET','/threats/search?'+query,role='analyst'))
    items += [req('Update threat','threats','PUT','/threats/{{threat_id}}',body=dict(description='Reviewed',severity='High',source='Reviewed lab')),
              req('Internal stats','threats','GET','/internal/stats',role=None,service_key=True),
              req('Critical threat notification','notifications','GET','/notifications/search?type=Threat%20Alert'),
              req('Threat audit records','logs','GET','/logs/search?service=threats')]
    negative=[req('No token','threats','GET','/threats',401,role=None),
              req('User denied','threats','GET','/threats',403,role='user'),
              req('Auditor search denied','threats','GET','/threats/search?source=Lab',403,role='auditor'),
              req('Analyst update denied','threats','PUT','/threats/{{threat_id}}',403,dict(severity='Low'),role='analyst'),
              req('Missing threat','threats','GET','/threats/2147483647',404),
              req('Empty body','threats','POST','/threats',400,{}),
              req('Invalid enum','threats','POST','/threats',400,{**threat,'severity':'Urgent'}),
              req('Invalid IP','threats','POST','/threats',400,{**threat,'threat_type':'IP Address','threat_value':'999.2.3.4'}),
              req('Invalid domain','threats','POST','/threats',400,{**threat,'threat_value':'https://invalid.test'}),
              req('Invalid hash','threats','POST','/threats',400,{**threat,'threat_type':'File Hash','threat_value':'xyz'}),
              req('Invalid search','threats','GET','/threats/search?severity=bad',400),
              req('JWT denied internal stats','threats','GET','/internal/stats',401)]
    write('threats',[dict(name='1. Positive operations',item=items),dict(name='2. Negative tests',item=negative),
                     dict(name='3. Cleanup',item=[req('Delete threat','threats','DELETE','/threats/{{threat_id}}'),req('Deleted threat','threats','GET','/threats/{{threat_id}}',404)])])

    asset=dict(asset_name='Postman vulnerability fixture',asset_type='Server',ip_address='192.0.2.220',owner_id='{{owner_id}}',department='Lab',criticality='High')
    vuln=dict(title='Synthetic Postman vulnerability',description='Lab scenario only',cve_id='CVE-2026-12345',cvss_score=9.8,severity='Critical',asset_id='{{vulnerability_asset_id}}',discovery_source='Postman lab')
    items=[req('Create affected asset','assets','POST','/assets',201,asset,extra=[savevar('vulnerability_asset_id')]),
           req('Create Critical vulnerability','vulnerabilities','POST','/vulnerabilities',201,vuln,extra=[savevar('vulnerability_id')]),
           req('List vulnerabilities','vulnerabilities','GET','/vulnerabilities',role='auditor'),
           req('Get vulnerability','vulnerabilities','GET','/vulnerabilities/{{vulnerability_id}}',role='analyst')]
    for query in ('cve=CVE-2026-12345','severity=Critical','asset={{vulnerability_asset_id}}','status=Open'):
        items.append(req('Search '+query,'vulnerabilities','GET','/vulnerabilities/search?'+query,role='analyst'))
    items += [req('Cannot skip lifecycle','vulnerabilities','PUT','/vulnerabilities/{{vulnerability_id}}',400,dict(status='Closed'))]
    for status in ('Under Investigation','In Progress','Resolved','Closed'):
        extra=['pm.test("Automatic resolution date", () => pm.expect(body.data.resolution_date).to.be.a("string"));'] if status in ('Resolved','Closed') else []
        items.append(req('Transition '+status,'vulnerabilities','PUT','/vulnerabilities/{{vulnerability_id}}',body=dict(status=status),role='analyst',extra=extra))
    items += [req('Internal stats','vulnerabilities','GET','/internal/stats',role=None,service_key=True),
              req('Critical vulnerability notification','notifications','GET','/notifications/search?type=Vulnerability%20Alert'),
              req('Linked asset cannot be deleted','assets','DELETE','/assets/{{vulnerability_asset_id}}',409)]
    negative=[req('No token','vulnerabilities','GET','/vulnerabilities',401,role=None),
              req('User denied','vulnerabilities','GET','/vulnerabilities',403,role='user'),
              req('Analyst create denied','vulnerabilities','POST','/vulnerabilities',403,vuln,role='analyst'),
              req('Auditor update denied','vulnerabilities','PUT','/vulnerabilities/{{vulnerability_id}}',403,dict(description='x'),role='auditor'),
              req('Missing vulnerability','vulnerabilities','GET','/vulnerabilities/2147483647',404),
              req('Empty body','vulnerabilities','POST','/vulnerabilities',400,{})]
    for name,change in [('Invalid CVE',dict(cve_id='CVE-26-1')),('Invalid CVSS',dict(cvss_score=10.1)),
                        ('Wrong type',dict(cvss_score=True)),('Missing asset',dict(asset_id=2147483647)),('Invalid severity',dict(severity='bad'))]:
        negative.append(req(name,'vulnerabilities','POST','/vulnerabilities',400,{**vuln,**change}))
    negative += [req('Closed cannot reopen','vulnerabilities','PUT','/vulnerabilities/{{vulnerability_id}}',400,dict(status='Open'))]
    write('vulnerabilities',[dict(name='1. Relationships and lifecycle',item=items),dict(name='2. Negative tests',item=negative),
        dict(name='3. Cleanup',item=[req('Delete vulnerability','vulnerabilities','DELETE','/vulnerabilities/{{vulnerability_id}}'),
            req('Delete affected asset','assets','DELETE','/assets/{{vulnerability_asset_id}}')])])

    book=dict(name='Postman laboratory response',description='Lab procedure',incident_category='Malware',severity='High')
    items=[req('Create playbook','playbooks','POST','/playbooks',201,book,extra=[savevar('playbook_id')]),
           req('List playbooks','playbooks','GET','/playbooks',role='auditor'),
           req('Add second step first','playbooks','POST','/playbooks/{{playbook_id}}/actions',201,dict(description='Contain host',step_number=2),role='analyst'),
           req('Add first step','playbooks','POST','/playbooks/{{playbook_id}}/actions',201,dict(description='Collect evidence',step_number=1),role='analyst',extra=[savevar('action_id')]),
           req('Verify ordered actions','playbooks','GET','/playbooks/{{playbook_id}}',role='auditor',extra=[
               'pm.test("Ordered steps", () => pm.expect(body.data.actions.map(a=>a.step_number)).to.eql([1,2]));']),
           req('Duplicate step rejected','playbooks','POST','/playbooks/{{playbook_id}}/actions',409,dict(description='Duplicate',step_number=1)),
           req('Cannot skip Pending','playbooks','PUT','/actions/{{action_id}}/status',400,dict(status='Completed')),
           req('Start assigned action','playbooks','PUT','/actions/{{action_id}}/status',body=dict(status='In Progress',assigned_user_id='{{analyst_id}}'),role='analyst'),
           req('Complete action','playbooks','PUT','/actions/{{action_id}}/status',body=dict(status='Completed'),role='analyst',extra=[
               'pm.test("Completion recorded",()=>pm.expect(body.data.completion_date).to.be.a("string"));',
               'pm.test("History preserved",()=>pm.expect(body.data.execution_history.map(e=>e.to_status)).to.eql(["Pending","In Progress","Completed"]));'])]
    negative=[req('No token','playbooks','GET','/playbooks',401,role=None),req('User denied','playbooks','GET','/playbooks',403,role='user'),
              req('Analyst create denied','playbooks','POST','/playbooks',403,book,role='analyst'),
              req('Auditor action denied','playbooks','POST','/playbooks/{{playbook_id}}/actions',403,dict(description='x',step_number=3),role='auditor'),
              req('Missing playbook','playbooks','GET','/playbooks/2147483647',404),
              req('Missing action','playbooks','PUT','/actions/2147483647/status',404,dict(status='In Progress')),
              req('Invalid step','playbooks','POST','/playbooks/{{playbook_id}}/actions',400,dict(description='x',step_number=0)),
              req('Missing assigned user','playbooks','POST','/playbooks/{{playbook_id}}/actions',400,dict(description='x',step_number=3,assigned_user_id=2147483647)),
              req('Completed cannot change','playbooks','PUT','/actions/{{action_id}}/status',400,dict(status='Pending')),
              req('Invalid category','playbooks','POST','/playbooks',400,{**book,'incident_category':'bad'}),
              req('Empty body','playbooks','POST','/playbooks',400,{})]
    write('playbooks',[dict(name='1. Ordered workflow',item=items),dict(name='2. Negative tests',item=negative),dict(name='3. Cascade deletion',item=[
        req('Delete playbook','playbooks','DELETE','/playbooks/{{playbook_id}}'),req('Deleted playbook','playbooks','GET','/playbooks/{{playbook_id}}',404),
        req('Cascaded action missing','playbooks','PUT','/actions/{{action_id}}/status',404,dict(status='In Progress'))])])
    items=[]
    for name in ('assets','threats','vulnerabilities'):
        items.extend([req('Generate '+name+' report (admin)','reports','GET','/reports/'+name),
                      req('Generate '+name+' report (auditor)','reports','GET','/reports/'+name,role='auditor'),
                      req('No token '+name,'reports','GET','/reports/'+name,401,role=None),
                      req('Analyst denied '+name,'reports','GET','/reports/'+name,403,role='analyst'),
                      req('User denied '+name,'reports','GET','/reports/'+name,403,role='user')])
    write('reports_b',[dict(name='1. Report access and generation',item=items)])

    # Replace the formerly manual Assets conflict fixture with real API setup.
    assets_path=POSTMAN/'assets.postman_collection.json'
    collection=json.loads(assets_path.read_text())
    fixture_asset={**asset,'asset_name':'Postman FK fixture'}
    fixture_vuln={**vuln,'asset_id':'{{linked_asset_id}}','severity':'Low'}
    collection['item'][-1]=dict(name='4. Automatic linked-record conflict fixture',item=[
        req('Create linked asset','assets','POST','/assets',201,fixture_asset,extra=[savevar('linked_asset_id')]),
        req('Link vulnerability','vulnerabilities','POST','/vulnerabilities',201,fixture_vuln,extra=[savevar('linked_vulnerability_id')]),
        req('Linked vulnerability prevents deletion','assets','DELETE','/assets/{{linked_asset_id}}',409),
        req('Linked asset preserved','assets','GET','/assets/{{linked_asset_id}}'),
        req('Remove fixture vulnerability','vulnerabilities','DELETE','/vulnerabilities/{{linked_vulnerability_id}}'),
        req('Remove fixture asset','assets','DELETE','/assets/{{linked_asset_id}}')])
    collection['info']['description']='Developed by: Marc Bteich. Run all folders in order with all services running. Folder 4 now provisions and cleans up its linked-record fixture automatically.'
    current={v['key']:v for v in collection['variable']}
    for key,value in VARIABLES.items():
        current.setdefault(key,dict(key=key,value=value))
    collection['variable']=list(current.values())
    assets_path.write_text(json.dumps(collection,indent=2)+'\n')

    # Keep every original A request and script intact in the merged document.
    order=['users','assets','incidents','threats','logs','vulnerabilities','notifications','playbooks','reports_a','reports_b']
    merged=dict(info=dict(name='SIDRMS — Elie Medawar and Marc Bteich',schema=SCHEMA,
        description='Merged by Marc Bteich. Original Elie requests/scripts preserved. Run against a separate fresh database with only admin provisioned; the Users folder creates other roles. The integration runner provisions an independent fixture asset before Incidents.'),variable=[],item=[])
    values=dict(VARIABLES)
    for name in order:
        source=json.loads((POSTMAN/(name+'.postman_collection.json')).read_text())
        for variable in source.get('variable',[]):
            values.setdefault(variable['key'],variable.get('value',''))
        folder=dict(name=name,item=copy.deepcopy(source['item']))
        for inherited in ('event','auth'):
            if inherited in source:
                folder[inherited]=copy.deepcopy(source[inherited])
        if name=='incidents':
            folder['item'].insert(0,dict(name='Marc integration fixture',item=[
                req('Create persistent incident fixture asset','assets','POST','/assets',201,{**asset,'asset_name':'Combined incident fixture'},extra=[savevar('asset_id')])]))
        merged['item'].append(folder)
    merged['variable']=[dict(key=k,value=v) for k,v in values.items()]
    (POSTMAN/'SIDRMS.postman_collection.json').write_text(json.dumps(merged,indent=2)+'\n')
    print('Built Person B collections and merged',len(order),'service collections')


if __name__=='__main__':
    main()
