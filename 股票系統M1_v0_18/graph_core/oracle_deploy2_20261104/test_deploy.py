import datetime,json,os,tempfile,unittest
from pathlib import Path
from unittest.mock import patch
from . import deploy as d
from . import legacy as l
CTX={'tenancy':'ocid1.tenancy.SYNTHETIC','region':'ap-tokyo-1'}
class Fake:
 def __init__(self,fail=None):self.ctx=CTX;self.calls=[];self.resources={};self.fail=fail
 def read(self,op,params):
  self.calls.append(('read',op,params))
  if op==('limits','resource-availability','get'):return {'available':100}
  if op[-1]=='get':
   ident=next(iter(params.values()))
   if ident==CTX['tenancy']:return {'id':ident}
   return next(x for x in self.resources.values() if x['id']==ident)
  kind=next((k for k,v in d.LIST.items() if v==op),None)
  return [v for k,v in self.resources.items() if k==kind]
 def call(self,op,params):
  self.calls.append(('write',op,params))
  if op==('compute','compute-capacity-report','create'):
   return {'shape-availabilities':[{'instance-shape':params['shape-availabilities'][0]['instanceShape'],'availability-status':'AVAILABLE'}]}
  kind=next(k for k,v in d.WRITE.items() if v==op)
  if self.fail==kind:raise l.Refused('OCI_OUTCOME_UNKNOWN')
  r={'id':'ocid1.'+kind+'.SYNTHETIC',**params};self.resources[kind]=r;return r
