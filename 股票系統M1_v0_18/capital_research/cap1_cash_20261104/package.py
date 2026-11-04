"""Package the existing CAP1 interface with FOUR validated saved synthetic paths."""
from pathlib import Path
import json,io,zipfile,shutil
from .build import CAP,ROOT,OLD,DELIVERY,MIN_FREE,BUDGET,read,write,sha
from ..core import fingerprint
HTML_NAME='Twstockai_CAP1_FullCash_v02.html'
ZIP_NAME='Twstockai_CAP1_FullCash_v02.zip'


def render(result,declaration):
    if result['status']!='COMPARABLE_SYNTHETIC_ACCOUNTS' or result['branches']['cash']['liquidation']['status']!='VERIFIED_ALL_CASH_SYNTHETIC':raise ValueError('FULL_CASH_COMPARISON_NOT_VERIFIED')
    b=result['common']
    if not (b['origin']==declaration['seed_execution_spec']['origin_ledger'] and b['close']==declaration['seed_execution_spec']['ledger_close_proof'] and b['information']==declaration['decision_template'] and b['policy']==declaration['policy'] and b['tape']==declaration['tape'] and b['observed_until']==declaration['observed_until'] and b['evaluation_at']==declaration['evaluation_at']):raise ValueError('DECLARATION_COMPARISON_SOURCE_CONFLICT')
    cp=b['account']['checkpoint']['state']
    payload=dict(schema='cap1-four-actions-mobile/0.2',synthetic=True,comparison_id=result['comparison_id'],basis_id=result['basis_id'],
        decision_at=b['information']['decision_at'],cutoff=b['information']['data_cutoff'],evaluation_at=b['evaluation_at'],
        choice_row=cp['row'],general_reserve=cp['general_reserved_cash'],branches=result['branches'],
        source_manifest=dict(new_synthetic_declaration_id=fingerprint(declaration),declaration_sha256=sha((CAP/'declaration-v03.json').read_bytes()),
            original_case_commit='692594ee1567ac7f795da972a10ae6d89691f5e8',new_account_not_old_rights_release=True),
        qualification={k:result[k] for k in ('execution_qualified','historical_signal_eligible','policy_authorized','primary_pressure_id','ranking','strategy_validated')})
    data=json.dumps(payload,ensure_ascii=False,separators=(',',':'),allow_nan=False).replace('<','\\u003c')
    return (CAP/'viewer.html').read_text().replace('/*INLINE_STYLE*/',(CAP/'viewer.css').read_text()).replace('/*INLINE_SCRIPT*/',(CAP/'viewer.js').read_text()).replace('CAP1_DATA_PLACEHOLDER',data)


def package():
    if shutil.disk_usage(ROOT).free < MIN_FREE+BUDGET:raise ValueError('CAPACITY_BUDGET_REFUSED')
    result=read(CAP/'artifacts/comparison.json');html=render(result,read(CAP/'declaration-v03.json')).encode()
    write(DELIVERY/HTML_NAME,html);z=io.BytesIO()
    with zipfile.ZipFile(z,'w',compression=zipfile.ZIP_DEFLATED,compresslevel=9) as archive:
        for name,body in [(HTML_NAME,html),('README.txt','純合成帳戶，期初已交割，四方案同一起點。解壓後以瀏覽器開啟HTML。全退出在全部股份成交、款項交割且無剩餘權利後才標示全現金；非真實績效，不自動選最佳。'.encode())]:
            info=zipfile.ZipInfo(name,(2026,11,4,0,0,0));info.compress_type=zipfile.ZIP_DEFLATED;archive.writestr(info,body)
    write(DELIVERY/ZIP_NAME,z.getvalue())
    out=dict(schema='cap1-cash-package/0.2',synthetic=True,engine_calls=0,files=[dict(path=str(p.relative_to(ROOT)),bytes=p.stat().st_size,sha256=sha(p.read_bytes())) for p in [DELIVERY/HTML_NAME,DELIVERY/ZIP_NAME]])
    write(CAP/'package-verification.json',out);print(json.dumps(out,ensure_ascii=False))

if __name__=='__main__':package()
