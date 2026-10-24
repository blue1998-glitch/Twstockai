import json,re,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]


class GeneratedMATests(unittest.TestCase):
    def test_all_compact_curves_preserve_engine_values_at_the_selected_anchor(self):
        html=(ROOT/'價格結構重播.html').read_text()
        data=json.loads(re.search(r'const DATA=(.*?);\nfor\(const rec',html,re.S).group(1))
        for code,rec in data.items():
            for mode,compact in rec['ma'].items():
                full=json.loads((ROOT/'output'/f'{code}_{mode}_MA.json').read_text())
                self.assertEqual(len(compact['refs']),len(full['snapshots']))
                for i,snapshot in enumerate(full['snapshots']):
                    self.assertEqual(snapshot['as_of'],rec['candles'][i]['date'])
                    curves=compact['bases'][compact['refs'][i]]
                    for period,values in snapshot['curves'].items():
                        self.assertEqual(curves[period][:i+1],values)
                        self.assertEqual(len(values),i+1)
                self.assertEqual(full['action_qualification'],'NOT_EVALUATED')


if __name__=='__main__':unittest.main()
