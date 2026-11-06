'use strict';
// Only synthetic batches. Credentials, screenshots, downloads live outside Git.
const fs=require('fs'),path=require('path'),assert=require('assert/strict'),{isDeepStrictEqual}=require('util');
const input=JSON.parse(fs.readFileSync(process.env.DU1_BROWSER_INPUT)),out=process.env.DU1_BROWSER_OUT;
fs.mkdirSync(out,{recursive:true});let browser;const checks=[],errors=[],external=[];
const equal=(a,b)=>assert(isDeepStrictEqual(a,b),'Synthetic saved output mismatch');
(async()=>{try{
const {chromium}=require(path.join(process.env.CODEX_PRIMARY_RUNTIME_NODE_MODULES,'playwright'));
browser=await chromium.launch({headless:true,executablePath:'/usr/bin/chromium'});
for(const [width,height] of [[1280,900],[390,844],[844,390],[320,800]]){
 const ctx=await browser.newContext({viewport:{width,height},isMobile:width<900,hasTouch:width<900,acceptDownloads:true,httpCredentials:input.httpCredentials}),p=await ctx.newPage();
 p.on('pageerror',e=>errors.push(e.message));p.on('request',r=>{if(/^http/.test(r.url())&&new URL(r.url()).origin!==input.origin)external.push(r.url());});
 await p.goto(input.origin+'/batches');assert.equal(await p.locator('a').count(),2);assert(await p.evaluate(()=>document.documentElement.scrollWidth<=innerWidth));checks.push({width,name:'two-saved-batches-authenticated-selector-no-overflow',status:'PASS'});
 for(const b of input.batches){
  await p.goto(input.origin+'/batches');await p.locator('a[href="'+b.route+'"]').click();await p.waitForFunction(()=>window.marketState);
  assert.equal(await p.evaluate(()=>marketState.summary.as_of),b.as_of);assert.equal(await p.evaluate(()=>marketState.stocks.length),2);assert(await p.evaluate(()=>document.documentElement.scrollWidth<=innerWidth));
  checks.push({width,name:'selected-batch-date-and-reference-exact-no-overflow',status:'PASS'});
  for(const s of b.cases){
   await p.fill('#marketSearch',s.code);await p.locator('#marketResults button').click();await p.waitForFunction(code=>current.code===code&&!document.querySelector('main').hidden,s.code);
   assert.equal(await p.evaluate(()=>data.series.length),1);assert.equal(await p.evaluate(()=>result.as_of),b.as_of);assert.equal(await p.evaluate(()=>bars().length),s.records);
   assert(await p.evaluate(()=>geometry.price.x===geometry.volume.x&&geometry.price.x===geometry.macd.x));
   const downloadEvent=p.waitForEvent('download');await p.click('#download');const dl=await downloadEvent,actual=JSON.parse(fs.readFileSync(await dl.path())),expected=JSON.parse(fs.readFileSync(s.expected));
   equal(actual.core,expected.core);equal(actual.bars,expected.bars);equal(actual.macd,expected.macd);equal(actual.moving_averages,expected.moving_averages);
   assert.equal(actual.macd.at(-1).histogram,null);assert.equal(actual.source_input_binding.source_role,'SEGMENTED_NOT_CERTIFIED_CONTINUOUS');assert.equal(actual.core.comparison.primary_pressure_id,null);
   const old=await p.evaluate(()=>view.end-view.start);await p.click('#zoomIn');assert(await p.evaluate(()=>view.end-view.start)<old);await p.click('#left');assert.equal(await p.evaluate(()=>result.as_of),b.as_of);await p.click('#all');
   if(width<900){await p.selectOption('#interaction','query');await p.locator('#chart').scrollIntoViewIfNeeded();const z=await p.locator('#chart').boundingBox();await p.touchscreen.tap(z.x+z.width*.3,z.y+Math.min(z.height*.3,100));assert.equal(await p.evaluate(()=>result.as_of),b.as_of);}
   checks.push({width,name:'lazy-stock-exact-download-indicators-reset-synchronized-navigation-touch',status:'PASS'});
  }
  await p.screenshot({path:path.join(out,'synthetic-'+b.as_of+'-'+width+'.png'),fullPage:true});
 }
 await ctx.close();
}
assert.deepEqual(errors,[]);assert.deepEqual(external,[]);
fs.writeFileSync(path.join(out,'report.json'),JSON.stringify({status:'PASS',synthetic:true,checks,javascript_errors:errors,external_requests:external,android:'NOT_TESTED_NEW_BUILD'},null,2));console.log('PASS',checks.length,'synthetic Chromium checks');
}catch(e){fs.writeFileSync(path.join(out,'report.json'),JSON.stringify({status:'FAIL',synthetic:true,error:e.stack,checks,errors,external},null,2));console.error(e);process.exitCode=1;}finally{if(browser)await browser.close();}})();
