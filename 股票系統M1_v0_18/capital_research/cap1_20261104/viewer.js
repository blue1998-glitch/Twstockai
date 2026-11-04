"use strict";
const DATA=JSON.parse(document.getElementById('cap1-data').textContent);
const $=id=>document.getElementById(id), branches=DATA.branches;
const labels={hold:'續抱原持股',reduce:'明示減碼 B 3股',exit_b:'退出 B 7股，保留 C',cash:'全退出持現金'};
const colors={hold:'#53d9c4',reduce:'#f3cb72',exit_b:'#beadff'};
let selected='hold';
// Formatting only. All equity, return, costs and drawdown are saved engine fields.
const money=v=>v==null?'尚無足夠資料':String(v).replace(/(\.\d*?[1-9])0+$|\.0+$/, '$1');
const pct=v=>v==null?'尚無足夠資料':(Number(v)*100).toFixed(3)+'%';
function text(id,value){$(id).textContent=value;}
function shares(row){return Object.entries(row.shares).filter(([,n])=>Number(n)!==0).map(([c,n])=>c+' '+n+'股').join('・')||'無';}
function line(){
 const keys=Object.keys(branches),all=keys.flatMap(k=>branches[k].metrics.statistics.curve.map(r=>Number(r.equity)));
 const lo=Math.min(...all),hi=Math.max(...all),span=hi-lo||1;
 const width=Math.max(300,Math.round($('chart').clientWidth)),left=55,right=width-12;
 $('chart').setAttribute('viewBox','0 0 '+width+' 260');
 const x=i=>left+i*(right-left)/(branches[selected].metrics.statistics.curve.length-1),y=v=>22+(hi-Number(v))*188/span;
 let s='';
 for(let i=0;i<3;i++){let v=hi-(hi-lo)*i/2,py=y(v);s+='<line x1="55" x2="'+right+'" y1="'+py+'" y2="'+py+'" stroke="#2b3b52"/><text x="4" y="'+(py+4)+'" fill="#b2c0d2" font-size="11">'+v.toFixed(2)+'</text>';}
 // Decision date comes from the source, not a hardcoded case date.
 const rows=branches[selected].metrics.statistics.curve,di=rows.findIndex(r=>r.date===DATA.decision_at.slice(0,10));
 if(di>=0)s+='<line x1="'+x(di)+'" x2="'+x(di)+'" y1="16" y2="216" stroke="#889ab3" stroke-dasharray="4 4"/><text x="'+(x(di)+4)+'" y="246" fill="#a8b7cc" font-size="11">行動選擇</text>';
 const ordered=keys.filter(k=>k!==selected).concat(selected);
 for(const k of ordered){const path=branches[k].metrics.statistics.curve.map((r,i)=>(i?'L':'M')+x(i)+','+y(r.equity)).join(' ');s+='<path data-curve="'+k+'" d="'+path+'" fill="none" stroke="'+colors[k]+'" stroke-width="'+(k===selected?4:2)+'" opacity="'+(k===selected?1:.48)+'"/>';}
 const ix=Number($('day').value),row=rows[ix];s+='<circle cx="'+x(ix)+'" cy="'+y(row.equity)+'" r="5" fill="'+colors[selected]+'"/><text x="55" y="230" fill="#b2c0d2" font-size="11">'+rows[0].date+'</text><text x="'+right+'" y="230" text-anchor="end" fill="#b2c0d2" font-size="11">'+rows.at(-1).date+'</text>';
 $('chart').innerHTML=s;
}
function daily(){
 if(selected==='cash')return;
 const b=branches[selected],i=Number($('day').value),r=b.ledger.daily[i];
 text('date',r.date);text('day-equity',money(r.net_accrual_equity));text('day-cash',money(r.settled_cash));text('day-receivable',money(r.cash_receivable));text('day-holdings',shares(r));
 text('day-rights',r.share_receivables.length?'有，見進階明細':'無');line();
}
function select(key){
 selected=key;document.querySelectorAll('[data-action]').forEach(b=>b.setAttribute('aria-pressed',String(b.dataset.action===key)));
 text('action-title',labels[key]);$('blocked').hidden=key!=='cash';$('results').hidden=key==='cash';
 if(key==='cash'){text('action-note','未計算。賣出 B 不等於全帳現金化。');$('raw').textContent=JSON.stringify(DATA.unavailable,null,2);return;}
 const b=branches[key],m=b.metrics,s=m.statistics,end=b.ledger.daily.at(-1);
 text('action-note',key==='hold'?'維持原持股；原應收權利照原日程交付。':key==='reduce'?'只改明示賣出數量；未即日挪用未交割款。':'賣出 B 後仍有 C；不是全帳持現金。');
 text('period',m.source.start+' → '+m.source.end+' ｜ '+DATA.decision_at.slice(0,10)+' 收盤後選擇行動');
 text('initial',money(m.initial_capital));text('terminal',money(m.terminal_accrual_equity));text('return',pct(s.period_accrual_growth));text('drawdown',pct(s.maximum_drawdown));
 text('recovery',s.recovery_censored?'期末尚未回復・已觀察 '+s.ongoing_underwater_calendar_days+' 日':'已回復');
 text('fees',money(m.costs.recorded_fill_fee_tax));text('cash',money(end.settled_cash));text('reserve','一般預留 '+money(DATA.general_reserve)+'，非可自由動用額');
 const cp=DATA.choice_row,changes=[['已交割現金',money(cp.settled_cash)+' → '+money(end.settled_cash)],...Object.keys(end.shares).filter(c=>Number(cp.shares[c])||Number(end.shares[c])).map(c=>[c+' 持股',cp.shares[c]+' → '+end.shares[c]+' 股'])];
 $('changes').replaceChildren(...changes.map(([a,b])=>{let el=document.createElement('div'),left=document.createElement('span'),right=document.createElement('b');left.textContent=a;right.textContent=b;el.append(left,right);return el;}));
 $('day').max=String(b.ledger.daily.length-1);
 $('raw').textContent=JSON.stringify({comparison_id:DATA.comparison_id,basis_id:DATA.basis_id,decision_at:DATA.decision_at,source_manifest:DATA.source_manifest,qualification:DATA.qualification,branch:b},null,2);daily();
}
document.querySelectorAll('[data-action]').forEach(b=>b.addEventListener('click',()=>select(b.dataset.action)));
$('day').addEventListener('input',daily);
$('download').addEventListener('click',()=>{const blob=new Blob([JSON.stringify(DATA,null,2)+'\n'],{type:'application/json;charset=utf-8'}),url=URL.createObjectURL(blob),a=document.createElement('a');a.href=url;a.download='Twstockai_CAP1_synthetic_results.json';a.click();setTimeout(()=>URL.revokeObjectURL(url),1000);});
select('hold');

window.addEventListener('resize',()=>{if(selected!=='cash')line();});
