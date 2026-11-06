"""B macro merge hypotheses on identical broad saved price context; no classifier."""
from pathlib import Path
from decimal import Decimal
from datetime import date
import os,json,hashlib,calendar
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle
from matplotlib.font_manager import FontProperties
from matplotlib.ticker import FormatStrFormatter
from matplotlib.backends.backend_pdf import PdfPages

ROOT=Path(__file__).resolve().parent
SOURCE=Path(os.environ.get('STOCK_STUDY_2884','/workspace/scratch/54685b8dac93/independent-level-review/source-data-2884.json'))
EXPECTED='ab87a51b5b8afd076603f290b10f415bd60d31ae47c5ab2f6d9d609ad4014901'
assert hashlib.sha256(SOURCE.read_bytes()).hexdigest()==EXPECTED
s=json.loads(SOURCE.read_text()); bars=s['bars']; font=FontProperties(fname=os.environ.get('STOCK_STUDY_FONT','/workspace/scratch/54685b8dac93/version-continuity-review/research-font.otf'))
assert len(bars)==1213 and len({x['date'] for x in bars})==1213 and bars==sorted(bars,key=lambda x:x['date'])
(ROOT/'output/pdf').mkdir(parents=True,exist_ok=True)
(ROOT/'tmp/pdfs').mkdir(parents=True,exist_ok=True)
phases=[('低位活動','2025-11-03','2025-12-03','#5888a5'),('回升後較高活動','2025-12-04','2026-03-13','#9a7a47'),('3月後較低活動','2026-03-16','2026-05-29','#8c6f9f')]
def frame(a,b):
    q=[x for x in bars if a<=x['date']<=b]
    lo=min(Decimal(x['low']) for x in q); hi=max(Decimal(x['high']) for x in q)
    return {'display_start':q[0]['date'],'display_end':q[-1]['date'],'saved_bars':len(q),'observed_low':str(lo),'observed_high':str(hi),'low_dates':[x['date'] for x in q if Decimal(x['low'])==lo],'high_dates':[x['date'] for x in q if Decimal(x['high'])==hi],'formal_interval':None,'formal_price_bounds':None}
frames={label:frame(a,b) for label,a,b,col in phases}; whole=frame(phases[0][1],phases[-1][2])
def txt(fig,x,y,t,size=12,col='#203548'):
    fig.text(x,y,t,fontproperties=font,fontsize=size,color=col)
def draw(fig,rect,vr,start,end,overlay=None):
    q=[b for b in bars if start<=b['date']<=end]; ds=[b['date'] for b in q]; ix={d:i for i,d in enumerate(ds)}
    ax=fig.add_axes(rect); va=fig.add_axes(vr,sharex=ax)
    for i,b in enumerate(q):
        o,h,l,c=[float(b[k]) for k in ['open','high','low','close']]; color='#c34848' if c>=o else '#16856c'
        ax.vlines(i,l,h,color=color,lw=.9)
        ax.add_patch(Rectangle((i-.3,min(o,c)),.6,max(abs(c-o),.015),facecolor=color,edgecolor=color,lw=.3))
        va.bar(i,int(b['volume_shares_scaled'])/1e6,width=.65,color=color)
    for ar in (ax,va):
        ar.set_xlim(-1,len(q));ar.grid(axis='y',color='#d7dfe8',lw=.5);ar.set_axisbelow(True)
        ar.spines['top'].set_visible(False);ar.spines['right'].set_visible(False)
        if '2026-04-28' in ix:ar.axvline(ix['2026-04-28']+.5,color='#8994a3',lw=.9,ls='--')
        if end>'2026-04-28':ar.axvspan(ix['2026-04-28']+.5,len(q)-.5,color='#dce3eb',alpha=.22,zorder=-8)
    ax.tick_params(axis='x',labelbottom=False);ax.set_ylabel('Raw價格',fontproperties=font)
    ax.yaxis.set_major_formatter(FormatStrFormatter('%.2f'));va.set_ylabel('量／百萬股',fontproperties=font,fontsize=10)
    ticks=[0]+[i for i,d in enumerate(ds) if i and d[:7]!=ds[i-1][:7] and (int(d[5:7])-1)%2==0]+[len(q)-1]
    ticks=[i for i in ticks if i in (0,len(q)-1) or len(q)*.055<i<len(q)*.95]
    va.set_xticks(ticks,[ds[i][:7] for i in ticks],fontsize=9)
    for g in s['source_gaps']['known_calendar_missing_dates']:
        if ds[0]<=g<=ds[-1]:
            i=next((i for i,d in enumerate(ds) if d>g),None)
            if i is not None:ax.axvline(i-.5,ymin=0,ymax=.04,color='#c48b24',lw=2)
    if overlay=='whole':
        f=whole;a=ix[f['display_start']];b=ix[f['display_end']];lo,hi=map(float,[f['observed_low'],f['observed_high']])
        ax.add_patch(Rectangle((a-.5,lo),b-a+1,hi-lo,fill=False,edgecolor='#65689a',lw=1.9))
    elif overlay=='parallel':
        for label,a,b,col in phases:
            f=frames[label];lo,hi=map(float,[f['observed_low'],f['observed_high']])
            ax.add_patch(Rectangle((ix[a]-.5,lo),ix[b]-ix[a]+1,hi-lo,fill=False,edgecolor=col,lw=1.9))
    # Labels identify time portions only. Do not label the rejected April micro-pair.
    for label,a,b,col in phases:
        if a in ix:
            end_day=min(b,ds[-1]); display_label=label if end_day==b else label+'（截至4/28）'
            ax.plot([ix[a],ix[end_day]],[1.015,1.015],transform=ax.get_xaxis_transform(),color=col,lw=3,clip_on=False)
            ax.text((ix[a]+ix[end_day])/2,1.038,display_label,transform=ax.get_xaxis_transform(),ha='center',fontproperties=font,fontsize=10,color=col)
    return ax,va,q

