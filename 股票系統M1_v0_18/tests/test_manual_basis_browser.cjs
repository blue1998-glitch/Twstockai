/* Exact saved-series and no-fallback checks through a local HTTP chart. */
const assert = require('node:assert/strict');
const fs = require('node:fs');
const http = require('node:http');
const path = require('node:path');
const os = require('node:os');
const {execFileSync} = require('node:child_process');
const {chromium} = require(path.join(process.env.CODEX_PRIMARY_RUNTIME_NODE_MODULES, 'playwright'));
const root = path.join(__dirname, '..');
const delivery = path.join(root, '../deliveries/m1-v019-manual-basis-20261022/M1_v019_manual_basis_v01.zip');
const member = name => execFileSync('unzip', ['-p',delivery,name], {maxBuffer:50*1024*1024});
const html = member('M1_v019_manual_basis_v01.html');
const oracles = JSON.parse(member('selection-oracle.json'));
const output = process.env.MANUAL_BASIS_SCREENSHOT_DIR || fs.mkdtempSync(path.join(os.tmpdir(),'manual-basis-browser-'));
fs.mkdirSync(output,{recursive:true});
const browserPath = process.env.CHROME_HEADLESS_SHELL;
if (!browserPath) throw Error('Set CHROME_HEADLESS_SHELL to the installed browser');

