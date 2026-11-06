"""Render a later user-reviewed, approximately dated region; no automatic rules."""
import argparse
import json
from pathlib import Path
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib import font_manager
from matplotlib.patches import Rectangle


def build(data_path, output_path, font_path):
    d = json.loads(Path(data_path).read_text())
    bars = d['zoom_bars']
    font_manager.fontManager.addfont(font_path)
    plt.rcParams['font.family'] = font_manager.FontProperties(fname=font_path).get_name()
    plt.rcParams['axes.unicode_minus'] = False
    bg, fg, grid = '#101923', '#e6edf4', '#304153'
    fig, (price, vol) = plt.subplots(2, 1, figsize=(12, 9), dpi=140, sharex=True,
                                    gridspec_kw={'height_ratios':[2.1,1], 'hspace':.17})
    fig.set_facecolor(bg)
    fig.subplots_adjust(left=.08,right=.96,top=.82,bottom=.22)
    ix = {b['date']:i for i,b in enumerate(bars)}
    sep_start = next(i for i,b in enumerate(bars) if b['date'].startswith('2023-09'))
    sep_end = max(i for i,b in enumerate(bars) if b['date'].startswith('2023-09'))
    c = ix['2024-01-19']
    for ax in (price,vol):
        ax.set_facecolor(bg)
        ax.tick_params(colors=fg,labelsize=11)
        for spine in ax.spines.values(): spine.set_color(grid)
        ax.grid(axis='y',color=grid,alpha=.6)
        ax.set_axisbelow(True)
        ax.axvspan(sep_start-.5,sep_end+.5,color='#ffd36b',alpha=.055,hatch='///')
        ax.axvspan(sep_end+.5,c+.5,color='#ffd36b',alpha=.11)
        ax.axvspan(c+.5,len(bars)+1,color='#56c8be',alpha=.11)
        ax.axvline(c+.5,color='#86e4da',lw=1,ls='--')
    for i,b in enumerate(bars):
        o,h,l,cl = (float(b[k]) for k in ('open','high','low','close'))
        color = '#ff7179' if cl>o else '#51cbb5' if cl<o else '#d6dde6'
        price.vlines(i,l,h,color=color,lw=.9)
        if cl==o: price.hlines(cl,i-.34,i+.34,color=color,lw=1)
        else: price.add_patch(Rectangle((i-.34,min(o,cl)),.68,abs(cl-o),facecolor=color,edgecolor=color,lw=.3))
        vol.bar(i,int(b['volume_shares_scaled'])/1e6,width=.7,color=color)
    price.axhline(35.5,color='#ffd36b',lw=1.2,ls=(0,(5,4)))
    price.scatter(ix['2023-11-28'],35.5,s=46,color='#ffd36b',zorder=5)
    price.scatter(ix['2023-09-14'],35.5,s=35,facecolors='none',edgecolors=fg,zorder=5)
    price.annotate('G1 11/28・35.50\n整帶的代表點', (ix['2023-11-28'],35.5), xytext=(18,27),
                   textcoords='offset points',color='#ffd36b',fontsize=12,
                   arrowprops={'arrowstyle':'-','color':'#ffd36b'})
    price.annotate('9/14 同高35.50', (ix['2023-09-14'],35.5),xytext=(-8,29),
                   textcoords='offset points',color=fg,fontsize=10,ha='center',
                   arrowprops={'arrowstyle':'-','color':fg})
    price.annotate('C 1/19\n前後交易帶的分界', (c,31.8), xytext=(-35,-40),
                   textcoords='offset points',ha='center',fontsize=11,color='#86e4da',
                   arrowprops={'arrowstyle':'-','color':'#86e4da'})
    price.text((sep_end+c)/2,37.55,'舊價量起伏帶：你指定約9月到C',ha='center',color='#ffd36b',fontsize=12)
    price.text((c+len(bars))/2,36.7,'C右側：新的較平緩帶\n你判讀為籌碼更沉澱',ha='center',color='#86e4da',fontsize=11)
    price.text((sep_start+sep_end)/2,30.15,'約9月\n起日未定',ha='center',color='#dac185',fontsize=10)
    price.set_ylim(29.5,38.4)
    price.set_ylabel('Raw 價格',color=fg,fontsize=12)
    for date,label in [('2023-10-18','10/18'),('2023-11-30','11/30')]:
        i=ix[date]; v=int(bars[i]['volume_shares_scaled'])/1e6
        vol.annotate(f'{label}  {v:.2f}',(i,v),xytext=(0,12),textcoords='offset points',
                     ha='center',color=fg,fontsize=10)
    vol.set_ylim(0,140)
    vol.set_ylabel('成交量\n百萬股',color=fg,fontsize=12)
    vol.set_xlim(-2,len(bars)+2)
    ticks=[]; labels=[]; prev=None
    for i,b in enumerate(bars):
        if b['date'][:7]!=prev: ticks.append(i);labels.append(b['date'][:7])
        prev=b['date'][:7]
    vol.set_xticks(ticks,labels)
    fig.text(.08,.947,'1101 台泥｜代表點＋整段價量帶＋新的沉澱帶',color=fg,fontsize=21,weight='bold')
    fig.text(.08,.9,'依你本次判讀標示；分析截至2026-10-16，屬後來人工覆核',color='#b4c4d5',fontsize=12)
    fig.text(.08,.86,'底色只標時間範圍，沒有宣告價格上下緣或分價成本。',color='#b4c4d5',fontsize=11)
    fig.text(.08,.065,'斜線範圍表示「約2023年9月」，不是固定從9/1開始。\n'
             '右側底色僅畫到本圖末端，不代表新區域在4月底結束。\n'
             '「更沉澱」保存為你的結構判讀；目前未追蹤實際持有人或剩餘套牢股數。\n'
             'Raw公司行動未完整核實；自動分區、代表點選法及增量門檻尚未定量。',
             color='#b4c4d5',fontsize=10,linespacing=1.7)
    fig.savefig(output_path,facecolor=bg)
    plt.close(fig)


if __name__=='__main__':
    p=argparse.ArgumentParser()
    p.add_argument('--data',required=True);p.add_argument('--output',required=True);p.add_argument('--font',required=True)
    a=p.parse_args();build(a.data,a.output,a.font)
