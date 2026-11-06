"""New exact-source role/availability figures; no prior figure rebuild."""
import io,json,os,hashlib
from pathlib import Path
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle
from matplotlib.font_manager import FontProperties
from matplotlib.backends.backend_pdf import PdfPages
from pypdf import PdfReader
from source_roles import ROOT,load_inputs
src,cores,reg,selected=load_inputs()
font=FontProperties(fname='/workspace/scratch/54685b8dac93/version-continuity-review/research-font.otf')
plt.rcParams.update({'pdf.fonttype':3,'axes.unicode_minus':False,'font.size':10})
def text(f,x,y,s,size=11):f.text(x,y,s,fontproperties=font,fontsize=size)
def page(title,sub):
 f=plt.figure(figsize=(17,12));g=f.add_gridspec(5,1,height_ratios=[3,1,.5,3,1],left=.065,right=.965,top=.835,bottom=.24,hspace=.26)
 text(f,.065,.952,title,21);text(f,.065,.912,sub,12);return f,g
def draw(f,g,k,code,start,end,title):
 rows=[b for b in src[code]['bars']if start<=b['date']<=end];j=0 if k==0 else 3
 ax=f.add_subplot(g[j]);v=f.add_subplot(g[j+1],sharex=ax)
 for i,b in enumerate(rows):
  o,h,l,c=[float(b[x])for x in ['open','high','low','close']];col='#c44242'if c>=o else'#168268'
  ax.vlines(i,l,h,color=col,lw=.85)
  if o==c:ax.hlines(c,i-.3,i+.3,color=col,lw=1)
  else:ax.add_patch(Rectangle((i-.3,min(o,c)),.6,abs(c-o),facecolor=col,lw=0))
  v.bar(i,int(b['volume_shares_scaled'])/1e6,color=col,width=.65)
 lo=min(float(b['low'])for b in rows);hi=max(float(b['high'])for b in rows);span=hi-lo
 ax.set_ylim(lo-span*.12,hi+span*.37)
 for q in [ax,v]:q.set_xlim(-1,len(rows));q.grid(axis='y',alpha=.15);q.set_axisbelow(True)
 ax.tick_params(labelbottom=False);ax.set_title(title,fontproperties=font,fontsize=13,loc='left',pad=11)
 ax.set_ylabel('原始價格',fontproperties=font);v.set_ylabel('量／百萬股',fontproperties=font)
 ticks=sorted({round(i*(len(rows)-1)/8)for i in range(9)})
 v.set_xticks(ticks,[rows[i]['date'][5:].replace('-','/')for i in ticks],rotation=12,ha='right')
 return ax,v,rows
def ix(rows,d):return next(i for i,b in enumerate(rows)if b['date']==d)
def box(ax,rows,start,end,lo,hi,color='#6e69a3',alpha=.12,style='-'):
 ids=[i for i,b in enumerate(rows)if start<=b['date']<=end]
 if ids:ax.add_patch(Rectangle((ids[0]-.45,float(lo)),ids[-1]-ids[0]+.9,float(hi)-float(lo),facecolor=color,edgecolor=color,alpha=alpha,ls=style,lw=1.3,zorder=-1))
def manual(ax,v,rows,start,end):
 bs=[b for b in rows if start<=b['date']<=end];box(ax,rows,start,end,min(float(b['low'])for b in bs),max(float(b['high'])for b in bs),alpha=.12)
 ids=[i for i,b in enumerate(rows)if start<=b['date']<=end]
 v.add_patch(Rectangle((ids[0]-.45,0),ids[-1]-ids[0]+.9,max(int(b['volume_shares_scaled'])for b in bs)/1e6,facecolor='#6e69a3',alpha=.12,lw=0,zorder=-1))
def gold(ax,rows,z):box(ax,rows,z['path_start'],z['path_end'],z['common_close_low'],z['common_close_high'],'#bd8418',.32)
def maximal(r):
 ids={v['zone_id']for v in r['zone_views']if v['available_maximal_contiguous_span']};return[z for z in r['zones']if z['zone_id']in ids]
