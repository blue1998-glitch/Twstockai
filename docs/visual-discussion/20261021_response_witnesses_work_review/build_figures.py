"""New two-page opposing followup witnesses; old figure builders are not run."""
import hashlib,io,json,os
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle
from matplotlib.font_manager import FontProperties
from matplotlib.backends.backend_pdf import PdfPages
from pypdf import PdfReader
from response_witnesses import ROOT,prior,write
sources,c=prior.load_inputs();snap=json.loads((ROOT/'response-witnesses.json').read_text())
font=FontProperties(fname='/workspace/scratch/54685b8dac93/version-continuity-review/research-font.otf')
plt.rcParams.update({'pdf.fonttype':3,'axes.unicode_minus':False,'font.size':10})
def text(f,x,y,s,size=11):f.text(x,y,s,fontproperties=font,fontsize=size,color='#243449')
def page(title,sub):
    f=plt.figure(figsize=(17,12),facecolor='white');text(f,.065,.953,title,21);text(f,.065,.914,sub,12)
    g=f.add_gridspec(5,1,height_ratios=[3,1,.55,3,1],left=.065,right=.965,top=.837,bottom=.24,hspace=.28);return f,g
def ix(bs,day):return next(i for i,b in enumerate(bs)if b['date']==day)
def draw(f,g,k,start,end,title,r):
    j=0 if k==0 else 3;ax=f.add_subplot(g[j]);v=f.add_subplot(g[j+1],sharex=ax);bs=[b for b in sources[r['code']]['bars']if start<=b['date']<=end]
    for i,b in enumerate(bs):
        o,h,l,cl=[float(b[x])for x in ['open','high','low','close']];color='#c44242'if cl>=o else'#168268'
        ax.vlines(i,l,h,color=color,lw=.9)
        if o==cl:ax.hlines(cl,i-.3,i+.3,color=color,lw=1)
        else:ax.add_patch(Rectangle((i-.3,min(o,cl)),.6,abs(cl-o),facecolor=color,lw=0))
        v.bar(i,int(b['volume_shares_scaled'])/1e6,color=color,width=.65)
    lo=min(float(b['low'])for b in bs);hi=max(float(b['high'])for b in bs);span=hi-lo;ax.set_ylim(lo-span*.14,hi+span*.43)
    for a in [ax,v]:a.set_xlim(-1,len(bs));a.grid(axis='y',alpha=.15);a.set_axisbelow(True)
    ax.tick_params(labelbottom=False);ax.set_title(title,fontproperties=font,fontsize=12,loc='left',pad=10)
    ax.set_ylabel('保存原始價格',fontproperties=font);v.set_ylabel('量／百萬股',fontproperties=font)
    ticks=sorted({round(i*(len(bs)-1)/7)for i in range(8)});v.set_xticks(ticks,[bs[i]['date'][5:].replace('-','/')for i in ticks],fontsize=10)
    p=r['reference'];ids=[i for i,b in enumerate(bs)if b['date']>=p['known_on']]
    ax.hlines(float(p['price']),ids[0]-.4,len(bs)-.4,color='#537b9a',ls='--',lw=.9)
    ax.text(ids[0]+.1,float(p['price'])+.04,'原參照'+p['price'],fontproperties=font,fontsize=10,color='#537b9a',ha='left')
    a=r['anchor_source_bar'];i=ix(bs,a['date']);low,high=float(a['low']),float(a['high'])
    ax.add_patch(Rectangle((i-.42,low),.84,high-low,facecolor='#7770ad',alpha=.20,lw=0,zorder=-2))
    v.add_patch(Rectangle((i-.42,0),.84,int(a['volume_shares_scaled'])/1e6,facecolor='#7770ad',alpha=.20,lw=0,zorder=-2))
    ax.hlines([low,high],i-.4,len(bs)-.4,color='#9b7655',ls=':',lw=1)
    return ax,v,bs
def arrow(ax,bs,day,label,pos,field='close'):
    b=next(b for b in bs if b['date']==day);ax.annotate(label,xy=(ix(bs,day),float(b[field])),xytext=pos,textcoords='axes fraction',fontproperties=font,fontsize=11,arrowprops={'arrowstyle':'-','color':'#72539b'})
def notes(f,lines,n):
    for y,s in zip([.177,.137,.097,.052],lines):text(f,.065,y,s,11 if y>.052 else 10)
    text(f,.94,.025,f'{n} / 2',10)

