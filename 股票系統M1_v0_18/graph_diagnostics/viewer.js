// Independent read-only sidecar. All decisions/margins/relations come from Python.
const diagNames={REJECTED_GEOMETRY:'幾何被拒',VALID_NOT_SELECTED_BY_LONGEST_OR_FOUR_TURN_POLICY:'幾何通過，非最長／四轉折種子',EMITTED:'原核心已產生',DEDUPLICATED_EXISTING_SOURCE_ENDPOINTS:'已有同來源端點',FEWER_THAN_TWO_HIGHS:'高轉折不足兩個',FEWER_THAN_TWO_LOWS:'低轉折不足兩個',NONPOSITIVE_SPAN:'全跨度非正',HIGH_CLUSTER_SPREAD_EXCEEDS_RESEARCH_LIMIT:'高群跨度超研究限制',LOW_CLUSTER_SPREAD_EXCEEDS_RESEARCH_LIMIT:'低群跨度超研究限制',NO_POSITIVE_COMMON_CORRIDOR:'沒有共同正走廊'};
let diagnosticProbe=null;
function diagnostic(){return current.diagnostics[result.as_of];}
function diagInfo(id){return diagnostic().boxes.find(b=>b.box_id===id);}
function links(parent,title,ids){text('p',title+(ids.length?'':'無此精確關係'),parent);for(const id of ids){const b=text('button',boxLabel(id),parent);b.onclick=()=>{$('diagBox').value=id;showDiagnostic();};}}
function showDiagnostic(){const id=$('diagBox').value,b=box(id),d=diagInfo(id),body=$('diagnosticBody');body.replaceChildren();if(!b){$('probeSelect').replaceChildren();$('probeBody').replaceChildren();return;}const w=d.windows,t=w.date_semantics;
 text('p',`${boxLabel(id)}：來源首末轉折 ${b.start}～${t.source_last_turn}（${b.duration_records}筆）；確認 ${t.confirmed_at}，相隔${w.confirmation_lag_records}筆。來源末轉折不是整箱終點。`,body).className='diagnostic-facts';
 text('p',`確認後首次研究界外收盤 ${t.first_outside_close_at||'尚無'}；前一筆已觀察記錄 ${t.previous_observed_inside_record||'無（形成即在外或尚未離箱）'}；首次低於研究下緣 ${t.first_below_close_at||'尚無'}。人工／正式整箱終點仍未知，不由此替代。`,body);
 const o=w.path_observation,m=w.decline_measurement,v=w.prior_volume_window;
 text('p',`後續觀察 ${o.start||'無'}～${o.end||'無'}，含端點${o.records}筆${o.stopped_at?'；缺口停止於'+o.stopped_at:''}。最大後續下跌在${m.maximum_date||'無'}，距形成${m.records_after_formation_to_maximum??'未知'}筆；不同箱觀察長度不同，未作公平重要性或衰減校正。`,body);
 text('p',`來源量窗 ${w.source_volume_window.start}～${w.source_volume_window.end}；前段量比較 ${v.first_date||'無'}～${v.last_date||'無'}，完整資格 ${v.complete?'完整等筆數':'不足／缺量不可比'}。事件量口徑與此不同，原值在JSON。`,body);
 links(body,'同幾何來源（尺度／確認可不同，不獨立計票）：',d.same_geometry_other_ids);links(body,'同尺度最近來源前綴版本：',d.immediate_source_prefix_predecessor_ids);links(body,'本局部串位於其他較長來源串內（非同起點版本）：',d.local_subsequence_of_ids);
 text('p',`破底後廣義後來候選 ${d.later_after_breakdown.length}；僅時間先後，直接承接未知。幾何父箱 ${d.geometric_parent_ids.map(boxLabel).join('、')||'無'}不等人工重要性階層。`,body);
 text('p',d.default_display.selected?'原預設有顯示：UI多樣性選擇，不是正式主壓力。':`原預設未選：未贏得任一UI多樣性條件；原研究支配者 ${d.default_display.original_dominated_by.map(boxLabel).join('、')||'無'}。不等於引擎漏檢。`,body);
 raw(body,'精確來源ID、各選擇條件、觀察窗與時間關係',d);buildProbes();
}
function buildProbes(){const b=box($('diagBox').value);if(!b)return;const right=$('probeMode').value==='right';const list=diagnostic().enumeration.filter(t=>t.scale===b.scale&&t.segment===b.segment&&(right?t.first_turn_id===b.source_turn_ids[0]&&t.last_index>=b.last_index:t.last_turn_id===b.source_turn_ids.at(-1)));
 options($('probeSelect'),list.map(t=>[t.id,`${t.source_start}～${t.source_last_turn}｜${diagNames[t.decision]}`]),list.find(t=>t.box_id===b.id)?.id||list[0]?.id||'');showProbe();}
