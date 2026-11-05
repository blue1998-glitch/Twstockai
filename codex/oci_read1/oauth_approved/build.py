"""Reproducible OAuth runner package, no secrets or live account config."""
import hashlib,json,zipfile
from pathlib import Path
from codex.oci_read1.oauth_approved.native import render_workflow

def build(root,target):
    root=Path(root);target=Path(target)
    paths=["codex/oci_ctrl1/handler.py","codex/oci_bridge1/bridge.py","codex/oci_read1/protocol.py"]+["codex/oci_read1/oauth_approved/"+x for x in ["native.py","federation.py","entry.py"]]
    files={x:(root/x).read_bytes() for x in paths}
    for x in ["codex/__init__.py","codex/oci_ctrl1/__init__.py","codex/oci_bridge1/__init__.py","codex/oci_read1/__init__.py","codex/oci_read1/oauth_approved/__init__.py"]:files[x]=b""
    folder=root/"codex/oci_read1/oauth_approved"
    files["__main__.py"]=b"from codex.oci_read1.oauth_approved.entry import main\nraise SystemExit(main())\n"
    files["workflow.template"]=(folder/"workflow.template").read_bytes()
    files["requirements.lock"]=(folder/"requirements.lock").read_bytes()
    manifest={"schema":"read1-oauth-pinned-package/0.2","files":[{"path":x,"bytes":len(v),"sha256":hashlib.sha256(v).hexdigest()} for x,v in sorted(files.items())]}
    files["MANIFEST.json"]=(json.dumps(manifest,indent=2,sort_keys=True)+"\n").encode()
    with zipfile.ZipFile(target,"w",compression=zipfile.ZIP_DEFLATED,compresslevel=9) as z:
        for name,value in sorted(files.items()):
            info=zipfile.ZipInfo(name,(2026,11,5,0,0,0));info.compress_type=zipfile.ZIP_DEFLATED;info.external_attr=0o100600<<16;z.writestr(info,value,compresslevel=9)
    raw=target.read_bytes()
    return manifest,render_workflow(raw)
if __name__=="__main__":
    import sys
    root=Path(__file__).resolve().parents[3]
    manifest,workflow=build(root,sys.argv[1])
    Path(sys.argv[2]).write_bytes(workflow)
