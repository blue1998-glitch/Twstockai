"""Exact-source common-close-span figures, independent of research selection."""
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
p=Path(a.out);(p/'output/pdf').mkdir(parents=True,exist_ok=True);s=json.loads(Path(a.source).read_text());t=json.loads(Path(a.comparison).read_text());results=json.loads((p/'selected-common-spans.json').read_text());font=FontProperties(fname=a.font)
plt.rcParams.update({'pdf.fonttype':3,'axes.unicode_minus':False,'font.size':10})
def text(f,x,y,label,size=11):f.text(x,y,label,fontproperties=font,fontsize=size)
def page(title,subtitle):
 f=plt.figure(figsize=(17,12));g=f.add_gridspec(5,1,height_ratios=[3,1,.4,3,1],left=.07,right=.97,top=.84,bottom=.23,hspace=.24);text(f,.07,.95,title,21);text(f,.07,.91,subtitle,12);return f,g
def draw(f,g,k,src,start,end,title):
 rows=[b for b in src['bars']if start<=b['date']<=end];j=0 if k==0 else 3;ax=f.add_subplot(g[j]);v=f.add_subplot(g[j+1],sharex=ax)
 for i,b in enumerate(rows):
  o,h,l,c=[float(b[x])for x in ['open','high','low','close']];color='#c44242'if c>=o else'#168268';ax.vlines(i,l,h,color=color,lw=.85)
  if o==c:ax.hlines(c,i-.3,i+.3,color=color,lw=1)
  else:ax.add_patch(Rectangle((i-.3,min(o,c)),.6,abs(c-o),facecolor=color,edgecolor=color,lw=.4))
  v.bar(i,int(b['volume_shares_scaled'])/1e6,color=color,width=.65)
 values=[float(b[x])for b in rows for x in ['low','high']];span=max(values)-min(values);ax.set_ylim(min(values)-span*.14,max(values)+span*.36)
 for z in [ax,v]:z.set_xlim(-1,len(rows));z.grid(axis='y',alpha=.15);z.set_axisbelow(True)
 ax.set_title(title,fontproperties=font,fontsize=13,loc='left',pad=10);ax.set_ylabel('原始價格',fontproperties=font);v.set_ylabel('量／百萬股',fontproperties=font);ax.tick_params(labelbottom=False)
 ticks=np.unique(np.linspace(0,len(rows)-1,9,dtype=int));v.set_xticks(ticks,[rows[i]['date'][5:].replace('-','/')for i in ticks],rotation=15,ha='right');return ax,v,rows
def index(rows,day):return next(i for i,b in enumerate(rows)if b['date']==day)
def shade(ax,v,rows,start,end):
 ix=[i for i,b in enumerate(rows)if start<=b['date']<=end]
 if not ix:return
 lo=min(float(rows[i]['low'])for i in ix);hi=max(float(rows[i]['high'])for i in ix)
 ax.add_patch(Rectangle((ix[0]-.5,lo),len(ix),hi-lo,facecolor='#9370bb',edgecolor='none',alpha=.14,zorder=-2))
 v.add_patch(Rectangle((ix[0]-.5,0),len(ix),max(int(rows[i]['volume_shares_scaled'])for i in ix)/1e6,facecolor='#9370bb',edgecolor='none',alpha=.14,zorder=-2))
def core(ax,rows,z,color='#bd8418',alpha=.25):
 left,right=index(rows,z['path_start']),index(rows,z['path_end']);lo,hi=float(z['common_close_low']),float(z['common_close_high'])
 ax.add_patch(Rectangle((left-.45,lo),right-left+.9,hi-lo,facecolor=color,edgecolor='none',alpha=alpha,zorder=-1))
 ax.hlines([lo,hi],left-.45,right+.45,color=color,lw=.8,ls='--')
def maximal(r):
 ids={v['zone_id']for v in r['zone_views']if v['available_maximal_contiguous_span']};return[z for z in r['zones']if z['zone_id']in ids]
def turns_line(ax,rows,r):
 xs=[index(rows,x['plateau_end'])for x in r['turns']];ys=[float(x['close'])for x in r['turns']];ax.plot(xs,ys,color='#394f77',lw=1,marker='o',markersize=3,alpha=.8)
def arrow(ax,rows,day,price,label,position):ax.annotate(label,xy=(index(rows,day),price),xytext=position,textcoords='axes fraction',fontproperties=font,fontsize=11,arrowprops={'arrowstyle':'-','color':'#72539b'})
def notes(f,lines,n):
 for y,line in zip([.174,.136,.098,.060],lines):text(f,.07,y,line,12 if y==.174 else 11 if y>.06 else 10)
 text(f,.95,.025,f'{n} / 3',10)
