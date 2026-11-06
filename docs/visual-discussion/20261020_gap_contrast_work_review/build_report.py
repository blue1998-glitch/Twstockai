"""Read-only visual research packet. Reuses prior broad-context PDF page; saved values only."""
from pathlib import Path
import argparse,json,hashlib,textwrap
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle
from matplotlib import font_manager
from pypdf import PdfReader,PdfWriter
ap=argparse.ArgumentParser();ap.add_argument('--source',required=True);ap.add_argument('--evidence',required=True);ap.add_argument('--overview-pdf',required=True);ap.add_argument('--font',required=True);ap.add_argument('--out',default=str(Path(__file__).parent));a=ap.parse_args();out=Path(a.out);tmp=out/'tmp/pdfs';pd=out/'output/pdf';tmp.mkdir(parents=True,exist_ok=True);pd.mkdir(parents=True,exist_ok=True)
raw=Path(a.source).read_bytes();assert hashlib.sha256(raw).hexdigest()=='184bdef0b687ec0ab7bfcaaac2157ff7916fbc1000ef312d81b5efc0c2e73e15';p=json.loads(raw);e=json.loads(Path(a.evidence).read_text())
font_manager.fontManager.addfont(a.font);font=font_manager.FontProperties(fname=a.font);plt.rcParams.update({'font.family':font.get_name(),'axes.unicode_minus':False,'font.size':11,'pdf.fonttype':3})
ix=[i for i,b in enumerate(p['bars']) if '2024-07-01'<=b['date']<='2025-06-30'];assert ix==list(range(ix[0],ix[-1]+1));rows=[p['bars'][i] for i in ix];dates=[b['date'] for b in rows];pos={d:i for i,d in enumerate(dates)}
fig,(ax,av,am)=plt.subplots(3,1,figsize=(17,10),sharex=True,gridspec_kw={'height_ratios':[3.5,1,1.2]},layout='constrained');fig.patch.set_facecolor('#f6f8fc')
for z in [ax,av,am]:
 z.set_facecolor('white');z.grid(axis='y',color='#e5ebf2',lw=.7);z.spines[['top','right']].set_visible(False);z.set_xlim(-1,len(rows));z.axvspan(pos['2025-04-07']-.5,pos['2025-06-02']+.5,color='#dfeaf7',alpha=.42)
colors=[]
for j,b in enumerate(rows):
 o,h,l,c=[float(b[k]) for k in ['open','high','low','close']];co='#d94d4b' if c>o else '#158176' if c<o else '#626d7b';colors.append(co);ax.vlines(j,l,h,color=co,lw=.8)
 if o==c:ax.hlines(c,j-.3,j+.3,color=co,lw=1)
 else:ax.add_patch(Rectangle((j-.3,min(o,c)),.6,abs(c-o),facecolor=co,edgecolor=co,lw=.5))
for s,c in [('20','#bc9127'),('60','#477cb2'),('130','#8268b1'),('260','#7d8c49')]:ax.plot([None if p['moving_averages'][s][i] is None else float(p['moving_averages'][s][i]) for i in ix],color=c,lw=.9,label='原 MA'+s)
ax.set_ylim(min(float(b['low']) for b in rows)-.6,38.5);ax.legend(loc='upper left',ncol=4,fontsize=9);ax.set_ylabel('Raw 價格')
x1,x2=pos['2025-04-07'],pos['2025-06-02'];ax.plot([x1,x2],[37.4,37.4],color='#456c98',lw=1.5);ax.text((x1+x2)/2,37.65,'已答39筆：4/7 至 6/2',ha='center',fontsize=12,color='#234e7a')
ax.plot([x1,x2],[32.25,32.25],color='#456c98',ls='--',lw=1.1);ax.annotate('4/7前保存日低 32.25\n39筆最高31.40仍低0.85',xy=(x2,32.25),xytext=(x2-23,35.5),fontsize=10,color='#234e7a',arrowprops={'arrowstyle':'-','color':'#7891ae'})
ax.plot([pos['2025-05-14'],x2],[30.90,30.90],color='#a05782',ls=':',lw=1.2)
labels=[('2025-03-12',35.45,'3/12 原高35.45',(-28,36.7)),('2025-04-07',29.8,'A 4/7 跳空後\nABC已確認自己一區',(-54,28.0)),('2025-04-10',31.2,'B 4/10 高31.20\n只進入部分缺口',(-68,35.4)),('2025-04-22',28.5,'C 4/22 低28.50',(-20,26.1)),('2025-05-14',30.5,'D 5/14 區間內再跳空\n前低30.90 ＞ 當日高30.50',(-18,25.3))]
for d,y,t,(dx,ty) in labels:
 ax.annotate(t,xy=(pos[d],y),xytext=(pos[d]+dx,ty),fontsize=10,color='#283f5b' if d!='2025-05-14' else '#8a3e6a',arrowprops={'arrowstyle':'-','color':'#8796aa','lw':1})
