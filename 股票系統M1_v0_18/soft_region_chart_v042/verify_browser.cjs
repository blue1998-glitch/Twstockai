'use strict';
const fs=require('fs'),path=require('path'),http=require('http'),assert=require('assert/strict'),crypto=require('crypto');
const pw=require(path.join(process.env.CODEX_PRIMARY_RUNTIME_NODE_MODULES,'playwright'));
const root=__dirname,parent=fs.readFileSync(path.join(root,'../soft_region_chart/output/soft-v041/M1_v0_19_soft_regions_v041.html'));
const folder=path.resolve(process.env.M1_SOFT_DIR),after=fs.readFileSync(path.join(folder,'M1_v0_19_soft_regions_v042.html'));
const out=path.resolve(process.env.M1_SOFT_CHECKS);fs.mkdirSync(out,{recursive:true});
const checks=[],errors=[];let browser,server;
const pass=(name,size)=>checks.push({name,size,status:'PASS'});
(async()=>{try{
 browser=await pw.chromium.launch({headless:true,executablePath:process.env.CODEX_BROWSER_EXECUTABLE_PATH,args:['--no-sandbox','--disable-dev-shm-usage','--disable-gpu','--disable-software-rasterizer']});
 server=http.createServer((q,r)=>{if(q.url==='/qa-font.otf'){r.writeHead(200,{'Content-Type':'font/otf'});r.end(fs.readFileSync(process.env.M1_QA_FONT));return;}r.writeHead(200,{'Content-Type':'text/html;charset=utf-8'});const raw=q.url==='/before'?parent:after;r.end(raw.toString().replace('</head>',"<style>@font-face{font-family:'Noto Sans TC';src:url('/qa-font.otf')}</style></head>"));});await new Promise(r=>server.listen(0,'127.0.0.1',r));
 const origin='http://127.0.0.1:'+server.address().port;
 for(const size of [{width:390,height:844},{width:844,height:390},{width:320,height:740},{width:1280,height:900}]){
  const context=await browser.newContext({viewport:size,hasTouch:size.width!==1280,isMobile:size.width!==1280,deviceScaleFactor:1,acceptDownloads:true});
  const page=await context.newPage();page.on('pageerror',e=>errors.push(e.stack));
  // QA-only fallback for the host's missing CJK system font; both versions use
  // the same trusted local font. Production HTML has no font/network additions.
  await page.addInitScript(()=>{const p=CanvasRenderingContext2D.prototype,d=Object.getOwnPropertyDescriptor(p,'font');Object.defineProperty(p,'font',{configurable:true,get(){return d.get.call(this);},set(value){return d.set.call(this,value.replace(/system-ui/g,'"Noto Sans TC"'));}});});
  await page.goto(origin+'/before');await page.waitForFunction(()=>typeof regionDisplay!=='undefined'&&regionDisplay);await page.evaluate(()=>document.fonts.load('12px "Noto Sans TC"','中文＋−'));await page.evaluate(()=>draw());
  const old=await page.evaluate(()=>JSON.stringify(selected()));
  await page.locator('#focusG2').click();await page.locator('#chartWrap').screenshot({path:path.join(out,'before-G2-'+size.width+'.png')});
  await page.goto(origin+'/after');await page.waitForFunction(()=>typeof regionDisplay!=='undefined'&&regionDisplay);await page.evaluate(()=>document.fonts.load('12px "Noto Sans TC"','中文＋−'));await page.evaluate(()=>draw());
  const newValue=JSON.parse(await page.evaluate(()=>JSON.stringify(selected()))),oldValue=JSON.parse(old);
  assert.equal(newValue.view_version,'candle-region-chart-view/0.4.2');delete newValue.view_version;delete oldValue.view_version;assert.deepEqual(newValue,oldValue);
  pass('all selected numerical/source/manual/display fields exactly equal0.4.1 except view version',size);
  await page.evaluate(()=>{
   window.softPaint=[];window.inSoftPane=false;
   const pane=drawExtentPane;drawExtentPane=(...a)=>{window.inSoftPane=true;try{return pane(...a);}finally{window.inSoftPane=false;}};
   for(const name of ['fillRect','stroke','strokeRect']){const original=CanvasRenderingContext2D.prototype[name];CanvasRenderingContext2D.prototype[name]=function(...args){if(window.inSoftPane)softPaint.push({kind:name,alpha:this.globalAlpha,args});return original.apply(this,args);};}
  });
  const identity=await page.evaluate(()=>[frame.frame_id,frame.as_of,current.source.id,frame.chart_base]);
  for(const id of ['G2','G1']){
   await page.locator('#focus'+id).click();
   const result=await page.evaluate(()=>{softPaint.length=0;draw();return {paints:softPaint,extent:regionDisplay.extents[regionFocus],asOf:frame.as_of,priceBounds:regions.regions.find(r=>r.id===regionFocus).price_bounds};});
   assert(result.paints.filter(p=>p.kind==='fillRect').length>=2);assert.equal(result.paints.filter(p=>p.kind!=='fillRect').length,0);
   assert(result.paints.filter(p=>p.kind==='fillRect').every(p=>Math.abs(p.alpha-.12)<1e-9));assert.equal(result.priceBounds,null);assert.equal(result.asOf,'2026-10-16');
   await page.locator('#chartWrap').screenshot({path:path.join(out,'after-'+id+'-'+size.width+'.png')});
   pass(id+' actual renderer paints12% backgrounds and zero region perimeter strokes, formal bounds null',size);
  }
  await page.locator('#focusG2').click();
  const contrast=[];
  for(const value of ['0.08','0.12','0.20']){
   await page.selectOption('#regionShade',value);
   const v=await page.evaluate(()=>{
    const renderer=drawExtentPane,g=geometry,ctx=$('chart').getContext('2d'),w=$('chart').width;
    drawExtentPane=()=>{};draw();const plain=ctx.getImageData(0,Math.ceil(g.price.top),w,Math.floor(g.price.bottom-g.price.top)).data;
    drawExtentPane=renderer;softPaint.length=0;draw();const tinted=ctx.getImageData(0,Math.ceil(g.price.top),w,Math.floor(g.price.bottom-g.price.top)).data;
    let sum=0,max=0;for(let i=0;i<plain.length;i++){if(i%4===3)continue;const delta=Math.abs(plain[i]-tinted[i]);sum+=delta;max=Math.max(max,delta);}
    return {sum,max,alpha:softPaint.filter(p=>p.kind==='fillRect').map(p=>p.alpha),selection:JSON.stringify(selected())};
   });
   assert(v.alpha.every(a=>Math.abs(a-Number(value))<1e-9));contrast.push(v);
  }
  assert(contrast[0].sum<contrast[1].sum&&contrast[1].sum<contrast[2].sum);assert(contrast[1].max>=15);
  assert.equal(contrast[0].selection,contrast[1].selection);assert.equal(contrast[1].selection,contrast[2].selection);
  await page.selectOption('#regionShade','0.12');
  pass('three actual opacity choices visibly increase RGB contrast; default max contrast>=15; selections unchanged',size);
  const pixels=await page.evaluate(()=>{const g=geometry,ctx=$('chart').getContext('2d'),ratio=devicePixelRatio,w=$('chart').width;
   const read=()=>[[g.macd.top,g.macd.bottom],[g.price.bottom+2,g.volume.top-2],[g.volume.bottom+2,g.macd.top-15]].map(([a,b])=>Array.from(ctx.getImageData(0,Math.ceil(a*ratio),w,Math.max(1,Math.floor((b-a)*ratio))).data));
   const before=JSON.stringify(read()),x=g.price.x,y=v=>g.price.bottom-(Number(v)-g.priceLow)/(g.priceHigh-g.priceLow)*(g.price.bottom-g.price.top),step=(g.right-g.left)/(view.end-view.start+1),max=Math.max(1,...base().bars.slice(view.start,view.end+1).map(r=>Number(r.volume_shares_scaled)||0));
   drawRegionBands(ctx,x,y,g.price,g.volume,g.macd,step);drawRegionVolumeBands(ctx,x,g.volume,max,step);return before===JSON.stringify(read());});assert(pixels);
  pass('MACD and pane gaps remain pixel-exact after actual shade renderers',size);
  await page.locator('#focusG2').click();
  const clipped=await page.evaluate(()=>{const prior=JSON.stringify(regionDisplay);view.start=base().bars.findIndex(r=>r.date==='2023-06-01');view.end=base().bars.findIndex(r=>r.date==='2023-07-31');view.cursor=view.end;draw();return {same:prior===JSON.stringify(regionDisplay),high:geometry.priceHigh,fullHigh:regionDisplay.extents.G2.price.high};});
  assert(clipped.same);assert(clipped.high<Number(clipped.fullHigh));await page.locator('#chartWrap').screenshot({path:path.join(out,'clipped-G2-'+size.width+'.png')});
  await page.locator('#months24').click();assert.equal(await page.evaluate(()=>view.end-view.start+1),486);assert.deepEqual(await page.evaluate(()=>[frame.frame_id,frame.as_of,current.source.id,frame.chart_base]),identity);
  assert(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth));
  pass('clipping retains full original extent and return24 preserves486 bars/date/source, no overflow',size);
  const event=page.waitForEvent('download');await page.locator('#download').click();const d=await event;const downloaded=JSON.parse(fs.readFileSync(await d.path(),'utf8'));assert.equal(downloaded.view_version,'candle-region-chart-view/0.4.2');assert.deepEqual(downloaded.region_display,oldValue.region_display);
  pass('actual HTTP browser download preserves display data and identifies new style version',size);
  await context.close();
 }
 assert.deepEqual(errors,[]);
 fs.writeFileSync(path.join(out,'browser-report.json'),JSON.stringify({status:'PASS',checks,browser:browser.version(),html_sha256:crypto.createHash('sha256').update(after).digest('hex'),javascript_errors:errors,physical_android:'NOT_TESTED_NEW_BUILD',file_policy:'NOT_RETRIED_OR_BYPASSED'},null,2));console.log('PASS',checks.length,'focused HTTP checks');
}catch(e){fs.writeFileSync(path.join(out,'browser-report.json'),JSON.stringify({status:'FAIL',checks,error:e.stack},null,2));console.error(e);process.exitCode=1;}finally{if(browser)await browser.close();if(server)await new Promise(r=>server.close(r));}})();
