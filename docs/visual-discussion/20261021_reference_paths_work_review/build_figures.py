"""New same-reference evidence charts; no prior figure builder is run."""
import hashlib,io,json,os
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle
from matplotlib.font_manager import FontProperties
from matplotlib.backends.backend_pdf import PdfPages
from pypdf import PdfReader
from reference_paths import ROOT,prior,write
sources,c=prior.load_inputs();font=FontProperties(fname='/workspace/scratch/54685b8dac93/version-continuity-review/research-font.otf')
plt.rcParams.update({'pdf.fonttype':3,'axes.unicode_minus':False,'font.size':10})
def text(f,x,y,s,size=11):f.text(x,y,s,fontproperties=font,fontsize=size,color='#243449')
def page(title,sub):
    f=plt.figure(figsize=(17,12),facecolor='white');text(f,.065,.953,title,22);text(f,.065,.914,sub,12)
    g=f.add_gridspec(5,1,height_ratios=[3,1,.55,3,1],left=.065,right=.965,top=.837,bottom=.24,hspace=.28)
    return f,g
def draw(f,g,k,code,start,end,title):
    j=0 if k==0 else 3;ax=f.add_subplot(g[j]);v=f.add_subplot(g[j+1],sharex=ax);bs=[b for b in sources[code]['bars']if start<=b['date']<=end]
    for i,b in enumerate(bs):
        o,h,l,cl=[float(b[x])for x in ['open','high','low','close']];color='#c44242'if cl>=o else'#168268'
        ax.vlines(i,l,h,color=color,lw=.9)
        if o==cl:ax.hlines(cl,i-.3,i+.3,color=color,lw=1)
        else:ax.add_patch(Rectangle((i-.3,min(o,cl)),.6,abs(cl-o),facecolor=color,lw=0))
        v.bar(i,int(b['volume_shares_scaled'])/1e6,color=color,width=.65)
    lo=min(float(b['low'])for b in bs);hi=max(float(b['high'])for b in bs);span=hi-lo
    ax.set_ylim(lo-span*.12,hi+span*.38)
    for a in [ax,v]:a.set_xlim(-1,len(bs));a.grid(axis='y',alpha=.15);a.set_axisbelow(True)
    ax.tick_params(labelbottom=False);ax.set_title(title,fontproperties=font,fontsize=12,loc='left',pad=10)
    ax.set_ylabel('保存原始價格',fontproperties=font);v.set_ylabel('量／百萬股',fontproperties=font)
    ticks=sorted({round(i*(len(bs)-1)/7)for i in range(8)});v.set_xticks(ticks,[bs[i]['date'][5:].replace('-','/')for i in ticks],fontsize=10)
    return ax,v,bs
def ix(bs,day):return next(i for i,b in enumerate(bs)if b['date']==day)
def line(ax,bs,known,price,color,label):
    ids=[i for i,b in enumerate(bs)if b['date']>=known]
    if ids:ax.hlines(float(price),ids[0]-.4,len(bs)-.4,color=color,ls='--',lw=1);ax.text(len(bs)-.7,float(price)+.07,label,ha='right',fontproperties=font,fontsize=10,color=color)
def core(ax,bs,start,end,low,high,color):
    i,j=ix(bs,start),ix(bs,end);a,b=map(float,[low,high]);ax.add_patch(Rectangle((i-.4,a),j-i+.8,b-a,facecolor=color,alpha=.40,lw=0));ax.hlines([a,b],i-.4,j+.4,color=color,lw=1)
def arrow(ax,bs,day,label,pos,field='close'):
    b=next(b for b in bs if b['date']==day);ax.annotate(label,xy=(ix(bs,day),float(b[field])),xytext=pos,textcoords='axes fraction',fontproperties=font,fontsize=11,arrowprops={'arrowstyle':'-','color':'#72539b'})
def notes(f,lines,n):
    for y,s in zip([.177,.137,.097,.052],lines):text(f,.065,y,s,11 if y>.052 else 10)
    text(f,.94,.025,f'{n} / 2',10)

