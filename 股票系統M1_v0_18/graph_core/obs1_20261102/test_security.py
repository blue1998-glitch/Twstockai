"""New synthetic radar page through unchanged private allowlisted service."""
import hashlib,json,secrets,tempfile,threading,unittest
from pathlib import Path
from urllib.request import Request,urlopen
from urllib.error import HTTPError
from base64 import b64encode
from graph_core_chart.mobile_private import create_auth,make_server
from graph_core.obs1_20261102.build_demo import fixture
from graph_core.market_preview import build

class RadarSecurityTests(unittest.TestCase):
    def test_new_radar_html_and_shards_keep_owner_and_whitelist_boundary(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td);key,_=fixture(root);preview=build(root,key);password=secrets.token_urlsafe(24);auth=root/'auth.json';create_auth(auth,'owner',password)
            server=make_server(preview['path'],auth);worker=threading.Thread(target=server.serve_forever,daemon=True);worker.start()
            try:
                origin='http://127.0.0.1:'+str(server.server_port);target=origin+'/'+Path(preview['path']).name
                with self.assertRaises(HTTPError) as error:urlopen(target)
                self.assertEqual(error.exception.code,401)
                token='Basic '+b64encode(('owner:'+password).encode()).decode()
                with urlopen(Request(target,headers={'Authorization':token})) as response:
                    raw=response.read();self.assertEqual(hashlib.sha256(raw).hexdigest(),preview['sha256']);self.assertIn('no-store',response.headers['Cache-Control']);self.assertIn('sha256-',response.headers['Content-Security-Policy'])
                with self.assertRaises(HTTPError) as error:urlopen(Request(origin+'/auth.json',headers={'Authorization':token}))
                self.assertIn(error.exception.code,[403,404])
            finally:server.shutdown();server.server_close();worker.join();auth.unlink()
if __name__=='__main__':unittest.main()
