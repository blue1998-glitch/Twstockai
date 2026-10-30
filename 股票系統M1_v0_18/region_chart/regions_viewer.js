// Region meanings/indices come from Python; browser only lays them out and reads
// actual source rows. Draft points are local selections, never approved analysis.
let draftBinding=null,localDraft={start:null,end:null},regionFocus='G1';
const inheritedSelection=selected;
selected=()=>{const value=inheritedSelection();value.schema_version='manual-region-chart-selection/0.1';value.manual_regions=regions;return value;};
function resetDraftForFrame(){const binding=current.key+'|'+frame.frame_id;if(binding!==draftBinding){draftBinding=binding;localDraft={start:null,end:null};}}
function regionById(id){return regions?.regions.find(r=>r.id===id);}
function focusRegion(id){const r=regionById(id);if(!r)return;stop();regionFocus=id;view.start=r.navigation.start;view.end=r.navigation.end;view.cursor=r.navigation.cursor;view.requestedMonths=null;$('evidence').hidden=true;draw();}
function drawRegionBands(ctx,x,y,price,volume,macd,step){
 if(!regions)return;ctx.save();ctx.beginPath();ctx.rect(geometry.left,42,geometry.right-geometry.left,macd.bottom-42);ctx.clip();
 function span(a,b,color,title,uncertain=false){const from=Math.max(view.start,a),to=Math.min(view.end,b);if(from>to)return;
  const left=x(from)-step/2,width=x(to)-x(from)+step;ctx.fillStyle=color;ctx.globalAlpha=uncertain ? .08 : .055;ctx.fillRect(left,price.top,width,macd.bottom-price.top);
  ctx.globalAlpha=.7;ctx.fillRect(left,44,width,4);ctx.globalAlpha=1;ctx.font='10px system-ui';ctx.fillStyle=color;
  const short=width>145?title:width>70?(uncertain?'G1 約9月':title.split(' ')[0]):'';if(short)ctx.fillText(short,left+3,54);
  if(uncertain){ctx.save();ctx.beginPath();ctx.rect(left,price.top,width,macd.bottom-price.top);ctx.clip();ctx.globalAlpha=.25;ctx.strokeStyle=color;for(let a=left-(macd.bottom-price.top);a<left+width;a+=10){ctx.beginPath();ctx.moveTo(a,macd.bottom);ctx.lineTo(a+macd.bottom-price.top,price.top);ctx.stroke();}ctx.restore();}
 }
 const g1=regionById('G1'),g2=regionById('G2'),c=g1.display.c_index;
 span(g2.display.start_index,g2.display.end_index,'#b7a2ef','G2 1/16～8/16');
 span(g1.display.month_first_index,g1.display.month_last_index,'#f3bd7b','G1 約9月起緣',true);
 span(g1.display.month_last_index+1,c,'#f3bd7b','G1 →C');
 // Open-ended qualitative direction uses only a dashed rail, never a shaded
 // assertion that every later bar belongs to a verified flat/settled region.
 if(view.end>=c){const left=x(Math.max(view.start,c))-step/2;ctx.strokeStyle='#8fd6c2';ctx.setLineDash([3,4]);ctx.beginPath();ctx.moveTo(left,46);ctx.lineTo(geometry.right,46);ctx.stroke();ctx.setLineDash([]);ctx.fillStyle='#8fd6c2';ctx.font='10px system-ui';const title=geometry.right-left>175?'C後新帶：終點未定 →':'C後待定 →';if(geometry.right-left>65)ctx.fillText(title,left+3,55);}
 if(c>=view.start&&c<=view.end){const px=x(c),py=y(regions.c_source.low);ctx.strokeStyle='#8fd6c2';ctx.setLineDash([2,4]);ctx.beginPath();ctx.moveTo(px,price.top);ctx.lineTo(px,macd.bottom);ctx.stroke();ctx.setLineDash([]);if(py>=price.top&&py<=price.bottom){ctx.fillStyle='#8fd6c2';ctx.beginPath();ctx.moveTo(px,py-5);ctx.lineTo(px+5,py);ctx.lineTo(px,py+5);ctx.lineTo(px-5,py);ctx.closePath();ctx.fill();hits.push({kind:'pressure',id:'region:C',x:px,y:py,index:c,label:'C 2024-01-19 轉換參照',source:{type:'region',id:'C_RIGHT'}});}}
 ctx.restore();
}
function drawQueryMarker(ctx,x,y,price){const r=base().bars[view.cursor],py=y(r.close);if(py<price.top||py>price.bottom)return;ctx.save();ctx.strokeStyle='#f4f7fa';ctx.lineWidth=1.5;ctx.strokeRect(x(view.cursor)-3,py-3,6,6);ctx.restore();}
function drawRegionVolumeEvidence(ctx,x,volume,maxVol){if(!regions)return;ctx.save();ctx.strokeStyle='#f3bd7b';for(const e of regions.volume_evidence){const i=base().bars.findIndex(r=>r.date===e.bar.date);if(i<view.start||i>view.end)continue;const py=volume.bottom-Number(e.bar.volume_shares_scaled)/maxVol*(volume.bottom-volume.top);ctx.strokeRect(x(i)-3,py-3,6,6);hits.push({kind:'pressure',id:'region:volume:'+e.bar.date,x:x(i),y:py,index:i,label:e.bar.date+' 原量來源（非整區量）',source:{type:'region',id:'G1'}});}ctx.restore();}
function updateRegionTools(){
 $('pointDetails').hidden=!manual;$('regionControls').hidden=!regions;for(const id of ['focusG1','focusG2','focusC','regionEvidence'])$(id).disabled=!regions;
 $('regionStatus').textContent=regions?'人工時間帶｜G1 約9月→C；G2 2023/1/16～8/16；C後終點未定。':'此來源／分析日沒有套用本例人工區域。';
 const r=base().bars[view.cursor],m=base().macd[view.cursor];$('cursorValues').textContent=`${r.date}　開 ${r.open} 高 ${r.high} 低 ${r.low} 收 ${r.close}　量 ${r.volume_shares_scaled??'缺值'} 股　DIF ${fmt(m.dif)} DEA ${fmt(m.dea)} 柱 ${fmt(m.histogram)}`;
 $('queryDate').value=r.date;$('queryPrev').disabled=view.cursor===0;$('queryNext').disabled=view.cursor===frame.index;
 updateDraftView();
}
function queryIndex(index){const i=Math.max(0,Math.min(frame.index,index)),n=view.end-view.start+1;if(i<view.start){view.start=i;view.end=i+n-1;view.requestedMonths=null;}if(i>view.end){view.end=i;view.start=i-n+1;view.requestedMonths=null;}view.cursor=i;draw();}
function draftValue(){return {schema_version:'manual-region-point-draft/0.1',status:'DRAFT_NOT_SUBMITTED_NOT_APPROVED',view_version:data.view_version,
 binding:{code:current.code,price_mode:current.price_mode,source_id:current.source.id,frame_id:frame.frame_id,chart_base:frame.chart_base,analysis_as_of:frame.as_of},
 start:localDraft.start,end:localDraft.end,order:!localDraft.start||!localDraft.end?'PARTIAL':localDraft.start.date<=localDraft.end.date?'FORWARD':'REVERSED_UNRESOLVED',
 persistence:'MEMORY_ONLY_RELOAD_OR_SOURCE_FRAME_CHANGE_CLEARS',case_update:'NONE_REQUIRES_USER_SUBMISSION_AND_REVIEW',action_qualification:'NOT_EVALUATED'};}
