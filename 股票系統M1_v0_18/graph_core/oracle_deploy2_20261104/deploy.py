"""Conditional real OCI provisioning; private evidence, never forced eligibility."""
import decimal
import argparse,base64,datetime,getpass,hashlib,hmac,inspect,json,os,secrets,shutil,stat,subprocess,sys,time,uuid
from pathlib import Path
try:from . import legacy as l
except ImportError:import legacy as l
VERSION='oracle-deploy2/0.2'
WRITE={'compartment':('iam','compartment','create'),'vcn':('network','vcn','create'),'gateway':('network','internet-gateway','create'),'routes':('network','route-table','create'),'security':('network','security-list','create'),'subnet':('network','subnet','create'),'instance':('compute','instance','launch')}
LIST={'compartment':('iam','compartment','list'),'vcn':('network','vcn','list'),'gateway':('network','internet-gateway','list'),'routes':('network','route-table','list'),'security':('network','security-list','list'),'subnet':('network','subnet','list'),'instance':('compute','instance','list')}
CATEGORIES={'account':'帳戶：Billing & Cost Management → Upgrade and Manage Payment，Plan Type=Free Tier；不Upgrade', 'compute':'Compute → Create instance：全部候選配置明示Always Free eligible；整租戶A1最多4CPU／24GB、E2最多2台，本月A1時數仍足夠，非試用抵扣','storage':'Storage → Block Storage → Boot/Block Volumes：整租戶Home Region總量及保留額度；新50GB、10 VPU無額外費','image':'Compute建立頁Image：所選Ubuntu22.04官方映像，無Marketplace／授權費','network':'Networking → VCN、Public IP及官方Pricing：本計畫VCN/IGW/路由/安全清單/短期公網IPv4與流量均零費用；不NAT/LB/VPN服務'}
def digest(v):return l.sha(l.encode(v))
def now():return datetime.datetime.now(datetime.timezone.utc)
class Cloud:
 def __init__(self,ctx,state=None):self.ctx=ctx;self.state=state
 def call(self,parts,params):
  args=['oci',*parts]
  for k,v in params.items():
   args+=['--'+k]
   if k=='all' and v is True:continue
   args.append(json.dumps(v,separators=(',',':')) if isinstance(v,(dict,list)) else str(v).lower() if type(v)is bool else str(v))
  args+=['--region',self.ctx['region'],'--output','json','--max-retries','0']
  try:r=subprocess.run(args,capture_output=True,timeout=90)
  except (OSError,subprocess.TimeoutExpired):raise l.Refused('OCI_OUTCOME_UNKNOWN')
  if r.returncode:
   if self.state is not None:self.state.record('oci-failure',{'operation':list(parts),'observed_at':now().isoformat(),'returncode':r.returncode,'stdout':r.stdout[:32768].decode('utf-8','replace'),'stderr':r.stderr[:32768].decode('utf-8','replace'),'private_only':True})
   raise l.Refused('OCI_REQUEST_FAILED_'+('_'.join(parts)).upper())
  reason='EMPTY_STDOUT' if not r.stdout.strip() else 'NON_JSON'
  try:
   value=json.loads(r.stdout)
   reason='MISSING_DATA' if not isinstance(value,dict) or 'data' not in value else 'UNEXPECTED_DATA_TYPE'
   if isinstance(value,dict) and isinstance(value.get('data'),(dict,list)):return value['data']
  except (ValueError,UnicodeError):pass
  if self.state is not None:self.state.record('oci-response-invalid',{'operation':list(parts),'observed_at':now().isoformat(),'reason':reason,'returncode':r.returncode,'stdout':r.stdout[:32768].decode('utf-8','replace'),'stderr':r.stderr[:32768].decode('utf-8','replace'),'private_only':True})
  print('查詢未解析：'+' '.join(parts)+'；回應類型：'+reason+'；原件只留本人私有目錄。')
  raise l.Refused('OCI_RESPONSE_INVALID_'+('_'.join(parts)).upper()+'_'+reason)
 def read(self,parts,params):
  if parts[-1] not in ('list','get'):raise l.Refused('NOT_READONLY')
  return self.call(parts,params)

