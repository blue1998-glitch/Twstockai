"""Scope review pictures: display existing answers and explicitly proposed links."""
import json,hashlib
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.font_manager import FontProperties
from matplotlib.patches import Rectangle
from prepare_review import ROOT,SOURCE_PATHS
inp=json.loads((ROOT/'study-inputs.json').read_text());sources={code:json.loads(p.read_text())for code,p in SOURCE_PATHS.items()}
font=FontProperties(fname='/workspace/scratch/54685b8dac93/version-continuity-review/research-font.otf')
def txt(f,x,y,t,size=12):f.text(x,y,t,fontproperties=font,fontsize=size,color='#243449')
def ix(bs,day):return next(i for i,b in enumerate(bs)if b['date']==day)
def draw(f,grid,row,case,start,end,title):
 bs=[b for b in sources[inp['code_map'][case]]['bars']if start<=b['date']<=end];ax=f.add_subplot(grid[row]);v=f.add_subplot(grid[row+1],sharex=ax)
 for i,b in enumerate(bs):
  o,h,l,c=[float(b[k])for k in ['open','high','low','close']];color='#c44242'if c>=o else'#168268'
  ax.vlines(i,l,h,color=color,lw=.9);ax.add_patch(Rectangle((i-.28,min(o,c)),.56,max(abs(c-o),.008),facecolor=color))
  v.bar(i,int(b['volume_shares_scaled'])/1e6,color=color,width=.6)
 for a in [ax,v]:a.set_xlim(-1,len(bs));a.grid(axis='y',alpha=.15);a.set_axisbelow(True)
 ax.tick_params(labelbottom=False);ax.set_ylabel('保存Raw價格',fontproperties=font);v.set_ylabel('量／百萬股',fontproperties=font)
 ticks=sorted({round(i*(len(bs)-1)/7)for i in range(8)});v.set_xticks(ticks,[bs[i]['date'][5:].replace('-','/')for i in ticks])
 ax.set_title(title,fontproperties=font,fontsize=12,loc='left',pad=10)
 for j,(name,z)in enumerate(inp['zones'][case].items()):
  a,b=ix(bs,z['path_start']),ix(bs,z['path_end']);lo,hi=map(float,[z['common_close_low'],z['common_close_high']]);color=['#507a99','#b17b4d','#8a709b'][j]
  ax.add_patch(Rectangle((a-.4,lo),b-a+.8,hi-lo,facecolor=color,edgecolor=color,alpha=.28,zorder=-2))
 return ax,bs
def bracket(ax,bs,start,end,y,label,color):
 a,b=ix(bs,start)-.4,ix(bs,end)+.4;ax.plot([a,a,b,b],[y-.1,y,y,y-.1],color=color,lw=1.5)
 ax.text((a+b)/2,y+.08,label,fontproperties=font,fontsize=11,color=color,ha='center',va='bottom')
def arrow(ax,bs,day,label,pos,field='close'):
 i=ix(bs,day);ax.annotate(label,xy=(i,float(bs[i][field])),xytext=pos,textcoords='axes fraction',fontproperties=font,fontsize=11,va='top',arrowprops={'arrowstyle':'-','color':'#72539b'})
