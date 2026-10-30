"""Read saved synthetic inputs/oracles; write only new diagnostic artifacts."""
import hashlib
import json
from pathlib import Path

from capital_research.opening_evidence import check

HERE=Path(__file__).parent


def digest(path):
    data=path.read_bytes()
    return dict(bytes=len(data),sha256=hashlib.sha256(data).hexdigest())


def dump_new(path, value):
    with path.open('x',encoding='utf-8') as f:
        json.dump(value,f,ensure_ascii=False,indent=2,allow_nan=False);f.write('\n')


def build():
    intake=json.loads((HERE/'intake.json').read_text())
    if (HERE/'summary.json').exists() or any((HERE/'cases'/name/'actual.json').exists() for name in intake['case_names']):
        raise ValueError('Historical outputs already exist; READ them, never silently regenerate')
    for row in intake['input_expected_files']:
        path=HERE.parents[2]/row['path']
        if digest(path)!={k:row[k] for k in ('bytes','sha256')}:
            raise ValueError('Saved input/oracle changed before execution')
    results=[]
    for name in intake['case_names']:
        directory=HERE/'cases'/name
        data=json.loads((directory/'input.json').read_text())
        expected=json.loads((directory/'expected.json').read_text())
        actual=check(data)
        dump_new(directory/'actual.json',actual)
        row=actual['fields'][expected['field']]
        assertions=dict(status=actual['status']==expected['status'],
            classification=row['classification']==expected['classification'],
            preserved_value=row['declared_value']==expected['preserved_value'],
            gap=not expected['required_gap'] or expected['required_gap'] in row['gaps'],
            unsupported=not expected['required_unsupported'] or dict(field=expected['field'],reason=expected['required_unsupported']) in actual['unsupported_capabilities'])
        assertions.update({k:actual[k]==expected[k] for k in ('authenticity_verified','opening_entitlements_verified','ledger_called','legacy_qualification_updates')})
        results.append(dict(case=name,status=actual['status'],assertions=assertions,matched=all(assertions.values()),
                            input=digest(directory/'input.json'),expected=digest(directory/'expected.json'),actual=digest(directory/'actual.json')))
    dump_new(HERE/'summary.json',dict(schema='opening-evidence-synthetic-summary/0.1',
        cases=results,all_matched=all(x['matched'] for x in results),synthetic_only=True,
        independent_market_samples=0,real_account_qualifications_added=0,ledger_calls=0,
        note='22 synthetic fixtures are not 22 independent market samples or a test-method count'))
    if not all(x['matched'] for x in results):
        raise AssertionError('Saved expected/actual mismatch; preserve outputs and diagnose without changing the oracle')
    print(f'{len(results)} saved synthetic inputs matched the pre-saved expectations; no ledger/producer call')


if __name__=='__main__':build()
