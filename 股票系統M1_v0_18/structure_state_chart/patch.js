// P0-3 presentation only: all states, exact comparisons and events are Python outputs.
const p03Names={PULLBACK_HIGH:'回檔高點',ORIGINAL_BOX_FLOOR:'原箱下緣（研究）',ORIGINAL_BOX_UPPER:'原箱上緣（研究）',SHALLOW_OBSERVATION:'淺回檔觀察線'};
const p03Colors={PULLBACK_HIGH:'#ffcf70',ORIGINAL_BOX_FLOOR:'#7ed9ef',ORIGINAL_BOX_UPPER:'#aba6ff',SHALLOW_OBSERVATION:'#d5a6ff'};
const p03StateColors={STRENGTHENING:'#ffcf70',CONSOLIDATING:'#9ed9ff',WEAKENING:'#ff9cab',INSUFFICIENT:'#b7c9db'};
const p03Relation={ABOVE:'高於',BELOW:'低於',EQUAL:'相等（不是嚴格越過／跌破）'};
const p03Explanation={CLOSE_STRICTLY_ABOVE_PULLBACK_HIGH:'收盤嚴格越過回檔高點',CLOSE_STRICTLY_BELOW_ORIGINAL_BOX_FLOOR:'收盤嚴格跌破原箱下緣',NOT_ABOVE_PULLBACK_HIGH_AND_NOT_BELOW_ORIGINAL_BOX_FLOOR:'未越回檔高點，也未破箱底',POST_BREAKOUT_RETURN_NOT_YET_KNOWN:'返回結構尚不可知',NO_MATCHING_SAVED_STRUCTURE:'此來源／基底／日期沒有相符結構附層',INTERRUPTED_STRUCTURE_CONTEXT:'結構期間資料中斷'};
const p03Home=text('section','',document.querySelector('main'));p03Home.id='p03Bar';
document.querySelector('main').insertBefore(p03Home,$('workspace'));
const p03Toolbar=text('div','',p03Home);p03Toolbar.className='toolbar';
const p03Open=text('button','開啟'+p03Data.result.context.code+'真實研究案例',p03Toolbar);p03Open.id='p03OpenCase';
const p03Info=text('button','狀態與來源證據',p03Toolbar);p03Info.id='p03Evidence';
const p03Title=text('b','',p03Home);p03Title.id='p03State';p03Title.setAttribute('role','status');
const p03Refs=text('p','',p03Home);p03Refs.id='p03References';
const p03Aux=text('p','',p03Home);p03Aux.id='p03Auxiliary';
const p03Note=text('p','研究角色假設；不是人工核定原箱、買賣訊號或已驗獲利。',p03Home);p03Note.className='compact';
const p03Actions=text('div','',p03Home);p03Actions.className='toolbar';
for(const[id,label]of [['p03Wide','廣角24月'],['p03Local','局部放大'],['p03Replay','重播結構狀態'],['p03Download','下載結構JSON']]){const b=text('button',label,p03Actions);b.id=id;}
const p03Labels=text('div','',$('chartWrap'));p03Labels.id='p03LineLabels';
const p03Style=document.createElement('style');p03Style.textContent=`
body{font-family:system-ui,"Noto Sans CJK TC",sans-serif}#p03Bar{border:1px solid #597d9c;border-radius:8px;padding:8px;margin:5px 0}#p03Bar p{margin:4px 0;font-size:12px;overflow-wrap:anywhere}#p03State{display:block;font-size:16px}#p03Bar button{min-height:40px;padding:5px 8px}#p03References{font-variant-numeric:tabular-nums}#p03LineLabels{position:absolute;inset:0;pointer-events:none}.p03LineLabel{position:absolute;pointer-events:auto;font-size:11px;padding:2px 5px;min-height:28px;max-width:145px;background:#142334ed;border-radius:5px;white-space:nowrap}#p03Legacy summary{min-height:32px}#p03Bar .toolbar{margin:2px 0}#manualBasisBar{padding:6px}#manualBasisBar p{font-size:11px}#p03EvidenceBody{overflow-wrap:anywhere}@media(max-width:450px){#p03State{font-size:14px}#p03Bar{padding:5px}.p03LineLabel{font-size:10px;max-width:130px}#p03Bar button{font-size:11px}}`;
document.head.append(p03Style);
// Keep the old annotations operable, folded behind the new task's main chart.
const p03Legacy=text('details','',$('workspace'));p03Legacy.id='p03Legacy';text('summary','原價量區域／人工關卡（保留）',p03Legacy);
const p03LegacyLabel=text('label','疊加舊關卡及區域 ',p03Legacy),p03LegacyToggle=document.createElement('input');p03LegacyToggle.type='checkbox';p03LegacyToggle.id='p03LegacyOverlays';p03LegacyLabel.prepend(p03LegacyToggle);
for(const id of ['regionControls','regionStatus','pointDetails','manualUnavailable'])if($(id))p03Legacy.append($(id));
for(const name of ['drawPressureOverlay','drawRegionBands','drawRegionVolumeBands','drawRegionVolumeEvidence']){
 // Function wrappers keep all legacy calculations/data unchanged and only
 // control whether the old presentation is requested in this new page.
 if(name==='drawPressureOverlay'){const old=drawPressureOverlay;drawPressureOverlay=function(...a){if(p03LegacyToggle.checked)return old(...a);};}
 if(name==='drawRegionBands'){const old=drawRegionBands;drawRegionBands=function(...a){if(p03LegacyToggle.checked)return old(...a);};}
 if(name==='drawRegionVolumeBands'){const old=drawRegionVolumeBands;drawRegionVolumeBands=function(...a){if(p03LegacyToggle.checked)return old(...a);};}
 if(name==='drawRegionVolumeEvidence'){const old=drawRegionVolumeEvidence;drawRegionVolumeEvidence=function(...a){if(p03LegacyToggle.checked)return old(...a);};}
}
const p03LegacyManualOverlay=drawManualOverlay;drawManualOverlay=function(...a){if(p03LegacyToggle.checked)return p03LegacyManualOverlay(...a);$('manualLineLabels').replaceChildren();};
p03LegacyToggle.onchange=()=>draw();
let p03Timer=null,p03Geometry={references:[],events:[]};
function p03Matched(){const b=manualBinding,f=b&&p03Data.frame_map[b.as_of];return manualReady&&b&&f&&b.series_key===p03Data.series_key&&b.code===p03Data.result.context.code&&b.source_id===p03Data.result.context.source_id&&b.price_basis_id===p03Data.result.context.price_basis_id&&b.price_mode===p03Data.result.context.price_mode&&b.adjustment_version===p03Data.result.context.adjustment_version&&b.frame_id===f.frame_id;}
function p03Snapshot(){
 const date=manualIntent?.as_of||null;
 if(!p03Matched())return {schema_version:'p03-chart-snapshot/0.1',as_of:date,source_matched:false,current:{date,state:'INSUFFICIENT',label:'證據不足／不可判定',reasons:['NO_MATCHING_SAVED_STRUCTURE'],price_facts:{},role_prices:{},evidence:{}},records:[],events:[],reference_catalog:[],historical_signal_eligible:false,execution_qualified:false,imputed_close:null,valuation:null,primary_pressure_id:null,policy_authorized:false};
 const r=p03Data.result,records=r.records.filter(x=>x.date<=date),current=structuredClone(records.at(-1)),references=structuredClone(r.reference_catalog);
 for(const ref of references){ref.available_at_as_of=Object.hasOwn(current.role_prices,ref.role);ref.source_reference.price=current.role_prices[ref.role]??null;ref.origin_binding_role='LATER_SELECTION_ARTIFACT_NOT_HISTORICAL_FRAME';}
 return {schema_version:'p03-chart-snapshot/0.1',as_of:date,source_matched:true,source_binding:structuredClone(manualBinding),evaluated_prefix_fingerprint:p03Data.frame_map[date].source_prefix_fingerprint,layer_artifact_id:p03Data.artifact_id,source_qualification:r.source_qualification,current,records:structuredClone(records),events:structuredClone(r.events.filter(e=>e.date<=date)),reference_catalog:references,post_breakout_return:date>=r.post_breakout_return.known_on?structuredClone(r.post_breakout_return):{qualification:'NOT_YET_AVAILABLE'},historical_signal_eligible:false,execution_qualified:false,imputed_close:null,valuation:null,primary_pressure_id:null,policy_authorized:false,classification_quality:'NOT_VALIDATED',physical_android:'NOT_TESTED_NEW_BUILD'};
}
function p03Reason(reason){if(p03Explanation[reason])return p03Explanation[reason];if(reason.startsWith('ROLE_UNAVAILABLE'))return '參照角色尚不可知或已失效';if(reason.startsWith('INTERRUPTED_STRUCTURE'))return '結構期間資料中斷，不沿用舊參照';if(reason.startsWith('EQUAL_'))return '相等邊界獨立保留';return reason;}
function p03Render(){const s=p03Snapshot(),r=s.current;p03Title.style.color=p03StateColors[r.state];p03Title.textContent=`${s.as_of||'未選分析日'}｜${s.source_matched?'研究參照下：':''}${r.label}${r.state_changed_on?'｜變更 '+r.state_changed_on:''}`;
 p03Refs.textContent=s.source_matched?['PULLBACK_HIGH','ORIGINAL_BOX_FLOOR'].map(k=>`${p03Names[k]} ${r.role_prices[k]??'尚不可用'}`).join('　')+'｜'+r.reasons.map(p03Reason).join('；'):'請選擇模式／來源，或按「開啟真實研究案例」；其他股票或還原基底不擅套本案例。';
 const e=r.evidence,word=x=>x.startsWith('VOLUME_ABOVE')?'量較前筆多（描述）':x.startsWith('VOLUME_BELOW')?'量較前筆少（不否定過線）':x.startsWith('MACD_HISTOGRAM_POSITIVE')?'MACD柱正值':x.startsWith('MACD_HISTOGRAM_NEGATIVE')?'MACD柱負值':x.startsWith('VOLUME:')?'量資料不足':x==='MACD_HISTOGRAM_UNAVAILABLE'?'MACD缺值／暖機':x.startsWith('RESEARCH_ROLE')?'正式原箱未核定':x.startsWith('HISTORICAL')?'歷史可得未核':'行動／報酬未驗';
 p03Aux.textContent=s.source_matched?'支持：'+(e.supporting.map(word).join('、')||'無已列支持')+'｜反面：'+(e.opposing.map(word).join('、')||'無已列反面')+'｜缺證：'+e.missing.map(word).join('、'):'支持／反面／缺證須依相符保存來源查看，不借用另一基底的結果。';
 for(const id of ['p03Wide','p03Local','p03Replay'])$(id).disabled=!s.source_matched;
}
function p03Overlay(){p03Geometry={references:[],events:[]};p03Labels.replaceChildren();const s=p03Snapshot();if(!s.source_matched)return;
 const c=$('chart'),ctx=c.getContext('2d'),g=geometry,p=g.price,y=v=>p.bottom-(Number(v)-g.priceLow)/(g.priceHigh-g.priceLow)*(p.bottom-p.top),taken=[];
 for(const key of ['PULLBACK_HIGH','ORIGINAL_BOX_FLOOR']){const value=s.current.role_prices[key];if(value===undefined)continue;const actualY=y(value),inAxis=actualY>=p.top&&actualY<=p.bottom;
  p03Geometry.references.push({role:key,price:value,actualY,inAxis});if(!inAxis){p03Refs.textContent+=`｜${p03Names[key]}${value}${actualY>p.bottom?' ↓價格軸外':' ↑價格軸外'}`;continue;}
  ctx.save();ctx.strokeStyle=p03Colors[key];ctx.setLineDash([6,3]);ctx.beginPath();ctx.moveTo(g.left,actualY);ctx.lineTo(g.right,actualY);ctx.stroke();ctx.restore();
  let labelY=Math.max(p.top,Math.min(p.bottom-28,actualY-14));if(taken.some(v=>Math.abs(v-labelY)<30))labelY=Math.max(p.top,labelY-31);taken.push(labelY);
  const b=text('button',`${key==='PULLBACK_HIGH'?'回檔高':'研究箱底'} ${value}`,p03Labels);b.className='p03LineLabel';b.dataset.role=key;b.dataset.price=value;b.style.left=(g.left+3)+'px';b.style.top=labelY+'px';b.style.borderColor=b.style.color=p03Colors[key];b.onclick=e=>{e.stopPropagation();p03ShowEvidence(key);};
  const ref=s.reference_catalog.find(r=>r.role===key),dates=ref.source_reference.source_kind==='BAR_FIELD'?[ref.source_reference.occurred_at]:(ref.semantic.evidence.source_k_dates||[]);
  for(const date of dates){const i=base().bars.findIndex(r=>r.date===date);if(i<view.start||i>view.end||i>frame.index)continue;ctx.save();ctx.strokeStyle=p03Colors[key];ctx.beginPath();ctx.arc(g.price.x(i),actualY,5,0,Math.PI*2);ctx.stroke();ctx.restore();}
 }
 for(const e of s.events.filter(e=>e.kind==='ORIGINAL_BREAKOUT_CLOSE'||e.kind==='STATE_CHANGED'&&e.date>=p03Data.result.post_breakout_return.known_on)){const i=base().bars.findIndex(r=>r.date===e.date);if(i<view.start||i>view.end)continue;const px=g.price.x(i),py=y(e.close);if(py<p.top||py>p.bottom)continue;ctx.save();ctx.fillStyle=e.kind==='ORIGINAL_BREAKOUT_CLOSE'?'#c8b6ff':p03StateColors[e.to_state];ctx.beginPath();ctx.moveTo(px,py-10);ctx.lineTo(px-5,py-17);ctx.lineTo(px+5,py-17);ctx.closePath();ctx.fill();ctx.restore();p03Geometry.events.push({date:e.date,x:px,y:py-12,event_id:e.id,kind:e.kind});}
}
function p03ShowEvidence(role=null,eventDate=null){const s=p03Snapshot(),body=$('evidenceBody');body.replaceChildren();$('evidenceTitle').textContent='P0-3 結構狀態與參照來源';
 text('p',`${s.as_of}｜${s.current.label}；${s.current.reasons.map(p03Reason).join('；')}`,body);
 text('p','真實OHLCV；參照角色是本次後來明示的研究假設，不是人工核定正式原箱，也不是歷史已選訊號。',body);
 const labels={STRENGTHENING:'轉強',CONSOLIDATING:'整理',WEAKENING:'轉弱',INSUFFICIENT:'證據不足'};
 text('h3','保留的突破與狀態路徑',body);
 for(const event of s.events.filter(e=>e.kind==='ORIGINAL_BREAKOUT_CLOSE'||e.kind==='STATE_CHANGED'&&e.date>=p03Data.result.post_breakout_return.known_on))text('p',event.date+'｜'+(event.kind==='ORIGINAL_BREAKOUT_CLOSE'?'最初收盤越過研究原箱上緣（後來返回仍保留）':(labels[event.from_state]||'起始')+' → '+labels[event.to_state]+'：'+event.reasons.map(p03Reason).join('；')),body);
 if(eventDate){const e=s.events.filter(e=>e.date===eventDate);rawDetails(body,'所點日期的保留事件 '+eventDate,e);}
 for(const ref of s.reference_catalog.filter(r=>!role||r.role===role)){const r=ref.source_reference;text('h3',p03Names[ref.role]+' '+(r.price??'尚不可用'),body);text('p',`原值發生／候選來源末轉折 ${r.occurred_at}；原值可知 ${r.known_on}；角色可知 ${ref.semantic.known_on}；本次選取 ${ref.semantic.selected_at}。資格 ${ref.semantic.qualification}。`,body);
  const dates=r.source_kind==='BAR_FIELD'?[r.occurred_at]:(ref.semantic.evidence.source_k_dates||[]);for(const date of dates){const b=text('button','定位原K '+date,body);b.onclick=()=>{$('evidence').hidden=true;locateDate(date);};}
  const facts=s.current.price_facts[ref.role];if(facts)for(const field of ['close','high','low'])text('p',`${{close:'收盤',high:'最高',low:'最低'}[field]}：${p03Relation[facts[field].relation]||'不可比'}；差額 ${facts[field].delta??'未知'}。`,body);
  rawDetails(body,'語義依據、來源／候選ID及精確JSON',ref);
 }
 text('h3','支持／反面／缺證（不覆寫過線事實）',body);rawDetails(body,'原量、MACD與價格事實',s.current.evidence);rawDetails(body,'全部保留事件及來源資格',s);$('evidence').hidden=false;
}
const p03OldDraw=draw,p03OldApply=manualApply,p03OldSelected=selected;
draw=function(){p03OldDraw();p03Render();if(manualReady)p03Overlay();};
manualApply=function(q,persist=true){p03OldApply(q,persist);p03Render();if(!manualReady){p03Labels.replaceChildren();p03Geometry={references:[],events:[]};}};
selected=function(){const r=p03OldSelected();r.schema_version='p03-manual-chart-selection/0.1';r.view_version='p03-existing-chart/0.1';r.structure_state=p03Snapshot();return r;};
window.manualBasisExport=()=>selected();window.P03Export=()=>selected();window.P03Inspect=()=>({snapshot:p03Snapshot(),view:{...view},geometry:structuredClone(p03Geometry),chartGeometry:{left:geometry.left,right:geometry.right,width:geometry.width,priceLow:geometry.priceLow,priceHigh:geometry.priceHigh,panes_share_axis:!!geometry.price&&geometry.price.x===geometry.volume.x&&geometry.price.x===geometry.macd.x,pane_cursor_x:geometry.price?[geometry.price.x(view.cursor),geometry.volume.x(view.cursor),geometry.macd.x(view.cursor)]:[]},series_key:current?.key,ready:manualReady});
p03Open.onclick=()=>{manualUpdate({code:p03Data.result.context.code,price_mode:p03Data.result.context.price_mode,as_of:p03Data.case.display.analysis_date,series_key:p03Data.series_key});$('p03Bar').scrollIntoView({block:'start'});};
p03Info.onclick=()=>p03ShowEvidence();$('p03Wide').onclick=()=>calendarWindow(24);$('p03Local').onclick=()=>{const i=base().bars.findIndex(r=>r.date===p03Data.case.display.local_start);view.start=Math.max(0,Math.min(i,frame.index));view.end=frame.index;view.cursor=frame.index;view.requestedMonths=null;draw();};
$('p03Replay').onclick=()=>{if(p03Timer){clearInterval(p03Timer);p03Timer=null;$('p03Replay').textContent='重播結構狀態';return;}const days=p03Data.result.records.filter(r=>r.date>=p03Data.result.post_breakout_return.known_on).map(r=>r.date);let i=0;manualUpdate({as_of:days[i]});$('p03Replay').textContent='停止重播';p03Timer=setInterval(()=>{if(!p03Matched()||++i>=days.length){clearInterval(p03Timer);p03Timer=null;$('p03Replay').textContent='重播結構狀態';return;}manualUpdate({as_of:days[i]});},1000);};
$('p03Download').onclick=manualDownload;
$('chart').addEventListener('click',e=>{const r=$('chart').getBoundingClientRect(),x=e.clientX-r.left,y=e.clientY-r.top,hit=p03Geometry.events.find(p=>Math.hypot(x-p.x,y-p.y)<12);if(hit)p03ShowEvidence(null,hit.date);});
p03Render();if(manualReady)draw();
