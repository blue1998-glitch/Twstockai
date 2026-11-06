"""Only the new READ view, old JSON compatibility and refusal boundaries."""
from contextlib import redirect_stdout
from copy import deepcopy
import io
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from capital_research.research_choice_view import render_text
from capital_research.research_choice_cli import main
from .helpers import ROOT, OLD, load


class TextTests(unittest.TestCase):
    def test_frozen_READ_results_and_exact_legacy_JSON(self):
        for spec in load(ROOT / 'input-expected.json'):
            key = spec['key']; expected = spec['expected']
            text = load(ROOT / 'actual' / key / 'text-receipt.json')
            old_json = load(ROOT / 'actual' / key / 'json-receipt.json')
            self.assertEqual(text['exit_code'], expected['exit_code'])
            self.assertEqual(old_json['exit_code'], expected['exit_code'])
            self.assertFalse(text['stderr']); self.assertFalse(old_json['stderr'])
            for fragment in expected['contains']:
                self.assertIn(fragment, text['stdout'])
            receipt = load(OLD / 'receipts' / (key + '-read.json'))
            self.assertEqual(old_json['stdout'], json.dumps(receipt, ensure_ascii=False, indent=2) + '\n')
            self.assertEqual(text['guard'], 'FRESH_NO_ENGINE_NO_RESELECT_NO_SAVE_NO_WRITE_NO_NETWORK')

    def test_pure_projection_preserves_source_and_unknowns(self):
        for key in ['grid-intent', 'conditional-intent', 'rejected-old-trigger']:
            value = load(OLD / 'journal' / (key + '.json'))['value']; before = deepcopy(value)
            with patch('builtins.open', side_effect=AssertionError('VIEW_IO')), \
                 patch('capital_research.research_choice.choose_saved', side_effect=AssertionError('RESELECT')):
                text = render_text(value)
            self.assertEqual(value, before)
            self.assertEqual(text, (ROOT / 'actual' / key / 'readable.txt').read_text())
            self.assertIn('正式資格全部false，主壓力null', text)
        unknown = load(OLD / 'after-final' / 'same-id-cross-generation-refused' / 'actual.json')
        self.assertIsNone(unknown['choice']['source_binding'])
        text = render_text(unknown)
        self.assertIn('來源綁定：UNKNOWN', text)
        self.assertIn('目標股數（未執行）：無（未選中）', text)
        self.assertNotIn('歷史reviewed token：0', text)

    def test_bad_journal_and_SELECT_text_fail_before_side_effects(self):
        actual = load(ROOT / 'negative-actual.json')
        expected = load(ROOT / 'negative-input-expected.json')
        self.assertEqual(actual['files_before'], actual['files_after'])
        self.assertEqual([r['key'] for r in actual['results']], [r['key'] for r in expected])
        for row, spec in zip(actual['results'], expected):
            result = row['actual']
            self.assertEqual(result['exit_code'], spec['exit_code'], result)
            self.assertEqual(result['stdout'], '')
            self.assertIn(spec['reason'], result['stderr'])
            self.assertEqual(result['guard'], 'FRESH_NO_ENGINE_NO_RESELECT_NO_SAVE_NO_WRITE_NO_NETWORK')

    def test_SELECT_default_JSON_keeps_existing_call_and_output(self):
        receipt = load(OLD / 'receipts' / 'grid-intent-select.json')
        with tempfile.TemporaryDirectory() as folder:
            p = Path(folder) / 'input.json'; p.write_text('{"probe":"verbatim"}')
            for extra in [[], ['--format','json']]:
                stdout = io.StringIO()
                with patch('sys.argv',['choice','SELECT','--store',folder,'--id','one','--input',str(p)] + extra), \
                     patch('capital_research.research_choice_cli.select_and_save',return_value=receipt) as selected, \
                     redirect_stdout(stdout):
                    code = main()
                self.assertEqual(code,0)
                selected.assert_called_once_with(folder,'one',{'probe':'verbatim'})
                self.assertEqual(stdout.getvalue(),json.dumps(receipt,ensure_ascii=False,indent=2)+'\n')


if __name__ == '__main__':
    unittest.main()
