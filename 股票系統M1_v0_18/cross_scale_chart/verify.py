"""Re-read shipped HTML and verify every value against the fixed artifact."""
import argparse
import json
from pathlib import Path
from graph_core.core import fingerprint
from product_candidate.build import publish_immutable
from .build import NAME,load_fixed,make,read_new,render,sha


def verify(folder):
    folder=Path(folder);raw=(folder/NAME).read_bytes();data=read_new(folder/NAME)
    source,diagnostic=load_fixed()
    if data!=make(source,diagnostic):raise ValueError('Shipped comparison differs from fixed-source projection')
    if json.loads((folder/'comparison-data.json').read_text())!=data:raise ValueError('Separate exact JSON differs from HTML')
    if fingerprint({k:v for k,v in data.items() if k!='artifact_id'})!=data['artifact_id']:raise ValueError('Artifact fingerprint mismatch')
    if render(data).encode()!=raw:raise ValueError('Current display source does not reproduce HTML')
    for key in ['bars','macd','moving_averages','core','source','price_basis_id','source_gaps']:
        if data[key]!=source[key]:raise ValueError('Original field changed: '+key)
    return dict(status='PASS',html_sha256=sha(raw),html_bytes=len(raw),artifact_id=data['artifact_id'],
        data_fingerprint=fingerprint(data),original_core_result_id=source['core']['result_id'],
        real_ohlcv_records=len(data['bars']),all_macd_sma_and_original_core_values_equal=True,
        fixed_provenance=data['provenance'],layers=len(data['layers']),
        core_executed=False,numeric_engine_or_strategy_modified=False,physical_android='NOT_TESTED_NEW_BUILD',core_usefulness='NOT_ESTABLISHED')


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--artifact-dir',required=True);a=p.parse_args()
    report=verify(a.artifact_dir);print(publish_immutable(Path(a.artifact_dir)/'artifact-verification.json',json.dumps(report,ensure_ascii=False,indent=2).encode()))