async function run() {
  const server = http.createServer((req, res) => {
    res.setHeader('Content-Type', 'text/html; charset=utf-8');
    res.end(html);
  });
  server.listen(0, '127.0.0.1');
  await new Promise(resolve => server.once('listening', resolve));
  const browser = await chromium.launch({executablePath:browserPath, headless:true, args:['--no-sandbox']});
  const errors = [];
  const reports = [];
  try {
    const context = await browser.newContext({viewport:{width:1280,height:900}});
    const page = await context.newPage();
    page.on('pageerror', e => errors.push(e.message));
    const url = `http://127.0.0.1:${server.address().port}/chart.html`;
    await page.goto(url);
    await page.waitForFunction(() => !!window.manualBasisInspect, {timeout:30000});
    let state = await page.evaluate(() => manualBasisInspect());
    assert.equal(state.status,'REQUIRES_MODE');
    assert.equal(await page.locator('#chart').isVisible(), false);
    await page.selectOption('#analysisMode', 'RAW_CANDIDATE');
    state = await page.evaluate(() => manualBasisInspect());
    assert.equal(state.status,'READY_SAVED_RESEARCH');

    const rawOracle = oracles.find(x => x.request.code==='1101');
    await page.waitForFunction(() => manualBasisInspect().ready);
    state = await page.evaluate(() => manualBasisInspect());
    assert.equal(state.binding.frame_id,rawOracle.resolution.binding.frame_id);
    assert.equal(await page.locator('#chart').isVisible(),true);
    let exp = await page.evaluate(() => manualBasisExport());
    assert.deepEqual(exp.saved_selection,rawOracle.saved_selection);
    assert.equal(exp.historical_signal_eligible,false);
    assert.equal(exp.request.price_mode,'RAW_CANDIDATE');
    await page.screenshot({path:path.join(output,'desktop-raw.png'),fullPage:true});
    reports.push('1101_RAW_exact_saved_selection');

    await page.fill('#manualDate','2026-09-30');
    await page.dispatchEvent('#manualDate','change');
    state = await page.evaluate(() => manualBasisInspect());
    assert.equal(state.status,'REQUIRES_SOURCE');
    assert.equal(await page.locator('#chart').isVisible(),false);
    await page.selectOption('#mode', rawOracle.request.series_key);
    assert.equal((await page.evaluate(() => manualBasisInspect())).status,'READY_SAVED_RESEARCH');
    await page.click('#manualLastDate');

    await page.selectOption('#stock','8069');
    state = await page.evaluate(() => manualBasisInspect());
    assert.equal(state.request.price_mode,'RAW_CANDIDATE');
    assert.equal(state.status,'READY_SAVED_RESEARCH');
    await page.selectOption('#analysisMode','ADJUSTED_CANDIDATE');
    state = await page.evaluate(() => manualBasisInspect());
    assert.equal(state.status,'UNAVAILABLE');
    assert.equal(state.request.as_of,'2026-10-16');
    assert.equal(await page.locator('#chart').isVisible(),false);
    assert.equal((await page.evaluate(() => manualBasisExport())).saved_selection,null);
    await page.reload();
    await page.waitForFunction(() => !!window.manualBasisInspect, {timeout:30000});
    state = await page.evaluate(() => manualBasisInspect());
    assert.equal(state.status,'UNAVAILABLE');
    assert.equal(state.request.price_mode,'ADJUSTED_CANDIDATE');
    assert.equal(state.request.as_of,'2026-10-16');
    reports.push('missing_adjusted_kept_after_reload');

    await page.click('#manualLastDate');
    state = await page.evaluate(() => manualBasisInspect());
    assert.equal(state.request.as_of,'2026-09-30');
    assert.equal(state.status,'READY_SAVED_RESEARCH');
    const adjOracle = oracles.find(x => x.request.code==='8069');
    exp = await page.evaluate(() => manualBasisExport());
    assert.deepEqual(exp.saved_selection,adjOracle.saved_selection);
    assert.equal(exp.resolution_binding.frame_id,adjOracle.resolution.binding.frame_id);
    assert.match(await page.locator('#manualModeStatus').innerText(),/研究候選/);
    await page.screenshot({path:path.join(output,'desktop-adjusted.png'),fullPage:true});
    reports.push('8069_ADJUSTED_exact_saved_selection');

    await page.selectOption('#stock','6488');
    state = await page.evaluate(() => manualBasisInspect());
    assert.equal(state.request.price_mode,'ADJUSTED_CANDIDATE');
    assert.equal(state.status,'READY_SAVED_RESEARCH');
    await page.selectOption('#stock','2884');
    state = await page.evaluate(() => manualBasisInspect());
    assert.equal(state.request.price_mode,'ADJUSTED_CANDIDATE');
    assert.equal(state.status,'UNAVAILABLE');
    assert.equal((await page.evaluate(() => manualBasisExport())).saved_selection,null);
    assert.equal(await page.locator('#chart').isVisible(),false);
    reports.push('stock_switch_preserves_mode_and_blocks_missing');

    await page.selectOption('#stock','8069');
    await page.waitForFunction(() => manualBasisInspect().ready);
    const mobile = await browser.newContext({viewport:{width:390,height:844},isMobile:true,deviceScaleFactor:1});
    const mp = await mobile.newPage();
    mp.on('pageerror',e=>errors.push(e.message));
    await mp.goto(url);
    await mp.waitForFunction(() => !!window.manualBasisInspect,{timeout:30000});
    await mp.selectOption('#stock','8069');
    await mp.selectOption('#analysisMode','ADJUSTED_CANDIDATE');
    await mp.click('#manualLastDate');
    assert.equal((await mp.evaluate(() => manualBasisInspect())).status,'READY_SAVED_RESEARCH');
    await mp.screenshot({path:path.join(output,'mobile-adjusted.png'),fullPage:true});
    const mobileWidth = await mp.evaluate(() => ({scroll:document.documentElement.scrollWidth,viewport:innerWidth}));
    reports.push('mobile_390x844_'+JSON.stringify(mobileWidth));
    await mobile.close();

    const blocked = await browser.newContext();
    await blocked.addInitScript(() => {
      Storage.prototype.setItem = function() {throw Error('storage unavailable');};
    });
    const bp = await blocked.newPage();
    bp.on('pageerror',e=>errors.push(e.message));
    await bp.goto(url);
    await bp.waitForFunction(() => !!window.manualBasisInspect,{timeout:30000});
    await bp.selectOption('#analysisMode','RAW_CANDIDATE');
    assert.match(await bp.locator('#manualStorageStatus').innerText(),/保存未完成/);
    assert.equal((await bp.evaluate(() => manualBasisExport())).request.price_mode,'RAW_CANDIDATE');
    reports.push('storage_failure_visible_and_exportable');
    await blocked.close();
    await context.close();
    assert.deepEqual(errors,[]);
    console.log(JSON.stringify({status:'PASS',checks:reports,errors},null,2));
  } finally {await browser.close();server.close();}
}
run().catch(error => {console.error(error);process.exitCode=1;});