def arrow(ax,rows,d,price,s,pos):ax.annotate(s,xy=(ix(rows,d),price),xytext=pos,textcoords='axes fraction',fontproperties=font,fontsize=11,arrowprops={'arrowstyle':'-','color':'#72539b'})
def notes(f,lines,n):
 for y,s in zip([.18,.14,.10,.06],lines):text(f,.065,y,s,12 if y==.18 else 11 if y>.06 else 10)
 text(f,.94,.025,f'{n} / 3',10)
buf=io.BytesIO()
with PdfPages(buf)as pdf:
 f,g=page('2884：局部價帶先出現，較大原低點後確認','金色為既存共同收盤價帶；紫色外包只畫來源涵蓋的時間與價格，兩點價域不是正式箱體。')
 ax,v,rows=draw(f,g,0,'2884','2026-08-03','2026-10-07','截至10/7｜原3%來源：8/12低36.30 → 9/17高47.35 → 10/1低44.20')
 box(ax,rows,'2026-08-12','2026-09-17',36.30,47.35,alpha=.10)
 box(ax,rows,'2026-09-17','2026-10-01',44.20,47.35,alpha=.22)
 gold(ax,rows,selected['A-Oct7']['zones'][0])
 arrow(ax,rows,'2026-09-17',47.35,'9/17高47.35，9/23已確認',(.08,.90))
 arrow(ax,rows,'2026-10-01',44.2,'10/1低44.20，10/7才確認',(.57,.73))
 ax,v,rows=draw(f,g,1,'2884','2026-09-17','2026-10-16','後續另看至10/16｜固定同一局部核心，新增當前位置；不回填10/6')
 box(ax,rows,'2026-09-17','2026-10-01',44.20,47.35,alpha=.18);gold(ax,rows,selected['A-Oct7']['zones'][0])
 ax.hlines(47.35,ix(rows,'2026-09-17'),len(rows)-.4,color='#72539b',ls='--',lw=.8)
 arrow(ax,rows,'2026-10-05',44.8,'10/6才知共同44.85至45.35',(.01,.90))
 arrow(ax,rows,'2026-10-14',47.3,'10/14收47.30仍在44.20至47.35內',(.35,.74))
 arrow(ax,rows,'2026-10-16',49.15,'10/15、16收盤在47.35上',(.60,.92))
 notes(f,['已知：10/6局部核心已成立；當天原低44.20仍只是已出現原值，10/7才有原核心確認資格。',
 '10/7新增的44.20至47.35價域包含核心，但來源只到10/1，未包住9/30至10/5完整路徑。',
 '更早36.30至47.35也包含核心，來源卻全在局部路徑之前；價格包含本身不能定父子或主要性。',
 '兩點價域不是原箱體／正式界；10/7足夠辨認已確認，不宣稱10/6最早日，也不補造10/7原核心快照。'],1);pdf.savefig(f);plt.close(f)

 f,g=page('1101 ABC：同一價框，可有不同尺度與確認日','紫色為已確認人工ABC涵蓋；金色為局部共同價帶；藍框是原保存的研究箱界，非正式成員邊界。')
 ax,v,rows=draw(f,g,0,'1101','2024-11-25','2025-06-13','較廣下跌背景｜ABC自己的區間與相對舊主要帶更弱已確認；舊帶正式價界未定')
 manual(ax,v,rows,'2025-04-07','2025-06-02')
 arrow(ax,rows,'2025-05-13',31.4,'5/13代表影線31.40保留',(.42,.88))
 arrow(ax,rows,'2025-06-02',27.7,'6/2仍在人工39筆內；6/3在外',(.62,.70))
 ax,v,rows=draw(f,g,1,'1101','2025-04-07','2025-06-13','原研究價框28.45至31.40｜3%於5/14可用，6%於5/27才可用')
 manual(ax,v,rows,'2025-04-07','2025-06-02');box(ax,rows,'2025-04-08','2025-05-13',28.45,31.40,'#3b7b9a',.18)
 for z in maximal(selected['ABC-Jun2']):gold(ax,rows,z)
 arrow(ax,rows,'2025-05-13',31.4,'原值5/13即知；3%高點5/14確認',(.04,.91))
 arrow(ax,rows,'2025-05-27',29.35,'6%研究箱5/27才可用；不回填5/14',(.46,.75))
 notes(f,['已知：相同28.45至31.40幾何來自不同原尺度，確認日不同；不是兩張獨立支持票。',
 '6/2收27.70已在此原研究框下，仍屬已確認ABC39筆；價框離開不能直接決定正式停止。',
 '內部三個共同價帶仍保留；有些價格被框住、來源時間卻未被包住，不能僅靠包含或重疊合併。',
 '本圖是保存原輸出的時點資格研究，未重算原核心；不能用後來研究箱取代人工涵蓋或舊主要帶角色。'],2);pdf.savefig(f);plt.close(f)

 f,g=page('G2：保留較大整體，原影線代表另有確認時點','金色局部共同價帶只解釋內部活動；不把20個局部核心變成20個正式區間，也不取代較大G2。')
 ax,v,rows=draw(f,g,0,'1101','2023-01-16','2023-08-16','截至8/16｜G2人工完整136筆；5/2最高40.25仍是已確認代表')
 manual(ax,v,rows,'2023-01-16','2023-08-16')
 for z in maximal(selected['G2-full-manual-scope']):gold(ax,rows,z)
 arrow(ax,rows,'2023-05-02',40.25,'5/2原高40.25；原3%高點5/9才確認',(.21,.92))
 ax.axvline(ix(rows,'2023-08-04')-.5,color='#a84a4a',ls=':',lw=.8)
 arrow(ax,rows,'2023-08-04',float(next(b['low']for b in rows if b['date']=='2023-08-04')),'8/3原列待核缺日；新片段不跨接',(.64,.76))
 ax,v,rows=draw(f,g,1,'1101','2023-04-18','2023-05-10','截至5/10放大｜原值出現日與原確認日分開，後來人工選代表也不倒填歷史')
 available=[z for z in selected['G2-full-manual-scope']['zones']if z['known_on_saved_bar']<='2023-05-10']
 for z in available:
  if z['path_start']>='2023-04-18'and z['path_end']<='2023-05-10'and not any(set(z['leg_ids'])<set(other['leg_ids'])for other in available):gold(ax,rows,z)
 arrow(ax,rows,'2023-05-02',40.25,'5/2最高40.25原K完整保留',(.02,.90))
 arrow(ax,rows,'2023-05-09',38.65,'5/9達原3%確認；不是5/2當天已確認',(.48,.73))
 notes(f,['已知：價格活動核心、原高低代表、較大人工涵蓋是不同來源角色，可以同時保留。',
 '更晚出現的小核心，不因此提升主要性或降低舊高重要性；本輪不選主壓力、不定父子或正式合併。',
 '原核心確認時間採保存中繼資料，未證歷史公開時點；較早原快照缺失仍不補造，缺日資格保持。',
 '分類NOT_VALIDATED；Android未測新版；行動與資金飛輪成效未評估。保留main、原參數與全部前成果。'],3);pdf.savefig(f);plt.close(f)
b=buf.getvalue();assert b.rstrip().endswith(b'%%EOF')and len(PdfReader(io.BytesIO(b)).pages)==3
p=ROOT/'output/pdf/m1-local-core-original-source-roles.pdf';p.parent.mkdir(parents=True,exist_ok=True)
with p.open('wb')as out:out.write(b);out.flush();os.fsync(out.fileno())
assert p.read_bytes()==b;print(json.dumps({'pages':3,'bytes':len(b),'sha256':hashlib.sha256(b).hexdigest()}))
