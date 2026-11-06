"""Broad-to-detail vector comparison of activity source ranges and common spans."""
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
from study import ROOT,SOURCE_PATHS,EXPECTED,sha

CFG={
 'B':{'code':'2884','broad':'2025-01-02','detail':'2025-10-17','end':'2026-06-30','names':['B_advance','B_high','B_return'],'title':'B｜同一推進與返回歷程，三段來源仍分別保留',
 'sub':'承接已答大小帶包含關係；本頁三段是保存局部活動，不追認為已核小帶或三次獨立反應。',
 'rowlabels':['推進','高位','返回'],'rows':['33.20上：7筆','35.50：2上1等1下','35.50：2上2下'],
 'notes':['共同價位上移後回落，可以連看推進／返回；相鄰段共形成轉折，不能用三個框當三次測試。',
 '6/26才可知最後一段時，C34.55已低於其來源範圍34.90 - 36.60；活動形成與現價位置分開。']},
 'G2':{'code':'1101','broad':'2022-01-03','detail':'2023-01-03','end':'2023-08-02','names':['G_earlier','G_lower','G_rebound'],'title':'G2｜已回到較早來源範圍，尚未到共同價位',
 'sub':'更正「未到較早活動」的過廣表述：未到的是共同價位，並非整個來源價格範圍。原G2人工範圍不改。',
 'rowlabels':['較早','下移','回升'],'rows':['37.15上：7筆','37.15下：3筆','37.15上：4筆'],
 'notes':['回升段4筆收盤全在較早來源37.20 - 38.50內，但沒有一筆日高到38.05 - 38.25共同價位。',
 '後段完整來源晚於前段可知日，支持新的局部回升；這不等於統計獨立、正式帶合併或整體恢復。']}}
COLORS=['#477a9b','#b88738','#86659a']
def six_months(a,b):
 a,b=date.fromisoformat(a),date.fromisoformat(b);m=(b.year-a.year)*12+b.month-a.month
 return m>6 or(m==6 and b.day>=a.day)
