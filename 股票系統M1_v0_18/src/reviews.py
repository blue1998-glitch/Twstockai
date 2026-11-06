"""Append-only classification-review journal. Never changes numeric results."""
import json
import os
from datetime import datetime,timezone
from pathlib import Path
from uuid import uuid4
from contracts import DataError, fingerprint


def review_queue(result):
    run_id=fingerprint({k:result[k] for k in ['code','price_mode','rule_version','schema_version','parameters_fingerprint','data_fingerprint','events_fingerprint']})
    queue=[]
    for e in result['event_ledger']:
        if e['type']=='PIVOT_RULE_CONFIRMED_CANDIDATE':subject=e['pivot'];kind='PIVOT';dt=subject['confirmed_at'];price=subject['price']
        elif e['type']=='ZONE_CREATED_CANDIDATE':subject=e['zone'];kind='ZONE';dt=subject['created_at'];price=subject['center']
        else:continue
        key=fingerprint(dict(run_id=run_id,subject_type=kind,subject_id=subject['id']))
        queue.append(dict(target_key=key,run_id=run_id,code=result['code'],price_mode=result['price_mode'],
                          rule_version=result['rule_version'],parameters_fingerprint=result['parameters_fingerprint'],
                          subject_type=kind,subject_id=subject['id'],profile=subject['profile'],as_of=dt,
                          occurred_at=subject.get('occurred_at',''),price_at_creation=price,
                          review_status='UNREVIEWED',decision='',reason='',reviewer=''))
    return queue


def read_journal(path):
    if not Path(path).exists():return []
    result=[];ids=set()
    for n,line in enumerate(Path(path).read_text(encoding='utf-8').splitlines(),1):
        if not line.strip():raise DataError('MALFORMED_REVIEW_JOURNAL',f'line[{n}]','Blank journal line')
        try:r=json.loads(line)
        except ValueError:raise DataError('MALFORMED_REVIEW_JOURNAL',f'line[{n}]','Invalid JSON') from None
        if not isinstance(r,dict) or not all(k in r for k in ['review_id','target_key','decision','reason','reviewer','recorded_at','supersedes_id']):
            raise DataError('MALFORMED_REVIEW_JOURNAL',f'line[{n}]','Required fields missing')
        if r['review_id'] in ids:raise DataError('DUPLICATE_REVIEW_ID',f'line[{n}]','Review ID repeated')
        if r['decision'] not in ('ACCEPT','REJECT','UNSURE'):raise DataError('INVALID_REVIEW_DECISION',f'line[{n}]','Unsupported decision')
        prior=[x for x in result if x['target_key']==r['target_key']]
        expected=prior[-1]['review_id'] if prior else None
        if r['supersedes_id']!=expected:raise DataError('BROKEN_REVIEW_CHAIN',f'line[{n}]','Revision does not supersede current review')
        ids.add(r['review_id']);result.append(r)
    return result


def append_review(path,queue,*,target_key,decision,reason,reviewer,supersedes_id=None):
    if decision not in ('ACCEPT','REJECT','UNSURE'):raise DataError('INVALID_REVIEW_DECISION','decision','Use ACCEPT, REJECT or UNSURE')
    if not isinstance(reason,str) or not reason.strip() or not isinstance(reviewer,str) or not reviewer.strip():
        raise DataError('MISSING_REVIEW_CONTEXT','review','Reason and reviewer are required')
    targets=[x for x in queue if x['target_key']==target_key]
    if len(targets)!=1:raise DataError('UNKNOWN_REVIEW_TARGET','target_key','Target must resolve uniquely in this run')
    path=Path(path);path.parent.mkdir(parents=True,exist_ok=True);lock=Path(str(path)+'.lock')
    try:fd=os.open(lock,os.O_CREAT|os.O_EXCL|os.O_WRONLY,0o600)
    except FileExistsError:raise DataError('REVIEW_JOURNAL_BUSY','journal','Another writer holds the journal lock') from None
    try:
        os.close(fd);prior=read_journal(path);previous=[x for x in prior if x['target_key']==target_key]
        expected=previous[-1]['review_id'] if previous else None
        if supersedes_id!=expected:raise DataError('REVIEW_REVISION_CONFLICT','supersedes_id','Must reference the latest review; no overwrite allowed')
        record=dict(schema_version='classification-review/1.0',review_id=str(uuid4()),target_key=target_key,
                    run_id=targets[0]['run_id'],subject_id=targets[0]['subject_id'],decision=decision,
                    reason=reason.strip(),reviewer=reviewer.strip(),supersedes_id=supersedes_id,
                    recorded_at=datetime.now(timezone.utc).isoformat(),
                    meaning='Classification opinion only; not trading validation')
        with path.open('a',encoding='utf-8') as f:f.write(json.dumps(record,ensure_ascii=False,sort_keys=True)+'\n');f.flush();os.fsync(f.fileno())
        return record
    finally:lock.unlink(missing_ok=True)


def review_status(queue,journal):
    keys={q['target_key'] for q in queue};current={}
    for r in journal:
        if r['target_key'] in keys:current[r['target_key']]=r
    return dict(total_targets=len(keys),reviewed=len(current),unreviewed=len(keys)-len(current),
                decisions={d:sum(x['decision']==d for x in current.values()) for d in ('ACCEPT','REJECT','UNSURE')},
                classification_accuracy='NOT_ESTIMABLE',trading_value='NOT_VALIDATED')
