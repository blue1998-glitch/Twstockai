"""Offline plots/report producer. Plot dependency: matplotlib; core has none."""
from pathlib import Path
import base64, hashlib, json
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.font_manager import FontProperties, fontManager
from matplotlib.patches import Rectangle
from .core import dec

HERE=Path(__file__).resolve().parent
FONT=Path('/workspace/scratch/046c6c9354ed/cutoff-volume-study/NotoSansCJKtc-Regular.otf')
LABEL={'hold':'續抱 A','full':'全部換 B','staged25':'25%事件分批','staged50':'50%事件分批','cash':'賣 A 持現金','delay5':'延後5筆全換'}
COLORS={'hold':'#365b91','full':'#c03d34','staged25':'#8754a2','staged50':'#b37b16','cash':'#62716d','delay5':'#22836f'}

def setup_font():
    import os
    font=Path(os.environ.get('ROTATION_CJK_FONT',str(FONT)))
    if not font.exists():raise ValueError('Set ROTATION_CJK_FONT to a CJK font; never silently render missing glyphs')
    fontManager.addfont(str(font));plt.rcParams['font.family']=FontProperties(fname=font).get_name()
    plt.rcParams.update({'font.size':11,'axes.unicode_minus':False,'svg.fonttype':'path',
                         'axes.spines.top':False,'axes.spines.right':False})

def save(fig,out,stem):
    fig.savefig(out/(stem+'.svg'),bbox_inches='tight',metadata={'Date':None})
    fig.savefig(out/(stem+'.png'),dpi=150,bbox_inches='tight');plt.close(fig)

