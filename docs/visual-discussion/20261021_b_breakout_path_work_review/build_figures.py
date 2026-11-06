"""Broad B raw-price/volume figures; comparisons are descriptive, not thresholds."""
from pathlib import Path
from fractions import Fraction
from datetime import date
import json,hashlib,os,calendar
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle
from matplotlib.font_manager import FontProperties
from matplotlib.ticker import FormatStrFormatter
from matplotlib.backends.backend_pdf import PdfPages
from study import SOURCE,ROOT,EXPECTED

def main():
    s=json.loads(SOURCE.read_text());bs=s['bars']; evidence=json.loads((ROOT/'path-evidence.json').read_text());events={e['date']:e for e in evidence['events']}
    assert hashlib.sha256(SOURCE.read_bytes()).hexdigest()==EXPECTED
    font=FontProperties(fname=os.environ.get('STOCK_STUDY_FONT','/workspace/scratch/54685b8dac93/version-continuity-review/research-font.otf'))
    pdfdir=ROOT/'output/pdf';pdfdir.mkdir(parents=True,exist_ok=True);(ROOT/'tmp/pdfs').mkdir(parents=True,exist_ok=True)
    temp_pdf=ROOT/'tmp/pdfs/b-nested-price-volume-path.build.pdf'
    pdf=PdfPages(temp_pdf); manifest=[]
    def txt(f,x,y,t,size=12,col='#203548'):
        f.text(x,y,t,fontproperties=font,fontsize=size,color=col)
    def draw(f,start,end,pr,vr,markers=False):
        q=[b for b in bs if start<=b['date']<=end];dates=[b['date'] for b in q];ix={d:i for i,d in enumerate(dates)}
        ax=f.add_axes(pr);va=f.add_axes(vr,sharex=ax)
        for i,b in enumerate(q):
            o,h,l,c=[float(b[k])for k in ['open','high','low','close']];color='#c34848'if c>=o else'#16856c'
            ax.vlines(i,l,h,color=color,lw=.9);ax.add_patch(Rectangle((i-.30,min(o,c)),.6,max(abs(o-c),.015),facecolor=color,edgecolor=color,lw=.3))
            va.bar(i,int(b['volume_shares_scaled'])/1e6,width=.65,color=color)
        # The rolling comparison excludes each plotted day's own volume.
        global_ix={b['date']:i for i,b in enumerate(bs)}
        rolling=[]
        for b in q:
            j=global_ix[b['date']];rolling.append(float(Fraction(sum(int(x['volume_shares_scaled']) for x in bs[j-20:j]),20))/1e6 if j>=20 else None)
        va.plot(range(len(q)),rolling,color='#b08636',lw=1.3,label='prior20')
        # Frozen source median is not shown before the source period is complete.
        first=next((i for i,d in enumerate(dates) if d>='2026-05-29'),None)
        med=evidence['frozen_volume_comparison']['median_shares'];median_shares=med['numerator']/med['denominator']
        if first is not None:va.hlines(median_shares/1e6,first,len(q)-.5,color='#6d72a0',ls='--',lw=1.2)
        for d,p,c in [('2026-02-26',35.50,'#a77b42'),('2026-04-16',33.20,'#75649a')]:
            if d in ix:ax.hlines(p,ix[d],len(q)-.5,color=c,lw=1.4,ls='--')
        for ar in (ax,va):
            ar.set_xlim(-1,len(q)+.5);ar.grid(axis='y',color='#d7dfe8',lw=.55);ar.set_axisbelow(True)
            for spine in ('top','right'):ar.spines[spine].set_visible(False)
        ax.set_ylabel('Raw價格',fontproperties=font);ax.yaxis.set_major_formatter(FormatStrFormatter('%.2f'));ax.tick_params(labelbottom=False)
        va.set_ylabel('量／百萬股',fontproperties=font,fontsize=10)
        ticks=[0]+[i for i,d in enumerate(dates) if i and d[:7]!=dates[i-1][:7] and (len(q)<220 or int(d[5:7])%2==1)]+[len(q)-1]
        ticks=[i for i in ticks if i in (0,len(q)-1)or len(q)*.055<i<len(q)*.94]
        va.set_xticks(ticks,[dates[i][:7]for i in ticks],fontsize=10)
        for g in s['source_gaps']['known_calendar_missing_dates']:
            if dates[0]<=g<=dates[-1]:
                k=next((i for i,d in enumerate(dates)if d>g),None)
                if k is not None:ax.axvline(k-.5,ymin=0,ymax=.04,color='#c48b24',lw=2)
        if markers:
            for n,(d,dx,dy) in enumerate([('2026-06-04',-3,1.35),('2026-06-08',-1,-1.10),('2026-06-09',-1,1.4),('2026-06-22',-3,.65),('2026-06-24',1,.6)],1):
                x=ix[d];y=float(events[d]['bar']['close']);ax.scatter([x],[y],s=20,color='#273d56',zorder=5)
                ax.annotate(str(n),xy=(x,y),xytext=(x+dx,y+dy),fontsize=11,color='#273d56',ha='center',arrowprops={'arrowstyle':'-','color':'#60758d','lw':.8},bbox={'boxstyle':'circle,pad=.20','facecolor':'white','edgecolor':'#60758d','lw':.7})
        return q
    def save(f,name,q):
        p=ROOT/(name+'.png');f.savefig(p,dpi=130);pdf.savefig(f);plt.close(f)
        d0=date.fromisoformat(q[0]['date']);d1=date.fromisoformat(q[-1]['date']);y=d1.year;m=d1.month-6
        if m<1:y-=1;m+=12
        assert d0<=date(y,m,min(d1.day,calendar.monthrange(y,m)[1]))
        manifest.append({'image':p.name,'sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'start':q[0]['date'],'end':q[-1]['date'],'saved_bars':len(q),'at_least_six_calendar_months':True})
    
    f=plt.figure(figsize=(20,11),facecolor='white')
    txt(f,.055,.95,'B｜由小層原高向大層原高推進：先看一年半背景',22)
    txt(f,.055,.906,'2884｜2025/1 - 2026/6保存日K。大小帶關係已答；33.20及35.50先作原價格參照，正式帶界仍未定。',12)
    txt(f,.055,.862,'棕線：2/26 H35.50；紫線：4/16 H33.20。成交量橙線為此前20筆均量，紫虛線為來源期中位量。',11)
    q=draw(f,'2025-01-02','2026-06-30',[.055,.425,.92,.385],[.055,.205,.92,.155])
    txt(f,.055,.128,'6/4收過33.20 → 6/8回下 → 6/9再收過 → 6/22收過35.50 → 6/24回35.50下，仍在33.20上。',13)
    txt(f,.055,.078,'此圖為事後路徑研究；原高參照的價格跨越、正式帶突破、量能資格與交易資格分開，不把反覆當獨立成功次數。',11)
    txt(f,.055,.034,'Raw／公司行動／完整日曆／歷史公開可得限制保持；橙色短線是已列資料缺日，不補K。',10,'#637082')
    save(f,'b-nested-path-context',q)
    
    f=plt.figure(figsize=(20,13),facecolor='white')
    txt(f,.055,.955,'B｜小層跨過後仍會返回；大層回下時，小層可能仍在上',22)
    txt(f,.055,.916,'2025/10 - 2026/6保存日K；數字對應下表。33.20、35.50是原高參照，不是已核正式大小帶價界。',12)
    txt(f,.055,.875,'量的橙線：此前20筆均量（不含當筆）；紫虛線：3/16 - 5/29共52筆中位量35.68百萬股。',11)
    q=draw(f,'2025-10-17','2026-06-30',[.055,.515,.92,.30],[.055,.355,.92,.115],True)
    cols=[.055,.47,.65,.81]
    for x,t in zip(cols,['序號／日期／價格事實','成交量（百萬股）','對來源中位量','對此前20筆均量']):txt(f,x,.293,t,11)
    labels=[('2026-06-04','1｜6/4 C33.45：上跨33.20'),('2026-06-08','2｜6/8 C32.90：回33.20下'),('2026-06-09','3｜6/9 C34.20：再次上跨33.20'),('2026-06-22','4｜6/22 C35.80：已收過35.50'),('2026-06-24','5｜6/24 C35.00：回大參照下、仍在小參照上')]
    for j,(d,label)in enumerate(labels):
        e=events[d];v=e['volume'];y=.259-j*.032
        for x,t in zip(cols,[label,f"{int(v['shares'])/1e6:.2f}",v['vs_frozen_source_median']['display_2dp']+'倍',v['vs_prior20_mean']['display_2dp']+'倍']):txt(f,x,y,t,11)
    txt(f,.055,.072,'6/4量比前一筆低，但高於兩個比較基準。倍數只描述比較結果，尚未選為帶量門檻或投票。',11)
    txt(f,.055,.029,'來源期中位量僅在5/29資料完整後顯示；所有價格、量能與結構資格分開，Raw及全部來源限制保持。',10,'#637082')
    save(f,'b-nested-path-volume',q)
    pdf.close()
    from pypdf import PdfReader
    built=PdfReader(temp_pdf)
    assert len(built.pages)==2 and all(len(page.images)==0 for page in built.pages)
    assert temp_pdf.read_bytes().rstrip().endswith(b'%%EOF')
    os.replace(temp_pdf,pdfdir/'b-nested-price-volume-path.pdf')
    (ROOT/'figure-manifest.json').write_text(json.dumps({'PDF_pages':2,'figures':manifest,'source_sha256':EXPECTED,'volume_curves':'Descriptive previous20 mean excludes current volume; frozen median not plotted before source end.'},ensure_ascii=False,indent=2)+'\n')
    assert hashlib.sha256(SOURCE.read_bytes()).hexdigest()==EXPECTED
    print(json.dumps(manifest,ensure_ascii=False,indent=2))

if __name__=='__main__':main()
