const fs=require('fs'),vm=require('vm'),assert=require('assert/strict'),crypto=require('crypto');
const source=fs.readFileSync(require('path').join(__dirname,'../fm3_20261101/lazy_series.js'),'utf8');
const sha=s=>crypto.createHash('sha256').update(s).digest('hex');
(async()=>{
 const records=new Map(),r={result_id:'SYNTHETIC_RESULT',as_of:'2000-01-01',source_prefix_fingerprint:'SYNTHETIC_PREFIX'};
 const series={code:'SYNTHETIC',exchange:'TEST',source:{id:'SYNTHETIC_SOURCE'},price_basis_id:'SYNTHETIC_RAW',results:[r],bars:[{date:r.as_of}]};
 const desc=v=>{const raw=JSON.stringify(v),hash=sha(raw),path='series-'+hash+'.json';records.set(path,raw);return{path,sha256:hash,bytes:Buffer.byteLength(raw)}};
 const original=desc(series),stock={code:series.code,market:series.exchange,identity:'TEST:SYNTHETIC',as_of:r.as_of,preview_series:original};
 const comparison={schema:'stock-comparison-evidence/0.1',identity:stock.identity,code:stock.code,market:stock.market,as_of:stock.as_of,result_id:r.result_id,source_id:series.source.id,price_basis_id:series.price_basis_id,source_prefix_fingerprint:r.source_prefix_fingerprint};
 const evidence={schema:'private-workbench-evidence/0.1',identity:stock.identity,code:stock.code,market:stock.market,as_of:stock.as_of,result_id:r.result_id,source_id:series.source.id,price_basis_id:series.price_basis_id,source_prefix_fingerprint:r.source_prefix_fingerprint,original_series_sha256:original.sha256,comparison_evidence:comparison};
 stock.preview_evidence=desc(evidence);
 const ctx={console,Response,TextDecoder,Uint8Array,crypto:crypto.webcrypto,data:{series:[]},document:{getElementById:()=>null},decode:x=>x,options:()=>{},$:()=>({}),fetch:async path=>new Response(records.get(path)),};
 ctx.window=ctx;vm.createContext(ctx);vm.runInContext(source,ctx);
 let x=await ctx.readMarketStock(stock);assert.equal(x.comparison_evidence.result_id,r.result_id);assert.equal(ctx.data.series.length,0);
 for(const field of ['identity','as_of','source_id','price_basis_id','source_prefix_fingerprint','original_series_sha256']){
  const bad={...stock,preview_evidence:desc({...evidence,[field]:'OTHER'})};await assert.rejects(()=>ctx.readMarketStock(bad),/evidence identity/);
 }
 const nested={...stock,preview_evidence:desc({...evidence,comparison_evidence:{...comparison,result_id:'OTHER'}})};await assert.rejects(()=>ctx.readMarketStock(nested),/evidence identity/);
 const bad={...stock,preview_evidence:{...stock.preview_evidence,bytes:1}};await assert.rejects(()=>ctx.readMarketStock(bad),/length changed/);
 records.set(stock.preview_evidence.path,'X'.repeat(stock.preview_evidence.bytes));await assert.rejects(()=>ctx.readMarketStock(stock),/fingerprint changed/);
 const legacy={...stock};delete legacy.preview_evidence;assert.equal((await ctx.readMarketStock(legacy)).code,stock.code);
 console.log('PASS synthetic loader binding, nested mismatch, exact bytes/hash, no comparison cache growth and legacy compatibility');
})().catch(e=>{console.error(e);process.exitCode=1});
