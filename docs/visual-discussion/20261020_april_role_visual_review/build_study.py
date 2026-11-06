"""Research discussion booklet. Saved OHLCV/MA/MACD only, no M1 engine execution."""
import json,hashlib,argparse
from pathlib import Path
from decimal import Decimal as D
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib import font_manager
from matplotlib.patches import Rectangle
from pypdf import PdfReader,PdfWriter
from reportlab.pdfgen import canvas
from reportlab.lib.utils import ImageReader

ap=argparse.ArgumentParser();ap.add_argument('--source',required=True);ap.add_argument('--overview',required=True);ap.add_argument('--font',required=True);ap.add_argument('--out',default=str(Path(__file__).parent));args=ap.parse_args();out=Path(args.out);pdfdir=out/'output/pdf';tmp=out/'tmp/pdfs';pdfdir.mkdir(parents=True,exist_ok=True);tmp.mkdir(parents=True,exist_ok=True)
src=Path(args.source);raw=src.read_bytes();sha=hashlib.sha256(raw).hexdigest();assert sha=='184bdef0b687ec0ab7bfcaaac2157ff7916fbc1000ef312d81b5efc0c2e73e15';p=json.loads(raw)
ix=[i for i,b in enumerate(p['bars']) if '2024-07-01'<=b['date']<='2025-06-30'];assert ix==list(range(ix[0],ix[-1]+1));rs=[{'source_index':i,'bar':p['bars'][i],'macd':p['macd'][i],'moving_averages':{s:p['moving_averages'][s][i] for s in ['20','60','130','260']}} for i in ix];rows=[r['bar'] for r in rs];dates=[b['date'] for b in rows];pos={d:i for i,d in enumerate(dates)}
font_path=args.font;font_manager.fontManager.addfont(font_path);fp=font_manager.FontProperties(fname=font_path);plt.rcParams.update({'font.family':fp.get_name(),'axes.unicode_minus':False,'font.size':11,'pdf.fonttype':3})
fig,(ax,av,am)=plt.subplots(3,1,figsize=(16,10),sharex=True,gridspec_kw={'height_ratios':[3.5,1,1.25]},layout='constrained');fig.patch.set_facecolor('#f6f8fc')
for a in [ax,av,am]:
 a.set_facecolor('white');a.grid(axis='y',color='#e6ebf2',lw=.7);a.spines[['top','right']].set_visible(False);a.set_xlim(-1,len(rs));a.axvspan(pos['2025-04-01']-.5,pos['2025-04-30']+.5,color='#fff0bd',alpha=.5)
colors=[]
for x,b in enumerate(rows):
 o,h,l,c=[float(b[k]) for k in ['open','high','low','close']];co='#d94d4b' if c>o else '#158176' if c<o else '#626d7b';colors.append(co);ax.vlines(x,l,h,color=co,lw=.8)
 if o==c:ax.hlines(c,x-.3,x+.3,color=co,lw=1)
 else:ax.add_patch(Rectangle((x-.3,min(o,c)),.6,abs(c-o),facecolor=co,edgecolor=co,lw=.5))
for s,c in [('20','#bc9127'),('60','#477cb2'),('130','#8268b1'),('260','#7d8c49')]:ax.plot([None if r['moving_averages'][s] is None else float(r['moving_averages'][s]) for r in rs],color=c,lw=1,label='原 MA'+s)
ax.set_ylim(min(float(b['low']) for b in rows)-.6,38)
labels=[('2024-07-26',35.2,'2024/7/26 原高35.20',(-18,36.7)),('2025-03-12',35.45,'2025/3/12 原高35.45\n6%於3/24確認',(-25,37.0)),('2025-04-07',29.8,'A  4/7 收29.80，紅K\n較前保存收32.40下跌\n原當日量118,749,437股',(-62,28.0)),('2025-04-10',31.2,'B  4/10 高31.20／收30.75，綠K\n較前保存收28.50上升\n6%於4/18確認',(-1,34.4)),('2025-04-22',28.5,'C  4/22 原低28.50\n6%於5/5確認',(-24,26.1)),('2025-05-13',31.4,'5/13 高31.40\n已答局部代表，僅保留背景',(5,32.5))]
for d,y,t,(dx,ty) in labels:
 ax.annotate(t,xy=(pos[d],y),xytext=(pos[d]+dx,ty),fontsize=10,color='#25415e',arrowprops={'arrowstyle':'-','color':'#8796aa','lw':1})