def snapshot(cloud):
 ctx=cloud.ctx;t=cloud.read(('iam','tenancy','get'),{'tenancy-id':ctx['tenancy']});rs=cloud.read(('iam','region-subscription','list'),{'tenancy-id':ctx['tenancy'],'all':True})
 homes=[r for r in rs if r.get('is-home-region')]
 if t['id']!=ctx['tenancy'] or len(homes)!=1 or homes[0]['region-name']!=ctx['region']:raise l.Refused('HOME_REGION_MISMATCH')
 cs=cloud.read(('iam','compartment','list'),{'compartment-id':ctx['tenancy'],'compartment-id-in-subtree':True,'access-level':'ANY','all':True});cs=[{'id':ctx['tenancy']}]+[c for c in cs if c.get('lifecycle-state')=='ACTIVE'];ads=cloud.read(('iam','availability-domain','list'),{'compartment-id':ctx['tenancy'],'all':True})
 if len(cs)>32 or not 0<len(ads)<=8:raise l.Refused('INVENTORY_SCOPE_BOUND')
 out={'context':ctx,'compartments':cs,'ads':ads,'instances':[],'boots':[],'volumes':[],'errors':[],'shapes':{},'images':[],'quotas':[]}
 for c in cs:
  for kind,op in [('instances',('compute','instance','list')),('volumes',('bv','volume','list'))]:
   try:out[kind]+=cloud.read(op,{'compartment-id':c['id'],'all':True})
   except l.Refused:out['errors'].append(kind)
  for ad in ads:
   try:out['boots']+=cloud.read(('bv','boot-volume','list'),{'compartment-id':c['id'],'availability-domain':ad['name'],'all':True})
   except l.Refused:out['errors'].append('boots')
 for ad in ads:out['shapes'][ad['name']]=cloud.read(('compute','shape','list'),{'compartment-id':ctx['tenancy'],'availability-domain':ad['name'],'all':True})
 out['images']=cloud.read(('compute','image','list'),{'compartment-id':ctx['tenancy'],'operating-system':'Canonical Ubuntu','operating-system-version':'22.04','all':True})
 for service in ('compute','block-storage','vcn'):
  out['quotas'].append(cloud.read(('limits','value','list'),{'compartment-id':ctx['tenancy'],'service-name':service,'all':True}))
 return out

def binding(s):
 # All official records bound; sorting avoids harmless list order changes.
 def normal(v):
  if isinstance(v,list):return sorted([normal(x) for x in v],key=lambda x:l.encode(x))
  if isinstance(v,dict):return {k:normal(x) for k,x in v.items() if k not in ('time-last-modified',)}
  return v
 return digest(normal(s))

def options(s,cloud):
 opts=[]
 for shape,cpu,ram in [('VM.Standard.A1.Flex',1,6),('VM.Standard.E2.1.Micro',1,1)]:
  for ad in s['ads']:
   native=next((x for x in s['shapes'][ad['name']] if x['shape']==shape and x.get('billing-type') in ('ALWAYS_FREE','LIMITED_FREE')),None)
   if not native:continue
   # Compatibility API is required; OS label or same CPU is insufficient.
   for image in sorted(s['images'],key=lambda x:x.get('time-created',''),reverse=True):
    if image.get('compartment-id') is not None or image.get('operating-system')!='Canonical Ubuntu':continue
    compat=cloud.read(('compute','image-shape-compatibility-entry','list'),{'image-id':image['id'],'all':True})
    if not any(c.get('shape')==shape for c in compat):continue
    opts.append({'shape':shape,'ocpus':cpu,'ram_gb':ram,'ad':ad['name'],'image':image['id'],'billing_type':native['billing-type'],'quota_names':native.get('quota-names',[])});break
 return opts

