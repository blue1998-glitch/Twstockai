"""Fixed retrospective Work queries. Raw facts only, no strategy classifier."""
from pathlib import Path
from decimal import Decimal as D
import json,hashlib,os
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle
from matplotlib.font_manager import FontProperties
from matplotlib.backends.backend_pdf import PdfPages
from matplotlib.ticker import FormatStrFormatter
from pypdf import PdfReader

R=Path(__file__).resolve().parent
S=Path(os.environ.get('STOCK_STUDY_2884','/workspace/scratch/54685b8dac93/independent-level-review/source-data-2884.json'))
SHA='ab87a51b5b8afd076603f290b10f415bd60d31ae47c5ab2f6d9d609ad4014901'
FONT=FontProperties(fname=os.environ.get('STOCK_STUDY_FONT','/workspace/scratch/54685b8dac93/version-continuity-review/research-font.otf'))
def dump(n,x): (R/n).write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n')
def compare(v,ref):return 'ABOVE' if D(v)>D(ref) else 'BELOW' if D(v)<D(ref) else 'EQUAL'
def make_query(bars,cutoff,refdate,field,start):
    available=[b for b in bars if b['date']<=cutoff]
    ref=next(b for b in available if b['date']==refdate)
    assert refdate<start<=cutoff
    rows=[]
    for b in available:
        if b['date']>=start:
            rows.append({'bar':b,'close_relation':compare(b['close'],ref[field]),'low_relation':compare(b['low'],ref[field]),'high_relation':compare(b['high'],ref[field])})
    return {'as_of':cutoff,'reference_date':refdate,'reference_field':field,'value':ref[field],'start':start,'reference_role':'FIXED_RAW_PRICE_REFERENCE_NOT_FORMAL_BAND_EDGE','rows':rows,'formal_holding':None,'formal_success':None}
def chart(bars,start,end,title,subtitle):
    a=[b for b in bars if start<=b['date']<=end];ds=[b['date'] for b in a]
    f=plt.figure(figsize=(20,11),facecolor='white');ax=f.add_axes([.055,.34,.91,.47]);va=f.add_axes([.055,.15,.91,.14],sharex=ax)
    f.text(.055,.95,title,fontproperties=FONT,fontsize=21,color='#203548')
    f.text(.055,.906,subtitle,fontproperties=FONT,fontsize=12)
    for i,b in enumerate(a):
        o,h,l,c=[float(b[k]) for k in ['open','high','low','close']];co='#c34848' if c>=o else '#16856c'
        ax.vlines(i,l,h,color=co,lw=.8);ax.add_patch(Rectangle((i-.3,min(o,c)),.6,max(abs(c-o),.014),facecolor=co,edgecolor=co,lw=.2))
        va.bar(i,int(b['volume_shares_scaled'])/1e6,color=co,width=.65)
    for x in [ax,va]:
        x.set_xlim(-1,len(a)+2);x.grid(axis='y',alpha=.3,lw=.6);x.set_axisbelow(True)
        for edge in ['top','right']:x.spines[edge].set_visible(False)
    ax.set_ylabel('Raw價格',fontproperties=FONT);ax.yaxis.set_major_formatter(FormatStrFormatter('%.2f'));ax.tick_params(axis='x',labelbottom=False)
    va.set_ylabel('量／百萬股',fontproperties=FONT)
    step=2 if len(a)>300 else 1
    ts=[i for i,d in enumerate(ds) if (i==0 or d[:7]!=ds[i-1][:7]) and (int(d[5:7])-1)%step==0]
    va.set_xticks(ts,[ds[i][:7] for i in ts],fontsize=10)
    for g in DATA['source_gaps']['known_calendar_missing_dates']:
        if start<=g<=end:
            i=next((i for i,d in enumerate(ds) if d>g),None)
            if i is not None:ax.axvline(i-.5,ymin=0,ymax=.04,color='#bd8a2b',lw=2)
    f.text(.055,.071,'只讀保存日K；固定事後查詢，沒有歷史自動選帶證明。價、量、後續守價分開，不以最高量作成功硬門檻。',fontproperties=FONT,fontsize=11)
    f.text(.055,.034,'Raw公司行動覆蓋、完整日曆與歷史公開可得仍未全核；局部事實不等正式結構、獨立反應次數或交易資格。',fontproperties=FONT,fontsize=10,color='#64717b')
    return f,ax,va,ds
def mark(ax,ds,date,key,label,pos,color='#3a536c'):
    b=next(b for b in BARS if b['date']==date)
    ax.annotate(label,xy=(ds.index(date),float(b[key])),xytext=pos,textcoords='axes fraction',fontproperties=FONT,fontsize=11,color=color,va='top',arrowprops={'arrowstyle':'-','color':color,'lw':.8})
