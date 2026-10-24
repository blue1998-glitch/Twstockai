"""One new retrospective graphic, sourced from saved local activities only."""
import json,hashlib
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle
from matplotlib.font_manager import FontProperties
from study import ROOT,SOURCE
s=json.loads(SOURCE.read_text());c=json.loads((ROOT/'study-inputs.json').read_text());v=json.loads((ROOT/'context-views.json').read_text())
font=FontProperties(fname='/workspace/scratch/54685b8dac93/version-continuity-review/research-font.otf')
f=plt.figure(figsize=(18,14),facecolor='white')
def label(x,y,text,size=12):f.text(x,y,text,fontproperties=font,fontsize=size,color='#243449')
label(.065,.963,'收回一個參照，不等於收復較早活動或較大高點',23)
label(.065,.926,'1101／2023年 保存Raw日K。事後來源期疊圖；各活動須等標示的可知日，才可加入當日觀察。')
g=f.add_gridspec(5,1,height_ratios=[3.2,1,.7,3.2,1],left=.065,right=.965,top=.84,bottom=.25,hspace=.28)
def draw(row,start,end,title):
 bs=[b for b in s['bars']if start<=b['date']<=end];ax=f.add_subplot(g[row]);vol=f.add_subplot(g[row+1],sharex=ax)
 for i,b in enumerate(bs):
  o,h,l,cl=[float(b[k])for k in ['open','high','low','close']];color='#c44242'if cl>=o else'#168268'
  ax.vlines(i,l,h,color=color,lw=.9);ax.add_patch(Rectangle((i-.28,min(o,cl)),.56,max(abs(cl-o),.008),facecolor=color))
  vol.bar(i,int(b['volume_shares_scaled'])/1e6,color=color,width=.6)
 for a in [ax,vol]:a.set_xlim(-1,len(bs));a.grid(axis='y',alpha=.15);a.set_axisbelow(True)
 ax.tick_params(labelbottom=False);ax.set_ylabel('保存原始價格',fontproperties=font);vol.set_ylabel('量／百萬股',fontproperties=font)
 ticks=sorted({round(i*(len(bs)-1)/7)for i in range(8)});vol.set_xticks(ticks,[bs[i]['date'][5:].replace('-','/')for i in ticks])
 ax.set_title(title,fontproperties=font,fontsize=12,loc='left',pad=10)
 return ax,bs
def ix(bs,day):return next(i for i,b in enumerate(bs)if b['date']==day)
def pointline(ax,bs,key,color):
 p=c['pivots'][key];ids=[i for i,b in enumerate(bs)if b['date']>=p['known_on']]
 if ids:ax.hlines(float(p['price']),ids[0]-.4,len(bs)-.4,color=color,ls='--',lw=.9)
def zone(ax,bs,key,color,raw=False):
 z=c['zones'][key];a,b=ix(bs,z['path_start']),ix(bs,z['path_end']);lo,hi=[float(z[k])for k in ['common_close_low','common_close_high']]
 ax.add_patch(Rectangle((a-.4,lo),b-a+.8,hi-lo,facecolor=color,alpha=.25,edgecolor=color,lw=1.2,zorder=-2))
 if raw:
  low,high=[float(z['raw_path_frame'][k])for k in ['observed_low','observed_high']]
  ax.add_patch(Rectangle((a-.43,low),b-a+.86,high-low,fill=False,edgecolor=color,ls=':',lw=1.4))
 return a,b,lo,hi
def note(ax,bs,day,text,pos,field='close'):
 i=ix(bs,day);ax.annotate(text,xy=(i,float(bs[i][field])),xytext=pos,textcoords='axes fraction',fontproperties=font,fontsize=11,va='top',arrowprops={'arrowstyle':'-','color':'#72539b'})
ax,bs=draw(0,'2023-06-01','2023-07-31','背景：7/25收37.40已回37.15上，仍低於較早共同區38.05～38.25及原高39.25／40.25')
for key,color in [('later-low','#9b7655'),('earlier-high','#648493'),('retained-high','#4b607c')]:pointline(ax,bs,key,color)
ax.set_ylim(35.8,41.35)
zone(ax,bs,'earlier-local','#507a99');zone(ax,bs,'lower-local','#b17b4d');zone(ax,bs,'rebound-local','#779c71')
ax.text(.02,.93,'原5/2高40.25（5/9知）；原6/5高39.25（6/28知）',transform=ax.transAxes,fontproperties=font,fontsize=10,color='#4b607c')
ax.annotate('較早共同區38.05～38.25\n6/28～7/6來源，7/7才知',xy=((ix(bs,'2023-06-28')+ix(bs,'2023-07-06'))/2,38.15),xytext=(.20,.69),textcoords='axes fraction',fontproperties=font,fontsize=10,va='top',color='#507a99',arrowprops={'arrowstyle':'-','color':'#507a99'})
note(ax,bs,'2023-07-25','7/25 C37.40：局部回升位置',(.62,.67))
ax,bs=draw(3,'2023-07-07','2023-07-31','局部：共同區由36.75～37.00回升至37.25～37.35，影線來源價域仍有交疊')
ax.set_ylim(35.75,39.0)
pointline(ax,bs,'later-low','#9b7655');pointline(ax,bs,'older-low','#54789b')
zone(ax,bs,'lower-local','#b17b4d',True);zone(ax,bs,'rebound-local','#779c71',True)
note(ax,bs,'2023-07-18','下移活動：7/19才知\n共同36.75～37.00；原價域36.50～37.15',(.04,.91))
note(ax,bs,'2023-07-28','回升活動：7/31才知\n共同37.25～37.35；原價域36.80～37.65',(.53,.91))
ax.text(.02,.07,'填色只標共同區；點線框標來源原高低，並非正式箱。棕線37.15、藍線36.15為不同原參照。',transform=ax.transAxes,fontproperties=font,fontsize=10,color='#4b607c')
label(.065,.193,'7/25已可更新收回觀察，不必等7/31新局部活動完成；7/31才有新增完成活動，可補充局部回升證據。')
label(.065,.153,'7/25另有原3%研究框36.00～40.25可知，但與舊框重用5/2高40.25及5/15低37.15；不能當新增測壓或獨立票。')
label(.065,.113,'較大閱讀：把較早活動→下移→返回一起看；這只擴大需要比較的過程，尚未認定新大結構或原大G2恢復。')
label(.065,.073,'原大G2人工136筆、5/2代表與全部已答保持；新小活動不能取代較大背景。原參照高未再含，也不等於較大帶不存在。',11)
label(.065,.033,'有限事後研究，非盲掃描、分類率或交易資格；Raw／日曆／公司行動／歷史公開可得限制保持，分類器及新版Android未驗證。',11)
p=ROOT/'return-in-context.png';f.savefig(p,dpi=110);plt.close(f)
(ROOT/'figure-build.json').write_text(json.dumps({'builder_runs':2,'sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'image':'return-in-context.png','retrospective_source_overlay':True},indent=2)+'\n')
print(p)
