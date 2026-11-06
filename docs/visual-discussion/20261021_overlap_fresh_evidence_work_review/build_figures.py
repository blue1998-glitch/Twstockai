"""Three exact-source pages: fresh migration, actual visits, and reused evidence."""
import gzip,hashlib,io,json,os
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle
from matplotlib.font_manager import FontProperties
from matplotlib.backends.backend_pdf import PdfPages
from pypdf import PdfReader
from overlap_roles import ROOT,inputs,compare,write
src,zones,tm,lm,scopes,prior=inputs();zm={z['zone_id']:z for z in zones};specs=json.loads((ROOT/'selected-query-specs.json').read_text())
font=FontProperties(fname='/workspace/scratch/54685b8dac93/version-continuity-review/research-font.otf')
plt.rcParams.update({'pdf.fonttype':3,'axes.unicode_minus':False,'font.size':10})
def text(f,x,y,s,size=11):f.text(x,y,s,fontproperties=font,fontsize=size)
def page(title,sub):
 f=plt.figure(figsize=(17,12));g=f.add_gridspec(5,1,height_ratios=[3,1,.45,3,1],left=.065,right=.965,top=.835,bottom=.24,hspace=.27)
 text(f,.065,.953,title,21);text(f,.065,.913,sub,12);return f,g
def draw(f,g,k,code,start,end,title):
 bs=[b for b in src[code]['bars']if start<=b['date']<=end];j=0 if k==0 else 3;ax=f.add_subplot(g[j]);v=f.add_subplot(g[j+1],sharex=ax)
 for i,b in enumerate(bs):
  o,h,l,c=[float(b[x])for x in ['open','high','low','close']];color='#c44242'if c>=o else'#168268'
  ax.vlines(i,l,h,color=color,lw=.85)
  if o==c:ax.hlines(c,i-.3,i+.3,color=color,lw=1)
  else:ax.add_patch(Rectangle((i-.3,min(o,c)),.6,abs(c-o),facecolor=color,lw=0))
  v.bar(i,int(b['volume_shares_scaled'])/1e6,color=color,width=.65)
 lo=min(float(b['low'])for b in bs);hi=max(float(b['high'])for b in bs);span=hi-lo
 ax.set_ylim(lo-span*.12,hi+span*.39)
 for q in [ax,v]:q.set_xlim(-1,len(bs));q.grid(axis='y',alpha=.15);q.set_axisbelow(True)
 ax.tick_params(labelbottom=False);ax.set_title(title,fontproperties=font,fontsize=13,loc='left',pad=10);ax.set_ylabel('原始價格',fontproperties=font);v.set_ylabel('量／百萬股',fontproperties=font)
 ticks=sorted({round(i*(len(bs)-1)/8)for i in range(9)});v.set_xticks(ticks,[bs[i]['date'][5:].replace('-','/')for i in ticks],rotation=12,ha='right');return ax,v,bs
def ix(bs,d):return next(i for i,b in enumerate(bs)if b['date']==d)
def shade(ax,v,bs,start,end,color='#7770ad',alpha=.13):
 ids=[i for i,b in enumerate(bs)if start<=b['date']<=end];part=[bs[i]for i in ids]
 lo=min(float(b['low'])for b in part);hi=max(float(b['high'])for b in part)
 ax.add_patch(Rectangle((ids[0]-.45,lo),ids[-1]-ids[0]+.9,hi-lo,facecolor=color,alpha=alpha,lw=0,zorder=-2))
 v.add_patch(Rectangle((ids[0]-.45,0),ids[-1]-ids[0]+.9,max(int(b['volume_shares_scaled'])for b in part)/1e6,facecolor=color,alpha=alpha,lw=0,zorder=-2))
def core(ax,bs,z,color='#bd8418'):
 i,j=ix(bs,z['path_start']),ix(bs,z['path_end']);lo,hi=float(z['common_close_low']),float(z['common_close_high'])
 ax.add_patch(Rectangle((i-.45,lo),j-i+.9,hi-lo,facecolor=color,alpha=.35,edgecolor='none',zorder=-1))
 ax.hlines([lo,hi],i-.45,j+.45,color=color,lw=.8)
