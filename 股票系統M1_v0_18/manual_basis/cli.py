"""Explicit LOOKUP or SAVE; no UI, no stock-engine calculation."""
import argparse,json
from pathlib import Path
from .core import resolve
from .store import ChoiceJournal

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('action',choices=['LOOKUP','SAVE','READ']);p.add_argument('--catalogue');p.add_argument('--request');p.add_argument('--journal');p.add_argument('--selection-id');a=p.parse_args()
    if a.action=='READ':
        if not a.journal or not a.selection_id:p.error('READ requires journal and selection-id')
        value=ChoiceJournal(a.journal).read(a.selection_id)
    else:
        if not a.catalogue or not a.request:p.error('LOOKUP/SAVE require catalogue and request')
        value=resolve(json.loads(Path(a.catalogue).read_text()),json.loads(Path(a.request).read_text()))
        if a.action=='SAVE':
            if not a.journal:p.error('SAVE requires journal')
            value=ChoiceJournal(a.journal).save(value)
    print(json.dumps(value,ensure_ascii=False,indent=2))

if __name__=='__main__':main()
