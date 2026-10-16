"""Offline helper tests and synthetic fact checks, not an LLM audit benchmark."""
import copy
from fractions import Fraction
import importlib.util
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
TOOL = ROOT / 'skills/statistical-paper-qc/scripts/qc_tools.py'
sys.path.insert(0, str(TOOL.parent))
sys.path.insert(0, str(Path(__file__).resolve().parent))
import qc_tools as qc
from synthetic import generate


class Acceptance(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # Keep scratch inside the checkout: desktop sandboxes may deny system TEMP.
        scratch = ROOT / 'work'
        scratch.mkdir(exist_ok=True)
        cls.session = tempfile.TemporaryDirectory(prefix='statistical-qc-', dir=scratch)
        cls.addClassCleanup(cls.session.cleanup)
        cls.case = Path(cls.session.name)
        generate(cls.case / 'inputs')
        cls.main = cls.case / 'inputs/main.pdf'
        cls.supp = cls.case / 'inputs/supp.pdf'
        cls.manifest = qc.prepare(cls.main, cls.case / 'main-text')
        qc.prepare(cls.supp, cls.case / 'supp-text')

    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(dir=self.case)
        self.addCleanup(self.temp.cleanup)
        self.out = Path(self.temp.name)
        self.item = {'id': 'B1', 'module': 'B', 'object': 'Table 1',
                     'status': 'pending', 'claim': 'Total matches rows',
                     'location': {'role': 'main', 'pdf_page': 1, 'printed_page': '1'},
                     'equation_level': False, 'evidence': [], 'reason': 'Not run'}
        self.ledger = {'schema_version': 1, 'manuscript_id': 'SYNTHETIC-001',
                       'scope': 'Table 1', 'limitations': [],
                       'inputs': [{'role': 'main', 'path': str(self.main), 'sha256': qc.sha256(self.main)}],
                       'items': [self.item]}

    def test_pdf_page_identity_and_hash(self):
        self.assertEqual(self.manifest['page_count'], 2)
        self.assertEqual(self.manifest['sha256'], qc.sha256(self.main))
        self.assertIn('Theorem 1', (self.case / 'main-text/page-0002.txt').read_text(encoding='utf-8'))
        self.assertIn('=== PDF PAGE 2 ===', (self.case / 'main-text/all.txt').read_text(encoding='utf-8'))

    def test_fixture_bytes_are_repeatable(self):
        generate(self.out / 'second')
        for name in ('main.pdf', 'supp.pdf', 'blank.pdf'):
            self.assertEqual((self.case / 'inputs' / name).read_bytes(), (self.out / 'second' / name).read_bytes())

    def test_generator_refuses_overwrite(self):
        with self.assertRaises(ValueError):
            generate(self.case / 'inputs')

    def test_short_page_needs_review(self):
        m = qc.prepare(self.case / 'inputs/blank.pdf', self.out / 'blank-text')
        self.assertTrue(m['pages'][0]['needs_visual_review'])
        self.assertEqual(m['pages'][0]['characters'], 0)

    def test_pending_is_unfinished(self):
        result = qc.validate_ledger(self.ledger)
        self.assertFalse(result['scope_finished'])
        self.assertEqual(result['assessed'], 0)

    def test_unsupported_verified_rejected(self):
        self.item['status'] = 'verified'
        with self.assertRaisesRegex(ValueError, 'evidence'):
            qc.validate_ledger(self.ledger)

    def test_unseen_equation_rejected(self):
        self.item.update(status='finding', equation_level=True, kind='Error', severity='Major',
                         finding='Wrong equation', suggested_fix='Revise',
                         evidence=[{'method': 'derivation', 'detail': 'A counterexample'}])
        with self.assertRaisesRegex(ValueError, 'inspected page'):
            qc.validate_ledger(self.ledger)

    def test_modified_input_rejected(self):
        self.ledger['inputs'][0]['sha256'] = '0' * 64
        with self.assertRaisesRegex(ValueError, 'changed'):
            qc.validate_ledger(self.ledger)

    def test_duplicate_check_rejected(self):
        self.ledger['items'].append(copy.deepcopy(self.item))
        with self.assertRaisesRegex(ValueError, 'unique'):
            qc.validate_ledger(self.ledger)

    def test_invalid_page_rejected(self):
        with self.assertRaises(ValueError):
            qc.render(self.main, [3], self.out / 'bad-page')

    def test_existing_evidence_preserved(self):
        before = (self.case / 'main-text/all.txt').read_bytes()
        with self.assertRaisesRegex(ValueError, 'empty'):
            qc.prepare(self.supp, self.case / 'main-text')
        self.assertEqual(before, (self.case / 'main-text/all.txt').read_bytes())

    def test_pypdf_extraction_fallback(self):
        original = qc.importlib.util.find_spec
        with patch.object(qc.importlib.util, 'find_spec', side_effect=lambda n: None if n == 'pymupdf' else original(n)):
            m = qc.prepare(self.main, self.out / 'fallback-text')
        self.assertEqual(m['backend'], 'pypdf')
        self.assertEqual(m['page_count'], 2)

    @unittest.skipUnless(shutil.which('pdftoppm'), 'Optional Poppler pdftoppm is not installed')
    def test_poppler_render_fallback(self):
        original = qc.importlib.util.find_spec
        with patch.object(qc.importlib.util, 'find_spec', side_effect=lambda n: None if n == 'pymupdf' else original(n)):
            result = qc.render(self.main, [2], self.out / 'fallback-images')
        self.assertEqual(result['backend'], 'pdftoppm')
        self.assertTrue(Path(result['pages'][0]['artifact']).is_file())

    def test_rendered_page_is_valid_png(self):
        result = qc.render(self.main, [2], self.out / 'images')
        image = Path(result['pages'][0]['artifact'])
        self.assertEqual(image.read_bytes()[:8], b'\x89PNG\r\n\x1a\n')
        self.assertEqual(result['pages'][0]['pdf_page'], 2)
        self.assertFalse(result['visually_inspected'])

    def test_classification_counts(self):
        self.item.update(status='finding', kind='Error', severity='Major', finding='Sum is 110',
                         suggested_fix='Reconcile counts',
                         evidence=[{'method': 'recomputation', 'detail': '60 + 50 = 110'}])
        other = copy.deepcopy(self.item)
        other.update(id='B2', status='inconclusive', reason='SE definition unavailable')
        self.ledger['items'].append(other)
        result = qc.validate_ledger(self.ledger)
        self.assertEqual(result['severity'], {'Critical': 0, 'Major': 1, 'Minor': 0})
        self.assertEqual(result['status']['inconclusive'], 1)

    def test_cli_handles_paths_with_spaces(self):
        inputs = generate(self.out / 'folder with spaces')
        target = self.out / 'output with spaces'
        run = subprocess.run([sys.executable, str(TOOL), 'prepare', '--pdf', str(inputs / 'main.pdf'),
                              '--out', str(target)], capture_output=True, text=True, encoding='utf-8')
        self.assertEqual(run.returncode, 0, run.stderr)
        self.assertEqual(json.loads(run.stdout)['page_count'], 2)

    def test_cli_invalid_ledger_is_nonzero(self):
        self.item['status'] = 'verified'
        path = self.out / 'ledger.json'
        qc.write_json(path, self.ledger)
        run = subprocess.run([sys.executable, str(TOOL), 'check-ledger', '--ledger', str(path)],
                             capture_output=True, text=True, encoding='utf-8')
        self.assertNotEqual(run.returncode, 0)
        self.assertIn('evidence', run.stderr)

    def test_synthetic_facts_and_controls(self):
        main = (self.case / 'main-text/all.txt').read_text(encoding='utf-8')
        supp = (self.case / 'supp-text/all.txt').read_text(encoding='utf-8')
        # Check source facts, not a model's answer. Absence still needs human visual review in an audit.
        self.assertIn('Group A 60; Group B 50; printed total N = 100.', main)
        self.assertNotEqual(60 + 50, 100)
        self.assertIn('See supplementary Table S9', main)
        self.assertIn('Table S1', supp)
        self.assertNotIn('Table S9', supp)
        self.assertIn('For every real x', main)
        self.assertIn('assume x is nonzero', supp)
        self.assertFalse(0 ** 2 > 0)
        self.assertEqual(f'{float(Fraction(1, 3) * 100):.1f}', '33.3')
        self.assertIn('Experiment A uses R = 1000', main)
        self.assertIn('Experiment B uses R = 2000', supp)
        # Polynomial identity via convolution of coefficient arrays, not finite random trials.
        from collections import Counter
        lhs = Counter()
        for i in ((1, 0), (0, 1)):
            for j in ((1, 0), (0, 1)):
                lhs[(i[0] + j[0], i[1] + j[1])] += 1
        self.assertEqual(lhs, {(2, 0): 1, (1, 1): 2, (0, 2): 1})


if __name__ == '__main__':
    unittest.main(verbosity=2)
