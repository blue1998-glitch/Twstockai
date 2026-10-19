from pathlib import Path
import json,re,hashlib,argparse
ap=argparse.ArgumentParser();ap.add_argument('--template',required=True);ap.add_argument('--source',required=True);ap.add_argument('--output',required=True);a=ap.parse_args();root=Path(__file__).resolve().parent
source=json.loads(Path(a.source).read_text());s=Path(a.template).read_text();parent=json.loads(re.search(r'<script type="application/json" class="source">(.*?)</script>',s,re.S).group(1));assert source['bars']==parent['bars'];assert all(source[k]==parent[k] for k in ['source_id','frame_id','chart_base','analysis_as_of'])
for b in source['draft_boxes']:
 rows=[r for r in source['bars'] if b['start']<=r['date']<=b['end']];from decimal import Decimal
 assert min(Decimal(r['low']) for r in rows)==Decimal(b['low']) and max(Decimal(r['high']) for r in rows)==Decimal(b['high']) and len(rows)==b['records']
s=s.replace('c-right-region','box-range-comparison').replace('1101｜C右側的新平緩帶','1101｜箱型分段對照（助手草案）').replace('C附近','看全段')
s=re.sub(r'    <button[^\n]*data-endpoint="end"[^\n]*\n','',s)
s=re.sub(r'  <label class="form-label draft-label".*?</label>\n','',s,flags=re.S)
s=s.replace('  <div class="text-small range', (root/'box_controls.html').read_text()+'\n  <div class="text-small range',1)
s=s.replace('C=2024-01-19；新帶終點未定','A／B為助手分箱草案；日期與價格為同源實值')
s=re.sub(r'(<script type="application/json" class="source">).*?(</script>)',lambda m:m[1]+json.dumps(source,ensure_ascii=False,separators=(',',':'))+m[2],s,flags=re.S)
s=s.replace("date==='2024-01-19'","date==='2024-03-19'").replace("mode:'query',draftStart:null,draftEnd:null","mode:'query',boxMode:'whole'")
i=s.index('  function draft(){');j=s.index('  function axes(',i);s=s[:i]+s[j:]
i=s.index('    const cVisible=');j=s.index('    root.dataset.first=',i)
s=s[:i]+"    root.querySelector('.range').textContent=`${shown[0].date}～${shown.at(-1).date}｜${state.count}根｜同一段走勢`;\n"+s[j:]
s=s.replace("    const marks=px.select('g.marks');","    paintBoxes();\n    const marks=px.select('g.marks');")
s=s.replace('    guides();\n  }\n  const pointers=', '    paintBoxEvidence();\n    guides();\n  }\n  const pointers=',1)
i=s.index("  root.dataset.draftStatus=");j=s.index('  new ResizeObserver',i);s=s[:i]+(root/'box_layer.js').read_text()+'\n'+s[j:]
s=s.replace("data-action=\"g2\"","data-action=\"home\"").replace("case 'g2':","case 'home':")
assert '平緩' not in s and 'data-endpoint' not in s
Path(a.output).write_text(s)
report={'status':'PASS','1213_bars_exactly_equal_parent':True,'source_frame_basis_equal':True,'draft_extents_match_all_selected_wicks':True,'formal_user_box_bounds':None,'draft_status':'ASSISTANT_COMPARISON_HYPOTHESIS_NOT_USER_APPROVED','fragment_bytes':len(s.encode()),'fragment_sha256':hashlib.sha256(s.encode()).hexdigest(),'analysis_as_of':source['analysis_as_of']}
(root/'build-verification.json').write_text(json.dumps(report,ensure_ascii=False,indent=2));print(json.dumps(report))
