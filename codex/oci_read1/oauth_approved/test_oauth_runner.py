"""Only new OAuth runner contracts; synthetic crypto/REST, no live Oracle claim."""
import copy,hashlib,json,os,subprocess,sys,tempfile,time,unittest,zipfile
from pathlib import Path
from unittest.mock import patch
from cryptography.hazmat.primitives.asymmetric import rsa
import jwt,yaml
from codex.oci_ctrl1.handler import REPO,REPO_ID,OWNER_ID,Refused,git_blob
from codex.oci_read1.oauth_approved import native as n,federation as f
from codex.oci_read1.oauth_approved.build import build
ROOT=Path(__file__).resolve().parents[3]
FOLDER=Path('/workspace/twstockai-local-data/oci_read1_oauth_20261105')
class NativeRest:
    def __init__(self,package,ctx,event,now):
        self.calls=[];self.rows=[];self.ctx=ctx;self.event=event;self.now=now;self.package=package
        self.release=dict(schema='read1-oauth-release/0.2',version=n.VERSION,source_app_id=400,bot_id=600,bot_app_id=700,package_sha256=hashlib.sha256(package).hexdigest(),package_blob=git_blob(package))
        self.config=dict(schema='read1-server-config/0.2',domain_url='https://idcs-synthetic.identity.oraclecloud.com',client_id='SYNTHETIC_CLIENT_ID',region='ap-tokyo-1',pilot_compartment='ocid1.compartment.oc1..synthetic',availability_domains=['synthetic:AP-TOKYO-1-AD-1'])
        self.raw_config=(json.dumps(self.config)+'\n').encode()
        self.q=dict(schema='read1-owner-account/0.2',source='OWNER_CONSOLE_OBSERVATION_NOT_ORACLE_API',captured_at='2026-11-05T00:00:00Z',expires_at='2026-11-06T00:00:00Z',config_binding='SAME_IMMUTABLE_WORKFLOW_COMMIT',observations=dict(domain_kind='Free',wif_feature_and_region='SYNTHETIC_ONLY',pilot_scope_and_iam='SYNTHETIC_ONLY',quota_and_billing='SYNTHETIC_ONLY',private_writers_review='SYNTHETIC_ONLY'),findings={x:'OWNER_CONFIRMED' for x in n.REVIEW_FLAGS},config=self.config)
    def content(self,path,sha):
        assert sha==self.ctx['GITHUB_WORKFLOW_SHA']
        raw={'read1/oauth/release.json':json.dumps(self.release).encode(),n.PATH:n.render_workflow(self.package),'read1/oauth/account.json':json.dumps(self.q).encode()}[path]
        return raw,git_blob(raw)
    def comments(self):return self.rows
    def request(self,method,path,data=None):
        self.calls.append((method,path))
        if method=='GET':
            if path=='':return dict(id=REPO_ID,private=True,full_name=REPO,default_branch='main')
            if path=='/actions/runs/42':return dict(id=42,event='issue_comment',head_sha='a'*40,head_branch='main',path=n.PATH,run_attempt=1,status='in_progress',actor={'id':OWNER_ID},triggering_actor={'id':OWNER_ID},repository={'id':REPO_ID},head_repository={'id':REPO_ID},workflow_id=43,created_at='2026-11-05T00:00:01Z')
            if path=='/actions/workflows/43':return dict(id=43,path=n.PATH,state='active')
            if path=='/issues/comments/800':return self.event['comment']
            if path=='/collaborators/blue1998-glitch/permission':return dict(user={'id':OWNER_ID},permission='admin')
        if method=='POST':
            row=dict(id=900,body=data['body'],user={'id':600},performed_via_github_app={'id':700});self.rows.append(row);return row
        if method=='PATCH':self.rows[0]['body']=data['body'];return self.rows[0]
        raise AssertionError('unexpected path')
class Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.key=rsa.generate_private_key(public_exponent=65537,key_size=2048)
        cls.jwk=json.loads(jwt.algorithms.RSAAlgorithm.to_jwk(cls.key.public_key()));cls.jwk.update(kid='synthetic',use='sig')
    def setUp(self):
        self.now=1762300802
        import datetime
        self.now=datetime.datetime.fromisoformat('2026-11-05T00:00:02+00:00').timestamp()
        self.ctx=dict(GITHUB_ACTIONS='true',GITHUB_EVENT_NAME='issue_comment',GITHUB_REPOSITORY=REPO,GITHUB_REPOSITORY_ID=str(REPO_ID),GITHUB_ACTOR_ID=str(OWNER_ID),GITHUB_RUN_ATTEMPT='1',GITHUB_REF='refs/heads/main',GITHUB_WORKFLOW_REF=REPO+'/'+n.PATH+'@refs/heads/main',GITHUB_WORKFLOW_SHA='a'*40,GITHUB_SHA='a'*40,GITHUB_RUN_ID='42')
        self.event=dict(action='created',repository={'id':REPO_ID,'private':True},sender={'id':OWNER_ID},issue={'number':1},comment=dict(id=800,body='{"schema":"oci-read/0.1","operation":"list_pilot_compartment_resources"}',issue_url='https://api.github.com/repos/'+REPO+'/issues/1',user={'id':OWNER_ID,'login':'blue1998-glitch'},performed_via_github_app={'id':400},created_at='2026-11-05T00:00:00Z',updated_at='2026-11-05T00:00:00Z'))
        self.package=(ROOT/'codex/oci_read1/oauth_approved/Twstockai_READ1_OAUTH_RUNNER.pyz').read_bytes();self.api=NativeRest(self.package,self.ctx,self.event,self.now)
    def gate(self):return n.Gate(self.api,self.ctx,self.event,self.package,self.now)
    def claims(self):return dict(iss=f.ISSUER,aud=f.AUDIENCE,sub='repo:'+REPO+':ref:refs/heads/main',exp=int(self.now)+300,iat=int(self.now)-1,nbf=int(self.now)-1,jti='synthetic-jti',repository=REPO,repository_id=str(REPO_ID),repository_visibility='private',actor_id=str(OWNER_ID),event_name='issue_comment',ref='refs/heads/main',workflow_ref=REPO+'/'+n.PATH+'@refs/heads/main',workflow_sha='a'*40,run_id='42',run_attempt='1')
    def token(self,c):return jwt.encode(c,self.key,algorithm='RS256',headers={'kid':'synthetic'})
    def test_native_read_profile_without_installation_is_separate(self):
        self.assertEqual(self.gate().verify().cid,800);self.assertEqual(self.gate().verify().qualification(),self.api.config)
    def test_wrong_native_actor_scope_and_rerun_fail_before_any_secret(self):
        for key,value in [('GITHUB_ACTOR_ID','1'),('GITHUB_RUN_ATTEMPT','2'),('GITHUB_WORKFLOW_SHA','b'*40)]:
            self.setUp();self.ctx[key]=value
            with self.assertRaises(Refused):self.gate().verify()
    def test_canonical_app_permission_and_comment_schema_are_not_bypassed(self):
        self.event['comment']['performed_via_github_app']['id']=999
        with self.assertRaises(Refused):self.gate().verify()
        self.setUp();self.event['comment']['body']='{"schema":"oci-read/0.1","operation":"list_pilot_compartment_resources","url":"PRIVATE"}'
        with self.assertRaises(Refused):self.gate().verify()
        self.setUp();original=self.api.request
        self.api.request=lambda method,path,data=None:dict(user={'id':OWNER_ID},permission='read') if path=='/collaborators/blue1998-glitch/permission' else original(method,path,data)
        with self.assertRaises(Refused):self.gate().verify()
    def test_unknown_account_blocks_no_secret_factory_and_consumes_nonce(self):
        self.api.q['findings']['free_domain_wif']='UNKNOWN';gate=self.gate().verify()
        with patch.object(f,'execute',side_effect=AssertionError('must not execute')):
            self.assertFalse(gate.authorize());self.assertFalse(gate.authorize())
        self.assertEqual(len(self.api.rows),1);self.assertIn('BLOCKED_ACCOUNT_QUALIFICATION',self.api.rows[0]['body'])
    def test_qualification_expiry_wrong_config_and_minimum_iam_fail_closed(self):
        for kind in ['expired','config','iam']:
            self.setUp()
            if kind=='expired':self.api.q['expires_at']='2026-11-05T00:00:01Z'
            if kind=='config':self.api.q['config_binding']='MOVING_BRANCH_HEAD'
            if kind=='iam':self.api.q['findings']['minimum_list_iam']='UNKNOWN'
            with self.assertRaises(Refused):self.gate().verify().qualification()
    def test_nonce_claim_is_once_and_bound_to_native_run(self):
        gate=self.gate().verify();self.assertTrue(gate.authorize());self.assertEqual(gate.claim(),900)
        with self.assertRaises(Refused):gate.claim()
        self.ctx['GITHUB_RUN_ID']='99'
        with self.assertRaises(Refused):gate.read()
    def test_code_and_workflow_manifest_tamper_refused(self):
        self.api.release['package_sha256']='0'*64
        with self.assertRaises(Refused):self.gate().verify()
        from codex.oci_read1.oauth_approved.entry import integrity
        with self.assertRaises(Exception):integrity(self.package[:-30])
    def test_real_rsa_signature_and_exact_native_oidc_claims(self):
        claims=self.claims();self.assertEqual(f.verify_job_token(self.token(claims),self.ctx,self.now,{'keys':[self.jwk]})['run_id'],'42')
        for key,bad in [('iss','https://wrong.invalid'),('aud','wrong'),('sub','wrong'),('workflow_sha','b'*40),('event_name','pull_request'),('actor_id','1'),('run_id','99'),('repository_id','2')]:
            c=self.claims();c[key]=bad
            with self.assertRaises(Refused):f.verify_job_token(self.token(c),self.ctx,self.now,{'keys':[self.jwk]})
    def test_expired_future_and_unknown_signing_key_refused(self):
        for key,bad in [('exp',int(self.now)-1),('iat',int(self.now)+10),('nbf',int(self.now)+10)]:
            c=self.claims();c[key]=bad
            with self.assertRaises(Refused):f.verify_job_token(self.token(c),self.ctx,self.now,{'keys':[self.jwk]})
        with self.assertRaises(Refused):f.verify_job_token(self.token(self.claims()),self.ctx,self.now,{'keys':[]})
        token=self.token(self.claims());parts=token.split('.')
        import base64
        payload=self.claims();payload['jti']='TAMPERED_SIGNATURE'
        parts[1]=base64.urlsafe_b64encode(json.dumps(payload).encode()).rstrip(b'=').decode()
        with self.assertRaises(Refused):f.verify_job_token('.'.join(parts),self.ctx,self.now,{'keys':[self.jwk]})
    def test_rpst_request_exactly_control_plane_not_access_token(self):
        from urllib.parse import parse_qs
        form=parse_qs(f.exchange_form('SYNTHETIC_TOKEN','SYNTHETIC_PUBLIC_KEY').decode())
        self.assertEqual(form['requested_token_type'],['urn:oci:token-type:oci-rpst']);self.assertEqual(form['rpst_exp'],['5']);self.assertNotIn('access_token',form);self.assertEqual(form['res_type'],['githubactions'])
    def test_error_projection_never_returns_raw_ids_or_messages(self):
        out=f.error_projection(403,'NotAuthorizedOrNotFound','SYNTHETIC_REQUEST_ID')
        self.assertEqual(out['code'],'NotAuthorizedOrNotFound');self.assertNotIn('SYNTHETIC_REQUEST_ID',json.dumps(out));self.assertEqual(len(out['request_id_sha256']),64)
        self.assertEqual(f.error_projection(403,'PRIVATE_ERROR:ocid1.secret',None)['code'],'UNCLASSIFIED_REDACTED')
        self.assertEqual(f.control_plane_call_count([]),0)
        self.assertEqual(f.control_plane_call_count([{'http_status':403}]),1)
        self.assertEqual(f.control_plane_call_count([{'http_status':None}]),'UNKNOWN')
        self.assertEqual(f.control_plane_status([{'http_status':None}]),'UNKNOWN')
        self.assertEqual(f.control_plane_status([{'http_status':403}]),'ACTUAL_API_RESPONSES')
    def test_server_scope_rejects_arbitrary_url_root_duplicate_ad(self):
        for key,value in [('domain_url','https://evil.invalid'),('pilot_compartment','ocid1.tenancy.oc1..x'),('availability_domains',['Aaa','Aaa'])]:
            c=copy.deepcopy(self.api.config);c[key]=value
            with self.assertRaises(Refused):f.validate_config(c)
    def test_workflow_separates_secrets_and_has_default_deny(self):
        text=n.render_workflow(self.package).decode();doc=yaml.safe_load(text)
        self.assertIn("vars.OCI_READ1_ENABLED == 'OWNER_REVIEWED_ONCE'",doc['jobs']['authorize']['if'])
        self.assertNotIn('secrets.',json.dumps(doc['jobs']['authorize']));self.assertNotIn('id-token',doc['jobs']['authorize']['permissions']);self.assertEqual(doc['jobs']['read']['permissions']['id-token'],'write')
        self.assertEqual(doc['jobs']['read']['needs'],'authorize');self.assertEqual(text.count('secrets.'),1)
        for bad in ['uses:','checkout','workflow_dispatch','schedule:','id-token: write\n  authorize','curl|']:self.assertNotIn(bad,text)
        script=doc['jobs']['authorize']['steps'][0]['run'];code=script.split("python3.12 - <<'READ1_BOOTSTRAP'\n",1)[1].rsplit('READ1_BOOTSTRAP',1)[0];compile(code,'bootstrap','exec')
    def test_package_rebuild_and_offline_inspect_not_oci_success(self):
        with tempfile.TemporaryDirectory(dir=FOLDER) as d:
            file=Path(d)/'runner.pyz';build(ROOT,file);self.assertEqual(file.read_bytes(),self.package)
            result=json.loads(subprocess.check_output([sys.executable,str(file),'inspect']))
            self.assertEqual(result['oracle_calls'],0);self.assertEqual(result['status'],'DEFAULT_DENY_PENDING_ACCOUNT_EVIDENCE')
    def test_authorized_read_handoff_and_receipt_remain_run_bound(self):
        gate=self.gate().verify();self.assertTrue(gate.authorize());gate.claim()
        with patch.object(f,'execute',return_value=dict(status='OCI_READ_OK',oracle_calls=3,source='SYNTHETIC_TEST_ONLY')) as execute:
            self.assertEqual(gate.read(),'OCI_READ_OK');execute.assert_called_once()
        out=gate.prior_value(self.api.rows[0]);self.assertEqual(out['native_run_id'],42);self.assertEqual(out['request_comment_id'],800);self.assertEqual(out['source'],'SYNTHETIC_TEST_ONLY');self.assertEqual(len(out['account_evidence_sha256']),64)
        with self.assertRaises(Refused):gate.read()
    def test_github_oidc_http_failure_is_not_claimed_as_oracle_denial(self):
        import urllib.error
        with patch.object(f,'request_job_token',side_effect=urllib.error.HTTPError('https://synthetic.actions.githubusercontent.com',403,'PRIVATE_MESSAGE',{},None)):
            out=f.execute(self.api.config,self.ctx,self.now)
        self.assertEqual(out['oracle_calls'],0);self.assertEqual(out['identity_exchange_calls'],0);self.assertEqual(out['reason'],'GITHUB_OIDC_SOURCE_HTTP_REFUSED');self.assertNotIn('PRIVATE_MESSAGE',json.dumps(out))
    def test_locked_dependency_graph_satisfies_all_active_requirements(self):
        from packaging.markers import default_environment
        from packaging.requirements import Requirement
        from packaging.utils import canonicalize_name
        from packaging.version import Version
        meta=json.loads((ROOT/'codex/oci_read1/oauth_approved/dependency-metadata.json').read_text());versions={x['name']:Version(x['version']) for x in meta['packages']};env=default_environment();env.update(python_version='3.12',python_full_version='3.12.12',extra='')
        for item in meta['packages']:
            for raw in item['requires'] or []:
                r=Requirement(raw)
                if r.marker and not r.marker.evaluate(env):continue
                self.assertIn(canonicalize_name(r.name),versions);self.assertIn(versions[canonicalize_name(r.name)],r.specifier)
if __name__=='__main__':unittest.main(verbosity=2)
