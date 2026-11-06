"""Add one current evidence page; reuse first two already-confirmed gap-study chart pages."""
from pathlib import Path
import json,hashlib,argparse
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib import font_manager
from pypdf import PdfReader,PdfWriter
ap=argparse.ArgumentParser();ap.add_argument('--prior',default='gap-contrast-review/output/pdf/m1-gap-contrast-research.pdf');ap.add_argument('--font',default='version-continuity-review/research-font.otf');ap.add_argument('--out',default=str(Path(__file__).parent));a=ap.parse_args();root=Path(a.out);tmp=root/'tmp/pdfs';pdfdir=root/'output/pdf';tmp.mkdir(parents=True,exist_ok=True);pdfdir.mkdir(parents=True,exist_ok=True)
prior=Path(a.prior);raw=prior.read_bytes();assert hashlib.sha256(raw).hexdigest()=='b3d25d98845622ff14e8391043982c942a04ec423bc1cd1cf9857ecb93163afb';old=PdfReader(prior);assert len(old.pages)==3
e=json.loads((root/'evidence.json').read_text());font_manager.fontManager.addfont(a.font);plt.rcParams.update({'font.family':font_manager.FontProperties(fname=a.font).get_name(),'pdf.fonttype':3,'axes.unicode_minus':False})
f=plt.figure(figsize=(17,11),facecolor='white');f.text(.06,.94,'人工區間涵蓋哪些K線，不能只由轉折清單決定',fontsize=23,weight='bold',color='#233d57')
f.text(.06,.895,'ABC同屬自己的跳空下跌、更弱勢區間：已確認。本頁核原來源身分，不重問原案例。',fontsize=13)
f.text(.06,.85,'原39筆中：4個日期有確認轉折，跨尺度共8筆；另35筆沒有原轉折或同價日期別名。這不是漏判率。',fontsize=12)
rows=[['A，4/7','已確認在ABC內','全部原尺度皆無','跳空原K存在；不能因不是轉折而漏掉A。'],['B，4/10','已確認在ABC內','3%：4/11；6%：4/18確認','同日同價、確認不同；不能合併成兩票。'],['C，4/22','已確認在ABC內','3%：4/29；6%：5/5確認','原值先發生，轉折後確認；不倒填資格。'],['5/13','原已答局部代表','3%：5/14；6%：5/27確認','31.40只保留局部代表，不升整體主壓力。'],['6/2','原39筆的末筆','全部原尺度皆無','沒有末端轉折，也不擅自延到下一轉折。'],['6/3','原已答排除此箱','3%：6/5確認','轉折存在，仍不能因此納入這個區間。']]
ax=f.add_axes([.06,.43,.88,.36]);ax.axis('off');tab=ax.table(cellText=rows,colLabels=['原日期／標記','既有人工判讀','原轉折資格','應保留的差別'],colWidths=[.12,.18,.27,.43],cellLoc='left',bbox=[0,0,1,1]);tab.auto_set_font_size(False);tab.set_fontsize(10)
for (r,c),cell in tab.get_celld().items():cell.PAD=.045;cell.set_edgecolor('#d5dee8');cell.set_facecolor('#e7eef6' if r==0 else ('#f5f8fb' if r%2 else 'white'))
lines=[('三件事分開記錄','原K線涵蓋範圍、原確認轉折、原箱引用關係分欄；完整原來源正式成員表仍未定。'),('不能直接用原箱替代','B44／B80來源4/8至5/13；研究低28.45。原39筆末日6/2低27.65，相差0.80。'),('這個差值不產生新界線','27.65只是已選範圍的Raw最低；不補正式箱底，不由此宣告破底、解除或新生命階段。'),('已有資料足夠保留此差別','原reaction_facts已有完整日K；source-query本來只查原轉折，不是工具故障，無需重做。')]
y=.37
for title,body in lines:
 f.text(.06,y,title,fontsize=12,weight='bold',color='#315e86');f.text(.24,y,body,fontsize=11);y-=.055
f.text(.06,.12,'後兩頁沿用已裁決圖冊的兩頁原圖：597筆廣角、241筆原價量／MA／MACD；A／B／C與內部D跳空標記保持。',fontsize=10)
f.text(.06,.085,'凍結1101至2026-10-16，收27.30，非即時行情。Raw公司行動／歷史可得未核；OHLC不證日內先後。',fontsize=10)
f.text(.06,.05,'primary_pressure_id=null；歷史訊號資格false。未跑新產品／瀏覽器／Android驗收，不新增自動歸屬或買賣規則。',fontsize=10)
f.savefig(tmp/'current-evidence.pdf');f.savefig(root/'source-coverage-summary.png',dpi=150);plt.close(f)
w=PdfWriter();w.add_page(PdfReader(tmp/'current-evidence.pdf').pages[0]);w.add_page(old.pages[0]);w.add_page(old.pages[1]);w.add_metadata({'/Title':'M1 Source Coverage - Current Case Judgment and Original Broad Charts','/Subject':'Raw bars, original pivots and box references remain distinct. ABC already user-confirmed.'})
final=pdfdir/'m1-source-coverage-research.pdf'
with final.open('wb')as st:w.write(st)
new=PdfReader(final);assert len(new.pages)==3
for i in range(2):
 assert new.pages[i+1].get_contents().get_data()==old.pages[i].get_contents().get_data()
 assert [im.data for im in new.pages[i+1].images]==[im.data for im in old.pages[i].images]
assert len(new.pages[0].extract_text())>200
v=json.loads((root/'verification.json').read_text());v.update({'new_PDF_pages':3,'original_two_chart_page_content_streams_and_images_exact':'PASS_NO_CHART_REDRAW','new_summary_text_extraction':'PASS_OVER_200_CHARACTERS','original_PDF_sha256':hashlib.sha256(raw).hexdigest(),'final_PDF_sha256':hashlib.sha256(final.read_bytes()).hexdigest(),'PDF_QA':'PENDING_RENDER_INSPECTION'})
(root/'verification.json').write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n');print(final)