buf=io.BytesIO()
with PdfPages(buf)as pdf:
 r=results['A-Oct7'];z=maximal(r)[0]
 f,g=page('2884：多個片段可由共同往返價格連起來','只連已完成收盤上落；藍線是收盤端點路徑，金色是各段共同涵蓋的價帶，皆非正式箱界。')
 ax,v,rows=draw(f,g,0,s,'2026-05-04','2026-10-07','較廣上漲背景｜10/7足夠辨認與完整上漲整理再漲已確認，不重問')
 shade(ax,v,rows,'2026-09-17','2026-10-07')
 ax,v,rows=draw(f,g,1,s,'2026-09-17','2026-10-07','局部共同價帶44.85至45.35｜9/30低收、10/1至10/2高收平台、10/5低收')
 shade(ax,v,rows,z['path_start'],z['path_end']);core(ax,rows,z);turns_line(ax,rows,r)
 arrow(ax,rows,'2026-09-30',44.85,'9/30收44.85；10/1才可知低收',(.01,.90))
 arrow(ax,rows,'2026-10-02',45.35,'高收平台45.35；10/5才可知',(.34,.76))
 arrow(ax,rows,'2026-10-05',44.8,'10/5低收44.80；10/6才完成兩段',(.57,.90))
 notes(f,['已知：兩段完成上落共同涵蓋44.85至45.35，這個局部候選到10/6才有完整證據。',
 '10/7收45.75已高於這個共同價帶，仍不否定已確認整理；共同價帶、原K外包與正式區界不同。',
 '舊重訪片段可按參照價位與可知日追溯到此候選；不是多個片段投票，也不是單純重疊就合併。',
 '10/6僅本方法證據完成日，不宣稱最早整理日；收盤端點涵蓋不等於每個價位實際成交或籌碼密集。'],1);pdf.savefig(f);plt.close(f)

 r=results['B-May4'];zs=maximal(r)
 f,g=page('方向對照：時間相連，共同價位卻已下移','兩個候選共用一段真實下跌路徑，仍不能因此說它們共享同一價格核心或必須合併。')
 ax,v,rows=draw(f,g,0,s,'2026-01-02','2026-05-04','同股較廣背景｜此為事後方向對照，人工區間負標籤仍為null')
 shade(ax,v,rows,'2026-04-15','2026-05-04')
 ax,v,rows=draw(f,g,1,s,'2026-04-15','2026-05-04','先有32.75至33.00，後有32.45至32.55；中間共用4/22至4/23的下跌段')
 shade(ax,v,rows,zs[0]['path_start'],zs[0]['path_end']);core(ax,rows,zs[0]);core(ax,rows,zs[1],color='#477a99');turns_line(ax,rows,r)
 arrow(ax,rows,'2026-04-21',32.95,'金色32.75至33.00，4/24才可知擴展',(.015,.91))
 arrow(ax,rows,'2026-04-27',32.55,'藍色32.45至32.55，4/28才可知',(.42,.77))
 notes(f,['已知：兩個共同價帶互不相交；有共用下跌段，不等於它們是同一個穩定活動價位。',
 '這能描寫局部往返向下移動；不直接決定正式拆箱／合併，也不抹掉較早確實發生過的往返。',
 '4/23已知的較短候選保留，4/24可擴展為較長觀察；後來的擴展不回寫較早輸出或當獨立加票。',
 '共同價帶可能很窄，沒有新增寬度門檻或交易資格；與不同日期的10月例不比績效、概率或重要性。'],2);pdf.savefig(f);plt.close(f)

 gr=results['G2-full-manual-scope'];ar=results['ABC-next-Jun13'];az=maximal(ar)[0]
 f,g=page('局部共同價帶，不能取代較大整體或原影線代表','上圖保留已確認G2人工涵蓋，下圖觀察ABC離開後的新活動；兩種層次分開保存。')
 ax,v,rows=draw(f,g,0,t,'2023-01-16','2023-08-16','G2完整136筆｜金色僅局部共同價帶，不把較大G2拆成20個正式區間')
 shade(ax,v,rows,'2023-01-16','2023-08-16')
 for z in maximal(gr):core(ax,rows,z,alpha=.32)
 arrow(ax,rows,'2023-05-02',40.25,'已確認代表5/2最高40.25保留',(.21,.89))
 ax.axvline(index(rows,'2023-08-04')-.5,color='#a84a4a',lw=.7,ls=':')
 ax,v,rows=draw(f,g,1,t,'2025-06-03','2025-06-13','ABC後續｜6/6高收27.55→6/10低收27.15→6/11高收27.30；到6/12才可知')
 shade(ax,v,rows,az['path_start'],az['path_end']);core(ax,rows,az);turns_line(ax,rows,ar)
 arrow(ax,rows,'2025-06-11',27.3,'共同價帶27.15至27.30，6/12完成證據',(.23,.90))
 notes(f,['已知：ABC至6/11只有一段完成上落，至6/12才可提出共同價帶；新候選不等於正式新整理。',
 'G2較大涵蓋可包含多個不同共同價帶；8/3原列待核處未跨接新計算，舊G2人工涵蓋仍保留資格。',
 'ABC原39筆與6/3在外、5/13影線31.40代表保持；5/13確認K也完整另存，未被收盤價帶取代。',
 '這是圖形辨識研究；正式分類、資金飛輪成效與行動資格未驗，Android未測新版，main與原參數不改。'],3);pdf.savefig(f);plt.close(f)
b=buf.getvalue();assert b.rstrip().endswith(b'%%EOF')and len(PdfReader(io.BytesIO(b)).pages)==3;dest=p/'output/pdf/m1-common-return-price-bands.pdf'
with dest.open('wb')as out:out.write(b);out.flush();os.fsync(out.fileno())
assert dest.read_bytes()==b;print(json.dumps({'pages':3,'bytes':len(b),'sha256':hashlib.sha256(b).hexdigest()}))
