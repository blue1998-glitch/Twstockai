"""Three vector pages, each with broad context plus at least six-month detail."""
from pathlib import Path
from datetime import date
import json,os,hashlib
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle
from matplotlib.font_manager import FontProperties
from matplotlib.ticker import FormatStrFormatter
from matplotlib.backends.backend_pdf import PdfPages
from pypdf import PdfReader
from study import ROOT,SOURCES,EXPECTED,sha

DISPLAY={
 'G2':{'code':'1101','broad':'2022-01-03','detail':'2023-01-03','end':'2023-08-02','title':'G2｜局部收回後守在上方，仍未到較早活動',
 'sub':'原G2人工範圍2023/1/16 - 8/16保持；本頁後續證據只到8/2，避免跨越8/3原缺日。',
 'detail_note':'37.15原低參照；38.05 - 38.25較早共同區7/7才知。兩者分開看。',
 'origins':[('2023-07-10','7/10收下'),('2023-07-25','7/25收回上')],
 'notes':['7/10收下後，7/13影線越過仍收下；7/25重新收上，當時即可更新目前位置。',
 '7/25之後6筆全收上；7/28低穿後收上，7/31及8/2低點恰等37.15，兩種接觸分開保存。',
 '同期最高37.80仍低於38.05：支持局部收回，不能連帶認定較早區已收復或整體G2恢復。']},
 'ABC':{'code':'1101','broad':'2024-01-02','detail':'2024-12-02','end':'2025-06-12','title':'ABC｜收破後持續在下，補強向下離開的證據',
 'sub':'原ABC為2025/4/7 - 6/2共39筆；之後8筆另作後續，不延長原人工範圍。',
 'detail_note':'28.45是4/8原低；較早活動共同30.55 - 30.60於5/13可知，未升正式帶界。',
 'origins':[('2025-06-02','6/2收破')],
 'notes':['6/2 C27.70已低於28.45，當日H29.05仍跨含；6/3起後續8筆整根都在28.45下。',
 '6/12才有新的下方完成活動；6/2已收破的價格事實不必等它，原39筆身份保持。',
 '截至6/12尚無收復，支持下移的閱讀；這不是永久失敗、做空資格或已核正式大結構終點。']},
 'A':{'code':'2884','broad':'2025-01-02','detail':'2026-04-01','end':'2026-10-16','title':'A｜上越後已有續行，但後續資料目前只有一筆',
 'sub':'原A「上漲、短暫整理、再上漲」及10/7足夠辨認保持；本輪只對照既有上越後續。',
 'detail_note':'47.35為9/17原高，9/23原標記可知；與較早來源raw上緣同源，不重複計票。',
 'origins':[('2026-10-15','10/15上越')],
 'notes':['10/15 L47.60、C48.80在47.35上；10/16 L48.00、C49.15也在上，已有一筆續行證據。',
 '尚未觀察到返回路徑；只有一筆後續，不把「沒回測」充當已驗證回測守穩。',
 '價格已上越可立即更新問題；觀察仍開放，不用B的14筆或G2的6筆替A補證據。']}}

def at_least_six_months(start,end):
 a,b=date.fromisoformat(start),date.fromisoformat(end)
 return (b.year-a.year)*12+b.month-a.month>=6 and ((b.year-a.year)*12+b.month-a.month>6 or b.day>=a.day)

