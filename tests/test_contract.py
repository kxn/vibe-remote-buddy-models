import copy
import sys
import unittest
from pathlib import Path
from jsonschema import ValidationError
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'tools'))
from validate import load, validate_resources
from resolve import effective, identify, prepare_update

class Contract(unittest.TestCase):
    def setUp(self):
        self.resources, _ = load()
        self.model = self.resources['model', 'xiaomi.rc003']
        self.defaults = self.resources['defaults', self.model['defaults']]
        self.override = dict(format_version=1, device_id='local-device-a', model_id='xiaomi.rc003', buttons={})

    def test_navigation_defaults(self):
        expected = {'back': dict(type='keyboard', modifiers=0, usage=42),
                    'home': dict(type='app', command='task-view'),
                    'menu': dict(type='app', command='window-picker')}
        for (kind, model_id), model in self.resources.items():
            if kind != 'model': continue
            defaults = self.resources['defaults', model['defaults']]['buttons']
            for button in model['buttons']:
                if button['semantic'] in expected:
                    self.assertEqual(defaults[button['id']]['action'], expected[button['semantic']],
                                     (model_id, button['id']))

    def test_all_resources(self):
        validate_resources(self.resources)

    def test_shared_protocol_but_independent_appearance_and_keymaps(self):
        a, b = [self.resources['model', x] for x in ('unicom.sample-28', 'cmcc.sample-28')]
        self.assertNotEqual(a['layout'], b['layout'])
        self.assertEqual(a['protocol'], b['protocol'])
        self.assertNotEqual(a['keymap'], b['keymap'])

    def test_captured_voice_inputs_survive_migration(self):
        for keymap in ('xiaomi.rc003', 'xiaomi.legacy-32ba'):
            entries = self.resources['keymap', keymap]['entries']
            self.assertIn(dict(button='b02', report_id=1, usage=62), entries)
        for keymap in ('unicom.sample-28', 'cmcc.sample-28'):
            keys = self.resources['keymap', keymap]
            self.assertEqual(len(keys['entries']), 27)
            self.assertFalse(any(e['button'] == keys['voice_button'] for e in keys['entries']))

    def test_none_is_explicit_override(self):
        self.override['buttons']['b03'] = {'action': {'type': 'none'}}
        actual = effective(self.model, self.defaults, self.override, 'local-device-a')
        self.assertEqual(actual['b03']['action'], {'type': 'none'})
        self.assertEqual(actual['b03']['label'], self.defaults['buttons']['b03']['label'])
        self.assertNotEqual(self.defaults['buttons']['b03']['action'], {'type': 'none'})

    def test_equal_value_remains_override_after_update(self):
        original = copy.deepcopy(self.defaults['buttons']['b03']['action'])
        self.override['buttons']['b03'] = {'action': original}
        updated = copy.deepcopy(self.defaults)
        updated['buttons']['b03']['action'] = {'type': 'none'}
        updated['buttons']['b03']['label'] = '新默认名称'
        actual = effective(self.model, updated, self.override, 'local-device-a')
        self.assertEqual(actual['b03']['action'], original)
        self.assertEqual(actual['b03']['label'], '新默认名称')
        del self.override['buttons']['b03']
        self.assertEqual(effective(self.model, updated, self.override, 'local-device-a')['b03']['action'], {'type': 'none'})

    def test_action_is_replaced_not_deep_merged(self):
        self.override['buttons']['b03'] = {'action': {'type': 'app', 'command': 'window-picker'}}
        self.assertEqual(effective(self.model, self.defaults, self.override, 'local-device-a')['b03']['action'], self.override['buttons']['b03']['action'])

    def test_wrong_device_or_model_rejected(self):
        with self.assertRaises(ValueError): effective(self.model, self.defaults, self.override, 'local-device-b')
        self.override['model_id'] = 'cmcc.sample-28'
        with self.assertRaises(ValueError): effective(self.model, self.defaults, self.override, 'local-device-a')

    def test_orphaned_override_blocks_update(self):
        self.override['buttons']['removed-button'] = {'action': {'type': 'none'}}
        with self.assertRaises(ValueError): effective(self.model, self.defaults, self.override, 'local-device-a')

    def test_changed_semantics_blocks_update_even_without_override(self):
        updated = copy.deepcopy(self.model)
        updated['buttons'][0]['semantic'] = 'another-function'
        with self.assertRaises(ValueError):
            prepare_update(self.model, updated, self.defaults, self.override, 'local-device-a')

    def test_no_hardware_override(self):
        self.override['buttons']['b03'] = {'usage': 123}
        with self.assertRaises(ValidationError): effective(self.model, self.defaults, self.override, 'local-device-a')

    def evidence(self, fp):
        r = copy.deepcopy(fp['required'])
        r['report_map_hex'] = r.pop('report_map')['hex']
        return r

    def test_actual_fingerprints_preserve_indistinguishable_variants(self):
        fps = [r for (k, _), r in self.resources.items() if k == 'fingerprint']
        for fp in fps:
            result = identify(fps, self.evidence(fp))
            if fp['model'] in ('remote.muawdc1x', 'remote.mubbvfjx'):
                self.assertEqual(result['status'], 'ambiguous')
                self.assertEqual(result['matches'], ['remote.muawdc1x', 'remote.mubbvfjx'])
            else:
                self.assertEqual(result['status'], 'matched')
                self.assertEqual(result['matches'], [fp['model']])

    def test_names_do_not_identify_or_reject(self):
        fp = self.resources['fingerprint', 'xiaomi.rc003']
        self.assertEqual(identify([fp], {'name': '小米蓝牙语音遥控器'})['status'], 'incomplete')
        evidence = self.evidence(fp); evidence['name'] = 'A different advertisement name'
        self.assertEqual(identify([fp], evidence)['status'], 'matched')

    def test_ambiguous_and_missing_evidence_not_first_match(self):
        a = self.resources['fingerprint', 'xiaomi.rc003']; b = copy.deepcopy(a)
        b['model'] = 'different-layout'
        self.assertEqual(identify([a, b], self.evidence(a))['status'], 'ambiguous')
        b['required']['pnp'] = {'source': 1, 'vendor': 1, 'product': 1}
        self.assertEqual(identify([a, b], self.evidence(a))['status'], 'incomplete')

    def test_multiple_fingerprints_for_same_model_are_not_ambiguous(self):
        a = self.resources['fingerprint', 'xiaomi.rc003']
        self.assertEqual(identify([a, copy.deepcopy(a)], self.evidence(a))['status'], 'matched')

if __name__ == '__main__': unittest.main()