def refline(ax,ds,date,end,value,color):ax.hlines(float(value),ds.index(date),ds.index(end)+1,colors=color,linestyles='--',lw=1.1)
def main():
    global DATA,BARS
    assert hashlib.sha256(S.read_bytes()).hexdigest()==SHA
    DATA=json.loads(S.read_text());BARS=DATA['bars']
    queries={
      'june_lower':make_query(BARS,'2026-06-30','2026-04-16','high','2026-06-04'),
      'june_broader':make_query(BARS,'2026-06-30','2026-02-26','high','2026-06-22'),
      'july_local':make_query(BARS,'2026-07-24','2026-07-17','high','2026-07-20'),
      'july_new_high':make_query(BARS,'2026-07-24','2026-07-21','high','2026-07-22')}
    vb=[b for b in BARS if '2026-07-01'<=b['date']<='2026-07-17'];v=max(D(b['volume_shares_scaled']) for b in vb)
    frozen={'reading_scope':['2026-07-01','2026-07-17'],'saved_rows':len(vb),'max_shares':str(v),'max_dates':[b['date'] for b in vb if D(b['volume_shares_scaled'])==v],'role':'LOCAL_SAVED_WINDOW_MAX_NOT_FORMAL_BAND_OR_BASELINE','frozen_before':'2026-07-20','post_origin_does_not_update_max':True}
    out={'schema':'reference-path-review/0.1','source_sha256':SHA,'price_basis_id':DATA['price_basis_id'],'source_gaps':DATA['source_gaps'],'queries':queries,'frozen_july_volume':frozen,'cross_action_comparison_status':'NOT_USED_FOR_ECONOMIC_REACTION_OR_FORMAL_HOLDING','legacy_35_50_from_february_is_not_july_35_50_source':True,'unadjusted_old_reference_after_july_1':'NOT_PROMOTED_TO_REACTION_EVIDENCE','formal_bounds':None,'formal_merge':None,'holding_threshold':None,'volume_baseline_formula':None,'historical_signal_eligible':False}
    dump('evidence.json',out)
    (R/'tmp/pdfs').mkdir(parents=True,exist_ok=True);(R/'output/pdf').mkdir(parents=True,exist_ok=True)
    tmp=R/'tmp/pdfs/b-reference-path-review.pdf';manifest=[]
    with PdfPages(tmp) as pdf:
        f,ax,va,ds=chart(BARS,'2025-01-02','2026-06-30','B｜六月：同一條路徑，對不同高點會有不同結果','約一年半背景｜6/30收34.45，高於較近33.20、低於較大35.50；不把兩層合成單一成功／失敗')
        refline(ax,ds,'2026-04-16','2026-06-30','33.20','#43849a');refline(ax,ds,'2026-02-26','2026-06-30','35.50','#8666a8')
        mark(ax,ds,'2026-02-26','high','原前高35.50',(.64,.98),'#8666a8')
        mark(ax,ds,'2026-04-16','high','較近高33.20',(.72,.66),'#43849a')
        mark(ax,ds,'2026-06-09','close','6/9收回33.20後\n至6/30後14筆全收上',(.46,.18),'#43849a')
        mark(ax,ds,'2026-06-22','close','6/22收過35.50\n6/24又收下',(.82,.98),'#8666a8')
        mark(ax,ds,'2026-06-30','close','右端6/30 C34.45',(.81,.20))
        f.savefig(R/'b-june-layered-return.png',dpi=120);pdf.savefig(f);plt.close(f)
        manifest.append({'image':'b-june-layered-return.png','first':ds[0],'last':ds[-1],'bars':len(ds)})
        f,ax,va,ds=chart(BARS,'2025-10-01','2026-07-24','B｜七月：改用七月自身高點，不沿用除息前原數字','約十個月背景｜7/17 H35.50是新來源；右端7/24 C35.95仍低7/21的新高37.20')
        for a in [ax,va]:a.axvspan(-1,ds.index('2026-07-01')-.5,color='#ccd3dc',alpha=.20,zorder=-5);a.axvline(ds.index('2026-07-01')-.5,color='#9a7a55',ls=':',lw=1.2)
        f.text(.055,.857,'灰區保留舊背景；7/1除息日期來自公開報導，官方交易日明細仍待核，不直接用舊Raw價判回測。',fontproperties=FONT,fontsize=10,color='#6b6b72')
        refline(ax,ds,'2026-07-17','2026-07-24','35.50','#43849a');refline(ax,ds,'2026-07-21','2026-07-24','37.20','#8666a8')
        mark(ax,ds,'2026-07-17','high','新來源7/17 H35.50\n7/20 C35.85收過',(.56,.80),'#43849a')
        mark(ax,ds,'2026-07-21','high','7/21 H37.20；7/22日高相等\n截至7/24沒有收盤越過37.20',(.58,.98),'#8666a8')
        mark(ax,ds,'2026-07-24','low','7/23、24低於35.50\n兩日收盤仍高於35.50',(.34,.70),'#43849a')
        va.hlines(float(v)/1e6,ds.index('2026-07-17'),len(ds),color='#43849a',ls='--',lw=1)
        va.text(.54,.84,'7/1～17保存範圍最大量97.75百萬股\n7/20量80.23、7/21量66.29，均未超過',transform=va.transAxes,fontproperties=FONT,fontsize=10)
        f.savefig(R/'b-july-local-return.png',dpi=120);pdf.savefig(f);plt.close(f)
        manifest.append({'image':'b-july-local-return.png','first':ds[0],'last':ds[-1],'bars':len(ds)})
    rd=PdfReader(tmp);assert len(rd.pages)==2 and all(len(p.images)==0 for p in rd.pages)
    assert tmp.read_bytes().rstrip().endswith(b'%%EOF')
    dest=R/'output/pdf/b-reference-path-review.pdf';tmp.replace(dest)
    for x in manifest:x['sha256']=hashlib.sha256((R/x['image']).read_bytes()).hexdigest()
    dump('figure-manifest.json',{'figures':manifest,'pdf_sha256':hashlib.sha256(dest.read_bytes()).hexdigest(),'pages':2,'image_objects':0})
    print(json.dumps({'queries':list(queries),'frozen_volume':frozen,'figures':manifest},ensure_ascii=False))
if __name__=='__main__':main()
