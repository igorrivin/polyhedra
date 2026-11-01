"""Bind completed independent checks and actual page inspection to exact bytes."""
from pathlib import Path
import datetime
import hashlib
import json
import subprocess

ROOT = Path('/Volumes/Lexar/lambda/devel/polyhedra/consolidated')
EV = ROOT.parent / 'execution/section15-analytic-review-2026-11-01'
OUT = EV / 'integration-review'
BASE = '3ddf610dbe4578c7828e55f4e9cd92aacaba6df6'

def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def load(path):
    return json.loads(path.read_text())

def save(name, data):
    (OUT / name).write_text(json.dumps(data, indent=2) + '\n')

now = datetime.datetime.now(datetime.timezone.utc).isoformat()
checks = load(OUT / 'integration-checks.json')
numeric = load(OUT / 'numeric-delta-review.json')
inputs = load(OUT / 'pdf-inputs.json')
pdf = load(OUT / 'pdf-build-review.json')
assert checks['checks_passed'] and numeric['decision'] == 'approved_for_recorded_finite_evidence_scope'
sources = {row['path']: row['sha256'] for row in checks['source_identities']}
assert len(sources) == 12
for path, digest in sources.items():
    assert sha(ROOT / path) == digest, path
assert subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=ROOT).decode().strip() == BASE
status = subprocess.check_output(['git', 'status', '--porcelain', '--untracked-files=all'], cwd=ROOT).decode().splitlines()
assert status == checks['status_porcelain']
for path, digest in inputs['sha256'].items():
    assert sha(ROOT / path) == sha(OUT / 'source' / path) == digest
assert sha(Path(pdf['pdf'])) == pdf['pdf_sha256']
assert pdf['source_labels'] == pdf['compiled_labels'] == 607
assert pdf['bibliography_items'] == pdf['compiled_citations'] == 129
assert not pdf['undefined_or_duplicate_labels'] and not pdf['overfull_boxes']

math = load(EV / 'math-review/approved-hashes.json')
code = load(EV / 'computation-review/approved-hashes.json')
assert math['decision'] == 'approved_with_stated_scope'
assert code['decision'] == 'approved_for_corrected_source_and_bounded_finite_numerical_evidence'
assert sha(EV / 'computation-review/approved-hashes.json') == '8d6e476224516cc2d042bae3a799c3c65ed091d52de1711b58fc9786a6ee4d2d'
for path, digest in math['approved_sha256'].items():
    assert sha(EV / 'math-author/integration-baseline' / path) == digest
for path, digest in math['evidence_sha256'].items():
    assert sha(EV / 'math-review' / path) == digest
for path, digest in code['approved_code_sha256'].items():
    assert sources[path] == sha(ROOT / path) == digest
for path, digest in code['review_context_sha256'].items():
    assert sha(ROOT / path) == digest
for path, digest in code['review_and_evidence_sha256'].items():
    assert sha(EV / 'computation-review' / path) == digest, path

# The recorder must show exactly the 18 frozen manuscript inputs. System TeX
# packages/fonts remain runtime dependencies, not part of the manuscript graph.
snapshot, book = OUT / 'source', OUT / 'source/book'
actual_inputs = set()
for line in (OUT / 'build/main.fls').read_text().splitlines():
    if line.startswith('INPUT '):
        path = Path(line[6:])
        path = (path if path.is_absolute() else book / path).resolve()
        if path.is_relative_to(snapshot) and path.suffix == '.tex':
            actual_inputs.add(str(path.relative_to(snapshot)))
assert actual_inputs == set(inputs['sha256']) and len(actual_inputs) == 18

# Actual image inspection of these pages was performed through view_image.
# After inspection, distinguish the figure list and the next-section page
# from the conservative boundary ranges used by the rendering script.
pages = [2, 3, 4, 5, 6, 7, 72, 73, 74, 75, 76, 77, 78, 79, 80, 81,
         181, 182, 183, 184, 185, 186, 187]
