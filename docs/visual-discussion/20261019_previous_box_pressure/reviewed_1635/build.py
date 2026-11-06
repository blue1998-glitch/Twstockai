from pathlib import Path
from decimal import Decimal as D
import json,re,hashlib,argparse
ap=argparse.ArgumentParser();ap.add_argument('--template',default='/workspace/previous-box-pressure.html');ap.add_argument('--out',default='reviewed-box/publish/docs/visual-discussion/20261019_previous_box_pressure/reviewed_1635');ap.add_argument('--fragment',default='/workspace/reviewed-previous-box.html');args=ap.parse_args()
out=Path(args.out);out.mkdir(parents=True,exist_ok=True)
parent=Path(args.template).read_bytes();assert hashlib.sha256(parent).hexdigest()=='237bc7d0ec6a4e712829f4d07d403b4a32a20a6ed901e5e4f7f9df1cae679566'
s=parent.decode();source=json.loads(re.search(r'<script type="application/json" class="source">(.*?)</script>',s,re.S).group(1))
bars=source['bars'];by={b['date']:b for b in bars};a=[b for b in bars if '2025-04-07'<=b['date']<='2025-06-02']
assert len(a)==39 and min(D(b['low']) for b in a)==D('27.65') and max(D(b['high']) for b in a)==D('31.40')
source.pop('assistant_candidate');source['schema']='previous-box-reviewed-range/0.1'
source['user_region']={'start':'2025-04-07','end':'2025-06-02','inclusive':True,'records':39,'evidence_type':'USER_REPORTED_EXACT_TIME_RANGE','recorded_at':'2026-10-19T16:35:58+08:00','exact_quote':'4/7到6/2號','year_resolved_from_visible_case':2025,'formal_price_bounds':None,'user_selected_representative':None,'volume_measure_rule':None}
source['region_display']={'display_start':'2025-04-07','display_end':'2025-06-02','records':39,'wick_low':'27.65','wick_high':'31.40','volume_max_shares':118749437,'status':'USER_TIME_RANGE_SOURCE_VERIFIED_DISPLAY_ENVELOPE_ONLY','geometry_is_formal_price_bounds':False,'geometry_role':'full39-row wick envelope and separate single-day-volume envelope for display only'}
source['review_status']='EXACT_PREVIOUS_BOX_TIME_RANGE_REPORTED_SOURCE_VERIFIED'
source['user_reviewed']['previous_box_time_range']=source['user_region']
(out/'source.json').write_text(json.dumps(source,ensure_ascii=False,indent=2))
s=s.replace('previous-box-pressure','reviewed-previous-box')
s=s.replace('1101｜從27.30回看前一箱','1101｜前一箱4/7～6/2')
s=s.replace('候選整理','聚焦此箱').replace('淡底：前箱候選，尚未定界｜實線：已存收27.30','淡底：已確認時間段｜高低外包僅供顯示｜實線：已存收27.30')
s=s.replace('A 4/8低28.45｜B 5/13高31.40｜C 6/3舊箱破底（人工判讀）','起4/7｜迄6/2｜6/3在區間外（人工判讀）')
s=re.sub(r'(<script type="application/json" class="source">).*?(</script>)',lambda m:m[1]+json.dumps(source,ensure_ascii=False,separators=(',',':'))+m[2],s,flags=re.S)
s=s.replace("candidateStart=indexOf('2025-04-08'),candidateEnd=indexOf('2025-05-29'),candidateHigh=indexOf('2025-05-13')","candidateStart=indexOf('2025-04-07'),candidateEnd=indexOf('2025-06-02'),candidateHigh=indexOf('2025-05-13')")
s=s.replace('selected:event,guide:null','selected:candidateEnd,guide:null')
s=s.replace('const candidate=data.assistant_candidate','const region=data.region_display').replace('candidate.','region.').replace('candidateStart','regionStart').replace('candidateEnd','regionEnd').replace('candidateHigh','regionHigh')
s=s.replace('candidate-backdrop','region-backdrop').replace('candidate-fill','region-fill').replace('ASSISTANT_HYPOTHESIS_NOT_USER_APPROVED','USER_TIME_RANGE_SOURCE_VERIFIED_DISPLAY_ENVELOPE_ONLY')
s=s.replace("const points=[{i:regionStart,price:28.45,kind:'candidate-low',label:'A'}, {i:regionHigh,price:31.40,kind:'candidate-high',label:'B'}, {i:event,price:26.55,kind:'old-breakdown',label:'C'}, {i:g2,price:26.95,kind:'representative',label:'1/27'}]","const points=[{i:regionStart,price:29.20,kind:'range-start',label:'起'}, {i:regionEnd,price:27.65,kind:'range-low',label:'迄'}, {i:regionHigh,price:31.40,kind:'range-high',label:'高'}, {i:event,price:26.55,kind:'old-breakdown',label:'破'}, {i:g2,price:26.95,kind:'representative',label:'1/27'}]")
s=s.replace('候選未批准','時間已確認／價界未定').replace('root.dataset.candidateStatus=region.status','root.dataset.regionStatus=region.status')
s=s.replace('choose(event);break;','choose(regionEnd);break;').replace('detail(event);draw(false);','detail(regionEnd);draw(false);')
assert '28.45' not in re.sub(r'<script type="application/json" class="source">.*?</script>','',s,flags=re.S)
assert 'assistant_candidate' not in s and '候選' not in s and 'candidateStart' not in s
Path(args.fragment).write_text(s);(out/'discussion_fragment.html').write_text(s)
report={'status':'PASS_SOURCE_TIME_RANGE','parent_fragment_sha256':hashlib.sha256(parent).hexdigest(),'new_fragment_sha256':hashlib.sha256(s.encode()).hexdigest(),'all1213_bars_and_source_frame_basis_unchanged':True,'analysis_as_of':source['analysis_as_of'],'user_time_range':source['user_region'],'display_envelope':source['region_display'],'start_ohlcv':a[0],'end_ohlcv':a[-1],'high_record':by['2025-05-13'],'low_record':by['2025-06-02'],'max_daily_volume_record':by['2025-04-07'],'jun03_included':False,'jun03_record':by['2025-06-03'],'latest_close':'27.30','latest_below_display_low_by':'0.35','latest_above_jan27_high_by':'0.35','formal_pressure_bounds_established':False,'range_representative_approved':False,'volume_rule_approved':False,'original_phone_json_reread':False,'new_product_version':False}
(out/'source_verification.json').write_text(json.dumps(report,ensure_ascii=False,indent=2));print(json.dumps({'records':len(a),'bytes':len(s.encode()),'sha256':report['new_fragment_sha256']}))
