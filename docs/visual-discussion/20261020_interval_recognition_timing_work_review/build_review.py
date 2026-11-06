"""Read-only source truncation and vector plots; never invoke M1 or recompute indicators."""
from pathlib import Path
import json,hashlib,re,argparse
from datetime import datetime,timezone
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages
from matplotlib.font_manager import FontProperties
from matplotlib.patches import Rectangle
import numpy as np

ap=argparse.ArgumentParser();ap.add_argument('--html',default='independent-level-review/input/M1_v019_graph_recognition_v01.html');ap.add_argument('--font',default='version-continuity-review/research-font.otf');ap.add_argument('--out',default=str(Path(__file__).parent));a=ap.parse_args();out=Path(a.out);(out/'output/pdf').mkdir(parents=True,exist_ok=True)
sha=lambda x:hashlib.sha256(x).hexdigest()
canon=lambda x:json.dumps(x,sort_keys=True,ensure_ascii=False,separators=(',',':'),allow_nan=False).encode()
raw=Path(a.html).read_bytes();assert sha(raw)=='fbca1e1d7e82d5dc9dcca8da0d3c8619f59431c1119d2cd8cb4c8ffc8293a724'
t=json.loads(re.search(r'id="payload"[^>]*>(.*?)</script>',raw.decode(),re.S).group(1));memo={}
def get(i):
 if i not in memo:
  n=t['nodes'][i];memo[i]=n[1]if n[0]=='s'else[get(j)for j in n[1:]]if n[0]=='a'else{k:get(v)for k,v in n[1:]}
 return memo[i]
b=get(t['root']);assert 'sha256:'+sha(canon({k:v for k,v in b.items()if k!='artifact_id'}))==b['artifact_id'];s=next(x for x in b['series']if x['code']=='2884')
ex=json.loads(Path('independent-level-review/source-data-2884.json').read_text());assert all(ex[k]==s[k]for k in ['bars','macd','moving_averages','numeric_frame_ids']);assert sha(Path('independent-level-review/source-data-2884.json').read_bytes())=='ab87a51b5b8afd076603f290b10f415bd60d31ae47c5ab2f6d9d609ad4014901'
bars=s['bars'];frames=[]
for cut in ['2026-10-07','2026-10-14']:
 n=next(i+1 for i,z in enumerate(bars)if z['date']==cut);r=next((r for r in s['results']if r['as_of']==cut),None)
 if r:assert 'sha256:'+sha(canon({k:v for k,v in r.items()if k!='result_id'}))==r['result_id']and r['source_records']==n
 seq={'bars':bars[:n],'macd':s['macd'][:n],'moving_averages':{k:v[:n]for k,v in s['moving_averages'].items()}}
 assert all(z['date']<=cut for z in seq['bars'])and len(seq['macd'])==n and all(len(v)==n for v in seq['moving_averages'].values())
 frames.append({'cutoff':cut,'source_records':n,'last_bar':bars[n-1],'last_saved_macd':s['macd'][n-1],'source_values_fingerprint':'sha256:'+sha(canon(seq)),'saved_core_result_id':r['result_id']if r else None,'saved_numeric_frame_id':s['numeric_frame_ids'].get(cut),'core_snapshot_qualification':'ORIGINAL_SAVED_RESULT_READ_NOT_RECOMPUTED'if r else'NO_SAVED_RESULT_AT_THIS_CUTOFF_RAW_AND_SAVED_INDICATORS_TRUNCATED_ONLY','prefix_interval_sufficient':None,'historical_selection_time':None,'historical_signal_eligible':False,'primary_pressure_id':None})
