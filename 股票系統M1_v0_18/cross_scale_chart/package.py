"""Publish a small self-contained HTML and exact-data archive."""
import argparse
import io
import json
from pathlib import Path
import zipfile
from product_candidate.build import publish_immutable
from .build import NAME,sha

ZIP_NAME='M1_v019_cross_scale_real_v01.zip'


def main():
    p=argparse.ArgumentParser();p.add_argument('--artifact-dir',required=True);p.add_argument('--output-dir',required=True);a=p.parse_args();src=Path(a.artifact_dir);out=Path(a.output_dir)
    files={n:(src/n).read_bytes() for n in [NAME,'comparison-data.json','source-acquisition.json','artifact-verification.json']}
    files['README.txt']=(Path(__file__).parent/'README.md').read_bytes()
    files['SHA256SUMS.txt']=''.join(sha(v)+'  '+k+'\n' for k,v in files.items()).encode();buffer=io.BytesIO()
    with zipfile.ZipFile(buffer,'w',compression=zipfile.ZIP_DEFLATED,compresslevel=9) as z:
        for k,v in files.items():
            info=zipfile.ZipInfo(k,date_time=(2026,10,20,0,0,0));info.compress_type=zipfile.ZIP_DEFLATED;info.external_attr=0o100644<<16;z.writestr(info,v,compresslevel=9)
    blob=buffer.getvalue()
    with zipfile.ZipFile(io.BytesIO(blob)) as z:
        if z.testzip() is not None or z.namelist()!=list(files):raise ValueError('ZIP CRC/membership')
        if any(z.read(k)!=v for k,v in files.items()):raise ValueError('ZIP extracted bytes differ')
    report=dict(status='PASS',zip=ZIP_NAME,bytes=len(blob),sha256=sha(blob),crc='PASS',exact_extracted_bytes=True,
        members={k:dict(bytes=len(v),sha256=sha(v)) for k,v in files.items()},physical_android='NOT_TESTED_NEW_BUILD')
    for k,v in {ZIP_NAME:blob,'SHA256SUMS.txt':(sha(blob)+'  '+ZIP_NAME+'\n').encode(),'PACKAGE_VERIFICATION.json':json.dumps(report,ensure_ascii=False,indent=2).encode()}.items():print(k,publish_immutable(out/k,v))
    print(len(blob),sha(blob))


if __name__=='__main__':main()
