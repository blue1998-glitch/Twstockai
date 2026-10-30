/* New display evidence panels only; never recreate historical images. */
const fs=require('node:fs'),path=require('node:path'),http=require('node:http'),crypto=require('node:crypto');
const {chromium}=require(path.join(process.env.CODEX_PRIMARY_RUNTIME_NODE_MODULES,'playwright'));
const input=process.env.P03_READABLE_DIR,output=process.env.P03_READABLE_EVIDENCE;
if(!input||!output)throw Error('Explicit new artifact and evidence directories required');
fs.mkdirSync(output,{recursive:true});
const html=fs.readFileSync(path.join(input,'M1_P03_structure_state_readable_v02.html'));
(async()=>{
 const server=http.createServer((q,r)=>{r.setHeader('Content-Type','text/html; charset=utf-8');r.end(html);});
 await new Promise(r=>server.listen(0,'127.0.0.1',r));
 const browser=await chromium.launch({executablePath:process.env.CODEX_BROWSER_EXECUTABLE_PATH||'/usr/bin/chromium',headless:true,args:['--no-sandbox']});
 const files=[];
 try{for(const width of [1280,390]){
  const page=await browser.newPage({viewport:{width,height:1000}});await page.goto(`http://127.0.0.1:${server.address().port}/`);await page.waitForFunction(()=>!!window.P03Readability);await page.click('#p03OpenCase');
  for(const [id,prefix]of [['#p03Events','events'],['#p03Provenance','source-dates']]){
   if(id==='#p03Provenance')await page.locator(id).evaluate(e=>e.open=true);
   const filename=prefix+'-'+width+'.png',target=path.join(output,filename);await page.locator(id).screenshot({path:target});
   files.push({file:filename,bytes:fs.statSync(target).size,sha256:crypto.createHash('sha256').update(fs.readFileSync(target)).digest('hex'),scope:'NEW_BUILD_PANEL_CAPTURE_NOT_PRODUCT_TEST_OR_ANDROID'});
  }
  await page.close();
 }
 fs.writeFileSync(path.join(output,'panel-captures.json'),JSON.stringify({browser:await browser.version(),files,old_images_recreated:false,android:'NOT_TESTED_NEW_BUILD'},null,2)+'\n');console.log(JSON.stringify({captured:files.length}));
 }finally{await browser.close();await new Promise(r=>server.close(r));}
})().catch(e=>{console.error(e);process.exitCode=1;});
