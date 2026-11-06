"""New real-price overview and return detail. Does not run prior builders."""
import hashlib,json
from pathlib import Path
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle
from matplotlib.font_manager import FontProperties
from study import ROOT,SOURCE
font=FontProperties(fname='/workspace/scratch/54685b8dac93/version-continuity-review/research-font.otf')
source=json.loads(SOURCE.read_text());data=json.loads((ROOT/'return-paths.json').read_text())
f=plt.figure(figsize=(18,13),facecolor='white')
def label(x,y,s,size=12):f.text(x,y,s,fontproperties=font,fontsize=size,color='#243449')
label(.065,.96,'回到同一價位：影線到達、收盤收回、再次反向分開保留',23)
label(.065,.92,'1101／2023年 保存 Raw 日K；兩條重疊的事後指定路徑，不是獨立市場樣本，也不是正式支撐／壓力判準。')
g=f.add_gridspec(5,1,height_ratios=[3,1,.65,3,1],left=.065,right=.965,top=.84,bottom=.23,hspace=.27)
def draw(row,start,end,title):
    bs=[b for b in source['bars']if start<=b['date']<=end]
    ax=f.add_subplot(g[row]);v=f.add_subplot(g[row+1],sharex=ax)
    for i,b in enumerate(bs):
        o,h,l,c=map(lambda k:float(b[k]),['open','high','low','close']);color='#c44242' if c>=o else '#168268'
        ax.vlines(i,l,h,color=color,lw=.8)
        ax.add_patch(Rectangle((i-.29,min(o,c)),.58,max(abs(c-o),.008),facecolor=color))
        v.bar(i,int(b['volume_shares_scaled'])/1e6,color=color,width=.65)
    for p,known,color in [('36.15','2023-03-23','#54789b'),('37.15','2023-05-30','#9b7655')]:
        ids=[i for i,b in enumerate(bs)if b['date']>=known]
        if ids:ax.hlines(float(p),ids[0]-.4,len(bs)-.4,color=color,ls='--',lw=1)
    lo=min(float(b['low'])for b in bs);hi=max(float(b['high'])for b in bs);span=hi-lo
    ax.set_ylim(lo-.15*span,hi+.48*span)
    for a in [ax,v]:a.set_xlim(-1,len(bs));a.grid(axis='y',alpha=.15);a.set_axisbelow(True)
    ticks=sorted({round(i*(len(bs)-1)/7)for i in range(8)})
    v.set_xticks(ticks,[bs[i]['date'][5:].replace('-','/')for i in ticks]);ax.tick_params(labelbottom=False)
    ax.set_ylabel('保存原始價格',fontproperties=font);v.set_ylabel('量／百萬股',fontproperties=font)
    ax.set_title(title,fontproperties=font,fontsize=12,loc='left',pad=9)
    return ax,bs
def note(ax,bs,day,caption,pos,field='close'):
    i=next(i for i,b in enumerate(bs)if b['date']==day)
    ax.annotate(caption,xy=(i,float(bs[i][field])),xytext=pos,textcoords='axes fraction',fontproperties=font,fontsize=11,arrowprops={'arrowstyle':'-','color':'#72539b'})
ax,bs=draw(0,'2023-01-16','2023-08-02','廣角：已答大G2的一部分；止於8/2，不跨接已列缺日8/3，完整人工範圍仍至8/16共136筆')
note(ax,bs,'2023-04-11','4/11 C37.45：先前向上事實保留',(.08,.91))
note(ax,bs,'2023-05-02','5/2 H40.25代表保持',(.40,.91),'high')
note(ax,bs,'2023-07-21','7/21 C36.10：後來已收在36.15下',(.63,.73))
ax,bs=draw(3,'2023-07-07','2023-08-02','近看：原參照37.15（棕線）與36.15（藍線）是不同參照，不合成一條新價帶')
note(ax,bs,'2023-07-10','7/10 C36.85：先前向下事實保留',(.02,.91))
note(ax,bs,'2023-07-13','7/13 H37.25但C36.80：到達，未收回37.15',(.24,.73))
note(ax,bs,'2023-07-25','7/25 C37.40：才收回37.15上',(.61,.91))
label(.065,.173,'事實：4/11上移之後，7/21首次收在原36.15下；7/10下移之後，7/13先到達，7/25才收回原37.15上。')
label(.065,.132,'判讀：後來返回會改變目前位置與觀察問題，不能抹掉先前上移／下移；影線到達不能提前叫收盤收復。')
label(.065,.091,'界線：兩原參照、原代表與大G2分開保存；一次正負反應不直接定大結構成立／終止，不推因果、量資格或交易資格。')
label(.065,.050,'原來源日曆、公司行動、歷史公開可得限制仍在；分類器與新版Android未驗證。本輪只研究可回查時序。',11)
p=ROOT/'real-return-paths.png';f.savefig(p,dpi=110);plt.close(f)
(ROOT/'figure-build.json').write_text(json.dumps({'builder_runs':(json.loads((ROOT/'figure-build.json').read_text()).get('builder_runs',0)+1 if (ROOT/'figure-build.json').exists() else 1),'pages':1,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()},indent=2)+'\n')
print(p)