def sign(state,value):return {'plan':value,'hmac':hmac.new(state.key,l.encode(value),hashlib.sha256).hexdigest()}
def verify(state,p,allow_expired=False):
 v=p['plan']
 if not hmac.compare_digest(p.get('hmac',''),sign(state,v)['hmac']):raise l.Refused('PLAN_TAMPERED')
 if v['version']!=VERSION or (not allow_expired and now()>=datetime.datetime.fromisoformat(v['expires'])):raise l.Refused('PLAN_EXPIRED_OR_VERSION')
 return v

def plan(state,cloud):
 if (state.path/'deployment-plan.json').exists():
  old=verify(state,state.read('deployment-plan.json'),allow_expired=True)
  if old['context']!=cloud.ctx:raise l.Refused('ACCOUNT_OR_REGION_CHANGED')
  if (state.path/('resources-'+old['id']+'.json')).exists():return old
 s=snapshot(cloud)
 if s['errors']:state.record('deploy-inspection',s);raise l.Refused('INVENTORY_PARTIAL_NO_ZERO_ASSUMPTION')
 active=lambda xs:[x for x in xs if x.get('lifecycle-state') not in ('TERMINATED','DELETED')]
 volumes=active(s['boots']+s['volumes'])
 if any(type(x.get('size-in-gbs')) is not int for x in volumes):raise l.Refused('STORAGE_UNKNOWN')
 used=sum(x['size-in-gbs'] for x in volumes)
 if used+50>200:raise l.Refused('FREE_STORAGE_INSUFFICIENT')
 opts=options(s,cloud)
 qualified=[]
 for candidate in opts:
  try:candidate['free_allocation']=free_allocation(s,candidate);qualified.append(candidate)
  except l.Refused as e:
   if e.code!='ALWAYS_FREE_COMPUTE_EXHAUSTED':raise
 opts=qualified
 if not opts:raise l.Refused('NO_COMPATIBLE_FREE_CANDIDATE')
 p={'version':VERSION,'context':cloud.ctx,'created':now().isoformat(),'expires':(now()+datetime.timedelta(minutes=30)).isoformat(),'snapshot':binding(s),'snapshot_data':s,'options':opts,'boot_gb':50,'vpus_per_gb':10,'storage_used_gb':used,'pilot_sha':l.PILOT_SHA,'resource_types':list(WRITE),'public_ingress':[],'service_bind':'127.0.0.1:8786','id':uuid.uuid4().hex,'evidence':{},'reviewed':False}
 state.write('deployment-plan.json',sign(state,p));return p

def review(state,input_fn=input):
 p=verify(state,state.read('deployment-plan.json'),allow_expired=True)
 p['expires']=(now()+datetime.timedelta(minutes=30)).isoformat();p['reviewed']=False;p['evidence']={}
 print('請在控制台核對本計畫；證據只保存在您的Cloud Shell，勿傳聊天。')
 # Full context and exact resource configuration are only in this private file.
 state.write('console-review-private.json',{'plan':p,'requirements':CATEGORIES})
 for key,requirement in CATEGORIES.items():
  print(requirement)
  name=input_fn('上傳證據檔後，輸入檔名（HOME內PNG/JPEG/PDF原件；空白即停止）：').strip();path=Path.home()/name
  if not name or Path(name).name!=name or path.is_symlink() or not path.is_file():raise l.Refused('CONSOLE_EVIDENCE_REQUIRED')
  raw=path.read_bytes()
  if not 128<=len(raw)<=8*1024*1024 or not (raw.startswith(b'\x89PNG\r\n\x1a\n') or raw.startswith(b'%PDF-') or raw.startswith(b'\xff\xd8\xff')):raise l.Refused('ORIGINAL_CONSOLE_PNG_JPEG_PDF_REQUIRED')
  if input_fn('本人已視讀該原件，確認適用私有計畫內全部候選配置且不是試用抵扣；輸入「已核對」：')!='已核對':raise l.Refused('OWNER_REVIEW_REQUIRED')
  # Review is a documented human observation, never represented as API verification.
  target='evidence-'+l.sha(raw)+path.suffix;dest=state.path/target
  if not dest.exists():
   fd=os.open(dest,os.O_WRONLY|os.O_CREAT|os.O_EXCL,0o600)
   with os.fdopen(fd,'wb') as f:f.write(raw)
  p['evidence'][key]={'path':target,'sha256':l.sha(raw),'bytes':len(raw),'observed_at':now().isoformat(),'source':'OWNER_CONSOLE_REVIEW_NOT_API','plan_binding':digest({k:v for k,v in p.items() if k not in ('evidence','reviewed')})}
 p['reviewed']=True;state.write('deployment-plan.json',sign(state,p));return p

