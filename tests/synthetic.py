"""Generate small deterministic PDF fixtures without model or network access."""
import argparse
import hashlib
import json
from pathlib import Path


PAGES = {
    'main': [
        ['Synthetic statistical manuscript', 'Table 1 Disjoint groups from one cohort',
         'Group A 60; Group B 50; printed total N = 100.',
         'One of three participants is reported as 33.3 percent.',
         'Experiment A uses R = 1000 independent replicates.',
         'See supplementary Table S9 for extended results.', 'Printed page 1'],
        ['Theorem 1 For every real x, x squared is strictly positive.',
         'The proof appears in the supplement.',
         'Identity (a+b)^2 = a^2 + 2*a*b + b^2.', 'Printed page 2']],
    'supp': [
        ['Supplement', 'Table S1 Extended results',
         'Experiment B uses R = 2000 independent replicates.',
         'Proof of Theorem 1: assume x is nonzero. Then x squared is positive.',
         'Printed page S1']],
    'blank': [[]]
}


def generate(out):
    from reportlab.lib.pagesizes import A4
    from reportlab.pdfgen.canvas import Canvas
    target = Path(out).resolve()
    if target.exists() and (not target.is_dir() or any(target.iterdir())):
        raise ValueError(f'Output must be a new or empty directory: {target}')
    target.mkdir(parents=True, exist_ok=True)
    manifest = {'note': 'Synthetic test inputs only; no real manuscript data', 'files': []}
    for name, pages in PAGES.items():
        path = target / f'{name}.pdf'
        canvas = Canvas(str(path), pagesize=A4, invariant=1, pageCompression=0)
        canvas.setTitle(f'Synthetic QC {name}')
        canvas.setAuthor('Statistical Paper QC synthetic test')
        for lines in pages:
            for i, line in enumerate(lines):
                canvas.drawString(48, 790 - 24 * i, line)
            canvas.showPage()
        canvas.save()
        manifest['files'].append({'file': path.name, 'pages': len(pages),
                                  'sha256': hashlib.sha256(path.read_bytes()).hexdigest()})
    (target / 'manifest.json').write_text(json.dumps(manifest, indent=2) + '\n', encoding='utf-8')
    return target


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out', required=True)
    args = parser.parse_args()
    try:
        print(generate(args.out))
    except ValueError as exc:
        parser.exit(1, str(exc) + '\n')
