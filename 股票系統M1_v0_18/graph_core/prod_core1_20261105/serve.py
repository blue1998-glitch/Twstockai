"""The SAME owner authentication/listener. Exact allowlists; no public bind."""
import argparse,json,os,signal,subprocess,time
from pathlib import Path
from graph_core.scan1_20261104.provider import Provider as SavedProvider
from graph_core_chart.mobile_private import make_server,batch_index
from graph_core.graph_lazy1_20261104.activate import alive,ready
from graph_core.storage1_20261104.activate import request
from .flow import BASE,WORK,read,encode,sha,put,bound,descriptor,capacity,status,point,release_id
PROJECT=Path(__file__).resolve().parents[2]

class Provider:
    def __init__(self,config,work):
        self.work=Path(work);self.providers=[]
        for d in config['providers']:
            bound(d);self.providers.append(SavedProvider(d['path'],d['sha256']))
        self.route_map={}
        for p in self.providers:
            for route in p.routes():
                if route in self.route_map:raise ValueError('DUPLICATE_PRODUCT_ROUTE')
                self.route_map[route]=p
    def routes(self):return [*self.route_map,'product-status.json']
    def get(self,route,allowed):
        if route=='product-status.json':return encode(status(self.work)),'STATUS'
        return self.route_map[route].get(route,allowed)

def launch(argv,work,label):
    env=dict(os.environ,PYTHONDONTWRITEBYTECODE='1',PYTHONPATH=str(PROJECT)+os.pathsep+str(PROJECT/'src'))
    with (work/(label+'.stdout.log')).open('ab') as out,(work/(label+'.stderr.log')).open('ab') as err:
        return subprocess.Popen(argv,cwd=PROJECT.parent,env=env,stdout=out,stderr=err,start_new_session=True)

def activate(work=WORK):
    work=Path(work);capacity(work,2*1024**2);prepared=read(work/'prepared-head-private.json');receipt=bound(prepared);view=receipt['view'];bound(view['catalogue_descriptor'])
    current=work/'service-current-private.json';prior=read(current) if current.exists() else read(BASE/'scan1_20261104/service-current-private.json')
    pid=prior['pid'];proc=Path('/proc')/str(pid)/'cmdline';cmd=proc.read_bytes();argv=[v.decode() for v in cmd.split(bytes([0])) if v]
    conn=read(BASE/'scan1_20261104/browser-config-private.json')
    if 'graph_core.prod_core1_20261105.serve' in argv:
        oldconfig=read(argv[argv.index('--config')+1]);creds=oldconfig['credentials'];roots=oldconfig['linked_roots']
    elif 'graph_core_chart.mobile_private' in argv and argv[argv.index('--port')+1]=='8765':
        creds=argv[argv.index('--credentials')+1];roots=[argv[i+1] for i,v in enumerate(argv) if v=='--linked-root']
    else:raise ValueError('ORIGINAL_OWNER_PROCESS_CHANGED')
    config=dict(work=str(work),credentials=creds,linked_roots=roots,providers=view['providers'],catalogue=view['catalogue'],port=8765,release_id=release_id())
    body=encode(config);cp=work/('service-config-'+sha(body)+'.json');put(work,cp,body)
    if current.exists() and prior.get('config_sha256')==sha(body):
        h,_=request(conn,'/',303)
        if h['Location']!='/batch-'+view['entry']['sha256']+'/'+Path(view['entry']['path']).name:raise ValueError('RUNNING_PRODUCT_DIFFERS')
        point(work,'head-private.json',prepared)
        return dict(status='ACTIVE_PRODUCT_UNCHANGED',pid=pid)
    Provider(config,work);batch_index(config['catalogue'],linked_roots=roots)
    backup=work/('owner-before-'+str(pid)+'-private.json');put(work,backup,encode(dict(pid=pid,argv=argv)))
    request(conn,'/',401,authorized=False)
    if proc.read_bytes()!=cmd:raise ValueError('OWNER_PID_CHANGED')
    os.kill(pid,signal.SIGTERM)
    for _ in range(80):
        if not alive(pid):break
        time.sleep(.1)
    if alive(pid):raise ValueError('OWNER_NOT_STOPPED_NO_SECOND_LISTENER')
    newargs=[argv[0],'-m','graph_core.prod_core1_20261105.serve','--config',str(cp)];new=None
    try:
        new=launch(newargs,work,'owner-product');ready(conn,new)
        h,_=request(conn,'/',303)
        if h['Location']!='/batch-'+view['entry']['sha256']+'/'+Path(view['entry']['path']).name:raise ValueError('PRODUCT_DEFAULT_MISMATCH')
        _,raw=request(conn,'/product-status.json',200)
        if json.loads(raw)['schema']!='twstockai-daily-product/1.0':raise ValueError('PRODUCT_STATUS_MISMATCH')
    except Exception:
        if new and new.poll() is None:new.terminate();new.wait(timeout=8)
        restored=launch(argv,work,'owner-rollback');ready(conn,restored)
        point(work,'rollback-private.json',dict(pid=restored.pid,old_argv_preserved=str(backup)))
        point(work,'service-current-private.json',dict(prior,pid=restored.pid,status='ROLLED_BACK_ORIGINAL_OWNER'))
        raise
    result=dict(status='ACTIVE_PRODUCT',pid=new.pid,port=8765,config_sha256=sha(body),entry='/batch-'+view['entry']['sha256']+'/'+Path(view['entry']['path']).name,cloud_restart=False,external_android='ANDROID_EXTERNAL_NOT_CONNECTED')
    point(work,'service-current-private.json',result)
    point(work,'head-private.json',prepared) # commit publication ONLY after authenticated readiness
    return result

def main():
    p=argparse.ArgumentParser();p.add_argument('--config',required=True);a=p.parse_args();config=read(a.config)
    if Path(a.config).name!='service-config-'+sha(Path(a.config).read_bytes())+'.json':raise ValueError('PRODUCT_RELEASE_CONFIG_CHANGED')
    if config['port']!=8765:raise ValueError('ORIGINAL_PORT_ONLY')
    # A preserved prior configuration is a compatible read-only rollback. Its
    # producer release remains recorded; all financial providers keep exact pins.
    from rotation_research.artifact_codec import regular
    regular(a.config,config['work'])
    provider=Provider(config,config['work'])
    server=make_server(None,config['credentials'],port=8765,batches=config['catalogue'],linked_roots=config['linked_roots'],lazy_provider=provider)
    print('TWSTOCKAI_PRODUCT_LOOPBACK_OWNER_READY',flush=True)
    try:server.serve_forever()
    finally:server.server_close()
if __name__=='__main__':main()