def evidence(state,p):
 if not p.get('reviewed') or set(p['evidence'])!=set(CATEGORIES):raise l.Refused('FREE_PROOFS_MISSING')
 bound=digest({k:v for k,v in p.items() if k not in ('evidence','reviewed')})
 for e in p['evidence'].values():
  q=state.path/e['path']
  if q.is_symlink() or not q.is_file() or q.stat().st_size!=e['bytes'] or l.sha(q.read_bytes())!=e['sha256'] or e['plan_binding']!=bound:raise l.Refused('FREE_PROOF_CHANGED')

def free_allocation(s,choice):
 # Service quota may exceed Always Free. Count allocated stopped instances too.
 live=[x for x in s['instances'] if x.get('lifecycle-state') not in ('TERMINATED','DELETED')]
 shape=choice['shape'];same=[x for x in live if x.get('shape')==shape]
 if any(not x.get('shape') for x in live):raise l.Refused('FREE_COMPUTE_USAGE_UNKNOWN')
 if shape=='VM.Standard.E2.1.Micro':
  if len(same)+1>2:raise l.Refused('ALWAYS_FREE_COMPUTE_EXHAUSTED')
  return {'existing_instances':len(same),'maximum_instances':2}
 if shape!='VM.Standard.A1.Flex':raise l.Refused('NOT_ALLOWED_FREE_SHAPE')
 cpu=decimal.Decimal(0);ram=decimal.Decimal(0)
 for x in same:
  cfg=x.get('shape-config') or {}
  try:
   c=decimal.Decimal(str(cfg['ocpus']));m=decimal.Decimal(str(cfg['memory-in-gbs']))
   if not c.is_finite() or not m.is_finite() or c<=0 or m<=0:raise ValueError()
  except (KeyError,ValueError,decimal.InvalidOperation):raise l.Refused('FREE_COMPUTE_USAGE_UNKNOWN')
  cpu+=c;ram+=m
 if cpu+decimal.Decimal(str(choice['ocpus']))>4 or ram+decimal.Decimal(str(choice['ram_gb']))>24:raise l.Refused('ALWAYS_FREE_COMPUTE_EXHAUSTED')
 return {'existing_ocpus':str(cpu),'existing_ram_gb':str(ram),'maximum_ocpus':4,'maximum_ram_gb':24,'monthly_allowance':'REQUIRES_OWNER_CONSOLE_EVIDENCE'}

def quota_check(cloud,p,choice):
 names=choice['quota_names']
 if not names:raise l.Refused('COMPUTE_QUOTA_NAMES_UNKNOWN')
 for name in names:
  args={'compartment-id':cloud.ctx['tenancy'],'service-name':'compute','limit-name':name,'availability-domain':choice['ad']}
  result=cloud.read(('limits','resource-availability','get'),args)
  needed=choice['ram_gb'] if 'memory' in name else choice['ocpus'] if 'core' in name else 1
  if type(result.get('available')) not in (int,float) or result['available']<needed:raise l.Refused('SERVICE_QUOTA_INSUFFICIENT')

