// Routing and local choice records only. Prices/indicators/regions remain frozen.
const manualKeys=['series_key','code','price_mode','as_of','source_id','price_basis_id','frame_id','adjustment_version'];
const manualParentSetup=setupStock,manualParentFrame=setFrame,manualParentDraw=draw,manualParentSelected=selected;
let manualReady=false,manualLoading=false,manualIntent=null,manualBinding=null,manualStatus='REQUIRES_MODE',manualStorageNote='';
const manualPrefix='twstock-manual-basis-v01:'+manualCatalogue.catalogue_id+':';
const bar=document.createElement('section');bar.id='manualBasisBar';bar.className='toolbar';
const title=text('b','人工分析模式',bar),modeLabel=text('label','模式 ',bar),manualMode=document.createElement('select');
manualMode.id='analysisMode';manualMode.setAttribute('aria-label','人工分析模式');
setOptions(manualMode,[['','請選擇'],['RAW_CANDIDATE','原始日 K'],['ADJUSTED_CANDIDATE','還原 K（研究候選）']],'');modeLabel.append(manualMode);
const dateLabel=text('label','分析日 ',bar),manualDate=document.createElement('input');manualDate.type='date';manualDate.id='manualDate';manualDate.setAttribute('aria-label','指定分析日期');dateLabel.append(manualDate);
const lastButton=text('button','使用最後保存日',bar);lastButton.id='manualLastDate';
const downloadChoice=text('button','下載選擇紀錄',bar);downloadChoice.id='downloadChoice';
const statusBox=text('p','',bar);statusBox.id='manualModeStatus';statusBox.setAttribute('role','status');
const storageBox=text('p','',bar);storageBox.id='manualStorageStatus';
document.querySelector('main').prepend(bar);
const style=document.createElement('style');style.textContent='#manualBasisBar{border:1px solid #476582;padding:10px;margin-bottom:8px;flex-wrap:wrap}#manualBasisBar p{flex-basis:100%;margin:2px 0;overflow-wrap:anywhere}#manualBasisBar input{max-width:145px;min-height:34px}#manualBasisBar button{min-height:38px}body.manualModeBlocked #workspace,body.manualModeBlocked #details{display:none}#manualModeStatus{color:#ffd58a}';document.head.append(style);