figures=[]
f=plt.figure(figsize=(18,14),facecolor='white');txt(f,.065,.96,'同一較大觀察，可以保留多個局部身份',24)
txt(f,.065,.922,'括弧只標時間涵蓋，高度不是價位；共同區為事後來源期疊圖，不是正式箱或當日已知訊號。')
g=f.add_gridspec(5,1,height_ratios=[3.5,1,.65,3.5,1],left=.065,right=.965,top=.84,bottom=.25,hspace=.28)
ax,bs=draw(f,g,0,'A','2026-08-12','2026-10-16','A／2884／2026年：已答上漲、短暫整理、再漲；局部活動各自保存')
ax.set_ylim(34.5,57.0)
bracket(ax,bs,'2026-08-12','2026-10-16',54.5,'已答整體情境的示例觀察窗；8/12不是新認定的正式起點','#536a7e')
ax.hlines(47.35,ix(bs,'2026-09-23')-.4,len(bs)-.4,color='#54789b',ls='--',lw=.9)
arrow(ax,bs,'2026-10-15','10/15收48.80站上原47.35\n不抹掉各局部活動來源',(.70,.67))
ax.text(.38,.23,'三個局部來源仍分開：10/1、10/6、10/12各自才可用',transform=ax.transAxes,fontproperties=font,fontsize=10,color='#4b607c')
ax,bs=draw(f,g,3,'ABC','2025-04-07','2025-06-12','ABC／1101／2025年：39筆原範圍保持；跌出後可追蹤同一弱化問題')
ax.set_ylim(25.8,37.0)
bracket(ax,bs,'2025-04-07','2025-06-12',35.2,'研究觀察鏈：較弱活動 → 收破 → 後續下方活動（非新正式大結構）','#536a7e')
bracket(ax,bs,'2025-04-07','2025-06-02',33.8,'原已答ABC：4/7～6/2，39保存筆','#507a99')
bracket(ax,bs,'2025-06-03','2025-06-12',33.0,'後續8筆；不納原ABC','#8a709b')
ax.hlines(28.45,ix(bs,'2025-04-10')-.4,len(bs)-.4,color='#9b7655',ls='--',lw=.9)
arrow(ax,bs,'2025-06-02','6/2收27.70已在原28.45下\n仍為ABC人工第39筆',(.54,.52))
arrow(ax,bs,'2025-06-11','6/6～11下方活動\n6/12才知',(.77,.38))
txt(f,.065,.194,'可以連的是同一觀察問題及有記錄的演變路徑；不是把局部ID、形成來源、可知日或原人工成員全部合併。')
txt(f,.065,.153,'A、G2既有整體判斷保持；ABC跌出後只加觀察連結，原ABC39不延長。上下兩種關係可以同時保存。')
txt(f,.065,.112,'只有共同價格、時間靠近、來源重用或同屬大背景，尚不足以正式合併局部，更不能加成多張獨立確認票。')
txt(f,.065,.072,'本輪是當前語意關係研究，人工答案不作歷史數值引擎輸入；正式父子、結構身份合併與唯一主結構仍未定。',11)
txt(f,.065,.032,'原Raw／日曆／公司行動／歷史公開可得限制保持；分類器與新版Android未驗證，行動與飛輪效果未評估。',11)
p=ROOT/'process-and-local-identities.png';f.savefig(p,dpi=110);plt.close(f);figures.append(p)

f=plt.figure(figsize=(18,10),facecolor='white');txt(f,.065,.95,'同屬大G2，不代表兩個局部已互相回測或應被合併',23)
txt(f,.065,.899,'已答大G2人工1/16～8/16共136筆保持；本圖只放大1/16～3/27。括弧只標時間涵蓋，高度不是價位。')
g=f.add_gridspec(2,1,height_ratios=[4,1],left=.065,right=.965,top=.78,bottom=.30,hspace=.20)
ax,bs=draw(f,g,0,'G2','2023-01-16','2023-03-27','1101／2023年：共同區幾何重疊，與來源日K收盤實際再入分開')
ax.set_ylim(35.0,42.0)
bracket(ax,bs,'2023-01-16','2023-03-27',41.2,'兩個局部都在既有G2人工範圍中；不由此推出局部合併','#536a7e')
known=ix(bs,'2023-02-10');ax.hlines([36.60,36.75],known-.4,len(bs)-.4,color='#54789b',ls=':',lw=1)
arrow(ax,bs,'2023-02-09','較早共同36.60～36.75\n1/17～2/9來源，2/10才知',(.04,.71))
arrow(ax,bs,'2023-03-16','較晚共同36.35～37.10\n來源3/15～24，八筆實收均未在舊共同區內',(.45,.87))
arrow(ax,bs,'2023-03-27','3/27確認K C36.65才在舊共同區內\n不能倒填來源3/15～24',(.68,.65))
txt(f,.065,.230,'同一整體情境：既有人工答案已支持。局部兩者關係：保留幾何比較；尚未認證互相測試或形成同一局部結構。')
txt(f,.065,.175,'八筆收盤未再入不等於日內沒有成交或影線未碰；不能用它反過來否定既有大G2，也不把3/27改寫成較早已知。')
txt(f,.065,.120,'原5/2 H40.25代表仍保持（在此放大窗外）；完整G2中的8/3原已列缺日保持，未認證完整日曆連續性。')
txt(f,.065,.065,'同一較大觀察、局部比較、正式合併是不同關係；本輪不新增正式主結構／父子／反應規則。',11)
p=ROOT/'g2-context-with-parallel-locals.png';f.savefig(p,dpi=110);plt.close(f);figures.append(p)
write={'builder_runs':2,'images':[{'file':p.name,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()}for p in figures],'all_scope_brackets_are_retrospective_display_or_explicit_observation_proposals':True}
(ROOT/'figure-build.json').write_text(json.dumps(write,indent=2)+'\n')
print('Built two new scope-review images')
