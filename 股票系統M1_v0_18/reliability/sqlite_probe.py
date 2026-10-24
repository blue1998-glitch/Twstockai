"""Read-only incident observation. JSON to stdout; never recover or create files.

This is not a backup, authenticity check, or full AnalysisStore validation.
Run after stopping writers; before/after hashes only detect observed changes.
"""
import argparse
import hashlib
import json
import sqlite3
import stat
from pathlib import Path


def files(path):
    result = {}
    for suffix in ('', '-journal', '-wal', '-shm'):
        p = Path(str(path) + suffix)
        try:
            before = p.stat()
            h = hashlib.sha256()
            with p.open('rb') as stream:
                for chunk in iter(lambda: stream.read(1024 * 1024), b''):
                    h.update(chunk)
            after = p.stat()
            result[suffix or 'database'] = dict(
                bytes=after.st_size, sha256=h.hexdigest(),
                device=after.st_dev, inode=after.st_ino,
                mode=stat.S_IMODE(after.st_mode), mtime_ns=after.st_mtime_ns,
                stable_while_hashing=(before.st_size, before.st_mtime_ns, before.st_ino)
                == (after.st_size, after.st_mtime_ns, after.st_ino))
        except FileNotFoundError:
            result[suffix or 'database'] = dict(exists=False)
        except OSError as e:
            result[suffix or 'database'] = dict(error=type(e).__name__, detail=str(e))
    return result


def probe(path):
    path = Path(path).resolve()
    before = files(path)
    conn = None
    try:
        # Read-only WAL connections may create/update shared-memory sidecars.
        # Refuse before connecting, including clean WAL headers with no sidecars.
        # This requires quiescent writers; header inspection is not a lock.
        wal_hint = any(before[s].get('exists', True) for s in ('-wal', '-shm'))
        try:
            with path.open('rb') as stream:
                header = stream.read(20)
            wal_hint = wal_hint or (header[:16] == b'SQLite format 3\x00'
                                    and 2 in header[18:20])
        except OSError:
            pass  # mode=ro below reports a missing/unreadable path, never creates.
        if wal_hint:
            observation = dict(status='READ_REFUSED_WAL',
                               detail='WAL header/sidecar observed; no SQLite connection opened, no immutable bypass')
            after = files(path)
            return dict(schema_version='sqlite-incident-observation/1.0',
                        sqlite_version=sqlite3.sqlite_version, database=str(path),
                        access='READ_ONLY_NO_RECOVERY', observation=observation,
                        before=before, after=after, observed_files_unchanged=before == after,
                        root_cause='NOT_ESTABLISHED',
                        limits='WAL unsupported; observation requires stopped writers and is not a coherent backup')
        conn = sqlite3.connect(path.as_uri() + '?mode=ro', uri=True,
                               isolation_level=None, timeout=0)
        conn.execute('PRAGMA query_only=ON')
        conn.execute('BEGIN')
        observation = dict(
            status='READABLE',
            application_id=conn.execute('PRAGMA application_id').fetchone()[0],
            user_version=conn.execute('PRAGMA user_version').fetchone()[0],
            journal_mode=conn.execute('PRAGMA journal_mode').fetchone()[0],
            quick_check=[r[0] for r in conn.execute('PRAGMA quick_check')])
    except sqlite3.Error as e:
        observation = dict(status='READ_FAILED', error=type(e).__name__, detail=str(e),
                           sqlite_errorcode=getattr(e, 'sqlite_errorcode', None),
                           sqlite_errorname=getattr(e, 'sqlite_errorname', None))
    finally:
        if conn is not None:
            conn.close()
    after = files(path)
    return dict(schema_version='sqlite-incident-observation/1.0',
                sqlite_version=sqlite3.sqlite_version, database=str(path),
                access='READ_ONLY_NO_RECOVERY', observation=observation,
                before=before, after=after, observed_files_unchanged=before == after,
                root_cause='NOT_ESTABLISHED',
                limits='No coherent live backup, engine result validation, recovery, or attribution of an earlier incident')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--db', required=True)
    args = parser.parse_args()
    report = probe(args.db)
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0 if (report['observation']['status'] == 'READABLE'
                 and report['observation']['quick_check'] == ['ok']
                 and report['observed_files_unchanged']) else 2


if __name__ == '__main__':
    raise SystemExit(main())
