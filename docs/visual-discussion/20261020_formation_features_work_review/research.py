"""Exploratory, read-only price-path measurements. This is not an M1 classifier.

All dates are research observation settings, never detector thresholds.
No core import, new indicator, pivot, box, historical signal or label is produced.
"""
from pathlib import Path
from decimal import Decimal as D
import argparse, hashlib, json, io
from datetime import datetime, timezone
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages
from matplotlib.font_manager import FontProperties
from matplotlib.patches import Rectangle
import numpy as np

ap = argparse.ArgumentParser()
ap.add_argument('--source', required=True)
ap.add_argument('--comparison', required=True)
ap.add_argument('--font', required=True)
ap.add_argument('--out', default=str(Path(__file__).parent))
args = ap.parse_args()
out = Path(args.out); (out/'output/pdf').mkdir(parents=True, exist_ok=True)
raw = Path(args.source).read_bytes()
sha = lambda b: hashlib.sha256(b).hexdigest()
canon = lambda x: json.dumps(x, ensure_ascii=False, sort_keys=True, separators=(',', ':'), allow_nan=False).encode()
assert sha(raw) == 'ab87a51b5b8afd076603f290b10f415bd60d31ae47c5ab2f6d9d609ad4014901'
s = json.loads(raw)
cutoff = '2026-10-07'
bars = [b for b in s['bars'] if b['date'] <= cutoff]
assert len(bars) == 1207 and bars[-1]['date'] == cutoff
known_gaps = s['source_gaps']['known_calendar_missing_dates']
positive = [b for b in bars if b['date'] >= '2026-09-17']
n = len(positive)
assert n == 13

def measure(rows):
    cs = [D(b['close']) for b in rows]
    ls = [D(b['low']) for b in rows]; hs = [D(b['high']) for b in rows]
    delta = cs[-1] - cs[0]
    gross = sum((abs(b-a) for a,b in zip(cs,cs[1:])), D(0))
    signed = [b-a for a,b in zip(cs,cs[1:])]
    signs = [(v>0)-(v<0) for v in signed if v != 0]
    levels = sorted(set(ls+hs))
    cells = [{'low': str(a), 'high': str(b),
              'covering_ranges': sum(l < (a+b)/2 < h for l,h in zip(ls,hs))}
             for a,b in zip(levels,levels[1:]) if a < b]
    peak = max(c['covering_ranges'] for c in cells)
    overlaps = [min(hs[i-1],hs[i]) - max(ls[i-1],ls[i]) for i in range(1,len(rows))]
    min_low=min(ls);max_high=max(hs)
    low_last=max(i for i,v in enumerate(ls) if v==min_low)
    high_last=max(i for i,v in enumerate(hs) if v==max_high)
    return {'start':rows[0]['date'], 'end':rows[-1]['date'], 'records':len(rows),
            'net_close_change':str(delta), 'gross_close_path':str(gross),
            'directional_efficiency':str(abs(delta)/gross) if gross else None,
            'direction':'UP' if delta>0 else 'DOWN' if delta<0 else 'UNCHANGED',
            'up_close_steps':sum(v>0 for v in signed), 'down_close_steps':sum(v<0 for v in signed),
            'equal_close_steps':sum(v==0 for v in signed),
            'nonzero_close_direction_changes':sum(a!=b for a,b in zip(signs,signs[1:])),
            'positive_overlap_pairs':sum(v>0 for v in overlaps),
            'touch_only_pairs':sum(v==0 for v in overlaps), 'adjacent_pairs':len(rows)-1,
            'peak_range_coverage':peak, 'coverage_fraction':str(D(peak)/D(len(rows))),
            'peak_cells':[c for c in cells if c['covering_ranges']==peak],
            'records_since_latest_window_min_low':len(rows)-1-low_last,
            'latest_window_min_low_date':rows[low_last]['date'],
            'records_since_latest_window_max_high':len(rows)-1-high_last,
            'latest_window_max_high_date':rows[high_last]['date'],
            'last_close_position_in_observed_range':str((cs[-1]-min_low)/(max_high-min_low)) if max_high>min_low else None,
            'observed_low':str(min(ls)), 'observed_high':str(max(hs)),
            'bars_fingerprint':'sha256:'+sha(canon(rows))}

