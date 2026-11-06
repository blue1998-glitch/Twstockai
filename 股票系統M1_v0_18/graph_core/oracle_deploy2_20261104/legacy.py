"""Cloud Shell inspection and fail-closed plan/apply gate. Python stdlib only.
No provisioning backend is enabled: OCI read responses cannot prove every
required zero-charge component or an authorized Personal tailnet in this release.
Never present mock proof as a real Always Free deployment authorization.
"""
import argparse,configparser,contextlib,datetime,fcntl,hashlib,hmac,json,os,re,secrets,shutil,stat,subprocess,sys,time,unicodedata,urllib.request,urllib.error,zipfile,io
from pathlib import Path

VERSION='oracle-shell-safety/0.2'
PILOT_COMMIT='5789d9dafad8fe06ceb0341eb73f7b1004e09b51'
PILOT_BYTES=345616
PILOT_SHA='0c48c1d92a94cfcfc1a88f52c22c97cda0d9f0797a05d0367a32ca1fc4a6e750'
PILOT_MANIFEST_SHA='f8b9938fbecb77cf3e76844d0177e60618a7afd6ced529d02ffc23a2f0e32233'
PILOT_NAME='Twstockai_ORACLE_PILOT1_SYNTHETIC.zip'
PILOT_URL='https://raw.githubusercontent.com/blue1998-glitch/Twstockai/'+PILOT_COMMIT+'/deliveries/m1-oracle-pilot1-20261104/'+PILOT_NAME
TTL=600
MAX_CALLS=80
MAX_COMPARTMENTS=32
MAX_ADS=8
READ_OPS={
 'tenancy':('iam','tenancy','get'),
 'regions':('iam','region-subscription','list'),
 'compartments':('iam','compartment','list'),
 'ads':('iam','availability-domain','list'),
 'instances':('compute','instance','list'),
 'boots':('bv','boot-volume','list'),
 'volumes':('bv','volume','list'),
 'shapes':('compute','shape','list'),
 'images':('compute','image','list'),
 'vcns':('network','vcn','list'),
 'subnets':('network','subnet','list'),
 'public_ips':('network','public-ip','list'),
 'limits':('limits','value','list'),
 'limit_definitions':('limits','definition','list'),
 'availability':('limits','resource-availability','get'),
}
PARAMS={
 'tenancy':{'tenancy-id'},'regions':{'tenancy-id','all'},
 'compartments':{'compartment-id','compartment-id-in-subtree','access-level','all'},
 'ads':{'compartment-id','all'},'instances':{'compartment-id','all'},
 'boots':{'compartment-id','availability-domain','all'},'volumes':{'compartment-id','all'},
 'shapes':{'compartment-id','availability-domain','all'},'images':{'compartment-id','operating-system','all'},
 'vcns':{'compartment-id','all'},'subnets':{'compartment-id','all'},
 'public_ips':{'compartment-id','scope','availability-domain','all'},
 'limits':{'compartment-id','service-name','all'},'limit_definitions':{'compartment-id','service-name','all'},
 'availability':{'compartment-id','service-name','limit-name','availability-domain'},
}
LABELS={
 'ACCOUNT_CONTEXT':'Cloud Shell登入環境', 'TENANCY_HOME':'租戶與Home Region',
 'INVENTORY':'完整資源盤點', 'SHAPE_BILLING':'Compute免費類型',
 'SERVICE_QUOTA':'服務配額與剩餘量', 'FREE_STORAGE':'Always Free儲存餘額',
 'IMAGE_COST':'映像零費用證明', 'NETWORK_COST':'IP與網路零費用證明',
 'ACCOUNT_FREE':'帳戶免費資格與適用條件', 'CAPACITY':'實際主機供應',
 'TAILNET':'私人網路方案與授權', 'PILOT':'固定合成包',
}

class Refused(Exception):
    def __init__(self,code):self.code=code;super().__init__(code)

def encode(v):return (json.dumps(v,ensure_ascii=False,sort_keys=True,separators=(',',':'),allow_nan=False)+'\n').encode()
def sha(raw):return hashlib.sha256(raw).hexdigest()
def utc():return datetime.datetime.now(datetime.timezone.utc)
def stamp():return utc().isoformat()
def strict_object(raw):
    def pairs(rows):
        d={}
        for k,v in rows:
            if k in d:raise Refused('DUPLICATE_JSON_KEY')
            d[k]=v
        return d
    return json.loads(raw,object_pairs_hook=pairs,parse_constant=lambda _:(_ for _ in ()).throw(Refused('NONFINITE_JSON')))

