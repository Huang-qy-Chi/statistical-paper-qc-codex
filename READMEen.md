# Statistical Paper QC for Codex

**English** | [简体中文](README.md)

A Codex skill for assisted quality control of statistical manuscripts. It checks consistency between the main paper and supplement, numerical claims, proof assumptions, and proof gaps, while maintaining evidence and coverage records.

This is a review workflow for Codex, not a standalone automated reviewer or a formal proof verifier. The helper script handles PDF extraction, page rendering, and ledger validation only.

## Upstream source and authorization status

Adapted from `skills/jasa-acs-qc/SKILL.md` in [BIG-S2/statistical-paper-qc](https://github.com/BIG-S2/statistical-paper-qc). The upstream project provides Claude examples. This adaptation adds Codex instructions, portable tools, a coverage ledger, conditional statistical checks, and synthetic tests.

This version was prepared on October 16, 2026. No license file was found in the upstream local snapshot used for the adaptation. No license has been added to this repository, and no authorization to adapt or redistribute the upstream material is claimed. Confirm upstream authorization before public release; attribution alone does not grant permission. This directory is a release preparation draft and has not been uploaded to GitHub. Third-party runtime dependencies remain subject to their own licenses.

## Features

| Module | Scope |
| --- | --- |
| A | Consistency of references, tables, descriptions, and assumptions between the main paper and supplement |
| B | Recalculation of totals, percentages, statistics, simulation results, and numerical claims |
| C | Optional journal structure checks, subject to verification of current journal policies |
| D | Theorem-by-theorem checks of assumptions, derivations, boundaries, counterexamples, and use of external results |

The ledger distinguishes `pending`, `verified`, `finding`, `inconclusive`, and `not_applicable`. Diagnostic clues such as empirical convergence rates, inferred replication counts, or fitted parameters do not automatically become confirmed errors. Equation findings require inspection of page images; numerical findings retain reproducible calculations.

## Environment and dependencies

Tested on Windows with Python 3.12.14. Dependencies are pinned to the versions actually tested. Other operating systems and Python versions have not been verified. Do not assume installation will succeed if a compatible wheel is unavailable.

Prefer the workspace Python runtime and dependencies provided by Codex when available; there is no need to reinstall existing packages. For a regular Python environment, create an isolated environment from the repository root:

Windows PowerShell:

```powershell
python -m venv .venv
& .\.venv\Scripts\python.exe -m pip install -r requirements.txt
& .\.venv\Scripts\python.exe skills/statistical-paper-qc/scripts/qc_tools.py probe
```

macOS or Linux (commands are designed to be portable but have not been tested on these systems):

```bash
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
.venv/bin/python skills/statistical-paper-qc/scripts/qc_tools.py probe
```

`probe` checks only whether packages and commands can be found. It does not perform OCR or establish that all functionality works. The dependency file includes PyMuPDF (preferred extraction and rendering), pypdf (extraction fallback), NumPy (numerical calculations), and python-docx (Word generation).

Poppler's `pdftoppm` is an optional rendering fallback and is unnecessary when PyMuPDF works. Visual verification of Word reports also requires Codex document tools or an available LibreOffice rendering environment; these system components cannot be installed through requirements.txt. When visual verification is unavailable, deliver Markdown and retain the Word draft only as an unverified intermediate. Scanned documents require separate OCR.

## Install in Codex

After downloading the repository, copy the **entire** `skills/statistical-paper-qc` directory to a skill location that Codex discovers. Do not copy only SKILL.md or treat the entire repository as a single skill.

For project-level installation, use `.agents/skills/statistical-paper-qc`. For user-level installation, use `~/.agents/skills/statistical-paper-qc` as appropriate for your setup. Loading from `~/.codex/skills/statistical-paper-qc` was also verified in the current Codex desktop environment. See the [official skills documentation](https://learn.chatgpt.com/docs/build-skills).

For example, install to the documented user-level directory in PowerShell. The command stops if the destination exists to avoid overwriting a previous version:

```powershell
$skillRoot = Join-Path $HOME '.agents/skills'
$destination = Join-Path $skillRoot 'statistical-paper-qc'
if (Test-Path -LiteralPath $destination) { throw 'Skill already exists; inspect it before updating.' }
New-Item -ItemType Directory -Path $skillRoot -Force | Out-Null
Copy-Item -LiteralPath './skills/statistical-paper-qc' -Destination $destination -Recurse
```

Type `$statistical-paper-qc` in a new chat. If it does not appear, restart Codex and check the directory layout. If dependencies are installed in `.venv`, provide the interpreter's absolute path in your audit request. Copying the skill does not copy or install its Python environment.

## Usage

```text
Use $statistical-paper-qc to audit main.pdf and supp.pdf.
ID: PAPER-001. Run Modules A, B, and D; skip journal structure Module C.
Report in English. Inspect original pages before equation findings, and save
recalculation code and output for numerical findings.
Track checked, unchecked, and inconclusive items. Save deliverables under
this workspace's outputs directory.
Generate a Word report and visually verify its layout when possible;
otherwise deliver Markdown and state the limitation.
```

You can restrict an audit to specific tables, theorems, or sections. An automatic switch to a more expensive model is not required. Difficult mathematical conclusions still require stepwise verification; finite numerical experiments cannot prove a general theorem.

Examples of manual helper calls (replace `python` with your selected interpreter):

```bash
python skills/statistical-paper-qc/scripts/qc_tools.py prepare --pdf main.pdf --out work/main
python skills/statistical-paper-qc/scripts/qc_tools.py render --pdf main.pdf --pages 1 2 --out work/main-images
python skills/statistical-paper-qc/scripts/qc_tools.py check-ledger --ledger work/qc-ledger.json
```

Output directories must be empty to prevent overwriting existing evidence. The tools record one-based PDF page numbers and SHA-256 hashes; printed page labels require manual inspection. See [ledger.md](skills/statistical-paper-qc/references/ledger.md) for the ledger format.

## Reproducible tests

Run from the repository root. No Codex login or API key is required. These commands reuse the `.venv` created above without requiring activation.

Windows PowerShell:

```powershell
& .\.venv\Scripts\python.exe -m pip install -r requirements-test.txt
& .\.venv\Scripts\python.exe -m unittest discover -s tests -v
```

macOS or Linux:

```bash
.venv/bin/python -m pip install -r requirements-test.txt
.venv/bin/python -m unittest discover -s tests -v
```

Tests generate synthetic PDFs in temporary directories under the repository's `work/` folder, extract text, and check the helpers. They do not depend on a particular username or an earlier task directory. The checkout must be writable. Temporary files are cleaned up after the run, and tests can be repeated. If `pdftoppm` is unavailable, only its optional fallback test is skipped with an explanation; the remaining tests should still run.

To retain the materials for a manual or model audit (replace `python` with the `.venv` interpreter above, or the interpreter path provided by Codex when using its bundled environment):

```bash
python tests/synthetic.py --out work/synthetic
```

The generator refuses to overwrite a nonempty directory. PDF metadata is fixed, and a SHA-256 manifest is included. Repeated generation in the same environment should produce identical bytes. Identical PDF hashes are not guaranteed across dependency versions.

Give the generated main.pdf and supp.pdf to the skill using the [audit request](examples/synthetic/audit-request.txt). [expected.json](examples/synthetic/expected.json) contains ground truth for evaluation; do not provide it as input to the model being evaluated.

The synthetic case contains three issues (an incorrect total, a reference to nonexistent Table S9, and a strict positivity theorem that fails at zero) and three valid controls (33.3% rounding, different replication counts for different experiments, and a binomial expansion). The model need not use identical finding IDs or wording.

Automated tests check PDF tools, ledger boundaries, and verifiable facts in the synthetic materials. **They do not automatically evaluate whether Codex reviews a manuscript correctly.** Manual evaluation should examine evidence, coverage of the six scoped claims, and false positives rather than merely matching output text. Word generation and layout verification are not pass conditions for this test suite.

## Known limitations and material handling

- Validation was performed only on Windows with the dependency environment described above. Synthetic cases do not establish accuracy on real manuscripts.
- Word generation was verified locally, but visual verification could not be completed because LibreOffice was unavailable. A Markdown fallback is retained.
- Ledger validation checks structure, input hashes, and the existence of declared evidence files. It does not establish mathematical truth or ensure that page numbers are within the document; inspect the original pages.
- Do not commit real manuscripts, supplements, extracted text, data, or reports to this repository. `.gitignore` helps prevent mistakes but does not replace reviewing files before publication.
- Local tool execution does not mean that the model runs offline. Selected content is still sent to the current model service. Process only materials authorized for that environment.

## Repository layout

```text
README.md
READMEen.md
requirements.txt
requirements-test.txt
.gitignore
skills/statistical-paper-qc/
  SKILL.md
  agents/openai.yaml
  references/modules.md
  references/ledger.md
  scripts/qc_tools.py
tests/synthetic.py
tests/test_qc_tools.py
examples/synthetic/audit-request.txt
examples/synthetic/expected.json
```
