"""Export immutable saved period bundles. No calculation, recovery or network."""
import argparse
import json
from pathlib import Path
from period_store import PeriodStore
from period_store_cli import protect_output


def render(root):
    store = PeriodStore(root)
    records = [store.load(r['analysis_id']) for r in store.list()]
    data = json.dumps(dict(schema_version='period-viewer-export/1.0', records=records),
                      ensure_ascii=False, allow_nan=False, separators=(',', ':'))
    data = data.replace('&', '\\u0026').replace('<', '\\u003c').replace('>', '\\u003e').replace('\u2028', '\\u2028').replace('\u2029', '\\u2029')
    return Path(__file__).with_name('period_viewer_template.html').read_text(encoding='utf-8').replace('@@PERIOD_DATA@@', data)


def export(root, output):
    protect_output(root, output, [Path(__file__), Path(__file__).with_name('period_viewer_template.html')])
    html = render(root)
    # Atomic text export, separate from JSON worker serialization.
    import os, tempfile
    temporary = None
    try:
        path = Path(output)
        with tempfile.NamedTemporaryFile(dir=path.parent, prefix='.period-view-', mode='w', encoding='utf-8', delete=False) as f:
            temporary = Path(f.name); f.write(html); f.flush(); os.fsync(f.fileno())
        os.replace(temporary, path)
    finally:
        if temporary is not None: temporary.unlink(missing_ok=True)
    return dict(status='EXPORTED', records=len(PeriodStore(root).list()), output=str(output))


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__); p.add_argument('--store', required=True); p.add_argument('--output', required=True)
    a = p.parse_args(); print(json.dumps(export(a.store, a.output), ensure_ascii=False))
