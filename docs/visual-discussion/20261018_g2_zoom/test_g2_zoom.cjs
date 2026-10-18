const fs=require('fs'),http=require('http'),crypto=require('crypto'),assert=require('assert');
const {chromium:pw}=require('playwright');
const chromium=require('./qa/node_modules/@sparticuz/chromium');
const path=require('path');
const report={checks:[],errors:[],browser:null,physical_android:'NOT_TESTED',transport:'LOOPBACK_HTTP_ONLY',d3_transport:'REAL_PINNED_D3_BYTES_FULFILLED_AT_APPROVED_CDN_URL'};
const check=(name,condition,details={})=>{report.checks.push({name,pass:!!condition,...details});assert(condition,name);};
const hash=s=>crypto.createHash('sha256').update(s).digest('hex');
const source=JSON.parse(fs.readFileSync('review/g2_source.json','utf8'));
const original=JSON.parse(fs.readFileSync('review/source_original.json','utf8'));
const expected=original.new_history_analysis.bars.filter(b=>b.date>='2022-01-01'&&b.date<='2024-01-31');
check('507 bars exactly equal retained original source',JSON.stringify(source.bars)===JSON.stringify(expected));
check('original export hash',hash(fs.readFileSync('review/source_original.json'))==='369947bad71ab3fdff894c21511ebf242e1ddb12b59822d02ed93f0580bd2796');
check('G2 exact source high and date',source.G2.date==='2023-05-02'&&source.G2.high==='40.25');
const d3=fs.readFileSync('review/d3-7.9.0.min.js');report.d3_sha256=hash(d3);
const fragment=fs.readFileSync('/workspace/g2-region-zoom.html','utf8');report.fragment_sha256=hash(fragment);
const server=http.createServer((req,res)=>{if(req.url==='/qa-font.otf'){res.setHeader('Content-Type','font/otf');res.end(fs.readFileSync('review/qa-font.otf'));return;}res.setHeader('Content-Type','text/html; charset=utf-8');res.end(fs.readFileSync('review/g2-qa.html'));});
(async()=>{
  let browser;
  try{
    await new Promise(resolve=>server.listen(0,'127.0.0.1',resolve));
    browser=await pw.launch({executablePath:path.resolve('review/browser-tmp/chromium'),args:['--no-sandbox','--disable-dev-shm-usage','--disable-gpu','--disable-software-rasterizer'],headless:true});
    report.browser=await browser.version();
    for(const [width,height,touch] of [[320,740,true],[390,844,true],[844,390,true],[1280,900,false]]){
      const ctx=await browser.newContext({viewport:{width,height},hasTouch:touch,isMobile:touch});
      const page=await ctx.newPage();
      const errors=[];page.on('pageerror',e=>errors.push(e.message));
      await page.route('https://cdn.jsdelivr.net/npm/d3@7.9.0/dist/d3.min.js',route=>route.fulfill({contentType:'text/javascript',body:d3}));
      await page.goto(`http://127.0.0.1:${server.address().port}/`);
      const root=page.locator('#g2-region-zoom');await page.waitForFunction(()=>document.querySelector('#g2-region-zoom').dataset.render);await page.evaluate(()=>document.fonts.ready);
      const state=()=>root.evaluate(el=>({first:+el.dataset.first,count:+el.dataset.count,asof:el.dataset.analysisAsOf,range:el.querySelector('.range').textContent,candles:el.querySelectorAll('.candle').length,volumes:el.querySelectorAll('.vol').length,source:el.querySelector('.source').textContent}));
      const before=await state();check(`${width} initial actual SVG counts`,before.count===before.candles&&before.count===before.volumes);
      check(`${width} exact embedded source`,JSON.stringify(JSON.parse(before.source))===JSON.stringify(source));
      await page.locator('[data-action=in]').click();let now=await state();check(`${width} zoom in reduces window`,now.count<before.count);
      await page.locator('[data-action=out]').click();let wider=await state();check(`${width} zoom out expands window`,wider.count>now.count);
      await page.locator('[data-action=left]').click();let earlier=await state();check(`${width} left pans earlier`,earlier.first<wider.first);
      await page.locator('[data-action=right]').click();check(`${width} right pans later`,(await state()).first>earlier.first);
      await page.locator('[data-action=g2]').click();now=await state();check(`${width} G2 nearby is 96 real bars`,now.count===96&&await page.locator('.g2-source').count()===1);
      const hit=page.locator('.price rect.hit'),box=await hit.boundingBox();
      if(touch)await page.touchscreen.tap(box.x+box.width*.4,box.y+box.height*.7);
      else await page.mouse.click(box.x+box.width*.4,box.y+box.height*.7);
      check(`${width} tap selects dated exact readout`,/20\d\d-\d\d-\d\d/.test(await page.locator('.readout').textContent()));
      const preDrag=await state();
      await page.mouse.move(box.x+box.width*.6,box.y+box.height*.6);await page.mouse.down();
      await page.mouse.move(box.x+box.width*.35,box.y+box.height*.6,{steps:5});await page.mouse.up();
      check(`${width} drag pans window`,(await state()).first!==preDrag.first);
      if(touch){
        const cdp=await ctx.newCDPSession(page);await page.locator('[data-action=g2]').click();
        const b=await hit.boundingBox(),cx=b.x+b.width*.5,cy=b.y+b.height*.5;
        const old=(await state()).count;
        await cdp.send('Input.dispatchTouchEvent',{type:'touchStart',touchPoints:[{x:cx-20,y:cy,id:1},{x:cx+20,y:cy,id:2}]});
        await cdp.send('Input.dispatchTouchEvent',{type:'touchMove',touchPoints:[{x:cx-55,y:cy,id:1},{x:cx+55,y:cy,id:2}]});
        await cdp.send('Input.dispatchTouchEvent',{type:'touchEnd',touchPoints:[]});
        check(`${width} real touch pinch zoom`,(await state()).count<old);await cdp.detach();
      }
      await page.locator('[data-action=g2]').click();
      await page.locator('[data-action=left]').click();await page.locator('[data-action=left]').click();
      check(`${width} no fake source circle when offscreen`,await page.locator('.g2-source').count()===0);
      await page.locator('[data-action=g2]').click();await page.waitForTimeout(160);
      const after=await state();check(`${width} source and analysis unchanged`,after.source===before.source&&after.asof==='2026-10-16');
      check(`${width} price and volume stay aligned`,after.count===after.candles&&after.count===after.volumes);
      const overflow=await page.evaluate(()=>document.documentElement.scrollWidth>innerWidth+1);
      check(`${width} no horizontal page overflow`,!overflow);
      const bounds=await page.locator('.price').evaluate(svg=>({viewBox:svg.viewBox.baseVal.width,actual:svg.getBoundingClientRect().width}));
      check(`${width} SVG uses actual width`,Math.abs(bounds.viewBox-bounds.actual)<1);
      const labels=await page.locator('svg.chart text').evaluateAll(ns=>ns.filter(n=>n.getAttribute('visibility')!=='hidden').map(n=>({size:parseFloat(getComputedStyle(n).fontSize),text:n.textContent})));
      check(`${width} labels remain at least 12px`,labels.every(n=>n.size>=12));
      check(`${width} no JS page errors`,errors.length===0,{errors});
      await page.screenshot({path:`review/g2-qa-${width}.png`,fullPage:true});
      if(width===1280)await root.screenshot({path:'review/g2_original_size.png'});
      await ctx.close();
    }
    report.status='PASS_REAL_CHROMIUM_HTTP';
  }catch(e){report.status='FAIL';report.errors.push(e.stack);process.exitCode=1;}
  finally{if(browser)await browser.close();server.close();fs.writeFileSync('review/g2-browser-report.json',JSON.stringify(report,null,2)+'\n');console.log(JSON.stringify({status:report.status,checks:report.checks.length,browser:report.browser,errors:report.errors}));}
})();
