"""Prepare exact existing projections; new minified wire, no new finance math."""
from pathlib import Path
import json,math,shutil,gzip
from graph_core.prod_core1_20261105 import flow as f
from graph_core.scan1_20261104 import engine as e
from graph_core.storage1_20261104.facts import project
from . import intake

def prepare():
    w=intake.WORK;r=f.read(w/'source-result-private.json')
    if r['qualification']['status']!='SOURCE_QUALIFIED':raise ValueError('SOURCE_GATE_NOT_PASSED')
    files=f.read(w/'source-files-private.json');day,maps,markets,sigs=f.inc.sources(intake.store.Sources(w/'capture',files),r['capture_id'])
    if day!=intake.TARGET:raise ValueError('TARGET_MISMATCH')
    old=f.read(e.WORK/'manifest-private.json');prior={s['identity']:s for s in old['stocks']};members={m['market']+':'+m['code']:m for u in markets.values() for m in u['members']}
    active=set(members);oldstate=f.read(e.WORK/'view-state-private.json')
    for s in oldstate['stocks']:
        if s['identity'] not in members:members[s['identity']]={k:s[k] for k in ['code','market','isin','cfi','name']}
    sw=w/'scan';sw.mkdir(mode=0o700,exist_ok=True);facts=[];stocks=[];fact_blocks=0;available=0
    for identity,m in sorted(members.items()):
        lower='twse' if m['market']=='TWSE' else 'tpex';raw=maps[m['market']].get(m['code']) if identity in active else None
        fact=project(m,raw,as_of=day,capture_id=r['capture_id'],daily_sha256=sigs[lower+'-daily.json'],parent_isin=prior.get(identity,{}).get('isin'));fact['batch_id']=r['capture_id']
        body=f.encode(fact);h=f.sha(body);p=sw/'facts'/('series-'+h+'.json');facts.append((p,body));fact_blocks+=math.ceil(len(body)/4096)*4096;available+=fact['source_status']=='SOURCE_BAR_AVAILABLE'
        stocks.append(dict(**{k:fact[k] for k in ['identity','code','market','isin','cfi','as_of']},fact_path=str(p),fact=dict(path=p.name,bytes=len(body),sha256=h),parent_isin=prior.get(identity,{}).get('isin',fact['isin'])))
    # New records are bounded to ONE4KiB block, enforced before every commit.
    # Head/catalogue/control actual writes remain guarded; larger originals kept.
    estimate=dict(facts_physical=fact_blocks,journal_physical=len(stocks)*4096,audit_budget=600000,codec_indexes_actions_view_budget=1600000,control_and_tests_budget=524288)
    need=sum(estimate.values());free=shutil.disk_usage(w).free
    if free-need<f.RESERVE+65536:raise OSError('NEW_BATCH_CAPACITY_PREFLIGHT: need='+str(need)+' available_above_reserve='+str(free-f.RESERVE))
    intake.store.put(w,w/'batch-capacity-plan-private.json',f.encode(dict(estimated_additional_bytes=need,free_bytes=free,reserve_bytes=f.RESERVE,components=estimate,as_of=day,reference=len(stocks),available=available)))
    intake.store.put(w,sw/'baseline-private.json',f.encode(f.read(w/'baseline-private.json')))
    for path,body in facts:intake.store.put(w,path,body)
    originals={}
    for name,h in sigs.items():
        d=files[h];logical=Path(d['path']);physical=logical if logical.exists() else intake.store.c.sidecar(logical);s=physical.stat()
        originals[name]=dict(path=str(physical),logical_path=str(logical),logical_bytes=d['bytes'],sha256=h,metadata=[s.st_size,s.st_mtime_ns,s.st_ino,s.st_dev])
    protected=dict(old['protected_code'])
    for path in [Path(__file__),Path(__file__).with_name('scan_io.py'),Path(__file__).with_name('source_reader.py'),Path(f.__file__),Path(f.__file__).with_name('view.py'),Path(f.__file__).with_name('serve.py')]:protected[str(path)]=f.sha(path.read_bytes())
    spec=dict(version=e.VERSION,journal_encoding='MINIFIED_UTF8_V1',as_of=day,capture_id=r['capture_id'],source_stage_root=str(w),source_capture_root=str(w/'capture'),source_files=files,protected_code=protected,original_sources=originals,daily_sources={m:sigs[lower+'-daily.json'] for m,lower in [('TWSE','twse'),('TPEX','tpex')]},stocks=stocks)
    spec['id']=f.sha(f.encode(spec));intake.store.save_exact(w,sw/'manifest-private.json',f.encode(spec));return dict(scanwork=str(sw),as_of=day,reference=len(stocks),available=available,capacity=estimate)
if __name__=='__main__':print(json.dumps(prepare(),ensure_ascii=False))
