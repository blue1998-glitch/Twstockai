import argparse,json
from pathlib import Path
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib import font_manager
from matplotlib.backends.backend_pdf import PdfPages
from matplotlib.patches import Rectangle
from PIL import Image

ROOT=Path(__file__).resolve().parent

def build(font):
    font_manager.fontManager.addfont(str(font))
    plt.rcParams.update({'font.family':font_manager.FontProperties(fname=font).get_name(),'axes.unicode_minus':False,'pdf.fonttype':3,'font.size':11})
    data=json.loads((ROOT/'comparison-data.json').read_text());e=json.loads((ROOT/'evidence.json').read_text())
    output=ROOT/'output/pdf';output.mkdir(parents=True,exist_ok=True)
    dates=[b['date'] for b in data['raw']];x=list(range(len(dates)))
    ticks=[i for i,d in enumerate(dates) if i==0 or d[:7]!=dates[i-1][:7]]
    ev=dates.index('2026-07-01')
    def style(ax):
        ax.set_facecolor('#f8fafc');ax.grid(axis='y',color='#dbe3ee',alpha=.7);ax.set_xlim(-1,len(dates)+1)
        for sp in ['top','right']:ax.spines[sp].set_visible(False)
        ax.set_xticks(ticks,[dates[i][5:7]+'月' for i in ticks])
    pages=[]
    f=plt.figure(figsize=(13.4,8.6),facecolor='white');a=f.add_axes([.085,.29,.84,.50]);style(a)
    vals=[float(r['close']) for r in data['market']]
    a.plot(x,vals,color='#1d4ed8',lw=2.2);a.fill_between(x,vals,min(vals)-900,color='#dbeafe',alpha=.6);a.set_ylim(min(vals)-900,max(vals)+1500)
    peak=max(range(len(vals)),key=lambda i:vals[i]);a.scatter([peak,len(vals)-1],[vals[peak],vals[-1]],color=['#f59e0b','#1d4ed8'],s=55,zorder=3)
    a.annotate('6/22 收盤高點 47,741.51',xy=(peak,vals[peak]),xytext=(peak-37,vals[peak]+900),arrowprops={'arrowstyle':'-','color':'#6b7280'},fontsize=12)
    a.annotate('7/24 收盤 43,654.84',xy=(132,vals[-1]),xytext=(92,vals[-1]-4800),arrowprops={'arrowstyle':'-','color':'#6b7280'},fontsize=12)
    a.set_ylabel('加權指數（收盤線，非 K 線）');f.text(.07,.91,'先看大盤背景，再決定價格口徑',fontsize=23,weight='bold',color='#172554')
    f.text(.07,.85,'2026/1/2 - 7/24  |  133 筆官方收盤資料  |  僅作背景，不新增空頭門檻',fontsize=12,color='#475569')
    f.text(.09,.19,'事實：從視窗高點回落 8.56%；相較視窗起點仍上漲 48.74%。',fontsize=14)
    f.text(.09,.13,'待確認：這段走勢是否屬於你所說的「大盤空頭」？不能只由跌幅替你定義。',fontsize=13,color='#92400e')
    f.text(.07,.055,'來源：TWSE FMTQIK，2026/10/22 擷取。僅使用 7/24 以前資料；指數選擇與市況規則尚未核定。',fontsize=10,color='#64748b');pages.append(('market-context',f))
    for name,bars,title,sub in [
      ('raw-reference','raw','原始日 K：兩個 35.50，日期與來源不同','舊資料完整保留；跨除息比較仍須標記事件。'),
      ('single-event-reference','single_event_candidate','單次除息換算研究：二月參照約為 34.06','只將 7/1 前 OHLC 同乘 33.05 / 34.45；原始股數不換算。')]:
        b=data[bars];f=plt.figure(figsize=(13.4,8.6),facecolor='white');a=f.add_axes([.075,.40,.85,.38]);v=f.add_axes([.075,.235,.85,.12],sharex=a);style(a);style(v)
        for i,k in enumerate(b):
            o,h,l,c=[float(k[z]) for z in ['open','high','low','close']];color='#dc2626' if c>=o else '#16a34a'
            a.vlines(i,l,h,color=color,lw=1);a.add_patch(Rectangle((i-.32,min(o,c)),.64,max(abs(c-o),.013),facecolor=color,edgecolor=color,lw=.5))
            v.bar(i,int(k['volume_shares_scaled'])/1e6,width=.7,color=color,alpha=.65)
        a.set_ylim(28,38.7);a.set_ylabel('價格（元）');v.set_ylabel('百萬股');a.tick_params(labelbottom=False)
        a.axvline(ev,color='#64748b',ls=':',lw=1.2);v.axvline(ev,color='#64748b',ls=':',lw=1.2)
        a.text(ev,28.35,'7/1 除息 1.40',ha='center',color='#475569',fontsize=10)
        for ref,color in zip(e['references'],['#7c3aed','#d97706']):
            idx=dates.index(ref['source_date']);level=float(ref['raw' if bars=='raw' else 'candidate'])
            a.hlines(level,idx,len(dates),color=color,ls='--',lw=1.4)
            a.scatter([idx],[level],color=color,s=35,zorder=5)
            label=f"{ref['source_date'][5:]} 原高 {level:.2f}"
            if idx<80:a.text(idx+2,level+.23,label,color=color,fontsize=11)
            else:a.text(idx-2,level+.50,label,color=color,fontsize=11,ha='right')
        if bars!='raw':
            i=dates.index('2026-07-06');j=dates.index('2026-07-20')
            a.annotate('7/6 收 34.45\n高於換算後二月參照',xy=(i,34.45),xytext=(i-49,36.45),fontsize=11,color='#6d28d9',arrowprops={'arrowstyle':'->','color':'#6d28d9'})
            a.annotate('7/20 收 35.85\n高於七月自身參照',xy=(j,35.85),xytext=(j-26,37.1),fontsize=11,color='#92400e',arrowprops={'arrowstyle':'->','color':'#92400e'})
        f.text(.065,.91,title,fontsize=22,weight='bold',color='#172554');f.text(.065,.85,'2026/1/2 - 7/24  |  同樣 133 根 K、同樣價格軸  |  '+sub,fontsize=11,color='#475569')
        if bars=='raw':
            notes=['7/1 官方事件：前收 34.45，除息參考 33.05；當日收 32.90。','原始收盤差 1.55 元包含 1.40 元除息落差；相對參考價則低 0.15 元。']
        else:
            notes=['二月原高 35.50 → 單次換算約 34.06；七月新高 35.50 保持原值。','這是事後口徑對照，尚非完整還原歷史、正式帶界、成功判定或進場訊號。']
        f.text(.08,.15,notes[0],fontsize=13);f.text(.08,.095,notes[1],fontsize=12,color='#92400e')
        f.text(.065,.04,'來源：既存 2884 原始 OHLCV + 新核 TWSE 7/1 事件列。市場身份未定、未自動選口徑；成交量非硬門檻。',fontsize=10,color='#64748b');pages.append((name,f))
    pdf_temp=output/'b-basis-source-review.tmp.pdf'
    with PdfPages(pdf_temp) as pdf:
        for name,fig in pages:
            temp=ROOT/(name+'.tmp.png')
            fig.savefig(temp,dpi=145,facecolor='white')
            with Image.open(temp) as im: im.verify()
            temp.replace(ROOT/(name+'.png'))
            pdf.savefig(fig);plt.close(fig)
    from pypdf import PdfReader
    assert len(PdfReader(pdf_temp).pages)==3
    pdf_temp.replace(output/'b-basis-source-review.pdf')
    (ROOT/'figure-manifest.json').write_text(json.dumps({'pages':3,'windows':[{'start':dates[0],'end':dates[-1],'records':len(dates)}]*3,'chart_type':['market_close_line','raw_ohlcv','single_cash_event_candidate_ohlcv'],'same_price_axis':[28,38.7],'font':'NotoSansCJKtc-Regular.otf','font_source':'https://github.com/notofonts/noto-cjk','new_product_build':False},ensure_ascii=False,indent=2)+'\n')

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--font',type=Path,required=True);build(p.parse_args().font)
