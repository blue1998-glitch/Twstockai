"""Synthetic presentation tests over existing owner catalogue. No real data."""
import unittest,tempfile,json,re
from pathlib import Path
from graph_core.lite1_20261103.test_links import LinkedAssets
from graph_core_chart.mobile_private import batch_index
from rotation_research import artifact_codec as c
class DatePage(unittest.TestCase):
 setUp=LinkedAssets.setUp
 freeze=LinkedAssets.freeze
 def catalogue(self,page):
  raw=page.read_bytes();p=self.base/'catalogue.json';p.write_text(json.dumps(dict(schema='private-saved-batches/0.1',batches=[dict(path=str(page),bytes=len(raw),sha256=c.sha(raw),as_of='2020-01-02',run_id='INTERNAL_SYNTHETIC_RUN')])));return p
 def test_lite_page_hides_internal_id_but_keeps_original_validated_route(self):
  _,allowed,summary,_=batch_index(self.catalogue(self.page),linked_roots=[self.root]);raw=allowed['batches']['raw'].decode();self.assertIn('選擇資料日期',raw);self.assertIn('2020-01-02｜股票研究',raw);self.assertNotIn('INTERNAL_SYNTHETIC_RUN',raw);self.assertIn(summary['default_page'],raw);self.assertTrue(summary['default_page'].startswith('batch-'))
 def test_non_lite_catalogue_keeps_existing_presentation(self):
  self.page.write_text('<script id="market-state" type="application/json">'+json.dumps(dict(summary=dict(as_of='2020-01-02'),stocks=[]))+'</script>');_,allowed,summary,_=batch_index(self.catalogue(self.page));raw=allowed['batches']['raw'].decode();self.assertIn('私人已保存批次',raw);self.assertIn('INTERNAL_SYNTHETIC_RUN',raw);self.assertIsNone(summary['default_page'])
if __name__=='__main__':unittest.main()
