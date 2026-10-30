"""Literal, pre-frozen READ expectations, independent of numerical engines."""
from capital_research.lifecycle import FLAGS


def verify(expected, result):
    assert result['status'] == expected['status'], result['refusals']
    assert result['ranking'] is None and result['selected_label'] is None
    assert result['primary_pressure_id'] is None
    assert all(result[k] is False for k in FLAGS)
    if expected['status'] == 'REFUSED':
        assert result['columns'] == [] and not result['comparable']
        paths = {d['path'] for d in result['differences']}
        assert set(expected['mismatch_paths_include']) <= paths, result['differences']
        assert any(r['reason'] == 'COMMON_CONDITIONS_MISMATCH' for r in result['refusals'])
        return
    assert result['comparable'] and not result['refusals']
    assert result['total_mismatches'] == 0 and result['differences'] == []
    columns = result['columns']
    orders = [next(o for o in c['summary']['orders'] if o['order_id'] == 'r1-B') for c in columns]
    assert [o['approved_order_quantity'] for o in orders] == ['20', '20']
    assert [o['filled_quantity'] for o in orders] == expected['B_filled']
    assert [o['live_remaining_quantity'] for o in orders] == expected['B_live_remaining']
    assert [o['reviews'][0]['outcome'] for o in orders] == expected['B_review']
    assert [c['summary']['account']['saved_row']['purchase_payable'] for c in columns] == expected['B_payable']
    assert [c['summary']['account']['origin_initial_capital'] for c in columns] == expected['capital']
    assert result['provenance'][0]['identity_ids'] == result['provenance'][1]['identity_ids']
    if expected.get('distinct_execution_ids'):
        assert result['provenance'][0]['execution_result_id'] != result['provenance'][1]['execution_result_id']