class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self,*a,**kw):return None

def fixed_download(url,size,digest):
    if not url.startswith('https://raw.githubusercontent.com/blue1998-glitch/Twstockai/'):raise Refused('DOWNLOAD_ORIGIN')
    try:
        with urllib.request.build_opener(NoRedirect()).open(urllib.request.Request(url,headers={'User-Agent':'Twstockai-CloudShell/0.1'}),timeout=30) as response:
            if response.status!=200:raise Refused('DOWNLOAD_HTTP')
            raw=response.read(size+1)
    except (urllib.error.URLError,TimeoutError,OSError):raise Refused('DOWNLOAD_UNAVAILABLE_USE_CLOUD_SHELL_UPLOAD')
    if len(raw)!=size or sha(raw)!=digest:raise Refused('DOWNLOAD_SOURCE_SHA')
    return raw

def validate_zip(raw,*,expected_bytes=PILOT_BYTES,expected_sha=PILOT_SHA,manifest_sha=PILOT_MANIFEST_SHA):
    if len(raw)!=expected_bytes or sha(raw)!=expected_sha:raise Refused('ZIP_SOURCE_SHA')
    try:
        with zipfile.ZipFile(io.BytesIO(raw)) as z:
            infos=z.infolist()
            if not 1<=len(infos)<=64:raise Refused('ZIP_COUNT')
            seen=set();total=0;paths=[]
            for f in infos:
                name=f.filename
                if name!=unicodedata.normalize('NFC',name) or not re.fullmatch(r'[A-Za-z0-9_.\-/]+',name) or name.startswith('/') or '\\' in name or any(x in ('','.','..') for x in name.split('/')):raise Refused('ZIP_PATH')
                folded=name.casefold()
                if folded in seen:raise Refused('ZIP_DUPLICATE')
                seen.add(folded);paths.append(name)
                mode=f.external_attr>>16
                if f.is_dir() or (mode and stat.S_IFMT(mode) not in (0,stat.S_IFREG)) or f.flag_bits&1 or f.compress_type not in (zipfile.ZIP_STORED,zipfile.ZIP_DEFLATED):raise Refused('ZIP_MEMBER_TYPE')
                total+=f.file_size
                if f.file_size>2*1024*1024 or total>4*1024*1024:raise Refused('ZIP_SIZE_BOUND')
            if any(any(parent in seen for parent in ['/'.join(n.casefold().split('/')[:i]) for i in range(1,len(n.split('/')))]) for n in paths):raise Refused('ZIP_FILE_DIRECTORY_COLLISION')
            if 'MANIFEST.json' not in paths:raise Refused('ZIP_MANIFEST_MISSING')
            original=z.read('MANIFEST.json')
            if sha(original)!=manifest_sha:raise Refused('ZIP_MANIFEST_SHA')
            m=strict_object(original)
            if m.get('schema')!='synthetic-pilot-manifest/0.1' or m.get('synthetic_only') is not True or m.get('contains_credentials') is not False or m.get('contains_private_market_data') is not False:raise Refused('ZIP_NOT_SYNTHETIC')
            members=m.get('files',[]);declared=[i['path'] for i in members]
            if len(declared)!=len(set(declared)) or set(paths)!=set(declared)|{'MANIFEST.json'}:raise Refused('ZIP_MANIFEST_SET')
            if z.testzip() is not None:raise Refused('ZIP_CRC')
            for f in members:
                data=z.read(f['path'])
                if len(data)!=f['bytes'] or sha(data)!=f['sha256']:raise Refused('ZIP_MEMBER_SHA')
            return {'status':'PASS','bytes':len(raw),'sha256':sha(raw),'manifest_sha256':sha(original),'members':len(paths),'entry':m['entry'],'commit':PILOT_COMMIT}
    except (zipfile.BadZipFile,KeyError,ValueError,TypeError,RuntimeError):raise Refused('ZIP_INVALID')

