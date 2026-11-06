"""Corpus integrity/qualification checks; no prices, signals, model or UI dependency."""
import json, re, hashlib, argparse
from pathlib import Path

def errors(corpus):
    out=[]; cases=corpus.get('cases',[])
    ids=[c['case_id'] for c in cases]; hashes=[c['original_sha256'] for c in cases]
    if len(ids)!=len(set(ids)): out.append('DUPLICATE_CASE_ID')
    if len(hashes)!=len(set(hashes)): out.append('EXACT_DUPLICATE_NOT_MERGED')
    sources=[s for c in cases for s in c['sources']]
    if len({s['id'] for s in sources})!=len(sources): out.append('SOURCE_ASSIGNED_TWICE')
    if len(sources)!=corpus['counts']['source_files']: out.append('SOURCE_COUNT_MISMATCH')
    if sum(s['bytes'] for s in sources)!=corpus['counts']['source_bytes']: out.append('SOURCE_SIZE_MISMATCH')
    if len(cases)!=corpus['counts']['byte_unique_images']: out.append('CASE_COUNT_MISMATCH')
    for c in cases:
        for s in c['sources']:
            if s['sha256']!=c['original_sha256']: out.append('SOURCE_SHA_MISMATCH:'+c['case_id'])
            if not re.fullmatch(r'[a-f0-9]{64}',s['sha256']): out.append('INVALID_SHA:'+c['case_id'])
            if not s['url'].startswith('https://drive.google.com/file/d/'+s['id']+'/'): out.append('SOURCE_URL_ID_MISMATCH:'+c['case_id'])
        if c['training_ready'] and (not c['market_data_verified'] or not c['publication_availability_verified'] or not c['user_approved'] or c['training_blockers']): out.append('PREMATURE_TRAINING_PROMOTION:'+c['case_id'])
        if 'FUTURE_ANNOTATION_VISIBLE' in c['quality_flags'] and c['training_ready']: out.append('FUTURE_INFORMATION_LEAK:'+c['case_id'])
        if c['formal_price_bounds'] is not None and not c['user_approved']: out.append('INVENTED_FORMAL_BOUNDS:'+c['case_id'])
    # A future split must keep each subject/visual family together. None is not an assigned split.
    for field in ['split_group','visual_same_chart_group']:
        groups={}
        for c in cases:
            if c.get(field) and c.get('split_assignment'):
                groups.setdefault(c[field],set()).add(c['split_assignment'])
        if any(len(s)>1 for s in groups.values()): out.append('GROUP_SPLIT_LEAK:'+field)
    serialized=json.dumps(corpus,ensure_ascii=False)
    for forbidden in ['download_url','sig=','Signature=','/workspace/','blob.core.windows.net']:
        if forbidden in serialized: out.append('EPHEMERAL_SECRET_OR_LOCAL_PATH:'+forbidden)
    return out

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('corpus',type=Path); ap.add_argument('--report',type=Path,required=True); args=ap.parse_args()
    corpus=json.loads(args.corpus.read_text()); found=errors(corpus)
    checks=[{'name':'schema_and_source_qualification','status':'PASS' if not found else 'FAIL','errors':found}]
    parent=args.corpus.parent
    sums=json.loads((parent/'SHA256SUMS.json').read_text())
    mismatches=[n for n,v in sums.items() if hashlib.sha256((parent/n).read_bytes()).hexdigest()!=v['sha256'] or (parent/n).stat().st_size!=v['bytes']]
    checks.append({'name':'delivery_bytes_sha256','status':'PASS' if not mismatches else 'FAIL','errors':mismatches})
    import copy
    for name,change,expected in [
        ('reject_unverified_training',lambda c:c['cases'][0].update(training_ready=True),'PREMATURE_TRAINING_PROMOTION'),
        ('reject_future_input',lambda c:next(x for x in c['cases'] if 'FUTURE_ANNOTATION_VISIBLE' in x['quality_flags']).update(training_ready=True),'FUTURE_INFORMATION_LEAK'),
        ('reject_invented_formal_bounds',lambda c:c['cases'][0].update(formal_price_bounds=[1,2]),'INVENTED_FORMAL_BOUNDS'),
        ('reject_cross_split_duplicates',lambda c:[x.update(split_assignment=('train' if i==0 else 'test')) for i,x in enumerate([x for x in c['cases'] if x['visual_same_chart_group']=='VG-001'])],'GROUP_SPLIT_LEAK'),
        ('reject_ephemeral_urls',lambda c:c.update(download_url='private-token'),'EPHEMERAL_SECRET_OR_LOCAL_PATH'),
        ('reject_duplicate_ids',lambda c:c['cases'][1].update(case_id=c['cases'][0]['case_id']),'DUPLICATE_CASE_ID')]:
        modified=copy.deepcopy(corpus); change(modified); caught=errors(modified)
        checks.append({'name':name,'status':'PASS' if any(expected in x for x in caught) else 'FAIL'})
    status='PASS' if all(x['status']=='PASS' for x in checks) else 'FAIL'
    report={'status':status,'checks':checks,'source_files':corpus['counts']['source_files'],'unique_images':len(corpus['cases']),'scope':'新案例資料一致性/資格與六個故障注入檢查；不重新讀圖、不重跑M1產品測試','model_training':'NOT_EXECUTED','physical_android':'NOT_TESTED','strategy_validation':'NOT_VALIDATED'}
    args.report.write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n'); print(json.dumps(report,ensure_ascii=False)); return status!='PASS'
if __name__=='__main__': raise SystemExit(main())
