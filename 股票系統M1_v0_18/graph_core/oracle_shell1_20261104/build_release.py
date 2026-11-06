"""Deterministic stdlib zipapp; no embedded Oracle/account credentials."""
import hashlib,json,zipfile,io
from pathlib import Path
HERE=Path(__file__).parent

def build():
    code=(HERE/'shell_tool.py').read_bytes()
    readme=('Twstockai M-ORACLE-SHELL1\nPython3 + official authenticated OCI CLI in Oracle Cloud Shell.\ninspect, plan, status, stop are read-only against OCI; apply currently refuses.\nNO RESOURCE PROVISIONING BACKEND IS IMPLEMENTED IN THIS RELEASE.\nNo real Oracle qualification or Android/HTTPS deployment has been verified.\nAccount identifiers/raw OCI responses stay in a private 0700 Cloud Shell directory.\n').encode()
    contents={'__main__.py':code,'README.txt':readme}
    manifest={'schema':'oracle-shell-tool-release/0.1','version':'oracle-shell-safety/0.2','capability':'READONLY_INSPECTION_AND_REFUSAL_GATE_NOT_PROVISIONER','files':[{'path':name,'bytes':len(raw),'sha256':hashlib.sha256(raw).hexdigest()} for name,raw in sorted(contents.items())]}
    contents['MANIFEST.json']=(json.dumps(manifest,sort_keys=True,separators=(',',':'))+'\n').encode();out=io.BytesIO()
    with zipfile.ZipFile(out,'w',compression=zipfile.ZIP_DEFLATED,compresslevel=9) as z:
        for name,raw in sorted(contents.items()):
            info=zipfile.ZipInfo(name,date_time=(2026,11,4,0,0,0));info.compress_type=zipfile.ZIP_DEFLATED;info.external_attr=0o100644<<16;z.writestr(info,raw)
    raw=out.getvalue();return raw,{'bytes':len(raw),'sha256':hashlib.sha256(raw).hexdigest(),'manifest':manifest,'members':len(contents)}

if __name__=='__main__':
    raw,meta=build();import sys
    output=Path(sys.argv[1]);output.mkdir(exist_ok=False);(output/'Twstockai_ORACLE_SHELL1.pyz').write_bytes(raw);(output/'release.json').write_text(json.dumps(meta,ensure_ascii=False,indent=2)+'\n');print(json.dumps({k:v for k,v in meta.items() if k!='manifest'}))