class State:
    def __init__(self,path):
        path=Path(path).expanduser().absolute()
        if any(p.is_symlink() for p in (path,*path.parents)):raise Refused('STATE_SYMLINK')
        if any((p/'.git').exists() for p in (path,*path.parents)):raise Refused('STATE_MUST_BE_GIT_EXTERNAL')
        path.mkdir(mode=0o700,parents=True,exist_ok=True)
        if path.stat().st_uid!=os.getuid() or stat.S_IMODE(path.stat().st_mode)&0o077:raise Refused('STATE_NOT_PRIVATE')
        self.path=path
        key=path/'plan-key.bin'
        if not key.exists():
            fd=os.open(key,os.O_WRONLY|os.O_CREAT|os.O_EXCL,0o600)
            with os.fdopen(fd,'wb') as f:f.write(secrets.token_bytes(32))
        if key.is_symlink() or stat.S_IMODE(key.stat().st_mode)&0o077 or len(key.read_bytes())!=32:raise Refused('STATE_KEY_INVALID')
        self.key=key.read_bytes()
    def write(self,name,value):
        if not re.fullmatch(r'[A-Za-z0-9_.-]+',name):raise Refused('STATE_FILENAME')
        raw=encode(value);p=self.path/name
        if len(raw)>16*1024*1024 or sum(x.stat().st_size for x in self.path.iterdir() if x.is_file() and not x.is_symlink())+len(raw)>32*1024*1024 or shutil.disk_usage(self.path).free<len(raw)+16*1024*1024:raise Refused('PRIVATE_STATE_CAPACITY_BOUND')
        if p.is_symlink():raise Refused('STATE_SYMLINK')
        temp=self.path/('.new-'+secrets.token_hex(10));fd=os.open(temp,os.O_WRONLY|os.O_CREAT|os.O_EXCL,0o600)
        with os.fdopen(fd,'wb') as f:f.write(raw);f.flush();os.fsync(f.fileno())
        os.replace(temp,p)
    def read(self,name):
        p=self.path/name
        if p.is_symlink() or stat.S_IMODE(p.stat().st_mode)&0o077:raise Refused('STATE_NOT_PRIVATE')
        return strict_object(p.read_bytes())
    def record(self,kind,value):
        ident=sha(encode(value));name=kind+'-'+ident+'.json';p=self.path/name
        if p.exists():
            if p.read_bytes()!=encode(value):raise Refused('IMMUTABLE_REPORT_CONFLICT')
        else:self.write(name,value)
        self.write('latest-'+kind+'.json',{'file':name,'sha256':ident})
        return name
    def latest(self,kind):
        ref=self.read('latest-'+kind+'.json');name=ref['file']
        if not re.fullmatch(kind+r'-[a-f0-9]{64}\.json',name):raise Refused('REPORT_BINDING')
        value=self.read(name)
        if sha(encode(value))!=ref['sha256']:raise Refused('REPORT_BINDING')
        return value
    @contextlib.contextmanager
    def lock(self):
        p=self.path/'run.lock'
        if p.is_symlink():raise Refused('STATE_SYMLINK')
        fd=os.open(p,os.O_RDWR|os.O_CREAT,0o600)
        try:
            try:fcntl.flock(fd,fcntl.LOCK_EX|fcntl.LOCK_NB)
            except BlockingIOError:raise Refused('ANOTHER_SHELL_TOOL_RUNNING')
            yield
        finally:os.close(fd)

def identity(env=None):
    env=os.environ if env is None else env
    tenancy=env.get('OCI_TENANCY','');region=env.get('OCI_REGION') or env.get('OCI_CLI_REGION','')
    # Read only official CLI config metadata, never any token or key_file bytes.
    if not tenancy or not region:
        cfg=Path(env.get('OCI_CLI_CONFIG_FILE') or str(Path.home()/'.oci/config'))
        if cfg.is_file() and not cfg.is_symlink():
            c=configparser.ConfigParser(interpolation=None)
            try:
                c.read(cfg);profile=env.get('OCI_CLI_PROFILE','DEFAULT');section=c[profile];tenancy=tenancy or section.get('tenancy','');region=region or section.get('region','')
            except (configparser.Error,KeyError,OSError):pass
    if not re.fullmatch(r'ocid1\.tenancy\.[a-zA-Z0-9._-]+',tenancy) or not re.fullmatch(r'[a-z][a-z0-9-]{2,63}',region):raise Refused('CLOUD_SHELL_IDENTITY_UNAVAILABLE')
    return {'tenancy':tenancy,'region':region}

