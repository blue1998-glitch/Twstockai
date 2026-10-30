"""Freeze independent arithmetic oracles and exact, immutable source recipes first."""
from copy import deepcopy
from decimal import Decimal, localcontext
import hashlib
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parent
PROJECT=ROOT.parents[1]
BASE=ROOT.parent/'quantity_replay_20261026/cases'


def load(path):return json.loads(path.read_text())


def save(path,value):
    path.parent.mkdir(parents=True,exist_ok=True)
    with path.open('x') as f:json.dump(value,f,ensure_ascii=False,indent=2);f.write('\n')


def file_info(path):
    raw=path.read_bytes()
    return dict(path=str(path.relative_to(PROJECT)),bytes=len(raw),sha256=hashlib.sha256(raw).hexdigest())


def main():
    hand=[
        ('recovered',['1000','1100','880','990','1100'],'0.1','-0.2',3,False,'2026-01-09'),
        ('censored',['1000','1100','880','900'],'-0.1','-0.2',2,True,None),
        ('initial-fall',['1000','900','1000'],'0','-0.1',2,False,'2026-01-07'),
        ('flat',['1000','1000','1000'],'0','0',0,False,None),
        ('rising',['1000','1050','1100'],'0.1','0',0,False,None),
        ('two-episodes',['1000','800','1000','1100','825','1100'],'0.1','-0.25',2,False,'2026-01-10'),
        ('equal-high',['1000','1100','1100','990','1100'],'0.1','-0.1',2,False,'2026-01-09'),
    ]
    for name,values,growth,drawdown,duration,censored,recovery in hand:
        rows=[dict(date='2026-01-'+str(5+i).zfill(2),net_accrual_equity=v) for i,v in enumerate(values)]
        save(ROOT/'arithmetic'/name/'input.json',rows)
        save(ROOT/'arithmetic'/name/'expected.json',dict(growth=growth,maximum_drawdown=drawdown,
            maximum_duration_days=duration,recovery_censored=censored,worst_recovery_date=recovery,
            role='INDEPENDENT_HAND_ARITHMETIC_NOT_LEDGER_REPLAY'))
    normal='partial-then-independent';other='wait-then-new-review';partial='prefix-only';stopped='old-trigger-blocked'
    cases=[
        ('complete-partial-chain',normal,'NONE','EVALUATED',None),
        ('complete-settled-chain',other,'NONE','EVALUATED',None),
        ('partial-ledger',partial,'NONE','REFUSED','LEDGER_RETURN_REFUSED'),
        ('stopped-result',stopped,'NONE','REFUSED','INCOMPLETE_SAVED_RESULT'),
        ('missing-nav',normal,'MISSING_NAV','REFUSED','UNKNOWN_EQUITY'),
        ('missing-held-mark',normal,'MISSING_MARK','REFUSED','UNKNOWN_HELD_ASSET_MARK'),
        ('missing-day',normal,'MISSING_DAY','REFUSED','INCOMPLETE_CALENDAR_CURVE'),
        ('nonpositive',normal,'NONPOSITIVE','REFUSED','NONPOSITIVE_EQUITY'),
        ('changed-prefix',normal,'CHANGED_PREFIX','REFUSED','LEDGER_PREFIX_CHANGED'),
        ('changed-capital',normal,'CHANGED_CAPITAL','REFUSED','ORIGINAL_CAPITAL_CONFLICT'),
        ('missing-token',normal,'MISSING_TOKEN','REFUSED','SAVED_RESULT_UNREADABLE'),
        ('external-flow',normal,'EXTERNAL_FLOW','REFUSED','EXTERNAL_FLOW_NOT_IMPLEMENTED'),
        ('future-close',normal,'EARLY_EVALUATION','REFUSED','CLOSE_NOT_YET_AVAILABLE'),
        ('unknown-claims',normal,'UNKNOWN_CLAIMS','REFUSED','UNKNOWN_CASH_CLAIMS'),
        ('real-source',normal,'REAL_SOURCE','REFUSED','NON_SYNTHETIC_SOURCE_NOT_SUPPORTED'),
        ('intent-only',normal,'INTENT_ONLY','REFUSED','UNSUPPORTED_SAVED_RESULT'),
    ]
    sources={}
    with localcontext() as ctx:
        ctx.prec=50
        for name,src,recipe,status,reason in cases:
            path=BASE/src/'actual.json';info=file_info(path);sources[info['path']]=info
            spec=dict(schema='account-metrics-fixture-recipe/0.1',source=info,recipe=recipe,
                evaluation_at='2026-01-12T16:00:00+08:00')
            expected=dict(status=status,reason=reason)
            if name=='complete-partial-chain':
                expected.update(initial_capital='2230',terminal_accrual_equity='2225.640',recorded_fill_fee_tax='4',
                    terminal_exit_cost='9.110',terminal_net_equity='2216.530',
                    accrual_growth=str(Decimal('-4.360')/Decimal('2230')),
                    terminal_net_growth=str(Decimal('-13.470')/Decimal('2230')),
                    maximum_drawdown=str(Decimal('-4.360')/Decimal('2230')),
                    explanation='2230-4.360=2225.640; 2225.640-9.110=2216.530; recorded fee4 is already included')
            save(ROOT/'cases'/name/'input.json',spec);save(ROOT/'cases'/name/'expected.json',expected)
    originals=list(sources.values())
    for name in ['lifecycle.py','quantity_replay.py','trend_replay.py','execution.py','continuity.py']:
        originals.append(file_info(ROOT.parent/name))
    originals.append(file_info(PROJECT/'rotation_research/action_ledger.py'))
    save(ROOT/'intake.json',dict(baseline='4313799a78d3d319a12da83ad8a0f661126c54cd',
        originals=originals,arithmetic_cases=len(hand),saved_cases=len(cases),
        ordering='CONTRACT_AND_INPUT_EXPECTED_SAVED_BEFORE_PRODUCTION_IMPLEMENTATION',
        public_source_or_private_documents_fetched=False))


if __name__=='__main__':main()
