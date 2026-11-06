// One cold load per saved version; original HTML served locally, never repacked.
const fs=require('fs'),path=require('path');
const {chromium}=require(path.join(process.env.CODEX_PRIMARY_RUNTIME_NODE_MODULES,'playwright'));
(async()=>{const cfg=JSON.parse(fs.readFileSync(process.argv[2]));const rows=[];
for(const [version,url]of Object.entries(cfg.urls)){
 const browser=await chromium.launch({executablePath:'/usr/bin/chromium',headless:true,args:['--disk-cache-size=1048576','--media-cache-size=1048576']});
 const ctx=await browser.newContext({viewport:{width:390,height:844},isMobile:true,hasTouch:true,httpCredentials:cfg.auth});const page=await ctx.newPage();const cdp=await ctx.newCDPSession(page);await cdp.send('Performance.enable');const start=Date.now();let peak=0,bytes=0,errors=[];page.on('pageerror',e=>errors.push(e.message));cdp.on('Network.loadingFinished',e=>bytes+=e.encodedDataLength);await cdp.send('Network.enable');let busy=false;
 const poll=setInterval(async()=>{if(busy)return;busy=true;try{const m=await cdp.send('Runtime.getHeapUsage');peak=Math.max(peak,m.usedSize)}catch(e){}finally{busy=false}},250);
 try{await page.goto(url,{waitUntil:'networkidle',timeout:180000});await page.waitForSelector('#marketResults button',{timeout:30000});const m=await cdp.send('Runtime.getHeapUsage');peak=Math.max(peak,m.usedSize);rows.push({version,status:'LOADED',wait_ms:Date.now()-start,transfer_bytes:bytes,js_heap_used_bytes:m.usedSize,js_heap_sampled_peak_bytes:peak,navigation:await page.evaluate(()=>{const x=performance.getEntriesByType('navigation')[0];return {encoded:x.encodedBodySize,decoded:x.decodedBodySize,dom_content_loaded_ms:x.domContentLoadedEventEnd,load_ms:x.loadEventEnd}}),errors});}
 catch(e){rows.push({version,status:'NOT_LOADED',wait_ms:Date.now()-start,error:e.message,transfer_bytes:bytes,js_heap_sampled_peak_bytes:peak,errors})}finally{clearInterval(poll);await browser.close()}
 fs.writeFileSync(process.argv[3],JSON.stringify({schema:'lite-first-load-benchmark/0.1',method:'single cold Chromium context per version, same 390x844 viewport; no throttling; JS heap sampled 250ms, not process RSS',rows},null,2));}
 console.log(JSON.stringify(rows));})().catch(e=>{console.error(e);process.exitCode=1});
