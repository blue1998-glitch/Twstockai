"""Exact-source illustrative witnesses; figure choices never feed discovery."""
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

ap=argparse.ArgumentParser();ap.add_argument('--source',required=True);ap.add_argument('--comparison',required=True);ap.add_argument('--font',required=True);ap.add_argument('--out',default=str(Path(__file__).parent));a=ap.parse_args()
p=Path(a.out);(p/'output/pdf').mkdir(parents=True,exist_ok=True);s=json.loads(Path(a.source).read_text());t=json.loads(Path(a.comparison).read_text());selected=json.loads((p/'selected-revisits.json').read_text());font=FontProperties(fname=a.font)
plt.rcParams.update({'pdf.fonttype':3,'axes.unicode_minus':False,'font.size':10})
def text(f,x,y,label,size=11):f.text(x,y,label,fontproperties=font,fontsize=size)
def page(title,subtitle):
 f=plt.figure(figsize=(17,12));g=f.add_gridspec(5,1,height_ratios=[3,1,.4,3,1],left=.07,right=.97,top=.84,bottom=.23,hspace=.24);text(f,.07,.95,title,21);text(f,.07,.91,subtitle,12);return f,g
def draw(f,g,k,src,start,end,title):
 rows=[b for b in src['bars']if start<=b['date']<=end];j=0 if k==0 else 3;ax=f.add_subplot(g[j]);v=f.add_subplot(g[j+1],sharex=ax)
 for i,b in enumerate(rows):
  o,h,l,c=[float(b[x])for x in ['open','high','low','close']];color='#c44242'if c>=o else'#168268';ax.vlines(i,l,h,color=color,lw=.9)
  if c==o:ax.hlines(c,i-.3,i+.3,color=color,lw=1)
  else:ax.add_patch(Rectangle((i-.3,min(o,c)),.6,abs(c-o),facecolor=color,edgecolor=color,lw=.4))
  v.bar(i,int(b['volume_shares_scaled'])/1e6,color=color,width=.65)
 vals=[float(b[x])for b in rows for x in ['low','high']];span=max(vals)-min(vals);ax.set_ylim(min(vals)-span*.14,max(vals)+span*.36)
 for z in [ax,v]:z.set_xlim(-1,len(rows));z.grid(axis='y',alpha=.15);z.set_axisbelow(True)
 ax.set_title(title,fontproperties=font,fontsize=13,loc='left',pad=10);ax.set_ylabel('原始價格',fontproperties=font);v.set_ylabel('量／百萬股',fontproperties=font);ax.tick_params(labelbottom=False)
 ticks=np.unique(np.linspace(0,len(rows)-1,9,dtype=int));v.set_xticks(ticks,[rows[i]['date'][5:].replace('-','/')for i in ticks],rotation=15,ha='right');return ax,v,rows
def index(rows,day):return next(i for i,b in enumerate(rows)if b['date']==day)
def shade(ax,v,rows,start,end,color='#9370bb'):
 ix=[i for i,b in enumerate(rows)if start<=b['date']<=end]
 if not ix:return
 lo=min(float(rows[i]['low'])for i in ix);hi=max(float(rows[i]['high'])for i in ix)
 ax.add_patch(Rectangle((ix[0]-.5,lo),len(ix),hi-lo,facecolor=color,edgecolor='none',alpha=.18,zorder=-2))
 v.add_patch(Rectangle((ix[0]-.5,0),len(ix),max(int(rows[i]['volume_shares_scaled'])for i in ix)/1e6,facecolor=color,edgecolor='none',alpha=.18,zorder=-2))
def arrow(ax,rows,day,price,label,position):ax.annotate(label,xy=(index(rows,day),price),xytext=position,textcoords='axes fraction',fontproperties=font,fontsize=11,arrowprops={'arrowstyle':'-','color':'#72539b'})
def witness(name,price,day):
 r=selected[name];e=next(e for e in r['episodes']if e['anchor_price']==price and e['known_on_saved_bar']==day);return e,r['frames'][e['frame_id']]
def notes(f,lines,number):
 for y,line in zip([.174,.136,.098,.060],lines):text(f,.07,y,line,12 if y==.174 else 11 if y>.06 else 10)
 text(f,.95,.025,f'{number} / 3',10)
