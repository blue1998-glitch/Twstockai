// Presentation of saved daily evidence only. Never detect new pivots or zones.
const annotationState={items:[],hits:[],selected:'',issue:''};
const annotationStates={ACTIVE_CANDIDATE:'有效候選',BREACHED_CANDIDATE:'候選失效',INACTIVE_CORPORATE_ACTION:'公司行動後停用'};
const storedCoordinate=value=>value!==null&&value!==undefined&&value!==''&&Number.isFinite(plotNumber(value));

function resetAnnotations(){
 annotationState.items=[];annotationState.hits=[];annotationState.selected='';annotationState.issue='';
 el('annotationSelect').replaceChildren();el('annotationSelect').disabled=true;
 el('annotationDetail').textContent='請先讀取保存結果，再點選圖上的標記或從清單選取。';
 el('annotationSummary').textContent='';
}

function savedAnnotations(d,dates){
 annotationState.issue='';
 const level=el('annotationLevel').value||'major',history=el('annotationHistory').value||'active';
 if(!d||level==='off'||!dates.length)return [];
 const s=d.snapshot.structure,m=d.snapshot.daily_ma;
 if(!['structure-0.2-research','structure-0.3-research'].includes(s.rule_version)||
    s.as_of!==d.as_of||s.adjustment_anchor!==d.as_of||m.as_of!==d.as_of||s.price_mode!==d.price_mode){
  annotationState.issue='保存版本或價格錨定不符，停止繪製結構標記；不改選其他結果。';return [];
 }
 const accepts=p=>['major','minor'].includes(p)&&(level==='both'||level===p);
 const first=dates[0],last=dates.at(-1),result=[];
 s.pivots.forEach((p,index)=>{
  if(!accepts(p.profile)||!['HIGH','LOW'].includes(p.kind)||p.status!=='RULE_CONFIRMED_CANDIDATE'||
     !p.first_observed_at||!p.confirmed_at||p.confirmed_at>d.as_of||p.first_observed_at>p.confirmed_at||
     p.occurred_at>p.confirmed_at||!dates.includes(p.occurred_at)||!storedCoordinate(p.price))return;
  result.push({key:'pivot:'+p.id,type:'pivot',label:(p.profile==='major'?'主':'次')+(p.kind==='HIGH'?'高':'低')+(index+1),
   date:p.occurred_at,value:p.price,saved:p});
 });
 s.zones.forEach((z,index)=>{
  const pivot=s.pivots.find(p=>p.id===z.pivot_id);
  if(!accepts(z.profile)||!pivot||pivot.status!=='RULE_CONFIRMED_CANDIDATE'||
     !['SUPPORT_CANDIDATE','RESISTANCE_CANDIDATE'].includes(z.role)||!Object.hasOwn(annotationStates,z.state)||
     !z.created_at||z.created_at<pivot.confirmed_at||z.created_at>d.as_of||z.created_at>last||
     (z.invalidated_at&&(z.invalidated_at<first||z.invalidated_at<z.created_at||z.invalidated_at>d.as_of))||
     (history!=='all'&&(z.state!=='ACTIVE_CANDIDATE'||z.invalidated_at))||
     !storedCoordinate(z.low)||!storedCoordinate(z.high)||plotNumber(z.low)>plotNumber(z.high))return;
  const visible=dates.filter(date=>date>=z.created_at&&(!z.invalidated_at||date<=z.invalidated_at));
  if(!visible.length)return;
  result.push({key:'zone:'+z.id,type:'zone',label:(z.role==='SUPPORT_CANDIDATE'?'支':'壓')+(index+1),
   start:visible[0],end:visible.at(-1),low:z.low,high:z.high,saved:z});
 });
 return result;
}

function annotationDetail(item){
 if(!item)return '點選圖上的點／色帶，或從清單選取。點位標在發生日，需等到確認日才成立。';
 const v=item.saved,profile=v.profile==='major'?'主要':'次級';
 if(item.type==='pivot')return item.label+'｜'+profile+(v.kind==='HIGH'?'高點':'低點')+'候選 '+displayPrice(v.price)+
  '\n發生 '+v.occurred_at+'；首次觀察 '+v.first_observed_at+'；規則確認 '+v.confirmed_at+
  '\n狀態 '+v.status+'；原 ID '+v.id+'\n這是所選分析日已保存的歷史證據，不代表發生日已知，也不代表買賣資格。';
 return item.label+'｜'+profile+(v.role==='SUPPORT_CANDIDATE'?'支撐':'壓力')+'區候選 '+displayPrice(v.low)+' ～ '+displayPrice(v.high)+
  '\n建立 '+v.created_at+'；失效／停用 '+(v.invalidated_at||'尚無保存日期')+
  '\n狀態 '+annotationStates[v.state]+' ['+v.state+']；接觸過程 '+v.touch_episodes+' 次'+
  '\n原 ID '+v.id+'\n色帶只沿用保存的區域邊界與有效時間，不由長紅 K 或反彈形狀重新判定。';
}

