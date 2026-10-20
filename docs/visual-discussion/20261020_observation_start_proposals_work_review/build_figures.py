"""Render experimental seed proposals; no engine or indicator calculation."""
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
p=Path(a.out);(p/'output/pdf').mkdir(parents=True,exist_ok=True)
s=json.loads(Path(a.source).read_text());t=json.loads(Path(a.comparison).read_text());r=json.loads((p/'proposals.json').read_text())
font=FontProperties(fname=a.font);plt.rcParams.update({'pdf.fonttype':3,'axes.unicode_minus':False,'font.size':10})
def label(fig,x,y,text,size=11):fig.text(x,y,text,fontproperties=font,fontsize=size)
def bars(ax,v,rows):
    for i,b in enumerate(rows):
        o,h,l,c=[float(b[k])for k in ['open','high','low','close']];color='#c44242'if c>=o else'#168268'
        ax.vlines(i,l,h,color=color,lw=.9)
        if o==c:ax.hlines(c,i-.3,i+.3,color=color,lw=.9)
        else:ax.add_patch(Rectangle((i-.3,min(o,c)),.6,abs(c-o),facecolor=color,edgecolor=color,lw=.4))
        v.bar(i,int(b['volume_shares_scaled'])/1e6,width=.65,color=color)
    vals=[float(b[k])for b in rows for k in ['high','low']];span=max(vals)-min(vals);ax.set_ylim(min(vals)-span*.12,max(vals)+span*.22)
    for z in [ax,v]:z.set_xlim(-1,len(rows));z.grid(axis='y',alpha=.15);z.set_axisbelow(True)
    ax.set_ylabel('原始價格',fontproperties=font);v.set_ylabel('量／百萬股',fontproperties=font);ax.tick_params(labelbottom=False)
    ticks=np.unique(np.linspace(0,len(rows)-1,9,dtype=int));v.set_xticks(ticks,[rows[i]['date'][5:].replace('-','/')for i in ticks],rotation=15,ha='right')
def shade(ax,v,rows,start,end,color,alpha=.15):
    ids=[i for i,b in enumerate(rows)if start<=b['date']<=end]
    if not ids:return
    low=min(float(rows[i]['low'])for i in ids);high=max(float(rows[i]['high'])for i in ids)
    ax.add_patch(Rectangle((ids[0]-.5,low),len(ids),high-low,facecolor=color,edgecolor='none',alpha=alpha,zorder=-1))
    v.add_patch(Rectangle((ids[0]-.5,0),len(ids),max(int(rows[i]['volume_shares_scaled'])for i in ids)/1e6,facecolor=color,edgecolor='none',alpha=alpha,zorder=-1))