def arrow(ax,bs,day,label,pos,field='close'):
 b=next(b for b in bs if b['date']==day);ax.annotate(label,xy=(ix(bs,day),float(b[field])),xytext=pos,textcoords='axes fraction',fontproperties=font,fontsize=11,arrowprops={'arrowstyle':'-','color':'#72539b'})
def notes(f,lines,n):
 for y,s in zip([.18,.14,.10,.06],lines):text(f,.065,y,s,12 if y==.18 else 11 if y>.06 else 10)
 text(f,.94,.025,f'{n} / 3',10)
def pair(name):
 sp=specs[name];return zm[sp['older_zone_id']],zm[sp['later_zone_id']]
cases={}
for name in specs:
 a,b=pair(name);cases[name]=compare(src[a['code']],a,b,tm,lm,b['known_on_saved_bar'])
noa=next(z for z in zones if z['code']=='1101'and z['path_start']=='2023-01-17'and z['path_end']=='2023-02-09')
nob=next(z for z in zones if z['code']=='1101'and z['path_start']=='2023-03-15'and z['path_end']=='2023-03-24')
cases['G2-geometric-overlap-no-path-close-visit']=compare(src['1101'],noa,nob,tm,lm,'2023-03-27')
assert not cases['G2-geometric-overlap-no-path-close-visit']['actual_later_path_close_visits_older_core']
cases['G2-no-path-visit-confirmation-bar']=nob['right_evidence_bar']
write(ROOT/'figure-case-data.json',cases)
buf=io.BytesIO()
with PdfPages(buf)as pdf:
 a,b=pair('ABC-fresh-lower')
 f,g=page('ABC：影線仍交疊，後續活動價位已向下移','金色是較早共同價帶，藍綠色是後來候選；紫色仍保留已確認人工39筆，不用局部移動直接拆箱。')
 ax,v,bs=draw(f,g,0,'1101','2025-04-07','2025-06-02','完整人工ABC39筆｜較早30.55至30.60；較後29.80至30.30，仍在同一較大觀察內')
 shade(ax,v,bs,'2025-04-07','2025-06-02');core(ax,bs,a);core(ax,bs,b,'#438b98')
 arrow(ax,bs,'2025-05-13','5/13影線代表31.40保留',(.12,.91),'high')
 arrow(ax,bs,'2025-05-23','後續原影線29.50至30.40，仍與較早28.50至31.20交疊',(.42,.75))
 ax,v,bs=draw(f,g,1,'1101','2025-05-12','2025-05-26','證據時點｜較早候選5/13已可知；後段完整來源自5/16起，5/26才確認')
 shade(ax,v,bs,b['path_start'],b['path_end'],'#438b98',.15);core(ax,bs,b,'#438b98')
 ax.hlines([30.55,30.60],-.4,len(bs)-.4,color='#bd8418',ls='--',lw=.8)
 arrow(ax,bs,'2025-05-16','5/16是後段首轉向的左證據日',(.02,.91))
 arrow(ax,bs,'2025-05-26','5/26才知5/19至5/23的兩段活動',(.51,.75))
 notes(f,['可提出：全新完成的雙向活動，其共同價帶比先前更低；即使影線外包仍交疊，也有新增移動證據。',
 '此配對沒有共用轉向或完成段，後段最早證據5/16晚於前段可知日5/13，未重用前段期間。',
 '這是較大ABC內部活動價位下移，不自動選為新主區間、正式拆箱或否定原39筆／5/13代表。',
 '5/23以前沒有本配對後段完整確認；所述可知日是保存原值的研究資格，不證歷史當時曾選取。'],1);pdf.savefig(f);plt.close(f)

 a,b=pair('G2-fresh-overlap')
 f,g=page('G2：共同價域重疊，還要分開看實際收盤造訪','上圖有全新往返及保存收盤造訪；下圖路徑內僅有價域交集，確認K的實際收盤入內另記時點。')
 ax,v,bs=draw(f,g,0,'1101','2023-01-16','2023-08-16','人工G2完整136筆仍保留｜較早36.25至36.95，後段36.60至36.75，2/10才可知')
 shade(ax,v,bs,'2023-01-16','2023-08-16');core(ax,bs,a);core(ax,bs,b,'#438b98')
 arrow(ax,bs,'2023-02-09','2/7、8、9收36.65、36.75、36.60落在較早核心內',(.02,.91))
 arrow(ax,bs,'2023-05-02','5/2 H40.25代表照舊；不因新小核心改主參照',(.55,.76),'high')
 ax,v,bs=draw(f,g,1,'1101','2023-03-14','2023-03-27','另一對照｜後段共同36.35至37.10，涵蓋舊36.60至36.75；藍點為每日收盤')
 shade(ax,v,bs,nob['path_start'],nob['path_end'],'#438b98',.13);core(ax,bs,nob,'#438b98')
 ax.hlines([36.60,36.75],-.4,len(bs)-.4,color='#bd8418',ls='--',lw=.9)
 ax.plot(range(len(bs)),[float(q['close'])for q in bs],color='#35557b',marker='o',markersize=3,lw=.9)
 arrow(ax,bs,'2023-03-24','3/15至3/24保存收盤未落進舊核心',(.07,.91))
 arrow(ax,bs,'2023-03-27','3/27確認K收36.65入內，按當天另記；虛線為舊價參照',(.42,.75))
 notes(f,['可提出：上例在較早候選已知後，重新完成雙向路徑，且有真實保存收盤落進較早共同價域。',
 '下例路徑內無保存收盤進舊核心；3/27確認K收36.65入內，兩種證據按日期分開，不能倒填。',
 '也不能反推盤中從未成交；端點涵蓋、每日收盤造訪、日內成交與正式修復分開。藍線僅連點。',
 '全新來源不是統計獨立樣本或多票；跨原8/3資料疑點的配對另附資格，不認證整體連續性。'],2);pdf.savefig(f);plt.close(f)

 f,g=page('另兩種情況：共用完成段，或重用較早證據期間','新候選可以補充目前觀察；只有日期變晚、段數不同或不共用完整段，都不足以說來源全部換新。')
 a,b=pair('B-shared-path')
 ax,v,bs=draw(f,g,0,'2884','2026-04-15','2026-05-04','方向對照｜共同核心下移，卻共用4/22至4/23的完成下跌段')
 for z,col in [(a,'#bd8418'),(b,'#438b98')]:shade(ax,v,bs,z['path_start'],z['path_end'],col,.12);core(ax,bs,z,col)
 arrow(ax,bs,'2026-04-22','較早32.75至33.00，4/24可知',(.01,.91))
 arrow(ax,bs,'2026-04-23','後段32.45至32.55，4/28可知，但重用同一完成段',(.43,.75))
 a,b=pair('A-reused-context')
 ax,v,bs=draw(f,g,1,'2884','2026-09-17','2026-10-16','2884較廣整理與後續｜10/7足夠已答；較後候選不共段，仍共用10/5低收轉向')
 shade(ax,v,bs,'2026-09-17','2026-10-07');core(ax,bs,a);core(ax,bs,b,'#438b98')
 arrow(ax,bs,'2026-10-05','10/5低收同時接在兩組路徑；前組10/6已知',(.01,.91))
 arrow(ax,bs,'2026-10-12','後組10/12才知，但其完整來源從10/2開始',(.46,.75))
 notes(f,['可提出：B是共享既有路徑的價位變動；不能當成兩份全新往返。也不把此例升成人工全尺度負例。',
 'A雖無共用完整段，仍共用10/5轉向；後段左證據10/2早於前段可知10/6，尚非全部來源較晚。',
 '這些補充不刪候選，也不否定已答整理；可變當前位置與不可變出生證據分開，較晚不自動較重要。',
 '分類NOT_VALIDATED；正式起末成員／父子合併未定，Android未測新版；行動與資金飛輪成效未評估。'],3);pdf.savefig(f);plt.close(f)
b=buf.getvalue();assert b.rstrip().endswith(b'%%EOF')and len(PdfReader(io.BytesIO(b)).pages)==3
p=ROOT/'output/pdf/m1-overlapping-ranges-fresh-evidence.pdf';p.parent.mkdir(parents=True,exist_ok=True)
with p.open('wb')as out:out.write(b);out.flush();os.fsync(out.fileno())
assert p.read_bytes()==b;print(json.dumps({'pages':3,'bytes':len(b),'sha256':hashlib.sha256(b).hexdigest()}))
