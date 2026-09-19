"""Executable contract for matching and local overrides; not a desktop loader."""
from copy import deepcopy
import hashlib
import json
from pathlib import Path
from jsonschema import Draft202012Validator

ROOT = Path(__file__).resolve().parents[1]

def identify(fingerprints, evidence):
    """Name is a scan hint, never proof. Return all candidates, never first match."""
    matches, incomplete = set(), set()
    for fp in fingerprints:
        required = fp['required']
        missing, mismatch = False, False
        raw = evidence.get('report_map_hex')
        if raw is None: missing = True
        else:
            data = bytes.fromhex(raw)
            m = required['report_map']
            mismatch |= len(data) != m['length'] or hashlib.sha256(data).hexdigest() != m['sha256']
        for field in ('pnp', 'services', 'reports'):
            if field not in required: continue
            actual = evidence.get(field)
            if actual is None: missing = True
            elif field == 'pnp':
                for key, value in required[field].items():
                    if key not in actual: missing = True
                    elif actual[key] != value: mismatch = True
            elif field == 'reports':
                available = {(x['id'], x['type']) for x in actual}
                mismatch |= not all((x['id'], x['type']) in available for x in required[field])
            else: mismatch |= not set(required[field]) <= set(actual)
        if not mismatch:
            (incomplete if missing else matches).add(fp['model'])
    unresolved = incomplete - matches
    status = 'ambiguous' if len(matches) > 1 else 'incomplete' if unresolved else 'matched' if matches else 'unknown'
    return dict(status=status, matches=sorted(matches), incomplete=sorted(unresolved))

def effective(model, defaults, override, device_id):
    """Field patches, atomic action replacement, no inference from value equality."""
    schema = json.loads((ROOT / 'schemas/user-override.schema.json').read_bytes())
    Draft202012Validator(schema).validate(override)
    if override['device_id'] != device_id or override['model_id'] != model['id']:
        raise ValueError('Override belongs to a different device/model')
    buttons = {b['id'] for b in model['buttons']}
    if set(defaults['buttons']) != buttons: raise ValueError('Defaults do not cover the model')
    orphaned = set(override['buttons']) - buttons
    if orphaned: raise ValueError(f'Update conflicts with removed buttons: {sorted(orphaned)}')
    result = deepcopy(defaults['buttons'])
    semantics = {b['id']: b['semantic'] for b in model['buttons']}
    for button, patch in override['buttons'].items():
        action = patch.get('action')
        if action and action['type'] != 'none':
            is_voice = action['type'] in ('voice-preset', 'voice-shortcut')
            if is_voice != (semantics[button] == 'voice'):
                raise ValueError('Voice action assigned to an incompatible button')
        result[button].update(deepcopy(patch))
    return result

def prepare_update(old_model, new_model, defaults, override, device_id):
    """A proposed update only; the caller commits it after receiver verification."""
    if old_model['id'] != new_model['id']:
        raise ValueError('Changing model requires explicit reassignment')
    old = {b['id']: b['semantic'] for b in old_model['buttons']}
    new = {b['id']: b['semantic'] for b in new_model['buttons']}
    if any(old[b] != new[b] for b in old.keys() & new.keys()):
        raise ValueError('Button semantics changed; migration required')
    return effective(new_model, defaults, override, device_id)
