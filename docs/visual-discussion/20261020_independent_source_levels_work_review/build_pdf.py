"""Read-only chart of frozen original bars/MA/MACD; no recognition engine imports."""
from pathlib import Path
import json,os
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib import font_manager
from matplotlib.patches import Rectangle
from matplotlib.backends.backend_pdf import PdfPages
ROOT=Path(__file__).parent
font=Path(os.environ.get('M1_RESEARCH_FONT',str(ROOT.parent/'version-continuity-review/research-font.otf')))
font_manager.fontManager.addfont(str(font))
plt.rcParams.update({'font.family':font_manager.FontProperties(fname=str(font)).get_name(),'pdf.fonttype':3,'axes.unicode_minus':False,'font.size':10})
s=json.loads((ROOT/'source-data-2884.json').read_text()); e=json.loads((ROOT/'evidence.json').read_text())
bars=s['bars']; dates=[b['date'] for b in bars]; out=ROOT/'output/pdf';out.mkdir(parents=True,exist_ok=True)
def val(v):return None if v is None else float(v)
def chart(start,title,subtitle,name,detail=False):
 ids=[i for i,d in enumerate(dates) if d>=start]; a=ids[0];n=len(ids)
 fig=plt.figure(figsize=(17,11)); gs=fig.add_gridspec(3,1,height_ratios=[5.7,1.6,1.7],left=.065,right=.96,bottom=.14,top=.84,hspace=.08)
 ax=fig.add_subplot(gs[0]);vol=fig.add_subplot(gs[1],sharex=ax);mac=fig.add_subplot(gs[2],sharex=ax)
 for j,i in enumerate(ids):
  b=bars[i];o,h,l,c=[float(b[k]) for k in ['open','high','low','close']];co='#be3434' if c>=o else '#208864'
  ax.vlines(j,l,h,color=co,lw=.55 if n>500 else .9)
  ax.add_patch(Rectangle((j-.32,min(o,c)),.64,max(abs(c-o),.025),facecolor=co,edgecolor=co,lw=.3))
  vol.bar(j,float(b['volume_shares_scaled'])/1e6,color=co,width=.7)
 for key,co in zip(['5','20','60','130','260'],['#c39600','#407cc4','#9960ad','#d17c44','#707070']):
  arr=s['moving_averages'].get(key,s['moving_averages'].get('MA'+key))
  if arr is not None:ax.plot(range(n),[val(arr[i]) for i in ids],lw=.8,color=co,label='MA'+key)
 for k,co in [('dif','#476ba2'),('dea','#ba8644')]:mac.plot(range(n),[val(s['macd'][i][k])for i in ids],lw=.8,color=co,label=k.upper())
 hh=[(j,val(s['macd'][i]['histogram']))for j,i in enumerate(ids) if s['macd'][i]['histogram'] is not None]
 mac.bar([x[0]for x in hh],[x[1]for x in hh],color=['#be3434' if x[1]>=0 else '#208864' for x in hh],width=.7,alpha=.65)
 mac.axhline(0,color='#888',lw=.5)
 if detail:
  # All source lines begin when their own values are knowable; none are formal representatives.
  specs=[('2026-08-12',39.10,'原箱研究上界39.10（非正式代表）','#8874a2'),('2026-09-23',47.35,'已確認高轉折47.35','#4876a2'),('2026-10-15',49.50,'前日Raw高49.50','#b27a26')]
  for date,y,label,co in specs:
   x=dates.index(date)-a
   ax.hlines(y,max(0,x),n-.3,color=co,lw=1,linestyle='--')
   ax.plot(max(0,x),y,'o',ms=3,color=co)
   if y<49:ax.text(max(0,x)-n*.01,y+.5,label,ha='right',color=co,fontsize=9)
  ax.plot(n-1,49.95,'o',mfc='white',mec='#b27a26',ms=6)
  ax.annotate('10/16 H49.95：未確認極值',xy=(n-1,49.95),xytext=(n*.52,53),arrowprops={'arrowstyle':'-','color':'#777'},fontsize=10)
  ax.annotate('C49.15 < 前日H49.50',xy=(n-1,49.15),xytext=(n*.53,50.8),arrowprops={'arrowstyle':'-','color':'#777'},fontsize=10)
  ax.set_ylim(top=55)
 ax.axhline(49.15,lw=.8,color='#222',linestyle=':',label='保存收盤49.15')
 ax.legend(loc='upper left',ncol=6,fontsize=8,frameon=False)
 ax.set_ylabel('Raw價格');vol.set_ylabel('量／百萬股');mac.set_ylabel('原MACD')
 ticks=list(range(0,n,max(1,n//8)));ticks=[x for x in ticks if x<n-1-n*.065]+[n-1]
 mac.set_xticks(ticks,[dates[a+x]for x in ticks],fontsize=8)
 for aa in [ax,vol,mac]:aa.grid(axis='y',alpha=.15);aa.set_xlim(-1,n+max(2,n*.005))
 ax.tick_params(labelbottom=False);vol.tick_params(labelbottom=False);mac.legend(loc='upper left',ncol=2,fontsize=8,frameon=False)
 fig.text(.065,.94,title,fontsize=21,weight='bold');fig.text(.065,.895,subtitle,fontsize=11)
 fig.text(.065,.075,'凍結資料至2026-10-16；非即時行情。1213筆原來源；未重算核心、均線或MACD。原暖機空值保留。',fontsize=10)
 fig.text(.065,.045,'Raw跨年公司行動未核、五年Adjusted缺；待核日期不補交易日。收盤、日高與確認轉折分開，OHLC不證日內先後。',fontsize=10)
 fig.savefig(ROOT/name,dpi=150);return fig
with PdfPages(out/'m1-independent-source-levels.pdf') as pdf:
 f=chart('2021-01-01','2884｜五年完整保存背景','全部1213筆；先看長背景，再核對來源層級。跨年Raw僅研究，不據此排序不同股票壓力。','2884-full-context.png');pdf.savefig(f);plt.close(f)
 f=chart('2024-10-01','2884｜兩年背景與最新來源差別','原34箱研究上界全低於保存收盤；這只說明原箱候選的相對位置，不代表其他來源或正式壓力為零。','2884-recent-context.png',True);pdf.savefig(f);plt.close(f)
 f=plt.figure(figsize=(17,11));f.patch.set_facecolor('white')
 f.text(.065,.92,'沒有上方箱候選，不等於已完成正式壓力判斷',fontsize=23,weight='bold')
 rows=[['來源層','本例原值／原狀態','能說什麼；不能自動推出什麼'],['原K線','10/15 H49.50；10/16 H49.95、C49.15','日高有越過前高，收盤沒有；不推日內回測先後。'],['已確認轉折','最高原確認高轉折47.35；9/23確認','確認時間與發生日分開；不指定正式整體代表。'],['未確認極值','10/16 H49.95：UNCONFIRMED_NOT_A_PIVOT','不是已確認轉折；不得倒填歷史訊號。'],['原箱研究範圍','34箱上界最高39.10，均低於49.15','上方可比0／前緣0只限原箱候選；不等於風險或來源為0。'],['正式整體／主壓力','primary_pressure_id=null','沒有新增人工歸屬、解除、重要性排序或買賣資格。']]
 ax=f.add_axes([.065,.43,.89,.40]);ax.axis('off');tab=ax.table(cellText=rows[1:],colLabels=rows[0],colWidths=[.14,.32,.54],cellLoc='left',bbox=[0,0,1,1]);tab.auto_set_font_size(False);tab.set_fontsize(10)
 for (r,c),cell in tab.get_celld().items():cell.set_edgecolor('#d6dce4');cell.set_facecolor('#e9eff6' if r==0 else ('#f6f8fa' if r%2 else 'white'));cell.PAD=.06
 lines=['同尺度來源核對：B11是B12前綴；B13是B12後綴且研究幾何相同。它們不是獨立投票。',
 'B12與B14只共用5/28低點；共點不等於完整路徑承接，更不自動確定整體成員或生命階段。',
 '本例沒有原人工形態標籤；不能用2884替已確認的1101 ABC案例補一套自動分類答案。',
 '原畫面已限定「上方可比0／研究前緣0／唯一主壓力未定」；未發現需要重做工具的工程缺陷。',
 '本輪：讀原15個預存結果、核來源與確認日、製作靜態研究圖。沒有重跑15次核心或舊60次前綴驗收。',
 '歷史實際選取時間未核；historical_signal_eligible=false。Raw待核日曆非窮盡，Android未驗新建置。']
 for j,line in enumerate(lines):f.text(.065,.36-j*.045,line,fontsize=11)
 f.text(.065,.045,'研究結論：來源層級不可互相代替。本輪不新增問題、不調參、不宣稱正式歸屬或解除。',fontsize=12,weight='bold')
 pdf.savefig(f);plt.close(f)
print(out/'m1-independent-source-levels.pdf')
