"""New two-page cutoff comparison; no prior figure builder is invoked."""
import hashlib,io,json,os
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle
from matplotlib.font_manager import FontProperties
from matplotlib.backends.backend_pdf import PdfPages
from pypdf import PdfReader
from observation_topics import ROOT,prior,write

sources,c=prior.load_inputs();views=json.loads((ROOT/'reading-proposals.json').read_text())
font=FontProperties(fname='/workspace/scratch/54685b8dac93/version-continuity-review/research-font.otf')
plt.rcParams.update({'pdf.fonttype':3,'axes.unicode_minus':False,'font.size':10})
def text(f,x,y,s,size=11):f.text(x,y,s,fontproperties=font,fontsize=size,color='#243449')
def ix(bs,day):return next(i for i,b in enumerate(bs)if b['date']==day)
def draw(code,start,end,title,sub,charttitle):
    f=plt.figure(figsize=(17,12),facecolor='white');text(f,.065,.951,title,22);text(f,.065,.909,sub,12)
    ax=f.add_axes([.065,.573,.90,.248]);v=f.add_axes([.065,.460,.90,.075],sharex=ax)
    bs=[b for b in sources[code]['bars']if start<=b['date']<=end]
    for i,b in enumerate(bs):
        o,h,l,cl=[float(b[k])for k in ['open','high','low','close']];col='#c44242'if cl>=o else'#168268'
        ax.vlines(i,l,h,color=col,lw=.95)
        if o==cl:ax.hlines(cl,i-.3,i+.3,color=col,lw=1)
        else:ax.add_patch(Rectangle((i-.3,min(o,cl)),.6,abs(cl-o),facecolor=col,lw=0))
        v.bar(i,int(b['volume_shares_scaled'])/1e6,color=col,width=.65)
    lo=min(float(b['low'])for b in bs);hi=max(float(b['high'])for b in bs);span=hi-lo
    ax.set_ylim(lo-span*.12,hi+span*.43)
    for a in [ax,v]:a.set_xlim(-1,len(bs));a.grid(axis='y',alpha=.15);a.set_axisbelow(True)
    ax.tick_params(labelbottom=False);ax.set_title(charttitle,fontproperties=font,loc='left',fontsize=13,pad=12)
    ax.set_ylabel('保存原始價格',fontproperties=font);v.set_ylabel('量／百萬股',fontproperties=font)
    ticks=sorted({round(i*(len(bs)-1)/7)for i in range(8)});v.set_xticks(ticks,[bs[i]['date'][5:].replace('-','/')for i in ticks],fontsize=10)
    return f,ax,v,bs
def shade(ax,v,bs,start,end,col):
    ids=[i for i,b in enumerate(bs)if start<=b['date']<=end];p=[bs[i]for i in ids]
    lo=min(float(b['low'])for b in p);hi=max(float(b['high'])for b in p)
    ax.add_patch(Rectangle((ids[0]-.45,lo),ids[-1]-ids[0]+.9,hi-lo,facecolor=col,alpha=.13,lw=0,zorder=-2))
    v.add_patch(Rectangle((ids[0]-.45,0),ids[-1]-ids[0]+.9,max(int(b['volume_shares_scaled'])for b in p)/1e6,facecolor=col,alpha=.13,lw=0,zorder=-2))
def core(ax,bs,start,end,low,high,col):
    i,j=ix(bs,start),ix(bs,end);a,b=map(float,[low,high]);ax.add_patch(Rectangle((i-.4,a),j-i+.8,b-a,facecolor=col,alpha=.5,lw=0));ax.hlines([a,b],i-.4,j+.4,color=col,lw=1)
def arrow(ax,bs,day,label,pos,field='close'):
    b=next(b for b in bs if b['date']==day)
    ax.annotate(label,xy=(ix(bs,day),float(b[field])),xytext=pos,textcoords='axes fraction',fontproperties=font,fontsize=11,arrowprops={'arrowstyle':'-','color':'#72539b'})
