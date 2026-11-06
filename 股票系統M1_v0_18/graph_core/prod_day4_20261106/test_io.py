"""New wire/codec boundaries only. Synthetic cases are not market samples."""
import unittest,tempfile,json,shutil
from pathlib import Path
from unittest.mock import patch
from graph_core.prod_day4_20261106 import intake,scan_io as n
from graph_core.scan1_20261104 import engine as old
from graph_core.graph_lazy1_20261104.worker import run as original_core
from graph_core.prod_core1_20261105 import flow as f
from rotation_research.store import Journal
class IOTests(unittest.TestCase):
    def setUp(self):
        self.w=Path(tempfile.mkdtemp(prefix='io-',dir=str(intake.WORK/'tests')));(self.w/'baseline-private.json').write_bytes(f.encode(dict(free_bytes=shutil.disk_usage(self.w).free)))
    def fixture(self,source_sha="d"*64):
        stocks=[]
        for i in range(2):
            identity='TWSE:SYN'+str(i);dt='2026-11-05';fact=dict(identity=identity,code='SYN'+str(i),name='合成',market='TWSE',isin='SYNTHETIC',cfi='ESVUFR',as_of=dt,source_status='SOURCE_BAR_AVAILABLE',source_label='合成',bar=dict(date=dt,open='10.0000',high='12',low='9',close='11.2500',volume_shares_scaled='12345678901234567'),continuity='NOT_CERTIFIED_NO_HISTORY_APPENDED',source=dict(capture_id='c'*64,daily_sha256=source_sha,price_mode='RAW_CANDIDATE',volume_unit='SHARES_REPORTED',price_basis_id=identity+'-OFFICIAL-RAW-UNBRIDGED-'+dt))
            body=f.encode(fact);p=self.w/('fact'+str(i)+'.json');p.write_bytes(body);stocks.append(dict(**{k:fact[k] for k in ['identity','code','market','isin','cfi','as_of']},fact_path=str(p),fact=dict(path=p.name,bytes=len(body),sha256=f.sha(body))))
        spec=dict(version=old.VERSION,journal_encoding='MINIFIED_UTF8_V1',as_of='2026-11-05',capture_id='c'*64,daily_sources={'TWSE':source_sha},protected_code={},original_sources={},stocks=stocks);spec['id']=f.sha(f.encode(spec));intake.store.save_exact(intake.WORK,self.w/'manifest-private.json',f.encode(spec));return spec
    def test_original_journal_reader_exact_minified_values(self):
        value=dict(price='123.000000001',shares='12345678901234567',unknown=None,qualified=False)
        n.Journal(self.w/'records').save('synthetic',value);self.assertEqual(Journal(self.w/'records').read('synthetic')['value'],value);self.assertLessEqual((self.w/'records/synthetic.json').stat().st_size,4096)
    def test_checkpoint_resume_and_exact_core_result(self):
        spec=self.fixture();a=n.run(self.w,limit=1,runner=original_core);b=n.run(self.w,runner=original_core)
        self.assertEqual((a['status'],a['new_core_calls'],b['new_core_calls']),('PARTIAL',1,1))
        for s in spec['stocks']:
            v=Journal(self.w/'results').read(old.key_for(spec,s))['value'];self.assertEqual(v['result'],original_core(old.fact(spec,s))['series']['results'][0]);self.assertLessEqual(Journal(self.w/'results').path(old.key_for(spec,s)).stat().st_size,4096)
        before={str(p):p.read_bytes() for p in self.w.rglob('*') if p.is_file()};again=n.run(self.w,runner=lambda _:self.fail('NO_REPEAT'));self.assertEqual((again['new_core_calls'],again['new_records']),(0,0));self.assertEqual(before,{str(p):p.read_bytes() for p in self.w.rglob('*') if p.is_file()})
    def test_codec_descriptor_and_logical_catalogue_reader(self):
        p=self.w/'large.json';raw=f.encode(dict(rows=['合成'*1000]*50));intake.store.save_exact(intake.WORK,p,raw);self.assertFalse(p.exists());d=f.descriptor(p);self.assertEqual(f.bound(d),json.loads(raw));self.assertEqual(d['sha256'],f.sha(raw))
    def test_explicit_new_wire_required(self):
        s=self.fixture();s.pop('journal_encoding');intake.store.save_exact(intake.WORK,self.w/'different.json',f.encode(s))
        with patch.object(n,'read',return_value=s):
            with self.assertRaises(ValueError):n.run(self.w,runner=lambda _:self.fail('NO_LEGACY_REWRITE'))
    def test_minified_tamper_no_repair(self):
        s=self.fixture();n.run(self.w,runner=original_core);p=next((self.w/'results').glob('*.json'));p.write_bytes(p.read_bytes()+b' ')
        with self.assertRaises(ValueError):n.run(self.w,runner=lambda _:self.fail('NO_TAMPER_RECALC'))
    def test_capacity_before_new_write_but_zero_write_replay_allowed(self):
        p=self.w/'old';f.put(self.w,p,b'unchanged')
        with patch.object(f.shutil,'disk_usage',return_value=type('Usage',(),dict(free=f.RESERVE))()):
            f.put(self.w,p,b'unchanged')
            with self.assertRaises(OSError):f.put(self.w,self.w/'new',b'x')
        self.assertFalse((self.w/'new').exists())
    def test_saved_provider_codec_hit_and_tamper_refusal(self):
        from .source_reader import Provider
        body=('SYNTHETIC_SOURCE_'+self.w.name).encode();source=self.w/'source';intake.store.save_exact(intake.WORK,source,body);sh=f.sha(body)
        spec=self.fixture(sh);n.run(self.w,runner=original_core);stock=spec['stocks'][0];fact=f.read(stock['fact_path']);row=next(r for r in f.read(self.w/'complete-index.json')['records'] if r['identity']==stock['identity'])
        physical=intake.store.c.sidecar(source);st=physical.stat();desc=dict(path=str(physical),logical_path=str(source),logical_bytes=len(body),sha256=sh,metadata=[st.st_size,st.st_mtime_ns,st.st_ino,st.st_dev])
        action=dict(**{k:stock[k] for k in ['identity','code','market','isin','cfi','as_of']},route='action.json',request_id='synthetic',fact_route='fact.json',fact_path=stock['fact_path'],fact=stock['fact'])
        ap=self.w/'actions.json';raw=f.encode(dict(schema='private-lazy-graph-actions/0.1',actions=[action],capture_id='c'*64,protected_code={},original_daily_sources={'TWSE':desc},scan_index=f.descriptor(self.w/'complete-index.json'),scan_manifest=f.descriptor(self.w/'manifest-private.json')));intake.store.save_exact(intake.WORK,ap,raw)
        provider=Provider(ap,f.sha(raw));allowed={'fact.json':dict(path=Path(stock['fact_path']),bytes=stock['fact']['bytes'],sha256=stock['fact']['sha256'])}
        x,first=provider.get('action.json',allowed);y,second=provider.get('action.json',allowed);self.assertEqual((first,second),('MISS','HIT'));self.assertEqual(json.loads(x)['series']['results'][0],Journal(self.w/'results').read(row['key'])['value']['result']);self.assertEqual(json.loads(y)['core_calls'],0)
        root,manifest=intake.store.c.manifest(source);piece=manifest['pieces'][0];blob=intake.store.c.blob_path(root,piece['sha256']);blob.write_bytes(blob.read_bytes()+b'SYNTHETIC_TAMPER')
        with self.assertRaises(ValueError):provider.get('action.json',allowed)
if __name__=='__main__':unittest.main(verbosity=2)
