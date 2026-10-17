// Real Chromium loopback HTTP, synthetic data; never physical Android evidence.
'use strict';
const fs = require('fs'), path = require('path'), http = require('http');
const assert = require('assert/strict'), crypto = require('crypto');
const directory = path.resolve(process.env.M1_ATTEMPT_DIR);
const output = path.resolve(process.env.M1_ATTEMPT_BROWSER_OUTPUT_DIR);
fs.mkdirSync(output, {recursive: true});
const html = fs.readFileSync(path.join(directory, 'M1_v0_19_attempt_candidate.html'));
const bundle = JSON.parse(fs.readFileSync(path.join(directory, 'attempt-candidate.json'), 'utf8'));
const oracle = JSON.parse(fs.readFileSync(path.join(directory, 'attempt-selection-oracle.json'), 'utf8'));
const sha = buffer => crypto.createHash('sha256').update(buffer).digest('hex');
const checks = [], started = new Date().toISOString();
let browser, server, downloads = 0, lastDownloadAt = 0;
const record = (name, data = {}) => checks.push({name, status: 'PASS', elapsed_ms:Date.now()-Date.parse(started), ...data});
(async () => {
  try {
    const playwright = require(process.env.CODEX_PRIMARY_RUNTIME_NODE_MODULES ?
      path.join(process.env.CODEX_PRIMARY_RUNTIME_NODE_MODULES, 'playwright') : 'playwright');
    browser = await playwright.chromium.launch({headless: true,
      executablePath: process.env.CODEX_BROWSER_EXECUTABLE_PATH || '/usr/bin/chromium'});
    server = http.createServer((request, response) => {
      if (request.url !== '/attempt.html') { response.writeHead(404); response.end(); return; }
      response.writeHead(200, {'Content-Type': 'text/html; charset=utf-8'}); response.end(html);
    });
    await new Promise((resolve, reject) => { server.once('error', reject); server.listen(0, '127.0.0.1', resolve); });
    const url = 'http://127.0.0.1:' + server.address().port + '/attempt.html';
    for (const viewport of [{width:1280, height:900}, {width:390, height:844}]) {
      const mobile = viewport.width === 390;
      const context = await browser.newContext({viewport, isMobile: mobile, hasTouch: mobile,
        deviceScaleFactor: mobile ? 2 : 1, acceptDownloads: true});
      const page = await context.newPage(), errors = [], external = [];
      page.on('pageerror', error => errors.push(error.message));
      page.on('request', r => { if (/^https?:/.test(r.url()) && new URL(r.url()).origin !== new URL(url).origin) external.push(r.url()); });
      const click = async selector => mobile ? page.locator(selector).tap() : page.locator(selector).click();
      const choose = async (caseId, index) => {
        if (await page.locator('#sourceCase').inputValue() !== caseId) await page.selectOption('#sourceCase', caseId);
        await page.selectOption('#observation', String(index)); await click('#loadAttempt');
      };
      const tick = Date.now(); await page.goto(url);
      assert(await page.locator('#result').isHidden()); assert(await page.locator('#sourceCase').isDisabled());
      assert(await page.locator('#observation').isDisabled()); assert(await page.locator('#loadAttempt').isDisabled());
      record('disabled by default with no automatic source or latest time', {viewport, load_ms:Date.now()-tick});
      await click('#enableAttempt'); assert.equal(await page.locator('#sourceCase').inputValue(), '');
      assert(await page.locator('#result').isHidden()); assert(await page.locator('#loadAttempt').isDisabled());
      record('explicit opt-in still requires source and observation', {viewport});
      for (const source of oracle.cases) {
        await page.selectOption('#sourceCase', source.case_id);
        assert.equal(await page.locator('#observation').inputValue(), '');
        assert(await page.locator('#result').isHidden()); assert(await page.locator('#loadAttempt').isDisabled());
        assert((await page.locator('#referenceStatus').textContent()).includes('來源檔'));
        for (const row of source.views) {
          await page.selectOption('#observation', String(row.index));
          assert(await page.locator('#result').isHidden()); await click('#loadAttempt');
          assert.equal(await page.evaluate(() => current.frame.frame_id), row.frame_id);
          assert((await page.locator('#phase').textContent()).includes(row.observed_at));
          assert((await page.locator('#scope').textContent()).includes('假想'));
          assert((await page.locator('#qualification').textContent()).includes('NOT_EVALUATED'));
          const painted = await page.locator('canvas').evaluateAll(nodes => nodes.map(c => ({
            width:c.width, expected:Math.round(c.getBoundingClientRect().width * devicePixelRatio),
            painted:c.getContext('2d').getImageData(0,0,c.width,c.height).data.some((v,i) => i%4===3 && v>0)
          })));
          for (const c of painted) { assert.equal(c.width,c.expected); assert(c.painted); }
          assert(await page.evaluate(() => geometry.daily.x(windowState.cursor) === geometry.volume.x(windowState.cursor)));
          // Chromium denies a burst above roughly 10 downloads/second in this
          // runtime. Pace real clicks; retain every download/hash assertion.
          const remaining = 150 - (Date.now() - lastDownloadAt);
          if (remaining > 0) await page.waitForTimeout(remaining);
          const event = page.waitForEvent('download'); await click('#download'); lastDownloadAt=Date.now();
          const downloaded = await event; assert.equal(await downloaded.failure(), null);
          const bytes = fs.readFileSync(await downloaded.path()); assert.equal(sha(bytes), row.selection_sha256);
          // Raw-byte hashes retain Python's arbitrary-size integer source values.
          const value = JSON.parse(bytes.toString('utf8'));
          assert.equal(value.input.observations.length, row.index+1); assert.equal(value.result.frames.length,row.index+1);
          assert(value.result.events.every(e => e.observation_index <= row.index));
          assert(value.chart.daily.every(r => r.date <= value.result.frames.at(-1).bar_date));
          assert(value.chart.intraday.points.every(p => Date.parse(p.observed_at) <= Date.parse(row.observed_at)));
          assert.equal(value.result.frames.at(-1).probability_estimate,null);
          assert.equal(value.result.frames.at(-1).trend_strength,'NOT_CLASSIFIED');
          assert(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth));
          downloads++;
          record('exact core-prefix replay and raw-byte JSON download', {viewport, case_id:source.case_id,index:row.index,frame_id:row.frame_id});
        }
      }
      await choose('explicit_101_106',0);
      assert.deepEqual(await page.evaluate(() => current.frame.attempt_levels.map(r => r.price_attempt_condition)),['MET','NOT_MET']);
      assert.equal(await page.evaluate(() => current.chart.daily.at(-1).high),'101.5');
      assert.equal(await page.locator('[data-kind="VOLUME_LEAD_OBSERVED"]').count(),0);
      assert.equal(await page.evaluate(() => current.chart.intraday.points.length),1);
      record('101 price attempt is visible before volume support or 106', {viewport});
      await choose('explicit_101_106',1);
      assert((await page.locator('#volumeText').textContent()).includes('量先超過'));
      assert.equal(await page.evaluate(() => current.frame.attempt_levels[1].price_attempt_condition),'NOT_MET');
      await page.evaluate(() => scrollTo(0,0));
      await page.screenshot({path:path.join(output,viewport.width+'-volume-lead-page.png'),fullPage:true});
      await page.locator('#charts').screenshot({path:path.join(output,viewport.width+'-volume-lead-charts.png')});
      record('volume support without falsely claiming price success', {viewport});
      await choose('explicit_101_106',3);
      assert.equal(await page.evaluate(() => current.frame.is_close),false);
      assert.equal(await page.evaluate(() => current.frame.attempt_levels[1].latest_completed_close_relation),'BELOW');
      assert((await page.locator('#phase').textContent()).includes('收盤未知'));
      await choose('explicit_101_106',4);
      assert.equal(await page.evaluate(() => current.frame.attempt_levels[1].latest_completed_close_relation),'ABOVE');
      record('intraday crossing remains separate from later completed close', {viewport});
      await choose('explicit_101_106',5);
      assert.deepEqual(await page.evaluate(() => current.frame.attempt_levels.map(r => r.relation)),['ABOVE','BELOW']);
      const events = await page.evaluate(() => current.events.map(e => [e.reference_id,e.kind]));
      assert(events.some(e => e[0]==='LEFT_ZONE_UPPER' && e[1]==='CLOSE_CROSSED_ABOVE'));
      assert(events.some(e => e[0]==='LEFT_ZONE_UPPER' && e[1]==='CLOSE_RETURNED_BELOW'));
      assert(!events.some(e => e[0]==='NEAR_HIGH' && e[1]==='CLOSE_RETURNED_BELOW'));
      await page.evaluate(() => scrollTo(0,0));
      await page.screenshot({path:path.join(output,viewport.width+'-return-below-page.png'),fullPage:true});
      record('return below 106 retains 101 and prior crossing evidence', {viewport});
      await choose('daily_order',0);
      assert((await page.locator('#volumeText').textContent()).includes('先後未知'));
      assert((await page.locator('#intradayStatus').textContent()).includes('資料缺少'));
      assert.equal(await page.evaluate(() => current.chart.intraday.points.length),0);
      record('completed OHLC does not fabricate intraday path or volume-price order', {viewport});
      await choose('missing_volume',0);
      assert((await page.locator('#volumeNumbers').textContent()).includes('未知'));
      assert.equal(await page.evaluate(() => current.frame.attempt_levels[0].price_attempt_condition),'MET');
      record('missing benchmark stays unknown while price fact is retained', {viewport});
      await choose('price_precision',0);
      assert((await page.locator('[data-reference="NEAR_HIGH"]').textContent()).includes('101.00'));
      assert((await page.locator('[data-reference="NEAR_HIGH"]').textContent()).includes('價格子條件成立'));
      assert((await page.locator('#exactSource').textContent()).includes('101.0000000000000001'));
      await choose('integer_precision',0);
      assert((await page.locator('#volumeNumbers').textContent()).includes('9,007,199,254,740,993'));
      assert((await page.locator('#exactSource').textContent()).includes('"volume_shares": 9007199254740993'));
      record('subcent conditions and arbitrary-size integer shares keep original precision', {viewport});
      await choose('explicit_101_106',1);
      const before = await page.evaluate(() => ({frame:current.frame.frame_id,sha:current.selection_sha256,count:windowState.end-windowState.start+1}));
      await click('#zoomIn'); assert(await page.evaluate(() => windowState.end-windowState.start+1)<before.count);
      const start = await page.evaluate(() => windowState.start); await click('#left');
      assert(await page.evaluate(() => windowState.start)<start); await click('#right'); await click('#zoomOut'); await click('#reset');
      assert.deepEqual(await page.evaluate(() => ({frame:current.frame.frame_id,sha:current.selection_sha256})),{frame:before.frame,sha:before.sha});
      await page.locator('#daily').scrollIntoViewIfNeeded();
      const box = await page.locator('#daily').boundingBox();
      if(mobile) await page.touchscreen.tap(box.x+box.width*.5,box.y+100);
      else await page.mouse.click(box.x+box.width*.5,box.y+100);
      assert(await page.evaluate(() => geometry.daily.x(windowState.cursor)===geometry.volume.x(windowState.cursor)));
      record('time window and shared cursor are presentation-only', {viewport});
      await page.locator('#intraday').scrollIntoViewIfNeeded();
      const intradayBox = await page.locator('#intraday').boundingBox();
      const x = await page.evaluate(() => geometry.intraday.px(0));
      if(mobile) await page.touchscreen.tap(intradayBox.x+x,intradayBox.y+100);
      else await page.mouse.click(intradayBox.x+x,intradayBox.y+100);
      assert((await page.locator('#intradayCursor').textContent()).includes('09:10'));
      assert.equal(await page.evaluate(() => current.frame.frame_id),before.frame);
      record('actual supplied intraday-point cursor preserves selected frame', {viewport});
      if(mobile){
        await page.locator('#daily').scrollIntoViewIfNeeded(); const r=await page.locator('#daily').boundingBox();
        const old=await page.evaluate(() => scrollY),cdp=await context.newCDPSession(page);
        await cdp.send('Input.dispatchTouchEvent',{type:'touchStart',touchPoints:[{id:0,x:r.x+120,y:r.y+180}]});
        for(let dy=20;dy<=100;dy+=20)await cdp.send('Input.dispatchTouchEvent',{type:'touchMove',touchPoints:[{id:0,x:r.x+120,y:r.y+180-dy}]});
        await cdp.send('Input.dispatchTouchEvent',{type:'touchEnd',touchPoints:[]});
        await page.waitForFunction(old => scrollY!==old,old,{timeout:4000});
        record('native one-finger page scrolling on chart', {viewport});
      }
      await click('#full');
      assert(await page.evaluate(() => !!document.fullscreenElement||document.body.classList.contains('focus')));
      record('actual fullscreen attempt with truthful status', {viewport,native:await page.evaluate(() => !!document.fullscreenElement)});
      await click('#exitFocus');
      await page.evaluate(() => { el('charts').requestFullscreen=() => Promise.reject(new Error('injected browser refusal')); });
      await click('#full'); assert(await page.evaluate(() => document.body.classList.contains('focus')));
      assert((await page.locator('#fullscreenStatus').textContent()).includes('未進入瀏覽器原生'));
      await click('#exitFocus'); assert(!(await page.evaluate(() => document.body.classList.contains('focus'))));
      record('injected native refusal uses explicit focus fallback', {viewport});
      await page.setViewportSize({width:mobile?844:1000,height:mobile?390:900});
      await page.waitForFunction(() => el('daily').width===Math.round(el('daily').getBoundingClientRect().width*devicePixelRatio));
      assert.equal(await page.evaluate(() => current.frame.frame_id),before.frame);
      assert(await page.evaluate(() => document.documentElement.scrollWidth<=innerWidth));
      await page.locator('#charts').screenshot({path:path.join(output,mobile?'844-landscape.png':'1000-resize.png')});
      record('orientation and resize preserve analysis and avoid overflow', {viewport});
      await click('#enableAttempt'); assert(await page.locator('#result').isHidden()); assert(await page.locator('#sourceCase').isDisabled());
      await click('#enableAttempt'); assert.equal(await page.locator('#sourceCase').inputValue(),'');
      assert(await page.locator('#loadAttempt').isDisabled());
      assert.deepEqual(errors,[]); assert.deepEqual(external,[]);
      record('disable clears stale selection; no JS errors or external requests', {viewport});
      await context.close();
    }
    fs.writeFileSync(path.join(output,'browser-report.json'),JSON.stringify({status:'PASS',started_at_utc:started,
      ended_at_utc:new Date().toISOString(),browser:browser.version(),html_sha256:sha(html),bundle_id:bundle.bundle_id,
      checks,exact_downloads:downloads,physical_android:'NOT_TESTED',transport:'LOOPBACK_HTTP',
      source_kind:'SYNTHETIC_ENGINEERING_FIXTURE',download_min_interval_ms:150,core_product_acceptance:'NOT_ESTABLISHED'},null,2));
  } catch(error) {
    fs.writeFileSync(path.join(output,'browser-report.json'),JSON.stringify({status:'FAIL',error:error.stack,checks,
      exact_downloads:downloads,physical_android:'NOT_TESTED'},null,2)); process.exitCode=1;
  } finally {
    if(browser)await browser.close(); if(server)await new Promise(resolve => server.close(resolve));
  }
})();
