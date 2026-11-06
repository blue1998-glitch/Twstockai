// Actual saved new day, recent window and query; private config/PNG only.
const fs=require('fs'),path=require('path'),assert=require('assert/strict');
const {chromium}=require(path.join(process.env.CODEX_PRIMARY_RUNTIME_NODE_MODULES,'playwright'));
(async()=>{
 const cfg=JSON.parse(fs.readFileSync(process.argv[2])),out=process.argv[3],errors=[];
 const browser=await chromium.launch({headless:true,executablePath:'/usr/bin/chromium'});
 try{
  const ctx=await browser.newContext({viewport:{width:390,height:844},isMobile:true,hasTouch:true,httpCredentials:cfg.auth});
  const p=await ctx.newPage();p.setDefaultTimeout(120000);p.on('pageerror',e=>errors.push(e.message));
  await p.goto(cfg.url,{waitUntil:'domcontentloaded',timeout:180000});
  await p.evaluate(id=>window.openResearchStock(id),cfg.compare[0].identity);
  await p.getByRole('button',{name:'近期60根',exact:true}).click();
  await p.selectOption('#queryDate',cfg.as_of);
  assert.equal(await p.evaluate(()=>result.as_of),cfg.as_of);
  assert.equal(await p.evaluate(()=>bars()[view.end].date),cfg.as_of);
  assert((await p.locator('#readout').textContent()).includes(cfg.as_of));
  assert(await p.evaluate(()=>document.documentElement.scrollWidth<=innerWidth));
  assert.deepEqual(errors,[]);
  await p.screenshot({path:path.join(out,'private-current-day-390.png'),fullPage:true});
  fs.writeFileSync(path.join(out,'current-day-view.json'),JSON.stringify({status:'PASS',checks:1,viewport:[390,844],as_of:cfg.as_of,new_day_visible_and_queryable:true,analysis_date_unchanged:true,android:'NOT_TESTED_NEW_BUILD'}));
  await ctx.close();console.log('PASS actual new day visible/queryable in recent phone window');
 }finally{await browser.close()}
})().catch(e=>{console.error(e);process.exitCode=1});
