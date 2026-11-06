"""Read-only research excerpt. Does not import or execute any M1 engine.
Run from repository root with --source <original comparison-data.json> --font <CJK font>.
"""
import argparse, hashlib, json
from pathlib import Path
from decimal import Decimal
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle
from matplotlib.font_manager import FontProperties

ap=argparse.ArgumentParser();ap.add_argument('--source',required=True);ap.add_argument('--font',required=True);ap.add_argument('--out',default=str(Path(__file__).parent));args=ap.parse_args()
out=Path(args.out);out.mkdir(parents=True,exist_ok=True)
raw=Path(args.source).read_bytes();digest=hashlib.sha256(raw).hexdigest()
assert digest=='184bdef0b687ec0ab7bfcaaac2157ff7916fbc1000ef312d81b5efc0c2e73e15'
p=json.loads(raw); indices=[i for i,b in enumerate(p['bars']) if '2024-11-01'<=b['date']<='2025-02-14']
assert indices==list(range(indices[0],indices[-1]+1))
b74,b76=p['core']['boxes'][73],p['core']['boxes'][75]
assert b76['source_turn_ids'][:-1]==b74['source_turn_ids']
pivot=next(v for v in p['core']['pivots'] if v['id']==b76['source_turn_ids'][-1])
assert (pivot['occurred_at'],pivot['price'],pivot['confirmed_at'])==('2025-01-13','30.05','2025-02-12')
records=[{'source_index':i,'bar':p['bars'][i],'macd':p['macd'][i],'ma20':p['moving_averages']['20'][i],'ma60':p['moving_averages']['60'][i]} for i in indices]
for r in records:
 i=r['source_index'];assert r['bar']==p['bars'][i] and r['macd']==p['macd'][i]
rows=[r['bar'] for r in records];dates=[b['date'] for b in rows];pos={d:i for i,d in enumerate(dates)}
lookup={b['date']:b for b in p['bars']}
checks=[]
for d,expected in [('2025-01-10','BELOW'),('2025-01-15','EQUAL'),('2025-01-16','ABOVE')]:
 c=Decimal(lookup[d]['close']);old=Decimal(b74['research_bounds']['low']);relation='BELOW' if c<old else 'ABOVE' if c>old else 'EQUAL';assert relation==expected
 checks.append({'date':d,'close':lookup[d]['close'],'old_reference':str(old),'relation':relation})
evidence={'status':'ASSISTANT_RESEARCH_PENDING_USER_ADJUDICATION','source_sha256':digest,'source_core_result_id':p['core'].get('result_id'), 'display_window':['2024-11-01','2025-02-14'],'records':records,'box_B74':{k:b74[k] for k in ['id','confirmed_at','research_bounds','source_turn_ids']},'box_B76':{k:b76[k] for k in ['id','confirmed_at','research_bounds','source_turn_ids']},'new_pivot':pivot,'exact_close_checks':checks,'prefix_extension':True,'historical_selection_time':None,'historical_signal_eligible':False,'primary_pressure_id':None,'chart_kind':'STATIC_RESEARCH_EXCERPT_FROM_ORIGINAL_SAVED_STRINGS_NOT_PRODUCT_SCREENSHOT','macd':'SAVED_VALUES_ONLY_NO_RECOMPUTATION','calendar':'SAVED_RECORDS_ONLY_NOT_CERTIFIED_EXHAUSTIVE','no_retroactive_boundary':True}
(out/'evidence.json').write_text(json.dumps(evidence,ensure_ascii=False,indent=2)+'\n')
font=FontProperties(fname=args.font); plt.rcParams.update({'font.family':font.get_name(),'axes.unicode_minus':False,'font.size':12})
from matplotlib import font_manager
font_manager.fontManager.addfont(args.font)
fig,(ax,av,am)=plt.subplots(3,1,figsize=(14,11),sharex=True,gridspec_kw={'height_ratios':[3.4,1,1.4]},layout='constrained')
fig.patch.set_facecolor('#f6f8fc')
for a in [ax,av,am]:
 a.set_facecolor('white');a.grid(axis='y',color='#e5e9f0',linewidth=.7);a.spines[['top','right']].set_visible(False);a.set_xlim(-1,len(rows));a.tick_params(labelsize=10)
colors=[]
for x,b in enumerate(rows):
 o,h,l,c=[float(b[k]) for k in ['open','high','low','close']];color='#d74949' if c>o else '#168276' if c<o else '#596575';colors.append(color)
 ax.vlines(x,l,h,color=color,lw=1.1)
 if c==o:ax.hlines(c,x-.3,x+.3,color=color,lw=1.8)
 else:ax.add_patch(Rectangle((x-.3,min(o,c)),.6,abs(c-o),facecolor=color,edgecolor=color))