buf=io.BytesIO()
with PdfPages(buf)as pdf:
    f,g=page('同樣到達原低價域、收在其上，後續方向仍可相反','紫色只標第一根日K價域相交K；棕色點線凍結該K高低，作描述地標，並非正式箱界或反應充分條件。')
    up=snap['G2-low-later-up@2023-04-11'];down=snap['G2-low-later-down@2023-07-11']
    ax,v,bs=draw(f,g,0,'2023-03-13','2023-04-11','原3/13低36.15於3/23確認｜3/28 L36.10、H36.65、C36.20；4/11才首次後收在該K上',up)
    arrow(ax,bs,'2023-03-28','3/28收36.20仍在原低上',(.02,.91))
    arrow(ax,bs,'2023-03-29','3/29 L36.05已下探，但收仍在凍結K價域內',(.29,.73),'low')
    arrow(ax,bs,'2023-04-11','4/11 C37.45上移；保存量32.19百萬股',(.52,.91))
    ax,v,bs=draw(f,g,1,'2023-05-15','2023-07-11','原5/15低37.15於5/30確認｜7/7 L36.90、H37.50、C37.30；下一筆7/10收36.85在該K下',down)
    arrow(ax,bs,'2023-07-07','7/7收37.30仍在原低上',(.22,.91))
    arrow(ax,bs,'2023-07-10','7/10 C36.85下移；保存量26.00百萬股',(.50,.73))
    notes(f,['兩例當日收盤都在原低之上，只能先記收盤位置；3/28當日不能帶入4/11，7/7當日也不能先寫有效支撐。',
             '兩個後續收盤見證日的量都比接觸日大：27.29→32.19、19.47→26.00百萬股；方向相反，量較大不能單獨指向上漲。',
             '相交連續保存列分別為3/28至3/31四筆、7/7至7/10兩筆；同一段往返不能當四次／兩次獨立測試投票。',
             '均為已答G2內的局部對照，完整1/16至8/16共136及5/2 H40.25代表保持。日K相交不證日內先後；正式反應與分類器未驗證。'],1)
    pdf.savefig(f);plt.close(f)

    f,g=page('原高到達、影線越界與後續收盤，下探破低各分時點','所有結果按當日可用證據加入，保留形成點與較大背景；相等不嚴格過破，不把日K相交直接叫成功測壓／回測。')
    high=snap['ABC-high-equality-then-down@2025-05-14'];low=snap['ABC-low-close-through@2025-06-03']
    ax,v,bs=draw(f,g,0,'2025-04-07','2025-05-14','原4/10高31.20於4/11確認｜5/12 C31.20恰等原高；凍結該K30.80至31.20',high)
    arrow(ax,bs,'2025-05-12','5/12等於原高，沒有收盤嚴格跨過',(.02,.91))
    arrow(ax,bs,'2025-05-13','5/13 H31.40、C31.10；影線與收盤分開',(.37,.73),'high')
    arrow(ax,bs,'2025-05-14','5/14 C30.35才在凍結K下',(.64,.91))
    ax,v,bs=draw(f,g,1,'2025-05-13','2025-06-03','原4/8低28.45於4/10確認｜6/2 K為27.65至29.05、C27.70已在原低下；6/3續下',low)
    arrow(ax,bs,'2025-06-02','6/2 C27.70並未收回原低上，仍是人工ABC第39筆',(.02,.91))
    arrow(ax,bs,'2025-06-03','6/3 C26.85下於6/2低27.65',(.49,.73))
    notes(f,['上例可保存「到原高附近後續收盤下移」的時序證據；尚不能認證因該原高造成壓力，更不能把31.20升成主壓力。',
             '5/13影線代表31.40保持；它沒有改寫5/12凍結地標。下例6/2先收破、6/3整根在原低下，不能當通用正式終點。',
             'A10/15整根跳到47.35上卻無日K價域相交，仍走原參照跨越觀察；原形成K與同日確認來源不當確認後新反應。',
             'Raw／日曆／公司行動／歷史公開可得限制保持；舊主要帶月精度不改。正式結構、分類器、新Android及行動／飛輪成效未驗證或未評估。'],2)
    pdf.savefig(f);plt.close(f)
b=buf.getvalue();assert b.rstrip().endswith(b'%%EOF')and len(PdfReader(io.BytesIO(b)).pages)==2
p=ROOT/'output/pdf/m1-post-reference-response-witnesses.pdf';p.parent.mkdir(parents=True,exist_ok=True)
with p.open('wb')as out:out.write(b);out.flush();os.fsync(out.fileno())
assert p.read_bytes()==b
write(ROOT/'figure-build.json',{'builder_runs':2,'pages':2,'bytes':len(b),'sha256':hashlib.sha256(b).hexdigest(),'prior_figure_builders_run':0,
    'bound_views':['G2-low-later-up@2023-04-11','G2-low-later-down@2023-07-11','ABC-high-equality-then-down@2025-05-14','ABC-low-close-through@2025-06-03']})
print(json.dumps({'pages':2,'bytes':len(b),'sha256':hashlib.sha256(b).hexdigest()}))
