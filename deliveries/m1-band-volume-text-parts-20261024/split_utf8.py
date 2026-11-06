"""Lossless packaging only. No project imports, numeric producer or formatting."""
import argparse
import hashlib
import json
from pathlib import Path

PART_LIMIT = 256 * 1024
ORIGINAL_BYTES = 4102710
ORIGINAL_SHA256 = '03961ba8e322a4a1d2cfde52eeb4840f39b4540b2ad61fec8e55c27328621384'
SOURCE_COMMIT = 'ec51f617bf51b1ae77099efc4ecd8099d940996d'
SOURCE_PATH = 'deliveries/m1-explicit-band-volume-20261024/artifacts/band-volume.json'
sha = lambda data: hashlib.sha256(data).hexdigest()


def split(source, out):
    original = source.read_bytes()
    if len(original) != ORIGINAL_BYTES or sha(original) != ORIGINAL_SHA256:
        raise ValueError('Original bytes mismatch; preserve source and stop')
    original.decode('utf-8', errors='strict')
    # Slice bytes directly. Decode only to check boundaries, never reserialize.
    bodies = []
    start = 0
    while start < len(original):
        end = min(start + PART_LIMIT, len(original))
        while end < len(original) and original[end] & 0xC0 == 0x80:
            end -= 1
        body = original[start:end]
        body.decode('utf-8', errors='strict')
        assert body and len(body) <= PART_LIMIT <= 512 * 1024
        bodies.append((start, end, body))
        start = end
    parts_dir = out / 'parts'
    if parts_dir.exists():
        raise ValueError('Preserve existing parts; choose a new delivery directory')
    parts_dir.mkdir(parents=True)
    members = []
    for order, (start, end, body) in enumerate(bodies, 1):
        name = f'parts/band-volume.part-{order:04d}-of-{len(bodies):04d}.txt'
        with (out / name).open('xb') as stream:
            stream.write(body)
        members.append(dict(order=order, path=name, bytes=len(body), sha256=sha(body),
                            start_byte=start, end_byte_exclusive=end, strict_utf8_valid=True))
    joined = b''.join((out / row['path']).read_bytes() for row in members)
    assert len(joined) == ORIGINAL_BYTES and sha(joined) == ORIGINAL_SHA256
    assert joined == original
    source_object = json.loads(original)
    joined_object = json.loads(joined)
    assert joined_object == source_object
    manifest = dict(schema_version='lossless-utf8-text-parts/1',
                    repository='blue1998-glitch/Twstockai',
                    original=dict(commit=SOURCE_COMMIT, path=SOURCE_PATH,
                                  bytes=ORIGINAL_BYTES, sha256=ORIGINAL_SHA256,
                                  encoding='UTF-8', original_file_changed=False),
                    part_count=len(members), part_max_bytes=PART_LIMIT,
                    user_part_limit_bytes=512 * 1024, parts=members,
                    concatenation=dict(order='manifest.parts ascending numeric order',
                                       operation='Concatenate raw bytes directly; insert no separators, BOM, spaces or newlines; do not trim or normalize Unicode or line endings',
                                       each_part_is='UTF-8 text fragment, not independently parseable JSON',
                                       parse_only_after_full_join=True),
                    product_or_source_version_changed=False)
    verification = dict(status='PASS', scope='LOSSLESS_PACKAGING_ONLY_NOT_PRODUCT_TESTS',
                        original_bytes=ORIGINAL_BYTES, original_sha256=ORIGINAL_SHA256,
                        part_count=len(members), part_max_bytes=max(row['bytes'] for row in members),
                        all_parts_under_512_KiB=True, all_parts_strict_utf8=True,
                        contiguous_original_byte_ranges=True, joined_bytes=len(joined),
                        joined_sha256=sha(joined), joined_full_bytes_equal=True,
                        joined_json_parsed=True, full_json_object_equal=True,
                        input_reserialized=False, whitespace_or_newline_added=False,
                        product_tests_or_numeric_producer_run=False,
                        work_tool_acquisition_or_full_json_review_claimed=False)
    for name, obj in [('MANIFEST.json', manifest), ('packaging-verification.json', verification)]:
        with (out / name).open('xb') as stream:
            stream.write((json.dumps(obj, ensure_ascii=False, indent=2) + '\n').encode('utf-8'))
    print(json.dumps(verification, ensure_ascii=False, indent=2))
    return manifest, verification


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source', type=Path, required=True)
    parser.add_argument('--out', type=Path, required=True)
    args = parser.parse_args()
    split(args.source, args.out)
