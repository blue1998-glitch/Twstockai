"""External CLI for explicit source lookups; every invocation records actual time."""
import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
from product_candidate.build import publish_immutable
from .source_query_adapter import inspect_packet


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--input', required=True, help='Existing comparison or saved bundle JSON')
    parser.add_argument('--query', required=True, help='Explicit IDs/endpoints and saved result binding')
    parser.add_argument('--output', required=True, help='New output leaf, existing different bytes refused')
    args = parser.parse_args()
    query = json.loads(Path(args.query).read_text())
    query['selected_at'] = datetime.now(timezone.utc).isoformat()
    report = inspect_packet(json.loads(Path(args.input).read_text()), query)
    blob = (json.dumps(report, ensure_ascii=False, indent=2, allow_nan=False) + '\n').encode()
    print(publish_immutable(Path(args.output), blob), len(blob), report['report_id'])


if __name__ == '__main__':
    main()
