// Actual six old/new saved records; DOM/canvas doubles are not browser QA.
const fs=require('fs'),path=require('path'),vm=require('vm'),assert=require('assert/strict'),crypto=require('crypto');
const root=path.resolve(__dirname,'..'),out=path.join(root,'volume_revision/output');
const html=fs.readFileSync(path.join(root,'成交量版本比較瀏覽.html'),'utf8');
const data=html.match(/<script id="saved-data" type="application\/json">([\s\S]*?)<\/script>/)[1];
const script=html.match(/<script>\n([\s\S]*?)<\/script>/)[1];new vm.Script(script);
const expectations=JSON.parse(fs.readFileSync(path.join(out,'保存結果完整比對.json'),'utf8')).snapshot_expectations;
const pairs=JSON.parse(fs.readFileSync(path.join(out,'成交量單位與新舊版本驗收.json'),'utf8')).saved_pairs;
class Element{
 constructor(){this.children=[];this.listeners={};this.style={};this._text='';this.value='';this.disabled=false;}
 set textContent(v){this._text=String(v);this.children=[];}get textContent(){return this._text+this.children.map(n=>n.textContent).join('');}
 replaceChildren(...nodes){this._text='';this.children=nodes;}append(...nodes){this.children.push(...nodes);}
 addEventListener(t,fn){this.listeners[t]=fn;}fire(t,e={}){assert.equal(typeof this.listeners[t],'function');this.listeners[t](e);}
 click(){this.clicked=true;}remove(){this.removed=true;}
}
function setup(width=1160){
 const ids=['saved-data','stock','mode','version','date','back','forward','last','download','chart','error','date-title','summary','quality','identity','provenance','ma-values','legend','hover','source-bar','pivots','zones','pending','events','snapshot-json'];
 const elements=Object.fromEntries(ids.map(id=>[id,new Element()]));elements['saved-data'].textContent=data;
 const calls=[],downloads=[],links=[];
 const ctx=new Proxy({},{get(t,k){if(k in t)return t[k];return(...a)=>{for(const v of a)if(typeof v==='number')assert(Number.isFinite(v),'non-finite '+k);calls.push([k,...a]);};},set(t,k,v){t[k]=v;return true;}});
 Object.assign(elements.chart,{clientWidth:width-50,clientHeight:330,width:0,height:0,getContext:()=>ctx,getBoundingClientRect:()=>({left:0})});
 const sandbox=vm.createContext({document:{body:new Element(),getElementById:id=>elements[id],createElement:t=>{const e=new Element();if(t==='a')links.push(e);return e;}},window:{devicePixelRatio:1,addEventListener:()=>{}},Blob:class{constructor(parts){downloads.push(parts.join(''));}},URL:{createObjectURL:()=> 'blob:test',revokeObjectURL:()=>{}},setTimeout:()=>1});
 vm.runInContext(script,sandbox);return{elements,calls,downloads,links,run:s=>vm.runInContext(s,sandbox),change(id,v){elements[id].value=v;elements[id].fire('change');}};
}
function canonical(v){if(Array.isArray(v))return '['+v.map(canonical).join(',')+']';if(v&&typeof v==='object')return '{'+Object.keys(v).sort().map(k=>JSON.stringify(k)+':'+canonical(v[k])).join(',')+'}';return JSON.stringify(v);}
function hash(v){return 'sha256:'+crypto.createHash('sha256').update(canonical(v)).digest('hex');}
const results=[];function check(name,fn){fn();results.push({test:name,status:'PASS'});}
const q=setup();
function choose(p,id){q.change('stock',p.code);q.change('mode',p.price_mode);q.change('version',id);q.elements.last.fire('click');assert.equal(q.elements.error.textContent,'');}
check('actual old/new records require explicit version; neither is silently selected',()=>{
 assert.equal(q.run('DATA.records.length'),6);assert.equal(q.elements.version.value,'');assert(q.elements.download.disabled);assert.match(q.elements.error.textContent,/版本/);
 assert.match(q.elements.version.textContent,/來源單位修正版/);assert.match(q.elements.version.textContent,/歷史保存版/);
});
check('all 1490 actual saved snapshots equal Python public-read fingerprints',()=>{
 for(const expected of expectations){const b=q.run(`DATA.records.find(b=>b.record_id===${JSON.stringify(expected.record_id)}).result.shared_input`);q.change('stock',b.code);q.change('mode',b.price_mode);q.change('version',expected.record_id);q.change('date',expected.as_of);assert.equal(q.elements.error.textContent,'');assert.equal(hash(q.run('downloadValue().snapshot')),expected.snapshot_fingerprint);}
 assert.equal(expectations.length,1490);
});
check('native-source warning applies to the historical record and clears on corrected version',()=>{
 const p=pairs.find(p=>p.code==='1101');choose(p,p.old_record_id);assert.match(q.elements.quality.textContent,/誤標/);const values=q.elements['ma-values'].textContent;
 q.change('version',p.new_record_id);assert.equal(q.elements.error.textContent,'');assert(!q.elements.quality.textContent.includes('誤標'));assert.match(q.elements.quality.textContent,/沒有張數換算/);assert.equal(q.elements['ma-values'].textContent,values);assert.match(q.elements['source-bar'].textContent,/來源原生股數/);
});
check('old/new snapshots retain separate IDs, same MA and original unverified coverage',()=>{
 for(const p of pairs){choose(p,p.old_record_id);const a=q.run('downloadValue()');q.change('version',p.new_record_id);const b=q.run('downloadValue()');assert.notEqual(a.snapshot.analysis_id,b.snapshot.analysis_id);assert.notEqual(a.snapshot.structure.snapshot_id,b.snapshot.structure.snapshot_id);assert.equal(canonical(a.snapshot.daily_ma),canonical(b.snapshot.daily_ma));assert.equal(a.snapshot.evidence_coverage,b.snapshot.evidence_coverage);assert.equal(a.record.shared_input.source.id,b.record.shared_input.source.id);}
});
check('scaled-lot sources retain their original meaning in both producer versions',()=>{
 for(const p of pairs.filter(p=>p.code==='8069'))for(const id of [p.old_record_id,p.new_record_id]){choose(p,id);assert.match(q.elements['source-bar'].textContent,/來源張數換算股數/);assert.match(q.elements.quality.textContent,/由來源張數換算/);}
});
check('native null 260-window is never backfilled while switching versions',()=>{
 const p=pairs.find(p=>p.code==='1101');for(const id of [p.old_record_id,p.new_record_id]){choose(p,id);assert.match(q.elements['ma-values'].children[4].textContent,/資料不足.*179 筆/);assert.equal(q.run("current.snapshot.daily_ma.curves['260'].at(-1)"),null);}
});
check('snapshot JSON downloads preserve corrected and historical evidence without rewriting',()=>{
 const p=pairs.find(p=>p.code==='1101');choose(p,p.old_record_id);q.elements.download.fire('click');const a=JSON.parse(q.downloads.at(-1));assert(!('volume_unit' in a.snapshot.structure));assert(a.snapshot.structure.pivots.some(x=>x.evidence.volume_precision.startsWith('Source lots scaled')));
 q.change('version',p.new_record_id);q.elements.download.fire('click');const b=JSON.parse(q.downloads.at(-1));assert.equal(b.snapshot.structure.volume_unit,'SHARES_REPORTED');assert(b.snapshot.structure.pivots.every(x=>x.evidence.volume_precision.includes('no lot scaling')));assert.equal(b.record.rules.component_versions.structure,'structure-0.3-research');
});
check('missing dates and wrong record never retain old values or select a substitute',()=>{
 const p=pairs.find(p=>p.code==='8069');choose(p,p.new_record_id);q.change('date','2025-08-01');q.change('stock','1101');assert(q.elements.error.textContent);assert.equal(q.elements.summary.textContent,'');assert(q.elements.download.disabled);q.change('version','not-a-record');assert.equal(q.run('current'),null);
});
check('new unit mismatch fails closed and clears the previously shown record',()=>{
 const p=pairs.find(p=>p.code==='1101');choose(p,p.new_record_id);q.run("current.snapshot.structure.volume_unit='SHARES_SCALED_FROM_LOTS';draw()");assert.match(q.elements.error.textContent,/成交量來源單位/);assert.equal(q.elements['ma-values'].textContent,'');assert(q.elements.download.disabled);assert.equal(q.run('current'),null);
});
check('narrow-width actual new snapshot uses finite plot math and preserves dates',()=>{
 const mobile=setup(390),p=pairs.find(p=>p.code==='1101');mobile.change('version',p.new_record_id);mobile.elements.last.fire('click');assert.equal(mobile.elements.error.textContent,'');mobile.elements.chart.fire('pointermove',{clientX:120});assert.match(mobile.elements.hover.textContent,/錨定/);mobile.elements.back.fire('click');assert.match(mobile.elements.hover.textContent,/移到線圖/);assert(mobile.calls.length);
});
const report={status:'PASS',results,real_snapshot_comparisons:expectations.length,method:'Actual six saved records; real inline JS under Node VM with DOM/canvas doubles',browser_rendering:'NOT_TESTED',layout_and_touch:'NOT_TESTED'};
fs.writeFileSync(path.join(out,'新舊版本頁面邏輯測試.json'),JSON.stringify(report,null,2));console.log(JSON.stringify(report,null,2));
