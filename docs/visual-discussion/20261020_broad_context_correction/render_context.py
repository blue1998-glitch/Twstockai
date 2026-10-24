"""Research-only broad context. Read saved values; no M1 engine or MACD computation."""
import json,hashlib,argparse
from pathlib import Path
from decimal import Decimal
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle
from matplotlib import font_manager
ap=argparse.ArgumentParser();ap.add_argument('--source',required=True);ap.add_argument('--font',required=True);ap.add_argument('--out',default=str(Path(__file__).parent));a=ap.parse_args();out=Path(a.out);out.mkdir(parents=True,exist_ok=True)
raw=Path(a.source).read_bytes();sha=hashlib.sha256(raw).hexdigest();assert sha=='184bdef0b687ec0ab7bfcaaac2157ff7916fbc1000ef312d81b5efc0c2e73e15';p=json.loads(raw)
ix=[i for i,b in enumerate(p['bars']) if '2023-01-01'<=b['date']<='2025-06-30'];assert ix==list(range(ix[0],ix[-1]+1))
rs=[{'source_index':i,'bar':p['bars'][i],'macd':p['macd'][i],'moving_averages':{s:p['moving_averages'][s][i] for s in ['20','60','130','260']}} for i in ix]
rows=[r['bar'] for r in rs];dates=[b['date'] for b in rows];pos={d:i for i,d in enumerate(dates)}
reference_dates=['2023-05-02','2023-06-05','2023-11-28','2024-07-26','2024-09-30','2024-11-25','2025-01-13','2025-03-12']
selected=[dict(date=d,**{k:rows[pos[d]][k] for k in ['open','high','low','close','volume_shares_scaled']}) for d in reference_dates]
comparisons=[];focus=rows[pos['2024-11-25']]
for d in ['2023-11-28','2024-09-30']:
 b=rows[pos[d]]
 def rel(k):
  v,w=Decimal(focus[k]),Decimal(b[k]);return 'ABOVE' if v>w else 'BELOW' if v<w else 'EQUAL'
 comparisons.append({'focus_date':'2024-11-25','reference_date':d,'high_relation':rel('high'),'single_day_volume_relation':rel('volume_shares_scaled'),'not_a_keypoint_or_volume_threshold_rule':True})
assert comparisons[0]['high_relation']=='BELOW' and comparisons[0]['single_day_volume_relation']=='BELOW'
assert comparisons[1]['high_relation']=='EQUAL' and comparisons[1]['single_day_volume_relation']=='ABOVE'
evidence={'schema':'m1-broad-context-research/1','source_sha256':sha,'core_result_id':p['core']['result_id'],'window':[dates[0],dates[-1]],'display_only_window_not_formal_bounds':True,'record_count':len(rs),'records':rs,'selected_raw_records':selected,'descriptive_comparisons':comparisons,'reference_selection':'RETROSPECTIVE_ASSISTANT_CONTEXT_EXAMPLES_NOT_USER_APPROVED_KEYPOINTS','historical_selection_time':None,'historical_signal_eligible':False,'primary_pressure_id':None}
(out/'evidence.json').write_text(json.dumps(evidence,ensure_ascii=False,indent=2)+'\n')
font_manager.fontManager.addfont(a.font);font=font_manager.FontProperties(fname=a.font)
plt.rcParams.update({'font.family':font.get_name(),'axes.unicode_minus':False,'font.size':11})
fig,(ax,av,am)=plt.subplots(3,1,figsize=(17,11),sharex=True,gridspec_kw={'height_ratios':[3.5,1,1.2]},layout='constrained');fig.patch.set_facecolor('#f7f9fc')
for z in [ax,av,am]:
 z.set_facecolor('white');z.grid(axis='y',color='#e6ebf2',lw=.7);z.spines[['top','right']].set_visible(False);z.set_xlim(-2,len(rs)+1)
colors=[]
for x,b in enumerate(rows):
 o,h,l,c=[float(b[k]) for k in ['open','high','low','close']];color='#d94d4b' if c>o else '#158176' if c<o else '#626d7b';colors.append(color);ax.vlines(x,l,h,color=color,lw=.65)
 if c==o:ax.hlines(c,x-.35,x+.35,color=color,lw=.8)
 else:ax.add_patch(Rectangle((x-.35,min(o,c)),.7,abs(c-o),facecolor=color,edgecolor=color,lw=.35))
