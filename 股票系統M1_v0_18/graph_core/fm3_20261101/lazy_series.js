// Private same-origin stored data only. No analysis or source API in browser.
let marketLoadEpoch=0;
window.cancelMarketLoad=()=>{marketLoadEpoch++;};
async function readPrivateDescriptor(descriptor){
 if(!descriptor||!/^series-[a-f0-9]{64}\.json$/.test(descriptor.path)||descriptor.path.slice(7,-5)!==descriptor.sha256)throw Error('Missing private series binding');
 const embedded=document.getElementById('synthetic-demo-series');
 const response=embedded ? new Response(JSON.parse(embedded.textContent)[descriptor.path]) : await fetch(descriptor.path,{credentials:'same-origin',redirect:'error',cache:'no-store'});
 if(!response.ok)throw Error('Private series unavailable');
 const raw=await response.arrayBuffer();
 if(raw.byteLength!==descriptor.bytes)throw Error('Private series length changed');
 const sha=Array.from(new Uint8Array(await crypto.subtle.digest('SHA-256',raw))).map(n=>n.toString(16).padStart(2,'0')).join('');
 if(sha!==descriptor.sha256)throw Error('Private series fingerprint changed');
 return JSON.parse(new TextDecoder('utf-8',{fatal:true}).decode(raw));
}
async function withPrivateEvidence(series,stock){
 if(!stock.preview_evidence)return series; // All older batches keep their existing behavior.
 const x=await readPrivateDescriptor(stock.preview_evidence),r=series.results[0],c=x.comparison_evidence;
 if(x.schema!=='private-workbench-evidence/0.1'||x.identity!==stock.identity||x.code!==stock.code||x.market!==stock.market||x.as_of!==stock.as_of||x.result_id!==r.result_id||x.source_id!==series.source.id||x.price_basis_id!==series.price_basis_id||x.source_prefix_fingerprint!==r.source_prefix_fingerprint||x.original_series_sha256!==stock.preview_series.sha256||!c||c.result_id!==r.result_id||c.identity!==stock.identity||c.source_id!==series.source.id||c.price_basis_id!==series.price_basis_id||c.source_prefix_fingerprint!==r.source_prefix_fingerprint||c.as_of!==r.as_of)throw Error('Private evidence identity/source/basis mismatch');
 return {...series,comparison_evidence:c}; // Do not mutate any saved K/core/indicator values.
}
window.readMarketStock=async stock=>{
 let series=data.series.find(s=>s.code===stock.code&&s.exchange===stock.market&&s.results.some(r=>r.as_of===stock.as_of));
 if(!series)series=decode(await readPrivateDescriptor(stock.preview_series));
 if(series.code!==stock.code||series.exchange!==stock.market||series.results.length!==1||series.results[0].as_of!==stock.as_of)throw Error('Private series identity mismatch');
 return withPrivateEvidence(series,stock);
};
window.loadMarketStock=async stock=>{
 const epoch=++marketLoadEpoch;const series=await window.readMarketStock(stock);
 if(epoch!==marketLoadEpoch)throw Error('Superseded selection');
 data.series.splice(0,data.series.length,series);
 options($('stock'),[[stock.code,stock.code+' '+stock.name]],stock.code);
};
