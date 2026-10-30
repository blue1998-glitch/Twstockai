// Real saved catalog + inline JS under DOM/canvas doubles; not browser QA.
const fs=require('fs'),path=require('path'),assert=require('assert/strict');
const {setup,choose,expected,canonical,hash}=require('./test_cross_view.cjs');
const root=path.resolve(__dirname,'..'),html=fs.readFileSync(path.join(root,'日週月研究對照_結構標記_v0_18.html'),'utf8');
const data=html.match(/<script id="cross-data" type="application\/json">([\s\S]*?)<\/script>/)[1];
const ui=()=>setup(data,html),checks=[];
function check(name,work){work();checks.push({name,status:'PASS'})}
check('all 18 selections use only exact saved pivot and zone objects, without mutation or reanalysis',()=>{
 const q=ui();for(const c of expected.cases){choose(c,q);const before=hash(q.run('current'));
  for(const level of ['major','minor','both','off']){q.change('annotationLevel',level);
   const items=q.run('annotationState.items'),s=q.run('current.daily.snapshot.structure');
   for(const item of items){const collection=item.type==='pivot'?s.pivots:s.zones;
    assert(collection.some(record=>canonical(record)===canonical(item.saved)));
    if(level!=='both')assert.equal(item.saved.profile,level);
   }
   if(level==='off')assert.equal(items.length,0);
   assert.equal(hash(q.run('current')),before);
  }
 }
});
check('markers are date-exact; zones begin at creation and stop at invalidation, with no nearest-date substitution',()=>{
 const q=ui();for(const c of expected.cases){choose(c,q);q.change('annotationWindow','all');q.change('annotationLevel','both');q.change('annotationHistory','all');
  const dates=q.run('current.daily.source_candles.map(c=>c.date)');
  for(const item of q.run('annotationState.items')){
   if(item.type==='pivot'){assert(dates.includes(item.date));assert.equal(item.date,item.saved.occurred_at);assert(item.saved.confirmed_at<=c.as_of)}
   else{assert(item.start>=item.saved.created_at);assert(item.end<=c.as_of);if(item.saved.invalidated_at)assert(item.end<=item.saved.invalidated_at)}
  }
 }
});
check('active-only and historical filters preserve saved statuses and never turn stopped zones into live support',()=>{
 const q=ui();const c=expected.cases.find(c=>c.code==='8069'&&c.price_mode==='RAW_CANDIDATE'&&c.as_of==='2026-09-30');choose(c,q);
 q.change('annotationWindow','all');q.change('annotationLevel','both');q.change('annotationHistory','all');
 const historical=q.run("annotationState.items.filter(i=>i.type==='zone'&&i.saved.state!=='ACTIVE_CANDIDATE')");assert(historical.length>0);
 q.change('annotationHistory','active');assert(q.run("annotationState.items.filter(i=>i.type==='zone').every(i=>i.saved.state==='ACTIVE_CANDIDATE'&&!i.saved.invalidated_at)"));
});
check('missing, future, null-price, unknown-status and mismatched-anchor evidence fails closed',()=>{
 const q=ui();choose(expected.cases[0],q);q.change('annotationWindow','all');
 q.run("current.daily.snapshot.structure.pivots.forEach(p=>{p.confirmed_at='2099-01-01'});draw()");assert.equal(q.run('annotationState.items.length'),0);
 choose(expected.cases[1],q);q.run("current.daily.snapshot.structure.adjustment_anchor='1900-01-01';draw()");assert.equal(q.run('annotationState.items.length'),0);assert.match(q.el.annotationSummary.textContent,/錨定不符/);
 const r=ui();choose(expected.cases[0],r);r.run("current.daily.snapshot.structure.pivots.forEach(p=>p.price=null);current.daily.snapshot.structure.zones.forEach(z=>z.state='UNKNOWN_STATE');draw()");assert.equal(r.run('annotationState.items.length'),0);
});
check('Adjusted markers use the selected saved anchor; charts still have no fabricated adjusted daily candles',()=>{
 const q=ui(),c=expected.cases.find(c=>c.price_mode==='ADJUSTED_CANDIDATE');choose(c,q);q.change('annotationWindow','all');q.change('annotationLevel','both');
 assert(q.run('annotationState.items.length')>0);assert.match(q.el.dailyFacts.textContent,/還原日 K 沒有存入/);
 q.change('annotationLevel','off');q.calls.daily.length=0;q.run('draw()');assert(!q.calls.daily.some(call=>call[0]==='fillRect'));
});
check('pointer selection and exact dropdown selection expose original times, status and IDs; switching clears stale evidence',()=>{
 const q=ui();choose(expected.cases.find(c=>c.code==='8069'&&c.as_of==='2026-09-30'),q);q.change('annotationWindow','all');
 const item=q.run("annotationState.items.find(i=>i.type==='pivot')");assert(item);q.change('annotationSelect',item.key);
 for(const field of ['occurred_at','first_observed_at','confirmed_at','id','status'])assert(q.el.annotationDetail.textContent.includes(item.saved[field]));
 const hit=q.run("annotationState.hits.find(i=>i.type==='pivot')");q.el.dailyChart.getBoundingClientRect=()=>({left:0,top:0,width:900,height:300});
 q.el.dailyChart.listeners.pointerup({clientX:hit.x,clientY:hit.y});assert(q.run('annotationState.selected'));
 q.change('stock','TWSE / 2884');assert.equal(q.run('annotationState.items.length'),0);assert.equal(q.run('annotationState.hits.length'),0);assert(q.el.annotationSelect.disabled);
});
check('visual windows and all annotation controls preserve 72 exact full-precision downloads',()=>{
 const q=ui();let downloads=0;
 for(const c of expected.cases){choose(c,q);const original=JSON.parse(fs.readFileSync(path.join(root,'cross_view/output',c.case+'_VIEW.json'),'utf8'));
  for(const window of ['60','130','all']){q.change('annotationWindow',window);const source=q.run('current.daily.source_candles');
   const dates=source.slice(window==='all'?0:-Number(window)).map(c=>c.date);
   assert(q.run("annotationState.items.filter(i=>i.type==='pivot')").every(i=>dates.includes(i.date)));
  }
  for(const level of ['major','minor','both','off']){q.change('annotationLevel',level);q.el.download.fire('click');downloads++;
   assert.equal(canonical(JSON.parse(q.downloads.at(-1))),canonical(original));
  }
 }assert.equal(downloads,72);
});
check('conflict hides and clears all graph evidence without enabling calculations or external assets',()=>{
 const payload=JSON.parse(data),c=expected.cases[0];const view=payload.views.find(v=>v.view_id===c.view_id);view.status='CONFLICT';view.allow_comparison=false;
 const q=setup(JSON.stringify(payload),html);choose(c,q);assert(q.el.boards.hidden);assert.equal(q.run('annotationState.items.length'),0);
 assert.match(html,/connect-src 'none'/);assert(!/<script[^>]+src=/.test(html));
 assert(!/function\s+(analyze|project_prices|run_analysis_job)/.test(html));
});
const out=path.join(root,'annotations/output');fs.mkdirSync(out,{recursive:true});
fs.writeFileSync(path.join(out,'標記邏輯驗收.json'),JSON.stringify({status:'PASS',checks,comparison_cases:18,exact_downloads:72,browser_rendering:'NOT_TESTED',physical_android:'NOT_TESTED'},null,2));
console.log(JSON.stringify({status:'PASS',checks},null,2));
