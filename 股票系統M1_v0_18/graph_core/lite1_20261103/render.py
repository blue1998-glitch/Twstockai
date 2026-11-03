"""Render only a small new shell; all original graph/data shards untouched."""
import json,time,resource,shutil
from pathlib import Path
from graph_core.lite1_20261103.build import encoded,digest,budget
from technical_chart.build import pack
from rotation_research import artifact_codec as c

HERE=Path(__file__).parent
PROJECT=HERE.parents[1]

def render(output):
    output=Path(output);started=time.monotonic();entries=[];summary=[]
    viewer=(PROJECT/'graph_core_chart/viewer.js').read_text()
    boot="new ResizeObserver(()=>draw()).observe($('chart'));options($('stock'),data.series.map(s=>[s.code,s.code]),data.series[0].code);setup(data.series[0].code);"
    if viewer.count(boot)!=1:raise ValueError('EXACT_EXISTING_VIEWER_BOOT_REQUIRED')
    # Display-only 60px heading space; keep original pane heights with a 60px taller canvas.
    pane='const price={top:30,bottom:h*.57},volume={top:h*.63,bottom:h*.76},macd={top:h*.83,bottom:h-23}'
    if viewer.count(pane)!=1:raise ValueError('EXACT_EXISTING_PANE_LAYOUT_REQUIRED')
    viewer=viewer.replace(pane,'const plotH=h-60;const price={top:90,bottom:plotH*.57+60},volume={top:plotH*.63+60,bottom:plotH*.76+60},macd={top:plotH*.83+60,bottom:h-23}')
    extension=(PROJECT/'graph_core_chart/viewer_v02.js').read_text()
    extension=extension.replace('；FinMind未混入。','；依保存來源與分段界線。').replace('8069原來源顯示精度／單位限制保留，未認證FinMind精確股數。','來源與公司行動依保存資格；跨來源不自動認證。')
    viewer=viewer.replace(boot,extension+"\nnew ResizeObserver(()=>{if(result)draw();}).observe($('chart'));")
    # Same list on explicit expansion, rather than thousands of hidden DOM rows.
    viewer+="\nconst originalBuildList=buildList;buildList=()=>{if($('candidates').open)originalBuildList();else $('candidateList').replaceChildren();};$('candidates').ontoggle=()=>{if($('candidates').open&&result)originalBuildList();};\n"
    scope=(PROJECT/'graph_core/comp1_20261102/compare.js').read_text().split("if(typeof window!=='undefined')",1)[0]
    script=viewer+'\n'+(PROJECT/'graph_core/fm3_20261101/lazy_series.js').read_text()+'\n'+scope+'\n'+(HERE/'copy.js').read_text()+'\n'+(HERE/'view.js').read_text()
    style=(PROJECT/'graph_core_chart/viewer.css').read_text()+'\n'+(PROJECT/'graph_core_chart/viewer_v02.css').read_text()+'\n'+(HERE/'style.css').read_text()
    template=(PROJECT/'graph_core_chart/template.html').read_text()
    bundle=dict(schema_version='graph-recognition-chart-bundle/0.2',view_version='graph-recognition-view/0.2',series=[],sampling=dict(prices='ORIGINAL_BOUND_SERIES_ON_DEMAND'))
    payload=json.dumps(pack(bundle),ensure_ascii=False,separators=(',',':')).replace('<','\\u003c')
    ui_sha=digest((script+style+template).encode())
    latest=max(x['as_of'] for x in json.loads((output/'preparation-private.json').read_bytes())['batches'])
    completed=output/('render-'+ui_sha[:12]+'-private.json')
    if completed.exists():
        old=json.loads(completed.read_bytes());catalogue=json.loads(Path(old['catalogue']).read_bytes())
        for item in catalogue['batches']:
            raw=Path(item['path']).read_bytes()
            if len(raw)!=item['bytes'] or digest(raw)!=item['sha256']:raise ValueError('EXISTING_LITE_SHELL_CHANGED')
        return dict(old,reused_completed_view=True)
    for receipt in json.loads((output/'preparation-private.json').read_bytes())['batches']:
        folder=Path(receipt['folder']);state=json.loads((folder/'prepared-state-private.json').read_bytes())
        data=json.dumps(state,ensure_ascii=False,separators=(',',':')).replace('<','\\u003c').replace('&','\\u0026')
        html=template.replace('@@STYLE@@',style).replace('@@DATA@@',payload).replace('@@SCRIPT@@',script)
        html=html.replace('</body>','<script id="market-state" type="application/json">'+data+'</script></body>')
        # State must exist before script execution, without embedding any chart.
        html=html.replace('<title>M1 圖形辨識研究主圖 0.1</title>','<title>Twstockai 股票系統</title>')
        context='<script id="lite-view-context" type="application/json">'+json.dumps(dict(latest_saved_as_of=latest))+'</script>'
        marker='<script id="payload"';index=html.index(marker);tail='<script id="market-state" type="application/json">'+data+'</script>'
        html=html.replace(tail,'');html=html[:index]+tail+context+html[index:]
        raw=html.encode();name='market-lite1-'+ui_sha[:12]+'.html'
        if len(raw)>=10*1024*1024:raise ValueError('LITE_INITIAL_HTML_10MIB_BOUND')
        with budget(output):c.immutable(folder/name,raw)
        entries.append(dict(run_id=receipt['source_run'],as_of=receipt['as_of'],path=str(folder/name),bytes=len(raw),sha256=digest(raw)))
        summary.append(dict(as_of=receipt['as_of'],html_bytes=len(raw),stocks=receipt['stocks'],charts=receipt['charts'],original_events=receipt['original_events'],initial_embedded_events=0,initial_embedded_charts=0,ui_sha256=ui_sha))
    raw=encoded(dict(schema='private-saved-batches/0.1',batches=entries));catalogue=output/('lite-batches-'+digest(raw)+'.json')
    with budget(output):c.immutable(catalogue,raw)
    receipt=dict(status='SMALL_NEW_SHELL_RENDERED',catalogue=str(catalogue),batches=summary,elapsed_seconds=time.monotonic()-started,max_rss_kib=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,free_bytes=shutil.disk_usage(output).free)
    c.immutable(completed,encoded(receipt));return receipt

if __name__=='__main__':
    import sys
    print(json.dumps(render(sys.argv[1:] [0])))