function manualRows(q){return manualCatalogue.entries.filter(r=>r.code===q.code&&r.price_mode===q.price_mode&&(!q.series_key||r.series_key===q.series_key));}
function manualResolution(q){
 if(!q.price_mode)return {status:'REQUIRES_MODE',binding:null};
 const rows=manualRows(q).filter(r=>r.as_of===q.as_of);
 if(!rows.length)return {status:'UNAVAILABLE',binding:null};
 if(rows.length>1)return {status:'REQUIRES_SOURCE',binding:null};
 return {status:'READY_SAVED_RESEARCH',binding:Object.fromEntries(manualKeys.map(k=>[k,rows[0][k]]))};
}
function manualValid(q){const day=typeof q?.as_of==='string'?new Date(q.as_of):new Date(NaN);return q&&Object.keys(q).length===7&&q.schema_version==='manual-basis-request/0.1'&&typeof q.selection_id==='string'&&/^[A-Za-z0-9_-]{1,80}$/.test(q.selection_id)&&series.some(s=>s.code===q.code)&&[null,'RAW_CANDIDATE','ADJUSTED_CANDIDATE'].includes(q.price_mode)&&/^\d{4}-\d{2}-\d{2}$/.test(q.as_of)&&Number.isFinite(day.getTime())&&day.toISOString().slice(0,10)===q.as_of&&typeof q.selected_at==='string'&&/(Z|[+-]\d\d:\d\d)$/.test(q.selected_at)&&Number.isFinite(Date.parse(q.selected_at))&&(q.series_key===null||typeof q.series_key==='string'&&q.series_key.length>0);}
function manualStore(){
 try{
  const record={catalogue_id:manualCatalogue.catalogue_id,request:manualIntent};
  const key=manualPrefix+'record:'+manualIntent.selection_id;
  if(localStorage.getItem(key)!==null)throw Error('選擇紀錄識別碼衝突');
  localStorage.setItem(key,JSON.stringify(record));localStorage.setItem(manualPrefix+'latest',key);
  manualStorageNote='已記在此瀏覽器；不等於雲端保存。可下載 JSON 留存／交給獨立資料層。';
 }catch(e){manualStorageNote='本機保存未完成：'+e.message+'。目前選擇仍可下載，未宣稱已保存。';}
 storageBox.textContent=manualStorageNote;
}
function manualApply(q,persist=true){
 if(!manualValid(q))throw Error('選擇紀錄格式不符');
 stop();manualReady=false;manualIntent=structuredClone(q);manualBinding=null;
 manualMode.value=q.price_mode||'';manualDate.value=q.as_of;$('stock').value=q.code;
 const sourceRows=manualCatalogue.entries.filter(r=>r.code===q.code&&r.price_mode===q.price_mode);
 const sources=[...new Map(sourceRows.map(r=>[r.series_key,r])).values()];
 const result=manualResolution(q);manualStatus=result.status;manualBinding=result.binding;
 const activeKey=result.binding?.series_key||q.series_key||'';
 setOptions($('mode'),[['','請選資料來源'],...sources.map(r=>[r.series_key,r.kind==='NEW_OFFICIAL_RAW_HISTORY'?'五年官方原始日 K':'原保存研究資料（較短期間）'])],activeKey);
 $('mode').disabled=!sources.length;
 const available=manualRows(q).map(r=>r.as_of).sort();lastButton.disabled=!available.length;
 document.body.classList.toggle('manualModeBlocked',manualStatus!=='READY_SAVED_RESEARCH');$('focus').disabled=manualStatus!=='READY_SAVED_RESEARCH';
 if(manualStatus==='READY_SAVED_RESEARCH'){
  manualReady=true;manualLoading=true;
  try{manualParentSetup(q.code,q.price_mode,q.as_of,manualBinding.series_key);}finally{manualLoading=false;}
  const qualification=q.price_mode==='ADJUSTED_CANDIDATE'?'還原 K 為既存現金事件研究候選，完整公司行動／方法版本仍有限制。':'原始日 K 保留除權息機械落差；公司行動未完整認證。';
  statusBox.textContent='人工選擇：'+manualMode.selectedOptions[0].textContent+'｜'+q.code+'｜'+q.as_of+'。'+qualification+'分類未驗證，非交易訊號。';
 }else{
  frame=null;current=null;ev=null;walls=null;review=null;followup=null;hits=[];pointers.clear();gesture=null;
  const canvas=$('chart');canvas.getContext('2d').clearRect(0,0,canvas.width,canvas.height);$('evidence').hidden=true;
  for(const id of ['close','cursorValues','coverage','window','boundary','focusStatus','intervalStatus','priceWall','volumeWall'])if($(id))$(id).textContent='';
  const reason=manualStatus==='REQUIRES_MODE'?'請先選擇分析模式。':manualStatus==='REQUIRES_SOURCE'?'同日有多組來源，請明選「資料來源」。':'所選股票／模式／日期沒有相符保存資料；未改成另一模式，也未改日期。';
  statusBox.textContent=reason+(available.length?' 此來源範圍：'+available[0]+'～'+available.at(-1)+'。':' 還原或指定來源資料尚缺。');
 }
 if(persist)manualStore();else storageBox.textContent=manualStorageNote;
}
function manualUpdate(changes){
 const q={schema_version:'manual-basis-request/0.1',selection_id:crypto.randomUUID(),selected_at:new Date().toISOString(),code:manualIntent?.code||data.entry.series.split('|')[0],price_mode:manualIntent?.price_mode||null,as_of:manualIntent?.as_of||data.entry.as_of,series_key:manualIntent?.series_key||null,...changes};
 manualApply(q);
}
draw=function(){if(manualReady)manualParentDraw();};
setFrame=function(date){if(manualLoading)return manualParentFrame(date);manualUpdate({as_of:date,series_key:manualBinding?.series_key||manualIntent.series_key});};
setupStock=function(code,mode,date,key){manualUpdate({code,as_of:date,series_key:key||null});};
selected=function(){return {schema_version:'manual-price-mode-selection/0.1',view_version:'manual-basis-chart/0.1',catalogue_id:manualCatalogue.catalogue_id,parent_artifact_id:manualCatalogue.parent_artifact_id,request:structuredClone(manualIntent),resolution_status:manualStatus,resolution_binding:structuredClone(manualBinding),historical_selection_time:null,historical_signal_eligible:false,saved_selection:manualReady?manualParentSelected():null,local_persistence:manualStorageNote};};
function manualDownload(){const value=selected(),url=URL.createObjectURL(new Blob([JSON.stringify(value,null,2)],{type:'application/json'}));const a=document.createElement('a');a.href=url;a.download='M1_manual_'+manualIntent.code+'_'+(manualIntent.price_mode||'UNSELECTED')+'_'+manualIntent.as_of+'.json';a.click();setTimeout(()=>URL.revokeObjectURL(url),10000);}
manualMode.onchange=()=>manualUpdate({price_mode:manualMode.value||null,series_key:null});
$('stock').onchange=()=>manualUpdate({code:$('stock').value,series_key:null});
$('mode').onchange=()=>manualUpdate({series_key:$('mode').value||null});
manualDate.onchange=()=>{if(!manualDate.value){statusBox.textContent='請輸入完整分析日期；目前紀錄與圖表未變。';manualDate.value=manualIntent.as_of;return;}manualUpdate({as_of:manualDate.value});};
lastButton.onclick=()=>{const dates=manualRows(manualIntent).map(r=>r.as_of).sort();if(dates.length)manualUpdate({as_of:dates.at(-1)});};
$('download').onclick=manualDownload;downloadChoice.onclick=manualDownload;
window.manualBasisInspect=()=>({request:structuredClone(manualIntent),status:manualStatus,binding:structuredClone(manualBinding),ready:manualReady});
window.manualBasisExport=selected;
let restored=null;
try{const key=localStorage.getItem(manualPrefix+'latest');if(key){const record=JSON.parse(localStorage.getItem(key));if(record.catalogue_id!==manualCatalogue.catalogue_id||!manualValid(record.request))throw Error('舊選擇與目前資料版本不符');restored=record.request;manualStorageNote='已恢復此瀏覽器的人工選擇，並重新核對目前資料資格；未新增歷史訊號。';}}
catch(e){manualStorageNote='未恢復舊選擇：'+e.message+'；原紀錄未刪除。';}
if(restored)manualApply(restored,false);
else{
 const entrySeries=series.find(s=>s.key===data.entry.series);
 manualApply({schema_version:'manual-basis-request/0.1',selection_id:crypto.randomUUID(),selected_at:new Date().toISOString(),code:entrySeries.code,price_mode:null,as_of:data.entry.as_of,series_key:null},false);
}
