"""Retrospective opposite-direction chart comparison, with availability labels."""
import json,hashlib
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle
from matplotlib.font_manager import FontProperties
from study import ROOT,SOURCES
c=json.loads((ROOT/'study-inputs.json').read_text());sources={code:json.loads(p.read_text())for code,p in SOURCES.items()}
font=FontProperties(fname='/workspace/scratch/54685b8dac93/version-continuity-review/research-font.otf')
f=plt.figure(figsize=(18,14),facecolor='white')
def label(x,y,t,size=12):f.text(x,y,t,fontproperties=font,fontsize=size,color='#243449')
label(.065,.961,'同一套讀法，ABC下移與A上越得到不同結論',23)
label(.065,.923,'真實保存Raw日K；共同區為事後來源期疊圖，可知日另標。比較價格事實，不認證正式大結構或交易資格。')
g=f.add_gridspec(5,1,height_ratios=[3.3,1,.7,3.3,1],left=.065,right=.965,top=.84,bottom=.25,hspace=.28)
def ix(bs,day):return next(i for i,b in enumerate(bs)if b['date']==day)
def draw(row,case,start,end,title):
 bs=[b for b in sources[c['cases'][case]['code']]['bars']if start<=b['date']<=end];ax=f.add_subplot(g[row]);vol=f.add_subplot(g[row+1],sharex=ax)
 for i,b in enumerate(bs):
  o,h,l,cl=[float(b[k])for k in ['open','high','low','close']];color='#c44242'if cl>=o else'#168268'
  ax.vlines(i,l,h,color=color,lw=.85);ax.add_patch(Rectangle((i-.28,min(o,cl)),.56,max(abs(cl-o),.008),facecolor=color))
  vol.bar(i,int(b['volume_shares_scaled'])/1e6,color=color,width=.6)
 for a in [ax,vol]:a.set_xlim(-1,len(bs));a.grid(axis='y',alpha=.15);a.set_axisbelow(True)
 ax.tick_params(labelbottom=False);ax.set_ylabel('保存原始價格',fontproperties=font);vol.set_ylabel('量／百萬股',fontproperties=font)
 ticks=sorted({round(i*(len(bs)-1)/7)for i in range(8)});vol.set_xticks(ticks,[bs[i]['date'][5:].replace('-','/')for i in ticks])
 ax.set_title(title,fontproperties=font,fontsize=12,loc='left',pad=10)
 for key,p in c['cases'][case]['points'].items():
  ids=[i for i,b in enumerate(bs)if b['date']>=p['known_on']]
  if ids:ax.hlines(float(p['price']),ids[0]-.4,len(bs)-.4,color='#8b6f56'if key=='low'else'#54789b',ls='--',lw=.85)
 for key,z in c['cases'][case]['zones'].items():
  a,b=ix(bs,z['path_start']),ix(bs,z['path_end']);lo,hi=map(float,[z['common_close_low'],z['common_close_high']]);color={'earlier':'#507a99','lower':'#b17b4d','outside':'#9b6d9a','later':'#779c71'}[key]
  ax.add_patch(Rectangle((a-.4,lo),b-a+.8,hi-lo,facecolor=color,edgecolor=color,alpha=.24,zorder=-2))
 return ax,bs
def note(ax,bs,day,text,pos,field='close'):
 i=ix(bs,day);ax.annotate(text,xy=(i,float(bs[i][field])),xytext=pos,textcoords='axes fraction',fontproperties=font,fontsize=11,va='top',arrowprops={'arrowstyle':'-','color':'#72539b'})
ax,bs=draw(0,'ABC','2025-03-12','2025-06-12','ABC／1101／2025年：5/26已可比較活動下移；6/2已收破，6/12才有新的下方完成活動')
ax.set_ylim(25.8,40.1)
ax.text(.02,.94,'原3/12高35.45僅作原點參照，不是舊主要帶正式上緣。',transform=ax.transAxes,fontproperties=font,fontsize=10,color='#54789b')
note(ax,bs,'2025-05-13','較早共同30.55～30.60：5/13才知\n當日H31.40；原高標記5/14才知',(.27,.79),'high')
note(ax,bs,'2025-05-26','較晚共同29.80～30.30\n5/26才知，仍低於較早共同區',(.49,.58))
note(ax,bs,'2025-06-02','6/2 C27.70在原28.45下\n當日H29.05仍跨含；人工第39筆保留',(.72,.78))
note(ax,bs,'2025-06-11','下方共同27.15～27.30\n6/12才知，不倒填6/2',(.73,.50))
ax,bs=draw(3,'A','2026-09-08','2026-10-16','A／2884／2026年：10/14恰等較早共同區上緣；10/15整根在原47.35上')
ax.set_ylim(42.6,54.0)
ax.annotate('較早共同45.65～47.30\n9/15～30來源，10/1才知',xy=((ix(bs,'2026-09-15')+ix(bs,'2026-09-30'))/2,46.475),xytext=(.02,.91),textcoords='axes fraction',fontproperties=font,fontsize=11,va='top',arrowprops={'arrowstyle':'-','color':'#72539b'})
note(ax,bs,'2026-10-06','10/6 C45.45已過近端共同區\n仍低於較早共同區45.65',(.28,.72))
note(ax,bs,'2026-10-14','10/14 H=C47.30：相等不嚴格過\n仍低於原高47.35',(.53,.91))
note(ax,bs,'2026-10-15','10/15 L47.60 C48.80\n同時在較早原價域及原高之上',(.72,.57))
label(.065,.192,'ABC：收盤先收破、後來才有新的下方活動；A：收盤上越時已跨較早活動，不必先等新小帶完成。')
label(.065,.152,'A原高47.35與較早活動原高同源於9/17；跨越範圍較廣，不代表兩張獨立確認票，也不證回測已成功。')
label(.065,.112,'對照G2：7/25收回37.15，仍低於較早38.05～38.25。可以沿用分層讀法，不能把三案寫成同一種成敗。')
label(.065,.072,'ABC人工39、A已答上漲整理再漲與10/7足夠、G2人工136均保持；本輪沒有重新裁決或自動選主結構。',11)
label(.065,.032,'有限事後案例對照，不是通用分類器驗證；Raw／日曆／公司行動／歷史公開可得限制保持，新Android未測。',11)
p=ROOT/'abc-a-cross-case-reading.png';f.savefig(p,dpi=110);plt.close(f)
(ROOT/'figure-build.json').write_text(json.dumps({'builder_runs':2,'image':p.name,'sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'retrospective_source_overlay':True},indent=2)+'\n')
print(p)
