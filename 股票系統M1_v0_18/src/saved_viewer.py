"""Read-only offline export of immutable saved bundles. No engine execution."""
import argparse
import json
import os
from pathlib import Path
import sys
import tempfile

from analysis_store import AnalysisStore
from contracts import DataError
from store_contracts import canonical

SCHEMA = 'saved-analysis-view/1.0'
VERSION = 'saved-viewer-0.1'
TEMPLATE = Path(__file__).resolve().parents[1] / 'saved_viewer_template.html'


def export_saved(database, record_ids=None):
    """Only public mode=ro reads; never recover, create, save or calculate.

    The record set is the list captured at the start. Concurrent new appends
    require another export; old immutable bundles are not replaced.
    """
    store = AnalysisStore(database)
    rows = store.list_records()
    if record_ids is None:
        ids = [r['record_id'] for r in rows]
    else:
        if (not isinstance(record_ids, list) or not record_ids or
                any(not isinstance(r, str) for r in record_ids) or
                len(set(record_ids)) != len(record_ids)):
            raise DataError('VIEW_SELECTION', 'record_ids', 'Provide distinct exact saved record IDs')
        ids = record_ids
        if not set(ids).issubset({r['record_id'] for r in rows}):
            raise DataError('VIEW_NOT_FOUND', 'record_ids', 'Saved record not found; no automatic replacement')
    bundles = [store.load(rid) for rid in ids]
    return dict(schema_version=SCHEMA, exporter_version=VERSION, records=bundles,
                classification_quality='NOT_VALIDATED', action_qualification='NOT_EVALUATED')


def render_html(payload, template=None):
    if payload.get('schema_version') != SCHEMA:
        raise DataError('VIEW_SCHEMA', 'schema_version', 'Unsupported saved view format')
    text = TEMPLATE.read_text(encoding='utf-8') if template is None else template
    marker = '__SAVED_ANALYSIS_DATA__'
    if text.count(marker) != 1:
        raise DataError('VIEW_TEMPLATE', 'template', 'Exactly one data marker required')
    # Keep every stored string exact in JSON while preventing HTML/script escape.
    encoded = canonical(payload)
    for char, escaped in [('&', '\\u0026'), ('<', '\\u003c'), ('>', '\\u003e'),
                          ('\u2028', '\\u2028'), ('\u2029', '\\u2029')]:
        encoded = encoded.replace(char, escaped)
    return text.replace(marker, encoded)


def write_html(database, output, record_ids=None):
    db = Path(database).resolve()
    target = Path(output)
    # Protect DB, rollback/WAL/SHM files and hard-link/symlink aliases, even
    # when export will subsequently fail. Never delete or recover sidecars.
    protected = [db] + [Path(str(db) + suffix) for suffix in ['-journal', '-wal', '-shm']]
    resolved = target.resolve()
    for p in protected:
        if resolved == p or (target.exists() and p.exists() and os.path.samefile(target, p)):
            raise DataError('VIEW_OUTPUT_COLLISION', 'output', 'Output aliases database or recovery files')
    if target.is_symlink():
        raise DataError('VIEW_OUTPUT_COLLISION', 'output', 'Output must not be a symbolic link')
    payload = export_saved(db, record_ids)
    html = render_html(payload)
    temporary = None
    try:
        with tempfile.NamedTemporaryFile(mode='w', encoding='utf-8', dir=target.parent,
                                         prefix='.saved-view-', delete=False) as f:
            temporary = Path(f.name)
            f.write(html)
            f.flush()
            os.fsync(f.fileno())
        os.replace(temporary, target)
    finally:
        if temporary is not None and temporary.exists():
            temporary.unlink()
    return dict(schema_version=SCHEMA, status='EXPORTED', records=len(payload['records']),
                snapshots=sum(len(b['result']['aligned_snapshots']) for b in payload['records']),
                database_access='READ_ONLY_NO_RECOVERY', action_qualification='NOT_EVALUATED')


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--db', required=True)
    p.add_argument('--output', required=True)
    p.add_argument('--record-id', action='append', help='Exact ID, repeat for an explicit selection')
    a = p.parse_args()
    try:
        result = write_html(a.db, a.output, a.record_id)
        print(json.dumps(result, ensure_ascii=False))
        return 0
    except (DataError, OSError, ValueError) as e:
        result = e.as_dict() if isinstance(e, DataError) else dict(status='VIEW_EXPORT_ERROR', detail=str(e))
        result['database_access'] = 'READ_ONLY_NO_RECOVERY'
        print(json.dumps(result, ensure_ascii=False))
        return 2


if __name__ == '__main__':
    sys.exit(main())
