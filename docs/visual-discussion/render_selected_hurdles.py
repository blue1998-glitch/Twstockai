"""Render a manually reviewed case from the unchanged uploaded real OHLCV.
This is discussion evidence, not a product build or a recognition algorithm.
"""
import argparse
import hashlib
import json
from pathlib import Path
from decimal import Decimal
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.collections import LineCollection
from matplotlib.font_manager import FontProperties

p = argparse.ArgumentParser()
p.add_argument('--export', required=True, type=Path)
p.add_argument('--output', required=True, type=Path)
p.add_argument('--font', required=True, type=Path)
a = p.parse_args()
a.output.mkdir(parents=True, exist_ok=True)
raw = a.export.read_bytes()
assert hashlib.sha256(raw).hexdigest() == '1718fd0fd66f3abb6bbacfb73e802235bbd647976aeb903ea8b0ea757daedde3'
d = json.loads(raw)
analysis = d['new_history_analysis']
bars = analysis['bars']
assert len(bars) == 1213 and bars[-1]['date'] == '2026-10-16'
dates = [b['date'] for b in bars]
selections = [('G1', 1, '2023-11-28', '35.50'), ('G2', 2, '2023-05-02', '40.25'), ('G3', 3, '2021-10-18', '50.20')]
references = []
for name, order, day, level in selections:
    row = bars[dates.index(day)]
    assert row['high'] == level
    assert day < '2024-10-16'
    matches = [b for b in bars if b['high'] == level] if order == 3 else [row]
    assert all(b['date'] < '2024-10-16' for b in matches)
    references.append(dict(id=name, order=order, source_date=day if order < 3 else None,
        display_anchor_source_date=day, matching_source_dates=[b['date'] for b in matches], raw_high=level,
        date_assignment='USER_EXPLICIT_DATE' if order < 3 else 'USER_PRICE_ONLY_MULTIPLE_SOURCE_DATES_NOT_UNIQUELY_ASSIGNED',
        reference_type='USER_SELECTED_POINT_NOT_REGION_BOUNDARY',
        current_raw_close_relation='BELOW' if Decimal(bars[-1]['close']) < Decimal(level) else 'UNKNOWN',
        outside_current_24_calendar_month_window=True, source_bar=row if order < 3 else None, source_bars=matches,
        region_start=None, region_end=None, region_price_bounds=None,
        region_total_volume=None, volume_expansion_rule=None, automatic_selection_rule=None))
case = dict(schema_version='manual-left-hurdles-review/0.1', code='1101', price_mode='RAW_CANDIDATE',
    reviewed_at='2026-10-18T15:19:32+08:00', analysis_as_of='2026-10-16',
    user_quote='20231128高點35.5左側第一關，20230502高點40.25第二關。第三關高點50.2',
    source_id=analysis['source']['id'], frame_id=analysis['frame']['frame_id'], chart_base=analysis['frame']['chart_base'],
    export_sha256=hashlib.sha256(raw).hexdigest(), annotations_are='LATER_USER_MANUAL_REVIEW_NOT_ASOF_AUTOMATIC_SIGNALS',
    source_values_verification='THREE_POINT_HIGH_VALUES_MATCH_RETAINED_VERIFIED_EXPORT',
    references=references, original_review_references_preserved=True,
    action_qualification='NOT_EVALUATED', classification_quality='NOT_VALIDATED',
    comparison_basis='RAW_COMPANY_ACTIONS_NOT_FULLY_VERIFIED_NO_ADJUSTED_COMPARABILITY_CERTIFICATION',
    full_history_high='NOT_ESTABLISHED', remaining_ownership='UNKNOWN', generalization_to_other_stocks='NOT_AUTHORIZED_BY_THIS_CASE',
    product_integration='NOT_IMPLEMENTED', new_android_acceptance='NO_NEW_DEVICE_TEST_THIS_TURN')
(a.output / '1101-selected-hurdles-1519.json').write_text(json.dumps(case, ensure_ascii=False, indent=2) + '\n')