assert pages == pdf['selected_pages']
page_notes = {
    2: 'Contents opening, leaders and page-number column fit.',
    3: 'Contents Section15 heading and all seven subsections have readable page references; Section16 continues to the next contents page.',
    4: 'Contents continuation and shifted later-section page references fit.',
    5: 'Contents continuation, subsection indentation and long titles fit.',
    6: 'Contents ending, appendices and References entry fit; References points to181.',
    7: 'List of Figures remains legible with aligned references and no overlap.',
    72: 'Adjoining Section14 correction and companion paths fit with readable equations.',
    73: 'Section15 opening, normalization formulas and boxed additive theorem fit.',
    74: 'Corrected Gamma subtraction and real log-S/D integrals fit and are legible.',
    75: 'Phase/amplitude formulas, coefficient table and real phase-constant specialization fit.',
    76: 'Contour/tail proof, rational Psi derivative and final tail inequality fit.',
    77: 'Gaussian estimate, weighted expansion and integrated-remainder formulas fit.',
    78: 'Airy proof ending, numerical settings and all six corrected table rows are clear; first Q reads0.459086.',
    79: 'Independent-reference limitations, historical discrepancy, wrapped provenance paths and bounded interpretation fit.',
    80: 'Section16 begins cleanly on the following page; equations and subsection transition fit.',
    81: 'Additional adjoining Section16 page has readable equations and no pagination defect.',
    181: 'References opening and entries1-21 fit, with natural continuation.',
    182: 'References continuation through45 has legible wrapping and numbering.',
    183: 'References continuation through67, including DLMF54, is legible.',
    184: 'References continuation through89, including Murakami-Yano83, fits.',
    185: 'References continuation through108, including TV96 and its pinned version, fits.',
    186: 'References continuation through126 has readable URLs and wrapping.',
    187: 'Final entries127-129 and page footer are complete and legible.',
}
image_records = []
for page in pages:
    path = f'rendered/page-{page:03d}.png'
    assert sha(OUT / path) == pdf['rendered_sha256'][path]
    note = page_notes[page]
    for old, new in {'Section15': 'Section 15', 'Section16': 'Section 16',
                     'Section14': 'Section 14', 'to181': 'to 181', 'reads0': 'reads 0',
                     'entries1': 'entries 1', 'through45': 'through 45', 'through67': 'through 67',
                     'DLMF54': 'DLMF 54', 'through89': 'through 89', 'Yano83': 'Yano 83',
                     'through108': 'through 108', 'TV96': 'TV 96', 'through126': 'through 126'}.items():
        note = note.replace(old, new)
    image_records.append({'page': page, 'path': path, 'sha256': sha(OUT / path),
                          'inspected_with': 'view_image', 'finding': 'pass', 'notes': note})
pdf['section_pages']['section15']['all_section_pages'] = list(range(73, 80))
pdf['section_pages']['section15']['last_section_page'] = 79
pdf['contents_pages'] = [2, 3, 4, 5, 6]
pdf['list_of_figures_pages'] = [7]
pdf['visual_review'] = 'passed; all 23 selected pages actually inspected with view_image'
pdf['visual_review_record'] = 'visual-review.json'
pdf['actual_recorded_manuscript_inputs_match_frozen_graph'] = True
pdf['actual_recorded_manuscript_input_count'] = 18
pdf['page_classification_note'] = 'Post-inspection classification: Section 15 occupies 73-79; 80 starts Section 16; 7 is the List of Figures. Rendered page set is unchanged.'
prior_pdf = load(ROOT.parent / 'execution/quantum-surgery-review-2026-11-01/integration-review/pdf-build-review.json')
assert pdf['underfull_boxes'] == prior_pdf['underfull_boxes']
pdf['warning_assessment'] = {
    'underfull_box': 'Inherited unchanged Section 9 paragraph at chapter09 lines 131-143, badness 1014; no new overfull boxes.',
    'epstopdf': 'Expected shell-escape-disabled package warning with -no-shell-escape. The active manuscript graph has inline figures and no external-asset command.',
    'undefined_references_or_citations': False,
    'duplicate_labels_or_missing_glyphs': False,
}
save('pdf-build-review.json', pdf)
save('visual-review.json', {
    'reviewed_at_utc': now, 'decision': 'passed_for_stated_visual_scope',
    'pdf_sha256': pdf['pdf_sha256'], 'pdf_pages': 187, 'inspected_pages': pages,
    'inspected_page_count': 23, 'section15_pages': list(range(73, 80)),
    'adjoining_pages': [72, 80, 81], 'contents_pages': [2, 3, 4, 5, 6],
    'list_of_figures_pages': [7], 'bibliography_pages': list(range(181, 188)),
    'images': image_records, 'new_visual_defects': [],
    'summary': 'No clipped text, overlapping content, broken equations/tables, unreadable glyphs, bad headers/footers, or unresolved visual references found in the 23 inspected pages.',
    'scope': 'All Section 15 pages plus adjoining pages, complete contents, List of Figures and complete shifted bibliography. This is not a whole-book visual or mathematical review.',
})
assert 'Ran 25 tests' in (OUT / 'site-tests.stderr').read_text()
assert (OUT / 'site-tests.stderr').read_text().rstrip().endswith('OK')
save('validation-commands.json', {
    'recorded_at_utc': now,
    'site_tests': {
        'argv': ['/tmp/polyhedra-baseline-20261031/bin/python', '-B', '-m', 'unittest', 'discover', '-s', 'site/tests'],
        'cwd': str(ROOT), 'returncode': 0, 'tests_passed': 25,
        'stdout': 'site-tests.stdout', 'stdout_sha256': sha(OUT / 'site-tests.stdout'),
        'stderr': 'site-tests.stderr', 'stderr_sha256': sha(OUT / 'site-tests.stderr'),
        'scope': 'Existing site/build unit suite, not browser or hosted publication verification.',
    },
    'integration_check': {'script': 'verify_integration.py', 'script_sha256': sha(OUT / 'verify_integration.py'),
                          'returncode': 0, 'stdout': 'verify-integration.stdout', 'stderr': 'verify-integration.stderr'},
    'pdf_build': {'receipt': 'full-book-build-command.json', 'returncode': 0},
    'marker': {'receipt': 'pdf-operation-marker-command.json', 'successful_invocations': 1,
               'immediately_before_first_latexmk_build': True},
})

