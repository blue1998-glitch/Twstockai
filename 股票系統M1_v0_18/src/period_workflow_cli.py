"""One explicit period workflow command; compact stdout receipt, full JSON output."""
import argparse
import json
import os
import sys
from pathlib import Path
from contracts import DataError
from period_store import StoreFailure
from period_store_contracts import canonical, pairs
from period_store_cli import protect_output, atomic_export
from period_workflow import execute_period_workflow, WorkflowError, SCHEMA, VERSION


def _error(e, stage, response=None):
    identities = {k:response[k] for k in ('analysis_id','request_fingerprint','result_fingerprint') if k in (response or {})}
    return WorkflowError(e.code if isinstance(e, (DataError, StoreFailure)) else 'PERIOD_WORKFLOW_FILE',
                         e.path if isinstance(e, DataError) else 'file',
                         e.detail if isinstance(e, (DataError, StoreFailure)) else type(e).__name__,
                         stage=stage, operation=(response or {}).get('operation'),
                         commit_status=(response or {}).get('commit_status','NOT_SAVED'), identities=identities)


def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--store', required=True); p.add_argument('--input', required=True); p.add_argument('--output', required=True)
    p.add_argument('--create', action='store_true')
    a = p.parse_args(argv); response = None
    try:
        try:
            protect_output(a.store, a.output, [a.input])
            command = json.loads(Path(a.input).read_text(encoding='utf-8-sig'), object_pairs_hook=pairs)
        except (DataError, StoreFailure, OSError, ValueError, UnicodeError) as e:
            raise _error(e, 'FILE_PREFLIGHT') from None
        response = execute_period_workflow(command, a.store, create_if_missing=a.create)
        try: atomic_export(a.output, response)
        except (DataError, OSError, ValueError, UnicodeError) as e:
            raise _error(e, 'EXPORT', response) from None
        receipt = dict(schema_version=SCHEMA, workflow_version=VERSION, status='OUTPUT_WRITTEN',
                       operation=response['operation'], workflow_status=response['status'],
                       commit_status=response['commit_status'], process_id=os.getpid())
        for k in ('analysis_id','request_fingerprint','result_fingerprint','store_status'):
            if k in response: receipt[k] = response[k]
        try: print(canonical(receipt))
        except OSError as e: raise _error(e, 'STDOUT', response) from None
        return 0
    except WorkflowError as e:
        print(canonical(dict(**e.as_dict(), process_id=os.getpid())), file=sys.stderr)
        return 3 if e.stage in ('FILE_PREFLIGHT','EXPORT','STDOUT') else 2


if __name__ == '__main__': raise SystemExit(main())
