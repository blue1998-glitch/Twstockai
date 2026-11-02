"""Git-external private preview, reusing the M-G3 renderer and indicators."""
import argparse
from copy import deepcopy
import json
from pathlib import Path

from graph_core.market_daily import outside,encode,digest
from graph_core.core import fingerprint
from rotation_research.store import Journal
from rotation_research import artifact_codec as codec
from graph_core_chart.build import render,display_ids
from technical_chart.build import pack
from graph_core_chart.evidence import layers
from product_candidate.build import publish_immutable
from product_candidate.macd import macd,PARAMETERS
from moving_averages import curves


def source_segment_ma(bars,resets):
    """Reuse original SMA separately within known comparable source segments."""
    reset_set=set(resets);out={k:[] for k in curves([])};segment=[]
    def flush():
        if segment:
            for period,values in curves(segment).items():out[period].extend(values)
            segment.clear()
    for i,bar in enumerate(bars):
        if i in reset_set or bar['close'] is None:flush()
        if bar['close'] is None:
            for values in out.values():values.append(None)
        else:segment.append(bar)
    flush()
    return out


def build(root,run_id):
    root=outside(root);batch=Journal(root/'runs').read(run_id)['value'];series=[]
    incremental=batch['version'].startswith('official-market-increment/')
    finmind=batch['version'].startswith('finmind-market-history/')
    lazy=finmind or incremental
    compact=batch.get('storage_mode')=='compact'
    series_files={};preview_dir=root/'preview'/run_id
    base_series={};base_page=None
    if compact and batch.get('parent_run'):
        import re
        for name in ('market-du1-v01.html','market-fm3-v02.html','market-v04.html'):
            candidate=root/'preview'/batch['parent_run']/name
            if codec.exists(candidate):
                raw=codec.read_bytes(candidate);m=re.search(rb'<script id="market-state" type="application/json">(.*?)</script>',raw,re.S)
                if not m:raise ValueError('Parent preview index missing')
                old_state=json.loads(m[1]);base_page=candidate
                base_series={s['identity']:candidate.parent/s['preview_series']['path'] for s in old_state['stocks'] if s.get('preview_series')}
                break
    for stock in batch['stocks']:
        if not stock.get('result_key'):continue
        saved=Journal(root/'results').read(stock['result_key'])['value'];r=saved['result'];payload=saved['input'];bars=payload['bars'];as_of=batch['as_of']
        resets=[i for i,b in enumerate(bars) if b['date'] in r['data_gaps']['basis_resets']]
        indicators=saved.get('indicators')
        series.append(dict(code=stock['code'],exchange=stock['market'],source=dict(id=r['context']['source_id'],name=stock['name'],role='OFFICIAL_BULK_NATIVE_SHARES_NOT_OLD_MONTHLY_DATA',historical_available_at='UNKNOWN'),
            price_basis_id=r['context']['price_basis_id'],bars=deepcopy(bars),macd=deepcopy(indicators['macd']) if indicators else macd([b['close'] for b in bars],resets=resets),moving_averages=deepcopy(indicators['moving_averages']) if indicators else source_segment_ma(bars,resets),
            results=[r],presentations={as_of:display_ids(r)},manual_audits={},numeric_frame_ids={as_of:fingerprint(dict(kind='FM1_RESEARCH_INPUT_FRAME',result_id=r['result_id'],prefix=r['source_prefix_fingerprint']))},
            source_gaps=dict(calendar_status='OBSERVED_BATCH_DATES_ONLY_NOT_COMPLETE_CALENDAR',actions_coverage='UNKNOWN',historical_publication_timing='UNKNOWN'),
            macd_parameters=PARAMETERS,input_bindings={as_of:dict(source_id=r['context']['source_id'],price_basis_id=r['context']['price_basis_id'],basis_break_dates=r['data_gaps']['basis_resets'],historical_available_at='UNKNOWN',source_role='NEW_OFFICIAL_BULK_DAILY_NOT_OLD_MONTHLY_NOT_FINMIND')},
            box_evidence={as_of:layers(r,bars)}))
        if stock.get('history_source_provenance'):
            series[-1]['source'].update(role=stock['history_source_provenance']['role'],volume_provenance=deepcopy(stock['history_source_provenance']))
            series[-1]['source_gaps']=deepcopy(stock['history_source_provenance'].get('retained_source_gaps',
                dict(calendar_status='UNKNOWN_OLD_RECORD_MISSING_GAP_BINDING',actions_coverage='UNKNOWN',historical_publication_timing='UNKNOWN')))
            series[-1]['source']['indicator_provenance']={k:v for k,v in (indicators or {}).items() if k not in ('macd','moving_averages')}
            series[-1]['input_bindings'][as_of].update(source_role=stock['history_source_provenance']['role'],
                core_input_fingerprint=fingerprint(payload),retained_source_ledger_sha256=stock['history_source_provenance']['source_ledger_sha256'],
                corporate_action_type='UNKNOWN',cross_basis_comparability='NOT_CERTIFIED')
        if incremental:
            series[-1]['source'].update(role='RETAINED_HISTORY_AND_OFFICIAL_DAILY_EXPLICIT_SEGMENTS',
                increment_source_binding=deepcopy(saved['increment_source_binding']))
            series[-1]['source_gaps'].update(actions_coverage='UNKNOWN_NEW_DATE_RESET',cross_feed_comparability='NOT_CERTIFIED')
            series[-1]['input_bindings'][as_of].update(source_role='SEGMENTED_NOT_CERTIFIED_CONTINUOUS',
                increment_source_binding=deepcopy(saved['increment_source_binding']))
        if lazy:
            raw=encode(pack(series[-1]));name='series-'+digest(raw)+'.json'
            if compact:codec.publish_interned(preview_dir/name,raw,root=root,format='chart',bases=[base_series[stock['identity']]] if stock['identity'] in base_series else [])
            else:publish_immutable(preview_dir/name,raw)
            series_files[stock['identity']]=dict(path=name,sha256=digest(raw),bytes=len(raw))
            if len(series)>1:series.pop()  # bounded browser memory; no numerical sampling
    if not series:raise ValueError('No stored core output to preview; no fabricated chart')
    finmind = batch['version'].startswith('finmind-market-history/')
    bundle=dict(schema_version='graph-recognition-chart-bundle/0.2',view_version='graph-recognition-view/0.2',series=series,
        sampling=dict(analysis='CURRENT_SAVED_BATCH_ONLY',prices='ONLY_CAPTURED_OFFICIAL_ROWS_NOT_BACKFILLED'),physical_android='NOT_TESTED_NEW_BUILD',market_run_id=run_id)
    bundle['artifact_id']=fingerprint(bundle)
    if lazy:
        bundle['sampling'].update(prices='FINMIND_FREE_INDIVIDUAL_REPORTED_ROWS_NO_MISSING_PRICE_IMPUTATION')
        bundle['artifact_id']=fingerprint(bundle)
    if incremental:
        bundle['sampling'].update(prices='RETAINED_ORIGINAL_SEGMENT_PLUS_OFFICIAL_NEW_DATE_RESET_NOT_CONTINUOUS_CERTIFICATION')
        bundle['artifact_id']=fingerprint(bundle)
    shell=render(bundle)
    # Existing source-specific M-G3 note applies to its older four-stock parent,
    # not this new native-share bulk feed. All actual source records remain exact.
    volume_note='本頁含既存官方月源；TWSE原股數，TPEx逐月張／仟股×1000不增加精度，不是新整批原生股數認證。' if any(s.get('history_source_provenance') for s in batch['stocks']) else '本頁官方整批API明示原生成交股數；舊TPEx月表仟股／張×1000屬不同來源，不能混用認證。'
    if finmind:
        volume_note='FinMind免費個股TaiwanStockPrice：API原報股數，同日官方原生股數另核；並非全歷史官方精確股數認證。公司行動及歷史上市身分UNKNOWN，跨基底比較未認證。'
    if incremental:
        volume_note='保留原歷史來源及新官方原生股數；跨來源／公司行動未認證，在新官方日明確重啟MA／MACD及可比觀察，不能視為連續完整帶。'
    if batch['summary'].get('synthetic_demo'):volume_note='全部價量與代號均為合成；不是FinMind或交易所原件，不認證任何真實股數。'
    shell=shell.replace('8069原來源顯示精度／單位限制保留，未認證FinMind精確股數。',volume_note)
    shell=shell.replace('>約五年<','>全部累積日K<').replace('已算分析日為每120筆樣本與最近5交易日；K線與查詢保留全部真實來源，不補休市K。其他日期須離線CLI加算，不在UI補算。','本頁只有本次批次已保存分析日；價格僅實際累積官方日K，不宣稱五年或完整交易日曆。原四股歷史主圖獨立保留，不拼接缺失日期。')
    if finmind:
        shell=shell.replace('價格僅實際累積官方日K','價格為FinMind原報歷史日K，來源資格另列')
    if incremental:
        shell=shell.replace('價格僅實際累積官方日K','價格保留原來源歷史及分段官方日K')
    state=dict(summary=batch['summary'],stocks=deepcopy(batch['stocks']))
    if lazy:
        for row in state['stocks']:
            if row['identity'] in series_files:row['preview_series']=series_files[row['identity']]
    if incremental:
        shell=shell.replace('</body>','<a href="/batches">切換已保存批次</a></body>')
    data=json.dumps(state,ensure_ascii=False,separators=(',',':')).replace('<','\\u003c').replace('&','\\u0026')
    js=(Path(__file__).parent/'fm1_20261101/search.js').read_text()
    loader=(Path(__file__).parent/'fm3_20261101/lazy_series.js').read_text() if lazy else ''
    addon='<script id="market-state" type="application/json">'+data+'</script><script>'+loader+'\n'+js+'</script>'
    html=shell.replace('</body>',addon+'</body>')
    out=root/'preview'/run_id/'market-ux1-v02.html'
    if compact:codec.publish(out,html.encode(),root=root,bases=[base_page] if base_page else [])
    else:publish_immutable(out,html.encode())
    return dict(path=str(out),bytes=len(html.encode()),sha256=digest(html.encode()),stocks=len(batch['stocks']),charts=len(series_files) if lazy else len(series),transport='PRIVATE_FILE_OR_LOOPBACK_ONLY_NOT_DEPLOYED',android='NOT_TESTED')


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--root',required=True);p.add_argument('--run',required=True);a=p.parse_args();print(json.dumps(build(a.root,a.run),ensure_ascii=False,indent=2))
