"""Manual Work review of saved OHLCV; no detector, signal, or approved bounds."""
from pathlib import Path
from decimal import Decimal as D
import json, hashlib, os
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle
from matplotlib.font_manager import FontProperties
from matplotlib.backends.backend_pdf import PdfPages
from matplotlib.ticker import FormatStrFormatter
from pypdf import PdfReader

ROOT=Path(__file__).resolve().parent
SOURCE=Path(os.environ.get('STOCK_STUDY_2884','/workspace/scratch/54685b8dac93/independent-level-review/source-data-2884.json'))
EXPECTED='ab87a51b5b8afd076603f290b10f415bd60d31ae47c5ab2f6d9d609ad4014901'
FONT=FontProperties(fname=os.environ.get('STOCK_STUDY_FONT','/workspace/scratch/54685b8dac93/version-continuity-review/research-font.otf'))
CUTOFF='2026-05-29'
def dump(name,obj): (ROOT/name).write_text(json.dumps(obj,ensure_ascii=False,indent=2)+'\n')
def select(bars,start,end=CUTOFF): return [b for b in bars if start<=b['date']<=end]
def audit(bars,start,end):
    bs=select(bars,start,end)
    out={'requested_start':start,'requested_end':end,'first_saved':bs[0]['date'],'last_saved':bs[-1]['date'],'saved_bars':len(bs),'membership_status':'ASSISTANT_READING_SCOPE_NOT_FORMAL_BAND'}
    for key,fn in [('high',max),('low',min),('volume_shares_scaled',max)]:
        v=fn(D(b[key]) for b in bs)
        out[key]={'value':str(v),'dates':[b['date'] for b in bs if D(b[key])==v]}
    return out
def draw(bars,start,title,subtitle):
    bs=select(bars,start);dates=[b['date'] for b in bs]
    f=plt.figure(figsize=(20,10),facecolor='white')
    ax=f.add_axes([.055,.34,.91,.49]);va=f.add_axes([.055,.14,.91,.16],sharex=ax)
    f.text(.055,.947,title,fontproperties=FONT,fontsize=22,color='#203548')
    f.text(.055,.902,subtitle,fontproperties=FONT,fontsize=12)
    for i,b in enumerate(bs):
        o,h,l,c=[float(b[k]) for k in ['open','high','low','close']]
        color='#c34848' if c>=o else '#16856c'
        ax.vlines(i,l,h,color=color,lw=.7)
        ax.add_patch(Rectangle((i-.3,min(o,c)),.6,max(abs(c-o),.014),facecolor=color,edgecolor=color,lw=.2))
        va.bar(i,int(b['volume_shares_scaled'])/1e6,color=color,width=.66)
    for a in [ax,va]:
        a.set_xlim(-1,len(bs)+2);a.grid(axis='y',alpha=.35,lw=.6)
        a.set_axisbelow(True)
        for edge in ['top','right']: a.spines[edge].set_visible(False)
    ax.set_ylabel('Raw價格',fontproperties=FONT);ax.yaxis.set_major_formatter(FormatStrFormatter('%.2f'))
    va.set_ylabel('量／百萬股',fontproperties=FONT);ax.tick_params(axis='x',labelbottom=False)
    step=6 if len(bs)>700 else 2 if len(bs)>300 else 1
    ticks=[i for i,d in enumerate(dates) if (i==0 or d[:7]!=dates[i-1][:7]) and (int(d[5:7])-1)%step==0]
    va.set_xticks(ticks,[dates[i][:7] for i in ticks],fontsize=9)
    f.text(.055,.067,'右端為歷史選定截止2026/5/29，非即時今日；只有截至該日的保存K，沒有六月後續。',fontproperties=FONT,fontsize=11)
    f.text(.055,.032,'人工研究範圍與價位參照，非正式分帶或交易訊號。Raw公司行動、完整日曆與歷史公開可得性仍待核。',fontproperties=FONT,fontsize=10,color='#596875')
    for gap in DATA['source_gaps']['known_calendar_missing_dates']:
        if start<=gap<=CUTOFF:
            after=next((i for i,d in enumerate(dates) if d>gap),None)
            if after is not None: ax.axvline(after-.5,ymin=0,ymax=.035,color='#c48b24',lw=2)
    return f,ax,va,dates
