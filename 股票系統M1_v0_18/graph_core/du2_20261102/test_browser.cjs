'use strict';
// Old real prefix plus SYNTHETIC new days; no actual new-session claim.
const fs=require('fs'),path=require('path'),assert=require('assert/strict'),{isDeepStrictEqual}=require('util');
const input=JSON.parse(fs.readFileSync(process.env.DU2_BROWSER_INPUT)),out=process.env.DU2_BROWSER_OUT;
fs.mkdirSync(out,{recursive:true});let browser;const checks=[],errors=[],external=[];
const same=(a,b)=>assert(isDeepStrictEqual(a,b),'Stored value mismatch (private values omitted)');
(async()=>{try{
 const {chromium}=require(path.join(process.env.CODEX_PRIMARY_RUNTIME_NODE_MODULES,'playwright'));
 browser=await chromium.launch({headless:true,executablePath:'/usr/bin/chromium'});
 for(const [width,height] of [[1280,900],[390,844],[844,390]]){
  const ctx=await browser.newContext({viewport:{width,height},isMobile:width<900,hasTouch:width<900,acceptDownloads:true,httpCredentials:input.httpCredentials}),p=await ctx.newPage();p.setDefaultTimeout(60000);
  p.on('pageerror',e=>errors.push(e.message));p.on('request',r=>{if(/^http/.test(r.url())&&new URL(r.url()).origin!==input.origin)external.push(r.url());});
  await p.goto(input.origin+'/batches');assert.equal(await p.locator('a').count(),3);assert(await p.evaluate(()=>document.documentElement.scrollWidth<=innerWidth));checks.push({width,name:'old-and-two-synthetic-batches-private-selector',status:'PASS'});
  for(const [i,b] of input.batches.entries()){
   await p.goto(input.origin+'/batches');await p.locator('a[href="'+b.route+'"]').click();await p.waitForFunction(()=>window.marketState);
   assert.equal(await p.evaluate(()=>marketState.summary.as_of),b.as_of);assert.equal(await p.evaluate(()=>marketState.stocks.length),b.expected_count);assert(await p.evaluate(()=>document.documentElement.scrollWidth<=innerWidth));checks.push({width,name:'batch-cutoff-identity-no-overflow',synthetic_new_day:b.synthetic_new_day,status:'PASS'});
   for(const s of b.stocks){
    await p.fill('#marketSearch',s.code);await p.locator('#marketResults button').click();await p.waitForFunction(code=>current.code===code&&!document.querySelector('main').hidden,s.code);
    assert.equal(await p.evaluate(()=>data.series.length),1);assert.equal(await p.evaluate(()=>result.as_of),b.as_of);assert.equal(await p.evaluate(()=>bars().length),s.records);assert(await p.evaluate(()=>geometry.price.x===geometry.volume.x&&geometry.price.x===geometry.macd.x));
    const e=p.waitForEvent('download');await p.click('#download');const dl=await e,actual=JSON.parse(fs.readFileSync(await dl.path())),expected=JSON.parse(fs.readFileSync(s.expected));
    same(actual.core,expected.results[0]);same(actual.bars,expected.bars);same(actual.macd,expected.macd);same(actual.moving_averages,expected.moving_averages);assert.equal(actual.core.comparison.primary_pressure_id,null);
    const old=await p.evaluate(()=>view.end-view.start);await p.click('#zoomIn');assert(await p.evaluate(()=>view.end-view.start)<old);await p.click('#left');assert.equal(await p.evaluate(()=>result.as_of),b.as_of);await p.click('#all');
    if(width<900){await p.selectOption('#interaction','query');await p.locator('#chart').scrollIntoViewIfNeeded();const z=await p.locator('#chart').boundingBox();await p.touchscreen.tap(z.x+z.width*.4,z.y+Math.min(z.height*.3,90));assert.equal(await p.evaluate(()=>result.as_of),b.as_of);}
    checks.push({width,name:'exact-core-candles-volume-ma-macd-download-and-navigation',synthetic_new_day:b.synthetic_new_day,status:'PASS'});
   }
   await p.screenshot({path:path.join(out,(b.synthetic_new_day?'synthetic-':'retained-')+i+'-'+width+'.png'),fullPage:true});
  }
  await ctx.close();
 }
 same(errors,[]);same(external,[]);fs.writeFileSync(path.join(out,'report.json'),JSON.stringify({status:'PASS',checks,exact_downloads:18,javascript_errors:errors,external_requests:external,real_new_session:false,android:'NOT_TESTED_NEW_BUILD'},null,2));console.log('PASS',checks.length,'private storage/browser checks');
}catch(e){fs.writeFileSync(path.join(out,'report.json'),JSON.stringify({status:'FAIL',error:e.stack,checks,errors,external},null,2));console.error(e);process.exitCode=1;}finally{if(browser)await browser.close();}})();
