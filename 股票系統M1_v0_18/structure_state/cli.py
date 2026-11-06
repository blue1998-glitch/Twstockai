"""Headless replay from explicit input files; never opens a market database."""
import argparse
import json
from pathlib import Path
from .core import evaluate


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--input',required=True);parser.add_argument('--scenario',required=True)
    parser.add_argument('--as-of',required=True);parser.add_argument('--output',required=True)
    args=parser.parse_args()
    result=evaluate(json.loads(Path(args.input).read_text()),json.loads(Path(args.scenario).read_text()),as_of=args.as_of)
    body=json.dumps(result,ensure_ascii=False,separators=(',',':'),allow_nan=False).encode()
    target=Path(args.output)
    if target.is_symlink():raise ValueError('Refuse symlink output')
    target.parent.mkdir(parents=True,exist_ok=True)
    try:
        with target.open('xb') as stream:stream.write(body)
    except FileExistsError:
        if target.read_bytes()!=body:raise ValueError('Existing different result preserved; use new output')
    saved=json.loads(target.read_bytes())
    if saved!=result:raise ValueError('Readback differs')
    print(json.dumps(dict(status='SAVED_READBACK_EQUAL',result_id=result['result_id'],as_of=args.as_of,latest_state=result['records'][-1]['state']),ensure_ascii=False))


if __name__=='__main__':main()
