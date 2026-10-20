"""Read-only new current-case plot, retaining prior full five-year/two-year pages."""
from pathlib import Path
import json,hashlib,argparse
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib import font_manager
from matplotlib.patches import Rectangle
from pypdf import PdfReader,PdfWriter
ap=argparse.ArgumentParser();ap.add_argument('--prior',default='independent-level-review/output/pdf/m1-independent-source-levels.pdf');ap.add_argument('--font',default='version-continuity-review/research-font.otf');ap.add_argument('--out',default=str(Path(__file__).parent));a=ap.parse_args();out=Path(a.out);tmp=out/'tmp/pdfs';pd=out/'output/pdf';tmp.mkdir(parents=True,exist_ok=True);pd.mkdir(parents=True,exist_ok=True)
raw=Path(a.prior).read_bytes();assert hashlib.sha256(raw).hexdigest()=='a60128d12217e8f45f8e2088b407a5a2adb1b0618d45223a3b1f6ebaf2437978';old=PdfReader(a.prior);assert len(old.pages)==3
e=json.loads((out/'evidence.json').read_text());rows=e['recent_chart_rows'];dates=[r['bar']['date']for r in rows];pos={d:i for i,d in enumerate(dates)}
font_manager.fontManager.addfont(a.font);plt.rcParams.update({'font.family':font_manager.FontProperties(fname=a.font).get_name(),'pdf.fonttype':3,'axes.unicode_minus':False,'font.size':10})
fig=plt.figure(figsize=(17,11),facecolor='white');gs=fig.add_gridspec(3,1,height_ratios=[5,1.4,1.5],left=.065,right=.965,bottom=.25,top=.84,hspace=.075);ax=fig.add_subplot(gs[0]);av=fig.add_subplot(gs[1],sharex=ax);am=fig.add_subplot(gs[2],sharex=ax)
colors=[]
for j,r in enumerate(rows):
 b=r['bar'];o,h,l,c=[float(b[k])for k in ['open','high','low','close']];co='#bf4141' if c>o else '#188265' if c<o else '#777';colors.append(co);ax.vlines(j,l,h,lw=1,color=co)
 if o==c:ax.hlines(c,j-.3,j+.3,color=co,lw=1)
 else:ax.add_patch(Rectangle((j-.3,min(o,c)),.6,abs(c-o),facecolor=co,edgecolor=co,lw=.4))
