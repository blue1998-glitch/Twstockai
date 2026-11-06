  // Real-source fixed cases; all original interaction/download checks ran above.
  const fixed=JSON.parse(fs.readFileSync(path.join(folder,'../../mg3_20261101/expected.json')));
  await page.selectOption('#stock','1101');await page.selectOption('#asOf','2025-05-14');
  assert.equal(await page.evaluate(()=>data.view_version),'graph-recognition-view/0.2');
  assert.equal(await page.evaluate(()=>result.schema_version),'graph-recognition-research/0.2');
  assert(await page.evaluate(id=>!result.boxes.some(b=>b.id===id),fixed.automatic_local.L6_id));
  await page.selectOption('#boxSelect',fixed.automatic_local.L3_id);await page.click('#evidenceButton');
  assert((await page.locator('[data-layer=observation] [data-relation=whole-range]').textContent()).includes('位於整個研究箱內'));
  assert((await page.locator('[data-layer=observation] [data-relation=pressure-band]').textContent()).includes('低於研究壓力帶'));
  assert.deepEqual(await page.locator('#evidenceBody section').evaluateAll(ns=>ns.map(n=>n.dataset.layer)),['formation','observation','history']);
  assert((await page.locator('[data-layer=formation]').textContent()).includes('25筆'));
  assert(!(await page.locator('#evidenceBody').textContent()).includes('39筆'));
  assert(await page.locator('#manualAudit').isHidden());
  await page.screenshot({path:path.join(out,'three-layers-'+size.width+'.png'),fullPage:true});
  assert(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth));
  await page.locator('#dismiss').click();
  await page.selectOption('#asOf','2025-05-27');assert(await page.evaluate(id=>result.boxes.some(b=>b.id===id),fixed.automatic_local.L6_id));
  await page.selectOption('#asOf','2025-06-03');await page.selectOption('#boxSelect',fixed.automatic_local.L6_id);await page.click('#evidenceButton');
  assert((await page.locator('[data-layer=observation]').textContent()).includes('2025-06-02'));
  const beforeEvent=await identity();await page.locator('[data-event-type=CLOSE_BELOW_RESEARCH_RANGE]').first().click();
  assert.equal(await page.locator('#queryDate').inputValue(),'2025-06-02');assert.deepEqual(await identity(),beforeEvent);
  await page.click('#evidenceButton');await page.locator('[data-action=focus-formation]').click();
  assert(await page.evaluate(id=>visible.has(id),fixed.automatic_local.L6_id));
  await page.click('#evidenceButton');await page.locator('[data-action=return-chart]').click();
  assert.deepEqual(await identity(),beforeEvent);pass('0.2 three layers; whole-range vs pressure band; L6 causality; retained6/2 failure/event-focus/return',size);
  await page.selectOption('#stock','2884');
  for(const dt of ['2026-07-21','2026-07-22']){
    await page.selectOption('#asOf',dt);const stopped=await page.evaluate(()=>result.boxes.find(b=>!b.usable_at_anchor));assert(stopped);
    assert.equal(stopped.pressure_distance_fraction,null);assert.equal(stopped.relative_width_to_anchor,null);
    assert(await page.evaluate(()=>current.input_bindings[result.as_of].basis_break_dates.includes('2026-07-01')));
    await page.selectOption('#boxSelect',stopped.id);await page.click('#evidenceButton');
    assert((await page.locator('[data-layer=observation]').textContent()).includes('不可比'));
    assert((await page.locator('[data-layer=observation]').textContent()).includes('未知／null（不補0）'));
    await page.locator('[data-action=focus-formation]').click();
    assert(await page.evaluate(id=>hits.some(h=>h.id===id),stopped.id));
    assert(await page.evaluate(()=>selected().source_input_binding.source_role==='RETAINED_OFFICIAL_PARENT_NOT_FINMIND'));
  }
  pass('2884 retained7/1 warning; F-01null; incomparable historical formation selectable/located without current ray',size);
  for(const code of ['6488','8069']){
    const sample=fixed.return_counterexamples[code];await page.selectOption('#stock',code);await page.selectOption('#asOf',sample.event.date);
    await page.selectOption('#boxSelect',sample.box_id);await page.click('#evidenceButton');
    const original=await page.evaluate(id=>box(id),sample.box_id);assert(original.path.first_breakdown_at<sample.event.date);
    assert(await page.locator('[data-event-type=RETURN_IN_RANGE_AFTER_BREAKDOWN]').count()>0);
    assert((await page.locator('[data-layer=observation]').textContent()).includes('不等正式恢復有效'));
    assert.equal(await page.evaluate(id=>evidenceFor(id).history.lifecycle,sample.box_id),'UNKNOWN_RETURN_IS_NOT_FORMAL_REACTIVATION');
    await page.locator('#dismiss').click();
  }
  pass('6488/8069 real breakdown-return examples retain earlier counterevidence and no formal revival',size);