pdf=PdfPages(ROOT/'output/pdf/b-broad-merge-review.pdf'); outputs=[]
def save(fig,name,windows):
    p=ROOT/(name+'.png');fig.savefig(p,dpi=130);pdf.savefig(fig);plt.close(fig)
    outputs.append({'image':p.name,'sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'windows':windows})

fig=plt.figure(figsize=(20,10),facecolor='white')
txt(fig,.055,.95,'B｜先看約一年半：較大價格帶的範圍，才是這次比較',22)
txt(fig,.055,.908,'2884｜2025/1 - 2026/6保存日K；三條色線只定位閱讀階段，沒有預先替你定整體邊界。',12)
ax,va,q=draw(fig,[.055,.34,.92,.49],[.055,.17,.92,.13],'2025-01-02','2026-06-30')
txt(fig,.055,.09,'虛線為2026/4/28；右側是事後背景。5月／6月走勢可供事後看形狀，不能回填4/28當時已知。',11)
txt(fig,.055,.045,'保存Raw價量；公司行動、完整日曆及歷史公開可得仍待核。橙色短線是已列缺日，不補K。',10,'#647180')
save(fig,'b-overall-context',[{'start':q[0]['date'],'end':q[-1]['date'],'saved_bars':len(q)}])

fig=plt.figure(figsize=(20,15),facecolor='white')
txt(fig,.055,.965,'B｜兩種整體合併方案：使用同一段一年以上日K',22)
txt(fig,.055,.934,'比較的是幾個月的活動歸屬；原4月小段已判為微小波動，不再圈選或重問。',12)
txt(fig,.055,.888,'方案一：低位、回升、回落，合看成同一較大價格帶的內部階段',16)
ax1,v1,q1=draw(fig,[.055,.62,.92,.215],[.055,.535,.92,.062],'2025-06-02','2026-06-30','whole')
txt(fig,.055,.482,'方案二：保留低位、較高、較低三組活動，各自作價格帶候選並列',16)
ax2,v2,q2=draw(fig,[.055,.215,.92,.215],[.055,.13,.92,.062],'2025-06-02','2026-06-30','parallel')
# Same observations, same complete context and exact price/volume scales for both options.
assert q1==q2
assert ax1.get_ylim()==ax2.get_ylim() and v1.get_ylim()==v2.get_ylim()
txt(fig,.055,.074,'外框以各閱讀段的實際高低示意方案，並非正式價界；月份分段不是已核起末，可向更早或更晚擴展。',11)
txt(fig,.055,.043,'兩方案使用相同K線、座標與成交量。虛線4/28右側為事後背景；價格重疊本身不能決定合併。',11)
txt(fig,.055,.016,'Raw／公司行動／完整日曆／歷史公開可得限制保持；本圖是待比較的研究提案，非自動分類或買賣訊號。',10,'#647180')
save(fig,'b-whole-versus-parallel',[{'start':q1[0]['date'],'end':q1[-1]['date'],'saved_bars':len(q1),'panels':2,'same_observations_and_axes':True}])

fig=plt.figure(figsize=(20,10),facecolor='white')
txt(fig,.055,.95,'B｜截至4/28的廣角版本：只保留當日前的保存價量',22)
txt(fig,.055,.908,'2884｜2024/10 - 2026/4；與前兩頁分開，避免拿5月低點或6月上漲倒推當時的完整形狀。',12)
ax,va,q=draw(fig,[.055,.34,.92,.49],[.055,.17,.92,.13],'2024-10-17','2026-04-28')
txt(fig,.055,.09,'這頁沒有5月／6月。先前微小波動角色保留；當時能否定整體帶界仍未由這張圖自動裁定。',11)
txt(fig,.055,.045,'保存Raw價格；截至當日不等於歷史公開可得性已核。公司行動／日曆資格與全部原限制保持。',10,'#647180')
save(fig,'b-asof-broad-context',[{'start':q[0]['date'],'end':q[-1]['date'],'saved_bars':len(q),'cutoff':'2026-04-28','later_bars':0}])

fig=plt.figure(figsize=(20,11),facecolor='white')
txt(fig,.055,.954,'B｜參照放回大範圍：5月低點與6月前高路徑',22)
txt(fig,.055,.914,'同樣保留2025/6 - 2026/6完整日K。29.40、35.50是已保存原K參照，並非已核正式大帶價界。',12)
ax,va,q=draw(fig,[.055,.39,.92,.43],[.055,.245,.92,.11],'2025-06-02','2026-06-30')
ds=[x['date'] for x in q];ix={d:i for i,d in enumerate(ds)}
ax.hlines(35.50,ix['2026-02-26'],len(q)-.5,color='#b08048',ls='--',lw=1.2)
ax.hlines(29.40,ix['2025-11-10'],len(q)-.5,color='#547b9b',ls='--',lw=1.2)
ax.annotate('2/26 H35.50原價參照',xy=(ix['2026-02-26'],35.5),xytext=(.59,.96),textcoords='axes fraction',fontproperties=font,fontsize=10,arrowprops={'arrowstyle':'-','color':'#9b7e55'},color='#8c663b')
ax.annotate('5/28 C30.70、L30.65',xy=(ix['2026-05-28'],30.65),xytext=(.63,.17),textcoords='axes fraction',fontproperties=font,fontsize=10,arrowprops={'arrowstyle':'-','color':'#7b6597'},color='#70578f')
txt(fig,.055,.178,'5/28：C30.70低於3/23 L30.85，但仍高於11/10 L29.40。較近參照被跨過，不自動替較大帶定跌破。',12)
txt(fig,.055,.132,'6/17：H35.90、C35.50，收盤只是等於前高；6/18 H36.25、C35.40，影線過而收盤仍在下。',12)
txt(fig,.055,.087,'6/22：C35.80已收過35.50；6/24 C35.00又回到其下。觀察可當日更新，不等新小帶完成。',12)
txt(fig,.055,.038,'此頁為事後原價路徑核對，不宣稱正式突破／壓力確認或交易資格；Raw與全部來源限制保持。',10,'#647180')
save(fig,'b-broad-reference-paths',[{'start':q[0]['date'],'end':q[-1]['date'],'saved_bars':len(q),'price_references_only_not_formal_bounds':True}])
pdf.close()
def six_months_earlier(d):
    y,m=d.year,d.month-6
    if m<1:y,m=y-1,m+12
    return date(y,m,min(d.day,calendar.monthrange(y,m)[1]))
for item in outputs:
    for w in item['windows']:
        assert date.fromisoformat(w['start'])<=six_months_earlier(date.fromisoformat(w['end']))
examples={d:next(x for x in bars if x['date']==d) for d in ['2025-11-10','2026-01-14','2026-02-26','2026-03-16','2026-03-23','2026-04-28','2026-05-28','2026-06-17','2026-06-18','2026-06-22','2026-06-24']}
D=Decimal
assert D(examples['2025-11-10']['low'])<D(examples['2026-05-28']['close'])<D(examples['2026-03-23']['low'])
reference=D(examples['2026-02-26']['high'])
assert D(examples['2026-06-17']['close'])==reference<D(examples['2026-06-17']['high'])
assert D(examples['2026-06-18']['close'])<reference<D(examples['2026-06-18']['high'])
assert D(examples['2026-06-22']['close'])>reference>D(examples['2026-06-24']['close'])
first_over=next(x['date'] for x in bars if '2026-02-26'<x['date']<='2026-06-30' and D(x['close'])>reference)
assert first_over=='2026-06-22'
evidence={'selection':'RETROSPECTIVE_VISUAL_PROPOSALS_NOT_HISTORICAL_SELECTION','source_sha256':EXPECTED,'source_gaps':s['source_gaps'],'whole_display_frame':whole,'phase_display_frames':frames,'phase_month_boundaries':'ASSISTANT_READING_PARTITIONS_NOT_FORMAL_MEMBERSHIP','known_price_examples':examples,'first_saved_close_over_Feb26_high':first_over,'exact_reference_comparisons':'PASS','later_phase_raw_frame_inside_earlier_phase_raw_frame':D(frames['回升後較高活動']['observed_low'])<D(frames['3月後較低活動']['observed_low'])<D(frames['3月後較低活動']['observed_high'])<D(frames['回升後較高活動']['observed_high']),'containment_alone_does_not_decide_merge':True,'manual_B_micro_role':'ANSWERED_NOT_MATERIAL_INTERNAL_FLUCTUATION','formal_merge':None,'formal_bounds':None,'historical_signal_eligible':False}
(ROOT/'evidence.json').write_text(json.dumps(evidence,ensure_ascii=False,indent=2)+'\n')
(ROOT/'figure-manifest.json').write_text(json.dumps({'outputs':outputs,'minimum_calendar_months':6,'all_windows_satisfy_minimum':True,'PDF_pages':4,'comparison_price_volume_axes_equal':True,'source_sha256_after':hashlib.sha256(SOURCE.read_bytes()).hexdigest()},ensure_ascii=False,indent=2)+'\n')
assert hashlib.sha256(SOURCE.read_bytes()).hexdigest()==EXPECTED
print(json.dumps({'outputs':outputs,'frames':frames,'whole':whole},ensure_ascii=False,indent=2))
