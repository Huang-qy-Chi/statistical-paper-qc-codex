"""Portable local PDF preparation and QC ledger checks; no automated review."""
import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
import re
import shutil
import subprocess
import sys


def sha256(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as f:
        for block in iter(lambda: f.read(1024 * 1024), b''):
            h.update(block)
    return h.hexdigest()


def write_json(path, data):
    Path(path).write_text(json.dumps(data, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')


def new_directory(path):
    # Avoid silently replacing evidence from a previous input or run.
    out = Path(path).resolve()
    if out.exists() and any(out.iterdir()):
        raise ValueError(f'Output directory must be empty: {out}')
    out.mkdir(parents=True, exist_ok=True)
    return out


def prepare(pdf, out):
    source = Path(pdf).resolve(strict=True)
    if importlib.util.find_spec('pymupdf'):
        import pymupdf
        with pymupdf.open(source) as doc:
            if doc.needs_pass:
                raise ValueError('Encrypted PDF needs an authorized decrypted copy')
            texts = [page.get_text(sort=True) for page in doc]
        backend = 'pymupdf'
    else:
        from pypdf import PdfReader
        doc = PdfReader(str(source))
        if doc.is_encrypted:
            raise ValueError('Encrypted PDF needs an authorized decrypted copy')
        texts = [page.extract_text() or '' for page in doc.pages]
        backend = 'pypdf'
    target = new_directory(out)
    pages = []
    for n, content in enumerate(texts, 1):
        name = f'page-{n:04d}.txt'
        (target / name).write_text(content, encoding='utf-8')
        pages.append({'pdf_page': n, 'printed_page': None, 'text_file': name,
                      'characters': len(content.strip()),
                      'needs_visual_review': len(content.strip()) < 40})
    (target / 'all.txt').write_text('\n'.join(
        f'=== PDF PAGE {n} ===\n{t}' for n, t in enumerate(texts, 1)), encoding='utf-8')
    manifest = {'source': str(source), 'sha256': sha256(source), 'backend': backend,
                'page_count': len(pages), 'pages': pages,
                'note': 'No OCR or mathematical verification performed; printed labels require inspection.'}
    write_json(target / 'manifest.json', manifest)
    return manifest


def render(pdf, pages, out, dpi=144, pdftoppm=None):
    source = Path(pdf).resolve(strict=True)
    if dpi < 36 or dpi > 600 or any(p < 1 for p in pages):
        raise ValueError('Use one-based pages and DPI between 36 and 600')
    target = new_directory(out)
    artifacts = []
    if importlib.util.find_spec('pymupdf'):
        import pymupdf
        with pymupdf.open(source) as doc:
            if doc.needs_pass or any(p > len(doc) for p in pages):
                raise ValueError('Encrypted PDF or page outside document')
            for p in sorted(set(pages)):
                image = target / f'page-{p:04d}.png'
                doc[p-1].get_pixmap(dpi=dpi).save(image)
                artifacts.append({'pdf_page': p, 'artifact': str(image)})
        backend = 'pymupdf'
    else:
        exe = pdftoppm or shutil.which('pdftoppm')
        if not exe:
            raise RuntimeError('Rendering requires PyMuPDF or pdftoppm')
        for p in sorted(set(pages)):
            prefix = target / f'page-{p:04d}'
            subprocess.run([str(exe), '-f', str(p), '-l', str(p), '-singlefile',
                            '-r', str(dpi), '-png', str(source), str(prefix)],
                           check=True, capture_output=True, text=True, timeout=90)
            image = prefix.with_suffix('.png')
            if not image.is_file():
                raise RuntimeError(f'Renderer did not produce page {p}')
            artifacts.append({'pdf_page': p, 'artifact': str(image)})
        backend = 'pdftoppm'
    result = {'source': str(source), 'sha256': sha256(source), 'backend': backend,
              'dpi': dpi, 'pages': artifacts, 'visually_inspected': False}
    write_json(target / 'renders.json', result)
    return result


def validate_ledger(data):
    if data.get('schema_version') != 1:
        raise ValueError('Unsupported schema_version')
    for key in ('manuscript_id', 'scope'):
        if not isinstance(data.get(key), str) or not data[key].strip():
            raise ValueError(f'Missing {key}')
    if not isinstance(data.get('limitations'), list):
        raise ValueError('limitations must be a list')
    roles = set()
    if not isinstance(data.get('inputs'), list) or not data['inputs']:
        raise ValueError('inputs must be a nonempty list')
    for source in data['inputs']:
        role = source.get('role')
        if not isinstance(role, str) or not role or role in roles:
            raise ValueError('Input roles must be nonempty and unique')
        roles.add(role)
        if not re.fullmatch(r'[0-9a-fA-F]{64}', source.get('sha256', '')):
            raise ValueError('Input SHA-256 must be 64 hexadecimal digits')
        path = Path(source.get('path', ''))
        if not path.is_absolute() or not path.is_file() or sha256(path) != source['sha256'].lower():
            raise ValueError(f'Input absent or changed: {path}')
    if not isinstance(data.get('items'), list) or not data['items']:
        raise ValueError('items must contain scoped checks')
    counts = dict.fromkeys(('pending', 'verified', 'finding', 'inconclusive', 'not_applicable'), 0)
    severities = dict.fromkeys(('Critical', 'Major', 'Minor'), 0)
    kinds = dict.fromkeys(('Error', 'Gap', 'Defect'), 0)
    seen = set()
    for item in data['items']:
        ident = item.get('id')
        if not isinstance(ident, str) or not ident or ident in seen:
            raise ValueError('Check IDs must be nonempty and unique')
        seen.add(ident)
        for key in ('object', 'claim'):
            if not isinstance(item.get(key), str) or not item[key].strip():
                raise ValueError(f'{ident}: missing {key}')
        if item.get('module') not in ('A', 'B', 'C', 'D'):
            raise ValueError(f'{ident}: invalid module')
        status = item.get('status')
        if status not in counts:
            raise ValueError(f'{ident}: invalid status')
        counts[status] += 1
        loc = item.get('location', {})
        if loc.get('role') not in roles or type(loc.get('pdf_page')) is not int or loc['pdf_page'] < 1:
            raise ValueError(f'{ident}: invalid input role or page')
        if type(item.get('equation_level')) is not bool:
            raise ValueError(f'{ident}: equation_level must be boolean')
        evidence = item.get('evidence')
        if not isinstance(evidence, list):
            raise ValueError(f'{ident}: evidence must be a list')
        for e in evidence:
            if not e.get('method') or not e.get('detail'):
                raise ValueError(f'{ident}: evidence needs method and detail')
            if 'artifact' in e:
                path = Path(e['artifact'])
                if not path.is_absolute() or not path.is_file():
                    raise ValueError(f'{ident}: evidence artifact absent')
        if status in ('verified', 'finding') and not evidence:
            raise ValueError(f'{ident}: supported conclusions need evidence')
        if status in ('pending', 'inconclusive', 'not_applicable') and not item.get('reason'):
            raise ValueError(f'{ident}: reason required')
        if status == 'finding':
            if item.get('severity') not in severities or item.get('kind') not in kinds:
                raise ValueError(f'{ident}: invalid finding classification')
            if not item.get('finding') or not item.get('suggested_fix'):
                raise ValueError(f'{ident}: finding and suggested_fix required')
            severities[item['severity']] += 1
            kinds[item['kind']] += 1
            if item['equation_level'] and not any(
                e['method'] == 'page_image' and e.get('artifact', '').lower().endswith('.png')
                and e.get('visually_inspected') is True for e in evidence):
                raise ValueError(f'{ident}: equation finding requires inspected page image')
    return {'scoped': len(seen), 'status': counts, 'severity': severities, 'kind': kinds,
            'resolved': counts['verified'] + counts['finding'],
            'assessed': len(seen) - counts['pending'], 'scope_finished': counts['pending'] == 0,
            'note': 'Structural validation only; conclusions and evidence content require review.'}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest='command', required=True)
    commands.add_parser('probe')
    for name in ('prepare', 'render'):
        cmd = commands.add_parser(name)
        cmd.add_argument('--pdf', required=True)
        cmd.add_argument('--out', required=True)
        if name == 'render':
            cmd.add_argument('--pages', required=True, type=int, nargs='+')
            cmd.add_argument('--dpi', type=int, default=144)
            cmd.add_argument('--pdftoppm')
    cmd = commands.add_parser('check-ledger')
    cmd.add_argument('--ledger', required=True)
    args = parser.parse_args()
    try:
        if args.command == 'probe':
            result = {'python': sys.executable,
                      'packages': {n: importlib.util.find_spec(n) is not None
                                   for n in ('pymupdf', 'pypdf', 'pdfplumber', 'numpy', 'docx')},
                      'commands': {n: shutil.which(n) for n in ('pdftotext', 'pdftoppm', 'pdfinfo')},
                      'note': 'Availability only, not an execution or OCR test.'}
        elif args.command == 'prepare':
            result = prepare(args.pdf, args.out)
        elif args.command == 'render':
            result = render(args.pdf, args.pages, args.out, args.dpi, args.pdftoppm)
        else:
            result = validate_ledger(json.loads(Path(args.ledger).read_text(encoding='utf-8-sig')))
        print(json.dumps(result, ensure_ascii=False, indent=2))
    except Exception as exc:
        print(f'{type(exc).__name__}: {exc}', file=sys.stderr)
        return 1
    return 0


if __name__ == '__main__':
    sys.exit(main())
