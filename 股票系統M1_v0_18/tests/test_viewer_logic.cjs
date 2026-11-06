// Executes the real inline viewer script with a minimal DOM/canvas test double.
// This does NOT verify browser rendering, layout, accessibility, or touch input.
const fs=require('fs'),path=require('path'),vm=require('vm'),assert=require('assert/strict');
const root=path.resolve(__dirname,'..');
const html=fs.readFileSync(process.env.VIEWER_HTML||path.join(root,'價格結構重播.html'),'utf8');
const script=html.match(/<script>([\s\S]*)<\/script>/)[1];
const results=[];
class Element {
  constructor(id=''){this.id=id;this.value='';this.checked=false;this.children=[];this.listeners={};this._text='';this.style={};}
  set textContent(v){this._text=String(v);this.children=[];}
  get textContent(){return this._text+this.children.map(c=>c.textContent).join('');}
  append(...children){this.children.push(...children);}
  replaceChildren(...children){this._text='';this.children=children;}
  addEventListener(name,fn){this.listeners[name]=fn;}
  fire(name,event={}){const fn=this.listeners[name]||this['on'+name];assert.equal(typeof fn,'function');fn(event);}
}
function setup(width=1280){
  const ids=['stock','mode','span','minor','zones','day','date','progress','back','forward','last','chart','hover','status','events','pivots','ma5','ma20','ma60','ma130','ma260','ma_values'];
  const elements=Object.fromEntries(ids.map(id=>[id,new Element(id)]));
  for(const [id,v] of Object.entries({stock:'8069',mode:'ADJUSTED_CANDIDATE',span:'100',day:'282'}))elements[id].value=v;
  elements.zones.checked=true;
  elements.ma20.checked=true;elements.ma60.checked=true;
  const calls=[];
  const context2d=new Proxy({}, {get(target,key){if(key in target)return target[key];return (...args)=>{for(const a of args)if(typeof a==='number')assert(Number.isFinite(a),`nonfinite canvas argument in ${key}`);calls.push([key,...args]);};},set(target,key,value){target[key]=value;return true;}});
  Object.assign(elements.chart,{clientWidth:width-48,clientHeight:470,getContext:()=>context2d,getBoundingClientRect:()=>({left:0})});
  const listeners={};
  const sandbox=vm.createContext({document:{getElementById:id=>elements[id],createElement:()=>new Element()},window:{devicePixelRatio:1,addEventListener:(name,fn)=>{listeners[name]=fn;}}});
  vm.runInContext(script,sandbox);
  return {elements,calls,run:s=>vm.runInContext(s,sandbox),change:(id,value,event='change')=>{elements[id].value=value;elements[id].fire(event);}};
}
function check(name,fn){fn();results.push({test:name,status:'PASS'});}
const q=setup();
check('initial stock/date and record navigation',()=>{
  assert.equal(q.elements.date.textContent,'2026-09-30');
  q.elements.back.fire('click');assert.equal(q.elements.date.textContent,'2026-09-29');
  q.elements.forward.fire('click');assert.equal(q.elements.date.textContent,'2026-09-30');assert(q.elements.forward.disabled);
  q.change('day',0,'input');assert(q.elements.back.disabled);q.elements.back.fire('click');assert.equal(+q.elements.day.value,0);
});
check('stock and mode controls expose Raw dividend boundary',()=>{
  q.change('stock','6488');q.change('mode','RAW_CANDIDATE');
  const n=q.run("DATA['6488'].candles.findIndex(c=>c.date==='2026-07-16')");q.change('day',n,'input');
  assert.match(q.elements.events.textContent,/Raw除息邊界/);assert.match(q.elements.status.textContent,/未知/);
  q.change('mode','ADJUSTED_CANDIDATE');assert(!q.elements.events.textContent.includes('Raw除息邊界'));
});
check('all 1132 decoded snapshots respect occurrence and confirmation chronology',()=>{
  assert(q.run('Object.values(DATA).every(rec=>Object.values(rec.modes).every(ss=>ss.every((s,i)=>s.pivots.every(p=>p.occurred_index<=p.confirmed_index&&p.confirmed_index<=i))))'));
});
check('all 1132 real stock/mode/dates draw with finite numeric coordinates',()=>{
  let count=0;
  for(const code of ['8069','6488'])for(const mode of ['RAW_CANDIDATE','ADJUSTED_CANDIDATE']){
    q.change('stock',code);q.change('mode',mode);
    for(let i=0;i<283;i++){q.calls.length=0;q.change('day',i,'input');assert.equal(q.elements.date.textContent,q.run(`DATA[${JSON.stringify(code)}].candles[${i}].date`));count++;}
  }
  assert.equal(count,1132);
  assert.equal(q.run("prices(DATA['6488'],'RAW_CANDIDATE',238).find(c=>c.date==='2026-07-16').close"),1370);
});
check('display price basis matches numeric engine before/on/after cash events',()=>{
  const cases=JSON.parse(fs.readFileSync(path.join(root,'data/viewer_price_projection_cases.json'),'utf8'));
  assert.equal(cases.length,26);
  for(const c of cases){
    const rows=q.run(`prices(DATA[${JSON.stringify(c.code)}],${JSON.stringify(c.mode)},${c.index})`);
    assert.equal(rows.length,c.expected.length);
    for(let i=0;i<rows.length;i++)for(const [j,k] of ['open','high','low','close'].entries()){
      const expected=Number(c.expected[i][j]);assert(Math.abs(rows[i][k]-expected)<=1e-12*Math.max(1,Math.abs(expected)),`${c.code}/${c.mode}/${c.as_of}/${i}/${k}`);
    }
  }
});
check('MA readout distinguishes full windows and insufficient records',()=>{
  q.change('day',3,'input');assert.match(q.elements.ma_values.textContent,/需5筆，現有4筆/);
  q.change('day',4,'input');assert(!q.elements.ma_values.children[0].textContent.includes('尚未形成'));
  q.change('day',258,'input');assert.match(q.elements.ma_values.textContent,/需260筆，現有259筆/);
  q.change('day',259,'input');assert(!q.elements.ma_values.children[4].textContent.includes('尚未形成'));
  assert(q.run('Object.values(DATA).every(rec=>Object.values(rec.modes).every(ss=>ss.every((s,i)=>Object.values(s.moving_averages).every(v=>v.length===i+1))))'));
});
check('all five MA toggles add exactly five line paths at a complete window',()=>{
  q.elements.last.fire('click');q.run("for(const p of [5,20,60,130,260])$('ma'+p).checked=false");q.calls.length=0;q.run('draw()');
  const before=q.calls.filter(c=>c[0]==='stroke').length;
  q.run("for(const p of [5,20,60,130,260])$('ma'+p).checked=true");q.calls.length=0;q.elements.ma260.fire('change');
  assert.equal(q.calls.filter(c=>c[0]==='stroke').length,before+5);
});
check('all provided calendar states and unknown status remain explicit',()=>{
  for(const [s,pattern] of [['UNVERIFIED',/尚未核對/],['MATCHES_SUPPLIED_CALENDAR',/符合提供日曆.*來源未認證/],['DIFFERS_FROM_SUPPLIED_CALENDAR',/不一致/],['NEW_STATUS',/未知狀態/]]){
    q.run(`selected().snap.data_quality.calendar_status=${JSON.stringify(s)};draw()`);assert.match(q.elements.status.textContent,pattern);
  }
});
check('missing volume is not converted to zero in canvas or tooltip',()=>{
  q.elements.last.fire('click');q.change('span','60');
  q.run('selected().rec.candles.forEach(c=>c.volume_shares_scaled=null);selected().snap.data_quality.volume_context="UNAVAILABLE"');
  q.calls.length=0;q.run('draw()');
  // zones disabled below to count only price candles; no volume rectangles.
  q.elements.zones.checked=false;q.calls.length=0;q.run('draw()');
  assert.equal(q.calls.filter(c=>c[0]==='fillRect').length,60);
  q.elements.chart.fire('pointermove',{clientX:100});assert.match(q.elements.hover.textContent,/未提供/);assert(!q.elements.hover.textContent.includes('NaN'));
  assert.match(q.elements.status.textContent,/未提供成交量/);
});
check('zero volume remains an explicit valid zero, partial data is disclosed',()=>{
  q.run('selected().rec.candles.forEach(c=>c.volume_shares_scaled=0);selected().snap.data_quality.volume_context="PARTIAL";draw()');
  q.elements.chart.fire('pointermove',{clientX:100});assert.match(q.elements.hover.textContent,/0 股/);assert.match(q.elements.status.textContent,/部分缺少/);
  q.run('delete selected().rec.candles[282].volume_shares_scaled;draw()');
});
check('new stock/date selection clears stale hovered price',()=>{
  q.elements.chart.fire('pointermove',{clientX:100});q.change('stock','8069');assert.match(q.elements.hover.textContent,/移動到K線/);
});
check('controls use source record count instead of fixed 282',()=>{
  q.run("DATA['8069'].candles=DATA['8069'].candles.slice(0,25);for(const mode of Object.keys(DATA['8069'].modes))DATA['8069'].modes[mode]=DATA['8069'].modes[mode].slice(0,25);draw()");
  assert.equal(+q.elements.day.max,24);assert.equal(+q.elements.day.value,24);
  q.elements.back.fire('click');assert.equal(+q.elements.day.value,23);q.elements.last.fire('click');assert.equal(+q.elements.day.value,24);
});
check('narrow canvas arithmetic executes with optional overlays',()=>{
  const mobile=setup(390);mobile.elements.minor.checked=true;mobile.elements.minor.fire('change');mobile.elements.zones.checked=false;mobile.elements.zones.fire('change');mobile.change('span','180');assert(mobile.calls.length>0);
});
fs.writeFileSync(path.join(root,'output','頁面邏輯測試.json'),JSON.stringify({status:'PASS',results,method:'Real inline JavaScript executed by Node vm with DOM/canvas test doubles',browser_interaction:'NOT_VERIFIED',layout_and_touch:'NOT_VERIFIED',synthetic_mutations:'In-memory fixtures only; source files unchanged'},null,2));
console.log(JSON.stringify(results,null,2));
