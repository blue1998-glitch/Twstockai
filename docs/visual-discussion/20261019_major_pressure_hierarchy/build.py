from pathlib import Path
from decimal import Decimal as D
import json,re,hashlib,argparse
ap=argparse.ArgumentParser();ap.add_argument('--template',default='/workspace/box-reference-review.html');ap.add_argument('--out',default='major-pressure/publish/docs/visual-discussion/20261019_major_pressure_hierarchy');ap.add_argument('--fragment',default='/workspace/major-pressure-context.html');args=ap.parse_args()
out=Path(args.out);out.mkdir(parents=True,exist_ok=True)
parent=Path(args.template).read_bytes();assert hashlib.sha256(parent).hexdigest()=='05f9b63920d691d41006ed80bc45a11e9b6fad3f0e50acad7b046e8ba4352cad'
s=parent.decode();data=json.loads(re.search(r'<script type="application/json" class="source">(.*?)</script>',s,re.S).group(1));old=json.loads(json.dumps(data));bars=data['bars'];by={b['date']:b for b in bars}
context=[b for b in bars if '2023-06'<=b['date'][:7]<='2025-04'];assert len(context)==463
data['schema']='major-pressure-hierarchy-discussion/0.1';data['default_view']={'start':'2023-06-01','end':'2025-06-13'}
data.pop('reference_inspection');data['review_status']='LOCAL_REP_CONFIRMED_MAJOR_BAND_PRIORITY_REPORTED'
data['user_region']['user_selected_representative']={'date':'2025-05-13','high':'31.40','scope':'reviewed local39-row box only','importance':'secondary context;not main hurdle','evidence_type':'USER_REPORTED'}
data['major_pressure_band']={'start_month':'2023-06','end_month':'2025-04','time_precision':'MONTH','exact_start':None,'exact_end':None,'formal_price_bounds':None,'whole_region_volume_rule':None,'representative':None,'priority':'USER_IDENTIFIED_MORE_IMPORTANT_THAN_LOCAL_BOX','time_overlap_is_formal_nesting':False}
data['major_display']={'status':'MONTH_CONTEXT_ENVELOPE_ONLY_NOT_FORMAL_BOUNDARY','display_start':context[0]['date'],'display_end':context[-1]['date'],'full_month_context_records':463,'inner_start':'2023-07-03','inner_end':'2025-03-31','wick_low':str(min(D(b['low']) for b in context)),'wick_high':str(max(D(b['high']) for b in context)),'volume_max_shares':max(int(b['volume_shares_scaled']) for b in context),'opacity':.18,'edges':'fade throughoutJune2023 andApril2025;user exact endpoints unknown','display_month_window_is_approved_box_membership':False}
s=s.replace('box-reference-review','major-pressure-context').replace('1101｜前箱的價峰與量峰','1101｜主要壓力帶與局部箱')
s=s.replace('>前箱前後<','>長期壓力帶<').replace('>回最新<','>近期結構<').replace('>聚焦此箱<','>局部箱<').replace('>更左背景<','>同看現價<')
s=re.sub(r'  <div class="viz-controls" role="group" aria-label="切換查詢日，不選定案例代表">.*?整箱代表尚未選定</div>\n','',s,flags=re.S)
s=s.replace('淡底：已確認時間段｜高低外包僅供顯示｜實線：已存收27.30','主帶約2023/6～2025/4（月份起訖漸淡）｜局部箱4/7～6/2')
s=s.replace('4/7量峰日｜5/13價峰日｜6/2區間末｜6/3在外','主帶優先｜5/13為局部代表｜色帶僅顯示外包，非正式壓力界線')
s=re.sub(r'(<script type="application/json" class="source">).*?(</script>)',lambda m:m[1]+json.dumps(data,ensure_ascii=False,separators=(',',':'))+m[2],s,flags=re.S)
s=s.replace("const g2=bars.findIndex(b=>b.date==='2026-01-27');","const g2=bars.findIndex(b=>b.date==='2026-01-27');\n  const legacyG1=bars.findIndex(b=>b.date==='2023-11-28'),repeatHigh=bars.findIndex(b=>b.date==='2025-03-12');")
s=s.replace('selected:regionHigh,guide:null','selected:legacyG1,guide:null')
a=s.index('    const region=data.region_display;');b=s.index("    const marks=px.select('g.marks');",a)
layer='''    const major=data.major_display;
    const majorFirst=indexOf(major.display_start),majorLast=indexOf(major.display_end);
    const coreFirst=indexOf(major.inner_start),coreLast=indexOf(major.inner_end);
    const layers=[{kind:'major',first:majorFirst,last:majorLast,lo:+major.wick_low,hi:+major.wick_high,maxV:major.volume_max_shares,opacity:.18,color:'var(--viz-series-1)'},
      {kind:'local',first:regionStart,last:regionEnd,lo:+data.region_display.wick_low,hi:+data.region_display.wick_high,maxV:data.region_display.volume_max_shares,opacity:.10,color:'var(--viz-series-2)'}];
    for(const [svg,scale,h,volume] of [[px,py,priceH,false],[vx,vy,volumeH,true]]){
      const clipId='major-context-'+(volume?'volume':'price');
      const defs=svg.selectAll('defs').data([0]).join('defs');
      defs.selectAll('clipPath').data([0]).join('clipPath').attr('id',clipId).selectAll('rect').data([0]).join('rect')
        .attr('x',left).attr('y',top).attr('width',frameW).attr('height',h-top-bottom);
      const gradient=defs.selectAll('linearGradient').data([0]).join('linearGradient').attr('id',clipId+'-fade');
      const stops=[{o:0,a:0},{o:(coreFirst-majorFirst)/(majorLast-majorFirst+1),a:1},{o:(coreLast-majorFirst+1)/(majorLast-majorFirst+1),a:1},{o:1,a:0}];
      gradient.selectAll('stop').data(stops).join('stop').attr('offset',d=>100*d.o+'%').attr('stop-color','var(--viz-series-1)').attr('stop-opacity',d=>d.a);
      const active=layers.filter(l=>l.last>=state.first&&l.first<state.first+state.count);
      const groups=svg.selectAll('g.context-layer').data(active,l=>l.kind).join('g').attr('class',l=>'context-layer '+l.kind+'-layer').attr('clip-path',`url(#${clipId})`);
      groups.each(function(l){
        const yTop=volume?scale(l.maxV/1e6):scale(l.hi),yBottom=volume?scale(0):scale(l.lo);
        d3.select(this).selectAll('rect.context-fill').data([l]).join('rect').attr('class','context-fill '+l.kind+'-fill')
          .attr('x',x(l.first-.5)).attr('width',x(l.last+.5)-x(l.first-.5)).attr('y',yTop).attr('height',yBottom-yTop)
          .attr('data-display-only',l.kind==='major'?'MONTH_CONTEXT_ENVELOPE_ONLY':'LOCAL_TIME_VERIFIED_DISPLAY_ONLY')
          .attr('fill',l.kind==='major'?`url(#${clipId}-fade)`:l.color).attr('fill-opacity',l.opacity).attr('stroke','none');
      });
      groups.lower();svg.select('g.marks').attr('clip-path',`url(#${clipId})`);
    }
'''
s=s[:a]+layer+s[b:]
a=s.index('    const references=');b=s.index('    root.dataset.first=',a)
s=s[:a]+'''    const references=[{price:27.30,kind:'latest',color:'var(--foreground)'},{price:35.50,kind:'legacy-g1',color:'var(--viz-series-1)'},{price:26.95,kind:'jan27',color:'var(--foreground)'}];
    const inAxis=references.filter(r=>r.price>=py.domain()[0]&&r.price<=py.domain()[1]);
    px.selectAll('line.reference').data(inAxis,r=>r.kind).join('line').attr('class',r=>'reference '+r.kind)
      .attr('x1',left).attr('x2',width-right).attr('y1',r=>py(r.price)).attr('y2',r=>py(r.price))
      .attr('stroke',r=>r.color).attr('stroke-width',1).attr('stroke-dasharray',r=>r.kind==='latest'?null:'4 4');
    const points=[{i:legacyG1,price:35.50,kind:'legacy-g1',label:'原G1',color:'var(--viz-series-1)'},
      {i:repeatHigh,price:35.45,kind:'repeat-high',label:'3/12',color:'var(--viz-series-1)'},
      {i:regionHigh,price:31.40,kind:'local-rep',label:'5/13',color:'var(--viz-series-2)'},
      {i:g2,price:26.95,kind:'jan27',label:'1/27',color:'var(--foreground)'}].filter(p=>p.i>=state.first&&p.i<state.first+state.count);
    px.selectAll('circle.source-point').data(points,p=>p.kind).join('circle').attr('class',p=>'source-point '+p.kind)
      .attr('cx',p=>x(p.i)).attr('cy',p=>py(p.price)).attr('r',4).attr('fill',p=>p.color);
    px.selectAll('text.source-label').data(points,p=>p.kind).join('text').attr('class','source-label')
      .attr('x',p=>Math.min(width-right-32,Math.max(left+6,x(p.i)+6)))
      .attr('y',p=>Math.max(top+14,py(p.price)-8)).text(p=>p.label);
    root.querySelector('.range').textContent=`${shown[0].date}～${shown.at(-1).date}｜${state.count}根｜主帶月份約略／局部代表已確認${inAxis.some(r=>r.kind==='latest')?'':'｜27.30在軸外'}`;
    root.dataset.majorPriority='USER_REPORTED';root.dataset.localRepresentative='2025-05-13/31.40';
'''+s[b:]
s=s.replace("case 'g2':setWindow(initial.first,initial.count);choose(regionEnd);break;","case 'g2':setWindow(initial.first,initial.count);choose(legacyG1);break;")
s=s.replace("case 'recent':setWindow(bars.length-40,40);choose(bars.length-1);break;","case 'recent':setWindow(indexOf('2026-01-02'),bars.length-indexOf('2026-01-02'));choose(bars.length-1);break;")
s=s.replace("case 'background':setWindow(indexOf('2024-09-02'),indexOf('2025-06-13')-indexOf('2024-09-02')+1);choose(regionEnd);break;","case 'background':setWindow(initial.first,bars.length-initial.first);choose(bars.length-1);break;")
a=s.index("  root.querySelectorAll('[data-ref-date]').forEach(button=>button.addEventListener");b=s.index('  new ResizeObserver',a);s=s[:a]+s[b:]
s=s.replace('detail(regionHigh);draw(false);','detail(legacyG1);draw(false);')
assert 'data-ref-date=' not in s and 'NOT_SELECTED' not in s and 'data.assistant_candidate' not in s
Path(args.fragment).write_text(s);(out/'discussion_fragment.html').write_text(s);(out/'source.json').write_text(json.dumps(data,ensure_ascii=False,indent=2))
facts={'status':'PASS_SOURCE_BINDING_AND_CONTEXT_ONLY','parent_sha256':hashlib.sha256(parent).hexdigest(),'fragment_sha256':hashlib.sha256(s.encode()).hexdigest(),'all1213_bars_equal_parent':data['bars']==old['bars'],'source_frame_basis_analysis_equal':all(data[k]==old[k] for k in ['source_id','frame_id','chart_base','analysis_as_of']),'local_display_39_equal_parent':data['region_display']==old['region_display'],'local_representative_confirmed':data['user_region']['user_selected_representative'],'major_pressure_band':data['major_pressure_band'],'major_display':data['major_display'],'full_month_context_is_user_exact_boundaries':False,'source_records':[by[d] for d in ['2023-06-05','2023-11-28','2025-03-12','2025-04-07','2025-05-13','2026-01-27','2026-10-16']],'original_g1_reassigned_as_major_band_unique_rep':False,'original_phone_json_reread':False,'new_product_version':False}
(out/'source_verification.json').write_text(json.dumps(facts,ensure_ascii=False,indent=2));print(json.dumps({'bytes':len(s.encode()),'sha256':facts['fragment_sha256'],'context_records':len(context)}))
