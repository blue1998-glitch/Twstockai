"""Single-file synthetic viewer. Financial values are original engine outputs."""
from pathlib import Path
import json


def render(comparison, manifest):
    if comparison['status'] != 'COMPARABLE_SYNTHETIC_ACCOUNTS':
        raise ValueError('REFUSED_COMPARISON_CANNOT_RENDER')
    b=comparison['common'];cp=b['account']['checkpoint']['state']
    payload=dict(schema='cap1-mobile-view/0.1',synthetic=True,
        comparison_id=comparison['comparison_id'],basis_id=comparison['basis_id'],
        decision_at=b['information']['decision_at'],cutoff=b['information']['data_cutoff'],
        evaluation_at=b['evaluation_at'],choice_row=cp['row'],
        general_reserve=cp['general_reserved_cash'],branches=comparison['branches'],
        source_manifest=manifest,qualification={k:comparison[k] for k in
        ('execution_qualified','historical_signal_eligible','policy_authorized','primary_pressure_id','ranking','strategy_validated')},
        unavailable=dict(status='NOT_IMPLEMENTED',kind='EXIT_ALL_TO_CASH',metrics=None,
            reason='缺少全資產賣出、成交與待交付權利處理證據。'))
    here=Path(__file__).parent
    data=json.dumps(payload,ensure_ascii=False,separators=(',',':'),allow_nan=False).replace('<','\\u003c')
    return (here/'viewer.html').read_text().replace('/*INLINE_STYLE*/',(here/'viewer.css').read_text()).replace('/*INLINE_SCRIPT*/',(here/'viewer.js').read_text()).replace('CAP1_DATA_PLACEHOLDER',data)