def capacity(cloud,p):
 for candidate in p['options']:
  try:
   free_allocation(p['snapshot_data'],candidate)
   quota_check(cloud,p,candidate)
   for service,name,needed,scope in [('vcn','vcn-count',1,None),('block-storage','total-storage-gb',50,candidate['ad'])]:
    params={'compartment-id':cloud.ctx['tenancy'],'service-name':service,'limit-name':name}
    if scope:params['availability-domain']=scope
    avail=cloud.read(('limits','resource-availability','get'),params)
    if type(avail.get('available')) not in (int,float) or avail['available']<needed:raise l.Refused('SERVICE_QUOTA_INSUFFICIENT')
  except l.Refused as e:
   if str(e) in ('SERVICE_QUOTA_INSUFFICIENT','ALWAYS_FREE_COMPUTE_EXHAUSTED'):continue
   raise
  shape={'instanceShape':candidate['shape']}
  if candidate['shape']=='VM.Standard.A1.Flex':shape['instanceShapeConfig']={'ocpus':1,'memoryInGBs':6}
  # This non-persistent diagnostic POST is ONLY in apply, after all cost proofs.
  r=cloud.call(('compute','compute-capacity-report','create'),{'compartment-id':cloud.ctx['tenancy'],'availability-domain':candidate['ad'],'shape-availabilities':[shape]})
  rows=r.get('shape-availabilities',[])
  if any(x.get('instance-shape')==candidate['shape'] and x.get('availability-status')=='AVAILABLE' for x in rows):return candidate
 raise l.Refused('ALWAYS_FREE_CAPACITY_UNAVAILABLE_NO_PAID_FALLBACK')

def guest(p,owner_auth,console_hash):
 # Reuse exact fixed pilot validator; guest extraction only after full verification.
 validator='\n'.join([inspect.getsource(l.Refused),inspect.getsource(l.sha),inspect.getsource(l.strict_object),inspect.getsource(l.validate_zip)])
 installer="import io,zipfile,json,hashlib,re,stat,unicodedata,urllib.request,os\nfrom pathlib import Path\n"+f"PILOT_BYTES={l.PILOT_BYTES!r}\nPILOT_SHA={l.PILOT_SHA!r}\nPILOT_MANIFEST_SHA={l.PILOT_MANIFEST_SHA!r}\nPILOT_COMMIT={l.PILOT_COMMIT!r}\n"+validator+f"\nurl={l.PILOT_URL!r}\nclass NoRedirect(urllib.request.HTTPRedirectHandler):\n def redirect_request(self,*a,**kw):return None\nwith urllib.request.build_opener(NoRedirect()).open(url,timeout=30) as r:\n if r.status!=200:raise ValueError('HTTP')\n raw=r.read(PILOT_BYTES+1)\nvalidate_zip(raw)\nroot=Path('/opt/twstockai-pilot/bundle');root.mkdir(mode=0o755,exist_ok=False)\nwith zipfile.ZipFile(io.BytesIO(raw)) as z:\n for f in z.infolist():\n  q=root/f.filename;q.parent.mkdir(parents=True,exist_ok=True);q.write_bytes(z.read(f))\n"
 runner="import runpy,sys\nfrom pathlib import Path\np=Path('/opt/twstockai-pilot/private-host')\nsys.argv=['serve.py','serve','--bundle','/opt/twstockai-pilot/bundle','--credentials','/opt/twstockai-pilot/owner.json','--port','8786']\nif p.exists():sys.argv+=['--private-host',p.read_text().strip()]\nsys.path.insert(0,'/opt/twstockai-pilot/bundle');runpy.run_path('/opt/twstockai-pilot/bundle/serve.py',run_name='__main__')\n"
 unit='[Unit]\nAfter=network-online.target\nWants=network-online.target\n[Service]\nUser=pilot\nExecStart=/usr/bin/python3 /opt/twstockai-pilot/run.py\nRestart=on-failure\nNoNewPrivileges=yes\nProtectSystem=strict\nProtectHome=yes\nPrivateTmp=yes\nMemoryMax=256M\n[Install]\nWantedBy=multi-user.target\n'
 files=[('/opt/twstockai-pilot/install.py',installer,'root:root','0600'),('/opt/twstockai-pilot/run.py',runner,'root:root','0644'),('/opt/twstockai-pilot/owner.json',json.dumps(owner_auth),'pilot:pilot','0600'),('/etc/systemd/system/twstockai-pilot.service',unit,'root:root','0644')]
 return '#cloud-config\n'+json.dumps({'users':[{'name':'pilot','sudo':'ALL=(ALL) NOPASSWD:ALL','shell':'/bin/bash','lock_passwd':False,'passwd':console_hash}],'ssh_pwauth':False,'write_files':[{'path':path,'content':body,'owner':owner,'permissions':mode} for path,body,owner,mode in files],'runcmd':[['python3','/opt/twstockai-pilot/install.py'],['systemctl','daemon-reload'],['systemctl','enable','--now','twstockai-pilot.service']]})

