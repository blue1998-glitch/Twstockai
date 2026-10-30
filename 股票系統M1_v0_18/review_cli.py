"""Record one explicitly supplied classification review; never invent labels."""
import argparse,json,sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent/'src'))
from reviews import append_review
from contracts import DataError


def main():
    p=argparse.ArgumentParser();p.add_argument('--queue',required=True);p.add_argument('--journal',required=True)
    p.add_argument('--row',type=int,required=True);p.add_argument('--decision',choices=['ACCEPT','REJECT','UNSURE'],required=True)
    p.add_argument('--reason',required=True);p.add_argument('--reviewer',required=True);p.add_argument('--supersedes-id')
    a=p.parse_args();queue=json.loads(Path(a.queue).read_text(encoding='utf-8-sig'))
    if not isinstance(queue,list) or not 1<=a.row<=len(queue):p.error('row must resolve to a queue item (1-based)')
    try:r=append_review(a.journal,queue,target_key=queue[a.row-1]['target_key'],decision=a.decision,reason=a.reason,reviewer=a.reviewer,supersedes_id=a.supersedes_id)
    except DataError as e:print(json.dumps(e.as_dict(),ensure_ascii=False));return 2
    print(json.dumps(r,ensure_ascii=False,indent=2));return 0


if __name__=='__main__':raise SystemExit(main())
