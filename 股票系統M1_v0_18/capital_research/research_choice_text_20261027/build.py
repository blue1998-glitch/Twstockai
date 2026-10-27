"""Save new READ-only text and exact default-JSON receipts from old originals."""
import hashlib
from copy import deepcopy
from pathlib import Path
import tempfile
from .helpers import ROOT, REPO, OLD, load, save, run_cli


def main():
    rows = []
    for spec in load(ROOT / 'input-expected.json'):
        source = REPO / spec['source']['path']; before = source.read_bytes()
        assert len(before) == spec['source']['bytes'] and hashlib.sha256(before).hexdigest() == spec['source']['sha256']
        args = ['READ', '--store', str(OLD / 'journal'), '--id', spec['key']]
        text = run_cli(args + ['--format', 'text'])
        default_json = run_cli(args)
        save(ROOT / 'actual' / spec['key'] / 'text-receipt.json', text)
        save(ROOT / 'actual' / spec['key'] / 'json-receipt.json', default_json)
        with (ROOT / 'actual' / spec['key'] / 'readable.txt').open('x') as f:
            f.write(text['stdout'])
        assert text['exit_code'] == default_json['exit_code'] == spec['expected']['exit_code']
        assert not text['stderr'] and not default_json['stderr']
        assert all(fragment in text['stdout'] for fragment in spec['expected']['contains'])
        if spec['expected']['reason']:
            assert spec['expected']['reason'] in text['stdout']
        assert load(OLD / 'receipts' / (spec['key'] + '-read.json')) == __import__('json').loads(default_json['stdout'])
        assert source.read_bytes() == before
        rows.append(dict(key=spec['key'],status='PASS',old_source_unchanged=True,
            old_json_receipt_equal=True,expected_exit_code=spec['expected']['exit_code']))
        print(spec['key'], 'PASS', flush=True)
    save(ROOT / 'actual' / 'summary.json', rows)
    with tempfile.TemporaryDirectory() as folder:
        store = Path(folder); original = load(OLD / 'journal' / 'grid-intent.json')
        negatives = load(ROOT / 'negative-input-expected.json')
        for spec in negatives:
            if spec['edits'] is None:
                continue
            row = deepcopy(original)
            for edit in spec['edits']:
                target = row
                for key in edit['path'][:-1]:
                    target = target[key]
                target[edit['path'][-1]] = edit['value']
            save(store / (spec['key'] + '.json'), row)
        before = {p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in store.iterdir()}
        results = []
        for spec in negatives:
            args = ['READ', '--store', str(store), '--id', spec['key'], '--format', 'text']
            if spec['key'] == 'SELECT-text':
                args = ['SELECT','--store',str(store),'--id','must-not-exist','--format','text','--input',str(store / 'missing-input.json')]
            result = run_cli(args)
            results.append(dict(key=spec['key'],actual=result))
            assert result['exit_code'] == spec['exit_code'] and not result['stdout']
            assert spec['reason'] in result['stderr'], result
        after = {p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in store.iterdir()}
        save(ROOT / 'negative-actual.json', dict(results=results,files_before=before,files_after=after))
        assert before == after


if __name__ == '__main__':
    main()