class OCI:
    def __init__(self,context,runner=subprocess.run,executable=None):
        self.context=context;self.runner=runner;self.executable=executable or shutil.which('oci');self.calls=[];self.started=time.monotonic()
        if not self.executable:raise Refused('OCI_CLI_NOT_AVAILABLE')
    def read(self,op,params):
        if op not in READ_OPS:raise Refused('OCI_MUTATION_NOT_ALLOWED')
        if set(params)-PARAMS[op]:raise Refused('OCI_ARGUMENT_NOT_ALLOWED')
        if len(self.calls)>=MAX_CALLS or time.monotonic()-self.started>180:raise Refused('INSPECTION_BOUND_REACHED')
        args=[self.executable,*READ_OPS[op]]
        for k,v in params.items():
            if not re.fullmatch(r'[a-z][a-z-]+',k):raise Refused('OCI_ARGUMENT')
            if k=='all' and v is False:continue
            if k=='all' and v is not True:raise Refused('OCI_ARGUMENT')
            args.append('--'+k)
            if type(v) is bool and k!='all':
                args.append('true' if v else 'false')
            elif v is not True:
                text=str(v)
                if text.startswith('-') or any(ord(c)<32 for c in text):raise Refused('OCI_ARGUMENT')
                args.append(text)
        args+=['--region',self.context['region'],'--output','json','--max-retries','0']
        self.calls.append({'operation':op,'mutation':False})
        try:r=self.runner(args,stdout=subprocess.PIPE,stderr=subprocess.PIPE,timeout=25,check=False)
        except (OSError,subprocess.TimeoutExpired):raise Refused('OCI_READ_TRANSPORT_OR_TIMEOUT')
        if r.returncode:
            # Never echo arbitrary CLI stderr/argv/account identifiers or auth tokens.
            error=r.stderr.decode(errors='replace') if isinstance(r.stderr,bytes) else str(r.stderr)
            code='OCI_PERMISSION_DENIED' if re.search(r'NotAuthorized|Forbidden|\b403\b|\b401\b',error,re.I) else 'OCI_READ_FAILED'
            if re.search(r'requires an argument|no such option|no such command|missing option|invalid value for',error,re.I):code='OCI_CLI_ARGUMENT_ERROR'
            raise Refused(code)
        if len(r.stdout)>2*1024*1024:raise Refused('OCI_RESPONSE_BOUND')
        try:value=strict_object(r.stdout)
        except (ValueError,TypeError):raise Refused('OCI_INVALID_JSON')
        if not isinstance(value,dict) or 'data' not in value:raise Refused('OCI_SCHEMA')
        data=value['data']
        if op in ('tenancy','availability'):
            if not isinstance(data,dict):raise Refused('OCI_SCHEMA')
        elif not isinstance(data,list) or any(not isinstance(row,dict) for row in data):raise Refused('OCI_SCHEMA')
        # --all CLI must return a complete response; never silently ignore next page.
        if value.get('opc-next-page') or value.get('next-page'):raise Refused('OCI_INCOMPLETE_PAGE')
        return value['data']

