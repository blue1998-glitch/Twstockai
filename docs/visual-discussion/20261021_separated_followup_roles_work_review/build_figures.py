"""Exact raw-source separated follow-up role proposal review, three new pages."""
import io,os,json,gzip,hashlib
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle
from matplotlib.font_manager import FontProperties
from matplotlib.backends.backend_pdf import PdfPages
from pypdf import PdfReader
from followup_roles import ROOT,inputs
src,zones,pools,scopes,prior=inputs();selected=json.loads(gzip.decompress((ROOT/'selected-role-proposals.json.gz').read_bytes()))
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
def shade(ax,v,bs,start,end,color='#7770ad',alpha=.14):
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
def maximal(r):
 ids={v['zone_id']for v in r['zone_views']if v['available_maximal_contiguous_span']};return[z for z in r['zones']if z['zone_id']in ids]
buf=io.BytesIO()
with PdfPages(buf)as pdf:
 r=selected['ABC-2025-06-13'];l=r['links'][0];z=next(z for z in zones if z['zone_id']==l['zone_id'])
 f,g=page('ABC：離開舊範圍後，何時可另列局部活動？','本輪正面條件：先有整根外移，再在同一次外側收盤歷程中完成雙向往返，而且整段影線仍在舊框外。')
 ax,v,bs=draw(f,g,0,'1101','2024-11-25','2025-06-13','較廣背景｜原ABC39筆與自己的較弱區間已確認；舊主要帶正式價格界線仍未定')
 shade(ax,v,bs,'2025-04-07','2025-06-02');shade(ax,v,bs,z['path_start'],z['path_end'],'#478d99',.25);core(ax,bs,z)
 arrow(ax,bs,'2025-05-13','5/13代表影線31.40保留',(.38,.90),'high')
 arrow(ax,bs,'2025-06-03','6/3整根在舊凍結框28.45下',(.63,.73),'high')
 ax,v,bs=draw(f,g,1,'1101','2025-05-13','2025-06-13','截至6/13｜後續共同核心27.15至27.30；6/12才有完整證據')
 ax.hlines(28.45,-.4,len(bs)-.4,color='#72539b',ls='--',lw=.9);shade(ax,v,bs,z['path_start'],z['path_end'],'#478d99',.22);core(ax,bs,z)
 arrow(ax,bs,'2025-06-02','6/2仍在人工39筆內',(.01,.91))
 arrow(ax,bs,'2025-06-06','6/6至6/11影線外包26.90至27.65',(.25,.74))
 arrow(ax,bs,'2025-06-12','6/12完成兩段；6/11以前尚無此候選',(.58,.90))
 notes(f,['可提出：後續另有一段位於舊凍結框下方的雙向活動，與舊框分開觀察；不是只有一筆離開。',
 '6/6至6/11整段最高27.65仍低於28.45，且尚未收回舊框；6/12才可提出此角色候選。',
 '先保留舊範圍及較大歷史參照，再並列後續局部活動；不據此裁定正式新箱或舊箱終點。',
 '框是先前觀察外包，非正式區界；ABC39筆、6/3在外、5/13代表與相對舊主要帶更弱的已答保持。'],1);pdf.savefig(f);plt.close(f)

 r=selected['G2-2023-04-27'];l=r['links'][0];z=next(z for z in zones if z['zone_id']==l['zone_id'])
 f,g=page('G2：返回會結束一次離開，較大整體仍保留','不能把幾個月後的新活動，接成第一次離開的持續證據；每一次收回或資料中斷都要分開。')
 ax,v,bs=draw(f,g,0,'1101','2023-01-16','2023-08-16','完整人工G2共136筆｜後續局部外移不直接終止較大G2，也不取代5/2代表40.25')
 shade(ax,v,bs,'2023-01-16','2023-08-16');shade(ax,v,bs,z['path_start'],z['path_end'],'#478d99',.25);core(ax,bs,z)
 arrow(ax,bs,'2023-05-02','已確認5/2影線代表40.25保持',(.20,.91),'high')
 arrow(ax,bs,'2023-08-04','8/3原列待核；新追蹤不跨接',(.63,.76),'low')
 ax,v,bs=draw(f,g,1,'1101','2023-02-16','2023-05-16','固定舊框35.90至37.85｜2月離開後3/1已返回；4月後續屬另一次離開')
 ax.hlines(37.85,-.4,len(bs)-.4,color='#72539b',ls='--',lw=.9);shade(ax,v,bs,z['path_start'],z['path_end'],'#478d99',.22);core(ax,bs,z)
 arrow(ax,bs,'2023-03-01','3/1收37.80回舊框，2月歷程結束',(.01,.91))
 arrow(ax,bs,'2023-04-24','4/21另次離開；4/24整根在上',(.38,.75),'low')
 arrow(ax,bs,'2023-04-27','4/27才知外側雙向核心38.50至39.10',(.57,.92))
 notes(f,['可提出：4月另次離開中的局部外側活動；不可說它證明2月離開一直延續至4月。',
 '4/24至4/26影線外包38.20至39.80全在37.85上，4/27才知兩段；5/12又收回舊框。',
 '後來收回時，保留已完成活動作歷史參照，更新目前角色；不刪出生證據、不自動合併或解除。',
 '此處是同一舊凍結框的逐次離開，不是已定市場生命階段；G2人工大範圍與原缺日限制保持。'],2);pdf.savefig(f);plt.close(f)

 f,g=page('兩個限制：單筆外移與核心下移，都還不夠','正面條件只支持另列「外側局部活動候選」；不作所有區間的必要條件，不據此推回人工負例。')
 ax,v,bs=draw(f,g,0,'2884','2026-05-04','2026-10-16','2884較廣上漲背景｜10/7足夠辨認已答；10/16是目前來源最後一筆')
 shade(ax,v,bs,'2026-09-17','2026-10-07');core(ax,bs,prior['A-Oct7']['zones'][0])
 arrow(ax,bs,'2026-10-07','原整理已確認，不需等新的外側往返',(.22,.90))
 arrow(ax,bs,'2026-10-16','10/16整根在47.35上；只有一筆新種子',(.58,.76),'low')
 ax,v,bs=draw(f,g,1,'2884','2026-04-15','2026-05-04','方向對照｜兩核心下移，但各自整段影線範圍仍交疊')
 zs=maximal(prior['B-May4'])
 for z,col in zip(zs,['#bb8d2d','#488799']):shade(ax,v,bs,z['path_start'],z['path_end'],col,.12);core(ax,bs,z,col)
 arrow(ax,bs,'2026-04-21','先32.75至33.00；原影線32.35至33.20',(.01,.91))
 arrow(ax,bs,'2026-04-27','後32.45至32.55；原影線32.00至33.10',(.44,.74))
 notes(f,['2884截至10/16不能提出新種子的外側雙向活動；來源無後續，不補造、更不否定先前整理。',
 '方向對照的共同核心不相交，卻仍共用下跌路徑，影線範圍亦交疊；先描寫內部活動價位下移。',
 '因此核心下移、單根離開與外側反覆活動，給的是不同證據；不強制同一停止或正式拆箱結論。',
 '新研究非分類器；正式起末成員／主要角色仍未定，Android未測新版，行動與資金飛輪成效未評估。'],3);pdf.savefig(f);plt.close(f)
b=buf.getvalue();assert b.rstrip().endswith(b'%%EOF')and len(PdfReader(io.BytesIO(b)).pages)==3
p=ROOT/'output/pdf/m1-separated-followup-role-proposals.pdf';p.parent.mkdir(parents=True,exist_ok=True)
with p.open('wb')as out:out.write(b);out.flush();os.fsync(out.fileno())
assert p.read_bytes()==b;print(json.dumps({'pages':3,'bytes':len(b),'sha256':hashlib.sha256(b).hexdigest()}))
