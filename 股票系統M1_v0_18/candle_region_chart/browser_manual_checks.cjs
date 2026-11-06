'use strict';
module.exports=async function({page,manualOracle,size,fresh,choose,pass,mobile,out,assert,fs,path}) {
  if(!await page.locator('#pointDetails').evaluate(n=>n.open))await page.locator('#pointDetails > summary').click();
  // Uses real shipped data and independent offline oracle; no DOM stubs.
  assert.deepEqual(await page.evaluate(()=>manual),manualOracle);
  assert.equal(await page.locator('#manualPanel').isVisible(),true);
  assert.equal(await page.locator('.hurdleCard').count(),3);
  assert((await page.locator('#manualPosition').textContent()).includes('① 26.10 收盤已過點價'));
  assert((await page.locator('#manualPosition').textContent()).includes('④ 26.85 收盤已過點價'));
  assert((await page.locator('#manualQualification').textContent()).includes('人工回溯'));
  assert.equal(await page.evaluate(()=>view.end-view.start+1),486);
  const exactIdentity=await page.evaluate(()=>[current.key,current.source.id,frame.frame_id,frame.as_of,frame.chart_base]);
  const expectedY=await page.evaluate(()=>{const rows=base().bars.slice(view.start,view.end+1);let hi=Math.max(...rows.map(r=>Number(r.high))),lo=Math.min(...rows.map(r=>Number(r.low)));const spread=Math.max(hi-lo,hi*.01,.01);return [lo-spread*.12,hi+spread*.12];});
  assert.deepEqual(await page.evaluate(()=>[geometry.priceLow,geometry.priceHigh]),expectedY);
  assert(expectedY[1]<50.2);
  assert((await page.locator('[data-hurdle="G3"]').textContent()).includes('高於目前價格軸'));
  assert((await page.locator('[data-hurdle="G3"]').textContent()).includes('5個同價來源'));
  assert.equal(await page.evaluate(()=>hits.filter(h=>h.id.startsWith('manual:')).length),0);
  for(const id of ['G1','G2','G3'])assert((await page.locator(`[data-hurdle="${id}"]`).textContent()).includes('來源全在畫外'));
  pass('manual3 retain 24-month offscreen hints and candle-only Y axis; original1/4 separate',{size,y:expectedY});
  await page.evaluate(()=>scrollTo(0,0));await page.screenshot({path:path.join(out,size.width+'-manual-24-month.png'),fullPage:true});
  for(const id of ['G1','G2','G3']){
    const ref=manualOracle.references.find(r=>r.reference.id===id).reference;
    await page.locator(`[data-hurdle="${id}"] .hurdleEvidence`).click();
    assert((await page.locator('#evidenceBody').textContent()).includes(ref.raw_high));
    assert((await page.locator('#evidenceBody').textContent()).includes('非當時自動訊號'));
    assert.equal(await page.locator('#evidenceBody details[open]').count(),0);
    assert.equal(await page.locator('#evidenceBody table tr').count(),ref.source_bars.length+1);
    for(const date of ref.matching_source_dates)assert((await page.locator('#evidenceBody table').textContent()).includes(date));
    if(id==='G3'){
      assert((await page.locator('#evidenceBody').textContent()).includes('未指定唯一日期'));
      await page.screenshot({path:path.join(out,size.width+'-G3-evidence.png'),fullPage:true});
    }
    await page.locator('#dismiss').click();
    const btn=page.locator(`[data-hurdle="${id}"] .hurdleLocate`);const box=await btn.boundingBox();assert(box.width>=44&&box.height>=44);
    if(mobile)await btn.tap();else await btn.click();
    assert.deepEqual(await page.evaluate(()=>[current.key,current.source.id,frame.frame_id,frame.as_of,frame.chart_base]),exactIdentity);
    assert.equal(await page.evaluate(()=>base().bars[view.cursor].date),ref.display_anchor_source_date);
    assert(await page.evaluate(id=>hits.some(h=>h.id.startsWith('manual:'+id+':')&&h.y>=geometry.price.top&&h.y<=geometry.price.bottom),id));
    assert(await page.evaluate(()=>geometry.price.x(view.cursor)===geometry.volume.x(view.cursor)&&geometry.volume.x(view.cursor)===geometry.macd.x(view.cursor)));
    assert((await page.locator('#cursorValues').textContent()).includes(ref.display_anchor_source_date));
    await page.locator('#chart').scrollIntoViewIfNeeded();
    let mark=await page.evaluate(id=>{const h=hits.find(h=>h.id.startsWith('manual:'+id+':'));return {x:h.x,y:h.y};},id),canvas=await page.locator('#chart').boundingBox();
    if(mobile)await page.touchscreen.tap(canvas.x+mark.x,canvas.y+mark.y);else await page.mouse.click(canvas.x+mark.x,canvas.y+mark.y);
    assert((await page.locator('#evidenceTitle').textContent()).includes(id));
    if(id==='G1')await page.screenshot({path:path.join(out,size.width+'-G1-located.png'),fullPage:true});
    await page.getByRole('button',{name:'返回近期24月（不改分析日）',exact:true}).click();
    assert.equal(await page.evaluate(()=>view.end-view.start+1),486);
    assert.deepEqual(await page.evaluate(()=>[current.key,current.source.id,frame.frame_id,frame.as_of,frame.chart_base]),exactIdentity);
    pass('manual '+id+' evidence,44px source location,chart point and return preserve analysis',{size});
  }
  // Every G3 date is independently locatable; none becomes a unique user choice.
  for(const date of manualOracle.references[2].reference.matching_source_dates){
    await page.locator('[data-hurdle="G3"] .hurdleEvidence').click();
    await page.getByRole('button',{name:'G3定位'+date,exact:true}).click();
    assert.equal(await page.evaluate(()=>base().bars[view.cursor].date),date);
    assert.deepEqual(await page.evaluate(()=>[current.key,current.source.id,frame.frame_id,frame.as_of,frame.chart_base]),exactIdentity);
  }
  await page.locator('#months24').click();
  const evt=page.waitForEvent('download');await page.locator('#download').click();const downloaded=await evt;
  const actual=JSON.parse(fs.readFileSync(await downloaded.path(),'utf8'));assert.deepEqual(actual.manual_hurdles,manualOracle);
  assert.equal(actual.schema_version,'manual-region-chart-selection/0.2');assert.equal(actual.manual_hurdles.review.references[2].source_date,null);
  pass('all five G3 source dates locatable; downloaded case and fingerprints exact',{size});
  await page.selectOption('#asOf','2026-10-15');
  assert.equal(await page.evaluate(()=>manual),null);assert(await page.locator('#manualPanel').isHidden());assert.equal(await page.evaluate(()=>selected().manual_hurdles),null);
  await page.locator('#play').click();await page.waitForFunction(()=>frame.as_of==='2026-10-16');await page.locator('#play').click();
  assert.deepEqual(await page.evaluate(()=>manual),manualOracle);
  await page.locator('#prev').click();assert.equal(await page.evaluate(()=>manual),null);
  await page.locator('#next').click();assert.deepEqual(await page.evaluate(()=>manual),manualOracle);
  pass('prior day/replay/next preserve exact case qualification; no historical backfill',{size});
  const other=await page.evaluate(()=>data.history_series.find(s=>s.code==='2884').key);await choose(other,'2026-10-16');
  assert.equal(await page.evaluate(()=>manual),null);assert(await page.locator('#manualPanel').isHidden());
  await page.locator('#reviewCase').click();assert.equal(await page.evaluate(()=>manual),null);assert(await page.evaluate(()=>!!review));
  pass('other stock and original saved Raw case never receive new manual3',{size});
  await choose(fresh,'2026-10-16');

};
