"""New exact-price research figures; all older PDF/PNG artifacts remain unchanged."""
from pathlib import Path
import argparse,io,json,hashlib,os
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle
from matplotlib.font_manager import FontProperties
from matplotlib.backends.backend_pdf import PdfPages
from pypdf import PdfReader
import numpy as np

ap=argparse.ArgumentParser();ap.add_argument('--comparison',required=True);ap.add_argument('--font',required=True);ap.add_argument('--out',default=str(Path(__file__).parent));a=ap.parse_args()
p=Path(a.out);(p/'output/pdf').mkdir(parents=True,exist_ok=True);src=json.loads(Path(a.comparison).read_text());font=FontProperties(fname=a.font)
plt.rcParams.update({'pdf.fonttype':3,'axes.unicode_minus':False,'font.size':10})
def text(fig,x,y,s,size=11):fig.text(x,y,s,fontproperties=font,fontsize=size)
def page(title,subtitle):
 f=plt.figure(figsize=(17,12));g=f.add_gridspec(5,1,height_ratios=[3,1,.45,3,1],left=.07,right=.97,top=.84,bottom=.23,hspace=.24)
 text(f,.07,.95,title,21);text(f,.07,.91,subtitle,12);return f,g
def draw(fig,g,k,start,end,title):
 rows=[b for b in src['bars']if start<=b['date']<=end];j=0 if k==0 else 3;ax=fig.add_subplot(g[j]);v=fig.add_subplot(g[j+1],sharex=ax)
 for i,b in enumerate(rows):
  o,h,l,c=[float(b[x])for x in ['open','high','low','close']];color='#c44242'if c>=o else'#168268';ax.vlines(i,l,h,color=color,lw=.9)
  if c==o:ax.hlines(c,i-.3,i+.3,color=color,lw=1)
  else:ax.add_patch(Rectangle((i-.3,min(o,c)),.6,abs(c-o),facecolor=color,edgecolor=color,lw=.4))
  v.bar(i,int(b['volume_shares_scaled'])/1e6,width=.65,color=color)
 values=[float(b[x])for b in rows for x in ['high','low']];span=max(values)-min(values);ax.set_ylim(min(values)-span*.12,max(values)+span*.32)
 for z in [ax,v]:z.set_xlim(-1,len(rows));z.grid(axis='y',alpha=.15);z.set_axisbelow(True)
 ax.set_title(title,fontproperties=font,fontsize=13,loc='left',pad=10);ax.set_ylabel('原始價格',fontproperties=font);v.set_ylabel('量／百萬股',fontproperties=font);ax.tick_params(labelbottom=False)
 ticks=np.unique(np.linspace(0,len(rows)-1,8,dtype=int));v.set_xticks(ticks,[rows[i]['date'][5:].replace('-','/')for i in ticks],rotation=15,ha='right');return ax,v,rows
