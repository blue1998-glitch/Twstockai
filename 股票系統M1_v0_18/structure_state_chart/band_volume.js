// Only render prepared whole-source facts; no box/max/reference calculation here.
const bandVolumeStyle=document.createElement('style');bandVolumeStyle.textContent=`
#p03BandVolume{border-left:3px solid #ccabff;padding-left:7px;margin:6px 0;font-size:13px;line-height:1.5}#p03BandVolume p{margin:3px 0}#bandVolumeEvidence{min-height:44px}#bandSourceRows{font-size:12px}#bandSourceRows td{padding:4px;overflow-wrap:anywhere}#bandSourceRows{width:100%;border-collapse:collapse}#bandSourceRows th{text-align:left}#bandVolumeDrawHint{color:#cfb7ef}`;
document.head.append(bandVolumeStyle);
const bandVolumePanel=text('section','',p03Home);bandVolumePanel.id='p03BandVolume';p03Volume.after(bandVolumePanel);
const bandReasonNames={REFERENCE_NOT_YET_KNOWN:'候選／量參照當時尚不可知',NO_MATCHING_SAVED_BAND:'此來源／基底／日期沒有相符明示研究帶',MISSING_SOURCE_MEMBER_DATES:'缺來源成員日期',UNEXPECTED_SOURCE_MEMBER_DATES:'來源成員衝突',KNOWN_SOURCE_CALENDAR_GAPS:'來源段有已知待核缺日',BASIS_INTERRUPTION:'基底中斷',ROW_SOURCE_BASIS_VERSION_CONFLICT:'列來源／基底／版本衝突',MISSING_SOURCE_VOLUME:'來源段缺量',SOURCE_ROWS_FINGERPRINT_CONFLICT:'原段指紋不符',EXISTING_VOLUME_HELPERS_OR_SAVED_CANDIDATE_CONFLICT:'既有量統計／原件衝突',MISSING_CURRENT_VOLUME:'分析日缺量',CURRENT_RECORD_NOT_YET_KNOWN_OR_INCOMPLETE:'分析日未完整可知',GAP_BETWEEN_REFERENCE_AND_ANALYSIS:'來源段至分析日間有待核缺日'};
const bandCount=s=>s===null||s===undefined?'未知':String(s).replace(/\B(?=(\d{3})+(?!\d))/g,',');
let bandVolumeGeometry={visible:false};
function bandVolumeSnapshot(){
 const day=manualIntent?.as_of,b=bandVolumeData.snapshots[day];
 if(p03Matched()&&b&&p03Data.series_key===bandVolumeData.series_key)return structuredClone(b);
 return {schema_version:'explicit-research-band-volume/0.1',analysis_as_of:day||null,available:false,reference:null,comparison:{relation:null,delta:null,reason:'NO_MATCHING_SAVED_BAND'},reasons:['NO_MATCHING_SAVED_BAND'],current_volume_shares:null,historical_signal_eligible:false,execution_qualified:false,imputed_close:null,valuation:null,primary_pressure_id:null,policy_authorized:false,physical_android:'NOT_TESTED_NEW_BUILD'};
}
function bandVolumeRender(){
 const b=bandVolumeSnapshot(),r=b.reference;bandVolumePanel.replaceChildren();
 if(p03Volume.textContent.startsWith('量觀察：'))p03Volume.textContent='前筆量觀察：'+p03Volume.textContent.slice('量觀察：'.length);
 text('b','完整研究段最大量對照',bandVolumePanel);
 if(!b.available){text('p','不可比較：'+b.reasons.map(x=>bandReasonNames[x]||x).join('；')+'。不以已知部分最大量代替完整段。',bandVolumePanel);}
 else{
  const words={ABOVE:'高於（已越過）',BELOW:'低於（尚未越過）',EQUAL:'相等（未嚴格越過）'};
  text('p',`最大日量 ${bandCount(r.max_single_day_shares)}股｜當日 ${bandCount(b.current_volume_shares)}股：${words[b.comparison.relation]}，差額 ${bandCount(b.comparison.delta)}股。`,bandVolumePanel);
  text('p',`${r.source_start}～${r.source_end}／${r.actual_records}根完整保存來源；最大量日 ${r.max_single_day_dates.join('、')}。未越不判壞，不取消價格過線。`,bandVolumePanel);
 }
 text('p','密集量峰代表線：未實作；群組及估計法未定，不用平均／中位數或固定比例替代。',bandVolumePanel);
 const hint=text('p','',bandVolumePanel);hint.id='bandVolumeDrawHint';
 const button=text('button','研究段量來源與原K',bandVolumePanel);button.id='bandVolumeEvidence';button.onclick=bandVolumeEvidence;
}
function bandVolumeEvidence(){const b=bandVolumeSnapshot(),r=b.reference,body=$('evidenceBody');body.replaceChildren();$('evidenceTitle').textContent='明示研究段最大量來源（不改P0-3）';
 text('p',`分析截止 ${b.analysis_as_of}；後來明示研究參照，不是歷史當時已選或可交易。`,body);
 if(r){
  text('p',`${r.qualification}｜${r.source_start}～${r.source_end}；預期 ${r.expected_records}根／實際 ${r.actual_records}根。只是完整明示保存成員，不認證完整市場日曆或正式原箱。`,body);
  text('p',`候選確認 ${r.candidate_confirmed_on}；量參照可知 ${r.reference_known_on}；本次實際後來選取 ${r.selected_at}。最大量發生日另外逐筆列。`,body);
  for(const row of r.maximum_original_bars){text('p',`${row.date}｜開 ${row.open} 高 ${row.high} 低 ${row.low} 收 ${row.close}；原量 ${row.volume_shares_scaled}股。`,body);const locate=text('button','定位最大量原K '+row.date,body);locate.onclick=()=>{$('evidence').hidden=true;locateDate(row.date);};}
  const members=text('details','',body);text('summary','完整來源成員及逐筆原K量（'+r.source_rows.length+'筆）',members);
  const table=text('table','',members);table.id='bandSourceRows';const tr=text('tr','',table);for(const h of ['日期','原開／高／低／收','原量（股）'])text('th',h,tr);
  for(const row of r.source_rows){const tr=text('tr','',table);text('td',row.date,tr);text('td',[row.open,row.high,row.low,row.close].join(' / '),tr);text('td',row.volume_shares_scaled,tr);}
 }
 text('p',b.available?`精確比較 ${b.comparison.relation}；差額 ${b.comparison.delta}股。`:'不可用：'+b.reasons.map(x=>bandReasonNames[x]||x).join('；'),body);
 text('p','前筆量與整段最高日量是不同參照。密集量峰代表線尚未實作；量不取消價格過線，不表示已清籌碼、機率、交易或獲利。',body);
 rawDetails(body,'候選ID、完整原值／指紋與來源限制JSON',b);$('evidence').hidden=false;
}
function bandVolumeOverlay(){bandVolumeGeometry={visible:false};const b=bandVolumeSnapshot(),r=b.reference;if(!b.available||!r)return;
 const g=geometry,v=g.volume,maximum=v.displayMaximum,y=v.bottom-Number(r.max_single_day_shares)/maximum*(v.bottom-v.top),inAxis=y>=v.top&&y<=v.bottom;
 bandVolumeGeometry={visible:inAxis,maximum_shares:r.max_single_day_shares,y,displayMaximum:maximum,volumeTop:v.top,volumeBottom:v.bottom,tied_source_dates:r.max_single_day_dates,source_points:[]};
 if(!inAxis){$('bandVolumeDrawHint').textContent='來源最大量在本圖量軸外，保留提示，不調整量軸或貼到錯誤高度。';return;}
 const ctx=$('chart').getContext('2d');ctx.save();ctx.strokeStyle='#ccabff';ctx.setLineDash([5,4]);ctx.beginPath();ctx.moveTo(g.left,y);ctx.lineTo(g.right,y);ctx.stroke();ctx.setLineDash([]);
 for(const date of r.max_single_day_dates){const i=base().bars.findIndex(row=>row.date===date);if(i<view.start||i>view.end)continue;const x=v.x(i);ctx.beginPath();ctx.arc(x,y,5,0,Math.PI*2);ctx.stroke();bandVolumeGeometry.source_points.push({date,x,y});}
 ctx.restore();$('bandVolumeDrawHint').textContent='量圖紫色虛線＝此明示來源段最大日量；不是密集量峰代表線。';
}
const bandVolumeOldDraw=draw,bandVolumeOldRender=p03Render,bandVolumeOldSelected=selected;
p03Render=function(){bandVolumeOldRender();bandVolumeRender();};
draw=function(){bandVolumeOldDraw();if(manualReady)bandVolumeOverlay();};
selected=function(){const s=bandVolumeOldSelected();s.view_version='p03-existing-chart/0.3';s.band_volume=bandVolumeSnapshot();return s;};
window.BandVolumeInspect=()=>({snapshot:bandVolumeSnapshot(),geometry:structuredClone(bandVolumeGeometry)});
p03Render();if(manualReady)draw();
