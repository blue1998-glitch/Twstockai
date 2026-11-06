const {chromium}=require('/opt/codex/runtimes/codex-primary-runtime/dependencies/node/node_modules/playwright');
const fs=require('fs'),http=require('http'),path=require('path'),assert=require('assert/strict'),crypto=require('crypto');
const dir=__dirname,source=path.join(dir,'../real-review/input/M1_v019_cross_scale_real_v01.html');
const html=fs.readFileSync(source),sha=b=>crypto.createHash('sha256').update(b).digest('hex');
assert.equal(sha(html),'f5b3b4e5e03da1c8291ff5854e0a6dfbb974286fe5cfbcb9a466ec6e138203ee');
const font='/workspace/scratch/ca1bc9758970/core-next/qa-font.otf';
const server=http.createServer((req,res)=>{res.setHeader('Content-Type',req.url==='/font.otf'?'font/otf':'text/html;charset=utf-8');res.end(req.url==='/font.otf'?fs.readFileSync(font):html);});
(async()=>{await new Promise(r=>server.listen(0,'127.0.0.1',r));let browser;
try{browser=await chromium.launch({executablePath:'/workspace/scratch/ca1bc9758970/core-next/browser/runtime/chromium',headless:true,args:['--no-sandbox']});
const page=await browser.newPage({viewport:{width:1200,height:1000}}),errors=[],observations=[];page.on('pageerror',e=>errors.push(e.message));
await page.goto('http://127.0.0.1:'+server.address().port);
await page.addStyleTag({content:'@font-face{font-family:ReviewCJK;src:url(/font.otf)}body,button,select{font-family:ReviewCJK,system-ui!important}'});await page.evaluate(()=>document.fonts.ready);
await page.evaluate(()=>{const d=Object.getOwnPropertyDescriptor(CanvasRenderingContext2D.prototype,'font');Object.defineProperty(CanvasRenderingContext2D.prototype,'font',{get:d.get,set(v){d.set.call(this,v.replace(/system-ui/g,'ReviewCJK'));}});draw();});
const before=await page.evaluate(()=>JSON.stringify(data));
for(const spec of [
{name:'may-reclaim-lower-high',start:'2025-05-09',end:'2025-05-23',cursor:'2025-05-21',refLayer:'b77',refField:'low',title:'站回較低參照，仍未收復上方反彈高點',subtitle:'①5/14原高30.50　②5/20、21站回30.05　③5/22又收回下方；僅觀察參照',extraRefs:[{date:'2025-05-14',field:'high',label:'5/14 原高點'}],points:[{date:'2025-05-14',field:'high',label:'①'},{date:'2025-05-20',field:'close',label:'②'},{date:'2025-05-21',field:'high',label:'②'},{date:'2025-05-22',field:'close',label:'③'}]},
{name:'oct-intraday-vs-close',start:'2026-10-06',end:'2026-10-16',cursor:'2026-10-16',refLayer:'recent',refField:'high',title:'高低點上移，收盤仍未越過另一個參照',subtitle:'①10/14高27.40　②10/16高27.70／收27.30／低26.95；不推日內回測順序',extraRefs:[{date:'2026-10-14',field:'high',label:'10/14 原高點'}],points:[{date:'2026-10-14',field:'high',label:'①'},{date:'2026-10-16',field:'high',label:'②'},{date:'2026-10-16',field:'close',label:'收'},{date:'2026-10-16',field:'low',label:'低'}]}
]){
const details=await page.evaluate(s=>{visible.clear();selectedLayer=s.refLayer;view.start=rows.findIndex(r=>r.date>=s.start);view.end=rows.findLastIndex(r=>r.date<=s.end);view.cursor=rows.findIndex(r=>r.date===s.cursor);buildLayers();evidence();draw();
const refLayer=data.layers.find(l=>l.id===s.refLayer),value=refLayer.display_extent[s.refField],g=geometry,ctx=document.querySelector('#chart').getContext('2d');
const y=v=>g.price.bottom-(Number(v)-g.priceLow)/(g.priceHigh-g.priceLow)*(g.price.bottom-g.price.top);
ctx.save();ctx.strokeStyle='#ffe17a';ctx.lineWidth=1.5;ctx.setLineDash([6,5]);ctx.beginPath();ctx.moveTo(g.left,y(value));ctx.lineTo(g.right,y(value));ctx.stroke();ctx.setLineDash([]);ctx.font='14px ReviewCJK';ctx.fillStyle='#ffe17a';ctx.fillText('觀察參照 '+Number(value).toFixed(2)+'（非正式區界）',g.left+6,y(value)-12);
const extraReferences=[];for(const ref of s.extraRefs){const row=rows.find(r=>r.date===ref.date),v=row[ref.field];ctx.save();ctx.strokeStyle='#a4caff';ctx.setLineDash([3,5]);ctx.beginPath();ctx.moveTo(g.left,y(v));ctx.lineTo(g.right,y(v));ctx.stroke();ctx.setLineDash([]);ctx.fillStyle='#a4caff';ctx.font='14px ReviewCJK';ctx.fillText(ref.label+' '+Number(v).toFixed(2)+'（非正式壓力界）',g.left+6,y(v)-13);ctx.restore();extraReferences.push({source_date:row.date,field:ref.field,value:v,qualification:'EXPLICIT_RESEARCH_QUERY_REFERENCE_NOT_AUTO_SELECTED_PRESSURE'});}
const points=[];for(const p of s.points){const i=rows.findIndex(r=>r.date===p.date),r=rows[i],px=g.x(i),py=y(r[p.field]);ctx.strokeStyle='#fff';ctx.lineWidth=2;ctx.beginPath();ctx.arc(px,py,5,0,Math.PI*2);ctx.stroke();ctx.fillStyle='#fff';ctx.font='17px ReviewCJK';ctx.fillText(p.label,px-8,py-15);points.push({date:r.date,index:i,price:r[p.field],label:p.label,canvas_x:px,canvas_y:py,bar:r,macd:data.macd[i]});}ctx.restore();
let h=document.querySelector('#researchHeading');if(!h){h=document.createElement('div');h.id='researchHeading';document.querySelector('#chartWrap').prepend(h);}h.style.cssText='background:#1a293b;padding:10px;font-size:15px;line-height:1.8';h.textContent=s.title+'｜'+s.subtitle;
return {name:s.name,reference:{source_layer:s.refLayer,source_field:'display_extent.'+s.refField,value,qualification:'OBSERVATION_ONLY_EXISTING_RESEARCH_REFERENCE_NOT_NEW_FORMAL_BOUND'},window:document.querySelector('#window').textContent,readout:document.querySelector('#readout').textContent,points,extraReferences};},spec);
await page.locator('#chartWrap').screenshot({path:path.join(dir,spec.name+'.png')});observations.push(details);
}
assert.equal(await page.evaluate(()=>JSON.stringify(data)),before);assert.deepEqual(errors,[]);assert.equal(sha(fs.readFileSync(source)),sha(html));
fs.writeFileSync(path.join(dir,'browser-observation.json'),JSON.stringify({scope:'TWO_READ_ONLY_VIEW_CAPTURES_WITH_EXPLICIT_OBSERVATION_ONLY_REFERENCE_LINES_AND_POINT_LABELS',html_sha256:sha(html),browser:await browser.version(),viewport:{width:1200,height:1000},font:'Observation-only ReviewCJK substitution; original first-font image retained in prior real-review',original_data_core_analysis_unchanged:true,errors,observations,core_executed:false,bootstrap_executed:false,physical_android:'NOT_TESTED_NEW_BUILD',file_protocol_used:false},null,2)+'\n');console.log(JSON.stringify({screenshots:2,errors,original_data_core_analysis_unchanged:true}));
}finally{if(browser)await browser.close();server.close();}})().catch(e=>{console.error(e);server.close();process.exitCode=1;});