def check(status,reason,evidence=None):return {'status':status,'reason':reason,'evidence':evidence}
def inventory(client):
    ctx=client.context;now=stamp();raw={};errors=[];gates={k:check('UNKNOWN','未取得足夠官方證據') for k in LABELS}
    gates['ACCOUNT_CONTEXT']=check('PASS','使用既有官方OCI CLI身分；未要求密碼或私鑰')
    def read(op,params):
        try:
            data=client.read(op,params)
            if sum(len(encode(v)) for v in raw.values())+len(encode(data))>12*1024*1024:raise Refused('PRIVATE_REPORT_SIZE_BOUND')
            raw.setdefault(op,[]).append(data);return data
        except Refused as e:errors.append({'operation':op,'code':e.code});return None
    t=read('tenancy',{'tenancy-id':ctx['tenancy']});regions=read('regions',{'tenancy-id':ctx['tenancy'],'all':True})
    home=[x for x in regions or [] if x.get('is-home-region') is True]
    if not t or t.get('id')!=ctx['tenancy'] or len(home)!=1:gates['TENANCY_HOME']=check('UNKNOWN','租戶或Home Region無法核實')
    elif home[0].get('region-name')!=ctx['region']:gates['TENANCY_HOME']=check('FAIL','目前不是實際Home Region；不自動跨區建機')
    else:gates['TENANCY_HOME']=check('PASS','官方租戶與Home Region相符')
    comps=read('compartments',{'compartment-id':ctx['tenancy'],'compartment-id-in-subtree':True,'access-level':'ANY','all':True});ads=read('ads',{'compartment-id':ctx['tenancy'],'all':True})
    active=[x for x in comps or [] if x.get('lifecycle-state')=='ACTIVE'];all_comps=[{'id':ctx['tenancy']},*active]
    complete=comps is not None and ads is not None and len(active)<MAX_COMPARTMENTS and 0<len(ads)<=MAX_ADS and all(c.get('is-accessible') is True for c in active)
    instances=[];boots=[];volumes=[];network=[]
    if complete and gates['TENANCY_HOME']['status']=='PASS':
        for comp in all_comps:
            cid=comp['id']
            for op,target in [('instances',instances),('volumes',volumes),('vcns',network),('subnets',network)]:
                values=read(op,{'compartment-id':cid,'all':True})
                if values is None:complete=False
                elif isinstance(values,list):target.extend(values)
                else:complete=False
            for ad in ads:
                values=read('boots',{'compartment-id':cid,'availability-domain':ad['name'],'all':True})
                if values is None:complete=False
                elif isinstance(values,list):boots.extend(values)
                else:complete=False
            for scope,adname in [('REGION',None)]+[('AVAILABILITY_DOMAIN',a['name']) for a in ads]:
                params={'compartment-id':cid,'scope':scope,'all':True}
                if adname:params['availability-domain']=adname
                ips=read('public_ips',params)
                if ips is None:complete=False
                else:network.extend(ips)
    else:complete=False
    # Preserve all actual read responses privately. Missing access never means zero.
    live=lambda rows:[x for x in rows if x.get('lifecycle-state') not in ['TERMINATED','DELETED']]
    shapes=[];images=[];selected=None
    if gates['TENANCY_HOME']['status']=='PASS' and ads and len(ads)<=MAX_ADS:
        for ad in ads:
            values=read('shapes',{'compartment-id':ctx['tenancy'],'availability-domain':ad['name'],'all':True})
            if isinstance(values,list):
                shapes.extend(values)
                eligible=[x for x in values if x.get('shape') in ['VM.Standard.A1.Flex','VM.Standard.E2.1.Micro'] and x.get('billing-type')=='ALWAYS_FREE']
                eligible.sort(key=lambda x:(x['shape']!='VM.Standard.A1.Flex',x['shape']))
                if selected is None and eligible:selected={'shape':eligible[0]['shape'],'availability_domain':ad['name'],'billing_type':'ALWAYS_FREE','ocpus':1,'memory_gb':6 if eligible[0]['shape']=='VM.Standard.A1.Flex' else 1,'quota_names':eligible[0].get('quota-names',[])}
        images=read('images',{'compartment-id':ctx['tenancy'],'operating-system':'Oracle Linux','all':True}) or []
    if selected:gates['SHAPE_BILLING']=check('PASS','帳戶範圍官方Shape.billing-type=ALWAYS_FREE；不是試用額度',selected)
    elif shapes:gates['SHAPE_BILLING']=check('UNKNOWN','沒有已證ALWAYS_FREE機型；LIMITED_FREE／PAID不代替免費證明')
    limits={};availability={}
    for service in ['compute','block-storage','vcn']:
        values=read('limits',{'compartment-id':ctx['tenancy'],'service-name':service,'all':True});definitions=read('limit_definitions',{'compartment-id':ctx['tenancy'],'service-name':service,'all':True});limits[service]=values
        if isinstance(definitions,list):
            chosen=[x for x in definitions if x.get('is-resource-availability-supported') is True and any(k in x.get('name','') for k in ['a1','e2','storage-gb','vcn-count'])]
            for definition in chosen[:8]:
                params={'compartment-id':ctx['tenancy'],'service-name':service,'limit-name':definition['name']}
                scopes=[None] if definition.get('scope-type')!='AD' else [x['name'] for x in ads or []]
                for scope in scopes:
                    if scope:params['availability-domain']=scope
                    else:params.pop('availability-domain',None)
                    value=read('availability',params);availability[service+'|'+definition['name']+'|'+str(scope)]=value
    gates['INVENTORY']=check('PASS' if complete else 'UNKNOWN','根與已發現可存取compartment讀取完成；不證無隱藏資源' if complete else '範圍、權限、頁碼或請求上限不完整，不能當無資源')
    relevant=[v for k,v in availability.items() if selected and any('|'+n+'|' in k for n in selected['quota_names']) and (k.endswith('|None') or k.endswith('|'+selected['availability_domain']))]
    if relevant and all(isinstance(v,dict) and isinstance(v.get('available'),(int,float)) and not isinstance(v.get('available'),bool) for v in relevant):
        gates['SERVICE_QUOTA']=check('FAIL' if any(v['available']<1 for v in relevant) else 'UNKNOWN','所選機型官方配額不足' if any(v['available']<1 for v in relevant) else 'Compute有可用服務配額；完整儲存／網路需求與免費餘額尚未認證')
    gates['FREE_STORAGE']=check('UNKNOWN','已列實際Boot／Block；服務配額與目前GB不等Always Free授權餘額')
    gates['IMAGE_COST']=check('UNKNOWN','Oracle Linux／BASE身分不直接證明映像零計費')
    gates['NETWORK_COST']=check('UNKNOWN','VCN／IP清單不證全部必要網路元件零費用')
    gates['ACCOUNT_FREE']=check('UNKNOWN','IAM租戶與Shape免費類型不等整個配置的帳戶免費資格')
    gates['CAPACITY']=check('UNKNOWN','形狀清單不是實際供應；inspect／plan禁止CreateComputeCapacityReport')
    gates['TAILNET']=check('UNKNOWN','尚未取得Personal免費方案、本人同意與最小ACL證據；未啟動登入或Funnel')
    totals={'compartments':len(all_comps) if comps is not None else None,'availability_domains':len(ads) if ads is not None else None,'instances':len(live(instances)) if complete else None,'boot_volumes':len(live(boots)) if complete else None,'block_volumes':len(live(volumes)) if complete else None,'volume_gb_observed':sum(x.get('size-in-gbs',0) for x in live(boots+volumes)) if complete and all(isinstance(x.get('size-in-gbs'),int) for x in live(boots+volumes)) else None,'oracle_images_observed':len(images)}
    return {'schema':'oracle-shell-inspection/0.1','version':VERSION,'observed_at':now,'context':ctx,'gates':gates,'totals':totals,'selected':selected,'observations':raw,'errors':errors,'oracle_read_calls':len(client.calls),'oracle_mutation_calls':0,'created_resources':[],'whole_account_coverage':'UNKNOWN_UNDISCOVERED_OR_INACCESSIBLE_RESOURCES_NOT_EXCLUDED'}

