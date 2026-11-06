// Actual inline script + minimal DOM/canvas doubles. No rendering/touch claim.
const fs=require('fs'),path=require('path'),vm=require('vm'),assert=require('assert/strict'),crypto=require('crypto');
const root=path.resolve(__dirname,'..');
const html=fs.readFileSync(path.join(root,'已保存分析瀏覽.html'),'utf8');
const payload=html.match(/<script id="saved-data" type="application\/json">([\s\S]*?)<\/script>/)[1];
const script=html.match(/<script>\n([\s\S]*?)<\/script>/)[1];new vm.Script(script);
const expectations=JSON.parse(fs.readFileSync(path.join(root,'saved_viewer/output/保存結果瀏覽驗收.json'),'utf8')).snapshot_expectations;
const results=[];
class Element{
 constructor(tag='div'){this.tag=tag;this.children=[];this.listeners={};this.style={};this._text='';this._value='';this.disabled=false;}
 get value(){return this._value;}set value(v){this._value=String(v);}
 set textContent(v){this._text=String(v);this.children=[];}get textContent(){return this._text+this.children.map(n=>n.textContent).join('');}
 replaceChildren(...nodes){this._text='';this.children=nodes;}append(...nodes){this.children.push(...nodes);}
 addEventListener(type,fn){this.listeners[type]=fn;}fire(type,event={}){assert.equal(typeof this.listeners[type],'function',type);this.listeners[type](event);}
 click(){this.clicked=true;}remove(){this.removed=true;}
}
function setup(width=1160,mutate){
 const ids=['saved-data','stock','mode','version','date','back','forward','last','download','chart','error','date-title','summary','quality','identity','provenance','ma-values','legend','hover','source-bar','pivots','zones','pending','events','snapshot-json'];
 const elements=Object.fromEntries(ids.map(id=>[id,new Element()]));let data=JSON.parse(payload);if(mutate)mutate(data);elements['saved-data'].textContent=JSON.stringify(data);
 const calls=[],downloads=[],links=[],timers=[];
 const ctx=new Proxy({},{get(t,k){if(k in t)return t[k];return(...args)=>{for(const a of args)if(typeof a==='number')assert(Number.isFinite(a),'non-finite '+k);calls.push([k,...args]);};},set(t,k,v){t[k]=v;return true;}});
 Object.assign(elements.chart,{clientWidth:width-50,clientHeight:330,width:0,height:0,getContext:()=>ctx,getBoundingClientRect:()=>({left:0})});
 const sandbox=vm.createContext({document:{body:new Element('body'),getElementById:id=>elements[id],createElement:tag=>{const n=new Element(tag);if(tag==='a')links.push(n);return n;}},window:{devicePixelRatio:1,addEventListener:()=>{}},Blob:class{constructor(parts,options){downloads.push({parts,options});}},URL:{createObjectURL:()=> 'blob:test',revokeObjectURL:()=>{}},setTimeout:fn=>{timers.push(fn);return 1;}});
 vm.runInContext(script,sandbox);
 return{elements,calls,downloads,links,run:s=>vm.runInContext(s,sandbox),change(id,value){elements[id].value=value;elements[id].fire('change');}};
}
function check(name,fn){fn();results.push({test:name,status:'PASS'});}
function stable(v){if(Array.isArray(v))return v.map(stable);if(v&&typeof v==='object')return Object.fromEntries(Object.keys(v).sort().map(k=>[k,stable(v[k])]));return v;}
function canonical(v){if(Array.isArray(v))return '['+v.map(canonical).join(',')+']';if(v&&typeof v==='object')return '{'+Object.keys(v).sort().map(k=>JSON.stringify(k)+':'+canonical(v[k])).join(',')+'}';return JSON.stringify(v);}
function hash(v){return 'sha256:'+crypto.createHash('sha256').update(canonical(v)).digest('hex');}
const q=setup();
check('three exact saved records and all 745 selections match Python snapshot fingerprints',()=>{
 let count=0;
 for(const expected of expectations){const info=q.run(`DATA.records.find(b=>b.record_id===${JSON.stringify(expected.record_id)}).result.shared_input`);q.change('stock',info.code);q.change('mode',info.price_mode);q.change('version',expected.record_id);q.change('date',expected.as_of);assert.equal(q.elements.error.textContent,'');assert.equal(hash(q.run('downloadValue().snapshot')),expected.snapshot_fingerprint);assert(q.elements.identity.textContent.includes(expected.record_id));count++;}
 assert.equal(count,745);
});
check('initial native-share case exposes unverified events and incomplete 260 MA',()=>{
 q.change('stock','1101');q.elements.last.fire('click');assert.match(q.elements.quality.textContent,/UNVERIFIED/);assert.match(q.elements.quality.textContent,/原生股數/);assert.match(q.elements.quality.textContent,/誤標/);assert.match(q.elements['source-bar'].textContent,/來源原生股數/);assert.match(q.elements['ma-values'].children[4].textContent,/資料不足.*需 260 筆；此日 179 筆/);
});
check('earliest MA is null and a complete window is read from storage',()=>{
 const dates=q.run('selectedRecord().result.aligned_snapshots.map(s=>s.as_of)');q.change('date',dates[3]);assert.match(q.elements['ma-values'].children[0].textContent,/資料不足/);q.change('date',dates[4]);assert(!q.elements['ma-values'].children[0].textContent.includes('資料不足'));
});
check('raw and adjusted modes keep distinct snapshot identities and event policy',()=>{
 q.change('stock','8069');q.change('mode','RAW_CANDIDATE');const dt=q.run("selectedRecord().result.components.structure.snapshots.find(s=>s.daily_events.some(e=>e.type==='RAW_CORPORATE_ACTION_BOUNDARY')).as_of");q.change('date',dt);const raw=q.run('downloadValue().snapshot');assert.match(q.elements.events.textContent,/RAW_CORPORATE_ACTION_BOUNDARY/);q.change('mode','ADJUSTED_CANDIDATE');const adj=q.run('downloadValue().snapshot');assert.notEqual(raw.record_id,adj.record_id);assert.notEqual(raw.structure.snapshot_id,adj.structure.snapshot_id);assert(!q.elements.events.textContent.includes('RAW_CORPORATE_ACTION_BOUNDARY'));assert.equal(raw.as_of,adj.as_of);
});
check('missing date on stock change clears stale data and requires explicit selection',()=>{
 q.change('date','2025-08-01');assert(q.elements.summary.textContent);q.change('stock','1101');assert.match(q.elements.error.textContent,/日期/);for(const id of ['summary','identity','ma-values','source-bar','pivots','zones','snapshot-json','hover'])assert.equal(q.elements[id].textContent,'');assert(q.elements.download.disabled);assert.equal(q.run('current'),null);q.elements.last.fire('click');assert.equal(q.elements['date-title'].textContent,'2026-09-30');
});
check('invalid date and record never fall back to another saved result',()=>{
 q.change('date','2026-01-01');assert.match(q.elements.error.textContent,/日期/);assert(q.elements.download.disabled);q.change('version','not-saved');assert.match(q.elements.error.textContent,/版本/);assert.equal(q.run('current'),null);q.change('stock','1101');q.elements.last.fire('click');
});
check('back/forward boundaries and latest saved date navigate exact records',()=>{
 q.elements.last.fire('click');assert(q.elements.forward.disabled);const dt=q.elements['date-title'].textContent;q.elements.back.fire('click');assert.notEqual(q.elements['date-title'].textContent,dt);q.elements.forward.fire('click');assert.equal(q.elements['date-title'].textContent,dt);q.change('date',q.run('current.r.aligned_snapshots[0].as_of'));assert(q.elements.back.disabled);q.elements.back.fire('click');assert.equal(q.run('current.i'),0);
});
check('download payload retains exact snapshot and provenance without mutation',()=>{
 const before=q.run('JSON.stringify(DATA)');q.elements.download.fire('click');assert.equal(q.downloads.length,1);const value=JSON.parse(q.downloads[0].parts.join(''));assert.equal(hash(value.snapshot),hash(q.run('current.snapshot')));assert.equal(value.record.record_id,value.snapshot.record_id);assert.match(q.links[0].download,/1101_RAW_CANDIDATE_/);assert(q.links[0].clicked&&q.links[0].removed);assert.equal(q.run('JSON.stringify(DATA)'),before);
});
check('multiple evidence/rule versions require explicit record choice',()=>{
 const multi=setup(1160,data=>{const b=structuredClone(data.records.find(b=>b.result.shared_input.code==='1101'));b.record_id='fixture-new-evidence';b.created_at_utc='2099-01-01T00:00:00+00:00';b.evidence.records.push({status:'UNVERIFIED',reason:'synthetic selection only'});data.records.push(b);});assert.equal(multi.elements.version.value,'');assert(multi.elements.download.disabled);assert.match(multi.elements.error.textContent,/版本/);const id=multi.run("DATA.records.find(b=>b.result.shared_input.code==='1101').record_id");multi.change('version',id);assert.equal(multi.elements.error.textContent,'');assert.equal(multi.run('current.b.record_id'),id);
});
check('cross-linked snapshots, wrong source and malformed curves fail closed',()=>{
 for(const mutation of ["current.r.aligned_snapshots[current.i].structure_snapshot_id='wrong'","current.snapshot.structure.source_id='other'","current.snapshot.daily_ma.curves['5'][current.i]='NaN'","current.snapshot.daily_ma.available['260']=true"]){const bad=setup();bad.run(mutation+';draw()');assert(bad.elements.error.textContent);assert.equal(bad.elements.summary.textContent,'');assert(bad.elements.download.disabled);assert.equal(bad.run('current'),null);}
});
check('empty and malformed export envelopes show errors without stale metrics',()=>{
 for(const change of [d=>{d.records=[];},d=>{d.schema_version='future';}]){const bad=setup(1160,change);assert(bad.elements.error.textContent);assert.equal(bad.elements['ma-values'].textContent,'');assert(bad.elements.download.disabled);}
});
check('missing and zero source volume are distinct and are never scaled in UI',()=>{
 q.elements.last.fire('click');q.run('current.b.request.candles[current.i].volume_shares_scaled=null;draw()');assert.match(q.elements['source-bar'].textContent,/未提供/);q.run('current.b.request.candles[current.i].volume_shares_scaled=0;draw()');assert.match(q.elements['source-bar'].textContent,/成交量 0 股/);
});
check('narrow-width canvas math and hover work; date change clears hover',()=>{
 const narrow=setup(390);narrow.elements.chart.fire('pointermove',{clientX:150});assert.match(narrow.elements.hover.textContent,/錨定/);narrow.elements.back.fire('click');assert.match(narrow.elements.hover.textContent,/移到線圖/);assert(narrow.calls.length>0);
});
check('all-unavailable or deselected curves do not draw non-finite coordinates',()=>{
 q.elements.last.fire('click');q.run('chosen.clear();plotLines()');assert.equal(q.run('plot'),null);assert(q.calls.some(c=>c[0]==='fillText'&&c[1].includes('尚無可繪資料')));
});
check('stored text is inserted as text; no analysis or network code in page',()=>{
 assert(!/innerHTML|eval\(|fetch\(|XMLHttpRequest|localStorage|run_analysis_job|project_prices/.test(script));const xss=setup(1160,d=>{d.records.find(b=>b.result.shared_input.code==='1101').reason='<img src=x onerror=alert(1)>';});assert(xss.elements.provenance.textContent.includes('<img src=x onerror=alert(1)>'));
});
const report={status:'PASS',results,real_snapshots_compared:expectations.length,method:'Real inline JavaScript executed by Node VM with DOM/canvas doubles; snapshot canonical SHA256 compared with Python',browser_rendering:'NOT_TESTED',layout_and_touch:'NOT_TESTED',mutations:'In-memory synthetic fixtures only'};
fs.writeFileSync(path.join(root,'saved_viewer/output/唯讀頁面邏輯測試.json'),JSON.stringify(report,null,2));console.log(JSON.stringify(report,null,2));