for w,co in [('5','#c89a00'),('20','#487bb6'),('60','#9065aa'),('130','#c67e43'),('260','#737d84')]:ax.plot([None if r['moving_averages'][w]is None else float(r['moving_averages'][w])for r in rows],color=co,lw=.9,label='原MA'+w)
ax.set_ylim(28.5,55);ax.set_ylabel('Raw價格');ax.legend(loc='upper left',ncol=5,fontsize=9,frameon=False)
x1,x2=pos['2026-09-17'],pos['2026-10-14'];ax.plot([x1,x2],[53.6,53.6],color='#416b94',lw=1.3);ax.text((x1+x2)/2,54,'討論的反覆區，尚非正式區界',ha='center',fontsize=10,color='#315b80')
ax.hlines(47.35,x1,len(rows)-.3,color='#3b73a8',lw=1,ls='--');ax.hlines(49.50,pos['2026-10-15'],len(rows)-.3,color='#b38631',lw=1,ls=':')
ax.annotate('9/17 原高47.35\n3%於9/23確認',xy=(x1,47.35),xytext=(x1-38,49.1),fontsize=11,color='#315b80',arrowprops={'arrowstyle':'-','color':'#8b9caa'})
ax.annotate('10/1 原低44.20\n3%於10/7確認',xy=(pos['2026-10-01'],44.20),xytext=(pos['2026-10-01']-44,40.4),fontsize=11,color='#315b80',arrowprops={'arrowstyle':'-','color':'#8b9caa'})
ax.annotate('10/15、16整根日K\n皆在47.35上方',xy=(pos['2026-10-15'],48),xytext=(x1-36,45.2),fontsize=11,color='#315b80',arrowprops={'arrowstyle':'-','color':'#8b9caa'})
ax.plot(len(rows)-1,49.95,'o',mfc='white',mec='#b38631',ms=5)
ax.text(.98,.93,'保存收49.15\n當日高49.95未確認',transform=ax.transAxes,ha='right',va='top',fontsize=10,color='#835d18')
av.bar(range(len(rows)),[float(r['bar']['volume_shares_scaled'])/1e6 for r in rows],color=colors,width=.65);av.set_ylabel('量／百萬股')
for key,co in [('dif','#487bb6'),('dea','#ba8d35')]:am.plot([None if r['macd'][key]is None else float(r['macd'][key])for r in rows],color=co,lw=.9,label='原'+key.upper())
hh=[(i,float(r['macd']['histogram']))for i,r in enumerate(rows)if r['macd']['histogram']is not None];am.bar([i for i,v in hh],[v for i,v in hh],width=.65,color=['#bf4141' if v>=0 else '#188265'for i,v in hh],alpha=.65);am.axhline(0,color='#777',lw=.6);am.set_ylabel('原MACD');am.legend(loc='upper left',ncol=2,frameon=False,fontsize=9)
ticks=[0]+[i for i,d in enumerate(dates)if i and d[:7]!=dates[i-1][:7]]+[len(rows)-1];ticks=[i for i in ticks if i==len(rows)-1 or i<len(rows)-10];am.set_xticks(ticks,[dates[i]for i in ticks],fontsize=9)
for aa in [ax,av,am]:aa.grid(axis='y',alpha=.15);aa.set_xlim(-1,len(rows)+1)
ax.tick_params(labelbottom=False);av.tick_params(labelbottom=False)
fig.text(.065,.945,'2884｜這一段能否辨認成整理區間後向上離開？',fontsize=22,weight='bold',color='#233d57')
fig.text(.065,.895,'第1、2頁保留五年／兩年背景。本頁2026/5至10月全部115筆原K量、MA、MACD，沒有重算。',fontsize=12)
fig.text(.065,.19,'原值：10/15低47.60、收48.80；10/16低48.00、收49.15，都在9/17高47.35之上。',fontsize=12)
fig.text(.065,.15,'同時保留：10/16高49.95超過前日高49.50，但收盤49.15沒有過49.50；不同參照答案不同。',fontsize=12)
fig.text(.065,.105,'待判：9月至10月的反覆已可看成整理區間，還是只算上漲途中回檔、尚不足成區間？',fontsize=13,weight='bold',color='#315b80')
fig.text(.065,.06,'凍結至2026-10-16，非即時行情。44.20／47.35只作明示觀察參照，非正式區界；不推日內次序或買賣資格。',fontsize=10)
fig.text(.065,.032,'Raw公司行動／歷史可得未核；原轉折與49.95未確認分開。primary_pressure_id=null，historical_signal_eligible=false。',fontsize=10)
fig.savefig(tmp/'recent-case.pdf');fig.savefig(out/'2884-rising-case.png',dpi=150);plt.close(fig)
w=PdfWriter();w.add_page(old.pages[0]);w.add_page(old.pages[1]);w.add_page(PdfReader(tmp/'recent-case.pdf').pages[0]);w.add_metadata({'/Title':'M1 2884 Rising Interval - Real Broad Context and Pending Visual Judgment','/Subject':'Qualitative interval question only; no automatic classification or trading approval.'});final=pd/'m1-2884-rising-interval.pdf'
with final.open('wb')as f:w.write(f)
r=PdfReader(final);assert len(r.pages)==3
for i in [0,1]:assert r.pages[i].get_contents().get_data()==old.pages[i].get_contents().get_data() and [im.data for im in r.pages[i].images]==[im.data for im in old.pages[i].images]
assert len(r.pages[2].extract_text())>200
v=json.loads((out/'verification.json').read_text());v.update({'PDF_pages':3,'prior_five_year_two_year_page_content_streams_images':'PASS_EXACT_UNCHANGED_NO_REDRAW','new_page_original_records':len(rows),'new_page_text_extract':'PASS_OVER_200_CHARACTERS','final_PDF_sha256':hashlib.sha256(final.read_bytes()).hexdigest(),'PDF_QA':'PENDING_RENDER_INSPECTION'})
(out/'verification.json').write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n');print(final)