scanned=[]; excluded=[]; candidates=[]
for end in range(n-1,len(bars)):
    rows=bars[end-n+1:end+1]
    missing=[d for d in known_gaps if rows[0]['date']<=d<=rows[-1]['date']]
    if missing:
        excluded.append({'start':rows[0]['date'],'end':rows[-1]['date'],'known_gap_dates':missing})
        continue
    m=measure(rows);scanned.append(m)
    if D(m['net_close_change'])<0 and m['positive_overlap_pairs']==n-1:
        candidates.append(m)
assert candidates
ranked=sorted(candidates,key=lambda m:(-D(m['directional_efficiency']),m['start']))
selected=ranked[0]
control=[b for b in bars if selected['start']<=b['date']<=selected['end']]
profiles={name:[measure(rows[-k:]) for k in range(3,n+1)]
          for name,rows in [('reviewed_case',positive),('selected_control',control)]}
assert len(control)==n
for rows in (positive,control):
    assert all(b['date']<=cutoff for b in rows)
pm,cm=measure(positive),measure(control)
comparison_raw=Path(args.comparison).read_bytes()
assert sha(comparison_raw)=='184bdef0b687ec0ab7bfcaaac2157ff7916fbc1000ef312d81b5efc0c2e73e15'
comparison=json.loads(comparison_raw)
abc=[b for b in comparison['bars'] if '2025-04-07'<=b['date']<='2025-06-02']
assert len(abc)==39
abc_metrics=measure(abc)
assert abc_metrics['latest_window_min_low_date']=='2025-06-02'
assert abc_metrics['records_since_latest_window_min_low']==0
assert pm['positive_overlap_pairs']==cm['positive_overlap_pairs']==12
assert pm['peak_range_coverage']==cm['peak_range_coverage']==9
assert profiles['reviewed_case'][0]['directional_efficiency']==profiles['selected_control'][0]['directional_efficiency']=='1'
assert all(D(z['net_close_change'])<0 for z in profiles['selected_control'][:4])