def save_inspection(state,client=None,context=None,package=None):
    try:
        context=context or identity();client=client or OCI(context);value=inventory(client)
    except Refused as e:
        value={'schema':'oracle-shell-inspection/0.1','version':VERSION,'observed_at':stamp(),'context':context,'gates':{k:check('UNKNOWN',e.code) for k in LABELS},'totals':{},'selected':None,'observations':{},'errors':[{'code':e.code}],'oracle_read_calls':len(client.calls) if client else 0,'oracle_mutation_calls':0,'created_resources':[],'whole_account_coverage':'UNKNOWN_UNDISCOVERED_OR_INACCESSIBLE_RESOURCES_NOT_EXCLUDED'}
    try:
        raw=package
        if raw is None:
            cached=state.path/PILOT_NAME;upload=Path.home()/PILOT_NAME
            if cached.is_symlink() or upload.is_symlink():raise Refused('PILOT_SYMLINK')
            raw=cached.read_bytes() if cached.exists() and not cached.is_symlink() else upload.read_bytes() if upload.is_file() and not upload.is_symlink() else fixed_download(PILOT_URL,PILOT_BYTES,PILOT_SHA)
        receipt=validate_zip(raw);value['gates']['PILOT']=check('PASS','完整固定提交／bytes／SHA／CRC／manifest與全成員已核',receipt)
        cached=state.path/PILOT_NAME
        if not cached.exists():
            fd=os.open(cached,os.O_WRONLY|os.O_CREAT|os.O_EXCL,0o600)
            with os.fdopen(fd,'wb') as f:f.write(raw)
    except (Refused,OSError) as e:value['gates']['PILOT']=check('FAIL',e.code if isinstance(e,Refused) else 'PILOT_FILE_UNAVAILABLE')
    state.record('inspection',value);return value