def price_chart(data,cutoff,end,out,mode):
    start='2025-07-01' if cutoff=='2026-01-02' else '2026-02-02'
    fig,axes=plt.subplots(4,1,figsize=(10,12),sharex=True,gridspec_kw={'height_ratios':[3,1,3,1]})
    for index,code in enumerate(('1101','2884')):
        asset=data['assets'][code];bars=[b for b in asset['bars'] if start<=b['date']<=end]
        ax,vol=axes[index*2:index*2+2];dates=[b['date'] for b in bars];ci=dates.index(cutoff)
        original=[b for b in asset['bars'] if b['date']<cutoff][-20:]
        key=max(float(b['high']) for b in original);floor=min(float(b['low']) for b in original)
        for x,b in enumerate(bars):
            if b.get('missing'):
                ax.axvline(x,color='#999',ls=':',alpha=.5);continue
            o,h,l,c=[float(b[k]) for k in ('open','high','low','close')];color='#c03d34' if c>=o else '#158465'
            ax.vlines(x,l,h,color=color,lw=.7)
            ax.add_patch(Rectangle((x-.3,min(o,c)),.6,max(abs(c-o),.015),facecolor=color,edgecolor=color,lw=.5))
            vol.bar(x,int(b['volume'])/1e6,width=.7,color=color)
        ax.axhline(key,color='#7a509d',ls='--',lw=.8,label=f'截止前20筆原高試驗參照 {key:.2f}')
        ax.axhline(floor,color='#888',ls=':',lw=.8,label=f'同窗原低試驗參照 {floor:.2f}')
        if mode=='after':
            ax.axvspan(ci+.5,len(bars)-.5,color='#dce9f5',alpha=.6)
            vol.axvspan(ci+.5,len(bars)-.5,color='#dce9f5',alpha=.6)
            # Factual crossing/return relative to FROZEN experimental reference only.
            prev=float(bars[ci]['close'])
            for x in range(ci+1,len(bars)):
                b=bars[x];cur=float(b['close'])
                if cur>key>=prev:ax.scatter(x,cur,marker='^',s=35,color='#6433a1',zorder=4)
                if cur<=key<prev:ax.scatter(x,cur,marker='v',s=35,color='#343b45',zorder=4)
                prev=cur
            ax.axvline(ci+1,color='#cf7b20',lw=1,label='次筆開盤：全換候選成交日')
        ax.axvline(ci,color='#1c2637',lw=1)
        ax.set_title(f'{code}｜RAW 真實保存日K｜截止 {cutoff}',loc='left',fontsize=13,pad=38)
        ax.set_ylabel('元');vol.set_ylabel('百萬股');ax.legend(loc='lower left',bbox_to_anchor=(0,1.01),ncol=2,fontsize=8,frameon=False)
        ax.grid(axis='y',alpha=.15);vol.grid(axis='y',alpha=.1)
        ticks=sorted(set([0,ci,len(bars)-1]))
        for tick in range(0,len(bars),max(1,len(bars)//5)):
            if min(abs(tick-t) for t in ticks)>=max(10,len(bars)//10):ticks.append(tick)
        ticks.sort()
        vol.set_xticks(ticks,[dates[t][2:] for t in ticks],rotation=25,ha='right')
    fig.suptitle('決策當時：僅截止前資訊' if mode=='before' else '事後40筆：藍底是未來結果，當時不可見',fontsize=15,y=.99)
    fig.text(.08,.01,'紫線／灰線不是已核正式關鍵價或箱界；▲越試驗原高、▼返回線下，均非交易資格。\n保留所有量柱與無報價缺口；不判成功換手。價格與量單位分開。',fontsize=9)
    fig.tight_layout(rect=(0,.05,1,.965));stem=f'prices-{cutoff}-{mode}';save(fig,out,stem)
    return {'stem':stem,'first_date':start,'last_date':end,'cutoff':cutoff,
            'future_visible':mode=='after','bar_counts':{c:sum(start<=b['date']<=end for b in a['bars']) for c,a in data['assets'].items()}}

def equity_chart(rs,out,stem):
    fig,ax=plt.subplots(figsize=(10,5.8))
    for r in rs:
        initial=float(r['metrics']['initial_equity']);values=[100]+[float(n['net_liquidation_equity'])/initial*100 for n in r['nav']]
        ax.plot(range(len(values)),values,label=LABEL[r['plan']],color=COLORS[r['plan']],lw=1.9)
    ax.axhline(100,color='#777',ls=':',lw=.7);ax.set_xlabel('決策後保存交易日筆數');ax.set_ylabel('淨清算估值（起始資本＝100）')
    ax.set_title(f"A {rs[0]['incumbent']} → B {rs[0]['candidate']}｜{rs[0]['cutoff']} 起40筆",loc='left')
    ax.legend(ncol=2,fontsize=10);ax.grid(alpha=.16)
    fig.text(.08,.01,'扣模擬費稅、滑價及終點退出費；未完整計股利／公司行動，不是實際總淨報酬。',fontsize=9)
    fig.tight_layout(rect=(0,.05,1,1));save(fig,out,stem)

def main():
    setup_font();out=HERE/'generated';plots=out/'plots';plots.mkdir(exist_ok=True)
    data=json.loads((out/'input.json').read_text());results=json.loads((out/'chart-examples.json').read_text())
    all_results=json.loads((out/'results.json').read_text());loops=json.loads((out/'loop-results.json').read_text())
    cases={};figures=[]
    for cutoff in ('2026-01-02','2026-08-03'):
        for pair in [('1101','2884'),('2884','1101')]:
            rs=[r for r in results if r['cutoff']==cutoff and (r['incumbent'],r['candidate'])==pair]
            end=rs[0]['nav'][-1]['date'];key=f'{cutoff}-{pair[0]}'
            stem='equity-'+key;equity_chart(rs,plots,stem)
            if pair[0]=='1101':
                figures.append(price_chart(data,cutoff,cutoff,plots,'before'))
                figures.append(price_chart(data,cutoff,end,plots,'after'))
            cases[key]={'cutoff':cutoff,'A':pair[0],'B':pair[1],'end':end,'results':rs,
                        'initial_equity':rs[0]['metrics']['initial_equity'],'equity_stem':stem}
    fig,ax=plt.subplots(figsize=(10,5.8))
    loopnames={'hold':'續抱1101','full_review10':'10筆檢討全換實驗','half_review10':'10筆檢討半配實驗','cash_review10':'含現金候選實驗'}
    for loop in loops:
        vals=[100]+[float(p['net_liquidation_equity'])/float(loop['initial_equity'])*100 for p in loop['curve']]
        ax.plot(range(len(vals)),vals,label=loopnames[loop['policy']])
    ax.set_title('同一帳戶多次配置｜2026-05-04～10-16｜無外部注資',loc='left');ax.set_ylabel('淨清算估值（起始＝100）');ax.set_xlabel('保存交易日筆數');ax.legend(fontsize=9);ax.grid(alpha=.15)
    fig.text(.08,.01,'5筆漲幅／10筆檢討是帳務實驗，不是使用者價量策略；公司行動未完整計入。',fontsize=9)
    fig.tight_layout(rect=(0,.05,1,1));save(fig,plots,'capital-loop')
    figures.append({'stem':'capital-loop','status':'CONDITIONAL_ACCOUNTING_EXPERIMENT'})
    summary={}
    for period in ('development','temporal_holdout'):
        groups={}
        for r in all_results:
            if r['period']!=period:continue
            groups.setdefault((r['cutoff'],r['incumbent'],r['horizon']),{})[r['plan']]=r
        summary[period]={'comparisons':len(groups)}
        for stage in ('staged25','staged50'):
            summary[period][stage]={'end_value_above_full':sum(dec(g[stage]['metrics']['end_net_liquidation_equity'])>dec(g['full']['metrics']['end_net_liquidation_equity']) for g in groups.values()),
                                     'drawdown_less_than_full':sum(dec(g[stage]['metrics']['max_drawdown_close_net'])>dec(g['full']['metrics']['max_drawdown_close_net']) for g in groups.values())}
    dump=lambda p,x:p.write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n')
    dump(out/'summary.json',summary);dump(out/'figure-manifest.json',figures)
    sensitivity=json.loads((out/'sensitivity.json').read_text())
    base20=[{'cutoff':r['cutoff'],'A':r['incumbent'],'B':r['candidate'],'plan':r['plan'],
             'slippage_bps':'10','settlement_lag':0,'metrics':r['metrics']}
            for r in all_results if r['horizon']==20]
    report={'schema':'rotation-report/0.1','cases':cases,'summary':summary,'loops':loops,'figures':figures,
            'sensitivity20':base20+sensitivity}
    # Exact numeric results embedded; browser only selects/renders, never calculates strategy.
    images={p.stem:'data:image/svg+xml;base64,'+base64.b64encode(p.read_bytes()).decode() for p in plots.glob('*.svg')}
    template=(HERE/'report-template.html').read_text()
    (out/'report.html').write_text(template.replace('__REPORT_DATA__',json.dumps(report,ensure_ascii=False)).replace('__REPORT_IMAGES__',json.dumps(images)))
    dump(out/'report-data.json',report)
    print(json.dumps({'cases':len(cases),'svg':len(images),'summary':summary}))
if __name__=='__main__':main()