class Provisioner:
 def __init__(self,state,cloud,plan):self.state=state;self.cloud=cloud;self.p=plan;self.file='resources-'+plan['id']+'.json';self.log=state.read(self.file) if (state.path/self.file).exists() else {'plan':plan['id'],'context':plan['context'],'steps':{},'complete':False}
 def step(self,name,params,compartment):
  entry=self.log['steps'].get(name)
  if entry and entry.get('status')=='DONE':return entry['id']
  # Find only this exact plan's owned resources, never an unrelated same name.
  found=self.cloud.read(LIST[name],{'compartment-id':compartment,'all':True})
  matches=[x for x in found if x.get('freeform-tags',{}).get('TwstockaiPilotPlan')==self.p['id'] and x.get('lifecycle-state') not in ('TERMINATED','DELETED')]
  if len(matches)>1:raise l.Refused('AMBIGUOUS_OWNED_RESOURCES')
  if matches:resource=matches[0]
  elif entry:raise l.Refused('PRIOR_CREATE_OUTCOME_UNKNOWN_DO_NOT_RETRY')
  else:
   params={**params,'display-name':'twstockai-pilot-'+name+'-'+self.p['id'][:8],'freeform-tags':{'TwstockaiPilotPlan':self.p['id']}}
   if name=='compartment':params.pop('display-name',None)
   self.log['steps'][name]={'status':'STARTED','at':now().isoformat()};self.state.write(self.file,self.log)
   resource=self.cloud.call(WRITE[name],params)
  if resource.get('freeform-tags',{}).get('TwstockaiPilotPlan')!=self.p['id'] or not resource.get('id'):raise l.Refused('RESOURCE_OWNERSHIP_UNPROVEN')
  self.log['steps'][name]={'status':'DONE','id':resource['id']};self.state.write(self.file,self.log);return resource['id']
 def deploy(self,choice,user_data):
  tenancy=self.p['context']['tenancy'];comp=self.step('compartment',{'compartment-id':tenancy,'name':'twstockai-pilot-'+self.p['id'][:8],'description':'Isolated synthetic Always Free pilot'},tenancy)
  # Bounded readonly propagation wait. No retry of resource creations.
  ready=False
  for _ in range(12):
   try:self.cloud.read(('iam','compartment','get'),{'compartment-id':comp});ready=True;break
   except l.Refused:time.sleep(5)
  if not ready:raise l.Refused('COMPARTMENT_PROPAGATION_PENDING_RESUME_LATER')
  vcn=self.step('vcn',{'compartment-id':comp,'cidr-block':'10.78.0.0/24'},comp)
  gw=self.step('gateway',{'compartment-id':comp,'vcn-id':vcn,'is-enabled':True},comp)
  rt=self.step('routes',{'compartment-id':comp,'vcn-id':vcn,'route-rules':[{'destination':'0.0.0.0/0','destinationType':'CIDR_BLOCK','networkEntityId':gw}]},comp)
  sl=self.step('security',{'compartment-id':comp,'vcn-id':vcn,'ingress-security-rules':[],'egress-security-rules':[{'destination':'0.0.0.0/0','protocol':'6','tcpOptions':{'destinationPortRange':{'min':443,'max':443}}},{'destination':'0.0.0.0/0','protocol':'17','udpOptions':{'destinationPortRange':{'min':53,'max':53}}}]},comp)
  subnet=self.step('subnet',{'compartment-id':comp,'vcn-id':vcn,'cidr-block':'10.78.0.0/28','route-table-id':rt,'security-list-ids':[sl],'prohibit-public-ip-on-vnic':False},comp)
  args={'compartment-id':comp,'availability-domain':choice['ad'],'shape':choice['shape'],'source-details':{'sourceType':'image','imageId':choice['image'],'bootVolumeSizeInGBs':50,'bootVolumeVpusPerGB':10},'subnet-id':subnet,'assign-public-ip':True,'metadata':{'user_data':base64.b64encode(user_data.encode()).decode()}}
  if choice['shape']=='VM.Standard.A1.Flex':args['shape-config']={'ocpus':1,'memoryInGBs':6}
  if len(user_data.encode())>32000:raise l.Refused('GUEST_METADATA_SIZE_BOUND')
  self.step('instance',args,comp);self.log['complete']=True;self.log['guest_health']='NOT_VERIFIED';self.state.write(self.file,self.log)
  return self.log

