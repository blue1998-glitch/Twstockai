'use strict';
// Real old preview smoke only, no full history acceptance or new-day claim.
const fs=require('fs'),path=require('path'),assert=require('assert/strict'),{isDeepStrictEqual}=require('util');
const input=JSON.parse(fs.readFileSync(process.env.DU1_RETAINED_INPUT)),out=process.env.DU1_RETAINED_OUT;
fs.mkdirSync(out,{recursive:true});let browser;const checks=[],errors=[],external=[];
(async()=>{try{
const {chromium}=require(path.join(process.env.CODEX_PRIMARY_RUNTIME_NODE_MODULES,'playwright'));
browser=await chromium.launch({headless:true,executablePath:'/usr/bin/chromium'});
for(const [width,height] of [[390,844],[844,390]]){
 const ctx=await browser.newContext({viewport:{width,height},isMobile:true,hasTouch:true,acceptDownloads:true,httpCredentials:input.httpCredentials}),p=await ctx.newPage();
 p.on('pageerror',e=>errors.push(e.message));p.on('request',r=>{if(/^http/.test(r.url())&&new URL(r.url()).origin!==input.origin)external.push(r.url());});
 await p.goto(input.origin+'/'+path.basename(input.html));await p.waitForFunction(()=>window.marketState);
 assert.equal(await p.evaluate(()=>marketState.stocks.filter(s=>s.preview_series).length),1469);assert(await p.evaluate(()=>document.documentElement.scrollWidth<=innerWidth));
 checks.push({width,name:'retained-old-date-and-1469-descriptors-not-full-source-revalidation',status:'PASS'});
 for(const s of input.cases){
  await p.fill('#marketSearch',s.code);await p.locator('#marketResults button').click();await p.waitForFunction(code=>current.code===code&&!document.querySelector('main').hidden,s.code);
  assert.equal(await p.evaluate(()=>data.series.length),1);assert.equal(await p.evaluate(()=>result.as_of),input.as_of);assert.equal(await p.evaluate(()=>bars().length),s.records);
  const event=p.waitForEvent('download');await p.click('#download');const dl=await event,actual=JSON.parse(fs.readFileSync(await dl.path())),saved=JSON.parse(fs.readFileSync(s.saved_result)).value;
  assert(isDeepStrictEqual(actual.core,saved.result),'Saved core mismatch, restricted values omitted');assert(isDeepStrictEqual(actual.bars,saved.input.bars),'Saved bars mismatch, values omitted');
  checks.push({width,name:'retained-stock-exact-core-and-bars-lazy-download-no-new-day',status:'PASS'});
 }
 await ctx.close();
}
assert.deepEqual(errors,[]);assert.deepEqual(external,[]);
fs.writeFileSync(path.join(out,'report.json'),JSON.stringify({status:'PASS',scope:'ORIGINAL_20261030_RETAINED_PREVIEW_SMOKE_NOT_NEW_SESSION',checks,javascript_errors:errors,external_requests:external,android:'NOT_TESTED_NEW_BUILD'},null,2));console.log('PASS',checks.length,'retained-preview checks');
}catch(e){fs.writeFileSync(path.join(out,'report.json'),JSON.stringify({status:'FAIL',error:e.stack,checks,errors,external},null,2));console.error(e);process.exitCode=1;}finally{if(browser)await browser.close();}})();