def pos(rows,day):return next(i for i,b in enumerate(rows)if b['date']==day)
def arrow(ax,rows,day,price,label,xytext):ax.annotate(label,xy=(pos(rows,day),price),xytext=xytext,fontproperties=font,fontsize=11,arrowprops={'arrowstyle':'-','color':'#72539b'})
buf=io.BytesIO()
with PdfPages(buf)as pdf:
 f,g=page('ABC：離開之後，持續觀察新的價格活動','截至6/13的後續研究：九筆日K都在舊參照28.45下方，不能把這些後來資料提前用在6/3。')
 ax,v,rows=draw(f,g,0,'2025-01-02','2025-06-13','1101較廣背景｜紫色為原已確認4/7至6/2；後續資料另著色')
 start,end=pos(rows,'2025-04-07'),pos(rows,'2025-06-02');ax.axvspan(start-.5,end+.5,color='#9370bb',alpha=.13,zorder=-2);v.axvspan(start-.5,end+.5,color='#9370bb',alpha=.13,zorder=-2)
 ax.axvspan(end+.5,len(rows)-.5,color='#c59248',alpha=.13,zorder=-2);v.axvspan(end+.5,len(rows)-.5,color='#c59248',alpha=.13,zorder=-2)
 ax,v,rows=draw(f,g,1,'2025-05-13','2025-06-13','後續細節｜新種子6/3只有一筆；6/11才取得完成收盤的高低雙向往返證據')
 ax.axhline(28.45,color='#72539b',ls='--',lw=1);ax.text(.015,.38,'舊凍結參照28.45，非正式箱底',transform=ax.transAxes,fontproperties=font,fontsize=11,bbox={'facecolor':'white','edgecolor':'none','alpha':.9})
 arrow(ax,rows,'2025-06-03',28,'6/3：新觀察種子',(8,32.0));arrow(ax,rows,'2025-06-06',27.55,'6/6收盤高點，6/9才可知',(13,31.3));arrow(ax,rows,'2025-06-10',27.15,'6/10收盤低點，6/11才可知',(16,30.6))
 text(f,.07,.174,'已知：截至6/13，後續九筆都整根在28.45下方，沒有返回該舊觀察框；僅限此截止，並非永不返回。',12)
 text(f,.07,.136,'分析：新價位區已有自己的往返路徑，可持續研究後續範圍；高低往返本身還不足以正式認定整理。',11)
 text(f,.07,.098,'同日24個停止提案，只共用28.45與28.70兩個跨越價位；保留各自來源，不當24票，也不合併成同一結構。',11)
 text(f,.07,.060,'原ABC39筆與6/3在外裁決保持。新研究不重算原核心指標、不改參數、不提出買賣資格。',10)
 text(f,.95,.025,'1 / 2',10);pdf.savefig(f);plt.close(f)
 f,g=page('G2：整根離開之後，仍可能返回原先價格範圍','保留2/21當時的離開事實，同時新增後來的接觸與收盤返回；不回寫歷史，也不自動合併結構。')
 ax,v,rows=draw(f,g,0,'2023-01-16','2023-03-16','G2較廣早期背景｜完整1/16至8/16及5/2代表仍沿用前批已確認圖冊')
 ax.axhline(37.85,color='#72539b',ls='--',lw=1);ax.axvline(pos(rows,'2023-02-21')-.5,color='#c59248',ls=':',lw=1)
 ax,v,rows=draw(f,g,1,'2023-02-14','2023-03-03','逐時點｜2/22只是碰到37.85，3/1收37.80才回到原凍結範圍內')
 ax.axhline(37.85,color='#72539b',ls='--',lw=1)
 arrow(ax,rows,'2023-02-21',38.15,'2/21整根在上',(0,40.25));arrow(ax,rows,'2023-02-22',37.85,'2/22低37.85相等接觸，收38.05仍在上',(1.5,39.92));arrow(ax,rows,'2023-03-01',37.80,'3/1收37.80返回',(7.6,40.25))
 text(f,.07,.174,'已知：2/21新種子僅一筆；2/24已見收盤高低往返，3/1才有收盤返回舊框。每個時點分別保存。',12)
 text(f,.07,.136,'分析：相同的整根離開，也可能是較大範圍內的局部過程；返回可新增延續／回測研究證據，不能自動否定舊事件。',11)
 text(f,.07,.098,'限制：有往返不等於已形成新區間，返回不等於正式合併。G2人工時間涵蓋只作外部驗收，非本輪自動找到。',11)
 text(f,.07,.060,'圖上方較廣背景用至3/16；逐時點證據只至各自截止。完整G2跨原待核8/3，來源限制保持。',10)
 text(f,.95,.025,'2 / 2',10);pdf.savefig(f);plt.close(f)
b=buf.getvalue();assert b.rstrip().endswith(b'%%EOF')and len(PdfReader(io.BytesIO(b)).pages)==2;dest=p/'output/pdf/m1-persistent-followup-evidence.pdf'
with dest.open('wb')as out:out.write(b);out.flush();os.fsync(out.fileno())
assert dest.read_bytes()==b;print(json.dumps({'pages':2,'bytes':len(b),'sha256':hashlib.sha256(b).hexdigest()}))