review = f'''# Independent Section 15 integration review

Approved for source commit at the exact12-path manifest in
`approved-source-manifest.json`, with the scope limits below. Review date:
2026-11-01. Baseline: `{BASE}`. This reviewer changed no canonical file and
made no commit, upload, browser action, remote change or package installation.

The approved analytic chapter was archived before numerical editing. Its
prefix through the proof and its final interpretation subsection are
byte-identical to the independently approved bytes. Only the numerical
subsection changed. The13 prior ledger claims preserve their analytic proof
text, statuses and source pins; the finite numerical claim brings the total
to14. New numerical/computational metadata is explicitly distinct from proof.
The separate mathematical and code approval manifests are bound by hashes
in the final manifest; their scope is not expanded by this integration review.

The six displayed quantum/Airy table rows match nearest-six-decimal rounding
of the recorded90-dps C=1 values. The first quantum value is
0.459086488736078952..., hence0.459086; the other five historical quantum
roundings agree. The negative-zeta value and three scaled residuals match.
The runner's comparisons before Q serialization have maxima
3.96705306793319e-57 across60/90dps and1.22727336632443e-91 across contour/order
settings. Both support the stated strict upper bounds. Serialized-Q string
comparisons are recorded separately and do not replace these more precise
runner differences. The independent seven-input combined-Barnes QUADPACK
record agrees within1.80e-12. `numeric-delta-review.json` records these checks.

`computation/full-v1.json` remains the earlier source-recorded run, at its own
hashes. It is not relabeled as a run of the final corrected code. The later
clean-source full replay and canonical result remain separate post-commit
gates. No interval enclosure, guaranteed achieved digits, recovery of the
original historical run, arbitrary-shape theorem, unbounded-zeta result,
fixed-volume matching limit or global quantum invariant is asserted.

Preservation checks passed for all1,843 protected paths among the1,851-file
baseline, including412 materialized LFS files. Both original repositories
remain clean at their recorded heads, and all953 original files, the source
archive and supplied reference PDF match their inventories. All607 labels
remain in order, including all21 Section15 labels; all129 bibliography keys
remain in order. The frozen historical table and prior Section15 result are
unchanged. Existing artifacts and Site exports are included in this preserved
baseline. The12-path change set is exactly eight approved modifications and
four new evaluator files. All162 local Markdown links resolve except the
explicitly planned Section15 checkpoint README, pending curation.

The existing site/build suite passed25 tests. The full book was built with
`latexmk -norc -pdf -interaction=nonstopmode -halt-on-error -file-line-error
-no-shell-escape` from a frozen18-file active TeX graph outside canonical.
The recorder's manuscript inputs exactly match that graph. The skill marker
ran successfully once, immediately before the first build. The resulting
187-page PDF has SHA256 `{pdf['pdf_sha256']}`. All607 labels and129 citations
resolve, with no duplicate labels, missing glyphs or overfull boxes. The sole
underfull-box diagnostic is the unchanged Section9 paragraph at lines131-143;
the epstopdf warning records intentionally disabled shell escape.

All23 selected pages were rendered with the approved Ghostscript fallback
and actually inspected with `view_image`: contents2-6, List of Figures7,
Section15 pages73-79, adjoining pages72,80-81, and bibliography181-187. The
normalization formulas, derivative table, boxed theorem, corrected numerical
table, wrapped provenance paths, headers, footers and reference entries are
legible without clipping or overlap. This is a complete Section15 visual
review with the stated adjoining/front/back matter, not a whole-book visual
or mathematical review. Exact page/image hashes are in `visual-review.json`.

The evidence files are `integration-checks.json`, `numeric-delta-review.json`,
`pdf-inputs.json`, `pdf-build-review.json`, `visual-review.json`, and
`validation-commands.json`; the final source manifest binds all of them,
the independent review approvals and this report. Final clean numerical
generation, evidence curation and their independent verification remain
separate next stages; publication and upload remain deferred.
'''
# Use ordinary prose spacing even for the compact numerical identifiers above.
replacements = {
    'exact12': 'exact 12', 'The13': 'The 13', 'to14': 'to 14', 'recorded90': 'recorded 90',
    'hence0': 'hence 0', 'across60': 'across 60', 'and1.': 'and 1.', 'within1.': 'within 1.',
    'all1,843': 'all 1,843', 'the1,851': 'the 1,851', 'including412': 'including 412',
    'all953': 'all 953', 'All607': 'All 607', 'all21': 'all 21', 'all129': 'all 129',
    'The12': 'The 12', 'All162': 'All 162', 'passed25': 'passed 25', 'frozen18': 'frozen 18',
    'and129': 'and 129', 'lines131': 'lines 131', 'All23': 'All 23', 'contents2': 'contents 2',
    'Figures7': 'Figures 7', 'pages73': 'pages 73', 'pages72': 'pages 72',
    'bibliography181': 'bibliography 181',
    'Section15': 'Section 15', 'Section9': 'Section 9', '60/90dps': '60/90 dps',
    '72,80-81': '72, 80-81',
}
for old, new in replacements.items():
    review = review.replace(old, new)
