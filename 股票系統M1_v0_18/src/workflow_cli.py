"""One file request handles calculation, persistence and saved-state queries."""
import argparse,os
from pathlib import Path
from analysis_workflow import execute_workflow,WorkflowError,SCHEMA
from contracts import DataError
from store_cli import _read,_atomic
from store_contracts import canonical


def main(argv=None):
    parser=argparse.ArgumentParser(description='Headless analysis workflow')
    parser.add_argument('--input',required=True);parser.add_argument('--db',required=True)
    parser.add_argument('--output');parser.add_argument('--create',action='store_true')
    args=parser.parse_args(argv);response=None
    try:
        if args.output:
            out=Path(args.output)
            protected=[args.input,args.db,*[args.db+s for s in ['-journal','-wal','-shm']]]
            for path in protected:
                target=Path(path)
                if out.resolve()==target.resolve() or out.exists() and target.exists() and out.samefile(target):
                    raise WorkflowError('WORKFLOW_OUTPUT_COLLISION','output','Output must not replace input, database or recovery sidecars',stage='FILE_PREFLIGHT')
        try:request=_read(args.input)
        except (OSError,ValueError,UnicodeError) as e:
            raise WorkflowError('WORKFLOW_INPUT_FILE','input',type(e).__name__,stage='FILE_PREFLIGHT') from None
        response=execute_workflow(request,args.db,create_if_missing=args.create)
        if args.output:
            try:_atomic(args.output,response)
            except (OSError,ValueError,UnicodeError) as e:
                raise WorkflowError('WORKFLOW_OUTPUT_FILE','output',type(e).__name__,stage='EXPORT',
                                    commit_status=response.get('commit_status','NOT_SAVED'),record_id=response.get('record_id'),
                                    identities={k:response[k] for k in ['request_fingerprint','evidence_fingerprint'] if k in response}) from None
            receipt=dict(schema_version=SCHEMA,status='OUTPUT_WRITTEN',operation=request['operation'],process_id=os.getpid())
            for k in ['record_id','analysis_id','store_status','commit_status']: 
                if k in response:receipt[k]=response[k]
        else:receipt=dict(**response,process_id=os.getpid())
        print(canonical(receipt));return 0
    except WorkflowError as e:
        print(canonical(dict(**e.as_dict(),process_id=os.getpid())));return 3 if e.stage in ['EXPORT','FILE_PREFLIGHT'] else 2
    except DataError as e:
        print(canonical(dict(**e.as_dict(),process_id=os.getpid())));return 2

if __name__=='__main__':raise SystemExit(main())
