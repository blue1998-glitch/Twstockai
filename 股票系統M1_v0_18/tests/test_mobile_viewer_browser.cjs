// Real browser acceptance; use an existing Chromium only. Never install here.
const fs=require('fs'),path=require('path'),http=require('http'),assert=require('assert/strict');
const {pathToFileURL}=require('url');
const root=path.resolve(__dirname,'..'),out=path.resolve(process.env.M1_BROWSER_OUTPUT_DIR||path.join(root,'mobile_viewer/output/browser'));
const htmlPath=path.join(root,process.env.M1_BROWSER_HTML||'日週月研究對照_手機版_v0_18.html');
const annotated=path.basename(htmlPath)==='日週月研究對照_結構標記_v0_18.html';
const transport=process.env.M1_BROWSER_TRANSPORT||'file';
fs.mkdirSync(out,{recursive:true});
const cases=[],startedAt=new Date().toISOString();let browser,server;
function write(value){fs.writeFileSync(path.join(out,'手機版真實瀏覽器驗收.json'),JSON.stringify({started_at_utc:startedAt,ended_at_utc:new Date().toISOString(),html:path.basename(htmlPath),transport,physical_android_new_version:'NOT_TESTED',cases,...value},null,2))}
(async()=>{
 try{
  assert(['file','http'].includes(transport),'M1_BROWSER_TRANSPORT must be file or http');
  const playwright=require(process.env.CODEX_PRIMARY_RUNTIME_NODE_MODULES?path.join(process.env.CODEX_PRIMARY_RUNTIME_NODE_MODULES,'playwright'):'playwright');
  browser=await playwright.chromium.launch({headless:true,...(process.env.CODEX_BROWSER_EXECUTABLE_PATH?{executablePath:process.env.CODEX_BROWSER_EXECUTABLE_PATH}:{})});
  let url=pathToFileURL(htmlPath).href;
  if(transport==='http'){
   const content=fs.readFileSync(htmlPath);
   server=http.createServer((request,response)=>{
    if(request.url!=='/mobile.html'){response.writeHead(404);response.end();return}
    response.writeHead(200,{'Content-Type':'text/html; charset=utf-8','Cache-Control':'no-store'});response.end(content);
   });
   await new Promise((resolve,reject)=>{server.once('error',reject);server.listen(0,'127.0.0.1',resolve)});
   url='http://127.0.0.1:'+server.address().port+'/mobile.html';
  }
  const expected=JSON.parse(fs.readFileSync(path.join(root,'cross_view/output/日週月對照實算驗收.json'),'utf8'));
  const oracle=JSON.parse(fs.readFileSync(path.join(root,'mobile_viewer/output/顯示值獨立參照.json'),'utf8'));
  const viewports=[{width:1280,height:900},{width:390,height:844}];
  for(const viewport of viewports){
   const mobile=viewport.width===390,context=await browser.newContext({viewport,isMobile:mobile,hasTouch:mobile,deviceScaleFactor:mobile?3:1,acceptDownloads:true});
   const page=await context.newPage(),errors=[],externalRequests=[];
   page.on('pageerror',error=>errors.push(error.message));
   page.on('request',request=>{const requested=request.url();if(/^https?:/.test(requested)&&!(transport==='http'&&new URL(requested).origin===new URL(url).origin))externalRequests.push(requested)});
   await page.goto(url);assert(await page.locator('#result').isHidden());
   for(const originalCase of expected.cases){
    const row=oracle.cases.find(item=>item.case===originalCase.case);
    await page.selectOption('#stock',originalCase.exchange+' / '+originalCase.code);
    await page.selectOption('#mode',originalCase.price_mode);await page.selectOption('#date',originalCase.as_of);
    await page.selectOption('#daily',originalCase.daily_key);await page.selectOption('#period',originalCase.period_key);
    if(mobile)await page.locator('#load').tap();else await page.locator('#load').click();
    assert(await page.locator('#result').isVisible());assert.match(await page.locator('#badge').textContent(),/輸入對齊/);
    if(annotated){
     await page.selectOption('#annotationLevel','major');await page.selectOption('#annotationHistory','active');await page.selectOption('#annotationWindow','130');
     const saved=JSON.parse(fs.readFileSync(path.join(root,'cross_view/output',originalCase.case+'_VIEW.json'),'utf8'));
     const structure=saved.daily.snapshot.structure,dates=saved.daily.source_candles.slice(-130).map(bar=>bar.date);
     const wantedPivots=structure.pivots.filter(p=>p.profile==='major'&&dates.includes(p.occurred_at));
     const wantedZones=structure.zones.filter(z=>z.profile==='major'&&z.state==='ACTIVE_CANDIDATE'&&z.created_at<=dates.at(-1)&&!z.invalidated_at);
     const actual=await page.evaluate(()=>annotationState.items.map(item=>({type:item.type,saved:item.saved})));
     assert.deepEqual(actual.filter(item=>item.type==='pivot').map(item=>item.saved),wantedPivots);
     assert.deepEqual(actual.filter(item=>item.type==='zone').map(item=>item.saved),wantedZones);
     assert.equal(await page.locator('#annotationSelect option').count(),actual.length+1);
    }
    for(const basis of ['candidate','elapsed']){
     await page.selectOption('#basis',basis);
     const wanted={daily:row.daily,...row[basis]};
     for(const tf of ['daily','weekly','monthly']){
      const actual=await page.locator('#'+tf+'Values .amount').allTextContents();assert.equal(actual.length,wanted[tf].length);
      for(const [index,value] of wanted[tf].entries())if(value===null)assert.match(actual[index],/^— /);else assert.equal(actual[index],value);
     }
     const canvasState=await page.evaluate(()=>['daily','weekly','monthly'].map(tf=>{
      const canvas=document.getElementById(tf+'Chart'),rect=canvas.getBoundingClientRect(),ctx=canvas.getContext('2d');
      const pixels=ctx.getImageData(0,0,canvas.width,canvas.height).data;let hasDrawing=false;
      for(let index=3;index<pixels.length;index+=4)if(pixels[index]){hasDrawing=true;break}
      return {tf,width:canvas.width,height:canvas.height,expectedWidth:Math.round(rect.width*devicePixelRatio),expectedHeight:Math.round(rect.height*devicePixelRatio),hasDrawing};
     }));
     for(const canvas of canvasState){assert.equal(canvas.width,canvas.expectedWidth);assert.equal(canvas.height,canvas.expectedHeight);assert(canvas.hasDrawing)}
     assert(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth));
     assert(await page.locator('.value-table').evaluateAll(tables=>tables.every(table=>table.scrollWidth<=Math.ceil(table.getBoundingClientRect().width)+1)));
     const event=page.waitForEvent('download');if(mobile)await page.locator('#download').tap();else await page.locator('#download').click();
     const download=await event;assert.equal(await download.failure(),null);
     const actual=JSON.parse(fs.readFileSync(await download.path(),'utf8'));
     const wantedDownload=JSON.parse(fs.readFileSync(path.join(root,'cross_view/output',originalCase.case+'_VIEW.json'),'utf8'));
     assert.deepEqual(actual,wantedDownload);
     cases.push({viewport,case:originalCase.case,basis,status:'PASS',download_exact:true,display_two_decimals:true,canvas_backing:canvasState});
    }
    if(originalCase.price_mode==='ADJUSTED_CANDIDATE')assert.match(await page.locator('#dailyFacts').textContent(),/還原日 K 沒有存入/);
    if(annotated){
     const exact=await page.evaluate(()=>JSON.stringify(current));
     const visible=await page.evaluate(()=>annotationState.items.map(item=>({key:item.key,saved:item.saved})));
     if(visible.length){
      await page.selectOption('#annotationSelect',visible[0].key);
      assert((await page.locator('#annotationDetail').textContent()).includes(visible[0].saved.id));
      await page.locator('#dailyChart').scrollIntoViewIfNeeded();
      const hit=await page.evaluate(()=>annotationState.hits.find(item=>item.type==='pivot'));
      if(hit){const rect=await page.locator('#dailyChart').boundingBox();
       if(mobile)await page.touchscreen.tap(rect.x+hit.x,rect.y+hit.y);else await page.mouse.click(rect.x+hit.x,rect.y+hit.y);
       assert(await page.evaluate(()=>annotationState.selected.startsWith('pivot:')));
      }
     }
     if(originalCase.code==='8069'&&originalCase.as_of==='2026-09-30'&&originalCase.structure_version==='structure-0.3-research'){
      await page.locator('#dailyBoard').screenshot({path:path.join(out,viewport.width+'-'+originalCase.price_mode+'-annotations.png')});
      await page.screenshot({path:path.join(out,viewport.width+'-'+originalCase.price_mode+'-page.png'),fullPage:true});
     }
     await page.selectOption('#annotationLevel','both');await page.selectOption('#annotationHistory','all');await page.selectOption('#annotationWindow','all');
     assert(await page.evaluate(()=>annotationState.items.every(item=>item.type!=='zone'||(item.start>=item.saved.created_at&&(!item.saved.invalidated_at||item.end<=item.saved.invalidated_at)))));
     await page.selectOption('#annotationLevel','off');assert.equal(await page.evaluate(()=>annotationState.items.length),0);
     assert.equal(await page.evaluate(()=>JSON.stringify(current)),exact);
     assert(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth));
    }
   }
   const before=await page.evaluate(()=>JSON.stringify(current));
   await page.setViewportSize({width:mobile?844:1000,height:mobile?390:900});
   await page.waitForFunction(()=>['daily','weekly','monthly'].every(tf=>{const canvas=document.getElementById(tf+'Chart');return canvas.width===Math.round(canvas.getBoundingClientRect().width*devicePixelRatio)}));
   assert.equal(await page.evaluate(()=>JSON.stringify(current)),before);
   assert.deepEqual(errors,[]);assert.deepEqual(externalRequests,[]);await context.close();
  }
  write({status:'PASS',browser_version:browser.version(),method:'Real Chromium/Playwright; mobile emulation is not physical Android',completed_downloads:cases.length});
 }catch(error){
  const blocked=/Executable doesn't exist|Cannot find module|ERR_BLOCKED_BY_ADMINISTRATOR/.test(error.message);
  write({status:blocked?'BLOCKED':'FAIL',reason:error.message,completed_downloads:cases.length});process.exitCode=blocked?2:1;
 }finally{
  if(browser)await browser.close();if(server)await new Promise(resolve=>server.close(resolve));
 }
})();