def apply(state,cloud,auth=None,console_hash=None):
 p=verify(state,state.read('deployment-plan.json'));evidence(state,p)
 if cloud.ctx!=p['context']:raise l.Refused('ACCOUNT_OR_REGION_CHANGED')
 existing=state.path/('resources-'+p['id']+'.json')
 if existing.exists():
  ledger=state.read(existing.name)
  if ledger.get('context')!=cloud.ctx:raise l.Refused('ACCOUNT_CHANGED')
  # Resume must recheck ownership, but own resources change inventory naturally.
  for kind,row in ledger['steps'].items():
   if row['status']=='DONE':
    resource=cloud.read(('iam','compartment','get') if kind=='compartment' else ('compute','instance','get') if kind=='instance' else ('network',{'gateway':'internet-gateway','routes':'route-table','security':'security-list'}.get(kind,kind),'get'),{('instance-id' if kind=='instance' else 'compartment-id' if kind=='compartment' else {'gateway':'ig-id','routes':'rt-id','security':'security-list-id','subnet':'subnet-id','vcn':'vcn-id'}[kind]):row['id']})
    if resource.get('freeform-tags',{}).get('TwstockaiPilotPlan')!=p['id']:raise l.Refused('OWNERSHIP_CHANGED')
    if kind=='security' and resource.get('ingress-security-rules')!=[]:raise l.Refused('OWNED_NETWORK_SECURITY_CHANGED')
  if ledger.get('complete'):return ledger
  fresh=snapshot(cloud)
  if fresh['errors']:raise l.Refused('INVENTORY_PARTIAL')
  for key in ('instances','boots','volumes'):
   foreign=[x for x in fresh[key] if x.get('freeform-tags',{}).get('TwstockaiPilotPlan')!=p['id']]
   if digest(sorted(foreign,key=lambda x:x['id']))!=digest(sorted(p['snapshot_data'][key],key=lambda x:x['id'])):raise l.Refused('FOREIGN_RESOURCES_CHANGED_REVIEW_REQUIRED')
  choice=state.read('chosen.json');quota_check(cloud,p,choice)
  secrets_saved=state.read('guest-auth-private.json')
  return Provisioner(state,cloud,p).deploy(choice,guest(p,secrets_saved['auth'],secrets_saved['console_hash']))
 fresh=snapshot(cloud)
 if binding(fresh)!=p['snapshot']:raise l.Refused('INVENTORY_OR_QUOTA_CHANGED_REPLAN')
 raw=state.path/l.PILOT_NAME
 l.validate_zip(raw.read_bytes())
 choice=capacity(cloud,p)
 if auth is None or console_hash is None:raise l.Refused('PRIVATE_AUTH_REQUIRED')
 state.write('chosen.json',choice)
 return Provisioner(state,cloud,p).deploy(choice,guest(p,auth,console_hash))

