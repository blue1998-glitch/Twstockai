// Pure presentation of prepared manual evidence. No strategy rules in JS.
function rawDetails(parent, title, value){const d=text('details','',parent);text('summary',title,d);text('pre',JSON.stringify(value,null,2),d);return d;}
function selected(){const value=pressureSelected();value.schema_version='hurdle-chart-selection/0.1';value.view_version=data.view_version;value.manual_hurdles=manual;return value;}
const relationText=value=>value==='ABOVE'?'收盤已過點價':value==='BELOW'?'收盤低於點價':'收盤等於點價';
function axisHint(value){return Number(value)>geometry.priceHigh?'↑ 高於目前價格軸':Number(value)<geometry.priceLow?'↓ 低於目前價格軸':'價格在軸內';}
function manualRef(id){return manual?.references.find(r=>r.reference.id===id);}
function updateManualStrip(){
 $('manualPanel').hidden=!manual;$('manualUnavailable').hidden=!!manual;
 const strip=$('manualStrip');strip.replaceChildren();if(!manual)return;
 const original=refsForDisplay();
 $('manualPosition').textContent=`日收 ${fmt(frame.close)} ｜ 原${original.map(r=>r.reference.label+' '+fmt(r.reference.price)+' '+relationText(r.current_close_relation)).join('、')} → 後續人工三關`;
 for(const item of manual.references){const r=item.reference,card=text('div','',strip);card.className='hurdleCard';card.dataset.hurdle=r.id;
  const details=text('button',`${r.id} ${fmt(r.raw_high)} · ${relationText(item.current_close_relation)}`,card);details.className='hurdleEvidence';details.onclick=()=>openManual(r.id);
  text('span',r.source_date||'未指定唯一日 · 5個同價來源',card);
  text('span',`${r.matching_source_dates.every(outside)?'來源全在畫外':r.matching_source_dates.some(outside)?'部分來源在畫外':'來源在圖內'} · ${axisHint(r.raw_high)}`,card);
  const locate=text('button',r.source_date?'定位來源':'定位顯示錨',card);locate.className='hurdleLocate';locate.setAttribute('aria-label',r.id+'定位來源');locate.onclick=()=>{$('evidence').hidden=true;locateDate(r.display_anchor_source_date);};
 }
}
function drawManualOverlay(ctx,x,y,price){
 if(!manual)return;
 for(const item of manual.references){const r=item.reference,py=y(r.raw_high);if(py<price.top||py>price.bottom)continue;
  ctx.save();ctx.strokeStyle='#d5abff';ctx.setLineDash([3,5]);ctx.beginPath();ctx.moveTo(geometry.left,py);ctx.lineTo(geometry.right,py);ctx.stroke();ctx.setLineDash([]);
  for(const i of item.source_indices){if(i<view.start||i>view.end)continue;ctx.fillStyle='#d5abff';ctx.beginPath();ctx.arc(x(i),py,5,0,Math.PI*2);ctx.fill();
   hits.push({kind:'pressure',id:'manual:'+r.id+':'+i,x:x(i),y:py,index:i,label:r.id+' 人工點價 '+fmt(r.raw_high),source:{type:'manual',id:r.id}});
  }
  // Upper/lower out-of-axis levels stay in the strip, never at a false coordinate.
  const visible=item.source_indices.find(i=>i>=view.start&&i<=view.end);
  if(visible!==undefined){ctx.fillStyle='#d5abff';ctx.font='10px system-ui';ctx.fillText(r.id+' '+fmt(r.raw_high),Math.max(geometry.left,Math.min(geometry.right-56,x(visible)+7)),Math.max(price.top+10,py-12));}ctx.restore();
 }
}
function openManual(id){
 const item=manualRef(id);if(!item)return;const r=item.reference;
 const b=$('evidenceBody');b.replaceChildren();$('evidenceTitle').textContent=r.id+' 人工關卡來源';
 text('p',`${r.id} · Raw高 ${fmt(r.raw_high)} · 日收 ${fmt(frame.close)}：${relationText(item.current_close_relation)}。`,b);
 text('p',`來源日期：${r.source_date||'未指定唯一日期'}；${r.source_date?'使用者明選該日':'下列五日僅同價來源，不是區間起訖'}。`,b);
 text('p',`人工覆核 ${manual.review.reviewed_at}；分析日 ${frame.as_of}。這是後來人工回溯選點，非當時自動訊號，不套其他股票或分析日。`,b);
 text('p','Raw公司行動未完整核實，未認證共同校正基底壓力；點價不是整理區上緣。區界、整區量、增量、強度、衰減與自動選關仍未知。',b);
 const table=text('table','',b),header=text('tr','',table);for(const title of ['來源日','原始高價','查看'])text('th',title,header);
 for(const row of r.source_bars){const tr=text('tr','',table);text('td',row.date,tr);text('td',fmt(row.high),tr);const cell=text('td','',tr),button=text('button','定位',cell);button.setAttribute('aria-label',r.id+'定位'+row.date);button.onclick=()=>{$('evidence').hidden=true;locateDate(row.date);};}
 if(!r.source_date)text('p',`顯示錨 ${r.display_anchor_source_date} 只是定位起點，不是使用者唯一選日；五個原始K線全部保留。`,b);
 const recentButton=text('button','返回近期24月（不改分析日）',b);recentButton.onclick=()=>{$('evidence').hidden=true;calendarWindow(24);};
 rawDetails(b,'來源指紋／長ID',manual.source_fingerprints);
 rawDetails(b,'人工案例與原始OHLCV JSON',manual);
 $('evidence').hidden=false;
}