buf=io.BytesIO()
with PdfPages(buf)as pdf:
    f,g=page('2884：原參照已被收盤跨越，不必等新小價帶才更新觀察','固定原參照並列局部活動：價格事實、前批事件定義與正式結構資格分開。原10/7足夠辨認仍保持。')
    ax,v,bs=draw(f,g,0,'2884','2026-09-17','2026-10-16','原9/17高47.35（9/23確認）、原10/1低44.20（10/7確認）；虛線自確認日起畫')
    line(ax,bs,'2026-09-23','47.35','#9b7655','原高47.35');line(ax,bs,'2026-10-07','44.20','#6b87a1','原低44.20')
    core(ax,bs,'2026-09-30','2026-10-05','44.85','45.35','#bd8418');core(ax,bs,'2026-10-05','2026-10-08','45.00','45.75','#438b98')
    arrow(ax,bs,'2026-10-01','形成原低的10/1，不算10/7確認後再測',(.02,.91),'low')
    arrow(ax,bs,'2026-10-15','10/15首次保存收盤在原高上',(.53,.77))
    ax,v,bs=draw(f,g,1,'2884','2026-10-12','2026-10-16','放大原值｜10/14 H=C47.30仍下；10/15 O48.35、L47.60、C48.80，整根在47.35上')
    line(ax,bs,'2026-09-23','47.35','#9b7655','47.35參照')
    arrow(ax,bs,'2026-10-15','整根跳到參照上，不表示盤中曾成交或回測47.35',(.03,.90),'low')
    arrow(ax,bs,'2026-10-16','10/16 C49.15；尚無跨越後新完成雙向活動',(.35,.73))
    notes(f,['可更新較大觀察問題：原高被保存收盤跨過後，後續價格與原參照的關係如何發展；不等於新大結構或交易資格。',
             '10/15整根在原高上是原值事實；前批「離開後再等下一根整根在外」分支事件仍記10/16，不回寫舊事件。',
             '五個局部影線框包含44.20，都重用10/1形成低點；確認後未有日K價域含44.20，不能當五次回測。',
             '日K價域含點不是日內先後或該價成交證明；相等不嚴格過破。正式父子／主結構未定，分類器及新版Android未驗證。'],1)
    pdf.savefig(f);plt.close(f)

    f,g=page('多段活動在舊高之下，不足以證明被同一高點壓制','保留較大背景與原代表，但分開看「同側價位」、「形成點來源重用」及「確認後有沒有實際日K價域再含參照」。')
    ax,v,bs=draw(f,g,0,'1101','2025-03-12','2025-06-13','ABC｜原3/12 H35.45僅真實參照，非已定主帶上緣；原5/13 H31.40亦非主壓力')
    line(ax,bs,'2025-03-13','35.45','#9b7655','35.45');line(ax,bs,'2025-05-14','31.40','#9b7655','31.40');line(ax,bs,'2025-04-10','28.45','#6b87a1','28.45')
    core(ax,bs,'2025-05-19','2025-05-23','29.80','30.30','#438b98');core(ax,bs,'2025-06-06','2025-06-11','27.15','27.30','#3b68a0')
    arrow(ax,bs,'2025-06-02','6/2 C27.70先在原低下；仍是已答ABC第39筆',(.23,.91))
    arrow(ax,bs,'2025-06-03','6/3 H28.00才整根在下',(.60,.76),'high')
    ax,v,bs=draw(f,g,1,'1101','2023-05-09','2023-08-16','G2｜5/9原高確認後至8/16，69筆保存日K全未再含40.25；完整人工136筆與代表保持')
    line(ax,bs,'2023-05-09','40.25','#9b7655','原5/2高40.25，5/9確認')
    ax.set_ylim(35.5,41.15)
    arrow(ax,bs,'2023-06-07','多段後續活動都在下，仍缺原高再測證據',(.12,.89),'high')
    notes(f,['ABC在6/2已可記原低被保存收盤跌破，不必等6/12框下活動完成；不自動核定正式終點或改人工39筆。',
             'ABC兩個較早原高確認後均無保存日K價域再含該價；只證目前位置與未再到達，不直接證明反壓作用。',
             'G2九個局部影線框含40.25，來源均含5/2形成高點；這些不是5/9確認後九次測壓，也不能用數量投票。',
             '舊主要帶僅2023-06至2025-04月精度，不以35.45補其正式界線。原值／日曆資格保持；行動與資金飛輪成效未評估。'],2)
    pdf.savefig(f);plt.close(f)
b=buf.getvalue();assert b.rstrip().endswith(b'%%EOF')and len(PdfReader(io.BytesIO(b)).pages)==2
p=ROOT/'output/pdf/m1-same-reference-price-paths.pdf';p.parent.mkdir(parents=True,exist_ok=True)
with p.open('wb')as out:out.write(b);out.flush();os.fsync(out.fileno())
assert p.read_bytes()==b
write(ROOT/'figure-build.json',{'builder_runs':1,'pages':2,'bytes':len(b),'sha256':hashlib.sha256(b).hexdigest(),'prior_figure_builders_run':0,
    'reference_source':'reference-paths.json, original source OHLC, formation-point-reuse-audit.json'})
print(json.dumps({'pages':2,'bytes':len(b),'sha256':hashlib.sha256(b).hexdigest()}))