assert frames[0]['saved_core_result_id']is None and frames[0]['saved_numeric_frame_id']is None
font=FontProperties(fname=a.font);plt.rcParams.update({'pdf.fonttype':3,'axes.unicode_minus':False,'font.size':10})
def txt(ax,x,y,v,**kw):return ax.text(x,y,v,fontproperties=font,**kw)
pages=[]
pdf=out/'output/pdf/m1-2884-recognition-timing.pdf'
with PdfPages(pdf)as pp:
 for page,(start,cut,title)in enumerate([('2021-10-18','2026-10-07','長背景｜只顯示至 2026/10/7'),('2026-05-01','2026-10-07','截點 A｜只顯示至 2026/10/7'),('2026-05-01','2026-10-14','截點 B｜只顯示至 2026/10/14')],1):
  inds=[i for i,z in enumerate(bars)if start<=z['date']<=cut];rows=[bars[i]for i in inds];x=np.arange(len(rows));fig,axs=plt.subplots(3,1,figsize=(17,11),sharex=True,gridspec_kw={'height_ratios':[5,1.3,1.6]});fig.subplots_adjust(left=.065,right=.97,top=.87,bottom=.15,hspace=.08)
  fig.text(.065,.955,'2884 玉山金｜整理辨認時點複核',fontproperties=font,fontsize=20,weight='bold');fig.text(.065,.915,title,fontproperties=font,fontsize=15)
  for j,z in enumerate(rows):
   o,h,l,c=[float(z[k])for k in ['open','high','low','close']];color='#c43d3d'if c>=o else'#168467';axs[0].vlines(j,l,h,color=color,lw=.65 if page==1 else 1);axs[0].add_patch(Rectangle((j-.32,min(o,c)),.64,max(abs(c-o),.025),facecolor=color,edgecolor=color,lw=.4));axs[1].bar(j,int(z['volume_shares_scaled'])/1e6,color=color,width=.68)
  for window,col in [('20','#d38700'),('60','#4169aa')]:
   vals=[s['moving_averages'][window][i]for i in inds];axs[0].plot(x,[float(v)if v is not None else np.nan for v in vals],color=col,lw=1,label='MA'+window+' (saved)')
  for key,col in [('dif','#4169aa'),('dea','#d38700')]:axs[2].plot(x,[float(s['macd'][i][key])if s['macd'][i][key]is not None else np.nan for i in inds],color=col,lw=.9,label=key.upper())
  hist=[float(s['macd'][i]['histogram'])if s['macd'][i]['histogram']is not None else np.nan for i in inds];axs[2].bar(x,hist,color=['#c43d3d'if v>=0 else'#168467'for v in hist],width=.65);axs[2].axhline(0,color='#999',lw=.6)
  for ax in axs:ax.grid(axis='y',alpha=.18);ax.set_axisbelow(True);ax.set_xlim(-1,len(rows));ax.tick_params(labelsize=9)
  axs[0].set_ylabel('Price (raw candidate)');axs[1].set_ylabel('Vol / 1M shares');axs[2].set_ylabel('MACD (saved)');axs[0].legend(loc='upper left',frameon=False,ncol=2,fontsize=9);axs[2].legend(loc='upper left',frameon=False,ncol=2,fontsize=8)
  if page>1:
   axs[0].set_ylim(28,51)
   for date,field,label,offset in [('2026-09-17','high','9/17 日高 47.35',(-105,30)),('2026-10-01','low','10/1 日低 44.20',(-80,-36))]:
    j=next(i for i,z in enumerate(rows)if z['date']==date);axs[0].annotate(label,(j,float(rows[j][field])),xytext=offset,textcoords='offset points',fontproperties=font,fontsize=10,arrowprops={'arrowstyle':'-','color':'#555'})
  ticks=np.unique(np.linspace(0,len(rows)-1,9,dtype=int));axs[2].set_xticks(ticks,[rows[j]['date']for j in ticks],rotation=15,ha='right')
  fig.text(.065,.085,'來源：原真實圖保存的 Raw_CANDIDATE 價量及指標；未重算核心、MA 或 MACD。日序列僅至圖示截點。',fontproperties=font,fontsize=10)
  fig.text(.065,.059,'事後截點複核，非盲測或歷史訊號；整理是否已可辨認待判讀。標示日高／日低不代表正式區界或成員。',fontproperties=font,fontsize=10)
  qual='10/7 無獨立保存核心快照，本頁只截取原價量與保存指標。'if cut=='2026-10-07'else'10/14 有原保存核心快照；本頁仍未替人工整理補上歷史選取時間。'
  fig.text(.065,.031,qual+'  公司行動與當時公開可得性未核。',fontproperties=font,fontsize=10);fig.text(.94,.031,str(page),fontsize=10)
  pp.savefig(fig);fig.savefig(out/f'page-{page}.png',dpi=150);plt.close(fig)
  pages.append({'page':page,'start':rows[0]['date'],'cutoff':rows[-1]['date'],'plotted_records':len(rows),'last_bar':rows[-1],'source_indices':[inds[0],inds[-1]],'price_y_limits':[28,51]if page>1 else'AUTO_FROM_PREFIX_ONLY','future_rows':0,'MA_and_MACD':'SAVED_VALUES_SLICED_NOT_RECOMPUTED'})
doc={'schema':'m1-interval-recognition-timing-review/1','study_selected_at':datetime.now(timezone.utc).isoformat(),'source_html_sha256':sha(raw),'source_artifact_id':b['artifact_id'],'code':'2884','frames':frames,'pages':pages,'full_chart_interval_label':'USER_CONFIRMED_PRESERVED','new_question':'只看截至10/7的資料，是否已足以辨認這個整理區間？還需要10/7以後更多K線才足夠？','new_question_status':'PENDING_USER_REVIEW','qualification':'RETROSPECTIVE_TRUNCATED_REVIEW_NOT_BLIND_NOT_HISTORICAL_SIGNAL','no_exact_first_day_requested':True,'formal_membership_bounds_importance_lifecycle':'UNKNOWN','primary_pressure_id':None,'historical_signal_eligible':False,'engine_and_indicator_recomputations':0}
(out/'timing-evidence.json').write_text(json.dumps(doc,ensure_ascii=False,indent=2)+'\n')
assert sha(Path(a.html).read_bytes())==sha(raw)
print(json.dumps({'pages':pages,'frames':[{k:z[k]for k in ['cutoff','source_records','saved_core_result_id']}for z in frames],'PDF_bytes':pdf.stat().st_size,'engine_runs':0},ensure_ascii=False))
