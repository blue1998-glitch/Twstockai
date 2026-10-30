"""Save synthetic acceptance actuals; never acquires or copies real quotes."""
import hashlib
import json
from pathlib import Path
from graph_core.finmind_adapter import IntakeError, analyze_response, public_summary

HERE = Path(__file__).resolve().parent


def main():
    frozen = json.loads((HERE / 'refusal-frozen.json').read_text())
    raw = (HERE / 'refusal-inputs.json').read_bytes()
    assert hashlib.sha256(raw).hexdigest() == frozen['sha256']
    job = json.loads((HERE / 'input.json').read_text())
    expected = json.loads((HERE / 'expected.json').read_text())
    result = analyze_response(job['response'], job['request'])
    summary = public_summary(result)
    assert summary['status'] == expected['valid']
    assert summary['as_of'] == expected['anchor']
    assert summary['primary_pressure_id'] == expected['primary_pressure_id']
    assert summary['data_qualified'] == expected['data_qualified']
    cases = []
    for case in json.loads(raw):
        try:
            analyze_response(case['input']['response'], case['input']['request'])
            actual = 'UNEXPECTED_ACCEPTANCE'
        except IntakeError as exc:
            actual = str(exc)
        cases.append(dict(id=case['id'], expected=case['expected'], actual=actual,
                          matched=actual == case['expected']))
    assert all(c['matched'] for c in cases)
    data = dict(source_kind='SYNTHETIC_ONLY_NOT_MARKET_PERFORMANCE',
                positive_summary=summary, positive_core_result=result['analysis'],
                refusal_results=cases, all_matched=True,
                test_count_note='Evidence materialization, not additional unique test methods')
    with (HERE / 'synthetic-actual.json').open('x') as stream:
        stream.write(json.dumps(data, ensure_ascii=False, indent=2) + '\n')
    print('Synthetic actual saved; 1 positive and', len(cases), 'refusals matched')


if __name__ == '__main__': main()
