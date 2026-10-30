"""Validate generated v0.2 outputs and regenerate the UNREVIEWED queue."""
import csv,json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parent
sys.path.insert(0,str(ROOT/'src'))
from contracts import fingerprint,validate_output
from reviews import review_queue,review_status,read_journal


def main():
    baseline=json.loads((ROOT/'data/v0_1_功能參照指紋.json').read_text());keys=['as_of','pivots','zones','pending','daily_events','structure_status']
    comparison=[];queue=[]
    for code in ['8069','6488']:
        for mode in ['RAW_CANDIDATE','ADJUSTED_CANDIDATE']:
            result=json.loads((ROOT/'output'/f'{code}_{mode}.json').read_text());validate_output(result)
            digest=fingerprint([{k:s[k] for k in keys} for s in result['snapshots']])
            ok=digest==baseline[f'{code}_{mode}']['functional_hash']
            comparison.append(dict(case=f'{code}_{mode}',baseline='structure-0.1-research',current=result['rule_version'],functional_outputs='IDENTICAL' if ok else 'DIFFERENT'))
            if not ok:raise ValueError('Unexpected candidate-rule output change: '+f'{code}_{mode}')
            queue+=review_queue(result)
    out=ROOT/'output'
    (out/'v0_1與v0_2回歸比對.json').write_text(json.dumps(comparison,ensure_ascii=False,indent=2))
    (out/'覆核清單.json').write_text(json.dumps(queue,ensure_ascii=False,indent=2))
    with (out/'覆核清單.csv').open('w',encoding='utf-8-sig',newline='') as f:
        w=csv.DictWriter(f,fieldnames=list(queue[0]));w.writeheader();w.writerows(queue)
    journal=read_journal(out/'人工覆核.jsonl')
    (out/'分類覆核狀態.json').write_text(json.dumps(review_status(queue,journal),ensure_ascii=False,indent=2))
    print('4 baseline comparisons identical;',len(queue),'review targets. Existing journal preserved.')


if __name__=='__main__':main()