buf=io.BytesIO()
with PdfPages(buf)as pdf:
    x=r['2884-Oct7'];rows=[b for b in s['bars']if '2026-05-04'<=b['date']<=x['data_cutoff']];lookup={b['date']:i for i,b in enumerate(rows)}
    fig=plt.figure(figsize=(17,12));gs=fig.add_gridspec(3,1,height_ratios=[4,1.2,1.2],left=.07,right=.97,top=.84,bottom=.25,hspace=.32)
    label(fig,.07,.955,'先自動提出觀察起點，再判斷區間形態',22)
    label(fig,.07,.913,'2884｜只用截至 2026/10/7 的資料；9/17 自行出現在候選池，未輸入目標起日或 13 筆長度。',13)
    label(fig,.07,.877,'最新資料可用段共223筆；圖示5/4至10/7背景。紫色是9/17候選觀察窗，橘色是末3筆共同價位短窗。',11)
    ax=fig.add_subplot(gs[0]);v=fig.add_subplot(gs[1],sharex=ax);dots=fig.add_subplot(gs[2],sharex=ax);bars(ax,v,rows)
    shade(ax,v,rows,'2026-09-17',x['data_cutoff'],'#9370bb');shade(ax,v,rows,x['common_price_suffix']['start_date'],x['data_cutoff'],'#f2ae48',.30)
    for y,(method,col,lab)in enumerate([('backward_envelope','#7550a0','價格範圍向外推開'),('close_turn_baseline','#416b97','收盤方向轉折')]):
        ids=[lookup[z['start_date']]for z in x[method]['candidates']if z['start_date']in lookup];dots.scatter(ids,[y]*len(ids),s=17,color=col,label=lab)
    dots.scatter([lookup[x['common_price_suffix']['start_date']]],[2],s=45,color='#ca8722')
    dots.set_yticks([0,1,2],['範圍候選','收盤候選','共同價位短窗'],fontproperties=font);dots.set_ylim(-.5,2.5);dots.grid(axis='x',alpha=.12)
    ticks=np.unique(np.linspace(0,len(rows)-1,9,dtype=int));dots.set_xticks(ticks,[rows[i]['date'][5:].replace('-','/')for i in ticks],rotation=15,ha='right')
    j=lookup['2026-09-17'];ax.annotate('候選之一：9/17',xy=(j,47.35),xytext=(j-21,49),fontproperties=font,fontsize=12,arrowprops={'arrowstyle':'-','color':'#7550a0'})
    label(fig,.07,.185,'同一份截止資料：價格範圍方法提出66個起點；收盤轉折提出111個；共同價位法只留下10/5至10/7。',12)
    label(fig,.07,.148,'候選池保留多種較長與較短可能，不選唯一贏家。9/17只是候選之一，不等於正式整理起點已自動認證。',11)
    label(fig,.07,.111,'「範圍向外推開」：舊K的高／低超出它右側截至當下的價格外包，保留該K與下一筆作觀察起點。',11)
    label(fig,.07,.074,'圖上小點只是新研究的起點種子，並非原轉折、已成立區間或買賣訊號；原來源／核心／參數均保留。',10)
    label(fig,.07,.037,'資料已列缺日之前的歷史仍保留為背景；本批候選的保守可用段不代表市場結構真正從該日開始。',10)
    pdf.savefig(fig);plt.close(fig)

    fig=plt.figure(figsize=(17,12));gs=fig.add_gridspec(5,1,height_ratios=[3,1,.35,3,1],left=.07,right=.97,top=.84,bottom=.20,hspace=.22)
    label(fig,.07,.955,'找得到起點，仍不能自動決定區間終點',22)
    label(fig,.07,.913,'1101 ABC｜4/7 自行出現在候選池；但6/3到來後，「觀察到哪一天」不能直接變成正式成員。',13)
    for k,(key,begin,title)in enumerate([
      ('1101-ABC-Jun2','2025-01-02','截至6/2｜已確認39筆涵蓋；4/7為自動候選之一'),
      ('1101-ABC-Jun3','2025-05-13','加入6/3｜舊39筆保留；新40筆只是另一個觀察提案')]):
        rr=r[key];rows=[b for b in t['bars']if begin<=b['date']<=rr['data_cutoff']];row=0 if k==0 else 3
        ax=fig.add_subplot(gs[row]);v=fig.add_subplot(gs[row+1],sharex=ax);bars(ax,v,rows);shade(ax,v,rows,'2025-04-07','2025-06-02','#9370bb')
        ax.set_title(title,fontproperties=font,fontsize=13,loc='left',pad=10)
        if k==0:
            j=next(i for i,b in enumerate(rows)if b['date']=='2025-04-07');ax.annotate('4/7 候選起點',xy=(j,29.2),xytext=(j+5,34),fontproperties=font,fontsize=12,arrowprops={'arrowstyle':'-','color':'#7550a0'})
            label(fig,.07,.873,'4/2原日低32.25，高於4/7至6/2整個後段最高31.40；因此方法保留4/7作後段起點候選。',11)
        else:
            j=len(rows)-1;ax.axvline(j-.5,color='#b56329',linestyle='--',lw=1)
            ax.annotate('6/3 已確認在前箱外',xy=(j,float(rows[-1]['low'])),xytext=(j-8,max(float(b['high'])for b in rows)+.5),fontproperties=font,fontsize=12,arrowprops={'arrowstyle':'-','color':'#b56329'})
    label(fig,.07,.143,'4/7候選在5/14的區內跳空之後仍保留，沒有因每次跳空都刪掉較大觀察範圍。',12)
    label(fig,.07,.108,'但截至6/3的觀察提案仍會包含6/3，與正式ABC成員要求不同；此終點問題已展示，尚未解決。',12)
    label(fig,.07,.073,'紫色只沿用使用者已確認的39筆涵蓋，不是新自動分箱輸出。6/2與6/3提案分別保存，不覆寫舊紀錄。',10)
    label(fig,.07,.038,'本批為事後重建的截止資料研究；非歷史實際選取、分類準確率、正式區界或Android驗收。',10)
    pdf.savefig(fig);plt.close(fig)
b=buf.getvalue();assert b.rstrip().endswith(b'%%EOF')and len(PdfReader(io.BytesIO(b)).pages)==2
path=p/'output/pdf/m1-observation-start-proposals.pdf';path.write_bytes(b);assert path.read_bytes()==b
print(json.dumps({'PDF_pages':2,'bytes':len(b),'sha256':hashlib.sha256(b).hexdigest()}))
