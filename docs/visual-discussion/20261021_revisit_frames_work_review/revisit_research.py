"""Causal anchored-price revisit witnesses and immutable prior-price frames.

A side round-trip is evidence of a path, never a formal interval or membership.
Levels only enter when observed in this seed; no future-derived price grid.
"""
from pathlib import Path
from decimal import Decimal as D
from collections import Counter
import argparse,json,gzip,hashlib

canon=lambda x:json.dumps(x,sort_keys=True,ensure_ascii=False,separators=(',',':'),allow_nan=False).encode()
digest=lambda x:'sha256:'+hashlib.sha256(canon(x)).hexdigest()
norm=lambda x:str(D(x).normalize())

def discover(source,start,cutoff):
    rows=[b for b in source['bars']if start<=b['date']<=cutoff]
    if not rows or rows[0]['date']!=start or rows[-1]['date']!=cutoff:raise ValueError('saved start/cutoff required')
    levels={};episodes=[];frames={};gaps=source['source_gaps']['known_calendar_missing_dates'];segment_start=0
    for i,b in enumerate(rows):
        if i and any(rows[i-1]['date']<=g<=b['date']for g in gaps):
            levels={};segment_start=i
        for field in ['low','high','close']:
            key=norm(b[field])
            if key not in levels:levels[key]={'birth':b['date'],'roles':[],'runs':[]}
            q=levels[key]
            if q['birth']==b['date']:q['roles'].append(field)
        close=D(b['close'])
        for value,q in levels.items():
            level=D(value);side=(close>level)-(close<level)
            if not side:continue # equality stays visible in raw bars, no crossing
            if q['runs']and q['runs'][-1]['side']==side:continue
            q['runs'].append({'side':side,'index':i,'date':b['date'],'close':b['close']})
            if len(q['runs'])<3:continue
            runs=q['runs'][-3:];first=runs[0]['index'];prior=rows[first:i]
            lo=min(D(x['low'])for x in prior);hi=max(D(x['high'])for x in prior)
            frame={'code':source['code'],'observed_start':prior[0]['date'],'observed_end':prior[-1]['date'],
                   'records':len(prior),'observed_low':str(lo),'observed_high':str(hi),
                   'bars_fingerprint':digest(prior),'formal_price_bounds':None,'qualification':'PRE_RETURN_OBSERVED_GEOMETRY_NOT_FORMAL_BOX'}
            frame_id=digest(frame);frames[frame_id]=frame
            trip={'code':source['code'],'anchor_price':value,'anchor_known_on_in_seed':q['birth'],
                  'anchor_birth_roles':q['roles'][:],
                  'strict_side_visits':[{k:x[k]for k in ['side','date','close']}for x in runs],
                  'known_on_saved_bar':b['date'],'frame_id':frame_id,
                  'return_close_relation_to_prior_frame':'INSIDE_INCLUSIVE'if lo<=close<=hi else'BELOW'if close<lo else'ABOVE',
                  'return_bar_inside_prior_frame':D(b['low'])>=lo and D(b['high'])<=hi,
                  'return_bar':b,'formal_interval':None,'formal_membership':None,
                  'qualification':'CLOSE_SIDE_ROUND_TRIP_ONLY_NOT_TRANSACTION_PATH_OR_FORMATION'}
            trip['episode_id']=digest(trip);episodes.append(trip)
    current=rows[-1];views=[]
    for e in episodes:
        f=frames[e['frame_id']];lo,hi=D(f['observed_low']),D(f['observed_high']);c,l,h=[D(current[k])for k in ['close','low','high']]
        crossed=[g for g in gaps if f['observed_start']<=g<=cutoff]
        views.append({'episode_id':e['episode_id'],'frame_id':e['frame_id'],
                      'latest_close_relation':'INSIDE_INCLUSIVE'if lo<=c<=hi else'BELOW'if c<lo else'ABOVE',
                      'latest_bar_relation':'WHOLE_BELOW'if h<lo else'WHOLE_ABOVE'if l>hi else'INSIDE_INCLUSIVE'if l>=lo and h<=hi else'OVERLAPS_OR_TOUCHES',
                      'crossed_listed_missing_dates':crossed,'current_relation_source_qualified':False if crossed else None,
                      'formal_stopped':None})
    return {'schema':'m1-anchored-revisit-research/0.1','code':source['code'],'seed_start':start,'cutoff':cutoff,
        'source_records':len(rows),'source_bars_fingerprint':digest(rows),'episodes':episodes,'frames':frames,
        'current_views':views,'latest_segment_start':rows[segment_start]['date'],
        'last_segment_anchor_registry':{k:{'known_on':q['birth'],'birth_roles':q['roles'],'strict_side_runs':len(q['runs'])}for k,q in levels.items()},
        'formal_interval':None,'formal_start':None,'formal_end':None,'formal_membership':None,'selected_frame':None,
        'primary_pressure_id':None,'historical_selection_time':None,'historical_signal_eligible':False,
        'classification':'NOT_VALIDATED','core_usefulness':'NOT_ESTABLISHED','actions':'NOT_EVALUATED'}

