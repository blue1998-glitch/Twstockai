"""Two vector pages: full B context, then same-axis same-level identity proposals."""
import json,os
from datetime import date
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle
from matplotlib.font_manager import FontProperties
from matplotlib.ticker import FormatStrFormatter
from matplotlib.backends.backend_pdf import PdfPages
from pypdf import PdfReader
from study import ROOT,SOURCE,EXPECTED_SOURCE,sha

def six_months(a,b):
 a,b=date.fromisoformat(a),date.fromisoformat(b);m=(b.year-a.year)*12+b.month-a.month
 return m>6 or(m==6 and b.day>=a.day)

def main():
 assert sha(SOURCE)==EXPECTED_SOURCE
 src=json.loads(SOURCE.read_text());data=json.loads((ROOT/'study-inputs.json').read_text());zones=list(data['zones'].values())
 font=FontProperties(fname=os.environ.get('CONTRAST_FONT','/workspace/scratch/54685b8dac93/version-continuity-review/research-font.otf'))
 out=ROOT/'output/pdf';tmp=ROOT/'tmp/pdfs';out.mkdir(parents=True,exist_ok=True);tmp.mkdir(parents=True,exist_ok=True)
 final=out/'b-same-level-review.pdf';staged=tmp/'b-same-level-review.pdf';colors=['#477a9b','#a67d39','#80649a']
 broad=[b for b in src['bars']if '2024-10-01'<=b['date']<='2026-05-29'];detail=[b for b in src['bars']if '2025-09-01'<=b['date']<='2026-05-29']
 for bs in (broad,detail):assert six_months(bs[0]['date'],bs[-1]['date'])
 limits=(min(float(b['low'])for b in detail)-.65,max(float(b['high'])for b in detail)+.85)
 def label(fig,x,y,t,size=12,c='#253950'):fig.text(x,y,t,fontproperties=font,fontsize=size,color=c)
 def draw(ax,bs,vol=None,proposal=None):
  dates=[b['date']for b in bs];ix={d:i for i,d in enumerate(dates)}
  for i,b in enumerate(bs):
   o,h,l,c=map(float,[b[k]for k in ('open','high','low','close')]);col='#c34848'if c>=o else'#16856c'
   ax.vlines(i,l,h,color=col,lw=.8);ax.add_patch(Rectangle((i-.29,min(o,c)),.58,max(abs(c-o),.012),facecolor=col,edgecolor=col,lw=.25,zorder=3))
   if vol is not None:vol.bar(i,int(b['volume_shares_scaled'])/1e6,color=col,width=.65)
  for j,z in enumerate(zones):
   left=ix[z['path_start']];right=ix[z['path_end']];lo,hi=map(float,[z['raw_path_frame']['observed_low'],z['raw_path_frame']['observed_high']])
   if proposal!='together':
    ax.add_patch(Rectangle((left-.4,lo),right-left+.8,hi-lo,facecolor=colors[j],edgecolor=colors[j],alpha=.12,lw=1,zorder=1))
    cl,ch=map(float,[z['common_close_low'],z['common_close_high']]);ax.add_patch(Rectangle((left-.4,cl),right-left+.8,ch-cl,facecolor=colors[j],edgecolor=colors[j],alpha=.35,zorder=2))
   if bs is detail:ax.text((left+right)/2,limits[1]-.28,str(j+1),fontproperties=font,fontsize=11,ha='center',color=colors[j],bbox={'boxstyle':'circle,pad=.15','facecolor':'white','edgecolor':colors[j],'lw':.6})
  if proposal=='together':
   left=ix[zones[0]['path_start']];right=ix[zones[-1]['path_end']];lo=min(float(z['raw_path_frame']['observed_low'])for z in zones);hi=max(float(z['raw_path_frame']['observed_high'])for z in zones)
   ax.add_patch(Rectangle((left-.4,lo),right-left+.8,hi-lo,facecolor='#698da0',edgecolor='#52788b',alpha=.13,lw=1.2,zorder=1))
  ki=ix['2026-01-02'];ax.fill_between([ki,len(bs)],[33.75,33.75],[33.85,33.85],color='#ac8945',alpha=.15,zorder=0)
  ax.text(1.004,33.80,'33.75 - 33.85',transform=ax.get_yaxis_transform(),fontproperties=font,fontsize=9,color='#97773a',va='center')
  # Later context is visible for the broad manual reading, never backfilled into March6 evidence.
  ci=ix['2026-03-06'];ax.axvspan(ci+.5,len(bs),color='#a4adb8',alpha=.045,zorder=0)
  for gap in src['source_gaps']['known_calendar_missing_dates']:
   if dates[0]<gap<dates[-1]:ax.axvline(next(i for i,d in enumerate(dates)if d>gap)-.5,color='#c99b39',alpha=.3,lw=.7)
  ax.set_xlim(-1,len(bs));ax.set_ylabel('Raw價格',fontproperties=font,fontsize=10);ax.yaxis.set_major_formatter(FormatStrFormatter('%.2f'))
  if bs is detail:ax.set_ylim(*limits)
  ticks=sorted({round(i*(len(bs)-1)/7)for i in range(8)})
  if vol is None:ax.set_xticks(ticks,[dates[i]for i in ticks],fontsize=9)
  else:ax.tick_params(labelbottom=False);vol.set_xticks(ticks,[dates[i]for i in ticks],fontsize=9);vol.set_ylabel('量／百萬股',fontproperties=font,fontsize=10)
  for ar in [ax]+([vol]if vol is not None else[]):
   ar.grid(axis='y',color='#d7dfe8',lw=.5);ar.set_axisbelow(True)
   for sp in ('top','right'):ar.spines[sp].set_visible(False)
  return ix
 pages=[]
 with PdfPages(staged)as pdf:
  fig=plt.figure(figsize=(20,14),facecolor='white')
  label(fig,.06,.96,'B｜沒收在共同價位內，也可能已從兩側跨過',22)
  label(fig,.06,.925,'B大帶內有多個小帶已答保持；1／2／3只定位三組來源，尚不是三個已核小帶。',12)
  label(fig,.06,.884,'大背景｜2024/10 - 2026/5；先看全貌，再看十二月底、二月與三月初。',12)
  ax=fig.add_axes([.06,.635,.86,.22]);draw(ax,broad)
  label(fig,.06,.588,'細看來源｜2025/9 - 2026/5；淡框是來源高低，深條是共同價位；3/6右方僅事後背景。',12)
  detailax=fig.add_axes([.06,.345,.86,.217]);vol=fig.add_axes([.06,.239,.86,.062],sharex=detailax);ix=draw(detailax,detail,vol)
  for d,note,pos in [('2026-02-10','2/10 C33.80：收在區內',(.31,.85)),('2026-03-04','3/4收33.65下；3/5收34.05上',(.54,.51))]:
   b=next(b for b in detail if b['date']==d);detailax.scatter([ix[d]],[float(b['close'])],s=24,color='#293f58',zorder=7);detailax.annotate(note,(ix[d],float(b['close'])),xytext=pos,textcoords='axes fraction',fontproperties=font,fontsize=11,arrowprops={'arrowstyle':'-','color':'#73849c'},bbox={'facecolor':'white','edgecolor':'#c8d1dc','pad':3})
  for y,t in [(.174,'1｜12/22 - 12/31，1/2才知：共同33.75 - 33.85；來源32.75 - 34.15。'),(.138,'2｜2/2 - 2/23，2/24才知：9筆來源中，只有2/10收盤落在舊共同價位內。'),(.102,'3｜2/26 - 3/5，3/6才知：5筆來源都未收在舊區內；3/4、3/5兩日K卻皆觸及，收盤先下再上。')]:label(fig,.06,y,t,12)
  label(fig,.06,.042,'來源交疊、收盤停留、異側收盤跨越分開保存；不由日K推日內順序或連續成交。正式合併仍待判。',10,'#63758a');label(fig,.94,.025,'1/2',10)
  png=ROOT/'b-source-contrast.png';fig.savefig(png,dpi=145);pdf.savefig(fig);plt.close(fig);pages.append({'page':1,'png':png.name,'png_sha256':sha(png),'windows':[[broad[0]['date'],broad[-1]['date']],[detail[0]['date'],detail[-1]['date']]],'saved_bars':[len(broad),len(detail)]})
  fig=plt.figure(figsize=(20,14),facecolor='white')
  label(fig,.06,.96,'同一大帶內，這三組活動要如何保留身份？',22)
  label(fig,.06,.925,'本頁兩圖使用完全相同K線、時間及價格座標，只比較同層身份；不重問B大小帶包含關係。',12)
  label(fig,.06,.878,'讀法甲｜合看同一個小帶的多次活動，仍保留每段來源。',14)
  top=fig.add_axes([.06,.66,.86,.19]);draw(top,detail,proposal='together')
  label(fig,.06,.595,'讀法乙｜大帶內分別保留小帶候選；不因價位交疊就合成同一小帶。',14)
  bottom=fig.add_axes([.06,.376,.86,.19]);vol2=fig.add_axes([.06,.264,.86,.063],sharex=bottom);draw(bottom,detail,vol2,proposal='separate')
  assert top.get_xlim()==bottom.get_xlim()and top.get_ylim()==bottom.get_ylim()
  label(fig,.06,.192,'來源定位：1＝2025/12/22 - 12/31；2＝2026/2/2 - 2/23；3＝2026/2/26 - 3/5。',12)
  label(fig,.06,.148,'兩種都只是待比較提案；框只示觀察範圍，不預設正式起末價界，也不強制恰好三個帶。',12)
  label(fig,.06,.104,'也可以判斷：這些只是大帶內的小波動，目前不值得另分小帶；或直接調整你認為適當的範圍。',12)
  label(fig,.06,.042,'所有主圖至少六個月；這是本輪唯一新核心問題，尚無使用者新答案或正式合併標籤。',10,'#63758a');label(fig,.94,.025,'2/2',10)
  png=ROOT/'b-same-level-proposals.png';fig.savefig(png,dpi=145);pdf.savefig(fig);plt.close(fig);pages.append({'page':2,'png':png.name,'png_sha256':sha(png),'windows':[[detail[0]['date'],detail[-1]['date']]]*2,'saved_bars':[len(detail)]*2,'proposal_axes_identical':True,'same_OHLCV_in_both_proposals':True,'proposal_ylim':list(limits)})
 reader=PdfReader(staged);assert len(reader.pages)==2 and all(len(p.images)==0 for p in reader.pages);assert staged.read_bytes().rstrip().endswith(b'%%EOF');staged.replace(final)
 manifest={'pages':pages,'pdf':str(final.relative_to(ROOT)),'pdf_sha256':sha(final),'vector_pages':2,'image_objects':0,'all_main_windows_at_least_six_months':True,'atomic_replace_after_structure_check':True}
 (ROOT/'figure-manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n');print(json.dumps(manifest,ensure_ascii=False,indent=2))
if __name__=='__main__':main()
