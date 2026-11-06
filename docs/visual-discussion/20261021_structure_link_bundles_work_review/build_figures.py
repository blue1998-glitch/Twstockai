"""Three cutoff-qualified readouts; manual review is a separate display overlay."""
import gzip,hashlib,io,json,os
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle
from matplotlib.font_manager import FontProperties
from matplotlib.backends.backend_pdf import PdfPages
from pypdf import PdfReader
from observation_bundle import ROOT,load_inputs,unpack_snapshots,write

src,cat=load_inputs()
bundles=unpack_snapshots(json.loads(gzip.decompress((ROOT/'observation-bundles.json.gz').read_bytes())),cat)
font=FontProperties(fname='/workspace/scratch/54685b8dac93/version-continuity-review/research-font.otf')
plt.rcParams.update({'pdf.fonttype':3,'axes.unicode_minus':False,'font.size':10})
def text(f,x,y,s,size=11,color='#243449'):
    f.text(x,y,s,fontproperties=font,fontsize=size,color=color)
def zone(code,start,end):
    return next(z for z in cat['zones']if z['code']==code and z['path_start']==start and z['path_end']==end)
def pivot(code,day,scale):
    return next(p for p in cat['pivots']if p['code']==code and p['occurred_at']==day and p['scale']==scale and p['kind']=='HIGH')
def draw(code,start,end,title,subtitle,charttitle):
    f=plt.figure(figsize=(17,12),facecolor='white')
    text(f,.065,.948,title,22);text(f,.065,.907,subtitle,12)
    ax=f.add_axes([.065,.535,.90,.285]);v=f.add_axes([.065,.421,.90,.083],sharex=ax)
    bs=[b for b in src[code]['bars']if start<=b['date']<=end]
    for i,b in enumerate(bs):
        o,h,l,c=[float(b[x])for x in ['open','high','low','close']];color='#c44242'if c>=o else'#168268'
        ax.vlines(i,l,h,color=color,lw=.85)
        if o==c:ax.hlines(c,i-.3,i+.3,color=color,lw=1)
        else:ax.add_patch(Rectangle((i-.3,min(o,c)),.6,abs(c-o),facecolor=color,lw=0))
        v.bar(i,int(b['volume_shares_scaled'])/1e6,color=color,width=.65)
    lo=min(float(b['low'])for b in bs);hi=max(float(b['high'])for b in bs);span=hi-lo
    ax.set_ylim(lo-span*.13,hi+span*.43)
    for a in [ax,v]:a.set_xlim(-1,len(bs));a.grid(axis='y',alpha=.15);a.set_axisbelow(True)
    ax.tick_params(labelbottom=False);ax.set_title(charttitle,fontproperties=font,fontsize=13,loc='left',pad=11)
    ax.set_ylabel('保存原始價格',fontproperties=font);v.set_ylabel('量／百萬股',fontproperties=font)
    ticks=sorted({round(i*(len(bs)-1)/8)for i in range(9)})
    v.set_xticks(ticks,[bs[i]['date'].replace('-','/')for i in ticks],rotation=0,fontsize=9)
    return f,ax,v,bs
def ix(bs,d):return next(i for i,b in enumerate(bs)if b['date']==d)
def shade(ax,v,bs,start,end,color='#7770ad',alpha=.14):
    ids=[i for i,b in enumerate(bs)if start<=b['date']<=end];part=[bs[i]for i in ids]
    lo=min(float(b['low'])for b in part);hi=max(float(b['high'])for b in part)
    ax.add_patch(Rectangle((ids[0]-.45,lo),ids[-1]-ids[0]+.9,hi-lo,facecolor=color,alpha=alpha,lw=0,zorder=-2))
    v.add_patch(Rectangle((ids[0]-.45,0),ids[-1]-ids[0]+.9,max(int(b['volume_shares_scaled'])for b in part)/1e6,facecolor=color,alpha=alpha,lw=0,zorder=-2))
def core(ax,bs,z,color):
    i,j=ix(bs,z['path_start']),ix(bs,z['path_end']);lo,hi=float(z['common_close_low']),float(z['common_close_high'])
    ax.add_patch(Rectangle((i-.45,lo),j-i+.9,hi-lo,facecolor=color,alpha=.45,edgecolor='none',zorder=-1))
    ax.hlines([lo,hi],i-.45,j+.45,color=color,lw=1)
def arrow(ax,bs,day,label,pos,field='close'):
    b=next(b for b in bs if b['date']==day)
    ax.annotate(label,xy=(ix(bs,day),float(b[field])),xytext=pos,textcoords='axes fraction',fontproperties=font,fontsize=11,arrowprops={'arrowstyle':'-','color':'#72539b'})
