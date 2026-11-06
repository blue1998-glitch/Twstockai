"""Append-only SQLite research storage, separate from the numeric engines.

Read/write explicit paths only. No network, UI, global database or engine
execution. JSON content hashes check consistency, not source authentication.
"""
from contextlib import contextmanager
from datetime import datetime,timezone
import os,json,sqlite3
from pathlib import Path
from contracts import DataError,fingerprint,iso_date
from store_contracts import canonical,validate_bundle

APP_ID=0x53544B31
DB_VERSION=1
SCHEMA='analysis-store/1.0'
DDL=[
'''CREATE TABLE objects(object_id TEXT PRIMARY KEY,kind TEXT NOT NULL CHECK(kind IN ('request','result','evidence','rules')),fingerprint TEXT NOT NULL,payload TEXT NOT NULL,UNIQUE(kind,fingerprint))''',
'''CREATE TABLE analyses(analysis_id TEXT PRIMARY KEY,code TEXT NOT NULL,exchange TEXT NOT NULL,price_mode TEXT NOT NULL,request_id TEXT NOT NULL REFERENCES objects(object_id),result_id TEXT NOT NULL REFERENCES objects(object_id),rules_id TEXT NOT NULL REFERENCES objects(object_id))''',
'''CREATE TABLE records(record_id TEXT PRIMARY KEY,analysis_id TEXT NOT NULL REFERENCES analyses(analysis_id),evidence_id TEXT NOT NULL REFERENCES objects(object_id),created_at_utc TEXT NOT NULL,reason TEXT NOT NULL,UNIQUE(analysis_id,evidence_id))''',
'''CREATE TABLE snapshots(analysis_id TEXT NOT NULL REFERENCES analyses(analysis_id),as_of TEXT NOT NULL,structure_snapshot_id TEXT NOT NULL,daily_ma_snapshot_id TEXT NOT NULL,aligned_snapshot_id TEXT NOT NULL,PRIMARY KEY(analysis_id,as_of))''',
'''CREATE INDEX analyses_by_stock ON analyses(code,price_mode)''',
]
for table in ['objects','analyses','records','snapshots']:
    for action in ['UPDATE','DELETE']:
        DDL.append(f"CREATE TRIGGER immutable_{table}_{action.lower()} BEFORE {action} ON {table} BEGIN SELECT RAISE(ABORT,'Immutable research history'); END")


def _error(e):return DataError('STORE_DATABASE','database',type(e).__name__+': '+str(e))


