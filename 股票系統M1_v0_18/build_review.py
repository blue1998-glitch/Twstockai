"""Build offline review from numeric-engine outputs; rendering never decides states."""
import json
import sys
from pathlib import Path
ROOT=Path(__file__).resolve().parent
sys.path.insert(0,str(ROOT/'src'))
from structure import Config, project_prices, _run_prefix
from analysis_jobs import run_analysis_job


def build():
    viewer={}
    sensitivity=[]
    for code in ['8069','6488']:
        job=json.loads((ROOT/'data'/f'{code}_analysis_job.json').read_text())
        candles=job['candles'];events=job['corporate_actions']['records']
        viewer[code]=dict(name='元太' if code=='8069' else '環球晶',candles=candles,events=events,modes={},ma={})
        for mode in ['RAW_CANDIDATE','ADJUSTED_CANDIDATE']:
            job['price_mode']=mode
            combined=run_analysis_job(job)
            (ROOT/'output'/f'{code}_{mode}_ANALYSIS.json').write_text(json.dumps(combined,ensure_ascii=False,indent=2))
            # Keep historical standalone structure files byte-compatible.
            legacy=combined['components']['structure']
            result={k:legacy[k] for k in ['code','price_mode','rule_version','snapshots','event_ledger','schema_version','parameters_fingerprint','data_fingerprint','events_fingerprint','data_quality','limitations']}
            ma=combined['components']['daily_ma']
            (ROOT/'output'/f'{code}_{mode}_MA.json').write_text(json.dumps(ma,ensure_ascii=False,indent=2))
            bases={}
            for snapshot in ma['snapshots']:bases[snapshot['events_fingerprint']]=snapshot['curves']
            viewer[code]['ma'][mode]=dict(bases=bases,refs=[s['events_fingerprint'] for s in ma['snapshots']])
            (ROOT/'output'/f'{code}_{mode}.json').write_text(json.dumps(result,ensure_ascii=False,indent=2))
            # Compact display projection; complete audit outputs remain in JSON files.
            viewer[code]['modes'][mode]=[dict(
                p=[[p['kind']=='HIGH',p['profile']=='major',p['occurred_index'],p['confirmed_index'],p['price'],p['evidence']['reversal'],p['evidence']['required_reversal'],p['evidence']['bars_after_extreme']] for p in s['pivots']],
                z=[[z['profile']=='major',z['created_index'],z['low'],z['high'],z['role']=='SUPPORT_CANDIDATE'] for z in s['zones'] if z['state']=='ACTIVE_CANDIDATE'],
                q=[[p['profile']=='major',p['occurred_index'],p['price']] for p in s['pending']],
                d=s['daily_events'],s=s['structure_status']=='UNKNOWN',t=s['event_status'],v=s['data_quality']['volume_context'],cal=s['data_quality']['calendar_status']) for s in result['snapshots']]
        adjusted=project_prices(candles,events,candles[-1]['date'],'ADJUSTED_CANDIDATE')
        for factor,minor,major in [('0.75','1.125','2.25'),('1','1.5','3'),('1.25','1.875','3.75')]:
            r=_run_prefix(adjusted,Config(minor_multiple=minor,major_multiple=major))
            sensitivity.append(dict(code=code,factor=factor,minor_multiple=minor,major_multiple=major,
                                    minor_pivots=sum(p['profile']=='minor' for p in r['pivots']),
                                    major_pivots=sum(p['profile']=='major' for p in r['pivots']),
                                    interpretation='Count sensitivity only; no best parameter or trading performance inferred'))
        render_png(code,adjusted,result['snapshots'][-1])
    (ROOT/'output'/'參數敏感度.json').write_text(json.dumps(sensitivity,ensure_ascii=False,indent=2))
    template=(ROOT/'viewer_template.html').read_text()
    payload=json.dumps(viewer,ensure_ascii=False,separators=(',',':')).replace('</',r'<\/')
    (ROOT/'價格結構重播.html').write_text(template.replace('__ENGINE_DATA__',payload))


def render_png(code,candles,snapshot):
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    from matplotlib.patches import Rectangle
    start=max(0,len(candles)-100)
    part=candles[start:]
    fig,(ax,av)=plt.subplots(2,1,figsize=(15,8),gridspec_kw={'height_ratios':[4,1]},sharex=True,layout='constrained')
    fig.patch.set_facecolor('#f6f8fc')
    ymin=min(float(c['low']) for c in part);ymax=max(float(c['high']) for c in part)
    pad=(ymax-ymin)*.12
    for i,c in enumerate(part,start):
        o,h,l,close=[float(c[k]) for k in ['open','high','low','close']]
        color='#dd424c' if close>o else '#15956d' if close<o else '#68768a'
        ax.vlines(i,l,h,color=color,lw=1)
        ax.add_patch(Rectangle((i-.32,min(o,close)),.64,max(abs(o-close),(ymax-ymin)*.001),facecolor=color,edgecolor=color,lw=.6))
        av.bar(i,float(c['volume_shares_scaled'])/1e6,width=.65,color=color,alpha=.65)
    zones=[z for z in snapshot['zones'] if z['profile']=='major' and z['state']=='ACTIVE_CANDIDATE' and float(z['low'])<=ymax and float(z['high'])>=ymin][-4:]
    for z in zones:
        a=max(start,z['created_index'])
        color='#4c8bdc' if z['role']=='SUPPORT_CANDIDATE' else '#d99835'
        ax.fill_between([a,len(candles)-.5],float(z['low']),float(z['high']),color=color,alpha=.13)
    points=[p for p in snapshot['pivots'] if p['profile']=='major' and p['occurred_index']>=start]
    for p in points:
        idx=p['occurred_index'];confirm=p['confirmed_index'];price=float(p['price']);hi=p['kind']=='HIGH'
        ax.scatter(idx,price,marker='v' if hi else '^',color='#b8791d' if hi else '#366dcc',s=70,zorder=5)
        ax.scatter(confirm,float(candles[confirm]['close']),marker='o',s=24,facecolor='white',edgecolor='#374358',zorder=6)
        ax.annotate(p['occurred_at'][5:]+' > '+p['confirmed_at'][5:],(idx,price),xytext=(0,15 if hi else -22),textcoords='offset points',ha='center',fontsize=8,color='#30415b')
    x=[i for i in range(start,len(candles)) if (i-start)%15==0]
    av.set_xticks(x,[candles[i]['date'][5:] for i in x])
    ax.set_ylim(ymin-pad,ymax+pad)
    ax.set_title(f'{code} | Real daily OHLC | Major candidate pivots | As of 2026-09-30',loc='left',fontsize=15,pad=14,fontweight='bold')
    ax.set_ylabel('TWD / adjusted candidate')
    av.set_ylabel('Volume\n(million shares*)',fontsize=9)
    for a in (ax,av):
        a.set_facecolor('white');a.grid(axis='y',color='#e5eaf2',lw=.7);a.set_axisbelow(True)
        a.spines[['top','right']].set_visible(False)
    fig.supxlabel('Triangle = extreme date | Hollow circle = rule-confirmation date | Labels: occurrence > confirmation\nResearch candidates; cash-dividend adjustments only. *Source lots scaled; no precision recovery.',fontsize=10)
    fig.savefig(ROOT/'output'/f'{code}_結構候選.png',dpi=150)
    plt.close(fig)


if __name__=='__main__':build()
