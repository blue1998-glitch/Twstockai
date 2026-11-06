"""Offline export of the independent read-only cross-timeframe catalog."""
from pathlib import Path
from contracts import DataError
from store_contracts import canonical
from period_store_cli import protect_output
from cross_view import SCHEMA, catalog, validate_config, require
import os
import tempfile

TEMPLATE=Path(__file__).with_name('cross_view_template.html')


def render(payload):
    require(payload.get('schema_version')==SCHEMA,'catalog.schema_version')
    text=TEMPLATE.read_text(encoding='utf-8');require(text.count('@@CROSS_DATA@@')==1,'template')
    encoded=canonical(payload)
    for char,escaped in [('&','\\u0026'),('<','\\u003c'),('>','\\u003e'),('\u2028','\\u2028'),('\u2029','\\u2029')]:encoded=encoded.replace(char,escaped)
    return text.replace('@@CROSS_DATA@@',encoded)


def protect(config,output,inputs=()):
    validate_config(config)
    files=list(map(Path,inputs))+[TEMPLATE,Path(__file__)]
    for p in config['daily_stores'].values():
        files.extend(Path(str(p)+suffix) for suffix in ('','-journal','-wal','-shm'))
    for root in config['period_stores'].values():protect_output(root,output,files)


def write_text(output,text):
    path=Path(output);temp=None
    try:
        with tempfile.NamedTemporaryFile(dir=path.parent,prefix='.cross-export-',mode='w',encoding='utf-8',delete=False) as f:
            temp=Path(f.name);f.write(text);f.flush();os.fsync(f.fileno())
        os.replace(temp,path)
    finally:
        if temp is not None:temp.unlink(missing_ok=True)


def export(config,output,inputs=()):
    protect(config,output,inputs)
    payload=catalog(config);write_text(output,render(payload))
    return dict(status='EXPORTED',daily_snapshots=len(payload['daily']),period_records=len(payload['period']),
                aligned_views=sum(v['allow_comparison'] for v in payload['views']),database_access='READ_ONLY_NO_RECOVERY',action_qualification='NOT_EVALUATED')
