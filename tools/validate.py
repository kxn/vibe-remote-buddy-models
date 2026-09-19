"""Validate the current catalog snapshot. Historical versions live in Git."""
import argparse
import hashlib
import json
import re
import subprocess
from pathlib import Path
from jsonschema import Draft202012Validator

ROOT = Path(__file__).resolve().parents[1]
FOLDERS = dict(protocols='protocol', keymaps='keymap', layouts='layout', defaults='defaults', models='model', fingerprints='fingerprint')

def crc32c(data):
    crc = 0xffffffff
    for b in data:
        crc ^= b
        for _ in range(8):
            crc = (crc >> 1) ^ (0x82f63b78 if crc & 1 else 0)
    return f'{crc ^ 0xffffffff:08x}'

def load(root=ROOT):
    check = Draft202012Validator(json.loads((root / 'schemas/resource.schema.json').read_bytes()))
    resources, index = {}, []
    for folder, kind in FOLDERS.items():
        for path in sorted((root / folder).rglob('*.json')):
            data = path.read_bytes()
            assert not path.is_symlink() and b'\r' not in data, path
            assert re.fullmatch(r'[a-z0-9]+(?:-[a-z0-9]+)*', path.stem), path
            item = json.loads(data)
            check.validate(item)
            assert item['kind'] == kind, path
            key = kind, item['id']
            assert key not in resources, f'Duplicate current resource: {key}'
            resources[key] = item
            index.append(dict(kind=kind, id=item['id'], revision=item['revision'], path=path.relative_to(root).as_posix(), sha256=hashlib.sha256(data).hexdigest(), size=len(data)))
    return resources, index

def validate_resources(resources):
    for (kind, _), item in resources.items():
        if kind == 'keymap':
            inputs = [(x['report_id'], x['usage']) for x in item['entries']]
            assert len(inputs) == len(set(inputs)), 'Duplicate raw input'
        if kind == 'fingerprint':
            assert ('model', item['model']) in resources
            m = item['required']['report_map']
            data = bytes.fromhex(m['hex'])
            assert len(data) == m['length'] and crc32c(data) == m['crc32c']
            assert hashlib.sha256(data).hexdigest() == m['sha256']
        if kind != 'model': continue
        for field in ('protocol', 'keymap', 'layout', 'defaults'):
            assert (field, item[field]) in resources, f'Missing {field}: {item[field]}'
        keys = resources['keymap', item['keymap']]
        defaults = resources['defaults', item['defaults']]['buttons']
        geometry = resources['layout', item['layout']]['geometry']
        buttons = {b['id'] for b in item['buttons']}
        assert len(buttons) == len(item['buttons'])
        assert {x['button'] for x in keys['entries']} | {keys['voice_button']} == buttons
        assert set(defaults) == buttons
        assert len(geometry['buttons']) == len(buttons)
        assert {b['button'] for b in geometry['buttons']} == buttons
        for b in geometry['buttons']:
            assert b['width'] > 0 and b['height'] > 0 and b['radius'] >= 0
            assert 0 <= b['x'] - b['width']/2 < b['x'] + b['width']/2 <= 100
            assert 0 <= b['y'] - b['height']/2 < b['y'] + b['height']/2 <= 100
        for button, entry in defaults.items():
            action = entry['action']
            assert (button == keys['voice_button']) == (action['type'] in ('voice-shortcut', 'voice-preset'))
            if action['type'] in ('keyboard', 'voice-shortcut'):
                assert action['usage'] >= 4 or (action['usage'] == 0 and action['modifiers'])

def check_revisions(base, resources):
    files = subprocess.check_output(['git', 'ls-tree', '-r', '--name-only', base], cwd=ROOT, text=True).splitlines()
    old = {}
    for path in files:
        if path.split('/')[0] in FOLDERS and path.endswith('.json'):
            item = json.loads(subprocess.check_output(['git', 'show', f'{base}:{path}'], cwd=ROOT))
            if item.get('format_version') == 2: old[item['kind'], item['id']] = item
    for key, item in old.items():
        assert key in resources, f'Removing {key} needs an explicit migration change'
        current = resources[key]
        if current != item:
            assert current['revision'] > item['revision'], f'Increment revision: {key}'

def validate(write=False, base=None):
    resources, index = load()
    validate_resources(resources)
    if base: check_revisions(base, resources)
    path = ROOT / 'catalog.json'
    catalog = json.loads(path.read_bytes())
    assert catalog['format_version'] == 2 and catalog['minimum_catalog_api'] == 2
    assert re.fullmatch(r'\d+\.\d+\.\d+', catalog['catalog_version'])
    if write:
        catalog['resources'] = index
        path.write_bytes((json.dumps(catalog, ensure_ascii=False, indent=2) + '\n').encode())
    else:
        assert catalog['resources'] == index, 'Run python tools/validate.py --write-index'
    print(f'Validated {len(resources)} current resources; catalog {catalog["catalog_version"]}')

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--write-index', action='store_true')
    parser.add_argument('--base')
    args = parser.parse_args()
    validate(args.write_index, args.base)