av.bar(range(len(rows)),[float(b['volume_shares_scaled'])/1e6 for b in rows],color=colors,width=.65);av.set_ylabel('成交量\n百萬股')
am.bar(range(len(rows)),[float(p['macd'][i]['histogram']) for i in ix],color=['#d94d4b' if float(p['macd'][i]['histogram'])>=0 else '#158176' for i in ix],width=.65,alpha=.6,label='原柱值');am.plot([float(p['macd'][i]['dif']) for i in ix],color='#477cb2',lw=.9,label='原 DIF');am.plot([float(p['macd'][i]['dea']) for i in ix],color='#bc9127',lw=.9,label='原 DEA');am.axhline(0,color='#8997aa',lw=.7);am.set_ylabel('原 MACD');am.legend(loc='upper right',ncol=3,fontsize=9)
ticks=[0]+[i for i,d in enumerate(dates) if i and d[:7]!=dates[i-1][:7]];am.set_xticks(ticks,[dates[i][:7].replace('-','/') for i in ticks],rotation=30,ha='right',fontsize=9)
fig.suptitle('已確認的ABC弱勢區間，內部仍可以出現跳空\n不能只因一次跳空，就強制拆掉目前這一層區間',fontsize=19,color='#193650')
am.set_xlabel('第1頁保留完整廣角。本頁全部241筆原K／量／均線／MACD，無補日曆或重算；藍底為既有已答39筆閱讀範圍。\n兩條水平線只是各次跳空前一保存日的低點，不是正式整體價界。可能更細的內部結構仍未判定。',fontsize=10)
fig.savefig(out/'gap-contrast-context.png',dpi=180);fig.savefig(tmp/'contrast-vector.pdf');plt.close(fig)
# Evidence summary: dates and labels only, no extra classification thresholds.
s=plt.figure(figsize=(17,10),facecolor='#f6f8fc');s.text(.055,.93,'本輪完成的正反對照',fontsize=23,color='#193650');s.text(.055,.885,'沿用既有附層；不重建工具、不重問已定案例、不調參湊答案。',fontsize=14,color='#4b6380')
items=[('ABC的原值支持','4/7後的既有39筆，最高日高31.40仍低於前保存日低32.25。4/10曾反彈進入部分缺口，沒有因此回到舊位置。這支持此例整段位置下移；不宣告舊帶解除。'),('區間內也有跳空','5/14當日高30.50低於5/13低30.90，相隔0.40。它仍在已答39筆區間內。可研究更細結構，但不能以跳空為由強制拆掉這一層區間。'),('日高、相等收、收過要分開','1/10原間隔0.05：1/14日高30.90先越30.80；1/15收盤等於30.80；1/16收盤才高於30.80。只保留原觀察，不重開已撤回的一月結構問題。'),('相等與缺證不補答案','4/18是原TOUCHING，不列整段在下。8/14跨待核8/13，原附層保持UNKNOWN，不混入53筆可比較下移記錄，也不跨缺日接回返路徑。')]
y=.79
for title,body in items:
 s.text(.055,y,title,fontsize=16,color='#234e7a',weight='bold');lines='\n'.join(textwrap.wrap(body,64,break_long_words=True,break_on_hyphens=False));s.text(.055,y-.047,lines,fontsize=12.5,color='#253b53',va='top',linespacing=1.65);y-=.165
s.text(.055,.08,'原成品1,213筆：53筆整段在下、31筆整段在上、43筆接觸、1,079筆重疊；6筆連續性不足＋首筆無前值。',fontsize=11,color='#4b6380')
s.text(.055,.043,'這些是保存Raw原值的研究證據，不是53個獨立型態、策略成功率或自動歸屬規則；歷史訊號資格維持false。',fontsize=11,color='#4b6380')
s.savefig(tmp/'summary.pdf');plt.close(s)
w=PdfWriter();prior=PdfReader(a.overview_pdf);w.add_page(prior.pages[0])
for name in ['contrast-vector.pdf','summary.pdf']:
 for pg in PdfReader(tmp/name).pages:w.add_page(pg)
w.add_metadata({'/Title':'M1 Gap Contrast - Broad Context and Existing Range','/Subject':'User-confirmed ABC case, original reaction facts, no automatic classifier'})
final=pd/'m1-gap-contrast-research.pdf'
with final.open('wb') as f:w.write(f)
r=PdfReader(final);assert len(r.pages)==3
assert [im.data for im in r.pages[0].images]==[im.data for im in prior.pages[0].images]
assert len(r.pages[2].extract_text())>200
assert hashlib.sha256(Path(a.source).read_bytes()).hexdigest()==hashlib.sha256(raw).hexdigest()
vpath=out/'verification.json';v=json.loads(vpath.read_text());v['PDF_visual_QA']='PENDING_RENDER_INSPECTION';v['pdf_pages']=3;v['first_page_original_overview_image_bytes_unchanged']=True;v['page2_original_records']=len(rows);v['PDF_text_extract_checked']=True;v['pdf_sha256']=hashlib.sha256(final.read_bytes()).hexdigest();v['png_sha256']=hashlib.sha256((out/'gap-contrast-context.png').read_bytes()).hexdigest();vpath.write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n');print(json.dumps({'pages':len(r.pages),'right_records':len(rows),'pdf_bytes':final.stat().st_size,'first_page_original_image_exact':True}))
