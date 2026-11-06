"""Deterministic no-key staging package. Does not install or enable anything."""
import hashlib,json,zipfile
from pathlib import Path

def build(root, output):
    root=Path(root);output=Path(output)
    paths=["codex/oci_bridge1/bridge.py", "codex/oci_read1/protocol.py"]
    files={p:(root/p).read_bytes() for p in paths}
    for p in ["codex/__init__.py","codex/oci_bridge1/__init__.py","codex/oci_read1/__init__.py"]:
        files[p]=b""
    files["__main__.py"]=(root/"codex/oci_read1/bundle_main.py").read_bytes()
    files["stage.json"]=(root/"codex/oci_read1/stage.json").read_bytes()
    manifest={"schema":"oci-read1-keyless-stage/0.1","files":[
        {"path":p,"bytes":len(raw),"sha256":hashlib.sha256(raw).hexdigest()}
        for p,raw in sorted(files.items())]}
    files["MANIFEST.json"]=(json.dumps(manifest,sort_keys=True,indent=2)+"\n").encode()
    with zipfile.ZipFile(output,"w",compression=zipfile.ZIP_DEFLATED,compresslevel=9) as z:
        for p,raw in sorted(files.items()):
            info=zipfile.ZipInfo(p,date_time=(2026,11,5,0,0,0));info.compress_type=zipfile.ZIP_DEFLATED
            info.external_attr=0o100600<<16;z.writestr(info,raw,compresslevel=9)
    return manifest
if __name__=="__main__":
    import sys
    build(Path(__file__).resolve().parents[2],Path(sys.argv[1]))
