// Actual Chromium interactions; synthetic gestures do not establish Android QA.
const fs=require('fs'),path=require('path'),http=require('http'),assert=require('assert/strict'),crypto=require('crypto');
const folder=path.resolve(process.env.M1_CANDIDATE_DIR),out=path.resolve(process.env.M1_BROWSER_OUTPUT_DIR);
fs.mkdirSync(out,{recursive:true});const source=fs.readFileSync(path.join(folder,'M1_v0_19_candidate.html'));
const payload=JSON.parse(fs.readFileSync(path.join(folder,'candidate.json'),'utf8'));
const oracle=JSON.parse(fs.readFileSync(path.join(folder,'selection-oracle.json'),'utf8'));
const canonical=v=>Array.isArray(v)?'['+v.map(canonical).join(',')+']':v&&typeof v==='object'?'{'+Object.keys(v).sort().map(k=>JSON.stringify(k)+':'+canonical(v[k])).join(',')+'}':JSON.stringify(v);
const hash=v=>'sha256:'+crypto.createHash('sha256').update(canonical(v)).digest('hex');
const checks=[],started=new Date().toISOString();let browser,server;
function record(name,data={}){checks.push({name,status:'PASS',...data})}
(async()=>{try{
 const playwright=require(process.env.CODEX_PRIMARY_RUNTIME_NODE_MODULES?path.join(process.env.CODEX_PRIMARY_RUNTIME_NODE_MODULES,'playwright'):'playwright');
 browser=await playwright.chromium.launch({headless:true,executablePath:process.env.CODEX_BROWSER_EXECUTABLE_PATH||'/usr/bin/chromium'});
 server=http.createServer((req,res)=>{if(req.url!=='/candidate.html'){res.writeHead(404);res.end();return}res.writeHead(200,{'Content-Type':'text/html; charset=utf-8'});res.end(source)});
 await new Promise((resolve,reject)=>{server.once('error',reject);server.listen(0,'127.0.0.1',resolve)});
 const url='http://127.0.0.1:'+server.address().port+'/candidate.html';
 for(const viewport of [{width:1280,height:900},{width:390,height:844}]){
  const mobile=viewport.width===390,context=await browser.newContext({viewport,isMobile:mobile,hasTouch:mobile,deviceScaleFactor:mobile?2:1,acceptDownloads:true});
  const page=await context.newPage(),errors=[],external=[];page.on('pageerror',e=>errors.push(e.message));page.on('request',r=>{if(/^https?:/.test(r.url())&&new URL(r.url()).origin!==new URL(url).origin)external.push(r.url())});
  const tick=Date.now();await page.goto(url);assert(await page.locator('#result').isHidden());record('initial blank selection',{viewport,load_ms:Date.now()-tick});
  for(const row of oracle.cases){
   await page.selectOption('#series',row.series);await page.selectOption('#asOf',row.as_of);if(mobile)await page.locator('#load').tap();else await page.locator('#load').click();
   assert.equal(await page.evaluate(()=>frame.frame_id),row.frame_id);
   assert((await page.locator('#unknown').textContent()).includes('未知'));
   const canvas=await page.locator('canvas').evaluateAll(nodes=>nodes.map(c=>({width:c.width,wanted:Math.round(c.getBoundingClientRect().width*devicePixelRatio),height:c.height,painted:c.getContext('2d').getImageData(0,0,c.width,c.height).data.some((v,i)=>i%4===3&&v>0)})));
   for(const c of canvas){assert.equal(c.width,c.wanted);assert(c.painted)}
   assert(await page.evaluate(()=>geometry.price.x(view.cursor)===geometry.volume.x(view.cursor)&&geometry.price.x(view.cursor)===geometry.macd.x(view.cursor)));
   const event=page.waitForEvent('download');if(mobile)await page.locator('#download').tap();else await page.locator('#download').click();const download=await event;assert.equal(await download.failure(),null);
   const value=JSON.parse(fs.readFileSync(await download.path(),'utf8'));assert.equal(hash(value),row.selection_fingerprint);
   assert.equal(value.bars.at(-1).date,row.as_of);assert(value.known_events.every(e=>e.effective_date<=row.as_of));assert.equal(value.frame.lifecycle.stage,'UNKNOWN');
   assert.equal(value.frame.action_qualification,'NOT_EVALUATED');assert(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth));
   record('exact analysis replay and independent Python JSON oracle',{viewport,series:row.series,as_of:row.as_of,bars:value.bars.length});
  }
  const s=payload.series.find(s=>s.code==='1101'&&s.price_mode==='RAW_CANDIDATE');
  await page.selectOption('#series',s.key);await page.selectOption('#asOf',s.available_end);await page.locator('#load').click();
  const frameId=await page.evaluate(()=>frame.frame_id);
  await page.locator('#from').fill(s.frames[20].as_of);await page.locator('#to').fill(s.frames[120].as_of);await page.locator('#applyRange').click();
  assert.deepEqual(await page.evaluate(()=>[view.start,view.end]),[20,120]);record('arbitrary available date window',{viewport});
  const n=await page.evaluate(()=>view.end-view.start);await page.locator('#zoomIn').click();assert(await page.evaluate(()=>view.end-view.start)<n);await page.locator('#zoomOut').click();
  await page.locator('#left').click();const left=await page.evaluate(()=>view.start);await page.locator('#right').click();assert(await page.evaluate(()=>view.start)>left);
  await page.locator('#priceControls summary').click();await page.locator('#priceIn').click();assert(await page.evaluate(()=>view.priceSpan!==null));const center=await page.evaluate(()=>view.priceCenter);await page.locator('#priceUp').click();assert(await page.evaluate(()=>view.priceCenter)>center);await page.locator('#priceDown').click();await page.locator('#priceOut').click();await page.locator('#priceAuto').click();assert(await page.evaluate(()=>view.priceSpan===null));await page.locator('#priceControls summary').click();
  assert.equal(await page.evaluate(()=>frame.frame_id),frameId);record('time and price controls preserve candidate frame',{viewport});
  await page.locator('#from').fill(s.frames[40].as_of);await page.locator('#to').fill(s.frames[140].as_of);await page.locator('#applyRange').click();await page.selectOption('#interaction','pan');await page.locator('#price').scrollIntoViewIfNeeded();
  const rect=await page.locator('#price').boundingBox(),before=await page.evaluate(()=>view.start);
  if(mobile){
   const cdp=await context.newCDPSession(page);const send=(type,points)=>cdp.send('Input.dispatchTouchEvent',{type,touchPoints:points});
   const y=rect.y+120,x=rect.x+rect.width*.5;
   await send('touchStart',[{id:0,x:x-40,y}]);for(let dx=10;dx<=60;dx+=10)await send('touchMove',[{id:0,x:x-40+dx,y}]);await send('touchEnd',[]);
   assert.notEqual(await page.evaluate(()=>view.start),before);record('actual injected one-finger chart pan',{viewport});
   const count=await page.evaluate(()=>view.end-view.start);
   await send('touchStart',[{id:0,x:x-45,y},{id:1,x:x+45,y}]);for(let dx=10;dx<=35;dx+=5)await send('touchMove',[{id:0,x:x-45-dx,y},{id:1,x:x+45+dx,y}]);await send('touchEnd',[]);
   assert(await page.evaluate(()=>view.end-view.start)<count);record('actual injected two-finger pinch',{viewport});
   await page.selectOption('#interaction','scroll');await page.locator('#price').scrollIntoViewIfNeeded();const box=await page.locator('#price').boundingBox(),scroll=await page.evaluate(()=>scrollY);
   await send('touchStart',[{id:0,x:box.x+100,y:box.y+150}]);for(let dy=20;dy<=100;dy+=20)await send('touchMove',[{id:0,x:box.x+100,y:box.y+150-dy}]);await send('touchEnd',[]);
   await page.waitForFunction(old=>scrollY!==old,scroll,{timeout:4000});record('scroll mode preserves native page scroll',{viewport});
  }else{
   await page.mouse.move(rect.x+rect.width*.4,rect.y+100);await page.mouse.down();await page.mouse.move(rect.x+rect.width*.55,rect.y+100,{steps:8});await page.mouse.up();assert.notEqual(await page.evaluate(()=>view.start),before);record('actual mouse drag pan',{viewport});
  }
  await page.locator('#price').scrollIntoViewIfNeeded();const box=await page.locator('#price').boundingBox();if(mobile)await page.touchscreen.tap(box.x+box.width*.6,box.y+100);else await page.mouse.click(box.x+box.width*.6,box.y+100);
  const cursorDate=await page.evaluate(()=>base().bars[view.cursor].date);assert((await page.locator('#cursorValues').textContent()).includes(cursorDate));await page.locator('#inspectDate').click();assert.equal(await page.evaluate(()=>frame.as_of),cursorDate);record('shared cursor can replay its exact historical frame',{viewport});
  await page.selectOption('#asOf',s.available_end);await page.locator('#load').click();await page.locator('#reset').click();assert.deepEqual(await page.evaluate(()=>[view.start,view.end]),[0,s.frames.length-1]);
  await page.locator('#full').click();assert(await page.evaluate(()=>!!document.fullscreenElement||document.body.classList.contains('focus')));record('native fullscreen or explicit focus fallback',{viewport,native:await page.evaluate(()=>!!document.fullscreenElement)});await page.locator('#exitFocus').click();
  await page.locator('#charts').screenshot({path:path.join(out,viewport.width+'-charts.png')});await page.screenshot({path:path.join(out,viewport.width+'-page.png'),fullPage:true});
  const beforeRotate=await page.evaluate(()=>frame.frame_id);await page.setViewportSize({width:mobile?844:1000,height:mobile?390:900});await page.waitForFunction(()=>document.getElementById('price').width===Math.round(document.getElementById('price').getBoundingClientRect().width*devicePixelRatio));assert.equal(await page.evaluate(()=>frame.frame_id),beforeRotate);assert(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth));await page.locator('#charts').screenshot({path:path.join(out,(mobile?'844-landscape':'1000-resize')+'.png')});record('orientation/resize with unchanged analysis',{viewport});
  assert.deepEqual(errors,[]);assert.deepEqual(external,[]);record('no JS errors or external requests',{viewport});await context.close();
 }
 fs.writeFileSync(path.join(out,'browser-report.json'),JSON.stringify({status:'PASS',started_at_utc:started,ended_at_utc:new Date().toISOString(),browser:browser.version(),source_html_sha256:crypto.createHash('sha256').update(source).digest('hex'),checks,exact_downloads:checks.filter(c=>c.name==='exact analysis replay and independent Python JSON oracle').length,physical_android:'NOT_TESTED',core_product_acceptance:'NOT_ESTABLISHED'},null,2));
}catch(error){fs.writeFileSync(path.join(out,'browser-report.json'),JSON.stringify({status:'FAIL',error:error.stack,checks,physical_android:'NOT_TESTED'},null,2));process.exitCode=1}finally{if(browser)await browser.close();if(server)await new Promise(resolve=>server.close(resolve))}})();