evidence={'schema':'m1-exploratory-formation-features/1',
 'created_at_utc':datetime.now(timezone.utc).isoformat(),
 'qualification':'EXPLORATORY_SAME_SOURCE_PATH_COMPARISON_NOT_CLASSIFIER_VALIDATION',
 'source_commit':'a9b292a1b9708b31151f0f7709ba5e6d1953bd7a',
 'source_path':'docs/visual-discussion/20261020_independent_source_levels_work_review/source-data-2884.json',
 'source_sha256':sha(raw),'code':s['code'],'price_basis_id':s['price_basis_id'],
 'source_artifact_id':s['source_artifact_id'],'data_cutoff':cutoff,'cutoff_records':len(bars),
 'source_qualification':s['source_gaps'],
 'window_qualification':'13 rows from Sep17 source high through confirmed sufficient Oct7 cutoff; research window only, not approved interval start/end or general detector length.',
 'definitions':{
   'positive_overlap':'min(previous high,current high)>max(previous low,current low); equality is touch only.',
   'directional_efficiency':'abs(last close-first close)/sum(abs(each close change)); null for zero denominator. A descriptive path ratio, not probability.',
   'peak_range_coverage':'Maximum count of daily [low,high] ranges spanning one positive-width price cell. This is geometric range coverage, not trade count, price-volume distribution, or holdings.',
   'extreme_age_and_close_location':'Records since latest occurrence of observed min/max, and (last close-min low)/(max high-min low). Observational only; no confirmation, formal bound or support designation.',
   'suffix_profile':'All suffix lengths 3 through 13 are reported. No best lookback, threshold, score, vote or boundary is selected.'},
 'control_selection':{'universe':'Every 13-record saved window ending by Oct7; windows crossing listed known missing dates excluded only.',
    'all_windows':len(bars)-n+1,'excluded_known_gap_windows':len(excluded),'measured_windows':len(scanned),
    'down_close_all_adjacent_positive_overlap_candidates':len(candidates),
    'ranking':'Largest directional_efficiency among candidate windows; tie earliest start.',
    'all_measured_fingerprint':'sha256:'+sha(canon(scanned)),
    'qualification':'Retrospective extreme diagnostic selection, not blind test, independent sample, or human-negative interval label. Passing listed gaps does not authenticate full calendar or company actions.'},
 'reviewed_case':{'human_label':'RECOGNIZABLE_CONSOLIDATION_BY_OCT7','label_scope':'User cutoff sufficiency, not approval of this 13-row membership.', 'human_reviewed_at':'2026-10-20T21:46:37+08:00','metrics':pm,'bars':positive},
 'selected_control':{'human_interval_label':None,'assistant_description':'All adjacent ranges overlap, while final six closes have no upward step and a negative net move. This is not a claim of no interval at every scale.','metrics':cm,'bars':control},
 'suffix_profiles':profiles,'classifier':'NOT_IMPLEMENTED','classification_quality':'NOT_VALIDATED',
 'boundary_case':{'code':'1101','case':'ABC-own-weaker-interval','human_label':'USER_CONFIRMED_OWN_INTERVAL_RELATIVE_GAP_DOWN_WEAKER',
   'human_first_recognition_time':None,'source_comparison_sha256':sha(comparison_raw),
   'window_qualification':'Previously user-selected 39-record coverage; not exhaustive formal source membership or price bounds.',
   'metrics':abc_metrics,'bars':abc,
   'result':'A confirmed own interval can have a new observed window low at its included endpoint. Stopping new lows is not a necessary condition for all own-interval labels.',
   'not_inferred':'No formal breakdown boundary/event, all-horizon downtrend, or consolidation subtype added.'},
 'action_qualification':'NOT_EVALUATED','historical_selection_time':None,'historical_signal_eligible':False,'primary_pressure_id':None,
 'saved_core_result_at_Oct7':None,'saved_numeric_frame_at_Oct7':None}
(out/'evidence.json').write_text(json.dumps(evidence,ensure_ascii=False,indent=2)+'\n')
(out/'control-scan.json').write_text(json.dumps({'schema':'m1-diagnostic-control-scan/1','selection':evidence['control_selection'],
 'excluded':excluded,'ranked_candidates':ranked,'unlabelled_is_not_negative':True},ensure_ascii=False,indent=2)+'\n')

font=FontProperties(fname=args.font)
plt.rcParams.update({'pdf.fonttype':3,'axes.unicode_minus':False,'font.size':10})
def text(ax,x,y,t,**kw):return ax.text(x,y,t,fontproperties=font,**kw)
def label(fig,x,y,t,size=12,**kw):return fig.text(x,y,t,fontproperties=font,fontsize=size,**kw)
def plot_bars(ax,vol,rows,detail=False):
    for j,b in enumerate(rows):
        o,h,l,c=[float(b[k])for k in ['open','high','low','close']]
        color='#c44242' if c>=o else '#168268'
        ax.vlines(j,l,h,color=color,lw=1 if detail else .8)
        if c==o:ax.hlines(c,j-.32,j+.32,color=color,lw=1.1)
        else:ax.add_patch(Rectangle((j-.32,min(o,c)),.64,abs(c-o),facecolor=color,edgecolor=color,lw=.5))
        vol.bar(j,int(b['volume_shares_scaled'])/1e6,color=color,width=.68)
    for a in [ax,vol]:a.grid(axis='y',alpha=.15);a.set_axisbelow(True);a.set_xlim(-1,len(rows))
    vals=[float(b['low'])for b in rows]+[float(b['high'])for b in rows]
    span=max(vals)-min(vals);ax.set_ylim(min(vals)-span*.12,max(vals)+span*.25)
    ax.set_ylabel('原始價格',fontproperties=font);vol.set_ylabel('成交量／百萬股',fontproperties=font)
    ticks=list(range(len(rows))) if detail else np.unique(np.linspace(0,len(rows)-1,9,dtype=int))
    multi_year=rows[0]['date'][:4]!=rows[-1]['date'][:4]
    vol.set_xticks(ticks,[(rows[j]['date']if multi_year else rows[j]['date'][5:]).replace('-','/')for j in ticks],rotation=30 if detail else 15,ha='right',fontsize=9)
    ax.tick_params(labelbottom=False)

