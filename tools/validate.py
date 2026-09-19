"""Validate data, reference closure, fingerprints and the downloadable index."""
import argparse
import hashlib
import json
from pathlib import Path
from jsonschema import Draft202012Validator

ROOT = Path(__file__).resolve().parents[1]

def crc32c(data):
    crc = 0xffffffff
    for b in data:
        crc ^= b
        for _ in range(8):
            crc = (crc >> 1) ^ (0x82f63b78 if crc & 1 else 0)
    return f'{crc ^ 0xffffffff:08x}'

def validate(write=False):
    schema = json.loads((ROOT / 'schemas/resource-v1.schema.json').read_text(encoding='utf8'))
    check = Draft202012Validator(schema)
    resources, index = {}, []
    for folder, kind in [('voices','voice'),('keys','keys'),('fingerprints','fingerprint'),('models','model')]:
        for path in sorted((ROOT / folder).glob('*/*.json')):
            data = path.read_bytes()
            item = json.loads(data)
            errors = list(check.iter_errors(item))
            if errors:
                raise ValueError(f'{path}: {errors[0].message}')
            assert item['kind'] == kind and path.parent.name == item['id'] and path.stem == str(item['revision']), path
            key = (kind, item['id'], item['revision'])
            assert key not in resources
            resources[key] = item
            index.append(dict(kind=kind,id=item['id'],revision=item['revision'],path=path.relative_to(ROOT).as_posix(),sha256=hashlib.sha256(data).hexdigest(),size=len(data)))
    def resolve(kind, ref):
        return resources[(kind,ref['id'],ref['revision'])]
    for (kind, _, _), item in resources.items():
        if kind == 'keys':
            inputs = [(x['report_id'],x['usage']) for x in item['entries']]
            assert len(inputs) == len(set(inputs)), 'duplicate raw input'
        if kind == 'model':
            resolve('voice',item['voice'])
            keys = resolve('keys',item['keys'])
            buttons = {x['id'] for x in item['buttons']}
            assert len(buttons) == len(item['buttons'])
            assert {x['button'] for x in keys['entries']} | {keys['voice_button']} == buttons
            layout = item['layout']['buttons']
            assert len(layout) == len(buttons) and {x['button'] for x in layout} == buttons
            for b in layout:
                assert b['width'] > 0 and b['height'] > 0 and b['radius'] >= 0
                assert 0 <= b['x'] <= 100 and 0 <= b['y'] <= 100
            for b in item['buttons']:
                k,mod,val=b['default']
                assert 0 <= k <= 5 and 0 <= mod <= 255 and 0 <= val <= 65535
                assert (b['id'] == keys['voice_button']) == (k in (3,5))
                if k == 0: assert mod == val == 0
                if k in (1,3): assert val <= 223 and (val >= 4 or (val == 0 and mod))
                if k == 2: assert mod == 0 and val < 8
                if k == 4: assert mod == 0 and val in (65534,65535)
                if k == 5: assert mod == 0 and val in (1,2)
        if kind == 'fingerprint':
            model = resolve('model',item['model'])
            assert model['keys'] == item['keys'] and model['voice'] == item['voice']
            m = item['required']['report_map']
            if item['confidence'] == 'captured-map':
                data = bytes.fromhex(m['hex'])
                assert len(data) == m['length'] and crc32c(data) == m['crc32c']
                assert hashlib.sha256(data).hexdigest() == m['sha256']
            else:
                assert item['id'] == 'xiaomi.rc003', 'new contributions require full Map'
    catalog_path = ROOT / 'catalog.json'
    catalog = json.loads(catalog_path.read_text(encoding='utf8'))
    assert catalog['format_version'] == 1 and catalog['minimum_catalog_api'] == 1
    assert len(catalog['catalog_version'].split('.')) == 3
    if write:
        catalog['resources'] = index
        catalog_path.write_text(json.dumps(catalog,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
    else:
        assert catalog['resources'] == index, 'Run python tools/validate.py --write-index'
    print(f'Validated {len(resources)} resources; catalog {catalog["catalog_version"]}')

if __name__ == '__main__':
    parser=argparse.ArgumentParser()
    parser.add_argument('--write-index',action='store_true')
    validate(parser.parse_args().write_index)
