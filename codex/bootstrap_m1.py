#!/usr/bin/env python3
"""Prepare the verified v0.18 worktree from repository-owned v0.17 ZIPs.

Standard library only; no network, trading, engine execution or DB recovery.
Existing work is verified and never overwritten. New files stage privately.
"""
import hashlib
import argparse
import json
from pathlib import Path, PurePosixPath
import re
import stat
import sys
import tempfile
import shutil
import zipfile

sys.dont_write_bytecode = True


def sha256(path):
    digest = hashlib.sha256()
    with path.open('rb') as source:
        for block in iter(lambda: source.read(1024 * 1024), b''):
            digest.update(block)
    return digest.hexdigest()


def require(condition, message):
    if not condition:
        raise ValueError(message)


def archive_name(info):
    name = PurePosixPath(info.filename)
    require(not name.is_absolute() and '..' not in name.parts and '\\' not in info.filename, 'Unsafe archive path')
    require(not stat.S_ISLNK(info.external_attr >> 16), 'Archive symlinks are not supported')
    return name


def verify_project(root, plan):
    manifest_path = root / 'output/交付檔案指紋.json'
    require(manifest_path.is_file() and not manifest_path.is_symlink(), 'Missing or linked manifest')
    require(sha256(manifest_path) == plan['manifest_sha256'], 'Manifest differs; existing work preserved')
    manifest = json.loads(manifest_path.read_text(encoding='utf-8'))
    require(len(manifest['files']) == plan['manifest_entries'], 'Manifest entry count differs')
    for entry in manifest['files']:
        relative = PurePosixPath(entry['file'])
        require(not relative.is_absolute() and '..' not in relative.parts, 'Unsafe manifest path')
        file = root.joinpath(*relative.parts)
        require(file.is_file() and not file.is_symlink(), 'Missing or linked file: ' + entry['file'])
        require(file.resolve().is_relative_to(root.resolve()), 'File escapes project root')
        require(file.stat().st_size == entry['bytes'] and sha256(file) == entry['sha256'], 'File differs; existing work preserved: ' + entry['file'])
    # Do not remove generated caches, local notes or later user work.
    return len(manifest['files']) + 1


def hydrate_missing(stage, target):
    """Restore verified baseline assets without overwriting later development."""
    missing, differing = [], []
    for source in sorted(stage.rglob('*')):
        if not source.is_file():
            continue
        relative = source.relative_to(stage)
        destination = target / relative
        require(not destination.is_symlink(), 'Linked existing file preserved: ' + str(relative))
        require(destination.resolve().is_relative_to(target.resolve()), 'Existing path escapes project root')
        if destination.exists():
            require(destination.is_file(), 'Existing non-file preserved: ' + str(relative))
            if sha256(destination) != sha256(source):
                differing.append(str(relative))
        else:
            missing.append((source, destination))
    for source, destination in missing:
        destination.parent.mkdir(parents=True, exist_ok=True)
        # Exclusive creation also preserves files created after the preflight.
        with source.open('rb') as original, destination.open('xb') as output:
            shutil.copyfileobj(original, output)
    return dict(status='HYDRATED_PRESERVING_CHANGES', project=str(target),
                restored_files=len(missing), differing_files_preserved=differing,
                baseline_verified=True, current_tree_matches_baseline=not differing,
                action_qualification='NOT_EVALUATED')


def prepare(repository, *, hydrate=False):
    repository = Path(repository).resolve()
    resources = Path(__file__).resolve().parent
    plan = json.loads((resources / 'handoff.json').read_text(encoding='utf-8'))
    target = repository / '股票系統M1_v0_18'
    require(not target.is_symlink(), 'Existing project root is a symlink; preserved')
    existing = target.exists()
    if existing and not hydrate:
        count = verify_project(target, plan)
        return dict(status='ALREADY_PREPARED',project=str(target),verified_files=count,action_qualification='NOT_EVALUATED')
    for archive in plan['baseline_archives']:
        source = repository / archive['name']
        require(source.is_file() and sha256(source) == archive['sha256'], 'Baseline ZIP missing or changed: ' + archive['name'])
    overlay = resources / plan['overlay_archive']
    require(overlay.is_file() and sha256(overlay) == plan['overlay_sha256'], 'Update ZIP missing or changed')
    with tempfile.TemporaryDirectory(prefix='.m1-prepare-', dir=repository) as temporary:
        stage = Path(temporary) / 'project'
        stage.mkdir()
        seen = set()
        for archive in plan['baseline_archives']:
            with zipfile.ZipFile(repository / archive['name']) as source:
                require(source.testzip() is None, 'Baseline ZIP CRC failed')
                for info in source.infolist():
                    name = archive_name(info)
                    require(name.parts and name.parts[0] == '股票系統M1_v0_17', 'Unexpected baseline root')
                    if info.is_dir():
                        continue
                    relative = PurePosixPath(*name.parts[1:])
                    require(str(relative) not in seen, 'Duplicate baseline file')
                    seen.add(str(relative))
                    destination = stage.joinpath(*relative.parts)
                    destination.parent.mkdir(parents=True, exist_ok=True)
                    destination.write_bytes(source.read(info))
        require(len(seen) == 827, 'Baseline file count differs')
        applied = set()
        with zipfile.ZipFile(overlay) as source:
            require(source.testzip() is None, 'Update ZIP CRC failed')
            for info in source.infolist():
                relative = archive_name(info)
                require(not info.is_dir() and str(relative) not in applied, 'Unexpected update entry')
                applied.add(str(relative))
                destination = stage.joinpath(*relative.parts)
                destination.parent.mkdir(parents=True, exist_ok=True)
                destination.write_bytes(source.read(info))
        require(applied == set(plan['overlay_entries']), 'Update entry list differs')
        # Build the new presentation from the exact old embedded catalog.
        # No catalog() call, market requests, calculations or database reads.
        original = (stage / '日週月研究對照.html').read_text(encoding='utf-8')
        match = re.search(r'<script id="cross-data" type="application/json">(.*?)</script>', original, re.S)
        require(match is not None, 'Original saved catalog is missing')
        sys.path.insert(0, str(stage / 'src'))
        try:
            from cross_view_export import render, MOBILE_TEMPLATE
            rendered = render(json.loads(match.group(1)), template=MOBILE_TEMPLATE)
        finally:
            sys.path.pop(0)
        (stage / plan['generated_html']).write_text(rendered, encoding='utf-8')
        count = verify_project(stage, plan)
        if existing:
            return hydrate_missing(stage, target)
        require(not target.exists(), 'Target appeared during preparation; no overwrite')
        stage.rename(target)
    return dict(status='PREPARED',project=str(target),verified_files=count,action_qualification='NOT_EVALUATED')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--hydrate-missing', action='store_true',
                        help='Verify a private baseline and restore missing files only; preserve and report existing edits')
    args = parser.parse_args()
    try:
        print(json.dumps(prepare(Path(__file__).resolve().parents[1], hydrate=args.hydrate_missing), ensure_ascii=False))
        return 0
    except (OSError, ValueError, KeyError, zipfile.BadZipFile) as error:
        print(json.dumps(dict(status='PREPARATION_FAILED',detail=str(error),existing_work='PRESERVED'), ensure_ascii=False),file=sys.stderr)
        return 2


if __name__ == '__main__':
    raise SystemExit(main())