class Tests(unittest.TestCase):
 def setUp(self):
  self.temp=tempfile.TemporaryDirectory(dir=os.environ['DEPLOY2_TEST_ROOT']);self.addCleanup(self.temp.cleanup);self.state=l.State(Path(self.temp.name)/'state');self.cloud=Fake()
  self.choice={'shape':'VM.Standard.A1.Flex','ocpus':1,'ram_gb':6,'ad':'SYNTHETIC_AD','image':'ocid1.image.SYNTHETIC','quota_names':['standard-a1-core-count']}
  self.snap={'context':CTX,'errors':[],'instances':[],'boots':[],'volumes':[]}
  self.p={'version':d.VERSION,'context':CTX,'id':'synthetic-plan','expires':(d.now()+datetime.timedelta(minutes=10)).isoformat(),'snapshot':d.binding(self.snap),'snapshot_data':self.snap,'options':[self.choice],'evidence':{},'reviewed':False}
 def proven(self):
  self.p['reviewed']=True;bound=d.digest({k:v for k,v in self.p.items() if k not in ('evidence','reviewed')})
  for k in d.CATEGORIES:
   name=k+'.txt';raw=b'SYNTHETIC ENGINEERING EVIDENCE NOT AN ORACLE ACCOUNT';(self.state.path/name).write_bytes(raw);self.p['evidence'][k]={'path':name,'bytes':len(raw),'sha256':l.sha(raw),'plan_binding':bound}
  self.state.write('deployment-plan.json',d.sign(self.state,self.p))
 def test_real_success_path_emits_all_oci_resource_operations(self):
  self.proven();pilot=Path('deliveries/m1-oracle-pilot1-20261104/'+l.PILOT_NAME).read_bytes();(self.state.path/l.PILOT_NAME).write_bytes(pilot)
  with patch.object(d,'snapshot',return_value=self.snap),patch.object(d,'quota_check'),patch.object(d,'capacity',return_value=self.choice):
   ledger=d.apply(self.state,self.cloud,{'schema':'mobile-owner-auth/0.1'},'$6$SYNTHETIC')
  self.assertTrue(ledger['complete']);self.assertEqual(set(self.cloud.resources),set(d.WRITE));self.assertEqual(ledger['guest_health'],'NOT_VERIFIED')
  launch=self.cloud.resources['instance'];self.assertEqual(launch['source-details']['bootVolumeSizeInGBs'],50);self.assertEqual(launch['shape-config'],{'ocpus':1,'memoryInGBs':6});self.assertEqual(self.cloud.resources['security']['ingress-security-rules'],[])
 def test_no_evidence_no_mutations(self):
  self.state.write('deployment-plan.json',d.sign(self.state,self.p))
  with self.assertRaisesRegex(l.Refused,'FREE_PROOFS'):d.apply(self.state,self.cloud)
  self.assertEqual(self.cloud.calls,[])
 def test_tampered_expired_plan_refused(self):
  signed=d.sign(self.state,self.p);signed['plan']['id']='changed'
  with self.assertRaisesRegex(l.Refused,'TAMPERED'):d.verify(self.state,signed)
  self.p['expires']=(d.now()-datetime.timedelta(seconds=1)).isoformat()
  with self.assertRaisesRegex(l.Refused,'EXPIRED'):d.verify(self.state,d.sign(self.state,self.p))
  self.assertEqual(d.verify(self.state,d.sign(self.state,self.p),allow_expired=True),self.p)
 def test_evidence_changed_refused(self):
  self.proven();(self.state.path/'account.txt').write_bytes(b'changed')
  with self.assertRaisesRegex(l.Refused,'PROOF_CHANGED'):d.evidence(self.state,self.p)
 def test_repeated_success_no_second_create(self):
  pr=d.Provisioner(self.state,self.cloud,self.p);a=pr.deploy(self.choice,'SYNTHETIC');before=sum(c[0]=='write' for c in self.cloud.calls);b=d.Provisioner(self.state,self.cloud,self.p).deploy(self.choice,'SYNTHETIC');self.assertEqual(a,b);self.assertEqual(before,sum(c[0]=='write' for c in self.cloud.calls))
 def test_crash_after_create_reconciles_by_exact_tag(self):
  pr=d.Provisioner(self.state,self.cloud,self.p);pr.log['steps']['vcn']={'status':'STARTED'};self.state.write(pr.file,pr.log);self.cloud.resources['vcn']={'id':'ocid1.vcn.SYNTHETIC','freeform-tags':{'TwstockaiPilotPlan':self.p['id']}}
  self.assertEqual(d.Provisioner(self.state,self.cloud,self.p).step('vcn',{},CTX['tenancy']),'ocid1.vcn.SYNTHETIC');self.assertFalse(any(c[0]=='write' for c in self.cloud.calls))
 def test_unknown_create_never_reissued(self):
  pr=d.Provisioner(self.state,self.cloud,self.p);pr.log['steps']['vcn']={'status':'STARTED'};self.state.write(pr.file,pr.log)
  with self.assertRaisesRegex(l.Refused,'OUTCOME_UNKNOWN'):d.Provisioner(self.state,self.cloud,self.p).step('vcn',{},CTX['tenancy'])
  self.assertFalse(any(c[0]=='write' for c in self.cloud.calls))
 def test_new_foreign_inventory_stops_before_creates(self):
  self.proven()
  with patch.object(d,'snapshot',return_value={**self.snap,'instances':[{'id':'foreign'}]}):
   with self.assertRaisesRegex(l.Refused,'INVENTORY_OR_QUOTA_CHANGED'):d.apply(self.state,self.cloud)
  self.assertEqual(self.cloud.calls,[])
 def test_guest_is_original_pinned_package_auth_loopback(self):
  text=d.guest(self.p,{'schema':'mobile-owner-auth/0.1'},'$6$SYNTHETIC');cfg=json.loads(text.split('\n',1)[1]);installer=next(f['content'] for f in cfg['write_files'] if f['path'].endswith('install.py'));compile(installer,'guest-install','exec');self.assertIn(l.PILOT_SHA,installer);self.assertNotIn('FM3',installer);runner=next(f['content'] for f in cfg['write_files'] if f['path'].endswith('run.py'));self.assertIn('8786',runner);self.assertFalse(cfg['ssh_pwauth']);self.assertNotIn('tailscale funnel',text)
 def test_capacity_fallback_is_only_declared_free_candidates(self):
  e2={**self.choice,'shape':'VM.Standard.E2.1.Micro','ram_gb':1};self.p['options']=[self.choice,e2]
  def quota(c,p,v):
   if v['shape']=='VM.Standard.A1.Flex':raise l.Refused('SERVICE_QUOTA_INSUFFICIENT')
  with patch.object(d,'quota_check',side_effect=quota):self.assertEqual(d.capacity(self.cloud,self.p),e2)
  self.assertEqual(len([c for c in self.cloud.calls if c[0]=='write']),1)
 def test_inventory_does_not_skip_missing_is_accessible(self):
  calls=[]
  class Inventory:
   ctx=CTX
   def read(self,op,args):
    calls.append((op,args))
    if op==('iam','tenancy','get'):return {'id':CTX['tenancy']}
    if op==('iam','region-subscription','list'):return [{'is-home-region':True,'region-name':CTX['region']}]
    if op==('iam','compartment','list'):return [{'id':'child','lifecycle-state':'ACTIVE'}]
    if op==('iam','availability-domain','list'):return [{'name':'AD'}]
    return []
  s=d.snapshot(Inventory());self.assertEqual(s['errors'],[])
  self.assertEqual({a['compartment-id'] for op,a in calls if op==('compute','instance','list')},{CTX['tenancy'],'child'})
 def test_wrong_home_region_no_mutations(self):
  class Wrong:
   ctx=CTX
   def read(self,op,args):return {'id':CTX['tenancy']} if op[-1]=='get' else [{'is-home-region':True,'region-name':'wrong'}]
  with self.assertRaisesRegex(l.Refused,'HOME_REGION_MISMATCH'):d.snapshot(Wrong())
 def test_service_quota_refuses_unknown_and_insufficient(self):
  class Q:
   ctx=CTX
   def read(self,*args):return {'available':0}
  with self.assertRaisesRegex(l.Refused,'QUOTA_INSUFFICIENT'):d.quota_check(Q(),self.p,self.choice)
if __name__=='__main__':unittest.main(verbosity=2)
