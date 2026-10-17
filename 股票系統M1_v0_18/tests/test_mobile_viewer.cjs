// Tests the real mobile inline JS and saved results. No browser/layout claim.
process.env.M1_CROSS_VIEW_HTML='日週月研究對照_手機版_v0_18.html';
const fs=require('fs'),path=require('path'),assert=require('assert/strict');
const {setup,choose,canonical,hash,expected,html}=require('./test_cross_view.cjs');
const root=path.resolve(__dirname,'..'),output=path.join(root,'mobile_viewer/output');
const oracle=JSON.parse(fs.readFileSync(path.join(output,'顯示值獨立參照.json'),'utf8'));
const results=[];
function check(name,work){work();results.push({test:name,status:'PASS'})}
check('decimal halves, negative zero, carries and large values match independent Python Decimal',()=>{
 const ui=setup();
 for(const sample of oracle.examples)assert.equal(ui.run('displayPrice('+JSON.stringify(sample.raw)+')'),sample.display,sample.raw);
 assert.equal(ui.run('displayPrice(null)'),'—');assert.equal(ui.run('displayPrice(undefined)'),'—');assert.equal(ui.run('displayPrice("NOT_AVAILABLE")'),'NOT_AVAILABLE');
});
check('all 18 daily views and both period bases show two decimals without rounding nulls to zero',()=>{
 const ui=setup();
 for(const item of oracle.cases){
  const c=expected.cases.find(row=>row.case===item.case);choose(c,ui);
  for(const [index,wanted] of item.daily.entries()){
   const text=ui.el.dailyValues.children[index].children[1].children[0].textContent;
   if(wanted===null)assert.match(text,/^— 資料不足/);else assert.equal(text,wanted);
  }
  for(const basis of ['candidate','elapsed']){
   ui.change('basis',basis);
   for(const tf of ['weekly','monthly'])for(const [index,wanted] of item[basis][tf].entries()){
    const cell=ui.el[tf+'Values'].children[index].children[1],text=cell.children[0].textContent;
    if(wanted===null)assert.match(text,/^— /);else assert.equal(text,wanted);
    assert.match(cell.children[1].textContent,/期間 .* · 最後價格日 /);
   }
  }
 }
});
check('display and basis changes preserve exact records, snapshots and every JSON download',()=>{
 const ui=setup();
 for(const c of expected.cases){
  choose(c,ui);const before=hash(ui.run('current'));
  for(const basis of ['candidate','elapsed']){
   ui.change('basis',basis);assert.equal(hash(ui.run('current')),before);ui.el.download.fire('click');
   const downloaded=JSON.parse(ui.downloads.at(-1));
   const original=JSON.parse(fs.readFileSync(path.join(root,'cross_view/output',c.case+'_VIEW.json'),'utf8'));
   assert.equal(canonical(downloaded),canonical(original));
  }
 }
});
check('canvas backing uses real width and pixel ratio while price/data ranges remain original',()=>{
 const ui=setup(),c=expected.cases.find(row=>row.price_mode==='RAW_CANDIDATE');
 for(const tf of ['daily','weekly','monthly'])ui.el[tf+'Chart'].getBoundingClientRect=()=>({width:342,height:280});
 ui.run('globalThis.window={devicePixelRatio:3}');choose(c,ui);
 for(const tf of ['daily','weekly','monthly']){
  const canvas=ui.el[tf+'Chart'];assert.equal(canvas.width,1026);assert.equal(canvas.height,840);
  assert(ui.calls[tf].some(call=>call[0]==='setTransform'&&call[1]===3&&call[4]===3));
  assert(ui.calls[tf].some(call=>call[0]==='set'&&call[1]==='font'&&call[2]==='13px system-ui, sans-serif'));
  const labels=ui.calls[tf].filter(call=>call[0]==='fillText');assert(labels.length>=7);
  for(const [,text,x,y] of labels){assert(x>=0&&x<=342);assert(y>=0&&y<=280);assert.equal(typeof text,'string')}
 }
 const original=JSON.parse(fs.readFileSync(path.join(root,'cross_view/output',c.case+'_VIEW.json'),'utf8'));
 assert.equal(hash(ui.run('current.daily.snapshot')),hash(original.daily.snapshot));
});
check('resize redraws on current saved values and resets backing-pixel clears on selection changes',()=>{
 const ui=setup(),c=expected.cases.find(row=>row.price_mode==='ADJUSTED_CANDIDATE');choose(c,ui);const before=hash(ui.run('current'));
 for(const tf of ['daily','weekly','monthly'])ui.el[tf+'Chart'].getBoundingClientRect=()=>({width:700,height:280});
 ui.run('globalThis.window={devicePixelRatio:2};draw()');assert.equal(hash(ui.run('current')),before);
 for(const tf of ['daily','weekly','monthly'])assert.equal(ui.el[tf+'Chart'].width,1400);
 ui.change('date','2026-09-29');assert.equal(ui.run('current'),null);assert(ui.el.result.hidden);
 assert(ui.calls.daily.some(call=>call[0]==='clearRect'&&call[3]===1400&&call[4]===560));
});
check('mobile price tables have wrapping values, preserved context and no technical reason-code requirement',()=>{
 assert.equal((html.match(/class="value-table"/g)||[]).length,3);
 assert.match(html,/table-layout:fixed;white-space:normal/);assert.match(html,/overflow-wrap:anywhere/);
 const ui=setup();choose(expected.cases.find(c=>c.code==='2884'&&c.as_of==='2026-09-30'),ui);
 assert.match(ui.el.monthlyValues.children[3].children[1].textContent,/連續有效期間不足/);
 assert(!ui.el.monthlyValues.children[3].children[1].textContent.includes('INSUFFICIENT_CONTIGUOUS_PERIODS'));
 assert.match(html,/價格與均線顯示小數兩位/);
});
const report={status:'PASS',results,baseline_view_checks:16,comparison_cases:18,exact_download_comparisons:36,method:'Actual inline JS and saved data under Node VM; DOM/canvas doubles; Decimal oracle independent',browser_layout:'NOT_TESTED',physical_android_new_version:'NOT_TESTED'};
fs.writeFileSync(path.join(output,'手機頁面新增檢查.json'),JSON.stringify(report,null,2));console.log(JSON.stringify(report,null,2));