def timelines(f,bs,lines):
    a=f.add_axes([.065,.322,.90,.085]);a.set_xlim(-1,len(bs));a.set_ylim(-.25,len(lines)+.2);a.axis('off')
    for j,(start,end,col,label)in enumerate(lines):
        x1,x2=ix(bs,start),ix(bs,end);y=len(lines)-j-1
        a.plot([x1,x2],[y,y],color=col,lw=3);a.plot([x1,x2],[y,y],color=col,ls='',marker='|',ms=13)
        a.text((x1+x2)/2,y+.15,label,ha='center',fontproperties=font,fontsize=11,color=col)
def table(f,rows):
    a=f.add_axes([.065,.125,.90,.145]);a.axis('off')
    t=a.table(cellText=[['證據變化','研究可以走到哪一步']]+rows,cellLoc='left',colWidths=[.18,.82],bbox=[0,0,1,1]);t.auto_set_font_size(False)
    for (rr,cc),cell in t.get_celld().items():
        cell.set_text_props(fontproperties=font,fontsize=11,color='#243449');cell.set_edgecolor('#d5dce4');cell.PAD=.035
        cell.set_facecolor('#eaf0f6'if rr==0 else'#f7f9fb'if rr%2 else'white')
def foot(f,n,line):
    text(f,.065,.078,line,10)
    text(f,.065,.049,'橫線只標閱讀／追蹤期間，不是正式箱界。Raw候選與日曆／公司行動／歷史公開可得限制保持。',10)
    text(f,.065,.025,'分類器、正式主結構／父子／合併未驗證；新版Android未測；行動及資金閉環／飛輪成效未評估。',9)
    text(f,.94,.025,f'{n} / 2',10)

