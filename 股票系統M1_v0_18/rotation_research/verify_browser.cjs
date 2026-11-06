/* Actual Chromium HTTP checks. No external site or real Android implied. */
const fs=require('fs'),path=require('path'),http=require('http'),assert=require('assert'),crypto=require('crypto');
const {chromium}=require(process.env.CODEX_PRIMARY_RUNTIME_NODE_MODULES+'/playwright');
const out=path.join(__dirname,'generated'),expected=JSON.parse(fs.readFileSync(path.join(out,'report-data.json'),'utf8'));
const html=fs.readFileSync(path.join(out,'report.html'));const screenshots=path.join(out,'screenshots');fs.mkdirSync(screenshots,{recursive:true});
const checks=[];const check=(name,ok)=>{assert(ok,name);checks.push(name)};
const server=http.createServer((req,res)=>{if(req.url==='/report.html'){res.writeHead(200,{'Content-Type':'text/html; charset=utf-8'});res.end(html)}else{res.writeHead(404);res.end()}});
(async()=>{await new Promise(r=>server.listen(0,'127.0.0.1',r));server.unref();let browser;
try{
 browser=await chromium.launch({executablePath:process.env.ROTATION_BROWSER,headless:true,args:['--no-sandbox']});
 const page=await browser.newPage({viewport:{width:390,height:844},deviceScaleFactor:1,isMobile:true,hasTouch:true});
 const errors=[],requests=[];page.on('pageerror',e=>errors.push(String(e)));page.on('request',r=>requests.push(r.url()));
 await page.goto(`http://127.0.0.1:${server.address().port}/report.html`);await page.waitForFunction(()=>document.querySelector('#prices').complete&&document.querySelector('#prices').naturalWidth>0);
 check('exact embedded numeric report',JSON.stringify(await page.evaluate(()=>REPORT))===JSON.stringify(expected));
 for(const date of ['2026-01-02','2026-08-03'])for(const pair of ['1101','2884']){
  await page.selectOption('#date',date);await page.selectOption('#pair',pair);const c=expected.cases[date+'-'+pair];
  check('table rows '+date+pair,await page.locator('#metrics tr').count()===6);
  check('sensitivity rows '+date+pair,await page.locator('#sensitivity tr').count()===9);
  const cells=await page.locator('#metrics tr').allTextContents();
  check('formatted return matches source '+date+pair,c.results.every((r,i)=>cells[i].includes((Number(r.metrics.net_price_return)*100).toFixed(2)+'%')));
  check('cutoff no future '+date+pair,await page.locator('#prices').getAttribute('data-last-date')===date);
  await page.click('#after');check('after cutoff explicit '+date+pair,await page.locator('#prices').getAttribute('data-last-date')===c.end);
  await page.click('#before');check('return to cutoff '+date+pair,await page.locator('#prices').getAttribute('data-last-date')===date);
  check('390 no horizontal body overflow '+date+pair,await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth));
 }
 await page.selectOption('#date','2026-08-03');await page.selectOption('#pair','1101');await page.click('#after');
 await page.locator('#zoom').fill('200');await page.locator('#zoom').dispatchEvent('input');
 check('plot zoom local scroll',await page.locator('.plot-scroll').evaluate(x=>x.scrollWidth>x.clientWidth));
 check('zoom no horizontal body overflow',await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth));
 await page.locator('#zoom').fill('100');await page.locator('#zoom').dispatchEvent('input');
 await page.locator('#prices').screenshot({path:path.join(screenshots,'mobile-k-volume.png')});
 await page.locator('#metrics').screenshot({path:path.join(screenshots,'mobile-metrics.png')});
 await page.evaluate(()=>scrollTo(0,0));await page.screenshot({path:path.join(screenshots,'mobile-top.png')});
 let promise=page.waitForEvent('download');await page.click('#downloadJSON');let download=await promise;
 let downloaded=fs.readFileSync(await download.path(),'utf8');check('real JSON download exact',JSON.stringify(JSON.parse(downloaded))===JSON.stringify(expected));
 promise=page.waitForEvent('download');await page.click('#downloadPrice');download=await promise;
 const svg=fs.readFileSync(await download.path());check('real SVG download exact',svg.equals(fs.readFileSync(path.join(out,'plots','prices-2026-08-03-after.svg'))));
 await page.setViewportSize({width:1400,height:1000});await page.screenshot({path:path.join(screenshots,'desktop.png'),fullPage:true});
 check('1400 no body overflow',await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth));
 check('zero JS errors',errors.length===0);check('zero external requests',requests.every(r=>r.startsWith('http://127.0.0.1:')||r.startsWith('data:')));
 const result={status:'PASS',browser:browser.version(),checks:checks.length,details:checks,errors,physical_android:'NOT_TESTED_NEW_BUILD'};
 fs.writeFileSync(path.join(out,'browser-verification.json'),JSON.stringify(result,null,2)+'\n');console.log(JSON.stringify(result));
}finally{if(browser)await browser.close();server.close()}
})().catch(e=>{console.error(e);process.exitCode=1;server.close()});
