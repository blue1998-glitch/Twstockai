// Real browser QA when an executable exists. Missing browser = BLOCKED, never PASS.
const fs=require('fs'),path=require('path'),assert=require('assert/strict'),{pathToFileURL}=require('url');
const root=path.resolve(__dirname,'..'),output=path.join(root,'cross_view/output/日週月真實瀏覽器檢查.json');
(async()=>{let browser;const checks=[];try{
 const playwright=require(process.env.CODEX_PRIMARY_RUNTIME_NODE_MODULES?path.join(process.env.CODEX_PRIMARY_RUNTIME_NODE_MODULES,'playwright'):'playwright');
 browser=await playwright.chromium.launch({headless:true,...(process.env.CODEX_BROWSER_EXECUTABLE_PATH?{executablePath:process.env.CODEX_BROWSER_EXECUTABLE_PATH}:{})});
 const expected=JSON.parse(fs.readFileSync(path.join(root,'cross_view/output/日週月對照實算驗收.json'),'utf8'));
 for(const viewport of [{width:1280,height:900},{width:390,height:844}]){
  const context=await browser.newContext({viewport,isMobile:viewport.width===390,hasTouch:viewport.width===390,acceptDownloads:true});
  const page=await context.newPage(),errors=[];page.on('pageerror',e=>errors.push(e.message));await page.goto(pathToFileURL(path.join(root,'日週月研究對照.html')).href);
  assert(await page.locator('#result').isHidden());
  for(const c of expected.cases){
   await page.selectOption('#stock',c.exchange+' / '+c.code);await page.selectOption('#mode',c.price_mode);await page.selectOption('#date',c.as_of);
   await page.selectOption('#daily',c.daily_key);await page.selectOption('#period',c.period_key);await page.locator('#load').click();
   assert(await page.locator('#result').isVisible());assert((await page.locator('#badge').textContent()).includes('輸入對齊'));
   await page.selectOption('#basis','candidate');await page.selectOption('#basis','elapsed');
  }
  const event=page.waitForEvent('download');await page.locator('#download').click();const download=await event;const value=JSON.parse(fs.readFileSync(await download.path(),'utf8'));assert.equal(value.alignment.status,'ALIGNED_INPUTS');
  assert(await page.evaluate(()=>document.documentElement.scrollWidth<=window.innerWidth));assert.deepEqual(errors,[]);
  checks.push({viewport,status:'PASS',actual_comparisons:18,json_download:true,no_horizontal_overflow:true});await context.close();
 }
 fs.writeFileSync(output,JSON.stringify({status:'PASS',method:'Real Chromium/Playwright desktop and mobile emulation; not physical Android',checks},null,2));
}catch(e){const blocked=/Executable doesn't exist|Cannot find module/.test(e.message);fs.writeFileSync(output,JSON.stringify({status:blocked?'BLOCKED':'FAIL',reason:e.message,checks,browser_rendering:blocked?'NOT_TESTED':'ATTEMPTED',physical_android:'NOT_TESTED'},null,2));process.exitCode=blocked?2:1;}finally{if(browser)await browser.close()}})();