font = FontProperties(fname=str(a.font))
plt.rcParams.update({'font.family': font.get_name(), 'font.size': 12, 'axes.unicode_minus': False})
from matplotlib import font_manager
font_manager.fontManager.addfont(str(a.font))
fig, ax = plt.subplots(figsize=(13.5, 7.4), dpi=150)
fig.patch.set_facecolor('#101923')
ax.set_facecolor('#101923')
for spine in ax.spines.values(): spine.set_color('#465464')
ax.tick_params(colors='#bac7d6')
ax.grid(axis='y', color='#304253', alpha=.7)
wicks, bodies, colors = [], [], []
for i, b in enumerate(bars):
    op, hi, lo, cl = [float(b[k]) for k in ('open', 'high', 'low', 'close')]
    wicks.append([(i, lo), (i, hi)])
    bodies.append([(i, op), (i, cl if cl != op else cl + .025)])
    colors.append('#ef7775' if cl >= op else '#52c3ad')
ax.add_collection(LineCollection(wicks, colors=colors, linewidths=.55))
ax.add_collection(LineCollection(bodies, colors=colors, linewidths=1.1))
start24 = next(i for i, b in enumerate(bars) if b['date'] >= '2024-10-16')
assert len(bars) - start24 == 486
ax.axvspan(start24, len(bars)-1, facecolor='#82a9e5', alpha=.09)
ax.axvline(start24, color='#7598c5', linewidth=.8, linestyle=':')
ax.text((start24 + len(bars)-1)/2, 52.0, '手機目前的24月視窗', ha='center', color='#a7c6f4', fontsize=12)
styles = [('#ffcf66', '第一關'), ('#e7a473', '第二關'), ('#c2adff', '第三關')]
for ref, (color, label) in zip(references, styles):
    i = dates.index(ref['display_anchor_source_date']); level = float(ref['raw_high'])
    ax.hlines(level, i, len(bars)+30, color=color, linestyles=(0, (5, 4)), linewidth=1.25)
    ax.scatter([dates.index(day) for day in ref['matching_source_dates']], [level]*len(ref['matching_source_dates']), s=42, color=color, zorder=6)
    caption = ref['source_date'] if ref['id'] != 'G3' else '50.20 同價高點×5'
    ax.annotate(caption, xy=(i, level), xytext=(12, 12 if ref['id'] in ('G1','G3') else -27),
        textcoords='offset points', color=color, fontsize=11,
        arrowprops=dict(arrowstyle='-', color=color, lw=.7))
    ax.text(len(bars)+42, level, f'{label}  {ref["raw_high"]}', color=color, va='center', fontsize=13, fontweight='bold')
last = float(bars[-1]['close'])
ax.scatter([len(bars)-1], [last], color='#78dacf', s=30, zorder=7)
ax.plot([len(bars)-1,len(bars)+30],[last,last], color='#78dacf',linewidth=.8)
ax.text(len(bars)+42, last, '10/16收盤 27.30', va='center', color='#78dacf', fontsize=12)
ticks = [0] + [i for i,b in enumerate(bars) if b['date'][:4] != bars[i-1]['date'][:4] and i > 100] + [len(bars)-1]
ax.set_xticks(ticks)
ax.set_xticklabels([dates[i][:7] if i not in (0,len(bars)-1) else dates[i] for i in ticks], fontsize=10)
ax.set_xlim(-18, len(bars)+210)
ax.set_ylim(17.5, 53.7)
ax.set_yticks([20,25,30,35,40,45,50])
ax.set_ylabel('原始價格 Raw', color='#bac7d6')
fig.text(.07, .945, '1101 台泥｜你指定的三個左側關卡', color='#f0f4fa', fontsize=21, fontweight='bold')
fig.text(.07, .901, '真實日K 2021-10-18～2026-10-16 · 三個來源日期都在目前24月畫面之外', color='#b8c6d6', fontsize=12)
fig.text(.07, .075, '10/18人工選點定位圖；尚未接入手機成品。不是當時的自動訊號，點價不代表整區邊界。', color='#b8c6d6', fontsize=11)
fig.text(.07, .038, '公司行動尚未完整核實：這是Raw來源定位，不認證共同還原基底壓力或完整歷史最高價。', color='#b8c6d6', fontsize=11)
fig.subplots_adjust(left=.075,right=.975,bottom=.16,top=.855)
fig.savefig(a.output / '1101-selected-hurdles-1519.png', facecolor=fig.get_facecolor())
plt.close(fig)
print(json.dumps({'point_checks_passed':3, 'all_three_outside_24_month_window':True, 'true_daily_bars_rendered':len(bars), 'product_changed':False, 'files':sorted(p.name for p in a.output.iterdir())},ensure_ascii=False))
