"""Explicit IMPORT/READ/LIST/LOOKUP worker. No numeric engine imports."""
import argparse
import json
import os
import sys
import tempfile
from pathlib import Path
from contracts import DataError
from period_store import PeriodStore, StoreFailure
from period_store_contracts import canonical, pairs, require


def protect_output(root, output, inputs=()):
    root = Path(root); output = Path(output)
    if output.is_symlink() or output.resolve() == root.resolve() or root.resolve() in output.resolve().parents:
        raise StoreFailure('OUTPUT_COLLISION', 'Output must be outside the store and may not be a symlink')
    protected = list(inputs) + (list(root.rglob('*')) if root.exists() else [])
    for p in map(Path, protected):
        if output.resolve() == p.resolve() or output.exists() and p.is_file() and output.samefile(p):
            raise StoreFailure('OUTPUT_COLLISION', 'Output aliases input or store content')


def atomic_export(output, value):
    path = Path(output); temporary = None
    try:
        with tempfile.NamedTemporaryFile(dir=path.parent, prefix='.period-export-', mode='w', encoding='utf-8', delete=False) as f:
            temporary = Path(f.name); f.write(canonical(value) + '\n'); f.flush(); os.fsync(f.fileno())
        os.replace(temporary, path)
    finally:
        if temporary is not None: temporary.unlink(missing_ok=True)


def execute(root, command):
    require(isinstance(command, dict) and command.get('schema_version') == 'period-store-command/1.0', 'command')
    op = command.get('operation')
    fields = {'IMPORT': {'request','result','reason'}, 'READ': {'analysis_id'}, 'LIST': set(), 'LOOKUP': {'filters'}}
    require(op in fields and set(command) == {'schema_version','operation'} | fields[op], 'command.fields')
    if op == 'IMPORT':
        # Validate before creating even an empty store on invalid import.
        from period_store_contracts import validate_bundle
        validate_bundle(command['request'], command['result'])
        require(isinstance(command['reason'], str) and bool(command['reason'].strip()) and len(command['reason']) <= 2000, 'reason')
        return PeriodStore.create(root).save(command['request'], command['result'], reason=command['reason'])
    store = PeriodStore(root)
    if op == 'READ': value = store.load(command['analysis_id'])
    elif op == 'LIST': value = store.list()
    else:
        require(isinstance(command['filters'], dict), 'filters')
        value = store.lookup(**command['filters'])
    return dict(status='READ', commit_status='NOT_APPLICABLE', operation=op, value=value, action_qualification='NOT_EVALUATED')


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--store', required=True); p.add_argument('--input', required=True); p.add_argument('--output', required=True)
    a = p.parse_args(); receipt = None
    try:
        protect_output(a.store, a.output, [a.input])
        command = json.loads(Path(a.input).read_text(encoding='utf-8-sig'), object_pairs_hook=pairs)
        receipt = execute(a.store, command)
        atomic_export(a.output, receipt)
    except (DataError, StoreFailure, OSError, ValueError, UnicodeError) as e:
        error = e.as_dict() if isinstance(e, (DataError, StoreFailure)) else dict(status='STORE_ERROR', code='PERIOD_WORKER_IO', detail=str(e))
        error.setdefault('commit_status', 'NOT_SAVED')
        if receipt is not None:
            error.update(commit_status=receipt['commit_status'], analysis_id=receipt.get('analysis_id'), code='OUTPUT_FILE_ERROR')
        error['action_qualification'] = 'NOT_EVALUATED'
        print(json.dumps(error, ensure_ascii=False), file=sys.stderr)
        return 3 if error['code'] in ('OUTPUT_FILE_ERROR','OUTPUT_COLLISION','PERIOD_WORKER_IO','PERIOD_STORE_IO') else 2
    print(json.dumps(dict(status=receipt['status'], commit_status=receipt['commit_status'],
                         analysis_id=receipt.get('analysis_id'), process_id=os.getpid())))
    return 0


if __name__ == '__main__': raise SystemExit(main())