pages=[]
pdf_buffer=io.BytesIO()
with PdfPages(pdf_buffer) as pdf:
    fig=plt.figure(figsize=(17,12));gs=fig.add_gridspec(5,1,height_ratios=[3,1,.35,3,1],left=.065,right=.97,top=.87,bottom=.15,hspace=.24)
    label(fig,.065,.955,'區間形成研究：價格有重疊，仍要看它往哪裡走',21)
    label(fig,.065,.916,'2884 同源實際日線；上圖是已確認案例，下圖是機械選出的方向對照。',13)
    for k,(start,end,win,title) in enumerate([
       ('2026-05-04',cutoff,positive,'A｜10/7 已可辨認整理（使用者已確認）'),
       ('2026-01-02',selected['end'],control,'B｜相鄰日範圍全部重疊，末段仍連續走低（未取得區間標籤）')]):
        rows=[b for b in bars if start<=b['date']<=end]
        row=0 if k==0 else 3
        ax=fig.add_subplot(gs[row]);v=fig.add_subplot(gs[row+1],sharex=ax)
        plot_bars(ax,v,rows)
        ax.set_title(title,fontproperties=font,fontsize=13,loc='left',pad=10)
        j=next(i for i,b in enumerate(rows) if b['date']==win[0]['date'])
        low=min(float(b['low'])for b in win);high=max(float(b['high'])for b in win)
        ax.add_patch(Rectangle((j-.5,low),len(win),high-low,facecolor='#a58ad3',alpha=.15,edgecolor='none',zorder=-1))
        v.add_patch(Rectangle((j-.5,0),len(win),max(int(b['volume_shares_scaled'])for b in win)/1e6,facecolor='#a58ad3',alpha=.15,edgecolor='none',zorder=-1))
        text(ax,.015,.88,f"淡紫色僅為 {win[0]['date']} 至 {win[-1]['date']} 的 13 筆研究觀察窗",transform=ax.transAxes,fontsize=10)
        pages.append({'page':1,'panel':'A'if k==0 else'B','display_start':rows[0]['date'],'display_end':rows[-1]['date'],'display_records':len(rows),'future_rows':0})
    label(fig,.065,.088,'背景價量完整保留。兩個 13 筆觀察窗皆非正式區界；不同日期的市場環境未控制，不比較投資績效或重要性。',11)
    label(fig,.065,.060,'B 為事後選取的極端描述對照，不是使用者認定的整理負例。Raw 公司行動、完整日曆與歷史可得性仍未核。',10)
    label(fig,.065,.034,'原資料未改；只計算研究特徵，未重算 MA／MACD／轉折／候選箱。本頁不是產品或 Android 驗收。',10)
    pdf.savefig(fig);fig.savefig(out/'page-1.png',dpi=140);plt.close(fig)

    fig=plt.figure(figsize=(17,12));gs=fig.add_gridspec(3,2,height_ratios=[3.1,1,2.3],left=.065,right=.97,top=.86,bottom=.20,hspace=.47,wspace=.20)
    label(fig,.065,.957,'重疊程度相同，完整路徑與較短觀察卻不同',21)
    label(fig,.065,.915,'兩窗皆有 12/12 組相鄰範圍重疊，同一價位最多被 9/13 根日範圍涵蓋。這兩個數字無法表達方向。',12)
    for j,(rows,title) in enumerate([(positive,'A｜9/17 至 10/7'),(control,'B｜4/15 至 5/4')]):
        ax=fig.add_subplot(gs[0,j]);v=fig.add_subplot(gs[1,j],sharex=ax);plot_bars(ax,v,rows,True)
        ax.set_title(title,fontproperties=font,fontsize=14,loc='left')
        ax.plot(range(len(rows)),[float(b['close'])for b in rows],color='#344a6c',lw=1,alpha=.5,label='收盤走徑');ax.legend(frameon=False,loc='upper right',prop=font)
    for col,(key,title,ylabel) in enumerate([
      ('directional_efficiency','淨位移 / 累積收盤變動','位移比（非機率）'),
      ('coverage_fraction','同一價位的最大日範圍涵蓋比例','日範圍涵蓋比例（非機率）')]):
        ax=fig.add_subplot(gs[2,col])
        for name,color,lab in [('reviewed_case','#7550a0','A：已確認案例'),('selected_control','#b56a26','B：方向對照')]:
            vals=profiles[name];ax.plot([x['records']for x in vals],[float(x[key])if x[key]is not None else np.nan for x in vals],marker='o',color=color,label=lab)
        ax.set_title(title,fontproperties=font,fontsize=13,loc='left');ax.set_ylim(-.04,1.08);ax.set_xticks(range(3,n+1));ax.set_xlabel('各自截點往回看的資料筆數',fontproperties=font);ax.set_ylabel(ylabel,fontproperties=font,fontsize=10);ax.grid(alpha=.18);ax.legend(frameon=False,prop=font)
    label(fig,.065,.135,'往回看 3 筆：A 連續收高，B 連續收低；兩者位移比都是 1。必須同時保留方向與較廣背景。',12)
    label(fig,.065,.105,'A 觀察窗最低價之後已有 4 筆，末收位於窗內約 49%；B 最後一筆才刷新窗內低價，收在最低處。',11)
    label(fig,.065,.075,'完整列出 3 至 13 筆；8 筆位移比 A 約 0.055、B 約 0.897。窗長與所有數值皆未選為策略門檻。',10)
    label(fig,.065,.045,'價格涵蓋不是實際成交分布；窗內高低不是正式區界。本研究非盲測、分類準確率或買賣訊號，人工標籤範圍不變。',10)
    pages.append({'page':2,'detail_records_each':13,'suffix_lengths':list(range(3,14)),'future_rows':0})
    pdf.savefig(fig);fig.savefig(out/'page-2.png',dpi=140);plt.close(fig)

    fig=plt.figure(figsize=(17,12));gs=fig.add_gridspec(5,1,height_ratios=[3,1,.3,3,1],left=.065,right=.97,top=.87,bottom=.16,hspace=.24)
    label(fig,.065,.955,'區間存在，末端仍可能轉弱：1101 的 ABC 已確認案例',21)
    label(fig,.065,.916,'原 39 筆涵蓋包含 6/2；6/2 也刷新這個觀察窗低價。這兩件事同時成立。',13)
    context=[b for b in comparison['bars']if '2023-01-03'<=b['date']<='2025-06-02']
    for k,(rows,title)in enumerate([(context,'較廣背景｜2023/1/3 至 2025/6/2；舊大帶與較弱 ABC 區間'),(abc,'39 筆觀察｜2025/4/7 至 6/2；自己的區間，後段仍能走弱')]):
        row=0 if k==0 else 3
        ax=fig.add_subplot(gs[row]);v=fig.add_subplot(gs[row+1],sharex=ax);plot_bars(ax,v,rows,False)
        ax.set_title(title,fontproperties=font,fontsize=13,loc='left')
        if k==0:
            j=next(i for i,b in enumerate(rows)if b['date']=='2025-04-07')
            ax.add_patch(Rectangle((j-.5,min(float(b['low'])for b in abc)),39,max(float(b['high'])for b in abc)-min(float(b['low'])for b in abc),facecolor='#a58ad3',alpha=.15,edgecolor='none',zorder=-1))
        else:
            ax.annotate('6/2 低 27.65；收 27.70',xy=(38,27.65),xytext=(24,28.6),fontproperties=font,fontsize=11,arrowprops={'arrowstyle':'-','color':'#555'})
        pages.append({'page':3,'panel':'context'if k==0 else'ABC39','display_start':rows[0]['date'],'display_end':rows[-1]['date'],'display_records':len(rows),'future_rows':0})
    label(fig,.065,.100,'「末端不再創低」可輔助研究回穩，不能變成所有區間存在的必要條件；6/3 在前箱外的裁決保持不變。',12)
    label(fig,.065,.068,'39 筆為原使用者選取涵蓋；淡色只示研究範圍，不定正式箱界。圖僅至 6/2，未使用之後走勢。',10)
    label(fig,.065,.038,'本例不新增整理細分類、正式破底門檻或最早辨認日；不與 2884 不同觀察長度直接排名。',10)
    pdf.savefig(fig);fig.savefig(out/'page-3.png',dpi=140);plt.close(fig)

