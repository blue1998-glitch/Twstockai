'use strict';
const comparison=JSON.parse($('comparison-payload').textContent);$('comparison-payload').remove();
const chartMain=document.querySelector('main'),tabs=document.createElement('nav');tabs.id='viewTabs';tabs.setAttribute('aria-label','研究畫面切換');chartMain.before(tabs);
const chartTab=text('button','原主圖',tabs),compareTab=text('button','四股比較',tabs);chartTab.id='chartTab';compareTab.id='compareTab';
const compareView=document.createElement('section');compareView.id='comparisonView';compareView.hidden=true;chartMain.before(compareView);
function switchView(compare){stop();$('evidence').hidden=true;chartMain.hidden=compare;compareView.hidden=!compare;chartTab.setAttribute('aria-pressed',String(!compare));compareTab.setAttribute('aria-pressed',String(compare));if(!compare)requestAnimationFrame(()=>draw());}
chartTab.onclick=()=>switchView(false);compareTab.onclick=()=>switchView(true);switchView(false);
function goChart(code,id){setup(code,comparison.as_of);$('stock').value=code;switchView(false);if(id)locate(id);$('chartWrap').scrollIntoView({block:'start'});}
text('h1','同期四股比較｜2026-10-16 完成日K',compareView);
const warning=text('p','固定同期研究，不隨主圖其他分析日改變。描述證據不排名、不推薦買賣；正式false、NOT_VALIDATED、主壓力null。',compareView);warning.className='comparisonWarning';
text('p','資料來自已保存M-C2總覽與原主圖，不重算箱型、不載入9份候選分片。確認與pending分開；回箱不代表正式恢復，停止比較不補0。',compareView);
const cards=text('div','',compareView);cards.className='stockCards';
for(const s of comparison.stocks){
 const series=data.series.find(v=>v.code===s.code),r=series.results.find(v=>v.as_of===comparison.as_of),card=text('article','',cards);card.className='stockCard';card.dataset.code=s.code;
 text('h2',`${s.code}｜${comparison.as_of}`,card);text('p',`${s.completed_records}根完成K；原收盤 ${r.anchor.close}；${s.box_count}箱全留。數量不代表強弱。`,card);
 const open=text('button','開啟此股互動主圖',card);open.dataset.openStock=s.code;open.onclick=()=>goChart(s.code);
 text('h3','已確認高低轉折（發生與確認分開）',card);
 table(card,['尺度／類型','原價','發生','確認'],Object.entries(s.latest_confirmed_by_scale).flatMap(([scale,kinds])=>Object.entries(kinds).flatMap(([kind,points])=>points.map(p=>[`${scale} ${kind}`,p.price,p.occurred_at,p.confirmed_at]))));
 text('h3','整箱位置 ≠ 研究壓力帶位置',card);
 const locations={whole:{},band:{}};for(const b of r.boxes){const whole=b.usable_at_anchor?b.path.last_close_location:'NOT_COMPARABLE_AFTER_GAP';locations.whole[whole]=(locations.whole[whole]||0)+1;locations.band[b.anchor_relation]=(locations.band[b.anchor_relation]||0)+1;}
 const names={ABOVE:'上方',INSIDE:'內部',BELOW:'下方',NOT_COMPARABLE_AFTER_GAP:'停止比較／不可比'};
 table(card,['位置','整個研究箱','研究壓力帶'],[...new Set([...Object.keys(locations.whole),...Object.keys(locations.band)])].map(k=>[names[k]||k,locations.whole[k]||0,locations.band[k]||0]));
 text('p','此處0只表示已讀集合的個數，不是將未知價格／距離填0。可在主圖選任一箱看三層證據。',card);
 text('h3',`最近上方研究帶｜全部${s.nearest_above.candidate_ids.length}個並列`,card);
 const nearest=text('p',s.nearest_above.distance_fraction===null?'NULL：沒有可比上方研究箱；距離不可計，不是0。':`原距離比例 ${s.nearest_above.distance_fraction}；僅展示距離，不是重要性排序。`,card);nearest.dataset.nearestDistance=s.nearest_above.distance_fraction===null?'NULL':s.nearest_above.distance_fraction;
 const ties=text('div','',card);ties.className='ties';
 for(const id of s.nearest_above.candidate_ids){const b=r.boxes.find(b=>b.id===id),button=text('button',`${b.research_bounds.pressure_band.join('～')}｜${b.scale}｜${id.slice(-8)}`,ties);button.dataset.boxId=id;button.title=id;button.onclick=()=>goChart(s.code,id);}
 text('h3','既有反證、回箱與停止比較',card);
 const counts={};for(const b of r.boxes)for(const e of b.path.events)counts[e.type]=(counts[e.type]||0)+1;
 table(card,['原事件類型','原箱事件筆數'],Object.entries(counts).map(([k,n])=>[eventNames[k]||k,n]));text('p','事件分屬不同原箱，可能共用同日，不是獨立樣本或成功率。既往失守不因回箱消失。',card);
 text('h3','pending｜尚未確認，不當成已確認訊號',card);for(const p of s.pending_extrema)text('p',`${p.direction}：高 ${p.high.price}（${p.high.source_dates.join('、')}）；低 ${p.low.price}（${p.low.source_dates.join('、')}）｜${p.qualification}`,card);
 text('h3','量價與來源限制',card);text('p',`當日原換算量 ${s.anchor_volume.current_shares}；來源欄位 ${s.volume_provenance.source_volume_fields.join('／')}；換算×${s.volume_provenance.multiplier}。`,card);
 text('p',s.volume_provenance.multiplier==='1000'?'張數／仟股精度；×1000不增加精度，SHARES_REPORTED不等原生精確股數，未認證FinMind股數。':'原來源申報股數；不代表歷史可得或交易資格通過。',card);
 text('p',`已知中斷：${s.source_input_binding.basis_break_dates.join('、')||'未列（不證無公司行動）'}。歷史available_at UNKNOWN；完整公司行動、日曆及跨基底可比尚未認證。`,card);
 text('p','人工後見覆核獨立保留，不輸入當時訊號；1101人工39筆不替換原自動25筆。',card);
 raw(card,'來源、完整原件SHA、NULL／UNKNOWN原因（原值）',{source:s.source_id,price_basis_id:s.price_basis_id,original:s.original,result_id:s.result_id,source_prefix_fingerprint:s.source_prefix_fingerprint,source_input_binding:s.source_input_binding,source_gaps:s.source_gaps,null_reasons:s.null_reasons,unknown_reasons:s.unknown_reasons,coverage:s.coverage});
}
