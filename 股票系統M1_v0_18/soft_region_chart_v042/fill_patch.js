// Display-only controls over the unchanged prepared candle/volume extents.
(()=>{
 let alpha=.12;
 drawExtentPane=function(ctx,extent,x,pane,top,bottom,color,step){
  const left=x(extent.first_index)-step/2,right=x(extent.last_index)+step/2;
  if(right<geometry.left||left>geometry.right)return;
  ctx.save();ctx.beginPath();ctx.rect(geometry.left,pane.top,geometry.right-geometry.left,pane.bottom-pane.top);ctx.clip();
  ctx.globalAlpha=alpha;ctx.fillStyle=color;
  if(extent.uncertain_start_month){
   const split=x(regionById('G1').display.month_last_index)+step/2;
   const fade=ctx.createLinearGradient(left,0,Math.max(left+1,split),0);
   fade.addColorStop(0,color+'00');fade.addColorStop(1,color+'ff');ctx.fillStyle=fade;
  }
  ctx.fillRect(left,top,right-left,bottom-top);ctx.restore();
 };
 const label=document.createElement('label');label.append('底色 ');
 const select=document.createElement('select');select.id='regionShade';select.setAttribute('aria-label','底色濃淡');
 for(const [value,title]of [['0.08','較淡'],['0.12','標準'],['0.20','明顯']]){
  const option=document.createElement('option');option.value=value;option.textContent=title;select.append(option);
 }
 select.value='0.12';select.onchange=()=>{alpha=Number(select.value);draw();};
 label.append(select);$('regionControls').append(label);draw();
})();
