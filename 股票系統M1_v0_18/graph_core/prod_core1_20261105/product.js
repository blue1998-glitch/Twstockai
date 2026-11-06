// Formal product status; prices and charts remain the original source-bound UI.
(()=>{
 const root=document.querySelector('#workbench'),overview=document.querySelector('#marketOverview');
 const panel=document.createElement('section');panel.id='productStatus';panel.setAttribute('aria-live','polite');
 const heading=document.createElement('h2');heading.textContent='每日分析';panel.append(heading);
 const line=document.createElement('p');line.textContent='讀取更新狀態';panel.append(line);overview.before(panel);
 const dates=document.createElement('a');dates.href='/batches';dates.textContent='選擇資料日期';panel.append(dates);
 document.querySelector('#workStatus').textContent='選股 → 看價量與判定';
 document.querySelector('#marketFilter').setAttribute('aria-label','分析狀態');
 document.querySelector('#marketExchange').setAttribute('aria-label','交易市場');
 const style=document.createElement('style');style.textContent='#productStatus{padding:12px;border:1px solid #294350;border-radius:12px;margin:10px 0}#productStatus p{margin:8px 0;overflow-wrap:anywhere}#productStatus a{display:inline-block;padding:10px}#marketResults article{min-width:0}.toolbar select{max-width:100%}';document.head.append(style);
 fetch('/product-status.json',{credentials:'same-origin',cache:'no-store'}).then(r=>{if(!r.ok)throw Error();return r.json();}).then(v=>{
  window.productStatus=v;line.textContent='已完成 '+v.active_date+' · '+v.reference+' 檔';
  const a=v.latest_intake;if(a){const t=document.createElement('p');t.id='latestIntake';t.textContent=a.target_date+'：'+(a.status==='BLOCKED_SOURCE'?'來源未合格，保留目前資料':a.status==='PARTIAL'?'逐股處理中，保留前批':'接件完成');panel.append(t);}
  const note=document.createElement('small');note.textContent='手動更新｜歷史不足不產生買賣判定';panel.append(note);
 }).catch(()=>{line.textContent='更新狀態暫不可讀；目前價格日期不變';});
})();
