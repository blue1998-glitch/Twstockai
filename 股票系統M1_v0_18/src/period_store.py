"""Independent immutable JSON store. Directory entries are the authoritative index."""
import json
import os
import re
import tempfile
from pathlib import Path
from contracts import DataError, fingerprint
from period_store_contracts import STORE_SCHEMA, RECORD_SCHEMA, canonical, pairs, require, validate_bundle

HEADER = {'schema_version': STORE_SCHEMA, 'record_schema': RECORD_SCHEMA,
          'index': 'COMMITTED_ANALYSIS_ID_JSON_FILES', 'overwrite': False}
HEX = re.compile(r'^[0-9a-f]{64}$')


class StoreFailure(Exception):
    def __init__(self, code, detail, commit_status='NOT_SAVED', analysis_id=None):
        super().__init__(detail)
        self.code, self.detail, self.commit_status, self.analysis_id = code, detail, commit_status, analysis_id

    def as_dict(self):
        return dict(status='STORE_ERROR', code=self.code, detail=self.detail, commit_status=self.commit_status,
                    analysis_id=self.analysis_id, action_qualification='NOT_EVALUATED')


def _sync_dir(path):
    fd = os.open(path, os.O_RDONLY | os.O_DIRECTORY)
    try: os.fsync(fd)
    finally: os.close(fd)


def _publish(path, value):
    """One fsynced object, one exclusive link commit; never replaces an old file."""
    temporary = None; linked = False
    try:
        with tempfile.NamedTemporaryFile(dir=path.parent, prefix='.pending-', mode='w', encoding='utf-8', delete=False) as f:
            temporary = Path(f.name); f.write(canonical(value) + '\n'); f.flush(); os.fsync(f.fileno())
        os.link(temporary, path)
        linked = True
        _sync_dir(path.parent)
    except FileExistsError:
        return False
    except OSError as e:
        raise StoreFailure('PERIOD_STORE_IO', str(e), 'UNKNOWN' if linked else 'NOT_SAVED') from e
    finally:
        if temporary is not None:
            try: temporary.unlink(missing_ok=True)
            except OSError: pass  # A pending file is never a committed entry; preserve on failure.
    return True


def _read_json(path):
    if path.is_symlink(): raise StoreFailure('PERIOD_STORE_SYMLINK', str(path))
    try: return json.loads(path.read_text(encoding='utf-8'), object_pairs_hook=pairs)
    except DataError: raise
    except (OSError, ValueError, UnicodeError) as e: raise StoreFailure('PERIOD_STORE_READ', str(e)) from e


class PeriodStore:
    """Opening/reading is strictly read only. Creation/import are explicit actions."""
    def __init__(self, root):
        self.root = Path(root)
        if self.root.is_symlink(): raise StoreFailure('PERIOD_STORE_SYMLINK', str(root))
        require(_read_json(self.root / 'STORE.json') == HEADER, 'store.header', 'Unsupported or damaged store header')

    @classmethod
    def create(cls, root):
        path = Path(root)
        if path.is_symlink(): raise StoreFailure('PERIOD_STORE_SYMLINK', str(root))
        if path.exists():
            if not (path / 'STORE.json').exists():
                raise StoreFailure('PERIOD_STORE_UNINITIALIZED', 'Existing directory without header; preserve for diagnosis')
        else:
            try:
                path.mkdir(parents=True)
            except FileExistsError: pass  # Concurrent initializer; exclusive header publish below.
            _publish(path / 'STORE.json', HEADER)
            _sync_dir(path.parent)
        return cls(path)

    def load(self, analysis_id):
        require(isinstance(analysis_id, str) and analysis_id.startswith('sha256:') and HEX.fullmatch(analysis_id[7:]), 'analysis_id')
        record = _read_json(self.root / (analysis_id[7:] + '.json'))
        canonical(record)
        require(isinstance(record, dict) and set(record) == {'schema_version','analysis_id','request','result','reason','metadata','record_fingerprint'}, 'record.fields')
        require(record['schema_version'] == RECORD_SCHEMA and record['analysis_id'] == analysis_id, 'record.identity')
        payload = {k:v for k,v in record.items() if k != 'record_fingerprint'}
        require(record['record_fingerprint'] == fingerprint(payload), 'record.fingerprint')
        require(isinstance(record['reason'], str) and bool(record['reason'].strip()) and len(record['reason']) <= 2000, 'reason')
        metadata = validate_bundle(record['request'], record['result'])
        require(record['result']['analysis_id'] == analysis_id and record['metadata'] == metadata, 'record.links')
        return record

    def save(self, request, result, *, reason):
        metadata = validate_bundle(request, result)
        require(isinstance(reason, str) and bool(reason.strip()) and len(reason) <= 2000, 'reason')
        aid = result['analysis_id']
        payload = dict(schema_version=RECORD_SCHEMA, analysis_id=aid, request=request, result=result, reason=reason, metadata=metadata)
        record = dict(**payload, record_fingerprint=fingerprint(payload))
        try:
            created = _publish(self.root / (aid[7:] + '.json'), record)
        except StoreFailure as e:
            e.analysis_id = aid
            raise
        if not created:
            old = self.load(aid)
            if canonical(old) != canonical(record):
                raise StoreFailure('PERIOD_STORE_CONFLICT', 'Same analysis identity has different immutable content; old record retained', analysis_id=aid)
        return dict(status='SAVED' if created else 'DUPLICATE', commit_status='COMMITTED',
                    analysis_id=aid, record_fingerprint=record['record_fingerprint'], action_qualification='NOT_EVALUATED')

    def list(self):
        result = []
        for path in sorted(self.root.iterdir()):
            if path.name == 'STORE.json' or path.name.startswith('.pending-'): continue
            require(path.suffix == '.json' and HEX.fullmatch(path.stem), 'store.entry', 'Unexpected store entry; inspect without deleting')
            r = self.load('sha256:' + path.stem)
            result.append(dict(analysis_id=r['analysis_id'], reason=r['reason'], record_fingerprint=r['record_fingerprint'], **r['metadata']))
        return sorted(result, key=lambda r:(r['exchange'],r['code'],r['price_mode'],r['as_of'],r['analysis_id']))

    def lookup(self, **filters):
        required = {'code','exchange','price_mode','as_of'}
        allowed = required | {'rule_version','aggregation_version','adapter_version','parameters_fingerprint','source_id'}
        require(required <= set(filters) <= allowed, 'lookup.filters', 'Exact stock/exchange/mode/as_of required; no latest fallback')
        return [r for r in self.list() if all(r[k] == v for k,v in filters.items())]

    def diagnostics(self):
        # Interrupted unpublished files are reported, never repaired/deleted by reads.
        return dict(committed_records=len(self.list()), pending_files=sorted(p.name for p in self.root.glob('.pending-*')),
                    recovery='PENDING_FILES_ARE_UNCOMMITTED; NO_AUTOMATIC_CLEANUP')