class AnalysisStore:
    def __init__(self,path):self.path=Path(path).resolve()

    @classmethod
    def create(cls,path):
        """Explicit exclusive initialization; never adopt an existing file."""
        p=Path(path).resolve()
        try:
            fd=os.open(p,os.O_CREAT|os.O_EXCL|os.O_WRONLY,0o600);os.close(fd)
        except FileExistsError:raise DataError('STORE_EXISTS','database','Initialization will not replace an existing path') from None
        except OSError as e:raise _error(e) from None
        conn=None
        try:
            conn=sqlite3.connect(str(p),isolation_level=None);conn.execute('PRAGMA foreign_keys=ON');conn.execute('PRAGMA synchronous=FULL')
            conn.execute('BEGIN IMMEDIATE')
            for sql in DDL:conn.execute(sql)
            conn.execute(f'PRAGMA application_id={APP_ID}');conn.execute(f'PRAGMA user_version={DB_VERSION}');conn.execute('COMMIT')
        except sqlite3.Error as e:
            if conn is not None and conn.in_transaction:conn.rollback()
            raise _error(e) from None
        finally:
            if conn is not None:conn.close()
        return cls(p)

    @contextmanager
    def _db(self,write=False):
        conn=None
        try:
            conn=sqlite3.connect(self.path.as_uri()+('?mode=rw' if write else '?mode=ro'),uri=True,isolation_level=None,timeout=3)
            conn.row_factory=sqlite3.Row;conn.execute('PRAGMA foreign_keys=ON')
            if conn.execute('PRAGMA application_id').fetchone()[0]!=APP_ID or conn.execute('PRAGMA user_version').fetchone()[0]!=DB_VERSION:
                raise DataError('STORE_VERSION','database','Unrecognized database identity or schema version; no automatic migration')
            if write:conn.execute('PRAGMA synchronous=FULL');conn.execute('BEGIN IMMEDIATE')
            else:conn.execute('BEGIN')
            yield conn
            conn.commit()
        except sqlite3.Error as e:
            if conn is not None and conn.in_transaction:conn.rollback()
            raise _error(e) from None
        except BaseException:
            if conn is not None and conn.in_transaction:conn.rollback()
            raise
        finally:
            if conn is not None:conn.close()

    def _put(self,db,kind,value):
        payload=canonical(value);fp=fingerprint(value);oid=kind+':'+fp
        db.execute('INSERT OR IGNORE INTO objects VALUES(?,?,?,?)',(oid,kind,fp,payload))
        if db.execute('SELECT payload FROM objects WHERE object_id=?',(oid,)).fetchone()[0]!=payload:
            raise DataError('STORE_HASH_CONFLICT','object','Stored content differs at the same identity')
        return oid

    def _object(self,db,oid,kind):
        row=db.execute('SELECT * FROM objects WHERE object_id=?',(oid,)).fetchone()
        if row is None:raise DataError('STORE_INTEGRITY','object','Referenced object is missing')
        try:value=json.loads(row['payload']);canonical(value)
        except (ValueError,TypeError):raise DataError('STORE_INTEGRITY','object','Stored JSON is invalid') from None
        fp=fingerprint(value)
        if row['kind']!=kind or row['fingerprint']!=fp or oid!=kind+':'+fp:
            raise DataError('STORE_INTEGRITY','object','Stored payload fingerprint or kind differs')
        return value

    @staticmethod
    def _indexes(analysis_id,result):
        return [(analysis_id,s['as_of'],s['structure_snapshot_id'],s['daily_ma_snapshot_id'],s['snapshot_id']) for s in result['aligned_snapshots']]

    def save(self,request,result,evidence,*,reason):
        rules=validate_bundle(request,result,evidence)
        if not isinstance(reason,str) or not reason.strip():raise DataError('STORE_REASON','reason','A change/import reason is required')
        aid=result['analysis_id'];record_id=fingerprint(dict(analysis_id=aid,evidence_fingerprint=fingerprint(evidence)))
        with self._db(write=True) as db:
            old=db.execute('SELECT * FROM analyses WHERE analysis_id=?',(aid,)).fetchone()
            if old is not None and old['result_id']!='result:'+fingerprint(result):
                raise DataError('STORE_RESULT_CONFLICT','analysis_id','Same computation identity produced different content; old result retained')
            ids={k:self._put(db,k,v) for k,v in [('request',request),('evidence',evidence),('rules',rules),('result',result)]}
            values=(aid,request['code'],request['exchange'],request['price_mode'],ids['request'],ids['result'],ids['rules'])
            if old is None:
                db.execute('INSERT INTO analyses VALUES(?,?,?,?,?,?,?)',values)
                db.executemany('INSERT INTO snapshots VALUES(?,?,?,?,?)',self._indexes(aid,result))
            else:
                if tuple(old)!=values:raise DataError('STORE_INTEGRITY','analysis','Existing run metadata differs')
                indexes=[tuple(r) for r in db.execute('SELECT * FROM snapshots WHERE analysis_id=? ORDER BY as_of',(aid,))]
                if indexes!=self._indexes(aid,result):raise DataError('STORE_INTEGRITY','snapshots','Stored snapshot index differs')
            existing=db.execute('SELECT record_id FROM records WHERE record_id=?',(record_id,)).fetchone()
            if existing is None:
                db.execute('INSERT INTO records VALUES(?,?,?,?,?)',(record_id,aid,ids['evidence'],datetime.now(timezone.utc).isoformat(),reason))
            status='EXISTING' if existing else 'CREATED'
        return dict(schema_version=SCHEMA,status=status,record_id=record_id,analysis_id=aid,
                    request_fingerprint=fingerprint(request),result_fingerprint=fingerprint(result),evidence_fingerprint=fingerprint(evidence),
                    action_qualification='NOT_EVALUATED')

    def load(self,record_id):
        with self._db() as db:
            rec=db.execute('SELECT * FROM records WHERE record_id=?',(record_id,)).fetchone()
            if rec is None:raise DataError('STORE_NOT_FOUND','record_id','Saved record not found')
            run=db.execute('SELECT * FROM analyses WHERE analysis_id=?',(rec['analysis_id'],)).fetchone()
            if run is None:raise DataError('STORE_INTEGRITY','analysis','Referenced run missing')
            q=self._object(db,run['request_id'],'request');r=self._object(db,run['result_id'],'result')
            e=self._object(db,rec['evidence_id'],'evidence');rules=self._object(db,run['rules_id'],'rules')
            expected=validate_bundle(q,r,e)
            if rules!=expected or r['analysis_id']!=run['analysis_id'] or (q['code'],q['exchange'],q['price_mode'])!=(run['code'],run['exchange'],run['price_mode']):
                raise DataError('STORE_INTEGRITY','analysis','Saved run identity or rules differ')
            if fingerprint(dict(analysis_id=run['analysis_id'],evidence_fingerprint=fingerprint(e)))!=record_id:
                raise DataError('STORE_INTEGRITY','record','Evidence association differs')
            indexes=[tuple(row) for row in db.execute('SELECT * FROM snapshots WHERE analysis_id=? ORDER BY as_of',(run['analysis_id'],))]
            if indexes!=self._indexes(run['analysis_id'],r):raise DataError('STORE_INTEGRITY','snapshots','Saved snapshot index differs')
            return dict(schema_version=SCHEMA,record_id=record_id,analysis_id=run['analysis_id'],created_at_utc=rec['created_at_utc'],
                        reason=rec['reason'],request=q,result=r,evidence=e,rules=rules,action_qualification='NOT_EVALUATED')

    def snapshot(self,record_id,as_of):
        iso_date(as_of,'as_of');saved=self.load(record_id)
        dates=[s['as_of'] for s in saved['result']['aligned_snapshots']]
        if as_of not in dates:raise DataError('STORE_NOT_FOUND','as_of','Exact saved date required; no nearest-date substitution')
        i=dates.index(as_of);r=saved['result']
        return dict(schema_version=SCHEMA,record_id=record_id,analysis_id=saved['analysis_id'],as_of=as_of,
                    aligned=r['aligned_snapshots'][i],structure=r['components']['structure']['snapshots'][i],
                    daily_ma=r['components']['daily_ma']['snapshots'][i],evidence_coverage=saved['evidence']['coverage_status'],
                    corporate_action_coverage=r['shared_input']['corporate_action_coverage'],action_qualification='NOT_EVALUATED')

    def list_records(self,code=None):
        with self._db() as db:
            sql='SELECT r.record_id,r.analysis_id,a.code,a.exchange,a.price_mode,r.created_at_utc,r.reason FROM records r JOIN analyses a USING(analysis_id)'
            args=()
            if code is not None:sql+=' WHERE a.code=?';args=(code,)
            return [dict(row) for row in db.execute(sql+' ORDER BY r.created_at_utc,r.record_id',args)]

    def recover(self):
        """Open an existing store read/write so SQLite can roll back a hot
        journal left by a terminated writer. Never create/replace/migrate it.
        Call at worker startup before read-only queries after an interruption.
        """
        with self._db(write=True) as db:
            integrity=[r[0] for r in db.execute('PRAGMA quick_check')]
            if integrity!=['ok'] or list(db.execute('PRAGMA foreign_key_check')):
                raise DataError('STORE_INTEGRITY','database','Recovery could not establish SQLite consistency')
        return dict(schema_version=SCHEMA,status='VERIFIED_READABLE',action_qualification='NOT_EVALUATED')

    def stats(self):
        with self._db() as db:
            integrity=[r[0] for r in db.execute('PRAGMA quick_check')]
            fk=list(db.execute('PRAGMA foreign_key_check'))
            if integrity!=['ok'] or fk:raise DataError('STORE_INTEGRITY','database','SQLite integrity or foreign-key check failed')
            return dict(schema_version=SCHEMA,sqlite_integrity='ok',**{t:db.execute('SELECT count(*) FROM '+t).fetchone()[0] for t in ['objects','analyses','records','snapshots']})
