const {chromium}=require(process.env.M1_REVIEW_PLAYWRIGHT||'/opt/codex/runtimes/codex-primary-runtime/dependencies/node/node_modules/playwright');
const fs=require('fs'),http=require('http'),path=require('path');
const dir=__dirname, font=process.env.M1_REVIEW_FONT||path.resolve(dir,'../core-next/qa-font.otf');
const server=http.createServer((req,res)=>{const file=req.url==='/font.otf'?font:path.join(dir,'M1_v019_graph_recognition_v01.html');res.setHeader('Content-Type',req.url==='/font.otf'?'font/otf':'text/html; charset=utf-8');res.end(fs.readFileSync(file));});
(async()=>{await new Promise(r=>server.listen(0,'127.0.0.1',r));const browser=await chromium.launch({executablePath:process.env.M1_REVIEW_CHROMIUM||path.resolve(dir,'../core-next/browser/runtime/chromium'),headless:true,args:['--no-sandbox']});
const page=await browser.newPage({viewport:{width:1400,height:1050},deviceScaleFactor:1});const errors=[];page.on('pageerror',e=>errors.push(e.message));await page.goto('http://127.0.0.1:'+server.address().port);await page.addStyleTag({content:'@font-face{font-family:ReviewCJK;src:url(/font.otf)}body,button,select{font-family:ReviewCJK,system-ui!important}'});await page.evaluate(()=>document.fonts.ready);await page.evaluate(()=>{const d=Object.getOwnPropertyDescriptor(CanvasRenderingContext2D.prototype,'font');Object.defineProperty(CanvasRenderingContext2D.prototype,'font',{get:d.get,set(v){d.set.call(this,v.replace(/system-ui/g,'ReviewCJK'));}});draw();});
const report={scope:'READ_ONLY_SHIPPED_ARTIFACT_OBSERVATION_NOT_CORE_RERUN_OR_ANDROID',observations:[],errors};
report.observations.push(await page.evaluate(()=>({header:document.querySelector('header').innerText,window:document.getElementById('window').innerText,as_of:result.as_of,source_id:result.context.source_id,frame_id:current.numeric_frame_ids[result.as_of],result_id:result.result_id,boxes:result.boxes.length,visible:[...visible].map(boxLabel)})));
await page.screenshot({path:path.join(dir,'default-1400.png')});
for(const spec of [{name:'major-B77',n:77,start:'2023-05-01',end:'2025-06-05'},{name:'previous-B44-B80',n:44,extra:80,start:'2025-03-25',end:'2025-06-12'},{name:'recent-B88',n:88,start:'2025-05-26',end:'2026-10-16'}]){
 const id=await page.evaluate(n=>boxes()[n-1].id,spec.n);await page.selectOption('#boxSelect',id);await page.click('#locate');
 await page.evaluate(s=>{visible=new Set([boxes()[s.n-1].id,...(s.extra?[boxes()[s.extra-1].id]:[])]);view.start=bars().findIndex(r=>r.date>=s.start);view.end=bars().findLastIndex(r=>r.date<=s.end);view.cursor=view.end;draw();},spec);
 report.observations.push(await page.evaluate(()=>({box:document.getElementById('boxSelect').selectedOptions[0].textContent,window:document.getElementById('window').innerText,as_of:result.as_of,result_id:result.result_id,visible:[...visible].map(boxLabel)})));
 await page.screenshot({path:path.join(dir,spec.name+'-1400.png')});
 await page.click('#evidenceButton');report.observations.push({name:spec.name,evidence:await page.locator('#evidence').innerText()});await page.click('#dismiss');
}
await page.setViewportSize({width:390,height:1000});await page.click('#months24');await page.evaluate(()=>draw());await page.screenshot({path:path.join(dir,'recent-B88-390.png')});
report.observations.push(await page.evaluate(()=>({portrait_window:document.getElementById('window').innerText,as_of:result.as_of,result_id:result.result_id})));
fs.writeFileSync(path.join(dir,'browser-observation.json'),JSON.stringify(report,null,2));await browser.close();server.close();console.log(JSON.stringify({status:'OBSERVED',screenshots:5,page_errors:errors,observations:report.observations.length}));})().catch(e=>{console.error(e);server.close();process.exit(1)});
