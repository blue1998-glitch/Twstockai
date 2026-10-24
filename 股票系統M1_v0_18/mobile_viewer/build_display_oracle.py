"""Independent Decimal reference for display-only rounding of saved prices."""
import json
from decimal import Decimal, ROUND_HALF_UP, localcontext
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]


def display(value):
    if value is None:
        return None
    with localcontext() as context:
        context.prec = 120
        result = Decimal(str(value).replace(',', '')).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
        if result == 0:
            result = abs(result)
        return format(result, ',.2f')


def main():
    text = (ROOT / '日週月研究對照.html').read_text()
    data = json.loads(re.search(r'<script id="cross-data" type="application/json">(.*?)</script>', text, re.S).group(1))
    expected = json.loads((ROOT / 'cross_view/output/日週月對照實算驗收.json').read_text())
    cases = []
    for case in expected['cases']:
        daily = next(item for item in data['daily'] if item['key'] == case['daily_key'])
        period = next(item for item in data['period'] if item['key'] == case['period_key'])
        row = dict(case=case['case'], daily=[display(daily['snapshot']['daily_ma']['curves'][str(n)][-1]) for n in [5, 20, 60, 130, 260]])
        for basis in ['candidate', 'elapsed']:
            row[basis] = {tf: [display(period['record']['result']['snapshot'][tf][basis]['latest'][str(n)]['value']) for n in period['record']['result']['snapshot'][tf]['periods']] for tf in ['weekly', 'monthly']}
        cases.append(row)
    raw_examples = ['144.30', '147.275', '168.6916666666666666666666666667', '1.005', '2.675', '999.995', '0', '0.0049', '0.005', '-0.0049', '-1.005', '90071992547409931234.995', '1,234.995']
    report = dict(method='Python Decimal ROUND_HALF_UP; only saved values are read', cases=cases, examples=[dict(raw=value, display=display(value)) for value in raw_examples])
    destination = ROOT / 'mobile_viewer/output/顯示值獨立參照.json'
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(json.dumps(report, ensure_ascii=False, indent=2))
    print('18 comparison cases; 13 independent Decimal examples written')


if __name__ == '__main__':
    main()
