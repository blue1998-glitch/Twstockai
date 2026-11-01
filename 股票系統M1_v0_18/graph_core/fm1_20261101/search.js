'use strict';
(()=>{
const marketState=JSON.parse($('market-state').textContent);$('market-state').remove();
window.marketState=marketState;
const mainChart=document.querySelector('main'),searchPanel=document.createElement('section');mainChart.before(searchPanel);searchPanel.style.cssText='padding:12px;max-width:1450px;margin:auto;overflow-wrap:anywhere';
text('h1','全市場每日研究｜私人預覽 PARTIAL',searchPanel);
text('p',`行情日期 ${marketState.summary.as_of}；應處理 ${marketState.summary.expected}／已留終態 ${marketState.summary.processed}。目前名單不是已認證歷史母體。沒有固定手機網址或正式策略／交易資格。`,searchPanel);
text('p','只有一日者為歷史不足，即使原核心能讀取，也不算完整分析成功。不是以沒有箱型判定沒有機會；不混接舊四股缺失期間。MA／MACD暖機null不補0。',searchPanel);
const controls=text('div','',searchPanel);controls.className='toolbar';const query=text('input','',controls);query.id='marketSearch';query.placeholder='股票代號或名稱';query.setAttribute('aria-label','全市場股票搜尋');query.style.cssText='min-height:44px;max-width:100%;padding:8px';
const filter=text('select','',controls);filter.id='marketFilter';filter.setAttribute('aria-label','分析終態篩選');options(filter,[['ALL','全部終態'],...new Set(marketState.stocks.map(s=>s.status))].map(v=>Array.isArray(v)?v:[v,v]),'ALL');
const previous=text('button','上一頁',controls),next=text('button','下一頁',controls),info=text('p','',searchPanel),list=text('div','',searchPanel);list.id='marketResults';let page=0;
function listStocks(){const matches=marketState.stocks.filter(s=>(s.code+' '+s.name).toLowerCase().includes(query.value.trim().toLowerCase())&&(filter.value==='ALL'||s.status===filter.value));const pages=Math.max(1,Math.ceil(matches.length/50));page=Math.min(page,pages-1);info.textContent=`符合 ${matches.length}檔；第${page+1}／${pages}頁（每頁50，完整集合可翻頁，非抽樣）。`;list.replaceChildren();for(const s of matches.slice(page*50,(page+1)*50)){const row=text('div','',list);row.style.cssText='padding:8px;border-bottom:1px solid #506c86;display:flex;flex-wrap:wrap;gap:8px;align-items:center';text('span',`${s.code} ${s.name}｜${s.market}｜${s.as_of}｜${s.status}`,row);const b=text('button',s.result_key?'看原核心／日K／量／MACD':'檢視拒判原因',row);b.dataset.marketCode=s.code;b.onclick=()=>{if(s.result_key){mainChart.hidden=false;$('stock').value=s.code;setup(s.code,s.as_of);$('status').textContent=`${s.status}｜${$('status').textContent} 來源／歷史不足仍UNKNOWN，非正式資格。`;$('chartWrap').scrollIntoView({block:'start'});}else{mainChart.hidden=true;info.textContent=`${s.code} ${s.status}：${s.reason||'原來源不足'}。不載其他股票或舊日期冒充。`;}};}previous.disabled=page===0;next.disabled=page===pages-1;}
query.oninput=filter.onchange=()=>{page=0;listStocks();};previous.onclick=()=>{page--;listStocks();};next.onclick=()=>{page++;listStocks();};listStocks();
})();
