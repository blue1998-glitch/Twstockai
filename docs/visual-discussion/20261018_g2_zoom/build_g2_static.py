import argparse,json
from pathlib import Path
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib import font_manager
from matplotlib.patches import Rectangle

def build(source,output,font):
    d=json.loads(Path(source).read_text())
    b=[x for x in d['bars'] if d['default_view']['start']<=x['date']<=d['default_view']['end']]
    font_manager.fontManager.addfont(font)
    plt.rcParams['font.family']=font_manager.FontProperties(fname=font).get_name()
    plt.rcParams['axes.unicode_minus']=False
    bg,fg,grid='#101923','#e6edf4','#304153'
    f,(p,v)=plt.subplots(2,1,figsize=(14,8),dpi=160,sharex=True,gridspec_kw={'height_ratios':[2.5,1],'hspace':.12})
    f.patch.set_facecolor(bg);f.subplots_adjust(left=.07,right=.98,top=.84,bottom=.17)
    for ax in (p,v):
        ax.set_facecolor(bg);ax.tick_params(colors=fg,labelsize=11);ax.grid(axis='y',color=grid,alpha=.6);ax.set_axisbelow(True)
        for spine in ax.spines.values():spine.set_color(grid)
    for i,x in enumerate(b):
        o,h,l,c=(float(x[k]) for k in ['open','high','low','close'])
        col='#ff7179' if c>o else '#51cbb5' if c<o else '#d6dde6'
        p.vlines(i,l,h,color=col,lw=.9)
        if c==o:p.hlines(c,i-.34,i+.34,color=col,lw=1)
        else:p.add_patch(Rectangle((i-.34,min(o,c)),.68,abs(c-o),facecolor=col,edgecolor=col,lw=.3))
        v.bar(i,int(x['volume_shares_scaled'])/1e6,color=col,width=.7)
    g=next(i for i,x in enumerate(b) if x['date']=='2023-05-02')
    p.axhline(40.25,color='#ffd36b',ls=(0,(5,4)),lw=1)
    p.scatter(g,40.25,s=40,color='#ffd36b',zorder=5)
    p.annotate('G2  2023-05-02\n40.25',(g,40.25),xytext=(18,20),textcoords='offset points',color='#ffd36b',fontsize=12,arrowprops={'arrowstyle':'-','color':'#ffd36b'})
    lo=min(float(x['low']) for x in b);hi=max(float(x['high']) for x in b);span=hi-lo
    p.set_ylim(lo-span*.06,hi+span*.2);p.set_xlim(-2,len(b)+2)
    ticks=[];labels=[];last=None
    for i,x in enumerate(b):
        if x['date'][:7]!=last:ticks.append(i);labels.append(x['date'][:7])
        last=x['date'][:7]
    v.set_xticks(ticks,labels);p.set_ylabel('Raw價格',color=fg);v.set_ylabel('量（百萬股）',color=fg)
    f.text(.07,.94,'1101 台泥｜G2附近真實K線與成交量',fontsize=23,color=fg)
    f.text(.07,.89,'原尺寸靜態參考圖；G2的區域範圍尚未選定',fontsize=13,color=fg)
    f.text(.07,.075,'分析截至2026-10-16；後來人工選點，不是當時自動訊號。\nRaw公司行動未完整核實；圖示月份只是閱讀視窗，不是壓力區界。',fontsize=11,color='#b4c4d5',linespacing=1.6)
    f.savefig(output,facecolor=bg);plt.close(f)

if __name__=='__main__':
    a=argparse.ArgumentParser();a.add_argument('--source',required=True);a.add_argument('--output',required=True);a.add_argument('--font',required=True);s=a.parse_args();build(s.source,s.output,s.font)
