"""Static visual QA from stored engine outputs; not a browser screenshot."""
import json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parent
sys.path.insert(0,str(ROOT/'src'))
from structure import project_prices
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle

code='6488';mode='ADJUSTED_CANDIDATE'
candles=json.loads((ROOT/'data'/f'{code}_candles.json').read_text())
events=json.loads((ROOT/'data'/f'{code}_events.json').read_text())
snapshot=json.loads((ROOT/'output'/f'{code}_{mode}_MA.json').read_text())['snapshots'][-1]
rows=project_prices(candles,events,snapshot['as_of'],mode);start=len(rows)-100
fig,(ax,av)=plt.subplots(2,1,figsize=(14,8),sharex=True,layout='constrained',gridspec_kw={'height_ratios':[4,1]})
for i in range(start,len(rows)):
    c=rows[i];o,h,l,close=[float(c[k]) for k in ['open','high','low','close']]
    color='#d9404d' if close>o else '#139870' if close<o else '#697c94'
    ax.vlines(i,l,h,color=color,linewidth=1)
    ax.add_patch(Rectangle((i-.3,min(o,close)),.6,max(.3,abs(close-o)),facecolor=color,edgecolor=color))
    av.bar(i,float(c['volume_shares_scaled'])/1e6,color=color,width=.6)
colors={5:'#af7310',20:'#8052bd',60:'#2672bd',130:'#d64b77',260:'#158887'}
for p,color in colors.items():
    values=snapshot['curves'][str(p)]
    x=[i for i in range(start,len(rows)) if values[i] is not None]
    ax.plot(x,[float(values[i]) for i in x],label=f'MA{p}',color=color,linewidth=1.5)
ax.set_title('6488 | Real daily candles + independent SMA core | as of '+snapshot['as_of'],loc='left',pad=16)
ax.set_ylabel('TWD | cash-dividend adjustment candidate');av.set_ylabel('Volume\n(million shares)')
ax.legend(ncol=5,loc='upper left');ax.grid(alpha=.15);av.grid(axis='y',alpha=.15)
ticks=list(range(start,len(rows),15));av.set_xticks(ticks,[rows[i]['date'][5:] for i in ticks])
fig.supxlabel('Red: close > open; green: close < open. MA260 starts after 260 supplied records.\nStatic numeric-output plot; browser/touch QA and classification quality remain unverified.',fontsize=10)
fig.savefig(ROOT/'output/6488_日均線核心預覽.png',dpi=140)
plt.close(fig)
