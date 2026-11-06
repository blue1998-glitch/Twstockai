// Display-only 0.2. All dates/prices/relations/states come from retained outputs.
const p03ReadableVersion='p03-existing-chart/0.2';
p03Names.ORIGINAL_BOX_UPPER='原突破參照（研究上緣）';
p03Names.PULLBACK_HIGH='返回階段高點';
p03Names.ORIGINAL_BOX_FLOOR='研究下緣';
const p03ReadableStyle=document.createElement('style');
p03ReadableStyle.textContent=`
#chartWrap #chart{height:clamp(500px,64dvh,760px);min-height:500px}
#panelZoom{flex-direction:row;width:90px;height:44px;right:3px;gap:2px}
#panelZoom button{flex:0 0 44px}
#p03Bar p{font-size:13px;line-height:1.5}#p03Bar button{font-size:13px;min-height:44px}
#p03References{display:flex;gap:5px;flex-wrap:wrap}.p03RefChip{padding:3px 6px;border:1px solid;border-radius:4px}
#p03Volume{color:#d2ddeb}#p03Auxiliary{color:#bdcfe0}
#p03Events{margin:7px 0;padding:8px;border:1px solid #4b647c;border-radius:6px}
#p03Events h3{font-size:14px;margin:0 0 4px}#p03Events>p{margin:4px 0;font-size:12px}
#p03EventRows{display:grid;grid-template-columns:repeat(auto-fit,minmax(185px,1fr));gap:5px}
.p03EventRow{min-width:0;padding:6px;background:#172638;border-left:3px solid;line-height:1.45}
.p03EventRow p{margin:2px 0;font-size:13px}.p03EventRow b{font-size:14px}
.p03RelationText{color:#cfdfed;font-variant-numeric:tabular-nums}
#p03Provenance summary{min-height:44px;font-size:14px}.p03SourceCard{padding:7px 0;border-bottom:1px solid #3e556e}
.p03SourceCard h4{margin:3px 0;font-size:14px}.p03Dates{display:grid;grid-template-columns:minmax(140px,auto) 1fr;gap:4px 10px;font-size:13px;line-height:1.6}
.p03Dates dt{color:#b7cce1}.p03Dates dd{margin:0;overflow-wrap:anywhere}
#p03Bar .compact{font-size:12px}.p03LineLabel{font-size:12px;min-height:32px}
@media(max-width:500px){main{padding-left:4px;padding-right:4px}#p03State{font-size:16px}#p03Bar{padding:6px}#p03EventRows{grid-template-columns:1fr}.p03EventRow{display:grid;grid-template-columns:124px minmax(0,1fr);gap:2px 6px}.p03EventRow .p03RelationText{grid-column:2;grid-row:1/4}.p03EventRow p{font-size:13px}.p03Dates{grid-template-columns:1fr;gap:0}.p03Dates dd{padding:0 0 5px 9px}#chartWrap #chart{height:62dvh;min-height:500px}.p03LineLabel{font-size:12px}}
@media(orientation:landscape) and (max-height:550px){#chartWrap #chart{height:500px;min-height:500px}}
`;
document.head.append(p03ReadableStyle);
const p03Volume=text('p','',p03Home);p03Volume.id='p03Volume';p03Home.insertBefore(p03Volume,p03Aux);
const p03Events=text('section','',p03Home);p03Events.id='p03Events';$('cursorValues').after(p03Events);
const p03Provenance=text('details','',p03Home);p03Provenance.id='p03Provenance';p03Events.after(p03Provenance);
text('summary','來源日期逐欄（後來研究選取）',p03Provenance);
const p03ProvenanceBody=text('div','',p03Provenance);p03ProvenanceBody.id='p03ProvenanceBody';
function p03DateVisible(value,s){return value&&value<=s.as_of?value:'尚不可知／未保存（不借其他日期）';}
function p03SourceDates(ref,s){
 const r=ref.source_reference,e=ref.semantic.evidence,research=r.source_kind==='RESEARCH_BOUND';
 const dates=research?(e.source_k_dates||[]):[r.occurred_at];
 return [
  ['原價位K日期',dates.filter(d=>d<=s.as_of).join('、')||'截止當時尚不可知'],
  ['候選來源末轉折日',research?p03DateVisible(e.source_end||r.occurred_at,s):'不適用（直接原K）'],
  ['候選確認日',research?p03DateVisible(r.known_on,s):'不適用（直接原K）'],
  ['原值可知日',p03DateVisible(r.known_on,s)],
  ['角色可知日',p03DateVisible(ref.semantic.known_on,s)],
  ['實際後來選取時間',ref.semantic.selected_at||'未知'],
  ['角色資格',ref.semantic.qualification==='RESEARCH_CANDIDATE'?'研究候選；不是正式人工核定':ref.semantic.qualification],
 ];
}
function p03RenderSources(host,s,role=null){host.replaceChildren();
 for(const ref of s.reference_catalog.filter(r=>!role||r.role===role)){
  const card=text('section','',host);card.className='p03SourceCard';card.dataset.role=ref.role;
  text('h4',p03Names[ref.role]+' '+(ref.source_reference.price??'截止當時尚不可用'),card);
  const dl=text('dl','',card);dl.className='p03Dates';
  for(const[label,value]of p03SourceDates(ref,s)){text('dt',label,dl);text('dd',value,dl);}
  const r=ref.source_reference,dates=r.source_kind==='BAR_FIELD'?[r.occurred_at]:(ref.semantic.evidence.source_k_dates||[]);
  for(const date of dates.filter(d=>d<=s.as_of)){const b=text('button','定位原K '+date,card);b.onclick=()=>{$('evidence').hidden=true;locateDate(date);};}
  const facts=s.current.price_facts[ref.role];if(facts)text('p',['close','high','low'].map(k=>`${{close:'收盤',high:'最高',low:'最低'}[k]}：${p03Relation[facts[k].relation]||'不可比'}（差額 ${facts[k].delta??'未知'}）`).join('；'),card);
  rawDetails(card,'原欄位／候選ID、語義及精確JSON',ref);
 }
}
function p03RelationLine(record){return ['ORIGINAL_BOX_UPPER','PULLBACK_HIGH','ORIGINAL_BOX_FLOOR'].map(k=>{
 const f=record.price_facts?.[k]?.close,value=record.role_prices[k];
 return {ORIGINAL_BOX_UPPER:'原突破',PULLBACK_HIGH:'返回高',ORIGINAL_BOX_FLOOR:'研究底'}[k]+' '+(value??'尚不可用')+'：'+(f?p03Relation[f.relation]||'不可比':'當日缺證');
}).join('；');}
function p03RenderEvents(s){p03Events.replaceChildren();text('h3','已保存的事件與結構狀態｜截止 '+(s.as_of||'未選'),p03Events);
 text('p','突破事實與返回後狀態分開；只列截止以前，不代表買賣訊號。',p03Events);
 const rows=text('div','',p03Events);rows.id='p03EventRows';if(!s.source_matched){text('p','此來源沒有相符的明示參照，不借另一股票或基底。',rows);return;}
 const visible=s.events.filter(e=>e.kind==='ORIGINAL_BREAKOUT_CLOSE'||e.kind==='STATE_CHANGED'&&e.date>=p03Data.result.post_breakout_return.known_on);
 const dates=[...new Set(visible.map(e=>e.date))];
 for(const date of dates){const record=s.records.find(r=>r.date===date);if(!record)continue;
  const row=text('article','',rows);row.className='p03EventRow';row.dataset.date=date;row.style.borderColor=p03StateColors[record.state];
  text('b',date+'｜收 '+record.close,row);
  const original=visible.some(e=>e.date===date&&e.kind==='ORIGINAL_BREAKOUT_CLOSE');
  const change=visible.find(e=>e.date===date&&e.kind==='STATE_CHANGED');
  text('p',original?'原突破已記錄':(change?({STRENGTHENING:'轉強',CONSOLIDATING:'整理',WEAKENING:'轉弱',INSUFFICIENT:'證據不足'}[change.from_state]||'起始')+' → '+record.label:record.label),row);
  if(original)text('p','返回後P0-3：'+record.label,row);
  const relation=text('p',p03RelationLine(record)+'。'+record.reasons.map(p03Reason).join('；'),row);relation.className='p03RelationText';
 }
 if(!dates.length)text('p','截止當時尚無已保存的原突破／返回後狀態變更。',rows);
}
const p03OldRenderReadable=p03Render;
p03Render=function(){p03OldRenderReadable();const s=p03Snapshot(),r=s.current,e=r.evidence;
 // The engine's first INSUFFICIENT may begin years before this return context.
 // Keep its original date in JSON, but don't label it as today's breakout date.
 const pending=r.reasons.includes('POST_BREAKOUT_RETURN_NOT_YET_KNOWN');
 p03Title.textContent=(s.as_of||'未選分析日')+'｜'+(s.source_matched?'研究參照下：':'')+r.label+
  (pending?'｜返回後角色尚不可知；原突破另列':r.state_changed_on?'｜結構狀態變更 '+r.state_changed_on:'');
 p03Refs.replaceChildren();if(s.source_matched){for(const k of ['ORIGINAL_BOX_UPPER','PULLBACK_HIGH','ORIGINAL_BOX_FLOOR']){
  const chip=text('button',p03Names[k]+' '+(r.role_prices[k]??'尚不可用'),p03Refs);chip.className='p03RefChip';chip.dataset.role=k;chip.style.color=chip.style.borderColor=p03Colors[k];chip.onclick=()=>p03ShowEvidence(k);
 }}else p03Refs.textContent='此來源／基底沒有相符明示參照，不能套用其他結果。';
 if(s.source_matched){
  const v=e.original_volume,codes=[...(e.supporting||[]),...(e.opposing||[]),...(e.missing||[])];
  const direction=codes.some(c=>c.startsWith('VOLUME_ABOVE'))?'增加':codes.some(c=>c.startsWith('VOLUME_BELOW'))?'減少':codes.some(c=>c.startsWith('VOLUME_EQUAL'))?'相等':'未列可比方向';
  p03Volume.textContent=v?`量觀察：${v.numerator_date} ${v.current_shares??'缺值'}股；較前一保存筆 ${v.denominator_dates?.join('、')||'未知'}（${v.previous_shares??'缺值'}股）${direction}。`:'量觀察：來源缺值。';
  p03Volume.textContent+=' 描述而已，不判好壞；不是整帶代表量、最大量比較或突破資格。';
  const macd=[...(e.supporting||[]),...(e.opposing||[])].filter(c=>c.startsWith('MACD_')).map(c=>c.startsWith('MACD_HISTOGRAM_POSITIVE')?'柱正值':c.startsWith('MACD_HISTOGRAM_NEGATIVE')?'柱負值':c);
  p03Aux.textContent='MACD觀察（原支持／反面描述）：'+(macd.join('、')||'未列／缺值')+'。量與MACD不取消價格過線；缺證：'+(e.missing||[]).map(c=>c.startsWith('RESEARCH_ROLE')?'正式原箱未核定':c.startsWith('HISTORICAL')?'歷史可得未核':c.startsWith('VOLUME:')?'量資料不足':c==='MACD_HISTOGRAM_UNAVAILABLE'?'MACD缺值／暖機':'行動／報酬未驗').join('、');
 }else{p03Volume.textContent='量觀察：沒有同來源結果，不借用另一基底。';}
 p03RenderEvents(s);p03RenderSources(p03ProvenanceBody,s);
};
p03Overlay=function(){p03Geometry={references:[],events:[]};p03Labels.replaceChildren();const s=p03Snapshot();if(!s.source_matched)return;
 const ctx=$('chart').getContext('2d'),g=geometry,p=g.price,y=v=>p.bottom-(Number(v)-g.priceLow)/(g.priceHigh-g.priceLow)*(p.bottom-p.top);
 for(const key of ['ORIGINAL_BOX_UPPER','PULLBACK_HIGH','ORIGINAL_BOX_FLOOR']){
  const value=s.current.role_prices[key];if(value===undefined)continue;const actualY=y(value),inAxis=actualY>=p.top&&actualY<=p.bottom;
  p03Geometry.references.push({role:key,price:value,actualY,inAxis});
  const chip=p03Refs.querySelector('[data-role="'+key+'"]');
  if(!inAxis){if(chip)chip.textContent+=actualY>p.bottom?' ↓價格軸外':' ↑價格軸外';continue;}
  ctx.save();ctx.strokeStyle=p03Colors[key];ctx.setLineDash(key==='ORIGINAL_BOX_UPPER'?[2,4]:[6,3]);ctx.beginPath();ctx.moveTo(g.left,actualY);ctx.lineTo(g.right,actualY);ctx.stroke();ctx.restore();
  const ref=s.reference_catalog.find(r=>r.role===key),r=ref.source_reference,dates=r.source_kind==='BAR_FIELD'?[r.occurred_at]:(ref.semantic.evidence.source_k_dates||[]);
  for(const date of dates){const i=base().bars.findIndex(b=>b.date===date);if(i<view.start||i>view.end||i>frame.index)continue;ctx.save();ctx.strokeStyle=p03Colors[key];ctx.beginPath();ctx.arc(g.price.x(i),actualY,5,0,Math.PI*2);ctx.stroke();ctx.restore();}
 }
 for(const e of s.events.filter(e=>e.kind==='ORIGINAL_BREAKOUT_CLOSE'||e.kind==='STATE_CHANGED'&&e.date>=p03Data.result.post_breakout_return.known_on)){
  const i=base().bars.findIndex(b=>b.date===e.date);if(i<view.start||i>view.end)continue;const px=g.price.x(i),py=y(e.close);if(py<p.top||py>p.bottom)continue;
  ctx.save();ctx.fillStyle=e.kind==='ORIGINAL_BREAKOUT_CLOSE'?'#c8b6ff':p03StateColors[e.to_state];ctx.beginPath();ctx.moveTo(px,py-10);ctx.lineTo(px-5,py-17);ctx.lineTo(px+5,py-17);ctx.closePath();ctx.fill();ctx.restore();
  p03Geometry.events.push({date:e.date,x:px,y:py-12,event_id:e.id,kind:e.kind});
 }
};
p03ShowEvidence=function(role=null,eventDate=null){const s=p03Snapshot(),body=$('evidenceBody');body.replaceChildren();$('evidenceTitle').textContent='P0-3 事件與分欄來源日期';
 text('p',s.as_of+'｜'+s.current.label+'；'+s.current.reasons.map(p03Reason).join('；'),body);
 text('p','真實行情；後來明示研究假設，不是人工核定正式原箱或歷史當時已選訊號。',body);
 text('h3','保留的突破與狀態路徑',body);
 for(const row of $('p03EventRows').children)body.append(row.cloneNode(true));
 if(eventDate)rawDetails(body,'所點日期的保留事件 '+eventDate,s.events.filter(e=>e.date===eventDate));
 const sources=text('div','',body);p03RenderSources(sources,s,role);
 text('h3','量觀察（描述，不判好壞）',body);text('p',p03Volume.textContent,body);text('p',p03Aux.textContent,body);
 rawDetails(body,'原核心supporting／opposing、原量及MACD（原值未改）',s.current.evidence);
 rawDetails(body,'全部保留事件與來源資格（原JSON）',s);$('evidence').hidden=false;
};
p03LegacyToggle.onchange=()=>{document.documentElement.dataset.p03Legacy=p03LegacyToggle.checked?'on':'off';draw();};
// Keep snapshot/schema/IDs identical; only the enclosing display version changes.
const p03ReadableSelected=selected;selected=function(){const r=p03ReadableSelected();r.view_version=p03ReadableVersion;return r;};
window.P03Readability=()=>({version:p03ReadableVersion,events:$('p03Events').innerText,source_dates:$('p03ProvenanceBody').innerText,volume:p03Volume.innerText});
p03Render();if(manualReady)draw();
