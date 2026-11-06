"""Small deterministic diagnostic delivery, preserving old deliveries."""
import argparse
import hashlib
import io
import json
from pathlib import Path
import zipfile
from product_candidate.build import publish_immutable
from .build import NAME

ZIP_NAME='M1_v019_graph_diagnostics_v01.zip'


def main():
    p=argparse.ArgumentParser();p.add_argument('--artifact-dir',required=True);p.add_argument('--output-dir',required=True);a=p.parse_args()
    folder=Path(a.artifact_dir);out=Path(a.output_dir)
    files={NAME:(folder/NAME).read_bytes(),'README.txt':(Path(__file__).parent/'README.md').read_bytes()}
    for name in ['diagnostics-1101-latest.json','diagnostics-2884-latest.json','diagnostics-6488-latest.json','diagnostics-8069-latest.json','review-diagnostics.json']:
        files[name]=(folder/name).read_bytes()
    files['SHA256SUMS.txt']=''.join(hashlib.sha256(v).hexdigest()+'  '+k+'\n' for k,v in files.items()).encode()
    buffer=io.BytesIO()
    with zipfile.ZipFile(buffer,'w',compression=zipfile.ZIP_DEFLATED,compresslevel=9) as z:
        for name,value in files.items():
            info=zipfile.ZipInfo(name,date_time=(2026,10,19,0,0,0));info.compress_type=zipfile.ZIP_DEFLATED;info.external_attr=0o100644<<16
            z.writestr(info,value,compresslevel=9)
    blob=buffer.getvalue()
    with zipfile.ZipFile(io.BytesIO(blob)) as z:
        if z.testzip() is not None or z.namelist()!=list(files):raise ValueError('ZIP CRC/members')
        for k,v in files.items():
            if z.read(k)!=v:raise ValueError('ZIP extracted bytes')
    digest=hashlib.sha256(blob).hexdigest()
    report=dict(status='PASS',zip=ZIP_NAME,bytes=len(blob),sha256=digest,crc='PASS',exact_extracted_bytes=True,
        members={k:dict(bytes=len(v),sha256=hashlib.sha256(v).hexdigest()) for k,v in files.items()},android='NOT_TESTED_NEW_BUILD')
    for k,v in {ZIP_NAME:blob,'SHA256SUMS.txt':(digest+'  '+ZIP_NAME+'\n').encode(),'PACKAGE_VERIFICATION.json':json.dumps(report,ensure_ascii=False,indent=2).encode()}.items(): print(k,publish_immutable(out/k,v))
    print(len(blob),digest)


if __name__=='__main__':main()
