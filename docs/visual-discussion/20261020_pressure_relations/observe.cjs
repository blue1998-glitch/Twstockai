const {chromium}=require('/opt/codex/runtimes/codex-primary-runtime/dependencies/node/node_modules/playwright');
const fs=require('fs'),http=require('http'),path=require('path'),assert=require('assert/strict'),crypto=require('crypto');
const root=__dirname, source=path.join(root,'../real-review/input/M1_v019_cross_scale_real_v01.html');
const bytes=fs.readFileSync(source), sha=b=>crypto.createHash('sha256').update(b).digest('hex');
assert.equal(sha(bytes),'f5b3b4e5e03da1c8291ff5854e0a6dfbb974286fe5cfbcb9a466ec6e138203ee');
const font='/workspace/scratch/ca1bc9758970/core-next/qa-font.otf';
const server=http.createServer((req,res)=>{res.setHeader('Content-Type',req.url==='/font.otf'?'font/otf':'text/html;charset=utf-8');res.end(req.url==='/font.otf'?fs.readFileSync(font):bytes);});
(async()=>{await new Promise(r=>server.listen(0,'127.0.0.1',r));let browser;
try{browser=await chromium.launch({executablePath:'/workspace/scratch/ca1bc9758970/core-next/browser/runtime/chromium',headless:true,args:['--no-sandbox']});
const page=await browser.newPage({viewport:{width:1400,height:1050}}),errors=[],observations=[];page.on('pageerror',e=>errors.push(e.message));
await page.goto('http://127.0.0.1:'+server.address().port);
await page.addStyleTag({content:'@font-face{font-family:ReviewCJK;src:url(/font.otf)}body,button,select{font-family:ReviewCJK,system-ui!important}'});
await page.evaluate(()=>document.fonts.ready);
await page.evaluate(()=>{const d=Object.getOwnPropertyDescriptor(CanvasRenderingContext2D.prototype,'font');Object.defineProperty(CanvasRenderingContext2D.prototype,'font',{get:d.get,set(v){d.set.call(this,v.replace(/system-ui/g,'ReviewCJK'));}});draw();});
const before=await page.evaluate(()=>JSON.stringify(data));
for(const spec of [
{name:'whole-context',start:'2023-06-01',end:'2026-10-16',layers:['major','b77','manual39','recent'],select:'b77'},
{name:'overlap-context',start:'2025-01-02',end:'2025-06-26',layers:['b77','manual39','same'],select:'manual39'},
{name:'earlier-descent',start:'2023-05-02',end:'2024-01-19',layers:['major','b77'],select:'b77'}]){
await page.evaluate(s=>{visible.clear();s.layers.forEach(x=>visible.add(x));selectedLayer=s.select;view.start=rows.findIndex(r=>r.date>=s.start);view.end=rows.findLastIndex(r=>r.date<=s.end);view.cursor=view.end;buildLayers();evidence();draw();},spec);
await page.locator('#chartWrap').screenshot({path:path.join(root,spec.name+'.png')});
observations.push(await page.evaluate(s=>({spec:s,state:window.M1_CROSS_SCALE.state(),window:document.querySelector('#window').textContent,readout:document.querySelector('#readout').textContent}),spec));
}
assert.equal(await page.evaluate(()=>JSON.stringify(data)),before);assert.deepEqual(errors,[]);assert.equal(sha(fs.readFileSync(source)),sha(bytes));
fs.writeFileSync(path.join(root,'browser-observation.json'),JSON.stringify({scope:'LIMITED_READ_ONLY_THREE_VIEW_CAPTURE_NOT_INTERACTION_REGRESSION',browser:await browser.version(),html_sha256:sha(bytes),font:'Observation-only DOM/Canvas ReviewCJK substitution; original artifact unchanged; original font screenshot retained in prior review',data_core_analysis_unchanged:true,errors,observations,physical_android:'NOT_TESTED_NEW_BUILD',file_protocol_used:false,core_executed:false,bootstrap_executed:false},null,2)+'\n');
console.log(JSON.stringify({screenshots:3,errors,data_core_analysis_unchanged:true}));
}finally{if(browser)await browser.close();server.close();}})().catch(e=>{console.error(e);server.close();process.exitCode=1;});
