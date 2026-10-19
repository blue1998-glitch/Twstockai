from pathlib import Path
from decimal import Decimal as D
import json,re,hashlib,argparse
ap=argparse.ArgumentParser();ap.add_argument('--template',default='/workspace/latest-close-anchor.html');ap.add_argument('--source',default='core-next/c-right-source.json');ap.add_argument('--out',default='left-pressure/publish/docs/visual-discussion/20261019_previous_box_pressure');ap.add_argument('--fragment',default='/workspace/previous-box-pressure.html');args=ap.parse_args()
out=Path(args.out);out.mkdir(parents=True,exist_ok=True)
src=Path(args.source).read_bytes();assert hashlib.sha256(src).hexdigest()=='48a8ea5f0a49719917ceb48b15149dbc6c5fa854f9bf36897b527bf9a0f990bb'
old=json.loads(src);bars=old['bars'];by={b['date']:b for b in bars};a=[b for b in bars if '2025-04-08'<=b['date']<='2025-05-29']
assert len(a)==37 and min(D(b['low']) for b in a)==D('28.45') and max(D(b['high']) for b in a)==D('31.40')
source={k:old[k] for k in ['source_export_sha256','source_id','frame_id','chart_base','analysis_as_of','code','price_mode','bars']}
source.update(schema='previous-box-pressure-discussion/0.1',default_view={'start':'2025-03-03','end':'2025-06-13'},assistant_candidate={'display_start':'2025-04-08','display_end':'2025-05-29','wick_low':'28.45','wick_high':'31.40','volume_max_shares':max(int(b['volume_shares_scaled']) for b in a),'records':37,'status':'ASSISTANT_HYPOTHESIS_NOT_USER_APPROVED','formal_start':None,'formal_end':None,'formal_price_bounds':None,'why_this_candidate':'nearest consolidation before lateMay/June decline, viewed from latest saved close27.30; not arbitrary historical split'},user_reviewed={'jan27_representative':{'date':'2026-01-27','high':'26.95'},'jun03_role':'previous box lower-edge breakdown, outside current box; user interpretation','settlement':'Jan27-to-latest user structural interpretation'},review_status='WAITING_FOR_USER_PREVIOUS_BOX_IDENTIFICATION')
(out/'source.json').write_text(json.dumps(source,ensure_ascii=False,indent=2))
s=Path(args.template).read_text().replace('latest-close-anchor','previous-box-pressure')
s=s.replace('1101｜以收盤27.30回看左側','1101｜從27.30回看前一箱')
s=s.replace('>6/3至最新<','>前箱前後<').replace('>近期40根<','>回最新<').replace('>1/27代表點<','>候選整理<')
s=s.replace('    <button class="btn" type="button" data-action="reference">候選整理</button>','    <button class="btn" type="button" data-action="reference">候選整理</button>\n    <button class="btn" type="button" data-action="background">更左背景</button>')
s=s.replace('實線：最新收27.30；虛線：1/27高26.95；圓點：真實來源','淡底：前箱候選，尚未定界｜實線：已存收27.30')
s=s.replace('1/27代表高26.95｜6/3原高28.00','A 4/8低28.45｜B 5/13高31.40｜C 6/3舊箱破底（人工判讀）')
s=re.sub(r'(<script type="application/json" class="source">).*?(</script>)',lambda m:m[1]+json.dumps(source,ensure_ascii=False,separators=(',',':'))+m[2],s,flags=re.S)
s=s.replace("  const start=", "  const indexOf=date=>bars.findIndex(b=>b.date===date);\n  const event=indexOf('2025-06-03'),candidateStart=indexOf('2025-04-08'),candidateEnd=indexOf('2025-05-29'),candidateHigh=indexOf('2025-05-13');\n  const start=")
s=s.replace("selected:bars.length-1,guide:null,mode:'query'","selected:event,guide:null,mode:'query'")
# Fill is behind candle/volume marks, clipped to the full original candidate envelope, never recomputed from a visible subwindow.
needle="    const marks=px.select('g.marks');"
layer='''    const candidate=data.assistant_candidate;
    for(const [svg,scale,h,volume] of [[px,py,priceH,false],[vx,vy,volumeH,true]]){
      const clipId='previous-box-'+(volume?'volume':'price');
      const defs=svg.selectAll('defs').data([0]).join('defs');
      defs.selectAll('clipPath').data([0]).join('clipPath').attr('id',clipId).selectAll('rect').data([0]).join('rect')
        .attr('x',left).attr('y',top).attr('width',frameW).attr('height',h-top-bottom);
      const backdrop=svg.selectAll('g.candidate-backdrop').data([0]).join('g').attr('class','candidate-backdrop').attr('clip-path',`url(#${clipId})`);
      const fullTop=volume?scale(candidate.volume_max_shares/1e6):scale(+candidate.wick_high);
      const fullBottom=volume?scale(0):scale(+candidate.wick_low);
      const intersects=candidateEnd>=state.first&&candidateStart<state.first+state.count;
      backdrop.selectAll('rect.candidate-fill').data(intersects?[0]:[]).join('rect').attr('class','candidate-fill')
        .attr('data-display-only','ASSISTANT_HYPOTHESIS_NOT_USER_APPROVED')
        .attr('x',x(candidateStart-.5)).attr('width',x(candidateEnd+.5)-x(candidateStart-.5))
        .attr('y',fullTop).attr('height',fullBottom-fullTop).attr('fill','var(--viz-series-1)').attr('fill-opacity',.18).attr('stroke','none');
      backdrop.lower();
      svg.select('g.marks').attr('clip-path',`url(#${clipId})`);
    }
'''
s=s.replace(needle,layer+needle)
a=s.index('    const refVisible=');b=s.index('    root.dataset.first=',a)
s=s[:a]+'''    const references=[{price:27.30,kind:'latest',color:'var(--foreground)'},{price:26.95,kind:'representative',color:'var(--viz-series-1)'}];
    const inAxis=references.filter(r=>r.price>=py.domain()[0]&&r.price<=py.domain()[1]);
    px.selectAll('line.reference').data(inAxis,r=>r.kind).join('line').attr('class',r=>'reference '+r.kind)
      .attr('x1',left).attr('x2',width-right).attr('y1',r=>py(r.price)).attr('y2',r=>py(r.price))
      .attr('stroke',r=>r.color).attr('stroke-width',1).attr('stroke-dasharray',r=>r.kind==='latest'?null:'4 4');
    const points=[{i:candidateStart,price:28.45,kind:'candidate-low',label:'A'}, {i:candidateHigh,price:31.40,kind:'candidate-high',label:'B'}, {i:event,price:26.55,kind:'old-breakdown',label:'C'}, {i:g2,price:26.95,kind:'representative',label:'1/27'}].filter(p=>p.i>=state.first&&p.i<state.first+state.count);
    px.selectAll('circle.source-point').data(points,p=>p.kind).join('circle').attr('class',p=>'source-point '+p.kind)
      .attr('cx',p=>x(p.i)).attr('cy',p=>py(p.price)).attr('r',4).attr('fill','var(--viz-series-1)');
    px.selectAll('text.source-label').data(points,p=>p.kind).join('text').attr('class','source-label')
      .attr('x',p=>Math.min(width-right-20,Math.max(left+6,x(p.i)+6)))
      .attr('y',p=>Math.max(top+14,py(p.price)-8)).text(p=>p.label);
    root.querySelector('.range').textContent=`${shown[0].date}～${shown.at(-1).date}｜${state.count}根｜候選未批准${inAxis.some(r=>r.kind==='latest')?'':'｜27.30在軸外'}${g2<state.first||g2>=state.first+state.count?'｜1/27來源在畫外':''}`;
    root.dataset.candidateStatus=candidate.status;
'''+s[b:]
s=s.replace("case 'g2':setWindow(initial.first,initial.count);choose(bars.length-1);break;","case 'g2':setWindow(initial.first,initial.count);choose(event);break;")
s=s.replace("case 'reference':setWindow(g2-30,70);choose(g2);break;","case 'reference':setWindow(indexOf('2025-04-01'),indexOf('2025-06-06')-indexOf('2025-04-01')+1);choose(candidateHigh);break;\n      case 'background':setWindow(indexOf('2024-09-02'),indexOf('2025-06-13')-indexOf('2024-09-02')+1);choose(event);break;")
s=s.replace('detail(bars.length-1);draw(false);','detail(event);draw(false);')
assert 'start-high' not in s and '<html' not in s
Path(args.fragment).write_text(s);(out/'discussion_fragment.html').write_text(s)
report={'status':'PASS_SOURCE_FACTS_ONLY','source_original_bytes_sha256':hashlib.sha256(src).hexdigest(),'all_1213_bars_unchanged':source['bars']==old['bars'],'source_binding':{k:source[k] for k in ['source_id','frame_id','chart_base','analysis_as_of']},'original_phone_json_reread':False,'source_window_is_box_membership':False,'candidate':source['assistant_candidate'],'latest_saved_close':'27.30','latest_below_candidate_low':D('27.30')<D('28.45'),'distance_to_candidate_low':'1.15','distance_to_candidate_low_percent':str((D('28.45')/D('27.30')-1)*100),'source_records':[by[d] for d in ['2025-04-07','2025-04-08','2025-05-13','2025-05-29','2025-06-02','2025-06-03','2026-01-27','2026-10-16']],'jun03_role':'USER_REPORTED_PREVIOUS_BOX_BREAKDOWN_NOT_CURRENT_BOX_MEMBER','jun02_relation':'close27.70 is below candidate28.45, candidate not approved; do not callJun03 first breakdown','candidate_approved':False,'fragment_sha256':hashlib.sha256(s.encode()).hexdigest()}
(out/'source_verification.json').write_text(json.dumps(report,ensure_ascii=False,indent=2));print(json.dumps({'fragment_bytes':len(s.encode()),'candidate_records':source['assistant_candidate']['records'],'sha256':report['fragment_sha256']}))