pdf_bytes=pdf_buffer.getvalue()
assert pdf_bytes.rstrip().endswith(b'%%EOF')
pdf_path=out/'output/pdf/m1-formation-evidence-comparison.pdf'
pdf_path.write_bytes(pdf_bytes)
assert pdf_path.read_bytes()==pdf_bytes
from pypdf import PdfReader
assert len(PdfReader(io.BytesIO(pdf_bytes)).pages)==3
assert sha(Path(args.source).read_bytes())==sha(raw)
assert sha(Path(args.comparison).read_bytes())==sha(comparison_raw)
previous_runs=json.loads((out/'verification.json').read_text()).get('research_script_runs',0) if (out/'verification.json').exists() else 0
verification={'schema':'m1-exploratory-formation-execution/1','research_script_runs':previous_runs+1,
 'source_sha_unchanged':True,'source_prefix_cutoff':cutoff,'source_prefix_records':len(bars),
 'window_scan':{'total':len(bars)-n+1,'excluded':len(excluded),'measured':len(scanned),'diagnostic_candidates':len(candidates)},
 'positive_and_control_n13_overlap_equal_12_of_12':True,'positive_and_control_n13_peak_coverage_equal_9_of_13':True,
 'all_suffix_lengths_3_to_13_reported':True,'control_selected_by_stated_sort':True,'all_plot_rows_within_each_shown_cutoff':True,
 'new_calculation':'READ_ONLY_RESEARCH_GEOMETRY_AND_CLOSE_PATH_FEATURES',
 'engine_MA_MACD_pivot_box_recalculations':0,'classifier_tests':'NOT_RUN_NOT_IMPLEMENTED',
 'new_PDF_pages':3,'PNG_previews':3,'PDF_render_visual_QA':'PENDING_EXTERNAL_INSPECTION',
 'ABC39_new_low_and_user_interval_coexistence':'PASS_SOURCE_VALUES_AND_EXISTING_LABEL_ONLY',
 'browser':'NOT_RUN','Android':'NOT_TESTED_NEW_BUILD','pages':pages,
 'source_limitations':s['source_gaps'],'primary_pressure_id':None,'historical_signal_eligible':False}
(out/'verification.json').write_text(json.dumps(verification,ensure_ascii=False,indent=2)+'\n')
print(json.dumps({'positive':pm,'control':cm,'ABC39':abc_metrics,'scan':verification['window_scan'],'pages':3},ensure_ascii=False))
