from pathlib import Path
import json,re,hashlib
import argparse,zipfile
ap=argparse.ArgumentParser();ap.add_argument('--zip',required=True);ap.add_argument('--g1-source',required=True);ap.add_argument('--template',required=True);ap.add_argument('--output-dir',required=True);ap.add_argument('--fragment',required=True);args=ap.parse_args()
r=Path(args.output_dir);r.mkdir(parents=True,exist_ok=True)
zipbytes=Path(args.zip).read_bytes();assert hashlib.sha256(zipbytes).hexdigest()=='ee5362de516d52f43b2d09f76b46c04345fd147a2beced4a32e208fbfaf41212'
html=zipfile.ZipFile(__import__('io').BytesIO(zipbytes)).read('M1_v0_19_soft_regions_v043.html');assert hashlib.sha256(html).hexdigest()=='8f09aff450d03afe88f6893264ecb2ccd0b85928f899c9b60567d1480404b434'
transport=json.loads(re.search(r'id="payload">(.*?)</script>',html.decode(),re.S).group(1));memo={}
def get(i):
 if i not in memo:
  n=transport['nodes'][i];memo[i]=n[1] if n[0]=='s' else [get(j) for j in n[1:]] if n[0]=='a' else {k:get(j) for k,j in n[1:]}
 return memo[i]
payload=get(transport['root'])
series=next(s for s in payload['history_series'] if s['code']=='1101')
basis='sha256:50e560b77640da3b7d000c0db67fc73a3f5b69d0bd744871ccb03483f8ec115e'
bars=series['bases'][basis]['bars'];assert len(bars)==1213
old=json.loads(Path(args.g1_source).read_text());assert series['source']['id']==old['source_id'];assert series['frames'][-1]['frame_id']==old['frame_id'];assert series['frames'][-1]['as_of']==old['analysis_as_of'];by={b['date']:b for b in bars}
assert all(by[b['date']]==b for b in old['overview_bars'])
assert by['2024-01-19']['low']=='31.80'
source={k:old[k] for k in ['source_export_sha256','source_id','frame_id','chart_base','analysis_as_of','code','price_mode']}
source.update(schema='c-right-region-discussion/0.1',bars=bars,C=by['2024-01-19'],review_status='WAITING_FOR_USER_C_RIGHT_END_JUDGMENT',default_view={'start':'2023-11-01','end':'2024-07-31'},exact_new_region_start=None,exact_new_region_end=None)
(r/'c-right-source.json').write_text(json.dumps(source,ensure_ascii=False,indent=2))
s=Path(args.template).read_text().replace('g2-coordinate-query','c-right-region')
s=s.replace('1101｜G2 座標查詢','1101｜C右側的新平緩帶').replace('G2附近','C附近').replace('記終點','記為待回報終點')
s=s.replace('    <button class="btn" type="button" data-endpoint="start">記起點</button>\n','')
s=s.replace('待回報區間（尚未提交）','待回報終點（尚未提交）').replace('起點終點查詢草稿','C右側終點查詢草稿')
s=s.replace('紅漲／綠跌｜Raw｜分析日2026-10-16｜G2約2023年2～8月；精確日待確認','紅漲／綠跌｜1101 Raw｜分析日2026-10-16｜C=2024-01-19；新帶終點未定')
s=re.sub(r'(<script type="application/json" class="source">).*?(</script>)',lambda m:m[1]+json.dumps(source,ensure_ascii=False,separators=(',',':'))+m[2],s,flags=re.S)
s=s.replace("date==='2023-05-02'","date==='2024-01-19'")
s=s.replace("case 'g2':setWindow(g2-48,96);choose(g2);break;","case 'g2':setWindow(initial.first,initial.count);choose(g2);break;")
a=s.index('    const refInAxis=');b=s.index("    root.dataset.first=",a)
s=s[:a]+'''    const cVisible=g2>=state.first&&g2<state.first+state.count;
    px.selectAll('line.c-reference').data(cVisible?[0]:[]).join('line').attr('class','c-reference')
      .attr('x1',x(g2)).attr('x2',x(g2)).attr('y1',top).attr('y2',priceH-bottom)
      .attr('stroke','var(--viz-series-1)').attr('stroke-width',1).attr('stroke-dasharray','4 4');
    px.selectAll('circle.c-source').data(cVisible?[0]:[]).join('circle').attr('class','c-source')
      .attr('cx',x(g2)).attr('cy',py(31.80)).attr('r',4).attr('fill','var(--viz-series-1)');
    px.selectAll('text.c-label').data(cVisible?[0]:[]).join('text').attr('class','c-label')
      .attr('x',Math.max(left+5,Math.min(width-right-65,x(g2)+6))).attr('y',top+14).text('C 1/19');
    root.querySelector('.range').textContent=`${shown[0].date}～${shown.at(-1).date}｜${state.count}根｜僅閱讀窗${cVisible?'':'｜C在畫外'}`;
'''+s[b:]
s=s.replace("root.querySelector('.draft').value=describe('起點',state.draftStart)+'\\n'+describe('終點',state.draftEnd)+\n      (state.draftStart!==null&&state.draftEnd!==null&&state.draftStart>state.draftEnd?'\\n起點晚於終點，請調整。':'');","root.querySelector('.draft').value='狀態：DRAFT_NOT_SUBMITTED_NOT_APPROVED\\n參照C：2024-01-19（不是已定新帶起日）\\n'+describe('待回報終點',state.draftEnd)+(state.draftEnd!==null&&state.draftEnd<g2?'\\n所選日早於C，請調整。':'');")
s=s.replace("root.querySelectorAll('[data-endpoint]').forEach", "root.dataset.draftStatus='DRAFT_NOT_SUBMITTED_NOT_APPROVED';\n  root.querySelectorAll('[data-endpoint]').forEach")
assert 'G2' not in re.sub(r'<script type="application/json" class="source">.*?</script>', '', s, flags=re.S)
out=Path(args.fragment);out.write_text(s)
report={'status':'PASS','frozen_zip_sha256':'ee5362de516d52f43b2d09f76b46c04345fd147a2beced4a32e208fbfaf41212','html_parent_sha256':'8f09aff450d03afe88f6893264ecb2ccd0b85928f899c9b60567d1480404b434','source_export_sha256_reference':source['source_export_sha256'],'original_export_file_reread':False,'source_binding':{k:source[k] for k in ['source_id','frame_id','chart_base','analysis_as_of']},'bars':len(bars),'source_span':[bars[0]['date'],bars[-1]['date']],'original_576_overlap_all_fields_equal':True,'exact_C_record':source['C'],'default_view_is_region_boundary':False,'new_region_end':None,'review_status':source['review_status'],'fragment_bytes':out.stat().st_size,'fragment_sha256':hashlib.sha256(out.read_bytes()).hexdigest()}
(r/'source-verification.json').write_text(json.dumps(report,ensure_ascii=False,indent=2))
print(json.dumps(report,ensure_ascii=False))
