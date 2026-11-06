"""Presentation correction only: saved daily OHLCV, no structure inference."""
from pathlib import Path
import os, json, hashlib
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle
from matplotlib.font_manager import FontProperties
from matplotlib.ticker import FormatStrFormatter
from matplotlib.backends.backend_pdf import PdfPages

ROOT = Path(__file__).resolve().parent
SOURCE = Path(os.environ.get('STOCK_STUDY_2884', '/workspace/scratch/54685b8dac93/independent-level-review/source-data-2884.json'))
FONT = os.environ.get('STOCK_STUDY_FONT', '/workspace/scratch/54685b8dac93/version-continuity-review/research-font.otf')
EXPECTED = 'ab87a51b5b8afd076603f290b10f415bd60d31ae47c5ab2f6d9d609ad4014901'
assert hashlib.sha256(SOURCE.read_bytes()).hexdigest() == EXPECTED
s = json.loads(SOURCE.read_text())
bars = s['bars']
assert len(bars) == len({b['date'] for b in bars}) == 1213
assert bars == sorted(bars, key=lambda b: b['date'])
font = FontProperties(fname=FONT)
cutoff = '2026-04-28'
specs = [
    ('b-two-year-context', '2024-10-17', '2026-10-16', 'B｜約兩年日K：先看這段在整體走勢的位置', 2),
    ('b-five-year-context', bars[0]['date'], bars[-1]['date'], 'B｜五年保存日K總覽：保留更早的背景', 6),
    ('b-one-year-detail', '2025-10-17', '2026-10-16', 'B｜約一年日K：B前後的活動一起看', 1),
    ('b-asof-context', '2024-10-17', cutoff, 'B｜截至4/28的約一年半日K：不含後續行情', 2),
]
manifest = []
(ROOT/'output/pdf').mkdir(parents=True, exist_ok=True)
pdf = PdfPages(ROOT/'output/pdf/b-wide-context.pdf')
for name, start, end, title, tick_months in specs:
    bs = [b for b in bars if start <= b['date'] <= end]
    dates = [b['date'] for b in bs]
    ci, a, z = [dates.index(d) for d in [cutoff, '2026-04-16', '2026-04-27']]
    fig = plt.figure(figsize=(20, 9), facecolor='white')
    ax = fig.add_axes([.055, .325, .92, .51])
    va = fig.add_axes([.055, .155, .92, .135], sharex=ax)
    fig.text(.055, .94, title, fontproperties=font, fontsize=22, color='#203548')
    fig.text(.055, .895, f"2884｜{dates[0]} ～ {dates[-1]}｜{len(bs)}筆保存日K；紅漲綠跌、日K與成交量對齊", fontproperties=font, fontsize=12)
    fig.text(.055, .065, '紫色只定位原B來源4/16～4/27，不是整體起末或價界；本圖沒有預選合併／拆分。', fontproperties=font, fontsize=12)
    fig.text(.055, .028, '保存Raw價格；公司行動、完整日曆及歷史公開可得性仍待核。已列資料缺日以橙色短線標示，不自行補值。', fontproperties=font, fontsize=11, color='#5b6571')
    for i, b in enumerate(bs):
        o, h, l, c = [float(b[k]) for k in ['open', 'high', 'low', 'close']]
        color = '#c34848' if c >= o else '#16856c'
        ax.vlines(i, l, h, color=color, lw=.7 if len(bs)>700 else .9)
        ax.add_patch(Rectangle((i-.31, min(o,c)), .62, max(abs(c-o), .015), facecolor=color, edgecolor=color, lw=.3))
        va.bar(i, int(b['volume_shares_scaled'])/1e6, color=color, width=.65)
    for axis in [ax, va]:
        axis.axvspan(a-.5, z+.5, color='#8b72b6', alpha=.18, zorder=-3)
        axis.axvline(ci+.5, color='#636f80', ls='--', lw=1.1)
        if ci < len(bs)-1:
            axis.axvspan(ci+.5, len(bs)-.5, color='#e3e9ef', alpha=.5, zorder=-5)
        axis.grid(axis='y', color='#d8dee6', alpha=.65, lw=.6)
        axis.set_axisbelow(True)
        axis.set_xlim(-1, len(bs))
        for spine in ['top','right']:
            axis.spines[spine].set_visible(False)
    ax.set_ylabel('Raw價格', fontproperties=font, fontsize=11)
    ax.yaxis.set_major_formatter(FormatStrFormatter('%.2f'))
    va.set_ylabel('量／百萬股', fontproperties=font, fontsize=11)
    ax.tick_params(axis='x', labelbottom=False)
    ticks = [0]
    for i, d in enumerate(dates):
        if i and d[:7] != dates[i-1][:7] and (int(d[5:7])-1)%tick_months == 0:
            ticks.append(i)
    if len(bs)-1-ticks[-1] > max(15, len(bs)/24):
        ticks.append(len(bs)-1)
    ticks = [t for t in ticks if t == 0 or t == len(bs)-1 or (t > len(bs)*.055 and t < len(bs)*.95)]
    va.set_xticks(ticks, [dates[i][:7] for i in ticks], fontsize=9)
    for g in s['source_gaps']['known_calendar_missing_dates']:
        if start <= g <= end:
            after = next((i for i,d in enumerate(dates) if d > g), None)
            if after is not None:
                ax.axvline(after-.5, ymin=0, ymax=.035, color='#c48b24', lw=2)
                va.axvline(after-.5, ymin=0, ymax=.15, color='#c48b24', lw=2)
    mid = (a+z)/2
    ax.annotate('原B來源位置\n4/16～4/27', xy=(mid, float(bs[a]['high'])), xytext=(mid, .91), textcoords=('data','axes fraction'), ha='center', va='top', fontproperties=font, fontsize=11, color='#70528f', arrowprops={'arrowstyle':'-','color':'#70528f'})
    if ci < len(bs)-1:
        ax.text(.70, 1.01, '4/28虛線右側為事後背景，不回填當時判斷', transform=ax.transAxes, ha='left', fontproperties=font, fontsize=10, color='#536679')
    else:
        ax.text(.70, 1.01, '右端止於2026/4/28；不含後續行情', transform=ax.transAxes, ha='left', fontproperties=font, fontsize=10, color='#536679')
    path = ROOT/(name+'.png')
    fig.savefig(path, dpi=120)
    pdf.savefig(fig)
    plt.close(fig)
    manifest.append({'image':path.name, 'start':dates[0], 'end':dates[-1], 'saved_bars':len(bs), 'b_source_indices':[a,z], 'cutoff':cutoff, 'cutoff_index':ci, 'later_bars':len(bs)-ci-1, 'known_missing_dates_in_window':[g for g in s['source_gaps']['known_calendar_missing_dates'] if start<=g<=end], 'sha256':hashlib.sha256(path.read_bytes()).hexdigest()})
pdf.close()
assert hashlib.sha256(SOURCE.read_bytes()).hexdigest() == EXPECTED
(ROOT/'figure-manifest.json').write_text(json.dumps({'source_sha256':EXPECTED, 'figures':manifest}, ensure_ascii=False, indent=2)+'\n')
print(json.dumps(manifest, ensure_ascii=False, indent=2))