def main():
 data=json.loads((ROOT/'study-inputs.json').read_text());font=FontProperties(fname=os.environ.get('FOLLOWUP_FONT','/workspace/scratch/54685b8dac93/version-continuity-review/research-font.otf'))
 sources={k:json.loads(p.read_text())for k,p in SOURCES.items()}
 for k,p in SOURCES.items():assert sha(p)==EXPECTED[k]
 out=ROOT/'output/pdf';tmp=ROOT/'tmp/pdfs';out.mkdir(parents=True,exist_ok=True);tmp.mkdir(parents=True,exist_ok=True)
 target=out/'cross-case-followup-review.pdf';staged=tmp/'cross-case-followup-review.pdf';manifest=[]
 with PdfPages(staged)as pdf:
  for page,(case,cfg)in enumerate(DISPLAY.items(),1):
   src=sources[cfg['code']];fig=plt.figure(figsize=(20,14),facecolor='white')
   def label(x,y,t,size=12,color='#253950'):fig.text(x,y,t,fontproperties=font,fontsize=size,color=color)
   label(.06,.957,cfg['title'],22);label(.06,.922,cfg['sub'],12)
   label(.06,.878,'大背景｜'+cfg['broad']+' - '+cfg['end']+'  保存Raw日K',12)
   label(.06,.537,'細看後續｜'+cfg['detail_note'],12)
   broad=fig.add_axes([.06,.595,.88,.255]);detail=fig.add_axes([.06,.30,.88,.205]);vol=fig.add_axes([.06,.18,.88,.075],sharex=detail)
   queries=[q for q in data['queries']if q['case']==case];ref=queries[0]['reference'];p=float(ref['price'])
   zones=[data['G2_earlier_zones']['earlier-local']]if case=='G2'else[data[case+'_earlier_zone']]
   counts=[];windows=[]
   for ar,start in ((broad,cfg['broad']),(detail,cfg['detail'])):
    bs=[b for b in src['bars']if start<=b['date']<=cfg['end']];dates=[b['date']for b in bs];ix={d:i for i,d in enumerate(dates)}
    assert at_least_six_months(dates[0],dates[-1]);counts.append(len(bs));windows.append([dates[0],dates[-1]])
    for i,b in enumerate(bs):
     o,h,l,c=[float(b[k])for k in ('open','high','low','close')];color='#c34848'if c>=o else'#16856c'
     ar.vlines(i,l,h,color=color,lw=.8);ar.add_patch(Rectangle((i-.29,min(o,c)),.58,max(abs(c-o),.012),facecolor=color,edgecolor=color,lw=.3))
     if ar==detail:vol.bar(i,int(b['volume_shares_scaled'])/1e6,color=color,width=.65)
    known=next((i for i,d in enumerate(dates)if d>=ref['known_on']),None)
    if known is not None:ar.hlines(p,known-.4,len(bs),color='#6c5b99',lw=1.3,ls='--')
    ar.text(1.006,p,ref['price'],transform=ar.get_yaxis_transform(),fontproperties=font,fontsize=11,color='#6c5b99',va='center')
    for z in zones:
     lo,hi=map(float,[z['common_close_low'],z['common_close_high']]);l=ix[z['path_start']];r=ix[z['path_end']]
     ar.add_patch(Rectangle((l-.4,lo),r-l+.8,max(hi-lo,.012),facecolor='#3b7499',edgecolor='#3b7499',alpha=.25,zorder=1))
     if case=='G2':
      ki=ix[z['known_on_saved_bar']];ar.fill_between([ki,len(bs)],[lo,lo],[hi,hi],color='#d3a452',alpha=.18)
      if ar==detail:ar.text(.02,.90,'較早共同區38.05 - 38.25',transform=ar.transAxes,fontproperties=font,fontsize=11,color='#947037')
    for j,(d,caption)in enumerate(cfg['origins']):
     i=ix[d];b=bs[i];y=float(b['close']);ar.scatter([i],[y],s=24,color='#293f58',zorder=6)
     if ar==detail:ar.annotate(caption,(i,y),xytext=(.50+j*.25,.86-j*.22),textcoords='axes fraction',fontproperties=font,fontsize=11,color='#293f58',arrowprops={'arrowstyle':'-','color':'#73849c'},bbox={'boxstyle':'round,pad=.25','facecolor':'white','edgecolor':'#bec9d4','lw':.6})
    if case=='G2'and ar==detail:
     for d in ('2023-07-28','2023-07-31','2023-08-02'):
      b=bs[ix[d]];ar.scatter([ix[d]],[float(b['low'])],s=55,facecolors='none',edgecolors='#326c9e',lw=1.2,zorder=6)
    for gap in src['source_gaps']['known_calendar_missing_dates']:
     if dates[0]<gap<dates[-1]:
      i=next(i for i,d in enumerate(dates)if d>gap);ar.axvline(i-.5,color='#d8a840',alpha=.3,lw=.7)
    ar.margins(y=.13);ar.set_xlim(-1,len(bs));ar.yaxis.set_major_formatter(FormatStrFormatter('%.2f'));ar.set_ylabel('Raw價格',fontproperties=font,fontsize=10)
    ticks=sorted({round(i*(len(bs)-1)/7)for i in range(8)})
    if ar==broad:ar.set_xticks(ticks,[dates[i]for i in ticks],fontsize=9)
    else:vol.set_xticks(ticks,[dates[i]for i in ticks],fontsize=9);ar.tick_params(labelbottom=False)
   vol.set_ylabel('量／百萬股',fontproperties=font,fontsize=10)
   for ar in (broad,detail,vol):
    ar.grid(axis='y',color='#d7dfe8',lw=.5);ar.set_axisbelow(True)
    for spine in ('top','right'):ar.spines[spine].set_visible(False)
   for j,note in enumerate(cfg['notes']):label(.06,.131-j*.027,note,12)
   label(.06,.025,'共同區是來源幾何，非正式帶界；保存筆數非門檻。Raw公司行動／完整日曆／歷史公開可得限制保持。',10,'#64768a')
   label(.924,.025,str(page)+'/3',10)
   png=ROOT/(case.lower()+'-followup-context.png');fig.savefig(png,dpi=145,facecolor='white');pdf.savefig(fig);plt.close(fig)
   manifest.append({'case':case,'main_windows':windows,'saved_bars':counts,'all_main_charts_at_least_six_months':True,'png':png.name,'png_sha256':sha(png)})
 check=PdfReader(staged);assert len(check.pages)==3 and all(len(p.images)==0 for p in check.pages)
 assert staged.read_bytes().rstrip().endswith(b'%%EOF')
 staged.replace(target)
 (ROOT/'figure-manifest.json').write_text(json.dumps({'pages':manifest,'pdf':str(target.relative_to(ROOT)),'pdf_sha256':sha(target),'vector_pages':3,'image_objects':0,'new_builder_runs':1,'atomic_replace_after_structure_check':True},ensure_ascii=False,indent=2)+'\n')
 print(json.dumps({'pdf_sha256':sha(target),'pages':manifest},ensure_ascii=False,indent=2))
if __name__=='__main__':main()