(OUT / 'review.md').write_text(review)

bound_records = ['review.md', 'numeric-delta-review.json', 'integration-checks.json',
                 'pdf-inputs.json', 'pdf-build-review.json', 'visual-review.json',
                 'validation-commands.json', 'full-book-build-command.json',
                 'pdf-operation-marker-command.json', 'verify_integration.py',
                 'build_review.py', 'finalize_review.py']
save('approved-source-manifest.json', {
    'schema_version': '1.0', 'generated_at_utc': now,
    'decision': 'approved_with_explicit_scope_limits', 'reviewer': 'airy_integration_review',
    'baseline_commit': BASE, 'repository_root': str(ROOT),
    'approved_source_sha256': sources, 'approved_source_count': 12,
    'modified_baseline_paths': 8, 'new_source_paths': 4,
    'independent_approvals': {
        'math': {'manifest': '../math-review/approved-hashes.json',
                 'manifest_sha256': sha(EV / 'math-review/approved-hashes.json'),
                 'report': '../math-review/analytic-review.md',
                 'report_sha256': sha(EV / 'math-review/analytic-review.md'),
                 'approved_analytic_sha256': math['approved_sha256'],
                 'carryover': 'Analytic prefix and interpretation suffix remain byte-identical; numerical/ledger delta independently approved by this review.'},
        'code': {'manifest': '../computation-review/approved-hashes.json',
                 'manifest_sha256': sha(EV / 'computation-review/approved-hashes.json'),
                 'report': '../computation-review/computational-review.md',
                 'report_sha256': sha(EV / 'computation-review/computational-review.md'),
                 'approved_code_sha256': code['approved_code_sha256']},
    },
    'review_records_sha256': {name: sha(OUT / name) for name in bound_records},
    'pdf': {'path': pdf['pdf'], 'sha256': pdf['pdf_sha256'], 'pages': 187,
            'active_input_files': 18, 'input_sha256': inputs['sha256'],
            'compiled_labels': 607, 'compiled_citations': 129,
            'visually_inspected_pages': pages},
    'source_commit_approval': True,
    'separate_remaining_gates': ['Commit exactly the approved 12-source change set.',
                                'Fresh clean-source full numerical replay and strict comparison.',
                                'Curated canonical result/PDF/evidence and independent checkpoint verification.'],
    'limitations': ['No whole-book mathematical or visual approval.',
                    'No interval quadrature certificate or achieved-digit guarantee.',
                    'No recovery of the missing historical evaluator/raw run.',
                    'No enlargement beyond the approved regular-family bounded-real-zeta theorem.',
                    'No upload, hosted browser QA, deployment or publication approval.'],
})
print(json.dumps({'decision': 'approved_with_explicit_scope_limits',
                  'approved_source_manifest_sha256': sha(OUT / 'approved-source-manifest.json'),
                  'review_sha256': sha(OUT / 'review.md'), 'pdf_sha256': pdf['pdf_sha256'],
                  'visual_pages': len(pages), 'source_paths': len(sources)}, indent=2))
