const assert=require('assert/strict');const {comparisonScope:f}=require('./compare.js');
const row=(id)=>({identity:id,schema:'stock-comparison-evidence/0.1',status:'ANALYZED_RESEARCH',as_of:'2026-11-02',source_end:'2026-11-02',source_start:'2026-01-01',anchor:{date:'2026-11-02'},price_mode:'RAW_CANDIDATE',source_kind:'SYNTHETIC',data_gaps:{},historical_available_at:'UNKNOWN',corporate_action_comparability:'UNVERIFIED'});
const a=row('A'),b=row('B');assert.equal(f([a,b]).status,'LIMITED_DESCRIPTIVE');
for(const change of [{as_of:'2026-10-30'},{source_end:'2026-10-30'},{price_mode:'ADJUSTED_CANDIDATE'},{status:'INSUFFICIENT_HISTORY'},{schema:null}])assert.equal(f([a,{...b,...change}]).status,'REFUSED');
assert.equal(f([a,a]).status,'REFUSED');assert.equal(f([a]).status,'REFUSED');assert.equal(f([a,b,row('C'),row('D')]).status,'LIMITED_DESCRIPTIVE');assert.equal(f([a,b,row('C'),row('D'),row('E')]).status,'REFUSED');
for(const change of [{source_start:'2026-03-01'},{source_kind:'OTHER'},{data_gaps:{basis_resets:['2026-07-01']}}])assert.equal(f([a,{...b,...change}]).status,'LIMITED_DESCRIPTIVE');assert.equal(f([a,b]).ranking,null);assert.equal(f([a,b]).expected_return,'UNKNOWN');console.log('PASS shared comparison scope positive/refusal/limited controls');

const invalid=f([a,{identity:'BAD',status:'COMPARISON_REFUSED'}]);assert.equal(invalid.status,'REFUSED');assert(!invalid.refuse.some(x=>x.includes('RAW')||x.includes('分析日期不同')));console.log('PASS refusal reasons do not invent date/mode mismatch for unavailable evidence');