for s,c in [('20','#bc9127'),('60','#477cb2'),('130','#8268b1'),('260','#7d8c49')]:ax.plot([None if r['moving_averages'][s] is None else float(r['moving_averages'][s]) for r in rs],color=c,lw=.9,label='原 MA'+s)
labels=[('2023-05-02',40.25,'2023/05/02 高40.25\n較早背景，不自動納入整體',(-55,42.3)),('2023-06-05',39.25,'2023/06/05 高39.25\n較早高位來源',(25,40.8)),('2023-11-28',35.5,'2023/11/28 高35.50',(12,37.0)),('2024-07-26',35.2,'2024/07/26 高35.20',(-80,37.0)),('2024-11-25',34.2,'2024/11/25 高34.20\n使用者：本例非關鍵點',(12,36.7)),('2025-03-12',35.45,'2025/03/12 高35.45',(-4,39.0))]
for d,y,t,(dx,ty) in labels:
 x=pos[d];ax.annotate(t,xy=(x,y),xytext=(x+dx,ty),fontsize=10.5,color='#283e58',arrowprops={'arrowstyle':'-','color':'#8a99ac','lw':.9})
x1,x2=pos['2024-09-30'],pos['2024-11-25'];ax.plot([x1,x2],[34.2,34.2],ls=':',color='#7f8ea1',lw=1);ax.annotate('9/30 同高34.20',xy=(x1,34.2),xytext=(x1-48,30.9),fontsize=9.5,arrowprops={'arrowstyle':'-','color':'#8a99ac','lw':.8})
ax.annotate('1月下探位於此處\n先放回整段觀察',xy=(pos['2025-01-13'],30.05),xytext=(pos['2025-01-13']-90,28.15),fontsize=10.5,color='#385a78',arrowprops={'arrowstyle':'-','color':'#8a99ac'})
ax.set_ylim(min(float(b['low']) for b in rows)-0.5,43.8);ax.set_ylabel('Raw 價格');ax.legend(loc='lower left',ncol=4,fontsize=9)
av.bar(range(len(rs)),[float(b['volume_shares_scaled'])/1e6 for b in rows],width=.75,color=colors);av.set_ylabel('成交量\n百萬股')
for d in ['2023-11-28','2024-11-25']:
 x=pos[d];vol=float(rows[x]['volume_shares_scaled'])/1e6;av.annotate(f'{d[2:].replace(chr(45),chr(47))}：{vol:.2f}',xy=(x,vol),xytext=(x-45,vol+22),fontsize=9.5,arrowprops={'arrowstyle':'-','color':'#8796a9'})
am.bar(range(len(rs)),[float(r['macd']['histogram']) for r in rs],color=['#d94d4b' if float(r['macd']['histogram'])>=0 else '#158176' for r in rs],width=.75,alpha=.6,label='原柱值');am.plot([float(r['macd']['dif']) for r in rs],color='#477cb2',lw=.8,label='原 DIF');am.plot([float(r['macd']['dea']) for r in rs],color='#bc9127',lw=.8,label='原 DEA');am.axhline(0,color='#8a99ac',lw=.7);am.set_ylabel('原 MACD');am.legend(loc='upper right',ncol=3,fontsize=9)
ticks=[0]+[i for i,d in enumerate(dates) if i and d[:7]!=dates[i-1][:7] and d[5:7] in ['01','04','07','10']]+[len(rs)-1];am.set_xticks(ticks,[dates[i][:7].replace('-','/') for i in ticks]);am.tick_params(axis='x',labelsize=10)
fig.suptitle('1101｜先看較早高位、整段下移與後續反覆\n2023年初至2025年6月底・原保存日K／量／均線／MACD',fontsize=20,color='#193650')
am.set_xlabel('全窗每筆保存日K均呈現；無補日曆／無指標重算。此為新靜態研究圖，非瀏覽器截圖。\n2023/06–2025/04仍僅是已答月份背景；標價用來對照原值，不指定正式成員、區界或代表。',fontsize=10)
fig.savefig(out/'broad-price-volume-context.png',dpi=160)
assert hashlib.sha256(Path(a.source).read_bytes()).hexdigest()==sha
(out/'verification.json').write_text(json.dumps({'record_count':len(rs),'contiguous_indices':True,'exact_original_string_copy':True,'source_sha_unchanged':True,'display_float_only':True,'comparison_method':'Decimal high and single-day raw volume only','image_visual_inspection':'PENDING','engine_query_reaction_macd_recompute':'NOT_RUN','browser':'NOT_RUN','Android':'NOT_TESTED_NEW_BUILD'},ensure_ascii=False,indent=2)+'\n');print(json.dumps({'records':len(rs),'first':dates[0],'last':dates[-1],'comparisons':comparisons}))