ax.set_ylabel('Raw 價格');ax.legend(loc='upper left',ncol=4,fontsize=9)
av.bar(range(len(rs)),[float(b['volume_shares_scaled'])/1e6 for b in rows],color=colors,width=.65);av.set_ylabel('成交量\n百萬股')
am.bar(range(len(rs)),[float(r['macd']['histogram']) for r in rs],color=['#d94d4b' if float(r['macd']['histogram'])>=0 else '#158176' for r in rs],width=.65,alpha=.6,label='原柱值');am.plot([float(r['macd']['dif']) for r in rs],color='#477cb2',lw=.9,label='原 DIF');am.plot([float(r['macd']['dea']) for r in rs],color='#bc9127',lw=.9,label='原 DEA');am.axhline(0,color='#8997aa',lw=.7);am.set_ylabel('原 MACD');am.legend(loc='upper right',ncol=3,fontsize=9)
ticks=[0]+[i for i,d in enumerate(dates) if i and d[:7]!=dates[i-1][:7]];am.set_xticks(ticks,[dates[i][:7].replace('-','/') for i in ticks],rotation=30,ha='right',fontsize=9)
fig.suptitle('第2頁｜保留前後脈絡，看四月在整體中的角色\nA 下跌、B 低位反彈、C 再下探：構成來源，還是後續反應？',fontsize=19,color='#193650')
am.set_xlabel('黃色僅提示四月閱讀位置，不是正式成員或區界。全窗原保存日K／量／均線／MACD逐筆保留，未補日曆或重算。\n先看第1頁完整全景再看本頁；A／B／C僅討論標記，來源發生與後來確認分開。',fontsize=10)
fig.savefig(out/'april-role-context.png',dpi=180)
fig.savefig(tmp/'right-context-vector.pdf')
# First page preserves the prior full overview instead of cutting it away.
overview=Path(args.overview);c=canvas.Canvas(str(tmp/'overview-page.pdf'),pagesize=(1152,720));c.setFillColorRGB(.97,.98,.99);c.rect(0,0,1152,720,fill=1,stroke=0);c.drawImage(ImageReader(str(overview)),12,10,width=1128,height=700,preserveAspectRatio=True,anchor='c');c.showPage();c.save()
w=PdfWriter()
for f in [tmp/'overview-page.pdf',tmp/'right-context-vector.pdf']:
 for pg in PdfReader(f).pages:w.add_page(pg)
w.add_metadata({'/Title':'M1 April Role - Full Context and Magnified Evidence','/Subject':'Research only; original values; formal membership unknown'})
with (pdfdir/'m1-april-role-study.pdf').open('wb') as f:w.write(f)
r=PdfReader(pdfdir/'m1-april-role-study.pdf');assert len(r.pages)==2;assert len(r.pages[1].extract_text())>200
by={b['date']:b for b in p['bars']};b77=p['core']['boxes'][76];refs={d:by[d] for d in ['2025-04-02','2025-04-07','2025-04-08','2025-04-09','2025-04-10','2025-04-11','2025-04-22','2025-05-13']};assert D(refs['2025-04-07']['close'])<D(b77['research_bounds']['low']);assert D(refs['2025-04-10']['close'])>D(b77['research_bounds']['low']);assert D(refs['2025-04-11']['close'])<D(b77['research_bounds']['low'])
e={'schema':'m1-april-role-visual-discussion/1','source_comparison_sha256':sha,'overview_png_sha256':hashlib.sha256(overview.read_bytes()).hexdigest(),'right_context_window':[dates[0],dates[-1]],'right_context_records':len(rs),'records':rs,'focus_original_bars':refs,'original_research_lower_not_formal_bound':b77['research_bounds']['low'],'question_status':'PENDING_USER_ADJUDICATION','question':'在完整大帶脈絡中，四月急跌及之後低位反彈／再下探，哪些是舊帶的構成來源，哪些僅是後續反應？可分開判讀，不必整月同一角色。','assistant_working_hypothesis_not_approved':'先將急跌記為原區之後續轉弱觀測、低位反覆單獨保留，未有歸屬依據前不自動納入舊帶構成；舊帶重要性不因而調降。','formal_structure_membership':None,'formal_end':None,'formal_clearance':None,'primary_pressure_id':None,'historical_selection_time':None,'historical_signal_eligible':False}
(out/'evidence.json').write_text(json.dumps(e,ensure_ascii=False,indent=2)+'\n');assert hashlib.sha256(src.read_bytes()).hexdigest()==sha
(out/'verification.json').write_text(json.dumps({'source_sha_unchanged':True,'right_context_records_contiguous':len(rs),'original_OHLCV_MA_MACD_string_copy':True,'pdf_pages':2,'page1_original_broad_context_reused':True,'page2_vector_graphics_and_embedded_fonts':True,'pdf_text_extraction_checked':True,'pdf_visual_QA':'PENDING_RENDER_INSPECTION','PDF_interactive_zoom_on_Android':'NOT_TESTED_NEW_BUILD','browser':'NOT_RUN_NO_LOCAL_BINARY','file_protocol':'NOT_ATTEMPTED','product_tests':'NOT_RUN','original_engines_query_CLI':'NOT_RUN'},ensure_ascii=False,indent=2)+'\n');print(json.dumps({'pages':len(r.pages),'right_records':len(rs),'pdf_bytes':(pdfdir/'m1-april-role-study.pdf').stat().st_size}))
