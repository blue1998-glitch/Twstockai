'use strict';
// Quotes, screenshots and downloaded JSON remain exclusively in external output.
const {isDeepStrictEqual}=require('util');const equal=(a,b)=>assert(isDeepStrictEqual(a,b),'Stored data mismatch (restricted values omitted)');
const fs=require('fs'),path=require('path'),http=require('http'),assert=require('assert/strict');
const input=JSON.parse(fs.readFileSync(process.env.FM3_BROWSER_INPUT)),out=process.env.FM3_BROWSER_OUT;
fs.mkdirSync(out,{recursive:true});let browser,server;const checks=[],errors=[],external=[];
(async()=>{try{
 const pw=require(path.join(process.env.CODEX_PRIMARY_RUNTIME_NODE_MODULES,'playwright'));
 browser=await pw.chromium.launch({headless:true,executablePath:'/usr/bin/chromium'});
 const dir=path.dirname(input.html);
 server=http.createServer((q,r)=>{const name=decodeURIComponent(q.url.split('?')[0]).replace(/^\//,'')||path.basename(input.html);if(name.includes('/')||name.includes('..')){r.writeHead(403);r.end();return;}const f=path.join(dir,name);if(!fs.existsSync(f)){r.writeHead(404);r.end();return;}r.writeHead(200,{'Content-Type':name.endsWith('.json')?'application/json':'text/html; charset=utf-8'});fs.createReadStream(f).pipe(r);});
 await new Promise(r=>server.listen(0,'127.0.0.1',r));const origin='http://127.0.0.1:'+server.address().port;
 for(const [width,height] of [[1280,900],[390,844],[844,390],[320,800]]){
  const ctx=await browser.newContext({viewport:{width,height},isMobile:width<900,hasTouch:width<900,acceptDownloads:true}),p=await ctx.newPage();
  p.on('pageerror',e=>errors.push(e.message));p.on('request',r=>{if(/^http/.test(r.url())&&new URL(r.url()).origin!==origin)external.push(r.url());});
  await p.goto(origin+'/'+path.basename(input.html));await p.waitForFunction(()=>typeof marketState!=='undefined');
  assert.equal(await p.evaluate(()=>marketState.stocks.length),input.expected);assert(await p.evaluate(()=>document.documentElement.scrollWidth<=innerWidth));checks.push({width,height,name:'searchable-reference-and-no-overflow',status:'PASS'});
  for(const selected of input.cases){
   await p.fill('#marketSearch',selected.code);const button=p.locator('#marketResults button').filter({hasText:'看原核心'});assert.equal(await button.count(),1);await button.click();
   await p.waitForFunction(code=>current.code===code&&!document.querySelector('main').hidden,selected.code);
   assert.equal(await p.evaluate(()=>result.as_of),input.as_of);assert.equal(await p.evaluate(()=>bars().length),selected.records);
   assert.equal(await p.evaluate(()=>result.comparison.primary_pressure_id),null);
   assert.equal(await p.evaluate(()=>geometry.price.x===geometry.volume.x&&geometry.price.x===geometry.macd.x),true);
   assert.equal(await p.evaluate(()=>data.series.length),1); // bounded lazy loading, no numerical sampling
   const event=p.waitForEvent('download');await p.click('#download');const download=await event;const raw=fs.readFileSync(await download.path());const actual=JSON.parse(raw),expected=JSON.parse(fs.readFileSync(selected.saved_result)).value;
   equal(actual.core,expected.result);equal(actual.bars,expected.input.bars);equal(actual.macd,expected.indicators.macd);equal(actual.moving_averages,expected.indicators.moving_averages);
   assert.equal(actual.source_input_binding.source_role,'FINMIND_FREE_INDIVIDUAL_HISTORY_NOT_OFFICIAL_MONTHLY_OR_NATIVE_BULK');
   if(selected.records>34){const before=await p.evaluate(()=>view.end-view.start);await p.click('#zoomIn');assert(await p.evaluate(()=>view.end-view.start)<before);await p.click('#left');assert.equal(await p.evaluate(()=>result.as_of),input.as_of);await p.click('#all');assert.equal(await p.evaluate(()=>view.end-view.start+1),selected.records);}
   else{assert(await p.locator('#zoomIn').isDisabled());assert(actual.macd.every(m=>m.histogram===null));}
   const gap=actual.bars.find(b=>b.close===null);
   if(gap){await p.selectOption('#queryDate',gap.date);assert((await p.locator('#readout').textContent()).includes('缺值'));assert(await p.evaluate(()=>geometry.priceLow>0));}
   if(width<900&&selected.records>34){await p.selectOption('#interaction','query');await p.locator('#chart').scrollIntoViewIfNeeded();const b=await p.locator('#chart').boundingBox();await p.touchscreen.tap(b.x+b.width*.3,b.y+Math.min(b.height*.3,100));assert.equal(await p.evaluate(()=>result.as_of),input.as_of);}
   checks.push({width,height,name:'stored-stock-source-candles-volume-macd-core-exact-download-navigation-touch',status:'PASS',history_records:selected.records});
  }
  await p.fill('#marketSearch','NO_SUCH_SECURITY');assert.equal(await p.locator('#marketResults button').count(),0);checks.push({width,height,name:'empty-search-not-another-stock',status:'PASS'});
  await p.screenshot({path:path.join(out,'private-'+width+'x'+height+'.png'),fullPage:true});await ctx.close();
 }
 assert.deepEqual(errors,[]);assert.deepEqual(external,[]);
 fs.writeFileSync(path.join(out,'report.json'),JSON.stringify({status:'PASS',checks,javascript_errors:errors,external_requests:external,android:'NOT_TESTED_NEW_BUILD'},null,2));console.log('PASS',checks.length,'private Chromium checks');
}catch(e){fs.writeFileSync(path.join(out,'report.json'),JSON.stringify({status:'FAIL',error:e.stack,checks,errors,external},null,2));console.error(e);process.exitCode=1;}finally{if(browser)await browser.close();if(server)await new Promise(r=>server.close(r));}})();
