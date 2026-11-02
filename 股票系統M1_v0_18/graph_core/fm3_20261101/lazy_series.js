// Private same-origin stored data only. No analysis or source API in browser.
let marketLoadEpoch=0;
window.cancelMarketLoad=()=>{marketLoadEpoch++;};
window.loadMarketStock=async stock=>{
 const epoch=++marketLoadEpoch;
 if(data.series.some(s=>s.code===stock.code&&s.exchange===stock.market))return;
 const descriptor=stock.preview_series;
 if(!descriptor||!/^series-[a-f0-9]{64}\.json$/.test(descriptor.path))throw Error('Missing private series binding');
 const embedded=document.getElementById('synthetic-demo-series');
 const response=embedded ? new Response(JSON.parse(embedded.textContent)[descriptor.path]) : await fetch(descriptor.path,{credentials:'same-origin',redirect:'error',cache:'no-store'});
 if(!response.ok)throw Error('Private series unavailable');
 const raw=await response.arrayBuffer();
 if(raw.byteLength!==descriptor.bytes)throw Error('Private series length changed');
 const sha=Array.from(new Uint8Array(await crypto.subtle.digest('SHA-256',raw))).map(n=>n.toString(16).padStart(2,'0')).join('');
 if(sha!==descriptor.sha256)throw Error('Private series fingerprint changed');
 const series=decode(JSON.parse(new TextDecoder('utf-8',{fatal:true}).decode(raw)));
 if(series.code!==stock.code||series.exchange!==stock.market||series.results.length!==1||series.results[0].as_of!==stock.as_of)throw Error('Private series identity mismatch');
 if(epoch!==marketLoadEpoch)throw Error('Superseded selection');
 data.series.splice(0,data.series.length,series);
 options($('stock'),[[stock.code,stock.code+' '+stock.name]],stock.code);
};
