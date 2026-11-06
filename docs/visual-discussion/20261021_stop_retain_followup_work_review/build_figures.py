"""New visual evidence for branch research. Does not modify prior figures."""
from pathlib import Path
import argparse,json,io,hashlib
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle
from matplotlib.font_manager import FontProperties
from matplotlib.backends.backend_pdf import PdfPages
from pypdf import PdfReader
import numpy as np

ap=argparse.ArgumentParser();ap.add_argument('--source',required=True);ap.add_argument('--comparison',required=True);ap.add_argument('--font',required=True);ap.add_argument('--out',default=str(Path(__file__).parent));a=ap.parse_args()
p=Path(a.out);(p/'output/pdf').mkdir(parents=True,exist_ok=True);s=json.loads(Path(a.source).read_text());t=json.loads(Path(a.comparison).read_text())
font=FontProperties(fname=a.font);plt.rcParams.update({'pdf.fonttype':3,'axes.unicode_minus':False,'font.size':10})
def label(fig,x,y,text,size=11):fig.text(x,y,text,fontproperties=font,fontsize=size)
def draw(ax,v,rows):
    for i,b in enumerate(rows):
        o,h,l,c=[float(b[k])for k in ['open','high','low','close']];color='#c44242'if c>=o else'#168268'
        ax.vlines(i,l,h,color=color,lw=.85)
        if o==c:ax.hlines(c,i-.30,i+.30,color=color,lw=.9)
        else:ax.add_patch(Rectangle((i-.3,min(o,c)),.6,abs(c-o),facecolor=color,edgecolor=color,lw=.4))
        v.bar(i,int(b['volume_shares_scaled'])/1e6,width=.65,color=color)
    values=[float(b[k])for b in rows for k in ['low','high']];span=max(values)-min(values);ax.set_ylim(min(values)-span*.12,max(values)+span*.30)
    for z in [ax,v]:z.set_xlim(-1,len(rows));z.grid(axis='y',alpha=.15);z.set_axisbelow(True)
    ax.set_ylabel('原始價格',fontproperties=font);v.set_ylabel('量／百萬股',fontproperties=font);ax.tick_params(labelbottom=False)
    ticks=np.unique(np.linspace(0,len(rows)-1,9,dtype=int));v.set_xticks(ticks,[rows[i]['date'][5:].replace('-','/')for i in ticks],rotation=15,ha='right')
def highlight(ax,v,rows,start,end,color='#9370bb'):
    ix=[i for i,b in enumerate(rows)if start<=b['date']<=end]
    if not ix:return
    lo=min(float(rows[i]['low'])for i in ix);hi=max(float(rows[i]['high'])for i in ix)
    ax.add_patch(Rectangle((ix[0]-.5,lo),len(ix),hi-lo,facecolor=color,edgecolor='none',alpha=.14,zorder=-1))
    v.add_patch(Rectangle((ix[0]-.5,0),len(ix),max(int(rows[i]['volume_shares_scaled'])for i in ix)/1e6,facecolor=color,edgecolor='none',alpha=.14,zorder=-1))
def page(title,subtitle):
    fig=plt.figure(figsize=(17,12));grid=fig.add_gridspec(5,1,height_ratios=[3,1,.4,3,1],left=.07,right=.97,top=.84,bottom=.20,hspace=.23)
    label(fig,.07,.955,title,21);label(fig,.07,.912,subtitle,12);return fig,grid
def axes(fig,grid,k,rows,title):
    r=0 if k==0 else 3;ax=fig.add_subplot(grid[r]);v=fig.add_subplot(grid[r+1],sharex=ax);draw(ax,v,rows);ax.set_title(title,fontproperties=font,fontsize=13,loc='left',pad=10);return ax,v
