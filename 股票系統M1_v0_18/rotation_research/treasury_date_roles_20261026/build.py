"""IO boundary: verify frozen originals and save one immutable source observation."""
import hashlib
import json
from pathlib import Path
from datetime import datetime,timezone
from rotation_research.action_scope import verify
from rotation_research.treasury_date_roles import observe,PDF_SHA,NATIVE_SHA,PAGE_SHA,CATALOG_ID,PRIOR_ID

ROOT=Path(__file__).resolve().parents[3]
HERE=Path(__file__).resolve().parent


def verify_input(data,root=ROOT):
    """Only saved original bytes; no old producer, extraction, network or ledger."""
    raw=root/'股票系統M1_v0_18/rotation_research/source_followup_20261023/raw'
    stem='tcc-2026-q2-consolidated-report'
    pins={'.response':PDF_SHA,'.txt':NATIVE_SHA,
        '.meta.json':'814befcb1241280e17ccb215cef2a59d297dfacf86c6faea1ae95b20cff9da69',
        '.extraction.json':'024e3bab42335098f75a11606e39a4884404697246e0332bda5172091a68de93'}
    contents={}
    for suffix,pin in pins.items():
        b=(raw/(stem+suffix)).read_bytes()
        if hashlib.sha256(b).hexdigest()!=pin:raise ValueError('Original file fingerprint conflict: '+suffix)
        contents[suffix]=b
    pdf,text=contents['.response'],contents['.txt']
    meta=json.loads(contents['.meta.json']);ext=json.loads(contents['.extraction.json'])
    if not pdf.startswith(b'%PDF-') or len(pdf)!=3320224:raise ValueError('Original PDF identity conflict')
    if (ext['pdf_sha256']!=PDF_SHA or ext['text_sha256']!=NATIVE_SHA
            or ext['pages']!=124 or ext['returncode']!=0 or text.count(b'\f')!=124):
        raise ValueError('Saved extraction/pdf binding conflict')
    page=text.decode().split('\f')[57]
    if hashlib.sha256(page.encode()).hexdigest()!=PAGE_SHA or page!=data['source']['page_text']:
        raise ValueError('Selected page does not match original full native text')
    for key,value in [('official_captured_at',meta['captured_at']),('original_readback_at',meta['readback_at']),('url',meta['url'])]:
        if data['source'][key]!=value:raise ValueError('Original provenance binding conflict')
    if data['source']['pdf_path']!=str((raw/(stem+'.response')).relative_to(root)) or data['source']['native_path']!=str((raw/(stem+'.txt')).relative_to(root)):
        raise ValueError('Original source path conflict')
    catalog=json.loads((raw.parent/'catalog-v07.json').read_text());verify(catalog)
    prior=next(o for o in catalog['observations'] if o['id']==PRIOR_ID)
    if catalog['id']!=CATALOG_ID or prior!=data['prior_observation']:raise ValueError('Prior observation binding conflict')
    return dict(original_pdf_bytes=len(pdf),native_pages=124,selected_page=58,
        pdf_sha256=PDF_SHA,native_sha256=NATIVE_SHA,page_sha256=PAGE_SHA,
        current_file_verified_at=datetime.now(timezone.utc).isoformat(),
        verification='READ_EXISTING_BYTES_NO_NEW_EXTRACTION_OR_OFFICIAL_FETCH')


def save(path,value):
    with path.open('x') as f:json.dump(value,f,ensure_ascii=False,indent=2);f.write('\n')


def build():
    data=json.loads((HERE/'input.json').read_text())
    receipt=verify_input(data)
    sources=[HERE.parent/'treasury_date_roles.py',*sorted(HERE.glob('*.py'))]
    save(HERE/'source-versions.json',dict(schema='treasury-date-role-source-versions/0.1',
        source='rotation-treasury-date-roles/0.1',files={str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in sources}))
    save(HERE/'verification.json',receipt)
    result=observe(data)
    save(HERE/'actual.json',result)
    print('SAVED_ONE_SOURCE_OBSERVATION; no catalog, ledger or qualification producer called')


if __name__=='__main__':build()