def running_digest():
    path=Path(sys.argv[0])
    return sha(path.read_bytes()) if path.is_file() else sha(Path(__file__).read_bytes())

def inspection_binding(value):
    return sha(encode({k:value.get(k) for k in ['context','gates','totals','selected','observations']}))

def make_plan(state,inspection,now=None,tool_digest=None):
    now=now or utc();age=now-datetime.datetime.fromisoformat(inspection['observed_at'])
    if age.total_seconds()<0 or age.total_seconds()>TTL:raise Refused('INSPECTION_STALE')
    blocking=[k for k,v in inspection['gates'].items() if v['status']!='PASS']
    value={'schema':'oracle-shell-plan/0.1','version':VERSION,'created_at':now.isoformat(),'expires_at':(now+datetime.timedelta(seconds=TTL)).isoformat(),'tool_sha256':tool_digest or running_digest(),'inspection_sha256':sha(encode(inspection)),'inspection_binding_sha256':inspection_binding(inspection),'context':inspection['context'],'gates':inspection['gates'],'blocking':blocking,'status':'BLOCKED' if blocking else 'QUALIFIED_NOT_DEPLOYED','deployment_backend':'NOT_ENABLED_UNTIL_ALL_REQUIRED_OFFICIAL_PROOFS_HAVE_SUPPORTED_READERS','resources_to_create':[],'proposal':{'isolated_compartment':True,'shape':inspection.get('selected'),'boot_gb':50,'listener':'127.0.0.1:8786','public_ingress':[],'private_https':'TAILSCALE_SERVE_ONLY_NOT_AUTHORIZED_YET','data':'PINNED_SYNTHETIC_PILOT_ONLY'},'pilot':{'commit':PILOT_COMMIT,'bytes':PILOT_BYTES,'sha256':PILOT_SHA},'oracle_mutation_calls':0}
    value['plan_id']=sha(encode(value));signed={'plan':value,'hmac':hmac.new(state.key,encode(value),hashlib.sha256).hexdigest()};state.record('plan',signed);return signed

def verify_plan(state,signed,now=None,tool_digest=None):
    value=signed.get('plan',{});mac=hmac.new(state.key,encode(value),hashlib.sha256).hexdigest()
    if not hmac.compare_digest(mac,str(signed.get('hmac',''))):raise Refused('PLAN_TAMPERED')
    now=now or utc()
    if value.get('version')!=VERSION or value.get('tool_sha256')!=(tool_digest or running_digest()):raise Refused('PLAN_VERSION_OR_TOOL_CHANGED')
    if now<datetime.datetime.fromisoformat(value['created_at']) or now>=datetime.datetime.fromisoformat(value['expires_at']):raise Refused('PLAN_EXPIRED')
    baseline=dict(value);ident=baseline.pop('plan_id')
    if ident!=sha(encode(baseline)):raise Refused('PLAN_ID_CHANGED')
    if value['pilot']!={'commit':PILOT_COMMIT,'bytes':PILOT_BYTES,'sha256':PILOT_SHA}:raise Refused('PLAN_PILOT_CHANGED')
    return value

def apply(state,context=None,client=None,now=None,tool_digest=None):
    value=verify_plan(state,state.latest('plan'),now=now,tool_digest=tool_digest)
    context=context or identity()
    if context!=value['context']:raise Refused('PLAN_ACCOUNT_OR_REGION_CHANGED')
    # Refresh actual readonly facts before even considering an apply.
    refreshed=save_inspection(state,client=client,context=context)
    if refreshed['context']!=value['context']:raise Refused('PLAN_ACCOUNT_OR_REGION_CHANGED')
    if inspection_binding(refreshed)!=value['inspection_binding_sha256']:raise Refused('PLAN_SOURCE_OR_QUOTA_CHANGED')
    blocked=[k for k in LABELS if refreshed['gates'][k]['status']!='PASS']
    if blocked or value['status']!='QUALIFIED_NOT_DEPLOYED':raise Refused('APPLY_BLOCKED_REQUIRED_PROOFS_UNKNOWN_OR_FAILED')
    # No permissive fallback, user --force, hand-edited proof, or unimplemented
    # image/network billing assumptions. This release cannot provision resources.
    # A real successful deployment path is explicitly NOT IMPLEMENTED, not mocked.
    raise Refused('DEPLOYMENT_BACKEND_NOT_ENABLED')

