"""Draw retained real OHLCV for discussion; does not select a resistance region."""
import argparse
import hashlib
import json
from pathlib import Path

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib import font_manager
from matplotlib.patches import Rectangle


def build(data_path, output_path, font_path):
    data = json.loads(Path(data_path).read_text())
    font_manager.fontManager.addfont(font_path)
    plt.rcParams['font.family'] = font_manager.FontProperties(fname=font_path).get_name()
    plt.rcParams['axes.unicode_minus'] = False
    plt.rcParams['font.size'] = 13
    bg, fg, grid = '#101923', '#e6edf4', '#304153'
    fig = plt.figure(figsize=(12, 12), dpi=140, facecolor=bg)
    gs = fig.add_gridspec(3, 1, height_ratios=[1, 1.55, .75], hspace=.5,
                          left=.08, right=.96, top=.88, bottom=.19)
    axes = [fig.add_subplot(gs[i]) for i in range(3)]
    for ax in axes:
        ax.set_facecolor(bg)
        ax.tick_params(colors=fg, labelsize=11)
        for spine in ax.spines.values():
            spine.set_color(grid)
        ax.grid(axis='y', color=grid, alpha=.65)
        ax.set_axisbelow(True)

    def candles(ax, bars):
        for i, bar in enumerate(bars):
            o, h, l, c = (float(bar[k]) for k in ['open', 'high', 'low', 'close'])
            color = '#ff7179' if c > o else '#51cbb5' if c < o else '#d6dde6'
            ax.vlines(i, l, h, color=color, lw=.75)
            if c == o:
                ax.hlines(c, i-.34, i+.34, color=color, lw=1)
            else:
                ax.add_patch(Rectangle((i-.34, min(o, c)), .68, abs(c-o),
                                       facecolor=color, edgecolor=color, lw=.3))
        ax.set_xlim(-2, len(bars)+2)

    overview, zoom = data['overview_bars'], data['zoom_bars']
    candles(axes[0], overview)
    candles(axes[1], zoom)
    for ax, bars, interval in [(axes[0], overview, 3), (axes[1], zoom, 1)]:
        tick_positions, tick_labels = [], []
        last_month = None
        for i, bar in enumerate(bars):
            month = bar['date'][:7]
            if month != last_month and (int(month[5:7])-1) % interval == 0:
                tick_positions.append(i)
                tick_labels.append(month)
            last_month = month
        ax.set_xticks(tick_positions, tick_labels, rotation=0)
        ax.axhline(35.5, color='#ffd36b', ls=(0, (5, 4)), lw=1.2)
        g = next(i for i, bar in enumerate(bars) if bar['date'] == '2023-11-28')
        ax.scatter(g, 35.5, color='#ffd36b', s=38, zorder=5)
        ax.set_ylabel('Raw 價格', color=fg)
    axes[0].set_title('先看背景：同一價位附近，後來還有其他交易', loc='left', color=fg, fontsize=14)
    axes[0].annotate('G1 35.50', (next(i for i,b in enumerate(overview) if b['date']=='2023-11-28'),35.5),
                     xytext=(10,14), textcoords='offset points', color='#ffd36b', fontsize=12)
    axes[1].set_title('放大 G1 附近：尚未圈選任何壓力區', loc='left', color=fg, fontsize=14)
    for label, date, key, offset in [('A', '2023-10-24', 'low', (0,-28)),
                                    ('G1', '2023-11-28', 'high', (0,34)),
                                    ('C', '2024-01-19', 'low', (0,-28))]:
        i = next(i for i,b in enumerate(zoom) if b['date']==date)
        price = float(zoom[i][key])
        color = '#ffd36b' if label=='G1' else '#b1cbef'
        axes[1].annotate(f'{label}  {date[5:]}\n{price:.2f}', (i,price), xytext=offset,
                         textcoords='offset points', ha='center', color=color, fontsize=11,
                         arrowprops={'arrowstyle':'-', 'color':color, 'lw':.8})
    axes[1].set_ylim(29.8, 38.5)
    for i, bar in enumerate(zoom):
        color = '#ff7179' if float(bar['close']) > float(bar['open']) else '#51cbb5'
        axes[2].bar(i, int(bar['volume_shares_scaled'])/1_000_000, width=.7, color=color)
    axes[2].set_xlim(axes[1].get_xlim())
    axes[2].set_xticks(axes[1].get_xticks(), [t.get_text() for t in axes[1].get_xticklabels()])
    axes[2].set_ylabel('成交量\n百萬股', color=fg)
    axes[2].set_title('逐日真實成交股數；目前沒有選區或計算整區量', loc='left', color=fg, fontsize=13)
    fig.text(.08,.955,'1101 台泥｜G1 的壓力量，應看哪一段？',color=fg,fontsize=22,weight='bold')
    fig.text(.08,.918,'分析截至 2026-10-16；沿用已核對的真實日線，沒有新增行情',color='#b4c4d5',fontsize=12)
    fig.text(.08,.065,'A／C 只是指圖用的位置，不是已認可的轉折或區間邊界。\n'
             '放大範圍只是閱讀視窗；你可以選更小、更大，或分成多段。\n'
             'Raw 公司行動未完整核實；歷史成交量不等於目前仍套牢的股數。',
             color='#b4c4d5',fontsize=11,linespacing=1.7)
    fig.savefig(output_path, facecolor=bg)
    plt.close(fig)


if __name__ == '__main__':
    p = argparse.ArgumentParser()
    p.add_argument('--data', required=True)
    p.add_argument('--output', required=True)
    p.add_argument('--font', required=True)
    args = p.parse_args()
    build(args.data, args.output, args.font)
