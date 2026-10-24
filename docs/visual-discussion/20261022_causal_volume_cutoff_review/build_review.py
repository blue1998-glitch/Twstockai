"""External read-only study: preserve saved OHLCV and materialize cutoff facts."""
from copy import deepcopy
from decimal import Decimal as D
import argparse
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent


def sha(value):
    return hashlib.sha256(json.dumps(value,ensure_ascii=False,sort_keys=True,separators=(',',':')).encode()).hexdigest()


def cases_from(value):
    bars=[]
    for item in value['raw1101']:
        response=item['response']
        if response['stat']!='OK' or response['fields'][1]!='成交股數':
            raise ValueError('Unexpected official source fields')
        for row in response['data']:
            year,month,day=row[0].split('/')
            clean=lambda s:s.replace(',','').strip()
            bars.append(dict(date=f'{int(year)+1911:04}-{month}-{day}',open=clean(row[3]),
                             high=clean(row[4]),low=clean(row[5]),close=clean(row[6]),
                             volume_shares=clean(row[1])))
    bars.sort(key=lambda b:b['date'])
    bars2884=[dict(date=b['date'],open=b['open'],high=b['high'],low=b['low'],close=b['close'],
                   volume_shares=b['volume_shares_scaled']) for b in value['raw2884']['bars']]
    return [dict(id='1101-2025',code='1101',name='1101 台泥｜2025',bars=bars,
                 dates=['2025-05-13','2025-05-29','2025-06-02','2025-06-03','2025-06-30'],
                 observation=dict(date='2025-05-13',price='31.40',volume_shares='10264322',role='OBSERVED_DAILY_HIGH_ONLY'),
                 review_notes=[dict(event_date='2025-06-03',recorded_at='2026-10-22',
                     text='事後人工研究：原案例把 6/3 標作前箱破底；先前量可提出待消化賣壓候選。這不是當時已保存的自動判定，沒有精確套牢股數。')],
                 source_gaps=dict(actions='UNVERIFIED_FULL_PERIOD_ACTIONS',publication='UNVERIFIED',calendar='NO_NEW_CALENDAR_AUTHENTICATION')),
            dict(id='2884-2026',code='2884',name='2884 玉山金｜2026',bars=bars2884,
                 dates=['2026-10-07','2026-10-14','2026-10-15','2026-10-16'],
                 observation=dict(date='2026-09-17',price='47.35',volume_shares='51011663',role='OBSERVED_DAILY_HIGH_ONLY_NOT_FORMAL_RETURN_REFERENCE'),
                 review_notes=[dict(event_date='2026-10-15',recorded_at='2026-10-22',
                     text='回顧對照：本日整根 K 高於 9/17 原高；價格向上與量增加都可見，仍不把它標成成功換手或買入資格。')],
                 source_gaps=value['raw2884']['source_gaps'])]


def snapshot(case,day):
    # Never read dates, review annotations or bars after this cutoff for facts.
    bars=deepcopy([b for b in case['bars'] if b['date']<=day])
    if not bars or bars[-1]['date']!=day:raise ValueError('Exact saved date required')
    peak=max(int(b['volume_shares']) for b in bars)
    high=max(D(b['high']) for b in bars);low=min(D(b['low']) for b in bars)
    obs=deepcopy(case['observation']) if case['observation']['date']<=day else None
    close=D(bars[-1]['close']);lastvol=int(bars[-1]['volume_shares'])
    comparison=None
    if obs:
        p=D(obs['price'])
        comparison=dict(close_relation='ABOVE' if close>p else 'BELOW' if close<p else 'EQUAL',
                        whole_candle_above=D(bars[-1]['low'])>p,
                        volume_vs_source_bar='ABOVE' if lastvol>int(obs['volume_shares']) else 'BELOW' if lastvol<int(obs['volume_shares']) else 'EQUAL')
    facts=dict(schema='cutoff-price-volume-facts/0.1',case_id=case['id'],as_of=day,
               price_mode='RAW_CANDIDATE',volume_unit='SHARES_REPORTED',bars=bars,
               first_date=bars[0]['date'],bar_count=len(bars),latest=bars[-1],
               observed_reference=obs,reference_comparison=comparison,
               reading_window_volume_max=str(peak),reading_window_volume_peak_dates=[b['date'] for b in bars if int(b['volume_shares'])==peak],
               plot_domain=dict(low=str(low),high=str(high),volume_max=str(peak)),
               historical_publication_authenticated=False,source_gaps=deepcopy(case['source_gaps']),
               inferred_structure_state=None,volume_economic_role='UNKNOWN',
               actual_trapped_share_count=None,action_qualification='NOT_EVALUATED',historical_signal_eligible=False)
    facts['facts_id']='sha256:'+sha(facts)
    return facts


def build(value):
    cases=cases_from(value)
    out=dict(schema='cutoff-volume-review/0.1',base_commit=value['base_commit'],
             selection_process=value['selection_process'],price_basis_selection='EXPLICIT_ASSISTANT_RAW_FACT_REVIEW_NOT_USER_B_MODE_DECISION',
             historical_classifier_validation='NOT_PERFORMED',cases=[])
    for c in cases:
        out['cases'].append(dict(id=c['id'],name=c['name'],snapshots=[snapshot(c,d) for d in c['dates']],
            retrospective_notes=c['review_notes'],manual_adjudication_available_in_historical_replay=False))
    return out