def report(value):
    gates=value.get('gates',{});blocked=[k for k in LABELS if gates.get(k,{}).get('status')!='PASS'];counts=value.get('totals',{})
    print('本版可唯讀檢查與產生阻塞計畫；建機／私人HTTPS後段尚未實作。')
    print('Twstockai｜'+('停止' if blocked else '檢查完成，尚未部署')+'｜本工具資源建立 0')
    if counts:print('唯讀盤點：Compute '+str(counts.get('instances') if counts.get('instances') is not None else '未知')+'；Boot '+str(counts.get('boot_volumes') if counts.get('boot_volumes') is not None else '未知')+'；Block '+str(counts.get('block_volumes') if counts.get('block_volumes') is not None else '未知'))
    for key in blocked[:7]:print('• '+LABELS[key]+'：'+{'PASS':'已核','FAIL':'不符','UNKNOWN':'尚未核實'}.get(gates.get(key,{}).get('status'),'尚未核實'))
    safe_errors=sorted({(e.get('operation'),e.get('code')) for e in value.get('errors',[]) if e.get('operation') in READ_OPS and e.get('code') in {'OCI_CLI_ARGUMENT_ERROR','OCI_PERMISSION_DENIED','OCI_READ_FAILED','OCI_SCHEMA','OCI_INCOMPLETE_PAGE','OCI_READ_TRANSPORT_OR_TIMEOUT'}})
    for op,code in safe_errors[:5]:print('查詢診斷：'+op+'／'+code)
    if len(blocked)>7:print('• 其他必要條件仍未知；完整明細僅保存在本人Cloud Shell私有目錄')
    print('私人HTTPS未建立；Android實機未驗。不要貼出私有JSON／帳戶識別或憑證。')
    return 2 if blocked else 0

def main(argv=None):
    p=argparse.ArgumentParser(description='Twstockai 官方Cloud Shell唯讀查核與安全部署閘門');p.error=lambda _:sys.exit('停止：指令不合法；僅支援inspect／plan／apply／status／stop');p.add_argument('command',choices=['inspect','plan','apply','status','stop']);args=p.parse_args(argv)
    try:
        state=State(Path.home()/'.local/share/twstockai-oracle-shell1')
        with state.lock():
            if args.command=='inspect':
                value=save_inspection(state);make_plan(state,value);return report(value)
            if args.command=='plan':
                inspection=state.latest('inspection');signed=make_plan(state,inspection);print('部署計畫：'+('停止，必要證據未完整' if signed['plan']['blocking'] else '資格已核，尚未部署')+'｜建立 0');return report(inspection)
            if args.command=='apply':apply(state);return 0
            if args.command=='stop':print('本工具尚未建立任何服務，無需停止；沒有刪除資源或更動原Cloud。');return 0
            try:inspection=state.latest('inspection')
            except FileNotFoundError:print('尚未檢查｜本工具資源建立 0｜私人服務未建立');return 2
            print('狀態只讀上次保存快照，不冒稱即時免費資格。');return report(inspection)
    except Refused as e:
        messages={'CLOUD_SHELL_IDENTITY_UNAVAILABLE':'請在本人已登入的Oracle Cloud Shell執行','OCI_CLI_NOT_AVAILABLE':'未找到官方OCI CLI','PLAN_EXPIRED':'計畫已過期，先重新執行inspect','PLAN_TAMPERED':'計畫遭修改，拒絕執行','APPLY_BLOCKED_REQUIRED_PROOFS_UNKNOWN_OR_FAILED':'必要免費／私人存取證據未核實，拒絕建機','DEPLOYMENT_BACKEND_NOT_ENABLED':'本版本尚未啟用建立資源後段，不會執行Create／Update／Delete'}
        print('停止：'+messages.get(e.code,'安全檢查未通過')+'｜本工具資源建立 0');return 2
    except Exception:
        print('停止：私有狀態或官方回應無法安全核對｜本工具資源建立 0');return 2

if __name__=='__main__':raise SystemExit(main())