def brief(result):
    bounded=[e for e in result['episodes']if e['return_close_relation_to_prior_frame']=='INSIDE_INCLUSIVE']
    ids={e['episode_id']for e in bounded};views=[v for v in result['current_views']if v['episode_id']in ids]
    return {'records':result['source_records'],'episodes':len(result['episodes']),'bounded_close_reentries':len(bounded),
        'side_return_overshoots':len(result['episodes'])-len(bounded),'distinct_bounded_frames':len({e['frame_id']for e in bounded}),
        'current_close_for_bounded_episodes':dict(Counter(v['latest_close_relation']for v in views)),
        'current_whole_bar_for_bounded_episodes':dict(Counter(v['latest_bar_relation']for v in views)),
        'formal_interval':None}

if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('--source',required=True);ap.add_argument('--comparison',required=True);ap.add_argument('--prior-dir',required=True);ap.add_argument('--out',default=str(Path(__file__).parent));a=ap.parse_args()
    p=Path(a.out);p.mkdir(parents=True,exist_ok=True);sraw=Path(a.source).read_bytes();traw=Path(a.comparison).read_bytes()
    assert hashlib.sha256(sraw).hexdigest()=='ab87a51b5b8afd076603f290b10f415bd60d31ae47c5ab2f6d9d609ad4014901'
    assert hashlib.sha256(traw).hexdigest()=='184bdef0b687ec0ab7bfcaaac2157ff7916fbc1000ef312d81b5efc0c2e73e15'
    s,t=map(json.loads,[sraw,traw]);packed=(Path(a.prior_dir)/'candidate-pools.json.gz').read_bytes();raw=gzip.decompress(packed)
    assert hashlib.sha256(raw).hexdigest()=='db4dc777c42dd89d605556be776841ba76e966ecdd9bd46055fbaa58e5d9c2b9';pools=json.loads(raw)
    registry={'layout':'NORMALIZED_EPISODES_FRAMES_AND_CURRENT_BAR; views exactly reconstructable from frame bounds/current bar/listed gaps',
              'episodes':{},'frames':{},'observations':{}};summary={};count=0
    for name,pool in pools.items():
        src=s if name.startswith('2884')else t;entries=[]
        for old in pool['results']:
            r=discover(src,old['start'],pool['cutoff']);count+=1
            for e in r['episodes']:
                previous=registry['episodes'].setdefault(e['episode_id'],e);assert previous==e
            for key,f in r['frames'].items():assert registry['frames'].setdefault(key,f)==f
            obs_id=digest({'code':src['code'],'seed_start':old['start'],'cutoff':pool['cutoff']})
            registry['observations'][obs_id]={'code':src['code'],'seed_start':old['start'],'cutoff':pool['cutoff'],
                'episode_ids':[e['episode_id']for e in r['episodes']],
                'latest_bar':next(b for b in src['bars']if b['date']==pool['cutoff']),
                'listed_missing_dates_in_observation':[g for g in src['source_gaps']['known_calendar_missing_dates']if old['start']<=g<=pool['cutoff']]}
            entries.append({'observation_id':obs_id,'start':old['start'],**brief(r)})
        summary[name]=entries
    specs=[('2884-Oct1',s,'2026-09-17','2026-10-01'),('2884-Oct5',s,'2026-09-17','2026-10-05'),('2884-Oct6',s,'2026-09-17','2026-10-06'),('2884-Oct7',s,'2026-09-17','2026-10-07'),
       ('2884-control-May4',s,'2026-04-15','2026-05-04'),('ABC-reviewed-Jun2',t,'2025-04-07','2025-06-02'),
       ('ABC-followup-Jun13',t,'2025-06-03','2025-06-13'),('G2-early-Feb20',t,'2023-01-16','2023-02-20'),
       ('G2-through-Mar3',t,'2023-01-16','2023-03-03'),('G2-new-seed-Mar3',t,'2023-02-21','2023-03-03'),('2884-last-seed',s,'2026-10-16','2026-10-16')]
    selected={name:discover(src,start,cut)for name,src,start,cut in specs}
    # Lossless indexed storage avoids repeating long random hashes in each seed.
    order=list(registry['episodes']);lookup={key:i for i,key in enumerate(order)}
    registry['episode_table']=[registry['episodes'][key]for key in order];del registry['episodes']
    for observation in registry['observations'].values():
        observation['episode_indices']=[lookup[key]for key in observation.pop('episode_ids')]
    raw_registry=(json.dumps(registry,ensure_ascii=False,separators=(',',':'))+'\n').encode();z=gzip.compress(raw_registry,mtime=0);assert gzip.decompress(z)==raw_registry
    (p/'pool-revisit-registry.json.gz').write_bytes(z)
    report={'pool_observations':count,'unique_episode_records':len(registry['episode_table']),'unique_frame_records':len(registry['frames']),
        'registry_raw_sha256':hashlib.sha256(raw_registry).hexdigest(),'registry_gzip_bytes':len(z),
        'selected':{name:brief(r)for name,r in selected.items()},'formal_formation_rule':'NOT_ESTABLISHED'}
    for name,obj in [('selected-revisits.json',selected),('pool-summaries.json',summary),('summary.json',report)]:
        (p/name).write_text(json.dumps(obj,ensure_ascii=False,indent=2)+'\n')
    assert Path(a.source).read_bytes()==sraw and Path(a.comparison).read_bytes()==traw
    assert(Path(a.prior_dir)/'candidate-pools.json.gz').read_bytes()==packed
    print(json.dumps(report,ensure_ascii=False))