function listAnnotations(items){
 annotationState.items=items;annotationState.hits=[];
 if(!items.some(item=>item.key===annotationState.selected))annotationState.selected='';
 const select=el('annotationSelect');select.replaceChildren();
 const placeholder=document.createElement('option');placeholder.value='';placeholder.textContent='選取標記以查看原證據';select.append(placeholder);
 for(const item of items){
  const option=document.createElement('option');option.value=item.key;
  option.textContent=item.label+'｜'+(item.type==='pivot'?item.date+' · '+displayPrice(item.value):
   item.saved.created_at+' · '+displayPrice(item.low)+'～'+displayPrice(item.high)+' · '+annotationStates[item.saved.state]);select.append(option);
 }
 select.value=annotationState.selected;select.disabled=!items.length;
 const count=items.filter(item=>item.type==='pivot').length;
 el('annotationSummary').textContent=annotationState.issue||('目前視窗 '+count+' 個歷史轉折候選、'+(items.length-count)+' 個區域候選。週月圖未新增結構判定。');
 el('annotationDetail').textContent=annotationDetail(items.find(item=>item.key===annotationState.selected));
}

function annotationBands(ctx,items,geometry){
 const {dates,x,y,left,right,top,bottom}=geometry;
 const labels=[];
 for(const item of items.filter(item=>item.type==='zone')){
  const a=Math.max(left,x(dates.indexOf(item.start))),b=Math.min(right,x(dates.indexOf(item.end)));
  const upper=Math.max(top,y(item.high)),lower=Math.min(bottom,y(item.low));
  const selected=item.key===annotationState.selected,support=item.saved.role==='SUPPORT_CANDIDATE';
  ctx.fillStyle=support?'rgba(23,128,82,.12)':'rgba(197,55,55,.12)';
  ctx.fillRect(a,upper,Math.max(1,b-a),Math.max(1,lower-upper));
  ctx.strokeStyle=support?'#178052':'#b33838';ctx.lineWidth=selected?2.5:1;
  ctx.setLineDash(item.saved.state==='ACTIVE_CANDIDATE'?[]:[4,3]);
  ctx.strokeRect(a,upper,Math.max(1,b-a),Math.max(1,lower-upper));ctx.setLineDash([]);
  annotationState.hits.push({key:item.key,type:'zone',left:a,right:b,top:upper,bottom:lower});
  ctx.fillStyle=support?'#11603c':'#992b2b';ctx.textAlign='right';ctx.textBaseline='bottom';
  const labelX=Math.max(left+32,b-3);let labelY=Math.max(top+14,upper-3);
  while(labelY>=top+14&&labels.some(p=>Math.abs(p.x-labelX)<48&&Math.abs(p.y-labelY)<17))labelY-=18;
  if(labelY>=top+14){ctx.fillText(item.label,labelX,labelY);labels.push({x:labelX,y:labelY})}
 }
}

function annotationDots(ctx,items,geometry){
 const {dates,x,y,left,right,top,bottom}=geometry,occupied=[];
 for(const item of items.filter(item=>item.type==='pivot')){
  const px=x(dates.indexOf(item.date)),py=y(item.value),high=item.saved.kind==='HIGH';
  const selected=item.key===annotationState.selected,radius=selected?7:item.saved.profile==='major'?5:3.5;
  ctx.fillStyle=high?'#c17b08':'#225ca8';ctx.strokeStyle='#fff';ctx.lineWidth=1.5;
  ctx.beginPath();ctx.arc(px,py,radius,0,Math.PI*2);ctx.fill();ctx.stroke();
  annotationState.hits.push({key:item.key,type:'pivot',x:px,y:py});
  // Suppress overlapping text, retaining the selectable dot and full evidence list.
  const labelY=Math.max(top+13,Math.min(bottom-4,py+(high?-12:21)));
  if(selected||!occupied.some(p=>Math.abs(p.x-px)<48&&Math.abs(p.y-labelY)<19)){
   ctx.fillStyle=high?'#855000':'#18457e';ctx.textAlign='center';ctx.textBaseline='middle';
   ctx.fillText(item.label,Math.max(left+20,Math.min(right-20,px)),labelY);occupied.push({x:px,y:labelY});
  }
 }
}

function selectAnnotation(key){
 if(!annotationState.items.some(item=>item.key===key))key='';
 annotationState.selected=key;
 if(current&&current.alignment.status!=='CONFLICT')draw();
}

el('annotationSelect').addEventListener('change',()=>selectAnnotation(el('annotationSelect').value));
for(const id of ['annotationLevel','annotationHistory','annotationWindow'])el(id).addEventListener('change',()=>{
 annotationState.selected='';if(current&&current.alignment.status!=='CONFLICT')draw();
});
el('dailyChart').addEventListener('pointerup',event=>{
 const rect=el('dailyChart').getBoundingClientRect(),px=event.clientX-rect.left,py=event.clientY-rect.top;
 const nearby=annotationState.hits.filter(hit=>hit.type==='pivot'&&Math.hypot(hit.x-px,hit.y-py)<=18)
  .sort((a,b)=>Math.hypot(a.x-px,a.y-py)-Math.hypot(b.x-px,b.y-py));
 const band=[...annotationState.hits].reverse().find(hit=>hit.type==='zone'&&px>=hit.left&&px<=hit.right&&py>=hit.top&&py<=hit.bottom);
 selectAnnotation(nearby.length?nearby[0].key:band?band.key:'');
});
