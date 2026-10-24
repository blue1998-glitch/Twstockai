import copy
import hashlib
import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'src'))
from contracts import DataError, fingerprint
from period_store import PeriodStore, StoreFailure, _publish
from period_store_cli import execute, protect_output
from period_store_contracts import canonical, validate_bundle
from period_viewer import render, export


def fixture():
    q = json.loads((ROOT/'period_analysis/requests/1101_RAW_CANDIDATE.json').read_text())
    r = json.loads((ROOT/'period_analysis/output/1101_RAW_CANDIDATE_PERIOD.json').read_text())
    return q, r


class PeriodStoreTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(); self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)/'store'; self.store = PeriodStore.create(self.root)
        self.q, self.r = fixture(); self.aid = self.r['analysis_id']

    def save(self): return self.store.save(self.q, self.r, reason='真實既有結果保存測試')
    def bytes(self): return {p.name:p.read_bytes() for p in self.root.iterdir()}

    def test_save_reopen_complete_read_and_dedup(self):
        self.assertEqual(self.save()['status'], 'SAVED'); before=self.bytes()
        self.assertEqual(self.save()['status'], 'DUPLICATE')
        record = PeriodStore(self.root).load(self.aid)
        self.assertEqual(record['request'], self.q); self.assertEqual(record['result'], self.r)
        self.assertEqual(before,self.bytes()); self.assertEqual(len(self.store.list()),1)

    def test_reason_is_immutable_content(self):
        self.save(); before=self.bytes()
        with self.assertRaisesRegex(StoreFailure,'different immutable content'):
            self.store.save(self.q,self.r,reason='不能修改既有理由')
        self.assertEqual(before,self.bytes())

    def test_same_analysis_different_numerics_conflicts_without_recomputing(self):
        self.save(); before=self.bytes(); r=copy.deepcopy(self.r)
        r['snapshot']['weekly']['candidate']['curves']['4'][-1]='999'
        r['snapshot']['weekly']['candidate']['latest']['4']['value']='999'
        # Hash links do not certify the math. The established immutable identity must reject this.
        validate_bundle(self.q,r)
        with self.assertRaises(StoreFailure):self.store.save(self.q,r,reason='真實既有結果保存測試')
        self.assertEqual(before,self.bytes())

    def test_bad_request_fingerprint_and_future_link_rejected(self):
        q=copy.deepcopy(self.q);q['candles'][-1]['close']='100'
        with self.assertRaises(DataError):self.store.save(q,self.r,reason='bad')
        self.assertEqual(len(self.store.list()),0)

    def test_unknown_version_rejected(self):
        r=copy.deepcopy(self.r);r['snapshot']['rule_version']='period-sma-9.9'
        with self.assertRaises(DataError):self.store.save(self.q,r,reason='bad')

    def test_shape_alignment_and_null_reason_rejected(self):
        for change in ('alignment','null','latest','anchor','qualification','calendar'):
            r=copy.deepcopy(self.r);s=r['snapshot']
            if change=='alignment':s['monthly']['candidate']['curves']['24'].pop()
            if change=='null':s['monthly']['candidate']['curves']['24'][-1]='0'
            if change=='latest':s['monthly']['candidate']['latest']['3']['value']='1'
            if change=='anchor':s['adjustment_anchor']='2026-09-29'
            if change=='qualification':r['action_qualification']='APPROVED'
            if change=='calendar':s['calendar_context']['coverage_end']='2026-09-29'
            with self.subTest(change=change),self.assertRaises(DataError):validate_bundle(self.q,r)

    def test_corruption_and_duplicate_json_keys_fail_closed(self):
        self.save();p=self.root/(self.aid[7:]+'.json');old=p.read_text();p.write_text(old.replace('真實既有結果保存測試','遭改寫'))
        with self.assertRaises(DataError):self.store.load(self.aid)
        p.write_text('{"schema_version":1,"schema_version":2}')
        with self.assertRaises(DataError):self.store.list()

    def test_unrecognized_header_and_invalid_entries_fail(self):
        (self.root/'STORE.json').write_text('{}')
        with self.assertRaises(DataError):PeriodStore(self.root)
        (self.root/'STORE.json').unlink()
        with self.assertRaises(StoreFailure):PeriodStore.create(self.root)

    def test_precommit_io_error_is_not_saved(self):
        with patch('period_store.os.link',side_effect=OSError('disk error')):
            with self.assertRaises(StoreFailure) as e:self.save()
        self.assertEqual(e.exception.commit_status,'NOT_SAVED');self.assertEqual(len(self.store.list()),0)

    def test_postcommit_fsync_error_is_unknown_and_readable(self):
        with patch('period_store._sync_dir',side_effect=OSError('fsync error')):
            with self.assertRaises(StoreFailure) as e:self.save()
        self.assertEqual(e.exception.commit_status,'UNKNOWN');self.assertEqual(e.exception.analysis_id,self.aid)
        self.assertEqual(self.store.load(self.aid)['result'],self.r)
        self.assertEqual(self.save()['status'],'DUPLICATE')

    def test_concurrent_identical_writers_commit_once(self):
        code="""import json,sys;from pathlib import Path;from period_store import PeriodStore
q=json.loads(Path(sys.argv[2]).read_text());r=json.loads(Path(sys.argv[3]).read_text())
print(json.dumps(PeriodStore(sys.argv[1]).save(q,r,reason='same')))
"""
        args=[sys.executable,'-c',code,str(self.root),str(ROOT/'period_analysis/requests/1101_RAW_CANDIDATE.json'),str(ROOT/'period_analysis/output/1101_RAW_CANDIDATE_PERIOD.json')]
        env={**os.environ,'PYTHONPATH':str(ROOT/'src')}
        ps=[subprocess.Popen(args,stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True,env=env) for _ in range(6)]
        statuses=[]
        for p in ps:
            out,err=p.communicate(timeout=30);self.assertEqual(p.returncode,0,err);statuses.append(json.loads(out)['status'])
        self.assertEqual(statuses.count('SAVED'),1);self.assertEqual(statuses.count('DUPLICATE'),5);self.assertEqual(len(self.store.list()),1)

    def test_concurrent_conflicting_writers_keep_one_complete_record(self):
        code="""import json,sys;from pathlib import Path;from period_store import PeriodStore,StoreFailure
q=json.loads(Path(sys.argv[2]).read_text());r=json.loads(Path(sys.argv[3]).read_text())
try:print(json.dumps(PeriodStore(sys.argv[1]).save(q,r,reason=sys.argv[4])))
except StoreFailure as e:print(json.dumps(e.as_dict()))
"""
        env={**os.environ,'PYTHONPATH':str(ROOT/'src')};args=[sys.executable,'-c',code,str(self.root),str(ROOT/'period_analysis/requests/1101_RAW_CANDIDATE.json'),str(ROOT/'period_analysis/output/1101_RAW_CANDIDATE_PERIOD.json')]
        ps=[subprocess.Popen(args+[str(i)],stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True,env=env) for i in range(4)]
        results=[]
        for p in ps:
            out,err=p.communicate(timeout=30);self.assertEqual(p.returncode,0,err);results.append(json.loads(out))
        self.assertEqual(sum(x['status']=='SAVED' for x in results),1)
        self.assertEqual(sum(x.get('code')=='PERIOD_STORE_CONFLICT' for x in results),3)
        self.assertEqual(len(self.store.list()),1)

    def test_killed_writer_before_commit_retains_pending_without_phantom_record(self):
        payload=Path(self.temp.name)/'payload.json';payload.write_text(json.dumps({'q':self.q,'r':self.r}))
        code="""import json,os,sys;from pathlib import Path;import period_store
p=json.loads(Path(sys.argv[2]).read_text());period_store.os.link=lambda *a:os._exit(71)
period_store.PeriodStore(sys.argv[1]).save(p['q'],p['r'],reason='killed')
"""
        p=subprocess.run([sys.executable,'-c',code,str(self.root),str(payload)],env={**os.environ,'PYTHONPATH':str(ROOT/'src')},capture_output=True)
        self.assertEqual(p.returncode,71);before=self.bytes();diag=self.store.diagnostics()
        self.assertEqual(diag['committed_records'],0);self.assertEqual(len(diag['pending_files']),1);self.assertEqual(before,self.bytes())
        self.save();self.assertEqual(self.store.diagnostics()['committed_records'],1);self.assertEqual(len(self.store.diagnostics()['pending_files']),1)

    def test_killed_writer_after_commit_can_be_read_without_recovery(self):
        payload=Path(self.temp.name)/'payload.json';payload.write_text(json.dumps({'q':self.q,'r':self.r}))
        code="""import json,os,sys;from pathlib import Path;import period_store
p=json.loads(Path(sys.argv[2]).read_text());period_store._sync_dir=lambda *a:os._exit(72)
period_store.PeriodStore(sys.argv[1]).save(p['q'],p['r'],reason='killed-after-link')
"""
        p=subprocess.run([sys.executable,'-c',code,str(self.root),str(payload)],env={**os.environ,'PYTHONPATH':str(ROOT/'src')},capture_output=True)
        self.assertEqual(p.returncode,72);self.assertEqual(self.store.load(self.aid)['result'],self.r)
        self.assertEqual(len(self.store.diagnostics()['pending_files']),1)

    def test_lookup_has_no_latest_fallback(self):
        self.save();f={k:self.q[k] for k in ('code','exchange','price_mode','as_of')}
        self.assertEqual(len(self.store.lookup(**f)),1);f['as_of']='2026-09-29';self.assertEqual(self.store.lookup(**f),[])
        del f['as_of']
        with self.assertRaises(DataError):self.store.lookup(**f)

    def test_read_export_without_importing_any_engine_and_without_writes(self):
        self.save();before=self.bytes();code="""import sys,importlib.abc
class Block(importlib.abc.MetaPathFinder):
 def find_spec(self,fullname,*args):
  if fullname in ('period_ma','period_jobs','structure','daily_ma','jobs','analysis_jobs','analysis_store'):raise RuntimeError('ENGINE IMPORT '+fullname)
sys.meta_path.insert(0,Block())
from period_store import PeriodStore
from period_viewer import render
s=PeriodStore(sys.argv[1]);assert len(s.list())==1;assert s.load(s.list()[0]['analysis_id']);assert '<html' in render(sys.argv[1])
"""
        p=subprocess.run([sys.executable,'-c',code,str(self.root)],env={**os.environ,'PYTHONPATH':str(ROOT/'src')},capture_output=True,text=True)
        self.assertEqual(p.returncode,0,p.stderr);self.assertEqual(before,self.bytes())

    def test_output_aliases_and_store_paths_are_protected(self):
        self.save();record=self.root/(self.aid[7:]+'.json')
        for path in (record,self.root/'new.json',self.root):
            with self.assertRaises(StoreFailure):protect_output(self.root,path)
        hard=Path(self.temp.name)/'hard.json';os.link(record,hard)
        with self.assertRaises(StoreFailure):export(self.root,hard)
        symlink=Path(self.temp.name)/'link.json';symlink.symlink_to(record)
        with self.assertRaises(StoreFailure):export(self.root,symlink)
        with self.assertRaises(DataError):self.store.load('../../escape')

    def test_response_export_failure_reports_committed_then_readback(self):
        cmd=Path(self.temp.name)/'import.json';cmd.write_text(json.dumps(dict(schema_version='period-store-command/1.0',operation='IMPORT',request=self.q,result=self.r,reason='worker')))
        p=subprocess.run([sys.executable,str(ROOT/'src/period_store_cli.py'),'--store',str(self.root),'--input',str(cmd),'--output',str(Path(self.temp.name)/'missing/receipt.json')],capture_output=True,text=True)
        self.assertEqual(p.returncode,3,p.stderr);err=json.loads(p.stderr);self.assertEqual(err['commit_status'],'COMMITTED');self.assertEqual(err['analysis_id'],self.aid)
        self.assertEqual(self.store.load(self.aid)['result'],self.r)

    def test_json_types_and_duplicate_keys_fail_closed(self):
        for x in (float('nan'),(1,2),{1:'key'},'\ud800'):
            with self.subTest(x=repr(x)),self.assertRaises(DataError):canonical(x)

    def test_export_escapes_script_in_source_and_is_read_only(self):
        q=copy.deepcopy(self.q);q['source']['note']='</script><script>BAD()</script>'
        r=copy.deepcopy(self.r);r['source']=q['source'];r['request_fingerprint']=fingerprint(q)
        r['analysis_id']=fingerprint(dict(request=fingerprint(q),rule_version=r['snapshot']['rule_version'],adapter=r['adapter_version'],snapshot=r['snapshot']['snapshot_id']))
        self.store.save(q,r,reason='escape');before=self.bytes();html=render(self.root)
        self.assertNotIn('</script><script>BAD()',html);self.assertIn('\\u003c/script\\u003e',html);self.assertIn("connect-src 'none'",html);self.assertEqual(before,self.bytes())


if __name__=='__main__':unittest.main()
