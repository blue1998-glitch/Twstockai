"""File-based CLI around the independent store. No engine execution."""
import argparse,json,os,sys,tempfile
from pathlib import Path
from analysis_store import AnalysisStore,SCHEMA
from contracts import DataError
from store_contracts import canonical


def _read(path):
    def pairs(items):
        d={}
        for k,v in items:
            if k in d:raise ValueError('Duplicate JSON key: '+k)
            d[k]=v
        return d
    return json.loads(Path(path).read_text(encoding='utf-8-sig'),object_pairs_hook=pairs)


def _atomic(path,value):
    p=Path(path);tmp=None
    try:
        with tempfile.NamedTemporaryFile(mode='w',encoding='utf-8',dir=p.parent,prefix=p.name+'.',suffix='.tmp',delete=False) as f:
            tmp=Path(f.name);f.write(canonical(value));f.flush();os.fsync(f.fileno())
        os.replace(tmp,p)
    finally:
        if tmp is not None and tmp.exists():tmp.unlink()


def main(argv=None):
    p=argparse.ArgumentParser(description='Independent versioned research storage')
    p.add_argument('command',choices=['init','save','load','snapshot','list','stats','recover']);p.add_argument('--db',required=True)
    p.add_argument('--request');p.add_argument('--result');p.add_argument('--evidence');p.add_argument('--reason')
    p.add_argument('--record-id');p.add_argument('--as-of');p.add_argument('--code');p.add_argument('--output')
    args=p.parse_args(argv)
    try:
        if args.output:
            out=Path(args.output)
            for path in [args.db,args.request,args.result,args.evidence]:
                if path and (out.resolve()==Path(path).resolve() or out.exists() and Path(path).exists() and out.samefile(path)):
                    raise DataError('STORE_OUTPUT_COLLISION','output','Output must not replace a database or input file')
        store=AnalysisStore(args.db)
        if args.command=='init':
            AnalysisStore.create(args.db);value=dict(schema_version=SCHEMA,status='CREATED')
        elif args.command=='save':
            if not all([args.request,args.result,args.evidence,args.reason]):raise DataError('STORE_ARGUMENT','save','Request, result, evidence and reason required')
            value=store.save(_read(args.request),_read(args.result),_read(args.evidence),reason=args.reason)
        elif args.command in ['load','snapshot']:
            if not args.record_id:raise DataError('STORE_ARGUMENT','record_id','Saved record ID required')
            if args.command=='snapshot' and not args.as_of:raise DataError('STORE_ARGUMENT','as_of','Exact saved date required')
            value=store.load(args.record_id) if args.command=='load' else store.snapshot(args.record_id,args.as_of)
        elif args.command=='recover':value=store.recover()
        elif args.command=='list':value=dict(schema_version=SCHEMA,records=store.list_records(args.code))
        else:value=store.stats()
        if args.output:
            _atomic(args.output,value)
            receipt=dict(schema_version=SCHEMA,status='OUTPUT_WRITTEN',process_id=os.getpid())
            if 'record_id' in value:receipt['record_id']=value['record_id']
        else:receipt=dict(**value,process_id=os.getpid())
        print(canonical(receipt));return 0
    except DataError as e:print(canonical(e.as_dict()));return 2
    except (OSError,ValueError,UnicodeError) as e:
        print(canonical(DataError('STORE_FILE','file',type(e).__name__+': '+str(e)).as_dict()));return 3

if __name__=='__main__':raise SystemExit(main())