def point(ax,dates,date,key,text,xytext,color='#384e67'):
    b=next(b for b in BARS if b['date']==date)
    ax.annotate(text,xy=(dates.index(date),float(b[key])),xytext=xytext,textcoords='axes fraction',fontproperties=FONT,fontsize=10,color=color,arrowprops={'arrowstyle':'-','color':color,'lw':.8},va='top')
def box(ax,dates,start,end,low,high,color):
    a=next(i for i,d in enumerate(dates) if d>=start);z=max(i for i,d in enumerate(dates) if d<=end)
    ax.add_patch(Rectangle((a-.5,low),z-a+1,high-low,facecolor=color,alpha=.07,edgecolor=color,lw=1.4))
    ax.plot([a-.5,z+.5],[high,high],color=color,lw=1)
    ax.plot([a-.5,z+.5],[low,low],color=color,lw=1)

def main():
    global DATA,BARS
    assert hashlib.sha256(SOURCE.read_bytes()).hexdigest()==EXPECTED
    DATA=json.loads(SOURCE.read_text());BARS=select(DATA['bars'],DATA['bars'][0]['date'])
    assert len(DATA['bars'])==1213 and all(b['date']<=CUTOFF for b in BARS)
    scopes={k:audit(BARS,a,z) for k,a,z in [
        ('whole_observation','2025-10-27',CUTOFF),
        ('whole_start_sensitivity','2025-11-03',CUTOFF),
        ('older_high_shelf','2025-07-10','2025-10-23'),
        ('internal_rebound','2025-12-04','2026-03-13'),
        ('recent_lower_activity','2026-03-16',CUTOFF)]}
    line_dates=['2025-12-22','2025-12-23','2025-12-24']
    baseline={'status':'ASSISTANT_VISUAL_TRIAL_NOT_USER_APPROVED','value_shares':'110000000','source_bars':[b for b in BARS if b['date'] in line_dates],'method':'視覺上以12/22～24相近的量柱峰值試畫；不是算術均量、SMA、倍量或正式算法','formal_baseline':None}
    evidence={'schema':'manual-right-to-left-review/0.1','as_of':CUTOFF,'source_sha256':EXPECTED,'price_basis_id':DATA['price_basis_id'],'source_gaps':DATA['source_gaps'],'latest_bar':BARS[-1],'scopes':scopes,'volume_baseline_trial':baseline,'formal_bounds':None,'formal_members':None,'formal_merge':None,'historical_signal_eligible':False,'reading':'右端低位→較近33.20→較大觀察35.50；向左舊高35.40仍比較，未按重疊自動合併。29.40與30.65為不同層低點來源。'}
    dump('evidence.json',evidence)
    (ROOT/'output/pdf').mkdir(parents=True,exist_ok=True);(ROOT/'tmp/pdfs').mkdir(parents=True,exist_ok=True)
    tmp=ROOT/'tmp/pdfs/b-right-to-left-review.pdf';manifest=[]
    with PdfPages(tmp) as pdf:
        f,ax,va,dates=draw(BARS,BARS[0]['date'],'B｜先看近五年，再向右端定位','2884｜完整保存背景截至2026/5/29；橙色短線為已列缺日，不補K')
        ax.axvspan(dates.index('2025-10-27'),len(dates),alpha=.08,color='#7963a7')
        point(ax,dates,CUTOFF,'close','右端5/29 C30.95',(.84,.94))
        point(ax,dates,'2026-02-26','high','2/26 H35.50',(.65,.98))
        f.savefig(ROOT/'b-five-year-anchor.png',dpi=120);pdf.savefig(f);plt.close(f)
        manifest.append({'image':'b-five-year-anchor.png','first':dates[0],'last':dates[-1],'bars':len(dates)})
        f,ax,va,dates=draw(BARS,'2024-05-29','B｜由右往左：整帶、內部活動、較早高台一起看','框為助手閱讀提案；完整涵蓋所讀活動，並非使用者核定界價／起末／父子關係')
        box(ax,dates,'2025-07-10','2025-10-23',31.65,35.40,'#a37f3f')
        box(ax,dates,'2025-10-27',CUTOFF,29.40,35.50,'#7761a6')
        box(ax,dates,'2026-03-16',CUTOFF,30.65,33.20,'#43819a')
        point(ax,dates,'2025-07-17','high','較早高台 H35.40',(.34,.99),'#916e34')
        point(ax,dates,'2026-02-26','high','較大觀察 H35.50',(.68,.99),'#7761a6')
        point(ax,dates,'2026-04-16','high','較近活動 H33.20',(.83,.79),'#43819a')
        point(ax,dates,'2025-11-10','low','較早低點 L29.40',(.58,.12),'#7761a6')
        point(ax,dates,'2026-05-28','low','右端鄰近低點 L30.65\n5/29 C30.95',(.86,.33),'#43819a')
        f.savefig(ROOT/'b-whole-band-reading.png',dpi=120);pdf.savefig(f);plt.close(f)
        manifest.append({'image':'b-whole-band-reading.png','first':dates[0],'last':dates[-1],'bars':len(dates)})
        f,ax,va,dates=draw(BARS,'2025-10-01','B｜價峰與量峰分找；右端有量仍要比較價位','約八個月日K；110百萬股線只是視覺試畫，不能視為已核整帶均量')
        point(ax,dates,'2026-02-26','high','價峰2/26 H35.50\n當日量101.50百萬股',(.49,.98))
        point(ax,dates,'2026-04-16','high','較近高33.20',(.76,.82))
        point(ax,dates,CUTOFF,'close','5/29 C30.95\n仍低於33.20／35.50',(.81,.35))
        va.axhline(110,color='#538a9b',ls='--',lw=1)
        for date in line_dates: va.scatter(dates.index(date),int(next(b for b in BARS if b['date']==date)['volume_shares_scaled'])/1e6,s=18,color='#538a9b',zorder=5)
        va.annotate('試畫110：依12/22～24相近量峰',xy=(dates.index('2025-12-23'),110),xytext=(.36,.88),textcoords='axes fraction',fontproperties=FONT,fontsize=10,arrowprops={'arrowstyle':'-','color':'#538a9b'})
        va.annotate('10/27量峰280.91\n急變原因待公司行動核對',xy=(dates.index('2025-10-27'),280.910308),xytext=(.03,.90),textcoords='axes fraction',fontproperties=FONT,fontsize=9,arrowprops={'arrowstyle':'-','color':'#5a6570'})
        va.annotate('若由11/3起讀：12/8最大146.71',xy=(dates.index('2025-12-08'),146.711672),xytext=(.36,.58),textcoords='axes fraction',fontproperties=FONT,fontsize=9,arrowprops={'arrowstyle':'-','color':'#5a6570'})
        va.annotate('5/29量119.51',xy=(dates.index(CUTOFF),119.510199),xytext=(.82,.66),textcoords='axes fraction',fontproperties=FONT,fontsize=10,arrowprops={'arrowstyle':'-','color':'#5a6570'})
        f.savefig(ROOT/'b-price-volume-reading.png',dpi=120);pdf.savefig(f);plt.close(f)
        manifest.append({'image':'b-price-volume-reading.png','first':dates[0],'last':dates[-1],'bars':len(dates)})
    reader=PdfReader(tmp);assert len(reader.pages)==3 and all(len(p.images)==0 for p in reader.pages)
    assert tmp.read_bytes().rstrip().endswith(b'%%EOF')
    dest=ROOT/'output/pdf/b-right-to-left-review.pdf';tmp.replace(dest)
    for item in manifest: item['sha256']=hashlib.sha256((ROOT/item['image']).read_bytes()).hexdigest()
    dump('figure-manifest.json',{'figures':manifest,'pdf_sha256':hashlib.sha256(dest.read_bytes()).hexdigest(),'vector_pages':3,'image_objects':0})
    assert hashlib.sha256(SOURCE.read_bytes()).hexdigest()==EXPECTED
    print(json.dumps({'scopes':scopes,'figures':manifest},ensure_ascii=False))
if __name__=='__main__':main()