def credentials():
 pw=getpass.getpass('新測試版owner密碼（至少16字，不記錄明文）：')
 if len(pw)<16 or pw!=getpass.getpass('再輸入owner密碼：'):raise l.Refused('OWNER_PASSWORD_INVALID')
 salt=secrets.token_bytes(16);auth={'schema':'mobile-owner-auth/0.1','username':'owner','salt':salt.hex(),'key':hashlib.scrypt(pw.encode(),salt=salt,n=16384,r=8,p=1).hex()}
 pw=getpass.getpass('獨立Oracle序列主控台pilot使用者密碼（至少16字）：')
 if len(pw)<16 or pw!=getpass.getpass('再輸入主控台密碼：'):raise l.Refused('CONSOLE_PASSWORD_INVALID')
 r=subprocess.run(['openssl','passwd','-6','-stdin'],input=(pw+'\n').encode(),capture_output=True)
 if r.returncode or not r.stdout.startswith(b'$6$'):raise l.Refused('PASSWORD_HASH_FAILED')
 return auth,r.stdout.decode().strip()

def main():
 a=argparse.ArgumentParser();a.add_argument('command',choices=['inspect','plan','review','apply','status','stop','connect']);cmd=a.parse_args().command
 try:
  state=l.State(Path.home()/'.local/share/twstockai-oracle-deploy2');cloud=Cloud(l.identity(),state)
  with state.lock():
   if cmd in ('inspect','plan'):
    raw=state.path/l.PILOT_NAME
    if not raw.exists():
     data=l.fixed_download(l.PILOT_URL,l.PILOT_BYTES,l.PILOT_SHA);l.validate_zip(data);raw.write_bytes(data);raw.chmod(0o600)
    p=plan(state,cloud);print('唯讀盤點完成；尚未建立資源。下一步執行review核對控制台證據；計畫30分鐘有效。');return 0
   if cmd=='review':review(state);print('本人證據已綁定計畫；下一步apply將重新查核再嘗試免費容量。');return 0
   p=verify(state,state.read('deployment-plan.json'),allow_expired=cmd in ('status','stop','connect'))
   if cloud.ctx!=p['context']:raise l.Refused('ACCOUNT_OR_REGION_CHANGED')
   path='resources-'+p['id']+'.json'
   if cmd=='apply':
    evidence(state,p)
    if (state.path/'guest-auth-private.json').exists():
     saved=state.read('guest-auth-private.json');auth,ch=saved['auth'],saved['console_hash']
    else:
     auth,ch=credentials();state.write('guest-auth-private.json',{'auth':auth,'console_hash':ch})
    apply(state,cloud,auth,ch);print('資源建立流程完成；guest服務健康待核實，私人HTTPS未啟用。');return 0
   ledger=state.read(path) if (state.path/path).exists() else {'steps':{},'complete':False}
   if cmd=='status':
    row=ledger['steps'].get('instance')
    if row and row['status']=='DONE':
     vm=cloud.read(('compute','instance','get'),{'instance-id':row['id']});print('主機狀態：'+vm.get('lifecycle-state','UNKNOWN')+'；服務健康／HTTPS／Android仍須實測。')
    else:print('本計畫主機尚未完成；已保存步驟數：'+str(len(ledger['steps'])))
    return 0
   if cmd=='stop':
    row=ledger['steps'].get('instance')
    if not row:print('本計畫沒有已核主機。');return 0
    vm=cloud.read(('compute','instance','get'),{'instance-id':row['id']})
    if vm.get('freeform-tags',{}).get('TwstockaiPilotPlan')!=p['id']:raise l.Refused('OWNERSHIP_CHANGED')
    cloud.call(('compute','instance','action'),{'instance-id':row['id'],'action':'SOFTSTOP'});print('僅停止本計畫主機；磁碟保留，不停止其他資源。');return 0
   print('停止於第三方本人登入邊界：先確認Tailscale Personal符合免費用途並同意條款。未替您安裝或接受條款。請依CONSOLE_GUIDE操作獨立VM主控台；禁止Funnel。');return 2
 except l.Refused as e:print('停止：'+e.code+'；既有原件與本計畫資源保留。');return 2
 except Exception:print('停止：回應／狀態無法安全確認；不重送未知建立，請查看本人私有狀態。');return 2
if __name__=='__main__':raise SystemExit(main())
