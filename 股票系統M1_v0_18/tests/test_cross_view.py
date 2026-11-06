import copy
import io
import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'src'))
from contracts import DataError,fingerprint
from cross_view import catalog,select,alignment,validate_config,SELECTION_SCHEMA
from cross_view_cli import read_config,main
from cross_view_export import protect,render,export
from analysis_store import AnalysisStore
from period_store import StoreFailure


class CrossViewTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.config=read_config(ROOT/'cross_view/sources.json');cls.data=catalog(cls.config)
        cls.view=next(v for v in cls.data['views'] if v['allow_comparison'])
        cls.d=next(d for d in cls.data['daily'] if d['key']==cls.view['daily_key'])
        cls.p=next(p for p in cls.data['period'] if p['key']==cls.view['period_key'])

    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup);self.base=Path(self.temp.name)

    def selection(self,d=None,p=None):
        d=d or self.d;p=p or self.p
        return dict(schema_version=SELECTION_SCHEMA,**self.view['scope'],daily=dict(store=d['store'],record_id=d['record_id']),period=dict(store=p['store'],analysis_id=p['analysis_id']))

    def test_all_real_pairs_preserve_exact_source_snapshots(self):
        self.assertEqual(len(self.data['daily']),18);self.assertEqual(len(self.data['period']),12)
        pairs=[v for v in self.data['views'] if v['allow_comparison']];self.assertEqual(len(pairs),18)
        for v in pairs:
            d=next(x for x in self.data['daily'] if x['key']==v['daily_key']);p=next(x for x in self.data['period'] if x['key']==v['period_key'])
            r=select(self.data,dict(schema_version=SELECTION_SCHEMA,**v['scope'],daily=dict(store=d['store'],record_id=d['record_id']),period=dict(store=p['store'],analysis_id=p['analysis_id'])))
            self.assertEqual(r['daily']['snapshot'],d['snapshot']);self.assertEqual(r['period']['record'],p['record']);self.assertEqual(r['alignment'],v)

    def test_both_historical_versions_remain_explicit(self):
        ds=[d for d in self.data['daily'] if d['code']=='1101' and d['as_of']=='2026-09-30']
        self.assertEqual({d['versions']['structure'] for d in ds},{'structure-0.2-research','structure-0.3-research'})
        self.assertEqual(len({d['record_id'] for d in ds}),2)

    def test_missing_daily_and_missing_period_are_partial_without_alignment(self):
        for field,status in [('daily','MISSING_DAILY'),('period','MISSING_PERIOD')]:
            q=self.selection();q[field]=None;r=select(self.data,q)
            self.assertEqual(r['alignment']['status'],status);self.assertFalse(r['alignment']['allow_comparison']);self.assertIsNone(r[field])

    def test_wrong_date_or_record_does_not_substitute(self):
        for key,value in [('as_of','2026-09-29'),('daily',{'store':self.d['store'],'record_id':'sha256:'+'0'*64}),('period',{'store':self.p['store'],'analysis_id':'sha256:'+'0'*64})]:
            q=self.selection();q[key]=value
            with self.subTest(key=key),self.assertRaises(DataError):select(self.data,q)

    def test_scope_mismatch_conflicts_in_both_full_and_partial_views(self):
        q=self.selection();q['code']='NOT_THIS_STOCK'
        self.assertEqual(select(self.data,q)['alignment']['status'],'CONFLICT')
        q['daily']=None;self.assertEqual(select(self.data,q)['alignment']['status'],'CONFLICT')

    def test_data_event_source_unit_anchor_and_count_mismatches_conflict(self):
        for kind in ('source','unit','raw','events','anchor','mode','date','count','coverage'):
            d=copy.deepcopy(self.d);p=copy.deepcopy(self.p)
            if kind=='source':d['source']['id']='different'
            if kind=='unit':d['source']['volume_unit']='SHARES_REPORTED' if d['source']['volume_unit']!='SHARES_REPORTED' else 'SHARES_SCALED_FROM_LOTS'
            if kind=='raw':d['source_candles'][0]['close']='1'
            if kind=='events':d['effective_actions'].append(dict(effective_date='2026-01-01',factor='0.9'))
            if kind=='anchor':d['snapshot']['structure']['adjustment_anchor']='2026-01-01'
            if kind=='mode':d['snapshot']['daily_ma']['price_mode']='other'
            if kind=='date':p['record']['result']['snapshot']['as_of']='2026-01-01'
            if kind=='count':d['snapshot']['daily_ma']['bars']+=1
            if kind=='coverage':d['snapshot']['corporate_action_coverage']='DIFFERENT'
            with self.subTest(kind=kind):
                v=alignment(d,p,self.view['scope']);self.assertEqual(v['status'],'CONFLICT');self.assertFalse(v['allow_comparison'])

    def test_snapshot_content_and_unsupported_versions_conflict(self):
        d=copy.deepcopy(self.d);d['snapshot']['daily_ma']['curves']['5'][-1]='1'
        self.assertEqual(alignment(d,self.p,self.view['scope'])['status'],'CONFLICT')
        d=copy.deepcopy(self.d);d['snapshot']['structure']['rule_version']='UNKNOWN_VERSION'
        self.assertEqual(alignment(d,self.p,self.view['scope'])['status'],'CONFLICT')

    def test_legacy_native_share_warning_is_retained_without_mutation(self):
        d=next(d for d in self.data['daily'] if d['code']=='1101' and d['versions']['structure']=='structure-0.2-research')
        p=next(p for p in self.data['period'] if p['code']==d['code'] and p['as_of']==d['as_of']);before=copy.deepcopy(d)
        v=alignment(d,p,{k:d[k] for k in ('code','exchange','price_mode','as_of')})
        self.assertTrue(v['allow_comparison']);self.assertTrue(any('誤標' in w for w in v['warnings']));self.assertEqual(before,d)

    def test_real_null_260_day_and_24_month_values_never_filled(self):
        d=next(d for d in self.data['daily'] if d['code']=='2884');p=next(p for p in self.data['period'] if p['code']==d['code'] and p['as_of']==d['as_of'])
        self.assertIsNone(d['snapshot']['daily_ma']['curves']['260'][-1]);self.assertIsNone(p['record']['result']['snapshot']['monthly']['candidate']['latest']['24']['value'])

    def test_select_returns_copies(self):
        before=fingerprint(self.d);r=select(self.data,self.selection());r['daily']['snapshot']['structure']['pivots'].clear();self.assertEqual(fingerprint(self.d),before)

    def test_bad_config_and_selection_fields_reject(self):
        c=copy.deepcopy(self.config);c['as_of_dates'].append(c['as_of_dates'][0])
        with self.assertRaises(DataError):validate_config(c)
        for q in (None,dict(self.selection(),extra=1),dict(self.selection(),schema_version='bad'),dict(self.selection(),daily=None,period=None)):
            with self.subTest(q=repr(q)[:50]),self.assertRaises(DataError):select(self.data,q)

    def test_relative_configuration_is_portable(self):
        for group in ('daily_stores','period_stores'):
            self.assertTrue(all(Path(p).is_absolute() for p in self.config[group].values()))

    def test_missing_store_never_created(self):
        c=copy.deepcopy(self.config);p=self.base/'missing.sqlite3';c['daily_stores']={'missing':str(p)}
        with self.assertRaises(DataError):catalog(c)
        self.assertFalse(p.exists())

    def test_output_protection_covers_databases_sidecars_store_and_aliases(self):
        db=Path(next(iter(self.config['daily_stores'].values())));period=Path(next(iter(self.config['period_stores'].values())))
        link=self.base/'hard.sqlite3';os.link(db,link)
        symlink=self.base/'symbol.html';symlink.symlink_to(db)
        for path in [db,Path(str(db)+'-journal'),Path(str(db)+'-wal'),Path(str(db)+'-shm'),period/'new.html',link,symlink]:
            with self.subTest(path=str(path)),self.assertRaises((StoreFailure,DataError)):protect(self.config,path)

    def test_escaped_json_cannot_escape_script_element(self):
        p=copy.deepcopy(self.data);p['source_aliases']['note']='</script><script>BAD()</script>'
        h=render(p);self.assertNotIn('</script><script>BAD()',h);self.assertIn('\\u003c/script\\u003e',h);self.assertIn("connect-src 'none'",h)

    def test_export_failure_preserves_existing_output_and_store(self):
        path=self.base/'old.html';path.write_text('previous');db=Path(next(iter(self.config['daily_stores'].values())));before=db.read_bytes()
        with patch('cross_view_export.os.replace',side_effect=OSError('export denied')),self.assertRaises(OSError):export(self.config,path)
        self.assertEqual(path.read_text(),'previous');self.assertEqual(db.read_bytes(),before)

    def test_read_export_in_fresh_process_cannot_import_engines_or_recover(self):
        code="""import sys,importlib.abc
class Block(importlib.abc.MetaPathFinder):
 def find_spec(self,fullname,*args):
  if fullname in ('structure','moving_averages','analysis_jobs','analysis_workflow','period_ma','period_jobs','period_workflow','jobs','prepare_daily'):raise RuntimeError('FORBIDDEN '+fullname)
sys.meta_path.insert(0,Block())
from analysis_store import AnalysisStore
AnalysisStore.recover=lambda *a:(_ for _ in ()).throw(RuntimeError('RECOVERY FORBIDDEN'))
from cross_view_cli import main
assert main(['--config',sys.argv[1],'--html','--output',sys.argv[2]])==0
"""
        p=subprocess.run([sys.executable,'-c',code,str(ROOT/'cross_view/sources.json'),str(self.base/'fresh.html')],env={**os.environ,'PYTHONPATH':str(ROOT/'src')},capture_output=True,text=True)
        self.assertEqual(p.returncode,0,p.stderr);self.assertTrue((self.base/'fresh.html').exists())

    def test_cli_duplicate_keys_rejected_and_no_output(self):
        config=self.base/'bad.json';config.write_text('{"schema_version":1,"schema_version":2}');out=self.base/'out.html';err=io.StringIO()
        with patch('sys.stderr',err):code=main(['--config',str(config),'--html','--output',str(out)])
        self.assertEqual(code,2);self.assertFalse(out.exists());json.loads(err.getvalue())


if __name__=='__main__':unittest.main()