def table(f,rows,n,foot):
    tax=f.add_axes([.065,.115,.90,.23]);tax.axis('off')
    t=tax.table(cellText=[['觀察角色','截至當日可說的內容']]+rows,colWidths=[.19,.81],cellLoc='left',bbox=[0,0,1,1])
    t.auto_set_font_size(False);t.set_fontsize(11)
    for (r,c),cell in t.get_celld().items():
        cell.set_text_props(fontproperties=font,fontsize=11,color='#243449')
        cell.set_edgecolor('#d5dce4');cell.PAD=.035
        cell.set_facecolor('#eaf0f6'if r==0 else'#f7f9fb'if r%2 else'white')
    text(f,.065,.075,foot,10)
    text(f,.065,.045,'原值研究資格不等於歷史已選取；人工確認另列，未送入組合器。正式形成／主區間／父子合併仍未定。',10)
    text(f,.065,.025,'分類器未驗證；新版Android未測；行動與資金閉環／飛輪成效未評估。候選數量不是重要性或票數。',9)
    text(f,.94,.025,f'{n} / 3',10)

readouts={};buf=io.BytesIO()
with PdfPages(buf)as pdf:
    r=bundles['A-2026-10-16'];p=pivot('2884','2026-09-17','0.03')
    pv=next(v for v in r['retained_original_pivot_views']if v['pivot_id']==p['id'])
    assert pv['first_saved_crossing_from_availability']=={'date':'2026-10-15','close':'48.80'}
    a=zone('2884','2026-09-30','2026-10-05');b=zone('2884','2026-10-05','2026-10-08')
    ev=next(e for e in cat['events']if e['code']=='2884'and e['frozen_frame']['frame_start']=='2026-09-17'and e['known_on_saved_bar']=='2026-10-16')
    assert not any(v['event_id']==ev['event_id']for v in r['separated_followup_views'])
    readouts['A']={'bundle':'A-2026-10-16','pivot':p,'pivot_view':pv,'zones':[a,b],'latest_event':ev,'latest_event_new_local_activity_links':0,'close':r['last_bar']['close']}
    f,ax,v,bs=draw('2884','2026-05-04','2026-10-16','2884：保留較大上漲背景，也看見整理後的新位置','截止2026/10/16｜紫色為9/17至10/7已討論範圍；金色及藍綠色僅標局部共同價帶。','廣角原K與成交量｜圖面背景從5/4起，並非新宣稱的正式形成起點')
    shade(ax,v,bs,'2026-09-17','2026-10-07');core(ax,bs,a,'#bd8418');core(ax,bs,b,'#438b98')
    ax.hlines(float(p['price']),ix(bs,'2026-09-17'),len(bs)-1,color='#9e7c30',ls='--',lw=.9)
    arrow(ax,bs,'2026-09-17','9/17原高47.35保留',(.49,.91),'high')
    arrow(ax,bs,'2026-10-16','10/16收49.15；尚無這次新種子的完成雙向活動',(.57,.72))
    table(f,[['較大背景與原參照','9/17原3%高47.35於9/23確認；自可用日起，第一筆保存收盤嚴格在其上為10/15收48.80。\n10/16收49.15在上；這個事實保留原高參照，不直接決定正式突破、主區間或進出。'],
             ['局部活動','前組9/30至10/5共同44.85至45.35，10/6才知；後組10/5至10/8共同45.00至45.75，10/12才知。\n後組仍共用10/5轉向與較早證據期間，不能當成全新獨立往返或較重要。'],
             ['離開與後續','固定舊觀察框44.20至47.35，10/15收離開、10/16整根在上；事件照截止日保留。\n就這次9/17種子事件，來源到10/16只有新種子一筆，不能補未來雙向活動或核定舊終點。'],
             ['人工確認另列','完整上漲、短暫整理、再漲，以及截至10/7足夠辨認整理，均已確認，不重問。\n9/17至10/16研究觀察共19筆，不代表正式起點、最早辨認日或正式成員。']],1,
          '資料：保存Raw候選。10/7原核心快照與numeric_frame仍無；原值投影與本次補充研究不能冒稱歷史產品判斷。')
    pdf.savefig(f);plt.close(f)

    r=bundles['ABC-2025-06-13'];a=zone('1101','2025-05-19','2025-05-23');b=zone('1101','2025-06-06','2025-06-11')
    assert r['observation_records']==48 and r['last_bar']['close']=='26.90'
    readouts['ABC']={'bundle':'ABC-2025-06-13','zones':[a,b],'research_rows':48,'retrospective_manual_rows':39,'close':r['last_bar']['close']}
    f,ax,v,bs=draw('1101','2023-06-01','2025-06-13','ABC：內部下移與框外新活動，可以並列保留','截止2025/06/13｜較早主要帶僅保留2023-06至2025-04的月精度認定，不強配正式日端點或價界。','廣角原K與成交量｜紫色是已確認4/7至6/2人工39筆；後續觀察另列')
    shade(ax,v,bs,'2025-04-07','2025-06-02');core(ax,bs,a,'#438b98');core(ax,bs,b,'#3b68a0')
    shade(ax,v,bs,b['path_start'],b['path_end'],'#3b68a0',.18)
    arrow(ax,bs,'2025-05-13','5/13 H31.40局部代表仍保留',(.54,.90),'high')
    arrow(ax,bs,'2025-06-11','6/6至6/11框下活動，6/12才知',(.59,.72))
    table(f,[['較大背景保留','舊主要帶2023-06至2025-04仍是較大背景；未挑戰舊主要帶高點前，不因新小核心先降重要性。\n其正式全成員、價界與主代表仍未知；本圖廣角起日只供閱讀，不能補成正式端點。'],
             ['人工範圍／研究範圍','人工ABC為4/7至6/2共39筆，6/2仍內、6/3在外；5/14內部跳空不是通用切段條件。\n本次4/7至6/13研究共48筆只是追蹤窗口，沒有把人工ABC延長成48筆。'],
             ['內部移動與框下活動','5/19至5/23共同29.80至30.30，5/26知，可提出全新內部活動下移，即使影線外包仍交疊。\n6/3整根低於固定28.45至31.40；6/6至6/11 raw26.90至27.65、共同27.15至27.30，6/12才知。'],
             ['目前位置與證據資格','6/13收26.90仍低於舊框，也低於後續共同27.15至27.30；現價離開核心不抹去過去活動。\n缺的候選比較與較晚追蹤已另存補充，原截止日前證據不變；不是歷史核心快照或正式新箱。']],2,
          '紫色與藍色僅沿各段原K價量範圍著色。5/13 H31.40是右側證據／人工局部代表，不用收盤核心取代影線。')
    pdf.savefig(f);plt.close(f)

    r=bundles['G2-2023-08-16'];p=pivot('1101','2023-05-02','0.03');pv=next(v for v in r['retained_original_pivot_views']if v['pivot_id']==p['id'])
    a=zone('1101','2023-04-24','2023-04-26')
    assert p['price']=='40.25'and p['known_on']=='2023-05-09'and pv['first_saved_crossing_from_availability']is None
    assert r['observation_records']==136 and '2023-08-03'in r['source_qualification']['listed_missing_dates_in_observation']
    readouts['G2']={'bundle':'G2-2023-08-16','pivot':p,'pivot_view':pv,'zone':a,'manual_rows':136,'qualification':r['source_qualification'],'close':r['last_bar']['close']}
    f,ax,v,bs=draw('1101','2023-01-16','2023-08-16','G2：局部多次離開返回，較大涵蓋仍保留','截止2023/08/16｜紫色保留人工完整136筆，金色只是一段較小活動，不把所有局部核心當正式箱。','完整人工G2原K與成交量｜5/2高40.25仍保留為已答代表')
    shade(ax,v,bs,'2023-01-16','2023-08-16');core(ax,bs,a,'#bd8418')
    ax.hlines(float(p['price']),ix(bs,'2023-05-02'),len(bs)-1,color='#9e7c30',ls='--',lw=.9)
    arrow(ax,bs,'2023-05-02','5/2 H40.25，原3%高在5/9確認',(.43,.91),'high')
    arrow(ax,bs,'2023-04-26','4/24至4/26局部共同38.50至39.10',(.02,.72))
    table(f,[['較大涵蓋與原高點','人工1/16至8/16共136保存筆保持；5/2 H40.25代表保持，原3%高5/9確認。\n自該確認日起至8/16，未見保存收盤嚴格高於40.25；不由此自動計算重要性或正式終點。'],
             ['歷程不能倒接','對固定35.90至37.85：二月外側歷程於3/1收37.80返回；4/21是另一次外收歷程。\n4/24整根在上，4/24至4/26 raw38.20至39.80、共同38.50至39.10於4/27知，5/12又返回。'],
             ['局部角色／當前位置','可並列較大背景、歷次返回與較小外側活動；局部事件結束，不刪過去活動或自動合併主範圍。\n8/16收36.05；當前位置與過去活動出生證據分開，不能用最近或最大局部窗代替較大G2。'],
             ['資料資格與未定事項','觀察內保存來源列有8/3缺日，資格仍保留；本次未認證完整日曆或連續性。\n正式全成員、價界、主要性與父子合併未定；不同候選數量不是市場獨立樣本或投票。']],3,
          '三頁皆只合看已保存原值與研究證據；公司行動、Adjusted、歷史公開可得等來源限制仍保留。')
    pdf.savefig(f);plt.close(f)

b=buf.getvalue();assert b.rstrip().endswith(b'%%EOF')and len(PdfReader(io.BytesIO(b)).pages)==3
p=ROOT/'output/pdf/m1-integrated-observation-bundles.pdf';p.parent.mkdir(parents=True,exist_ok=True)
with p.open('wb')as out:out.write(b);out.flush();os.fsync(out.fileno())
assert p.read_bytes()==b
write(ROOT/'figure-readout-data.json',readouts)
write(ROOT/'figure-build.json',{'builder_runs':1,'pages':3,'bytes':len(b),'sha256':hashlib.sha256(b).hexdigest(),'old_figure_rebuilds':0})
print(json.dumps({'pages':3,'bytes':len(b),'sha256':hashlib.sha256(b).hexdigest()}))