buf=io.BytesIO()
with PdfPages(buf)as pdf:
 e,fr=witness('2884-Oct7','45.1','2026-10-01')
 f,g=page('2884：自動提出價格重訪片段，與當前位置分開','參照45.10來自9/24原日低；只追蹤它已出現之後的收盤，不先畫好一個目標區間。')
 ax,v,rows=draw(f,g,0,s,'2026-05-04','2026-10-07','較廣上漲背景至10/7｜使用者已確認本例整理，不重問最早日／正式起點')
 shade(ax,v,rows,'2026-09-17','2026-10-07')
 ax,v,rows=draw(f,g,1,s,'2026-09-17','2026-10-07','紫色只標返回前9/24至9/30的原K價格範圍44.75至45.95；不是正式箱界')
 shade(ax,v,rows,fr['observed_start'],fr['observed_end']);ax.hlines(45.1,index(rows,'2026-09-24'),len(rows)-.5,color='#72539b',ls='--',lw=1)
 arrow(ax,rows,'2026-09-24',45.60,'9/24收45.60，在45.10上',(.015,.90))
 arrow(ax,rows,'2026-09-29',44.90,'9/29收44.90，到另一側',(.32,.76))
 arrow(ax,rows,'2026-10-01',45.35,'10/1收45.35返回；低44.20仍可創低',(.52,.90))
 notes(f,['已知：這個往返到10/1才完成；10/7收45.75仍在當時已知範圍44.75至45.95內。',
 '10/1最低44.20在舊範圍下，收盤卻回到範圍內；影線與收盤分開，不以創低一項否定往返。',
 '研究能自行提出局部觀察片段；圖示選一個可讀例，不排名、不當正式起末或整理充分條件。',
 '同源原值不改。10/1只是本片段證據完成日，不是新宣稱本例最早可辨認日；10/7已答保持。'],1);pdf.savefig(f);plt.close(f)

 e,fr=witness('2884-control-May4','32.8','2026-04-20')
 f,g=page('方向對照：以前有往返，後來價格已離開','不能用「目前在外」推論從未有過局部區間活動，也不能用「以前有往返」忽略當前走低。')
 ax,v,rows=draw(f,g,0,s,'2026-01-02','2026-05-04','同股較廣背景｜4/15至5/4是前批選出的方向對照，尚無人工區間負標籤')
 shade(ax,v,rows,'2026-04-15','2026-05-04')
 ax,v,rows=draw(f,g,1,s,'2026-04-15','2026-05-04','紫色為自動重訪的返回前4/16至4/17：32.50至33.20；參照32.80來自4/16低')
 shade(ax,v,rows,fr['observed_start'],fr['observed_end']);ax.hlines(32.8,index(rows,'2026-04-16'),len(rows)-.5,color='#72539b',ls='--',lw=1)
 arrow(ax,rows,'2026-04-20',32.85,'4/16在上、4/17在下；4/20收回上側',(.015,.91))
 arrow(ax,rows,'2026-05-04',31.30,'5/4收31.30，已在舊範圍下方',(.54,.78))
 notes(f,['已知：這段曾出現真正的同價位往返；截至5/4，四個收盤回入型重訪框的收盤關係都在下方。',
 '和10月例不同的是當前位置與後續方向；不是穿越次數多就較有整理資格，也不是此例從未有區間。',
 '自動紀錄往返事實，再分開更新當前關係；舊事實保留，不強制選正式停止、延續或合併。',
 '對照為事後選取，並非盲測／獨立樣本／全尺度負例；不比較不同日期的投資效益。'],2);pdf.savefig(f);plt.close(f)

 e,fr=witness('ABC-followup-Jun13','27.45','2025-06-09')
 f,g=page('ABC後續：舊範圍之外，也可長出自己的重訪片段','6/4原高27.45是新參照；6/9才能看見到另一側後再返回，還不能直接稱為新整理。')
 ax,v,rows=draw(f,g,0,t,'2025-01-02','2025-06-13','1101較廣背景｜原ABC 4/7至6/2共39筆保持；5/13最高影線31.40代表仍保留')
 shade(ax,v,rows,'2025-04-07','2025-06-02');arrow(ax,rows,'2025-05-13',31.4,'5/13最高31.40，未因收盤算法刪除',(.61,.86))
 ax,v,rows=draw(f,g,1,t,'2025-05-13','2025-06-13','紫色為新參照返回前6/4至6/6的原K範圍26.55至27.65；不是新區間正式起末')
 shade(ax,v,rows,fr['observed_start'],fr['observed_end']);ax.hlines(27.45,index(rows,'2025-06-04'),len(rows)-.5,color='#72539b',ls='--',lw=1)
 arrow(ax,rows,'2025-06-04',27.0,'6/4收27.00在下；6/5收27.50在上',(.16,.90))
 arrow(ax,rows,'2025-06-09',27.2,'6/9收27.20回到下側及先前範圍',(.59,.76))
 notes(f,['已知：這個片段6/9完成；到6/13收26.90仍在返回前範圍內，且整段仍在舊參照28.45下。',
 '新種子6/3仍保留；6/4只是本證據片段起日。一次重訪還不足正式定義新整理、父子或承接。',
 '5/13的31.40作為影線參照保留，雖此39筆內收盤始終未越過它；沒有收盤重訪不等於無代表價值。',
 '正式區間存在、局部活動、當前位置、來源確認分開。分類與Android仍未驗證；原核心參數不改。'],3);pdf.savefig(f);plt.close(f)
b=buf.getvalue();assert b.rstrip().endswith(b'%%EOF')and len(PdfReader(io.BytesIO(b)).pages)==3;dest=p/'output/pdf/m1-anchored-revisit-frames.pdf'
with dest.open('wb')as out:out.write(b);out.flush();os.fsync(out.fileno())
assert dest.read_bytes()==b;print(json.dumps({'pages':3,'bytes':len(b),'sha256':hashlib.sha256(b).hexdigest()}))