function probe(){return diagnostic().enumeration.find(t=>t.id===$('probeSelect').value);}
function showProbe(){const t=probe(),body=$('probeBody');body.replaceChildren();if(!t)return;const c=t.checks,m=c.metrics;
 text('p',`${t.source_start}～${t.source_last_turn}｜${diagNames[t.decision]}。觀察／判定 ${t.observed_at}；首個失敗 ${diagNames[c.first_failed_check]||'無'}。`,body).className='diagnostic-facts';
 text('p',`高群餘量 ${m.high_spread_margin??'不可算'}；低群餘量 ${m.low_spread_margin??'不可算'}；共同走廊 ${m.common_corridor_margin??'不可算'}。群跨度餘量負值為超限，走廊須大於0；原35%研究設定不變。`,body);
 raw(body,'全部檢查、極值證人與原核心實際選中替代串',t);
}
function refreshDiagnostics(){diagnosticProbe=null;const d=diagnostic();$('diagnosticSummary').textContent=`${d.summary.candidate_versions}個候選版本、${d.summary.exact_source_geometry_groups}組精確來源幾何；都不是獨立型態數或準確率。${d.enumeration.length}個實際檢查串；版本鏈與跨尺度同幾何分開，不硬合併。`;
 $('status').textContent=$('status').textContent.replace('自動候選 '+boxes().length+' 箱','自動候選 '+boxes().length+' 個版本');
 options($('diagBox'),boxes().map((b,i)=>[b.id,`B${i+1} ${b.scale}｜${b.start}～${b.source_end}`]),$('boxSelect').value);showDiagnostic();}
const originalSetFrame=setFrame;setFrame=function(dt){diagnosticProbe=null;originalSetFrame(dt);refreshDiagnostics();};
const originalSelected=selected;selected=function(){return {...originalSelected(),schema_version:'graph-diagnostic-selection/0.1',view_version:data.view_version,diagnostics:diagnostic()};};
const originalOpenBox=openBox;openBox=function(id){originalOpenBox(id);const body=$('evidenceBody');const old=[...body.children].find(p=>p.tagName==='P'&&p.textContent.includes('破底後新箱候選'));if(old)old.textContent=old.textContent.replace('破底後新箱候選','破底後廣義後來候選（非直接承接）');const btn=text('button','日期／版本／被拒診斷',body);btn.onclick=()=>{$('evidence').hidden=true;$('diagnosticPanel').open=true;$('diagBox').value=id;showDiagnostic();$('diagnosticPanel').scrollIntoView({block:'start'});};};
const originalDraw=draw;draw=function(){originalDraw();if(!diagnosticProbe)return;const t=diagnosticProbe;if(t.observed_at>result.as_of)return;const g=geometry,canvas=$('chart'),ctx=canvas.getContext('2d'),dpr=devicePixelRatio||1;ctx.save();ctx.setTransform(dpr,0,0,dpr,0,0);ctx.beginPath();ctx.rect(g.left,g.price.top,g.right-g.left,g.price.bottom-g.price.top);ctx.clip();const first=Math.max(t.first_index,view.start),last=Math.min(t.last_index,view.end);if(first<=last){const rows=bars().slice(t.first_index,t.last_index+1),lo=Math.min(...rows.map(r=>Number(r.low))),hi=Math.max(...rows.map(r=>Number(r.high))),y=v=>g.price.bottom-(v-g.priceLow)/(g.priceHigh-g.priceLow)*(g.price.bottom-g.price.top);ctx.strokeStyle='#f5e268';ctx.lineWidth=2;ctx.setLineDash([7,4]);ctx.strokeRect(g.x(first),y(hi),Math.max(1,g.x(last)-g.x(first)),y(lo)-y(hi));ctx.setLineDash([]);ctx.fillStyle='#f5e268';ctx.fillText('診斷串（非正式箱）',g.left+4,g.price.top+12);}ctx.restore();};
$('diagEvidence').onclick=showDiagnostic;$('diagBox').onchange=()=>{diagnosticProbe=null;showDiagnostic();draw();};$('probeMode').onchange=buildProbes;$('probeSelect').onchange=showProbe;
$('probeFocus').onclick=()=>{const t=probe();if(!t)return;diagnosticProbe=t;const b=box($('diagBox').value);visible=new Set([b.id]);view.start=Math.max(0,Math.min(t.first_index,b.first_index)-12);view.end=Math.min(result.source_records-1,Math.max(t.last_index,b.last_index)+12);view.cursor=t.last_index;buildList();draw();$('chartWrap').scrollIntoView({block:'start'});};
$('probeClear').onclick=()=>{diagnosticProbe=null;draw();};refreshDiagnostics();
