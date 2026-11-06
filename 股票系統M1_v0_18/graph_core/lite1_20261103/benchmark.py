"""One readonly original/new owner benchmark. All output remains private."""
import json,threading,subprocess,sys
from pathlib import Path
from graph_core_chart.mobile_private import make_server

def run(root,connection,out):
 root=Path(root);connection=json.loads(Path(connection).read_bytes());out=Path(out);out.mkdir(exist_ok=True)
 head=json.loads((root/'current-increment-run.json').read_bytes())
 server=make_server(head['private_preview']['path'],connection['credential_file']);thread=threading.Thread(target=server.serve_forever,daemon=True);thread.start()
 try:
  cfg=dict(auth=connection['auth'],urls=dict(original='http://127.0.0.1:'+str(server.server_port)+'/',lite=connection['url']))
  conf=out/'config-private.json';conf.write_text(json.dumps(cfg));conf.chmod(0o600)
  subprocess.run(['node',str(Path(__file__).with_name('test_perf.cjs')),str(conf),str(out/'summary.json')],check=True)
 finally:server.shutdown();server.server_close();thread.join()
if __name__=='__main__':run(*sys.argv[1:])
