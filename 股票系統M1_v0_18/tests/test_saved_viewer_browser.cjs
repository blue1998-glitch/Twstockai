// Real Playwright checks. Missing executable is BLOCKED, never PASS.
const fs=require('fs'),path=require('path'),assert=require('assert/strict');
const {pathToFileURL}=require('url');
const root=path.resolve(__dirname,'..'),report=path.join(root,'saved_viewer/output/真實瀏覽器檢查.json');
(async()=>{let browser;const checks=[];try{
 const playwright=require(process.env.CODEX_PRIMARY_RUNTIME_NODE_MODULES?path.join(process.env.CODEX_PRIMARY_RUNTIME_NODE_MODULES,'playwright'):'playwright');
 browser=await playwright.chromium.launch({headless:true});
 for(const viewport of [{width:1280,height:900},{width:390,height:844}]){
  const context=await browser.newContext({viewport,hasTouch:viewport.width===390,isMobile:viewport.width===390,acceptDownloads:true});
  const page=await context.newPage(),errors=[];page.on('pageerror',e=>errors.push(e.message));
  await page.goto(pathToFileURL(path.join(root,'已保存分析瀏覽.html')).href);
  await page.locator('#date-title').waitFor();assert.equal(await page.locator('#date-title').textContent(),'2026-09-30');
  assert.equal(await page.locator('#error').textContent(),'');
  assert(await page.locator('#quality').textContent().then(t=>t.includes('UNVERIFIED')));
  assert(await page.locator('#ma-values').textContent().then(t=>t.includes('需 260 筆；此日 179 筆')));
  await page.selectOption('#stock','8069');await page.selectOption('#mode','ADJUSTED_CANDIDATE');
  await page.selectOption('#date','2025-08-01');await page.selectOption('#stock','1101');
  assert(await page.locator('#download').isDisabled());assert.equal(await page.locator('#summary').textContent(),'');
  await page.locator('#last').click();assert.equal(await page.locator('#date-title').textContent(),'2026-09-30');
  const downloadEvent=page.waitForEvent('download');await page.locator('#download').click();const download=await downloadEvent;
  const selected=JSON.parse(fs.readFileSync(await download.path(),'utf8'));assert.equal(selected.snapshot.as_of,'2026-09-30');assert.equal(selected.snapshot.daily_ma.code,'1101');
  assert(await page.evaluate(()=>document.documentElement.scrollWidth<=window.innerWidth));assert.deepEqual(errors,[]);
  checks.push({viewport,status:'PASS',download_json:true,no_horizontal_page_overflow:true});await context.close();
 }
 fs.writeFileSync(report,JSON.stringify({status:'PASS',method:'Real Chromium through Playwright',checks},null,2));console.log('Real browser checks PASS');
}catch(e){const blocked=/Executable doesn't exist|Cannot find module.*playwright/.test(e.message);const out={status:blocked?'BLOCKED':'FAIL',reason:e.message,checks,browser_rendering:blocked?'NOT_TESTED':'ATTEMPTED'};fs.writeFileSync(report,JSON.stringify(out,null,2));console.log(JSON.stringify(out,null,2));process.exitCode=blocked?2:1;}finally{if(browser)await browser.close();}})();
