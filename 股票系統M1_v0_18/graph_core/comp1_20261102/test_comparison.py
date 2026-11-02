from pathlib import Path
from copy import deepcopy
import tempfile,unittest
from graph_core.comp1_20261102.build_demo import fixture
from graph_core.market_daily import Journal
from graph_core.stock_comparison import project
from graph_core_chart.comparison_export import BOX_FIELDS
from graph_core.core import fingerprint

class ComparisonTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup);self.root=Path(self.tmp.name);_,self.b=fixture(self.root)
    def load(self,code):
        s=next(s for s in self.b['stocks'] if s['code']==code);return s,Journal(self.root/'results').read(s['result_key'])['value']
    def test_exact_saved_fields_all_candidates_and_no_mutation(self):
        s,v=self.load('A');before=deepcopy(v);x=project(v,s,{'id':v['result']['context']['source_id']});r=v['result']
        self.assertEqual(x['anchor'],r['anchor']);self.assertEqual(x['anchor_volume'],r['anchor_volume']);self.assertEqual(x['pending_extrema'],r['pending_extrema'])
        self.assertEqual([b['id'] for b in x['boxes']],[b['id'] for b in r['boxes']])
        for a,b in zip(x['boxes'],r['boxes']):
            for k in BOX_FIELDS:self.assertEqual(a[k],b[k])
        self.assertEqual(v,before);self.assertIsNone(x['unvalidated']['strength_score']);self.assertFalse(x['policy_authorized'])
    def test_wrong_identity_cutoff_prefix_and_source_state_refuse(self):
        s,v=self.load('A')
        for field,value in [('code','WRONG'),('status','DATA_QUALITY_REFUSED'),('as_of','2026-10-30')]:
            bad=dict(s);bad[field]=value
            with self.assertRaises(ValueError):project(v,bad,{})
        with self.assertRaises(ValueError):project(v,s,{'id':'WRONG_SOURCE'})
        promoted=deepcopy(v);promoted['result']['comparison']['primary_pressure_id']='UNAUTHORIZED';promoted['result']['result_id']=fingerprint({k:t for k,t in promoted['result'].items() if k!='result_id'})
        with self.assertRaises(ValueError):project(promoted,s,{'id':promoted['result']['context']['source_id']})
        bad=deepcopy(v);bad['input']['bars'][0]['close']='999'
        with self.assertRaises(ValueError):project(bad,s,{})
    def test_latest_and_nearest_reuse_preserves_mc2_rules(self):
        from decimal import Decimal
        from graph_core_chart.comparison_export import reference_summary
        s,v=self.load('A');r=v['result'];latest,nearest,ties=reference_summary(r)
        for scale in r['parameters']['reversals']:
            for kind in ['HIGH','LOW']:
                pool=[p for p in r['pivots'] if p['scale']==scale and p['kind']==kind];day=max((p['confirmed_at'] for p in pool),default=None);self.assertEqual(latest[scale][kind],[p for p in pool if p['confirmed_at']==day])
        pool=[b for b in r['boxes'] if b['usable_at_anchor'] and b['anchor_relation']=='BELOW'];n=min((Decimal(b['pressure_distance_fraction']) for b in pool),default=None);self.assertEqual(nearest,n);self.assertEqual(ties,[b['id'] for b in pool if Decimal(b['pressure_distance_fraction'])==n])
    def test_mixed_date_and_short_preserve_individual_evidence(self):
        a,v=self.load('DATE');x=project(v,a,{'id':v['result']['context']['source_id']});self.assertNotEqual(x['as_of'],self.b['as_of']);self.assertEqual(x['source_end'],x['as_of'])
        s,v=self.load('SHORT');x=project(v,s,{'id':v['result']['context']['source_id']});self.assertEqual(x['records'],1);self.assertEqual(x['status'],'INSUFFICIENT_HISTORY');self.assertEqual(x['current_events'],[])
if __name__=='__main__':unittest.main()
