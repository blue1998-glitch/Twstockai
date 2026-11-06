"""Only the five predeclared rejection inputs, normal and preset contexts."""
import argparse
from .prepare import ROOT,load,save
from .reproduce import regression,controls,preset,probe


def main():
    p=argparse.ArgumentParser();p.add_argument('stage',choices=('before','after'));stage=p.parse_args().stage;rows=[]
    for spec in load(ROOT/'regression-specs.json'):
        args=regression(spec['name'])
        for c in (controls()[0],dict(name='preset',context=preset())):
            value,record=probe(args,c['context']);record['actual']=value
            record['expected_rejection']=bool(record['error'] and record['error']['type']=='ValueError' and spec['error'] in record['error']['detail'])
            save(ROOT/stage/'regressions'/spec['name']/c['name']/'actual.json',record)
            rows.append(dict(case=spec['name'],context=c['name'],error=record['error'],
                expected_rejection=record['expected_rejection'],input_unchanged=record['input_unchanged'],caller_context_unchanged=record['caller_context_unchanged']))
            print(spec['name'],c['name'],record['error'],record['expected_rejection'],flush=True)
    save(ROOT/stage/'regressions/summary.json',rows)


if __name__=='__main__':main()
