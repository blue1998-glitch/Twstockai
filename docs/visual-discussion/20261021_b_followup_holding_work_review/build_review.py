"""Reuse broad context page; add a long-context follow-up comparison page."""
from pathlib import Path
import json,os,hashlib
from datetime import date
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle
from matplotlib.font_manager import FontProperties
from matplotlib.ticker import FormatStrFormatter
from matplotlib.backends.backend_pdf import PdfPages
from pypdf import PdfReader,PdfWriter
from study_followup import ROOT,SOURCE,EXPECTED

def main():
    src=json.loads(SOURCE.read_text());bs=src['bars']; data=json.loads((ROOT/'episode-summaries.json').read_text())
    assert hashlib.sha256(SOURCE.read_bytes()).hexdigest()==EXPECTED
    font=FontProperties(fname=os.environ.get('STOCK_STUDY_FONT','/workspace/scratch/54685b8dac93/version-continuity-review/research-font.otf'))
    out=ROOT/'output/pdf';tmp=ROOT/'tmp/pdfs';out.mkdir(parents=True,exist_ok=True);tmp.mkdir(parents=True,exist_ok=True)
    old=Path(os.environ.get('B_PRIOR_PDF','/workspace/scratch/e9363d3b9105/b-breakout-path-research/output/pdf/b-nested-price-volume-path.pdf'))
    old_hash=hashlib.sha256(old.read_bytes()).hexdigest();assert old_hash=='c597b0c5ca8b9bb80537719200d76ec922391c214aff9f3d701cee06a8b28140'
    q=[b for b in bs if '2025-10-17'<=b['date']<='2026-06-30'];dates=[b['date']for b in q];ix={d:i for i,d in enumerate(dates)}
    fig=plt.figure(figsize=(20,12),facecolor='white')
    def text(x,y,t,size=12,c='#24384d'):fig.text(x,y,t,fontproperties=font,fontsize=size,color=c)
    text(.055,.95,'B｜突破後怎麼守價：三個觀察起點，保留不同後續',22)
    text(.055,.908,'2025/10 - 2026/6保存日K；33.20及35.50是原高參照，正式帶界與站穩判準仍未定。',12)
    text(.055,.868,'1＝6/4收過33.20；2＝6/9再收過33.20；3＝6/22收過35.50。空心圈標6/10、11低穿後收上。',11)
    ax=fig.add_axes([.055,.49,.92,.33]);va=fig.add_axes([.055,.335,.92,.105],sharex=ax)
    for i,b in enumerate(q):
        o,h,l,c=[float(b[k])for k in ('open','high','low','close')];color='#c34848'if c>=o else'#16856c'
        ax.vlines(i,l,h,color=color,lw=.9);ax.add_patch(Rectangle((i-.3,min(o,c)),.6,max(abs(c-o),.015),facecolor=color,edgecolor=color,lw=.3))
        va.bar(i,int(b['volume_shares_scaled'])/1e6,color=color,width=.65)
    for d,p,c in [('2026-02-26',35.50,'#a77b42'),('2026-04-16',33.20,'#75649a')]:ax.hlines(p,ix[d],len(q)-.5,color=c,ls='--',lw=1.3)
    for label,d,dx,dy in [('1','2026-06-04',-3,.8),('2','2026-06-09',-1,1.0),('3','2026-06-22',-2,.65)]:
        b=next(b for b in q if b['date']==d);x=ix[d];y=float(b['close']);ax.scatter([x],[y],s=24,color='#293f58',zorder=5)
        ax.annotate(label,(x,y),xytext=(x+dx,y+dy),fontsize=11,ha='center',color='#293f58',arrowprops={'arrowstyle':'-','color':'#73849c'},bbox={'boxstyle':'circle,pad=.2','facecolor':'white','edgecolor':'#73849c','lw':.7})
    for d in ('2026-06-10','2026-06-11'):
        b=next(b for b in q if b['date']==d);ax.scatter([ix[d]],[float(b['low'])],s=55,facecolors='none',edgecolors='#326c9e',lw=1.3,zorder=6)
    for ar in (ax,va):
        ar.set_xlim(-1,len(q)+.5);ar.grid(axis='y',color='#d7dfe8',lw=.5);ar.set_axisbelow(True)
        for spine in ('top','right'):ar.spines[spine].set_visible(False)
    ax.tick_params(labelbottom=False);ax.set_ylabel('Raw價格',fontproperties=font);ax.yaxis.set_major_formatter(FormatStrFormatter('%.2f'));va.set_ylabel('量／百萬股',fontproperties=font,fontsize=10)
    ticks=[0]+[i for i,d in enumerate(dates)if i and d[:7]!=dates[i-1][:7] and len(q)*.055<i<len(q)*.94]+[len(q)-1]
    va.set_xticks(ticks,[dates[i][:7]if i!=len(q)-1 else dates[i]for i in ticks],fontsize=9)
    for g in src['source_gaps']['known_calendar_missing_dates']:
        if dates[0]<=g<=dates[-1]:
            i=next(i for i,d in enumerate(dates)if d>g);ax.axvline(i-.5,ymin=0,ymax=.04,color='#c48b24',lw=2)
    columns=[.055,.335,.43,.555,.705]
    for x,t in zip(columns,['觀察起點','後續K數','首次收回下','首次再收上','截至6/30的後續價格事實']):text(x,.278,t,11)
    rows=[['1｜6/4收過33.20','17','6/8','6/9','曾收回下，之後已收回上'],['2｜6/9再收過33.20','14','未出現','—','14筆全收上；2筆低穿後收上'],['3｜6/22收過35.50','6','6/24','尚未','末5筆收下；6/25影線過收未過']]
    for j,row in enumerate(rows):
        for x,t in zip(columns,row):text(x,.232-j*.045,t,11)
    text(.055,.077,'後續K數不含突破當筆，是保存紀錄數，不是站穩天數門檻。1與2屬同參照的返回／收回歷程，非兩個獨立樣本。',11)
    text(.055,.034,'成交量保留作背景，未放量不否決；事後站穩不能倒填突破當天。Raw／公司行動／日曆／歷史可得等限制保持。',10,c='#637082')
    png=ROOT/'b-followup-holding-comparison.png';fig.savefig(png,dpi=130)
    detail=tmp/'detail.build.pdf'
    with PdfPages(detail)as pdf:pdf.savefig(fig)
    plt.close(fig)
    writer=PdfWriter();writer.append(PdfReader(old),pages=(0,1));writer.append(PdfReader(detail))
    combined=tmp/'combined.build.pdf'
    with combined.open('wb')as stream:writer.write(stream)
    built=PdfReader(combined);assert len(built.pages)==2 and all(len(p.images)==0 for p in built.pages) and combined.read_bytes().rstrip().endswith(b'%%EOF')
    final=out/'b-followup-holding-review.pdf';os.replace(combined,final)
    assert hashlib.sha256(old.read_bytes()).hexdigest()==old_hash and hashlib.sha256(SOURCE.read_bytes()).hexdigest()==EXPECTED
    assert date.fromisoformat(dates[0])<date(2025,12,30)
    (ROOT/'figure-manifest.json').write_text(json.dumps({'PDF_pages':2,'page_1':'Reused previous vector context page, 2025-01-02..2026-06-30 / 358 saved bars; not rebuilt','prior_PDF_sha256':old_hash,'page_2':{'image':png.name,'start':dates[0],'end':dates[-1],'saved_bars':len(q),'sha256':hashlib.sha256(png.read_bytes()).hexdigest()},'all_main_charts_at_least_six_calendar_months':True,'PDF_sha256':hashlib.sha256(final.read_bytes()).hexdigest(),'PDF_images_per_page':[len(p.images)for p in built.pages]},ensure_ascii=False,indent=2)+'\n')
    print(final)
if __name__=='__main__':main()
