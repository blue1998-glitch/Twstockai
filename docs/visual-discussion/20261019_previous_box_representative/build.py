from pathlib import Path
from decimal import Decimal as D
import json,re,hashlib,argparse
ap=argparse.ArgumentParser();ap.add_argument('--template',default='/workspace/reviewed-previous-box.html');ap.add_argument('--out',default='box-reference/publish/docs/visual-discussion/20261019_previous_box_representative');ap.add_argument('--fragment',default='/workspace/box-reference-review.html');args=ap.parse_args()
out=Path(args.out);out.mkdir(parents=True,exist_ok=True)
parent=Path(args.template).read_bytes();assert hashlib.sha256(parent).hexdigest()=='3115a5c4e16328269640d5bf8c94337bd6a7d0735cd8453c273a98ae101f9bc5'
s=parent.decode();data=json.loads(re.search(r'<script type="application/json" class="source">(.*?)</script>',s,re.S).group(1));old=json.loads(json.dumps(data));by={b['date']:b for b in data['bars']}
assert data['user_region']['start']=='2025-04-07' and data['user_region']['end']=='2025-06-02' and data['user_region']['records']==39
data['schema']='previous-box-reference-review/0.1';data['default_view']={'start':'2025-04-01','end':'2025-06-06'}
data['reference_inspection']={'status':'WAITING_FOR_USER_MEANINGFUL_REPRESENTATIVE','user_selected_date':None,'query_buttons_are_case_approval':False,'reference_dates':['2025-04-07','2025-05-13','2025-06-02'],'reference_dates_are_exhaustive_candidates':False,'automatic_max_high_or_volume_rule':None,'notes':'queries only;price peak and volume peak are different;no forced choice or auto classification'}
s=s.replace('reviewed-previous-box','box-reference-review').replace('1101｜前一箱4/7～6/2','1101｜前箱的價峰與量峰')
controls='''  <div class="viz-controls" role="group" aria-label="切換查詢日，不選定案例代表">
    <button class="btn" type="button" data-ref-date="2025-04-07">4/7量峰</button>
    <button class="btn" type="button" data-ref-date="2025-05-13">5/13價峰</button>
    <button class="btn" type="button" data-ref-date="2025-06-02">6/2區間末</button>
  </div>
  <div class="text-small">切換僅查詢價量；整箱代表尚未選定</div>
'''
s=s.replace('  <div class="text-small range tabular-nums"',controls+'  <div class="text-small range tabular-nums"')
s=s.replace('起4/7｜迄6/2｜6/3在區間外（人工判讀）','4/7量峰日｜5/13價峰日｜6/2區間末｜6/3在外')
s=re.sub(r'(<script type="application/json" class="source">).*?(</script>)',lambda m:m[1]+json.dumps(data,ensure_ascii=False,separators=(',',':'))+m[2],s,flags=re.S)
s=s.replace('selected:regionEnd,guide:null','selected:regionHigh,guide:null')
s=s.replace("{i:regionStart,price:29.20,kind:'range-start',label:'起'}","{i:regionStart,price:30.80,kind:'volume-date',label:'4/7'}")
s=s.replace("{i:regionHigh,price:31.40,kind:'range-high',label:'高'}","{i:regionHigh,price:31.40,kind:'price-date',label:'5/13'}")
s=s.replace("{i:regionEnd,price:27.65,kind:'range-low',label:'迄'}","{i:regionEnd,price:27.65,kind:'range-low',label:'低'}, {i:regionEnd,price:29.05,kind:'end-date',label:'6/2'}")
s=s.replace("    root.dataset.selectedDate=b.date;","    root.dataset.selectedDate=b.date;\n    root.querySelectorAll('[data-ref-date]').forEach(button=>button.setAttribute('aria-pressed',String(button.dataset.refDate===b.date)));")
s=s.replace('  new ResizeObserver',"  root.querySelectorAll('[data-ref-date]').forEach(button=>button.addEventListener('click',()=>{\n    setWindow(initial.first,initial.count,false);choose(indexOf(button.dataset.refDate));\n  }));\n  root.dataset.caseRepresentative='NOT_SELECTED';\n  new ResizeObserver")
s=s.replace('detail(regionEnd);draw(false);','detail(regionHigh);draw(false);')
Path(args.fragment).write_text(s);(out/'discussion_fragment.html').write_text(s)
(out/'source.json').write_text(json.dumps(data,ensure_ascii=False,indent=2))
facts={'status':'PASS_SOURCE_COMPARISON_ONLY','parent_fragment_sha256':hashlib.sha256(parent).hexdigest(),'fragment_sha256':hashlib.sha256(s.encode()).hexdigest(),'all1213_bars_equal_parent':data['bars']==old['bars'],'source_frame_basis_analysis_equal':all(data[k]==old[k] for k in ['source_id','frame_id','chart_base','analysis_as_of']),'user_range_and_display_equal_parent':data['user_region']==old['user_region'] and data['region_display']==old['region_display'],'reference_records':[by[d] for d in data['reference_inspection']['reference_dates']],'apr7_to_may13_daily_volume_ratio':str(D(by['2025-04-07']['volume_shares_scaled'])/D(by['2025-05-13']['volume_shares_scaled'])),'ratio_is_priority_weight':False,'max_high_day_is_automatically_representative':False,'max_volume_day_is_automatically_representative':False,'chosen_representative':None,'original_phone_json_reread':False,'latest_saved_record':by['2026-10-16'],'new_product_version':False}
(out/'source_verification.json').write_text(json.dumps(facts,ensure_ascii=False,indent=2));print(json.dumps({'bytes':len(s.encode()),'sha256':facts['fragment_sha256'],'range_records':data['user_region']['records'],'representative':None}))
