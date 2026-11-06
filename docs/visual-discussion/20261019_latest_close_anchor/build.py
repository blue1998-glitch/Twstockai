from pathlib import Path
import json,re,hashlib
from decimal import Decimal as D
root=Path(__file__).parent
out=root/'publish/docs/visual-discussion/20261019_latest_close_anchor'
src=Path('core-next/c-right-source.json').read_bytes()
assert hashlib.sha256(src).hexdigest()=='48a8ea5f0a49719917ceb48b15149dbc6c5fa854f9bf36897b527bf9a0f990bb'
data=json.loads(src); bars=data['bars']; by={b['date']:b for b in bars}
selected=[b for b in bars if b['date']>='2025-06-03']
assert len(selected)==336 and max(D(b['high']) for b in selected)==D('28.00')
assert by['2026-01-27']['high']=='26.95' and by['2026-10-16']['close']=='27.30'
source={k:data[k] for k in ['source_export_sha256','source_id','frame_id','chart_base','analysis_as_of','code','price_mode','bars']}
source.update(schema='latest-close-anchor-discussion/0.1',default_view={'start':'2025-06-03','end':'2026-10-16'},review_status='USER_METHOD_RECORDED_BOUNDARY_DISCREPANCY_PENDING',formal_price_bounds=None,representative_date='2026-01-27',representative_high='26.95')
(out/'source.json').write_text(json.dumps(source,ensure_ascii=False,indent=2))
s=Path('/workspace/c-right-region.html').read_text().replace('c-right-region','latest-close-anchor')
s=s.replace('1101｜C右側的新平緩帶','1101｜以收盤27.30回看左側')
s=s.replace('<button class="btn" type="button" data-action="g2">C附近</button>','<button class="btn" type="button" data-action="g2">6/3至最新</button>\n    <button class="btn" type="button" data-action="recent">近期40根</button>\n    <button class="btn" type="button" data-action="reference">1/27代表點</button>')
s=re.sub(r'    <button[^\n]+data-endpoint[^\n]+\n','',s)
s=re.sub(r'  <label class="form-label draft-label".*?</label>\n','',s,flags=re.S)
s=s.replace('微調日期與標記區間','逐交易日查詢')
s=s.replace('C=2024-01-19；新帶終點未定','1/27代表高26.95｜6/3原高28.00')
s=re.sub(r'(<script type="application/json" class="source">).*?(</script>)',lambda m:m[1]+json.dumps(source,ensure_ascii=False,separators=(',',':'))+m[2],s,flags=re.S)
s=s.replace("date==='2024-01-19'","date==='2026-01-27'")
s=s.replace("selected:g2,guide:null,mode:'query',draftStart:null,draftEnd:null","selected:bars.length-1,guide:null,mode:'query'")
a=s.index('  function draft(){'); b=s.index('  function axes(',a);s=s[:a]+s[b:]
a=s.index('    const cVisible=');b=s.index('    root.dataset.first=',a)
s=s[:a]+'''    const refVisible=g2>=state.first&&g2<state.first+state.count;
    const references=[{price:27.30,label:'最新收27.30',kind:'latest',color:'var(--foreground)'},{price:26.95,label:'1/27高26.95',kind:'representative',color:'var(--viz-series-1)'}];
    const inAxis=references.filter(r=>r.price>=py.domain()[0]&&r.price<=py.domain()[1]);
    const refLines=px.selectAll('line.reference').data(inAxis,r=>r.kind).join('line').attr('class',r=>'reference '+r.kind)
      .attr('x1',left).attr('x2',width-right).attr('y1',r=>py(r.price)).attr('y2',r=>py(r.price)).attr('stroke',r=>r.color).attr('stroke-width',1).attr('stroke-dasharray',r=>r.kind==='latest'?null:'4 4');
    const sourcePoints=[{i:g2,price:26.95,kind:'representative'}, {i:start,price:28.00,kind:'start-high'}].filter(p=>p.i>=state.first&&p.i<state.first+state.count);
    px.selectAll('circle.source-point').data(sourcePoints,p=>p.kind).join('circle').attr('class',p=>'source-point '+p.kind)
      .attr('cx',p=>x(p.i)).attr('cy',p=>py(p.price)).attr('r',4).attr('fill','var(--viz-series-1)');
    root.querySelector('.range').textContent=`${shown[0].date}～${shown.at(-1).date}｜${state.count}根｜${refVisible?'1/27代表點在窗內':'1/27來源在畫外'}${inAxis.length<2?'｜參照價超軸':''}`;
'''+s[b:]
s=s.replace("case 'g2':setWindow(initial.first,initial.count);choose(g2);break;","case 'g2':setWindow(initial.first,initial.count);choose(bars.length-1);break;\n      case 'recent':setWindow(bars.length-40,40);choose(bars.length-1);break;\n      case 'reference':setWindow(g2-30,70);choose(g2);break;")
a=s.index("  root.dataset.draftStatus=");b=s.index('  new ResizeObserver',a);s=s[:a]+s[b:]
s=s.replace('  detail(g2);draw(false);','  detail(bars.length-1);draw(false);')
# Reference prices never force the visible price domain. Source dots require actual date visibility.
s=s.replace('  <svg class="chart price"','  <div class="text-small">實線：最新收27.30；虛線：1/27高26.95；圓點：真實來源</div>\n  <svg class="chart price"')
# Query dots are clipped if the selected source is outside the price frame.
s=s.replace("const queryVisible=selectedVisible&&state.mode==='query';","const selectedPrice=bars[state.selected].c;\n    const queryVisible=selectedVisible&&state.mode==='query'&&selectedPrice>=py.domain()[0]&&selectedPrice<=py.domain()[1];")
assert 'draft' not in s and '平緩' not in s and '<html' not in s
Path('/workspace/latest-close-anchor.html').write_text(s);(out/'discussion_fragment.html').write_text(s)
latest=bars[-1]
volume=[]
for n in [1,5,20]:
 avg=sum(D(b['volume_shares_scaled']) for b in bars[-n-1:-1])/n
 volume.append({'prior_trading_records_excluding_current':n,'mean_shares':str(avg),'latest_ratio':str(D(latest['volume_shares_scaled'])/avg),'strategy_threshold':None})
facts={'status':'SOURCE_VERIFIED_USER_BOUNDARY_DISCREPANCY_PENDING','source_file_sha256':hashlib.sha256(src).hexdigest(),'source_1213_all_fields_unchanged':source['bars']==data['bars'],'original_phone_file_reread':False,'analysis_as_of':source['analysis_as_of'],'candidate_start':'2025-06-03','records':len(selected),'raw_whole_interval_max':{'date':'2025-06-03','high':'28.00'},'raw_whole_interval_min':{'date':'2025-11-19','low':'20.25'},'representative':by['2026-01-27'],'latest':latest,'latest_close_above_representative':True,'latest_close_above_raw_whole_interval_max':False,'exact_records':[by[d] for d in ['2025-06-03','2025-06-04','2026-01-27','2026-01-29','2026-10-12','2026-10-13','2026-10-14','2026-10-15','2026-10-16']],'volume_comparisons':volume,'comparators_user_approved':False,'old_pivot_4_date':'2026-01-29','old_pivot_4_price':'26.85','user_rep_is_old_pivot_4':False,'auto_box_or_breakout_rule_approved':False,'fragment_sha256':hashlib.sha256(s.encode()).hexdigest()}
(out/'source_verification.json').write_text(json.dumps(facts,ensure_ascii=False,indent=2))
print(json.dumps({k:v for k,v in facts.items() if k not in ['exact_records','volume_comparisons']},ensure_ascii=False))