buf=io.BytesIO()
with PdfPages(buf)as pdf:
    a=views['ABC-fresh-lower@2025-05-26'];b=views['ABC-outside@2025-06-12'];last=views['ABC-outside@2025-06-13']
    assert a['reading_proposal']['birth_reading_window']['saved_records']==34 and b['reading_proposal']['birth_reading_window']['saved_records']==47
    f,ax,v,bs=draw('1101','2025-04-07','2025-06-13','ABC：內部下移補充原結構；框下活動另開跨框對照','圖面截止6/13｜紫色保留人工4/7至6/2共39筆。兩條閱讀提案依完整證據日出生，不擴張人工成員。','金色較早共同30.55至30.60；藍綠色內部29.80至30.30；藍色框下27.15至27.30')
    shade(ax,v,bs,'2025-04-07','2025-06-02','#7770ad')
    for st,en,lo,hi,col in [('2025-04-09','2025-05-12','30.55','30.60','#bd8418'),('2025-05-19','2025-05-23','29.80','30.30','#438b98'),('2025-06-06','2025-06-11','27.15','27.30','#3b68a0')]:core(ax,bs,st,en,lo,hi,col)
    ax.hlines(28.45,-.4,len(bs)-.4,color='#9b7655',ls='--',lw=.9)
    arrow(ax,bs,'2025-05-13','5/13 H31.40局部代表仍保留',(.19,.91),'high')
    arrow(ax,bs,'2025-05-26','5/26才知內部較低價位的完成往返',(.48,.75))
    arrow(ax,bs,'2025-06-12','6/12才知框下完成活動',(.68,.91))
    timelines(f,bs,[('2025-04-08','2025-05-26','#438b98','5/26可另讀前後活動：4/8至5/26，34筆'),('2025-04-07','2025-06-12','#3b68a0','6/12可另讀舊框＋框下活動：4/7至6/12，47筆')])
    table(f,[['5/23至5/26','5/23尚缺後段確認；5/26可比較前後共同價帶的下移，仍屬原ABC內部活動補充。\n34筆是兩組活動的完整證據閱讀範圍，不是另成立較大箱或改寫39筆。'],
             ['6/11至6/12','6/11尚無框下完整雙向候選；6/12已有6/6至6/11完成活動，連到6/3整根離開事件。\n可另開47筆跨框對照閱讀，但較大結構是否成立、正式起末與歸屬仍未知。'],
             ['6/13更新','6/13收26.90低於舊框，也低於新共同價帶；保留6/12出生提案，更新當前閱讀至48筆。\n原人工ABC仍39筆；舊主要帶2023-06至2025-04的較大背景保持。']])
    foot(f,1,'本頁新增的是跨前後活動的閱讀提案；「範圍更大」相對局部證據，沒有認定比已確認ABC更高階的新結構。')
    pdf.savefig(f);plt.close(f)

    g=views['G2-outside-return@2023-04-27'];gr=views['G2-outside-return@2023-05-12'];assert gr['current_episode']['ended_on']=='2023-05-12'
    f,ax,v,bs=draw('1101','2023-01-16','2023-05-12','G2：返回改變當前狀態，已完成的跨框活動仍保留','圖面截止5/12｜只畫已答G2的前段；完整人工涵蓋仍為1/16至8/16共136筆，不以局部事件截短。','固定舊觀察35.90至37.85｜4/24至4/26共同38.50至39.10，4/27才知')
    shade(ax,v,bs,'2023-01-16','2023-02-16','#bd8418');shade(ax,v,bs,'2023-04-24','2023-04-26','#3b68a0')
    core(ax,bs,'2023-04-24','2023-04-26','38.50','39.10','#3b68a0')
    ax.hlines(37.85,-.4,len(bs)-.4,color='#9b7655',ls='--',lw=.9)
    arrow(ax,bs,'2023-03-01','3/1收37.80，二月歷程已返回',(.02,.90))
    arrow(ax,bs,'2023-04-27','4/27才有完成的框上活動',(.41,.74))
    arrow(ax,bs,'2023-05-12','5/12收37.80，再次返回',(.68,.91))
    timelines(f,bs,[('2023-02-17','2023-03-01','#9b7655','二月外側歷程，3/1已結束'),('2023-04-21','2023-05-12','#3b68a0','4/21另次離開，5/12返回'),('2023-01-16','2023-04-27','#72539b','4/27可另讀舊框＋上方活動：1/16至4/27，61筆')])
    table(f,[['4/26至4/27','4/26缺完整後續確認；4/27可把固定舊框與已完成上方活動放在同一閱讀範圍。\n提案從保存舊框來源1/16讀至4/27共61筆，不宣稱1/16是新正式結構起點。'],
             ['5/12返回','4/21歷程於5/12收37.80回框內；此時必須顯示已返回，不能仍稱持續在框上。\n4/27提案的出生日期與61筆證據不變；當前閱讀延伸至71筆，不刪歷史或自動合併。'],
             ['保留較大背景','人工G2完整136筆及5/2 H40.25代表保持；該原3%高點5/9才確認，不放入4/27判斷。\n原高點、局部活動、離開返回與正式結構角色分開；返回本身不是合併充分條件。']])
    foot(f,2,'對照限制：全新同價往返只補重訪；共段／重用來源只補活動；A10/16新離開尚無完成後續，不提本類新閱讀。')
    pdf.savefig(f);plt.close(f)
b=buf.getvalue();assert b.rstrip().endswith(b'%%EOF')and len(PdfReader(io.BytesIO(b)).pages)==2
p=ROOT/'output/pdf/m1-local-changes-and-broader-observations.pdf';p.parent.mkdir(parents=True,exist_ok=True)
with p.open('wb')as out:out.write(b);out.flush();os.fsync(out.fileno())
assert p.read_bytes()==b
write(ROOT/'figure-build.json',{'builder_runs':1,'pages':2,'bytes':len(b),'sha256':hashlib.sha256(b).hexdigest(),'prior_figure_builders_run':0,
    'bound_views':['ABC-fresh-lower@2025-05-26','ABC-outside@2025-06-12','ABC-outside@2025-06-13','G2-outside-return@2023-04-27','G2-outside-return@2023-05-12']})
print(json.dumps({'pages':2,'bytes':len(b),'sha256':hashlib.sha256(b).hexdigest()}))
