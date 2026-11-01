"""Git-external private preview, reusing the M-G3 renderer and indicators."""
import argparse
from copy import deepcopy
import json
from pathlib import Path

from graph_core.market_daily import outside,encode,digest
from graph_core.core import fingerprint
from rotation_research.store import Journal
from graph_core_chart.build import render,display_ids
from graph_core_chart.evidence import layers
from product_candidate.build import publish_immutable
from product_candidate.macd import macd,PARAMETERS
from moving_averages import curves


def source_segment_ma(bars,resets):
    """Reuse original SMA separately within known comparable source segments."""
    boundaries=sorted(set([0,len(bars)]+list(resets)));out={}
    for a,b in zip(boundaries,boundaries[1:]):
        for period,values in curves(bars[a:b]).items():out.setdefault(period,[]).extend(values)
    return out


def build(root,run_id):
    root=outside(root);batch=Journal(root/'runs').read(run_id)['value'];series=[]
    for stock in batch['stocks']:
        if not stock.get('result_key'):continue
        saved=Journal(root/'results').read(stock['result_key'])['value'];r=saved['result'];payload=saved['input'];bars=payload['bars'];as_of=batch['as_of']
        resets=[i for i,b in enumerate(bars) if b['date'] in r['data_gaps']['basis_resets']]
        series.append(dict(code=stock['code'],exchange=stock['market'],source=dict(id=r['context']['source_id'],name=stock['name'],role='OFFICIAL_BULK_NATIVE_SHARES_NOT_OLD_MONTHLY_DATA',historical_available_at='UNKNOWN'),
            price_basis_id=r['context']['price_basis_id'],bars=deepcopy(bars),macd=macd([b['close'] for b in bars],resets=resets),moving_averages=source_segment_ma(bars,resets),
            results=[r],presentations={as_of:display_ids(r)},manual_audits={},numeric_frame_ids={as_of:fingerprint(dict(kind='FM1_RESEARCH_INPUT_FRAME',result_id=r['result_id'],prefix=r['source_prefix_fingerprint']))},
            source_gaps=dict(calendar_status='OBSERVED_BATCH_DATES_ONLY_NOT_COMPLETE_CALENDAR',actions_coverage='UNKNOWN',historical_publication_timing='UNKNOWN'),
            macd_parameters=PARAMETERS,input_bindings={as_of:dict(source_id=r['context']['source_id'],price_basis_id=r['context']['price_basis_id'],basis_break_dates=r['data_gaps']['basis_resets'],historical_available_at='UNKNOWN',source_role='NEW_OFFICIAL_BULK_DAILY_NOT_OLD_MONTHLY_NOT_FINMIND')},
            box_evidence={as_of:layers(r,bars)}))
    if not series:raise ValueError('No stored core output to preview; no fabricated chart')
    bundle=dict(schema_version='graph-recognition-chart-bundle/0.2',view_version='graph-recognition-view/0.2',series=series,
        sampling=dict(analysis='CURRENT_SAVED_BATCH_ONLY',prices='ONLY_CAPTURED_OFFICIAL_ROWS_NOT_BACKFILLED'),physical_android='NOT_TESTED_NEW_BUILD',market_run_id=run_id)
    bundle['artifact_id']=fingerprint(bundle)
    shell=render(bundle)
    # Existing source-specific M-G3 note applies to its older four-stock parent,
    # not this new native-share bulk feed. All actual source records remain exact.
    shell=shell.replace('8069原來源顯示精度／單位限制保留，未認證FinMind精確股數。','本頁官方整批API明示原生成交股數；舊TPEx月表仟股／張×1000屬不同來源，不能混用認證。')
    shell=shell.replace('>約五年<','>全部累積日K<').replace('已算分析日為每120筆樣本與最近5交易日；K線與查詢保留全部真實來源，不補休市K。其他日期須離線CLI加算，不在UI補算。','本頁只有本次批次已保存分析日；價格僅實際累積官方日K，不宣稱五年或完整交易日曆。原四股歷史主圖獨立保留，不拼接缺失日期。')
    state=dict(summary=batch['summary'],stocks=batch['stocks'])
    data=json.dumps(state,ensure_ascii=False,separators=(',',':')).replace('<','\\u003c').replace('&','\\u0026')
    js=(Path(__file__).parent/'fm1_20261101/search.js').read_text()
    addon='<script id="market-state" type="application/json">'+data+'</script><script>'+js+'</script>'
    html=shell.replace('</body>',addon+'</body>')
    out=root/'preview'/run_id/'market-v03.html';publish_immutable(out,html.encode())
    return dict(path=str(out),bytes=len(html.encode()),sha256=digest(html.encode()),stocks=len(batch['stocks']),charts=len(series),transport='PRIVATE_FILE_OR_LOOPBACK_ONLY_NOT_DEPLOYED',android='NOT_TESTED')


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--root',required=True);p.add_argument('--run',required=True);a=p.parse_args();print(json.dumps(build(a.root,a.run),ensure_ascii=False,indent=2))
