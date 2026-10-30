"""Two concrete local-structure interpretations of identical B price evidence."""
import json,hashlib
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle
from matplotlib.font_manager import FontProperties
from prepare_review import ROOT,SOURCE
s=json.loads(SOURCE.read_text());c=json.loads((ROOT/'study-inputs.json').read_text());font=FontProperties(fname='/workspace/scratch/54685b8dac93/version-continuity-review/research-font.otf')
f=plt.figure(figsize=(18,14),facecolor='white')
def text(x,y,t,size=12):f.text(x,y,t,fontproperties=font,fontsize=size,color='#243449')
text(.065,.962,'B案例：一個整理內部下移，還是兩個較高／較低活動？',23)
text(.065,.924,'2884／2026年 保存Raw日K。只比較高亮4/16～4/27來源段；4/28確認K另看，不使用其後行情作裁決。')
def ix(bs,day):return next(i for i,b in enumerate(bs)if b['date']==day)
def draw(rect,start,end,volume=None):
 bs=[b for b in s['bars']if start<=b['date']<=end];ax=f.add_axes(rect)
 for i,b in enumerate(bs):
  o,h,l,cl=[float(b[k])for k in ['open','high','low','close']];color='#c44242'if cl>=o else'#168268'
  ax.vlines(i,l,h,color=color,lw=1);ax.add_patch(Rectangle((i-.28,min(o,cl)),.56,max(abs(cl-o),.008),facecolor=color))
 ax.set_xlim(-1,len(bs));ax.grid(axis='y',alpha=.15);ax.set_axisbelow(True);ax.set_ylabel('保存Raw價格',fontproperties=font)
 ticks=sorted({round(i*(len(bs)-1)/6)for i in range(7)});ax.set_xticks(ticks,[bs[i]['date'][5:].replace('-','/')for i in ticks])
 if volume:
  v=f.add_axes(volume,sharex=ax);ax.tick_params(labelbottom=False)
  for i,b in enumerate(bs):v.bar(i,int(b['volume_shares_scaled'])/1e6,color='#c44242'if float(b['close'])>=float(b['open'])else'#168268',width=.6)
  v.set_ylabel('量／百萬股',fontproperties=font);v.grid(axis='y',alpha=.15);v.set_axisbelow(True)
 return ax,bs
def note(ax,bs,day,t,pos,field='close'):
 ax.annotate(t,xy=(ix(bs,day),float(next(b for b in bs if b['date']==day)[field])),xytext=pos,textcoords='axes fraction',fontproperties=font,fontsize=11,va='top',arrowprops={'arrowstyle':'-','color':'#72539b'})
ax,bs=draw([.065,.654,.9,.205],'2026-02-26','2026-04-28',[.065,.581,.9,.058]);ax.set_ylim(30.1,38.0)
ax.set_title('廣角上下文：先前下跌、反彈到4月中，再看高亮的兩個局部活動',fontproperties=font,fontsize=12,loc='left',pad=10)
ax.axvspan(ix(bs,'2026-04-16')-.42,ix(bs,'2026-04-27')+.42,color='#7770ad',alpha=.13,zorder=-3)
note(ax,bs,'2026-04-23','4/23 C32.45在上方共同區下\n該活動要到4/24才確認',(.42,.72))
note(ax,bs,'2026-04-28','4/28 H32.95回到上方區\n但C32.45仍未收回',(.69,.92),'high')
text(.065,.529,'方案一：合看成一個局部整理',17);text(.545,.529,'方案二：上方整理轉弱，較低活動另列',17)
text(.065,.500,'內部重心由32.75～33.00移到32.45～32.55',11);text(.545,.500,'兩活動來源交疊，共用下跌段只算一次',11)
for k,x in enumerate([.065,.545]):
 ax,bs=draw([x,.274,.42,.205],'2026-04-13','2026-04-28');ax.set_ylim(31.75,34.3)
 dates=['2026-04-13','2026-04-16','2026-04-22','2026-04-23','2026-04-27','2026-04-28'];ax.set_xticks([ix(bs,d)for d in dates],[d[5:].replace('-','/')for d in dates])
 # Identical price series, same highlight of the one shared down leg.
 ax.axvspan(ix(bs,'2026-04-22')-.42,ix(bs,'2026-04-23')+.42,color='#7770ad',alpha=.12,zorder=-3)
 for key,color in [('upper','#507a99'),('lower','#b17b4d')]:
  z=c['zones'][key];a,b=ix(bs,z['path_start']),ix(bs,z['path_end']);lo,hi=map(float,[z['common_close_low'],z['common_close_high']])
  ax.add_patch(Rectangle((a-.4,lo),b-a+.8,hi-lo,facecolor=color,alpha=.28,edgecolor=color,zorder=-2))
 if k==0:
  a,b=ix(bs,'2026-04-16'),ix(bs,'2026-04-27');ax.add_patch(Rectangle((a-.43,32.0),b-a+.86,1.2,fill=False,edgecolor='#72539b',lw=2))
  ax.text(.04,.92,'單一較大候選框\n原來源去重共8筆',transform=ax.transAxes,fontproperties=font,fontsize=11,va='top',color='#72539b')
 else:
  for key,color in [('upper','#507a99'),('lower','#b17b4d')]:
   z=c['zones'][key];a,b=ix(bs,z['path_start']),ix(bs,z['path_end']);lo,hi=map(float,[z['raw_path_frame']['observed_low'],z['raw_path_frame']['observed_high']])
   ax.add_patch(Rectangle((a-.43,lo),b-a+.86,hi-lo,fill=False,edgecolor=color,lw=1.8))
  ax.text(.04,.92,'上方來源6筆、下方來源4筆\n4/22～23兩筆共用，非10筆',transform=ax.transAxes,fontproperties=font,fontsize=11,va='top',color='#4b607c')
text(.065,.223,'框只示候選來源範圍，不是在定正式價界或起末；兩圖使用完全相同的K線及座標，4/28不強行納入原來源期。',11)
text(.065,.181,'已核事實：上方活動4/24才知；下方活動4/28才知。共用1段下跌，去重4段活動；所有段沒有單一共同交集。',11)
text(.065,.139,'沒有單一共同交集不能單獨否決合併；共用下跌也不能單獨決定合併。4/28影線回到舊區與收盤仍在下方都要保留。',11)
text(.065,.097,'我的研究傾向：先採方案二；B尚無使用者整體裁決，這不是已批准規則。A、ABC、G2原答案均不重問。',12)
text(.065,.055,'這次只問高亮這一段屬一個局部整理或兩個局部；不判交易資格。原Raw／日曆／公司行動限制及分類器未驗證保持。',11)
p=ROOT/'b-merge-options.png';f.savefig(p,dpi=110);plt.close(f)
(ROOT/'figure-build.json').write_text(json.dumps({'builder_runs':2,'image':p.name,'sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'evidence_cutoff':'2026-04-28','later_prices_plotted':False,'same_price_data_and_axes_for_both_options':True},indent=2)+'\n')
print(p)