def main():
 data=json.loads((ROOT/'study-inputs.json').read_text());sources={k:json.loads(p.read_text())for k,p in SOURCE_PATHS.items()}
 for k,p in SOURCE_PATHS.items():assert sha(p)==EXPECTED[k]
 font=FontProperties(fname=os.environ.get('BRIDGE_FONT','/workspace/scratch/54685b8dac93/version-continuity-review/research-font.otf'))
 out=ROOT/'output/pdf';tmp=ROOT/'tmp/pdfs';out.mkdir(parents=True,exist_ok=True);tmp.mkdir(parents=True,exist_ok=True)
 staged=tmp/'activity-bridge-review.pdf';target=out/'activity-bridge-review.pdf';manifest=[]
 with PdfPages(staged)as pdf:
  for page,(case,cfg)in enumerate(CFG.items(),1):
   fig=plt.figure(figsize=(20,14),facecolor='white');src=sources[cfg['code']]
   def label(x,y,t,size=12,c='#253950'):fig.text(x,y,t,fontproperties=font,fontsize=size,color=c)
   label(.06,.959,cfg['title'],22);label(.06,.927,cfg['sub'],12)
   label(.06,.894,'大背景｜'+cfg['broad']+' - '+cfg['end']+'；原始保存日K',12)
   label(.06,.650,'細看來源｜淡色外框＝來源高低範圍；深色短條＝共同價位，兩者均非正式帶界。',12)
   broad=fig.add_axes([.06,.705,.88,.165]);detail=fig.add_axes([.06,.417,.88,.21]);vol=fig.add_axes([.06,.31,.88,.063],sharex=detail)
   windows=[];counts=[]
   for ax,start in ((broad,cfg['broad']),(detail,cfg['detail'])):
    bs=[b for b in src['bars']if start<=b['date']<=cfg['end']];dates=[b['date']for b in bs];ix={d:i for i,d in enumerate(dates)}
    assert six_months(dates[0],dates[-1]);windows.append([dates[0],dates[-1]]);counts.append(len(bs))
    for i,b in enumerate(bs):
     o,h,l,c=map(float,[b[k]for k in ('open','high','low','close')]);color='#c34848'if c>=o else'#16856c'
     ax.vlines(i,l,h,color=color,lw=.75);ax.add_patch(Rectangle((i-.29,min(o,c)),.58,max(abs(c-o),.01),facecolor=color,edgecolor=color,lw=.25,zorder=3))
     if ax==detail:vol.bar(i,int(b['volume_shares_scaled'])/1e6,color=color,width=.65)
    for name,color in zip(cfg['names'],COLORS):
     z=data['zones'][name];l=ix[z['path_start']];r=ix[z['path_end']];rl,rh=map(float,[z['raw_path_frame']['observed_low'],z['raw_path_frame']['observed_high']]);cl,ch=map(float,[z['common_close_low'],z['common_close_high']])
     ax.add_patch(Rectangle((l-.42,rl),r-l+.84,rh-rl,facecolor=color,edgecolor=color,alpha=.10,lw=.9,zorder=1))
     ax.add_patch(Rectangle((l-.42,cl),r-l+.84,ch-cl,facecolor=color,edgecolor=color,alpha=.42,lw=.9,zorder=2))
    for ref in data['references'][case]:
     if ref['low']!=ref['high']:continue
     ki=next(i for i,d in enumerate(dates)if d>=ref['known_on']);p=float(ref['low']);ax.hlines(p,ki,len(bs),ls='--',color='#77668e',lw=1.0)
     ax.text(1.005,p,ref['low'],transform=ax.get_yaxis_transform(),fontproperties=font,fontsize=10,color='#77668e',va='center')
    if case=='G2':
     z=data['zones']['G_earlier'];ki=ix[z['known_on_saved_bar']]
     for lo,hi,color in [(37.20,38.50,'#477a9b'),(38.05,38.25,'#b88738')]:ax.fill_between([ki,len(bs)],[lo,lo],[hi,hi],color=color,alpha=.08 if lo==37.20 else.22,zorder=0)
     if ax==detail:
      ax.text(.02,.93,'較早來源37.20 - 38.50；共同38.05 - 38.25',transform=ax.transAxes,fontproperties=font,fontsize=11,color='#526e86')
      ax.annotate('7/25收回37.15後的活動',(ix['2023-07-25'],37.40),xytext=(.64,.72),textcoords='axes fraction',fontproperties=font,fontsize=11,arrowprops={'arrowstyle':'-','color':'#73849c'},bbox={'facecolor':'white','edgecolor':'#c8d1dc','pad':3})
    elif ax==detail:
     for d,note,pos in [('2026-06-22','6/22收過35.50',(.53,.94)),('2026-06-26','6/26確認返回段時已收34.55',(.67,.62))]:
      bar=next(b for b in bs if b['date']==d);ax.annotate(note,(ix[d],float(bar['close'])),xytext=pos,textcoords='axes fraction',fontproperties=font,fontsize=11,arrowprops={'arrowstyle':'-','color':'#73849c'},bbox={'facecolor':'white','edgecolor':'#c8d1dc','pad':3})
    for gap in src['source_gaps']['known_calendar_missing_dates']:
     if dates[0]<gap<dates[-1]:ax.axvline(next(i for i,d in enumerate(dates)if d>gap)-.5,color='#d3a13e',alpha=.3,lw=.7)
    ax.set_xlim(-1,len(bs));ax.margins(y=.14);ax.yaxis.set_major_formatter(FormatStrFormatter('%.2f'));ax.set_ylabel('Raw價格',fontproperties=font,fontsize=10)
    ticks=sorted({round(i*(len(bs)-1)/7)for i in range(8)})
    if ax==broad:ax.set_xticks(ticks,[dates[i]for i in ticks],fontsize=9)
    else:vol.set_xticks(ticks,[dates[i]for i in ticks],fontsize=9);ax.tick_params(labelbottom=False)
   vol.set_ylabel('量／百萬股',fontproperties=font,fontsize=10)
   for ax in (broad,detail,vol):
    ax.grid(axis='y',color='#d7dfe8',lw=.5);ax.set_axisbelow(True)
    for spine in ('top','right'):ax.spines[spine].set_visible(False)
   columns=[.06,.165,.36,.475,.65,.80]
   for x,t in zip(columns,['活動','來源期間','可知日','共同價位','來源高低範圍','來源內收盤概況']):label(x,.261,t,11)
   for j,(name,caption,color)in enumerate(zip(cfg['names'],cfg['rowlabels'],COLORS)):
    z=data['zones'][name];frame=z['raw_path_frame'];row=[caption,z['path_start'][5:]+' - '+z['path_end'][5:],z['known_on_saved_bar'][5:],z['common_close_low']+' - '+z['common_close_high'],frame['observed_low']+' - '+frame['observed_high'],cfg['rows'][j]]
    for x,t in zip(columns,row):label(x,.229-j*.030,t,11,color)
   for j,note in enumerate(cfg['notes']):label(.06,.105-j*.029,note,12)
   label(.06,.027,'來源期與可知日不同；框不決定正式歸屬或反應次數。Raw公司行動／完整日曆／歷史公開可得限制保持。',10,'#64768a');label(.925,.027,str(page)+'/2',10)
   png=ROOT/(case.lower()+'-activity-bridge.png');fig.savefig(png,dpi=145,facecolor='white');pdf.savefig(fig);plt.close(fig)
   manifest.append({'case':case,'windows':windows,'saved_bars':counts,'all_main_windows_at_least_six_months':True,'png':png.name,'png_sha256':sha(png)})
 reader=PdfReader(staged);assert len(reader.pages)==2 and all(len(p.images)==0 for p in reader.pages)
 assert staged.read_bytes().rstrip().endswith(b'%%EOF');staged.replace(target)
 write={'pages':manifest,'pdf':str(target.relative_to(ROOT)),'pdf_sha256':sha(target),'vector_pages':2,'image_objects':0,'atomic_replace_after_validation':True}
 (ROOT/'figure-manifest.json').write_text(json.dumps(write,ensure_ascii=False,indent=2)+'\n');print(json.dumps(write,ensure_ascii=False,indent=2))
if __name__=='__main__':main()
