'use strict';
const fs=require('fs'),path=require('path'),http=require('http'),assert=require('assert/strict'),crypto=require('crypto');
const folder=path.resolve(process.env.M1_HURDLE_DIR),out=path.resolve(process.env.M1_EXTENT_BROWSER_OUTPUT_DIR);
const after=fs.readFileSync(path.join(folder,'M1_v0_19_candle_regions_v04.html')),before=fs.readFileSync(path.join(__dirname,'../region_chart/generated/M1_v0_19_manual_regions_v03.html'));
const oracle=JSON.parse(fs.readFileSync(path.join(folder,'region-display.json'))),checks=[],errors=[],external=[];let browser,server;fs.mkdirSync(out,{recursive:true});
const pass=(name,size,extra={})=>checks.push({name,size,status:'PASS',...extra});
const close=(a,b)=>assert(Math.abs(a-b)<1e-7,`${a} != ${b}`);
(async()=>{try{
 const pw=require(path.join(process.env.CODEX_PRIMARY_RUNTIME_NODE_MODULES,'playwright'));browser=await pw.chromium.launch({headless:true,executablePath:process.env.CODEX_BROWSER_EXECUTABLE_PATH||'/usr/bin/chromium'});
 server=http.createServer((q,r)=>{r.writeHead(200,{'Content-Type':'text/html;charset=utf-8'});r.end(q.url==='/before'?before:after)});await new Promise(r=>server.listen(0,'127.0.0.1',r));const origin='http://127.0.0.1:'+server.address().port;
 for(const size of [{width:1280,height:900},{width:390,height:844},{width:844,height:390},{width:320,height:740}]){
  const context=await browser.newContext({viewport:size,isMobile:size.width!==1280,hasTouch:size.width!==1280,deviceScaleFactor:1,acceptDownloads:true}),page=await context.newPage();
  page.on('pageerror',e=>errors.push(e.stack));page.on('request',r=>{if(/^https?:/.test(r.url())&&new URL(r.url()).origin!==origin)external.push(r.url());});
  await page.addInitScript(()=>{
   window.regionPaint=[];const proto=CanvasRenderingContext2D.prototype,states=new WeakMap(),state=ctx=>{if(!states.has(ctx))states.set(ctx,{clip:null,path:[],stack:[]});return states.get(ctx);};
   for(const name of ['save','restore','beginPath','rect','moveTo','lineTo','clip','fillRect','stroke']){const original=proto[name];proto[name]=function(...args){const s=state(this);
    if(name==='save')s.stack.push(s.clip?{...s.clip}:null);
    if(name==='restore')s.clip=s.stack.pop()??null;
    if(name==='beginPath')s.path=[];
    if(['rect','moveTo','lineTo'].includes(name))s.path.push({kind:name,args:[...args]});
    if(name==='clip'){const p=s.path.find(p=>p.kind==='rect');if(p){const[x,y,w,h]=p.args;const n={x,y,right:x+w,bottom:y+h};s.clip=s.clip?{x:Math.max(n.x,s.clip.x),y:Math.max(n.y,s.clip.y),right:Math.min(n.right,s.clip.right),bottom:Math.min(n.bottom,s.clip.bottom)}:n;}}
    if((name==='fillRect'&&['#b7a2ef','#f3bd7b'].includes(this.fillStyle))||(name==='stroke'&&['#b7a2ef','#f3bd7b'].includes(this.strokeStyle)))regionPaint.push({kind:name,args:[...args],path:s.path.map(p=>({...p,args:[...p.args]})),clip:s.clip?{...s.clip}:null,color:name==='fillRect'?this.fillStyle:this.strokeStyle,alpha:this.globalAlpha});
    return original.apply(this,args);};}
  });
  await page.goto(origin+'/before');await page.waitForFunction(()=>typeof regions!=='undefined'&&regions);for(const id of ['G1','G2']){await page.locator('#focus'+id).click();await page.locator('#chartWrap').screenshot({path:path.join(out,'before-'+id+'-'+size.width+'.png')});}
  await page.goto(origin+'/after');await page.waitForFunction(()=>typeof regionDisplay!=='undefined'&&regionDisplay);assert.deepEqual(await page.evaluate(()=>regionDisplay),oracle);
  const identity=await page.evaluate(()=>[current.key,frame.frame_id,frame.as_of,current.source.id,frame.chart_base]);
  const mainSelection=await page.evaluate(()=>JSON.stringify(selected()));
  pass('new HTML display extent equals independent Python oracle; old cases remain separate',size);
  for(const id of ['G2','G1']){
   await page.locator('#focus'+id).click();
   const actual=await page.evaluate(()=>{regionPaint.length=0;draw();const d=regionDisplay;return {paints:regionPaint,g:{...geometry,price:{top:geometry.price.top,bottom:geometry.price.bottom},volume:{top:geometry.volume.top,bottom:geometry.volume.bottom}},view:{...view},max:Math.max(1,...base().bars.slice(view.start,view.end+1).map(r=>Number(r.volume_shares_scaled)||0)),values:d,manual:regions};});
   const extent=oracle.extents[id],color=id==='G2'?'#b7a2ef':'#f3bd7b',g=actual.g,n=actual.view.end-actual.view.start+1,step=(g.right-g.left)/n;
   const fills=actual.paints.filter(p=>p.kind==='fillRect'&&p.color===color);assert.equal(fills.length,2);
   const price=fills.find(p=>p.clip.y===g.price.top),volume=fills.find(p=>p.clip.y===g.volume.top);assert(price&&volume);
   const x=i=>g.left+(i-actual.view.start+.5)*step,y=v=>g.price.bottom-(Number(v)-g.priceLow)/(g.priceHigh-g.priceLow)*(g.price.bottom-g.price.top);
   close(price.args[0],x(extent.first_index)-step/2);close(price.args[2],(extent.last_index-extent.first_index+1)*step);
   close(price.args[1],y(extent.price.high));close(price.args[3],y(extent.price.low)-y(extent.price.high));
   close(volume.args[0],price.args[0]);close(volume.args[2],price.args[2]);close(volume.args[1],g.volume.bottom-Number(extent.volume.max_volume_shares_scaled)/actual.max*(g.volume.bottom-g.volume.top));close(volume.args[1]+volume.args[3],g.volume.bottom);
   assert.equal(price.clip.bottom,g.price.bottom);assert.equal(volume.clip.bottom,g.volume.bottom);
   assert(price.alpha<.1&&volume.alpha<.1);assert.equal(actual.manual.regions.find(r=>r.id===id).price_bounds,null);
   if(id==='G1'){assert.equal(extent.left_edge,'OPEN_UNCERTAIN_MONTH_ANCHOR');const strokes=actual.paints.filter(p=>p.kind==='stroke'&&p.color===color&&p.clip?.y===g.price.top);assert(strokes.every(p=>!p.path.some(t=>t.kind==='rect')));assert.equal(actual.manual.regions[0].exact_start_date,null);}
   await page.locator('#chartWrap').screenshot({path:path.join(out,'after-'+id+'-'+size.width+'.png')});
   await page.locator('#regionEvidence').click();const evidence=await page.locator('#evidenceBody').textContent();assert(evidence.includes('顯示外包'));assert(evidence.includes('不是正式壓力上下界'));assert(evidence.includes(extent.price.low));assert(evidence.includes(extent.price.high));await page.locator('#dismiss').click();
   pass('actual canvas fill/stroke matches full source wick envelope and separate volume pane: '+id,size,{display:extent.price,source_bars:extent.included_source_bars});
  }
  // Calling the actual region renderers must leave MACD and pane gaps pixel-exact.
  const pixels=await page.evaluate(()=>{const ctx=$('chart').getContext('2d'),g=geometry,ratio=devicePixelRatio,w=$('chart').width,h=$('chart').height;const samples=[[g.macd.top,g.macd.bottom],[g.price.bottom+2,g.volume.top-2],[g.volume.bottom+2,g.macd.top-15]];const read=()=>samples.map(([a,b])=>Array.from(ctx.getImageData(0,Math.ceil(a*ratio),w,Math.max(1,Math.floor((b-a)*ratio))).data));const old=read(),x=g.price.x,y=v=>g.price.bottom-(Number(v)-g.priceLow)/(g.priceHigh-g.priceLow)*(g.price.bottom-g.price.top),step=(g.right-g.left)/(view.end-view.start+1),max=Math.max(1,...base().bars.slice(view.start,view.end+1).map(r=>Number(r.volume_shares_scaled)||0));drawRegionBands(ctx,x,y,g.price,g.volume,g.macd,step);drawRegionVolumeBands(ctx,x,g.volume,max,step);return {equal:JSON.stringify(old)===JSON.stringify(read()),cExtent:regionDisplay.c_right_extent};});assert(pixels.equal);assert.equal(pixels.cExtent,null);pass('real MACD and gaps pixel-exact after both overlay renderers; C-right has no closed envelope',size);
  await page.locator('#focusG2').click();
  const clipped=await page.evaluate(()=>{const e=regionDisplay.extents.G2;view.start=base().bars.findIndex(r=>r.date==='2023-06-01');view.end=base().bars.findIndex(r=>r.date==='2023-07-31');view.cursor=view.end;regionPaint.length=0;draw();return {extent:regionDisplay.extents.G2,geom:{low:geometry.priceLow,high:geometry.priceHigh,top:geometry.price.top,bottom:geometry.price.bottom,left:geometry.left,right:geometry.right},fills:regionPaint.filter(p=>p.kind==='fillRect'&&p.color==='#b7a2ef'),strokes:regionPaint.filter(p=>p.kind==='stroke'&&p.color==='#b7a2ef')};});
  assert.deepEqual(clipped.extent,oracle.extents.G2);assert(clipped.geom.high<Number(oracle.extents.G2.price.high));const cp=clipped.fills.find(p=>p.clip.y===clipped.geom.top);assert(cp.args[1]<clipped.geom.top);assert(cp.args[0]<clipped.geom.left);assert(cp.args[0]+cp.args[2]>clipped.geom.right);
  const topStroke=clipped.strokes.find(p=>p.clip?.y===clipped.geom.top);assert(topStroke.path.some(p=>p.kind==='rect'&&p.args[1]<clipped.geom.top));
  await page.locator('#chartWrap').screenshot({path:path.join(out,'clipped-G2-'+size.width+'.png')});pass('zoom/pan clips original full-section boundaries without recomputing extents, fake edge lines or price-axis expansion',size);
  // Distinct missing and zero display fixtures; source arrays/cases untouched.
  const missing=await page.evaluate(()=>{const saved=regionDisplay;regionDisplay=JSON.parse(JSON.stringify(saved));regionDisplay.extents.G2.volume.max_volume_shares_scaled=null;regionPaint.length=0;draw();const missingVolume=regionPaint.filter(p=>p.kind==='fillRect'&&p.color==='#b7a2ef'&&p.clip.y===geometry.volume.top).length;openRegion('G2');const text=$('evidenceBody').textContent;regionDisplay.extents.G2.volume.max_volume_shares_scaled='0';regionPaint.length=0;draw();const zero=regionPaint.filter(p=>p.kind==='fillRect'&&p.color==='#b7a2ef'&&p.clip.y===geometry.volume.top);regionDisplay=saved;$('evidence').hidden=true;draw();return {missingVolume,text,zero};});assert.equal(missing.missingVolume,0);assert(missing.text.includes('量圖資料不足'));assert.equal(missing.zero.length,1);assert.equal(missing.zero[0].args[3],0);pass('missing volume fixture shows insufficient data/no fake height; actual zero fixture stays zero-height',size);
  await page.locator('#months24').click();assert.equal(await page.evaluate(()=>view.end-view.start+1),486);assert.deepEqual(await page.evaluate(()=>[current.key,frame.frame_id,frame.as_of,current.source.id,frame.chart_base]),identity);assert.equal(await page.evaluate(()=>JSON.stringify(selected())),mainSelection);
  const event=page.waitForEvent('download');await page.locator('#download').click();const d=await event,downloaded=JSON.parse(fs.readFileSync(await d.path(),'utf8'));assert.equal(downloaded.schema_version,'manual-region-chart-selection/0.2');assert.deepEqual(downloaded.region_display,oracle);assert.equal(downloaded.manual_regions.original_reviews.g2.region.price_bounds,null);
  assert(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth));pass('return24/analysis/source/case/download precision and no horizontal overflow preserved',size);
  await page.selectOption('#asOf','2026-10-15');assert.equal(await page.evaluate(()=>regionDisplay),null);assert.equal(await page.evaluate(()=>selected().region_display),null);await page.selectOption('#stock','2884');assert.equal(await page.evaluate(()=>regionDisplay),null);pass('other dates and stocks cannot inherit extent layer',size);
  await context.close();
 }
 assert.deepEqual(errors,[]);assert.deepEqual(external,[]);
 fs.writeFileSync(path.join(out,'extent-report.json'),JSON.stringify({status:'PASS',browser:browser.version(),source_html_sha256:crypto.createHash('sha256').update(after).digest('hex'),before_html_sha256:crypto.createHash('sha256').update(before).digest('hex'),checks,javascript_errors:errors,external_requests:external,physical_android:'NOT_TESTED_NEW_BUILD',file_open:'PRIOR_POLICY_BLOCKER_NOT_RETRIED'},null,2));console.log('PASS',checks.length,'candle extent checks');
}catch(error){fs.writeFileSync(path.join(out,'extent-report.json'),JSON.stringify({status:'FAIL',error:error.stack,checks,javascript_errors:errors,external_requests:external},null,2));console.error(error);process.exitCode=1;}finally{if(browser)await browser.close();if(server)await new Promise(r=>server.close(r));}})();