def idx(rows,date):return next(i for i,b in enumerate(rows)if b['date']==date)
buf=io.BytesIO()
with PdfPages(buf)as pdf:
    fig,grid=page('ABC：首次收盤離開，與後來整根離開分開觀察','凍結首次離開前的觀察價格範圍，才能比較後續；這個範圍不是已核定的正式箱界。')
    broad=[b for b in t['bars']if '2025-01-02'<=b['date']<='2025-06-03'];detail=[b for b in t['bars']if '2025-05-13'<=b['date']<='2025-06-03']
    ax,v=axes(fig,grid,0,broad,'1101｜較廣背景至2025/6/3；紫色沿用已確認4/7至6/2的39筆涵蓋');highlight(ax,v,broad,'2025-04-07','2025-06-02')
    ax,v=axes(fig,grid,1,detail,'末端細節｜6/2仍跨著先前低價，6/3整根位於其下')
    ax.axhline(28.45,color='#72539b',linestyle='--',lw=1)
    ax.text(.025,.42,'首次離開前的觀察低價 28.45（非正式箱底）',transform=ax.transAxes,fontproperties=font,fontsize=11,bbox={'facecolor':'white','edgecolor':'none','alpha':.9})
    j=idx(detail,'2025-06-03');ax.axvline(j-.5,color='#bd7c28',linestyle='--',lw=1)
    ax.annotate('6/2：收27.70、最高29.05',xy=(j-1,29.05),xytext=(j-12,32.0),fontproperties=font,fontsize=11,arrowprops={'arrowstyle':'-','color':'#666'})
    ax.annotate('6/3：最高28.00 < 28.45',xy=(j,28),xytext=(j-7,31.4),fontproperties=font,fontsize=11,arrowprops={'arrowstyle':'-','color':'#bd7c28'})
    label(fig,.07,.144,'新提案分支：原觀察窗留到6/2（39筆）；6/3另列後續候選。同時保留不分段觀察，尚未自動選分支。',12)
    label(fig,.07,.106,'6/2創低仍不直接切斷；5/14的區內跳空也未把較大4/7觀察範圍切掉。',11)
    label(fig,.07,.070,'這是可重現的有限案例提案，並非已驗證通用終點。觀察28.45是原值產生，不是寫死的策略門檻。',10)
    label(fig,.07,.036,'只用圖示截止資料；日OHLC不證日內先後。原資料、核心、轉折與候選箱參數均未改。',10);pdf.savefig(fig);plt.close(fig)

    fig,grid=page('2884：一度收盤離開，不必立刻停止原觀察','9/30收在先前觀察低價下，10/1收回；與截至10/7已可辨認整理的原裁決相容。')
    broad=[b for b in s['bars']if '2026-05-04'<=b['date']<='2026-10-16'];detail=[b for b in s['bars']if '2026-09-17'<=b['date']<='2026-10-16']
    ax,v=axes(fig,grid,0,broad,'上漲與整理背景｜原完整走勢已確認，不重問');highlight(ax,v,broad,'2026-09-17','2026-10-07')
    ax,v=axes(fig,grid,1,detail,'末端事件｜先返回原觀察範圍，後續又出現向上離開證據')
    ax.axhline(44.9,color='#72539b',linestyle='--',lw=.8);ax.axhline(47.35,color='#b27831',linestyle=':',lw=.8)
    j=idx(detail,'2026-10-01');ax.annotate('9/30收44.85；10/1收45.35返回',xy=(j,45.35),xytext=(1,50.5),fontproperties=font,fontsize=11,arrowprops={'arrowstyle':'-','color':'#72539b'})
    j=idx(detail,'2026-10-16');ax.annotate('10/15先收過47.35；10/16整根在上',xy=(j,48),xytext=(9,50.8),fontproperties=font,fontsize=11,arrowprops={'arrowstyle':'-','color':'#b27831'})
    label(fig,.07,.145,'截至10/7：這個研究窗沒有停止提案，9/30離開及10/1返回事件分別保存，沒有用後來結果抹去前事實。',12)
    label(fig,.07,.107,'10/16另產生停止／後續候選分支，並保存10/15的首次收過；不宣稱使用者已核定10/15為區間終點。',11)
    label(fig,.07,.070,'44.90與47.35是各次首次離開前的不同觀察參照；圖窗、形態、來源確認與正式成員資格仍分開。',10)
    label(fig,.07,.036,'本頁使用至10/16的後續資料，僅供演化研究；10/7的研究輸出另存且未使用10/7之後價格。',10);pdf.savefig(fig);plt.close(fig)

    fig,grid=page('G2：局部離開事件，不能直接當較大範圍終點','G2原已確認時間涵蓋2023/1/16至8/16；本頁是人工範圍的壓力測試，不是假稱自動找到G2。')
    broad=[b for b in t['bars']if '2023-01-16'<=b['date']<='2023-08-16'];detail=[b for b in t['bars']if '2023-01-16'<=b['date']<='2023-02-24']
    ax,v=axes(fig,grid,0,broad,'原較大時間範圍｜136筆保存K線；5/2代表日仍位於範圍內')
    j=idx(broad,'2023-02-21');ax.axvline(j,color='#bd7c28',linestyle='--',lw=1)
    j2=idx(broad,'2023-05-02');ax.annotate('原已選代表5/2，最高40.25',xy=(j2,40.25),xytext=(j2-39,41.0),fontproperties=font,fontsize=11,arrowprops={'arrowstyle':'-','color':'#72539b'})
    ax,v=axes(fig,grid,1,detail,'較早事件｜2/21已出現整根離開凍結框架，卻不能據此把G2全部截在2/20')
    j=idx(detail,'2023-02-21');ax.annotate('2/21：低38.15 > 原觀察高37.85',xy=(j,38.15),xytext=(0,40.3),fontproperties=font,fontsize=11,arrowprops={'arrowstyle':'-','color':'#bd7c28'})
    label(fig,.07,.145,'若每次事件都強制選停止分支，會把已確認的較大涵蓋截短。新停止候選與較大延續觀察必須並存。',12)
    label(fig,.07,.107,'本批沒有決定哪些結構層級可以選停止分支，也沒有新增正式合併、承接、解除或生命階段規則。',11)
    label(fig,.07,.070,'原G2時間範圍是已知驗收約束，非本輪新批准。全窗含原待核8/3，Raw公司行動及完整日曆限制保留。',10)
    label(fig,.07,.036,'全部圖為事後截止研究，不代表歷史選取、分類準確率、買賣訊號或Android驗收。',10);pdf.savefig(fig);plt.close(fig)
b=buf.getvalue();assert b.rstrip().endswith(b'%%EOF')and len(PdfReader(io.BytesIO(b)).pages)==3
dest=p/'output/pdf/m1-stop-retain-followup-branches.pdf';dest.write_bytes(b);assert dest.read_bytes()==b
print(json.dumps({'pages':3,'bytes':len(b),'sha256':hashlib.sha256(b).hexdigest()}))