def draw_png(case,day,font_path):
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    from matplotlib.font_manager import FontProperties
    from matplotlib.patches import Rectangle
    font=FontProperties(fname=str(font_path))
    s=snapshot(case,day);bars=s['bars']
    fig,(ax,av)=plt.subplots(2,1,figsize=(12,5.8),gridspec_kw={'height_ratios':[3,1]},sharex=True)
    for i,b in enumerate(bars):
        o,h,l,c=map(float,[b['open'],b['high'],b['low'],b['close']]);color='#d74647' if c>=o else '#168b78'
        ax.vlines(i,l,h,color=color,linewidth=.7)
        ax.add_patch(Rectangle((i-.3,min(o,c)),.6,max(abs(c-o),.015),color=color,linewidth=0))
        av.bar(i,int(b['volume_shares'])/1e6,width=.7,color=color)
    idx=[0,len(bars)//2,len(bars)-1]
    av.set_xticks(idx,[bars[i]['date'] for i in idx])
    for axis in (ax,av):axis.grid(axis='y',alpha=.2);axis.set_axisbelow(True)
    ax.set_ylabel('價格（元）',fontproperties=font);av.set_ylabel('百萬股',fontproperties=font)
    av.set_xlabel('保存交易日｜只到指定截止日',fontproperties=font)
    ax.set_title(case['name']+'｜截止 '+day+'｜量的經濟角色：未知',fontproperties=font)
    fig.text(.08,.015,'原始日 K・回顧選樣非盲測・完整公司行動／歷史發布可得未核・非交易訊號',fontproperties=font,fontsize=10)
    fig.tight_layout(rect=(0,.035,1,1))
    fig.savefig(ROOT/f'{case["id"]}-{day}.png',dpi=140);plt.close(fig)


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--skip-png',action='store_true');p.add_argument('--font',type=Path,default=ROOT/'NotoSansCJKtc-Regular.otf');p.add_argument('--inline-output',type=Path);args=p.parse_args()
    if not args.skip_png and not args.font.is_file():p.error('Provide --font with a Chinese font, or --skip-png for data/HTML only')
    value=json.loads((ROOT/'source-inputs.json').read_text());out=build(value)
    (ROOT/'cutoff-facts.json').write_text(json.dumps(out,ensure_ascii=False,separators=(',',':'))+'\n')
    cases=cases_from(value)
    abc=[b for b in cases[0]['bars'] if '2025-04-07'<=b['date']<='2025-06-02']
    findings=dict(scope='RETROSPECTIVE_MANUAL_RANGE_NOT_HISTORICAL_AUTOMATIC_BOX',manual_range=dict(start='2025-04-07',end='2025-06-02',count=len(abc),historical_membership_known_at=None),price_peak_rows=[b for b in abc if D(b['high'])==max(D(r['high']) for r in abc)],volume_peak_rows=[b for b in abc if int(b['volume_shares'])==max(int(r['volume_shares']) for r in abc)],formal_volume_representative_line=None,actual_trapped_share_count=None)
    earlier=[b for b in abc if b['date']<='2025-05-29']
    june2=next(b for b in abc if b['date']=='2025-06-02')
    findings['boundary_guard']=dict(earlier_observation_window=['2025-04-07','2025-05-29'],earlier_minimum_low=str(min(D(b['low']) for b in earlier)),june2_low=june2['low'],june2_close=june2['close'],manual_box_end='2025-06-02',user_labelled_departure='2025-06-03',formal_box_floor=None,warning='DO_NOT_PROMOTE_READING_WINDOW_MINIMUM_OR_OLD_RESEARCH_CORRIDOR_TO_USER_APPROVED_FLOOR')
    (ROOT/'case-findings.json').write_text(json.dumps(findings,ensure_ascii=False,indent=2)+'\n')
    if not args.skip_png:
        for c in cases:
            for day in ([c['dates'][1],c['dates'][3]] if c['code']=='1101' else [c['dates'][1],c['dates'][2]]):draw_png(c,day,args.font)
    fragment=(ROOT/'viewer-template.html').read_text().replace('__FACTS_JSON__',json.dumps(out,ensure_ascii=False,separators=(',',':')).replace('<','\\u003c'))
    (ROOT/'viewer-fragment.html').write_text(fragment)
    if args.inline_output:args.inline_output.write_text(fragment)
    standalone='<!doctype html><html lang="zh-Hant"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>歷史截止價量研究</title><style>:root{font-family:system-ui,sans-serif;color-scheme:light dark;--foreground:light-dark(#182638,#e4eaf1);--background:light-dark(#fff,#15202c);--border:light-dark(#dce2e8,#465669);--red:#d74647;--green:#168b78;--primary:light-dark(#e8eef5,#35495f);--primary-foreground:var(--foreground)}body{max-width:1050px;margin:auto;padding:16px;background:var(--background);color:var(--foreground)}button,select{font:inherit;padding:8px;margin:4px;min-height:44px}p{line-height:1.6}</style></head><body>'+fragment+'</body></html>'
    (ROOT/'review.html').write_text(standalone)
    print(json.dumps({'cases':len(out['cases']),'snapshots':sum(len(c['snapshots']) for c in out['cases']),'facts_sha256':hashlib.sha256((ROOT/'cutoff-facts.json').read_bytes()).hexdigest()}))