ax.plot(range(len(rows)),[float(r['ma20']) for r in records],color='#c5902c',lw=1.2,label='原 MA20')
ax.plot(range(len(rows)),[float(r['ma60']) for r in records],color='#6a63ad',lw=1.2,label='原 MA60')
ax.plot([pos['2024-12-20'],len(rows)-.4],[30.80,30.80],color='#2563a6',lw=1.8,label='舊研究下緣 30.80（12/20起已確認）')
ax.plot([pos['2025-02-12'],len(rows)-.4],[30.05,30.05],color='#a55c1b',ls='--',lw=2,label='新增研究下緣 30.05（2/12起才確認）')
for a in [ax,av,am]: a.axvspan(pos['2025-01-10']-.5,pos['2025-01-16']+.5,color='#e8f0fd',alpha=.6)
ax.annotate('11/25 高 34.20\n12/20 才確認',xy=(pos['2024-11-25'],34.2),xytext=(pos['2024-11-25']-10,34.65),arrowprops={'arrowstyle':'-','color':'#65738a'},fontsize=11)
ax.annotate('1/10 收 30.25\n低於當時 30.80',xy=(pos['2025-01-10'],30.25),xytext=(pos['2025-01-10']-17,29.55),arrowprops={'arrowstyle':'-','color':'#2563a6'},fontsize=11,color='#174d80')
ax.annotate('1/13 日低 30.05\n這天尚未確認為新增來源',xy=(pos['2025-01-13'],30.05),xytext=(pos['2025-01-13']+3,29.15),arrowprops={'arrowstyle':'-','color':'#a55c1b'},fontsize=11,color='#864719')
ax.annotate('1/15 收 30.80：相等\n1/16 收 30.95：在上',xy=(pos['2025-01-16'],30.95),xytext=(pos['2025-01-16']+5,32.25),arrowprops={'arrowstyle':'-','color':'#2563a6'},fontsize=11,color='#174d80')
ax.axvline(pos['2025-02-12'],color='#a55c1b',ls=':',lw=1.1)
ax.annotate('2/12 新低點來源確認\nB76 才出現',xy=(pos['2025-02-12'],31.9),xytext=(pos['2025-02-12']-12,33.5),arrowprops={'arrowstyle':'-','color':'#a55c1b'},fontsize=11,color='#864719')
ax.set_ylim(28.85,35.25);ax.set_ylabel('Raw 價格');ax.legend(loc='upper right',fontsize=9,framealpha=.95)
fig.suptitle('1101｜跌到舊界下再回升：結構延續，還是需要另分段？\n原資料局部研究圖・2024/11/01–2025/02/14',fontproperties=font,fontsize=19,color='#18304b')
av.bar(range(len(rows)),[float(b['volume_shares_scaled'])/1e6 for b in rows],color=colors,width=.6);av.set_ylabel('成交量\n百萬股')
am.bar(range(len(rows)),[float(r['macd']['histogram']) for r in records],color=['#d74949' if float(r['macd']['histogram'])>=0 else '#168276' for r in records],width=.6,alpha=.65,label='原柱值')
am.plot([float(r['macd']['dif']) for r in records],color='#2563a6',lw=1.2,label='原 DIF');am.plot([float(r['macd']['dea']) for r in records],color='#b97b23',lw=1.2,label='原 DEA');am.axhline(0,color='#7a879a',lw=.8);am.set_ylabel('原 MACD');am.legend(loc='upper left',fontsize=9,ncol=3)
ticks=sorted(set(range(0,len(rows),7))|{pos['2025-01-10'],pos['2025-02-12'],len(rows)-1});am.set_xticks(ticks,[dates[i][5:].replace('-','/') for i in ticks],rotation=45,ha='right')
am.set_xlabel('每根為一筆原保存日K；未補日曆。紅／綠依收開，並非較前收漲跌。\n新繪研究摘圖，非互動頁截圖；完整舊箱與人工整體不以此視窗裁界。',fontsize=10)
fig.savefig(out/'january-continuity.png',dpi=150)
assert hashlib.sha256(Path(args.source).read_bytes()).hexdigest()==digest
(out/'verification.json').write_text(json.dumps({'source_sha_unchanged':True,'all_saved_window_records':len(records),'contiguous_source_indices':True,'original_OHLCV_MACD_MA_exact_string_copy':True,'original_prefix_relation_verified':True,'exact_close_comparisons':checks,'new_core_tests':'NOT_RUN','browser':'NOT_RUN','Android':'NOT_TESTED_NEW_BUILD','image_visual_inspection':'PENDING_SEPARATE_INSPECTION','font_source':'https://raw.githubusercontent.com/notofonts/noto-cjk/main/Sans/OTF/TraditionalChinese/NotoSansCJKtc-Regular.otf','font_sha256':hashlib.sha256(Path(args.font).read_bytes()).hexdigest()},ensure_ascii=False,indent=2)+'\n')
print(json.dumps({'records':len(records),'image':str(out/'january-continuity.png'),'sha256_source':digest},ensure_ascii=False))
