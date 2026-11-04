"""Mock OCI and packaging tests only; not real Oracle/Android validation."""
import contextlib,datetime,io,json,os,stat,subprocess,sys,tempfile,unittest,zipfile,warnings
from pathlib import Path
from unittest.mock import patch
from . import shell_tool as m
CTX={'tenancy':'ocid1.tenancy.oc1..syntheticprivate','region':'ap-tokyo-1'}

class MockCLI:
    def __init__(self,denied=None,home='ap-tokyo-1',billing='ALWAYS_FREE',available=1,incomplete=False):self.calls=[];self.denied=denied;self.home=home;self.billing=billing;self.available=available;self.incomplete=incomplete
    def __call__(self,args,**kw):
        prefix=next((k for k,v in m.READ_OPS.items() if tuple(args[1:1+len(v)])==v),None);assert prefix;self.calls.append(args)
        if self.denied==prefix:return subprocess.CompletedProcess(args,1,b'',b'403 NotAuthorized ocid1.tenancy.SECRET token=DO_NOT_PRINT')
        if prefix=='tenancy':data={'id':CTX['tenancy'],'home-region-key':'NRT'}
        elif prefix=='regions':data=[{'region-name':self.home,'is-home-region':True,'region-key':'NRT'}]
        elif prefix=='compartments':data=[]
        elif prefix=='ads':data=[{'name':'PRIVATE:AP-TOKYO-1-AD-1'}]
        elif prefix=='shapes':data=[{'shape':'VM.Standard.E2.1.Micro','billing-type':self.billing,'quota-names':['vm-standard-e2-1-micro-count']}]
        elif prefix=='instances':data=[{'id':'ocid1.instance.SECRET','shape':'VM.Standard.E2.1.Micro','lifecycle-state':'RUNNING'}]
        elif prefix in ('boots','volumes'):data=[{'id':'ocid1.bootvolume.SECRET','size-in-gbs':50,'lifecycle-state':'AVAILABLE'}]
        elif prefix=='images':data=[{'id':'ocid1.image.SECRET','operating-system':'Oracle Linux','listing-type':'BASE'}]
        elif prefix=='limit_definitions':data=[{'name':'vm-standard-e2-1-micro-count','scope-type':'AD','is-resource-availability-supported':True}]
        elif prefix=='availability':data={'available':self.available,'used':1,'effective-quota-value':2}
        else:data=[]
        obj={'data':data}
        if self.incomplete and prefix=='compartments':obj['opc-next-page']='MORE'
        return subprocess.CompletedProcess(args,0,m.encode(obj),b'')

class ShellTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):cls.pilot=Path('deliveries/m1-oracle-pilot1-20261104/'+m.PILOT_NAME).read_bytes()
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory(dir=os.environ['SHELL1_TEST_ROOT']);self.addCleanup(self.tmp.cleanup);self.root=Path(self.tmp.name);self.state=m.State(self.root/'state')
    def client(self,**kw):
        fake=MockCLI(**kw);return m.OCI(CTX,runner=fake,executable='/mock/oci'),fake
    def inspect(self,**kw):
        client,fake=self.client(**kw);v=m.save_inspection(self.state,client=client,context=CTX,package=self.pilot);return v,client,fake
    def plan(self,v):return m.make_plan(self.state,v,now=datetime.datetime.fromisoformat(v['observed_at']),tool_digest='TEST_RELEASE')
    def archive(self,rows,manifest=None):
        out=io.BytesIO()
        with warnings.catch_warnings():
            warnings.simplefilter('ignore',UserWarning)
            with zipfile.ZipFile(out,'w') as z:
                for name,body in rows:z.writestr(name,body)
                if manifest is not None:z.writestr('MANIFEST.json',m.encode(manifest))
        return out.getvalue()
    def verify_custom(self,raw,manifest=b'{}'):return m.validate_zip(raw,expected_bytes=len(raw),expected_sha=m.sha(raw),manifest_sha=m.sha(manifest))
    def test_fixed_pilot_all_members_manifest_crc(self):
        r=m.validate_zip(self.pilot);self.assertEqual(r['members'],26);self.assertEqual(r['commit'],m.PILOT_COMMIT)
    def test_source_sha_length_and_manifest_sha_reject(self):
        for raw in [self.pilot+b'x',b'x'+self.pilot[1:]]:
            with self.assertRaisesRegex(m.Refused,'ZIP_SOURCE_SHA'):m.validate_zip(raw)
        with self.assertRaisesRegex(m.Refused,'ZIP_MANIFEST_SHA'):self.verify_custom(self.archive([('MANIFEST.json',b'fake')]))
    def test_zip_paths_and_duplicate_names_reject(self):
        for name in ['../escape','/escape','a/../escape','a\\escape','C:/escape','a//x','caf\u00e9']:
            with self.assertRaises(m.Refused):self.verify_custom(self.archive([(name,b'x')]))
        for rows in [[('a',b'x'),('a',b'y')],[('A',b'x'),('a',b'y')]]:
            with self.assertRaisesRegex(m.Refused,'ZIP_DUPLICATE'):self.verify_custom(self.archive(rows))
    def test_zip_symlink_and_directory_collision_reject(self):
        out=io.BytesIO()
        with zipfile.ZipFile(out,'w') as z:
            x=zipfile.ZipInfo('link');x.create_system=3;x.external_attr=(stat.S_IFLNK|0o777)<<16;z.writestr(x,'target')
        with self.assertRaisesRegex(m.Refused,'ZIP_MEMBER_TYPE'):self.verify_custom(out.getvalue())
        with self.assertRaisesRegex(m.Refused,'ZIP_FILE_DIRECTORY_COLLISION'):self.verify_custom(self.archive([('a',b'x'),('a/b',b'y')]))
    def test_manifest_member_set_and_raw_sha_reject(self):
        mf={'schema':'synthetic-pilot-manifest/0.1','synthetic_only':True,'contains_credentials':False,'contains_private_market_data':False,'entry':'a','files':[{'path':'a','bytes':1,'sha256':m.sha(b'x')} ]}
        with self.assertRaisesRegex(m.Refused,'ZIP_MEMBER_SHA'):self.verify_custom(self.archive([('a',b'y')],mf),m.encode(mf))
        with self.assertRaisesRegex(m.Refused,'ZIP_MANIFEST_SET'):self.verify_custom(self.archive([('a',b'x'),('extra',b'z')],mf),m.encode(mf))
    def test_inspect_plan_have_only_exact_read_operations(self):
        v,c,f=self.inspect();self.plan(v);self.assertGreater(len(f.calls),5);self.assertEqual(v['oracle_mutation_calls'],0)
        for args in f.calls:self.assertFalse(any(x in args for x in ['create','update','delete','launch','start','stop','terminate']))
    def test_wrong_home_region_stops_compute_queries(self):
        v,c,_=self.inspect(home='us-ashburn-1');self.assertEqual(v['gates']['TENANCY_HOME']['status'],'FAIL');self.assertFalse(any(x['operation']=='instances' for x in c.calls));self.assertEqual(v['created_resources'],[])
    def test_selected_compute_quota_insufficient(self):
        v,_,_=self.inspect(available=0);self.assertEqual(v['gates']['SERVICE_QUOTA']['status'],'FAIL')
    def test_permission_or_incomplete_page_not_zero_inventory(self):
        for kwargs in [{'denied':'boots'},{'incomplete':True}]:
            v,_,_=self.inspect(**kwargs);self.assertEqual(v['gates']['INVENTORY']['status'],'UNKNOWN');self.assertIsNone(v['totals']['boot_volumes'])
    def test_limited_free_paid_not_always_free(self):
        for bill in ['LIMITED_FREE','PAID',None]:
            v,_,_=self.inspect(billing=bill);self.assertEqual(v['gates']['SHAPE_BILLING']['status'],'UNKNOWN');self.assertIsNone(v['selected'])
    def test_compute_billing_not_all_component_zero_cost(self):
        v,_,_=self.inspect();self.assertEqual(v['gates']['SHAPE_BILLING']['status'],'PASS')
        for key in ['FREE_STORAGE','ACCOUNT_FREE','IMAGE_COST','NETWORK_COST','CAPACITY','TAILNET']:self.assertEqual(v['gates'][key]['status'],'UNKNOWN')
        plan=self.plan(v)['plan'];self.assertEqual(plan['status'],'BLOCKED');self.assertEqual(plan['resources_to_create'],[]);self.assertEqual(plan['proposal']['public_ingress'],[])
    def test_plan_tamper_version_and_time_reject(self):
        v,_,_=self.inspect();s=self.plan(v);t=datetime.datetime.fromisoformat(v['observed_at']);s['plan']['status']='QUALIFIED_NOT_DEPLOYED'
        with self.assertRaisesRegex(m.Refused,'PLAN_TAMPERED'):m.verify_plan(self.state,s,now=t,tool_digest='TEST_RELEASE')
        s=self.plan(v)
        with self.assertRaisesRegex(m.Refused,'PLAN_VERSION'):m.verify_plan(self.state,s,now=t,tool_digest='CHANGED')
        for dt in [t-datetime.timedelta(seconds=1),t+datetime.timedelta(seconds=600)]:
            with self.assertRaisesRegex(m.Refused,'PLAN_EXPIRED'):m.verify_plan(self.state,s,now=dt,tool_digest='TEST_RELEASE')
        with self.assertRaisesRegex(m.Refused,'INSPECTION_STALE'):m.make_plan(self.state,v,now=t+datetime.timedelta(seconds=601))
    def test_wrong_account_refused_before_refresh(self):
        v,_,_=self.inspect();self.plan(v);c,f=self.client()
        with self.assertRaisesRegex(m.Refused,'ACCOUNT_OR_REGION'):m.apply(self.state,context=dict(CTX,tenancy='ocid1.tenancy.oc1..different'),client=c,now=datetime.datetime.fromisoformat(v['observed_at']),tool_digest='TEST_RELEASE')
        self.assertEqual(f.calls,[])
        changed,changed_runner=self.client(available=2)
        with self.assertRaisesRegex(m.Refused,'SOURCE_OR_QUOTA_CHANGED'):m.apply(self.state,context=CTX,client=changed,now=datetime.datetime.fromisoformat(v['observed_at']),tool_digest='TEST_RELEASE')
        self.assertFalse(any('create' in x for x in changed_runner.calls))
    def test_repeated_apply_no_mutation_or_fake_deployed_receipt(self):
        v,_,_=self.inspect();self.plan(v)
        for _ in range(2):
            c,f=self.client()
            with self.assertRaisesRegex(m.Refused,'APPLY_BLOCKED'):m.apply(self.state,context=CTX,client=c,now=datetime.datetime.fromisoformat(v['observed_at']),tool_digest='TEST_RELEASE')
            self.assertFalse(any('create' in x or 'update' in x or 'delete' in x for x in f.calls))
        self.assertFalse((self.state.path/'deployed.json').exists())
    def test_mutation_and_argument_injection_before_runner_reject(self):
        c,f=self.client()
        for op,params in [('launch',{}),('instances',{'compartment-id':'--evil'}),('instances',{'endpoint':'https://example.invalid'}),('instances',{'debug':True})]:
            with self.assertRaises(m.Refused):c.read(op,params)
        self.assertEqual(f.calls,[])
    def test_safe_summary_has_no_private_identifiers_or_error_tokens(self):
        v,_,_=self.inspect(denied='boots');out=io.StringIO()
        with contextlib.redirect_stdout(out):m.report(v)
        for secret in ['ocid1.','PRIVATE:','syntheticprivate','DO_NOT_PRINT','token=']:self.assertNotIn(secret,out.getvalue())
        self.assertIn('資源建立 0',out.getvalue())
    def test_private_modes_symlink_and_exclusive_lock(self):
        self.assertEqual(stat.S_IMODE(self.state.path.stat().st_mode),0o700);self.assertEqual(stat.S_IMODE((self.state.path/'plan-key.bin').stat().st_mode),0o600);ln=self.root/'link';ln.symlink_to(self.state.path)
        with self.assertRaisesRegex(m.Refused,'SYMLINK'):m.State(ln)
        with self.state.lock():
            with self.assertRaisesRegex(m.Refused,'ANOTHER'):
                with self.state.lock():pass
    def test_no_cli_stops_safely_and_retains_pilot_validation(self):
        with patch.object(m,'identity',return_value=CTX),patch.object(m.shutil,'which',return_value=None):v=m.save_inspection(self.state,package=self.pilot)
        self.assertEqual(v['gates']['ACCOUNT_CONTEXT']['status'],'UNKNOWN');self.assertEqual(v['gates']['PILOT']['status'],'PASS');self.assertEqual(v['oracle_read_calls'],0)
    def test_context_uses_official_environment_not_pasted_credentials(self):
        with patch.object(Path,'is_file',return_value=False):
            self.assertEqual(m.identity({'OCI_TENANCY':CTX['tenancy'],'OCI_REGION':CTX['region']}),CTX)
            with self.assertRaises(m.Refused):m.identity({})
    def test_status_and_stop_subprocess_no_cli_or_identifiers(self):
        home=self.root/'home';home.mkdir();env=dict(os.environ,HOME=str(home),OCI_TENANCY=CTX['tenancy'],OCI_REGION=CTX['region'])
        for cmd in ['status','stop']:
            r=subprocess.run([sys.executable,str(Path(m.__file__).resolve()),cmd],env=env,capture_output=True)
            self.assertIn('資源建立 0'.encode() if cmd=='status' else '沒有刪除'.encode(),r.stdout);self.assertNotIn(b'ocid1.',r.stdout+r.stderr)

if __name__=='__main__':unittest.main(verbosity=2)