function updateDraftView(){$('draftStatus').textContent=`起點：${localDraft.start?.date||'未選'}；終點：${localDraft.end?.date||'未選'}；尚未提交${localDraft.start&&localDraft.end&&localDraft.start.date>localDraft.end.date?'（順序相反，未自動交換）':''}`;$('draftText').value=JSON.stringify(draftValue(),null,2);$('draftDownload').disabled=!localDraft.start&&!localDraft.end;}
function downloadDraft(){const url=URL.createObjectURL(new Blob([JSON.stringify(draftValue(),null,2)],{type:'application/json'})),a=document.createElement('a');a.href=url;a.download=`M1_region_points_DRAFT_${current.code}_${frame.as_of}.json`;a.click();setTimeout(()=>URL.revokeObjectURL(url),10000);}
function openRegion(id=regionFocus){if(!regions)return;regionFocus=id;const r=regionById(id),b=$('evidenceBody');b.replaceChildren();$('evidenceTitle').textContent=r.title;
 text('p',r.id==='G2'?'人工精確時間帶：2023-01-16～2023-08-16，代表點5/2高40.25。':r.id==='G1'?'G1代表價量帶：大約2023年9月→C（2024-01-19）。九月精確起日與K線歸屬未定。':'C右側的新平緩帶是使用者結構判讀；精確起訖未定，不代表所有後續K都已分類為平緩或持股穩定。',b);
 if(r.representative){const row=base().bars.find(b=>b.date===r.representative.source_date);text('p',`代表點 ${row.date} 高 ${row.high}；當日量 ${row.volume_shares_scaled} 股不是整區量。`,b);}
 text('p','2026-10-18後來人工覆核，分析日2026-10-16；不是當時自動訊號。時間帶不是價格上下緣，價格區界／整區量／增量／自動分區／強度衰減仍未定。Raw未完整校正。',b);
 if(id==='G1'){const table=text('table','',b),head=text('tr','',table);for(const t of ['來源日','high','原始股數'])text('th',t,head);for(const row of Object.values(regions.g1_source_facts.exact_source_bars)){const tr=text('tr','',table);for(const v of [row.date,row.high,row.volume_shares_scaled])text('td',v,tr);}text('p','9/14同高35.50仍保留；10/18、11/30量峰各在真實日期，不把G1當日量當整帶。',b);}
 if(id==='G2'){for(const row of [r.endpoints.start,r.endpoints.end]){text('p',`${row.date}　開 ${row.open} 高 ${row.high} 低 ${row.low} 收 ${row.close} 量 ${row.volume_shares_scaled} 股`,b);}}
 const focus=text('button','聚焦此帶（不改分析日）',b);focus.onclick=()=>focusRegion(id);const back=text('button','返回24月',b);back.onclick=()=>{$('evidence').hidden=true;calendarWindow(24);};
 rawDetails(b,'人工原話、資格與來源指紋',regions);$('evidence').hidden=false;
}
const inheritedOpenPressure=openPressure;openPressure=hit=>hit.source.type==='region'?openRegion(hit.source.id):inheritedOpenPressure(hit);
$('focusG1').onclick=()=>focusRegion('G1');$('focusG2').onclick=()=>focusRegion('G2');$('focusC').onclick=()=>focusRegion('C_RIGHT');$('regionEvidence').onclick=()=>openRegion();
$('queryPrev').onclick=()=>queryIndex(view.cursor-1);$('queryNext').onclick=()=>queryIndex(view.cursor+1);$('queryDate').onchange=()=>queryIndex(base().bars.findIndex(r=>r.date===$('queryDate').value));
$('draftStart').onclick=()=>{localDraft.start=JSON.parse(JSON.stringify(base().bars[view.cursor]));updateDraftView();};$('draftEnd').onclick=()=>{localDraft.end=JSON.parse(JSON.stringify(base().bars[view.cursor]));updateDraftView();};$('draftClear').onclick=()=>{localDraft={start:null,end:null};updateDraftView();};$('draftDownload').onclick=downloadDraft;
$('chart').classList.add('query');
