"""Copy the reviewed offline candidate and prepare the final explicit local commit."""
from datetime import datetime, timezone
from hashlib import sha256
import json
from pathlib import Path
import subprocess

ROOT = Path('/Volumes/Lexar/lambda/devel/polyhedra/consolidated')
RAW = ROOT.parent / 'execution/sites-preview-2026-11-01'
CHECKPOINT = ROOT / 'docs/execution/sites-preview-2026-11-01'
MIRROR = ROOT.parent / 'publishing/polyhedra-reading-preview-20261101'
SOURCE = 'e79d4cee5b9fd7f999054617406ecebb1b9677cd'
PROJECT = 'appgprj_6ae6b5b94abc8191aa00dfe244adcf37'
ARCHIVE_SHA = '9425c791ecb0f7d88f91aae8b19dfb7d30c6526446b103cf6415e79734007cd1'


def digest(path):
    return sha256(path.read_bytes()).hexdigest()


def write_json(path, value):
    path.write_text(json.dumps(value, indent=2) + '\n')


assert subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=ROOT).decode().strip() == SOURCE
assert not subprocess.check_output(['git', 'status', '--porcelain'], cwd=ROOT)
review = json.loads((RAW / 'final-archive-verification.json').read_text())
export = json.loads((RAW / 'final-export-verification.json').read_text())
native = json.loads((RAW / 'native-sites-state.json').read_text())
assert review['archive_sha256'] == ARCHIVE_SHA and review['file_count'] == 50
assert digest(Path(review['archive_path'])) == ARCHIVE_SHA
assert review['research_source_commit'] == SOURCE and export['source_commit'] == SOURCE

command = {
    'source': 'Exact official helper invocation and completion reported by the root agent; payload independently inspected.',
    'argv': ['node', '/Users/igorrivin/.codex/plugins/cache/openai-curated-remote/sites/1.1.2/scripts/package-site.mjs',
             str(MIRROR), str(RAW / 'offline-sites-preview.tar.gz')],
    'cwd': str(MIRROR), 'environment': {'COPYFILE_DISABLE': '1'}, 'returncode': 0,
    'archive_sha256': ARCHIVE_SHA, 'archive_bytes': 2778427,
    'publication': 'Offline packaging only. No source push, saved version or deployment.'}
write_json(RAW / 'offline-package-command.json', command)
state = dict(native['after_packaging_get_site'])
assert state.pop('id') == PROJECT
state.update({'project_id': PROJECT, 'registered_status': state.pop('status'),
              'status': 'registered_owner_private_unpublished_after_offline_packaging',
              'recorded_at_utc': native['recorded_at_utc'],
              'source': 'native-sites-state.json, whitelisted record of the root native tool results',
              'source_record_sha256': digest(RAW / 'native-sites-state.json'),
              'site_source_commit': None, 'saved_version_id': None, 'deployment_id': None,
              'active_means': 'The registration exists; no live or preview deployment URL exists.',
              'dns_blocker': native['source_open']['error']})
write_json(RAW / 'site-status-after-packaging.json', state)

evidence = [
    'checkpoint_prepare.py', 'checkpoint_build.py', 'checkpoint_archive.py',
    'checkpoint_closeout.py', 'final-postcommit-verification.py',
    'source-staging-manifest.json', 'source-staging-verification.json',
    'source-whitespace-review.json', 'source-commit.json', 'source-commit.log',
    'final-preview-build-command.json', 'final-preview-build.log',
    'final-search-checks-command.json', 'final-search-checks.log',
    'final-dist-metadata-cleanup.json', 'final-export-verification.json',
    'final-archive-verification.json', 'parent-prepackaging-verification.json',
    'parent-offline-package-verification.json', 'parent-package-check-history.json',
    'native-sites-state.json', 'site-status-after-packaging.json',
    'offline-package-command.json']
copies = []
paths = []
for name in evidence:
    source = RAW / name
    destination = CHECKPOINT / name
    assert not destination.exists(), str(destination)
    destination.write_bytes(source.read_bytes())
    assert digest(destination) == digest(source)
    copies.append({'source': str(source), 'destination': str(destination),
                   'sha256': digest(source), 'bytes': source.stat().st_size})
    paths.append(str(destination.relative_to(ROOT)))
artifacts = ROOT / 'artifacts/sites-preview'
artifacts.mkdir(exist_ok=False)
archive = artifacts / 'polyhedra-sites-preview.tar.gz'
archive.write_bytes((RAW / 'offline-sites-preview.tar.gz').read_bytes())
assert digest(archive) == ARCHIVE_SHA
copies.append({'source': str(RAW / 'offline-sites-preview.tar.gz'), 'destination': str(archive),
               'sha256': ARCHIVE_SHA, 'bytes': archive.stat().st_size})
paths.append(str(archive.relative_to(ROOT)))
manifest = {
    'status': 'verified_offline_candidate_not_published',
    'research_source_commit': SOURCE, 'research_source_dirty_at_export': False,
    'numerical_source_commit': 'c1f100b957166b93eca0d214586322d5af71b9cf',
    'archive': {'path': str(archive.relative_to(ROOT)), 'sha256': ARCHIVE_SHA, 'bytes': archive.stat().st_size},
    'preview_manifest_sha256': export['preview_manifest_sha256'],
    'project_id': PROJECT, 'site_source_commit': None, 'saved_version_id': None, 'deployment_id': None,
    'archive_members': review['member_count'], 'archive_regular_files': review['file_count'],
    'preview_payload_files': 49, 'official_hosting_manifest_files': 1,
    'scientific_inputs_unchanged': 46,
    'archive_verification': 'docs/execution/sites-preview-2026-11-01/final-archive-verification.json',
    'archive_verification_sha256': digest(RAW / 'final-archive-verification.json'),
    'format_metadata': review['pax_scope'],
    'sidecar_files_symlinks_traversal_duplicates_and_extra_payloads_absent': True,
    'local_index': str(MIRROR / 'dist/index.html'),
    'site_status': 'Registered owner-private, version zero, no live or preview URL; Git-host DNS blocks source synchronization.',
    'browser_verification': 'Not performed.',
    'scientific_generation': 'Existing reports, PDF, code, figures and reproduction ZIPs copied unchanged; no numerical replay or PDF rebuild.',
    'scope': 'Section 9 reading preview; the full monograph source download remains a broader draft.'}
write_json(artifacts / 'manifest.json', manifest)
paths.append('artifacts/sites-preview/manifest.json')
(artifacts / 'README.md').write_text('''# Offline Sites preview candidate

[Download the candidate](polyhedra-sites-preview.tar.gz) and see its
[manifest](manifest.json) and [checkpoint closeout](../../docs/execution/sites-preview-2026-11-01/closeout.md).
The archive contains the 49 preview files and the official minimal hosting
manifest. Its SHA-256 is
`9425c791ecb0f7d88f91aae8b19dfb7d30c6526446b103cf6415e79734007cd1`.

This is an inspected offline candidate. The registered owner-private Site has
no saved version or deployment; source synchronization failed at Git-host DNS.
The official archive retains its recorded macOS provenance PAX headers and has
no metadata sidecar payload files. Browser rendering and interaction remain
unchecked. No numerical calculation or PDF build was repeated for this export.
''')
paths.append('artifacts/sites-preview/README.md')
write_json(CHECKPOINT / 'final-copy-manifest.json', {
    'scope': 'Bytewise copies of source-commit, clean-export, official-package, independent archive and native-state evidence plus the unchanged offline candidate.',
    'copied_at_utc': datetime.now(timezone.utc).isoformat(), 'files': copies})
paths.append('docs/execution/sites-preview-2026-11-01/final-copy-manifest.json')

(CHECKPOINT / 'README.md').write_text('''# Section 9 Sites reading preview

The [offline reading preview candidate](../../../artifacts/sites-preview/README.md)
is built and independently inspected. It adds a six-subsection contents list,
local passage search and shared navigation to the reviewed Section 9 chapter
and its two computational companions. The [closeout](closeout.md) records the
source commit, archive identity, verification and continuation steps.

The PDF, numerical reports, figures, code and reproduction ZIPs retain the
frozen scientific bytes from the [barrier checkpoint](../section9-barrier-2026-10-31/README.md).
The three derived HTML pages differ only by two reversible presentation inserts.
This presentation increment includes no new computation, PDF build or proof audit.
The complete LaTeX download is the broader draft; Section 9 review does not
extend to the rest of the monograph.

The [independent review](independent-review.md) approves the nine source hashes.
Its checks include 25 site tests, pure search assertions, real-edition queries,
473 local/search targets, 204 passages, 209 original MathML nodes and exact HTML
restoration. Initial path, symlink and directory-link findings remain preserved
in the [evidence inventory](evidence-copy-manifest.json). The
[clean export](final-export-verification.json) and [actual archive inspection](final-archive-verification.json)
agree on all 49 payload files. Browser rendering and interaction were not tested.

The [native Site record](native-sites-state.json) confirms an owner-private
registration with version zero and no live or preview URL after packaging.
The official source helper failed because `git.chatgpt-team.site` could not be
resolved. No source push, saved version or deployment occurred. The expected
registration URL is not a verified live URL. No credentials are stored here.

The derived checkout is outside the research repository at
`/Volumes/Lexar/lambda/devel/polyhedra/publishing/polyhedra-reading-preview-20261101`.
Its `dist/index.html` is the local entry point. Resume the supported Sites
source workflow for the existing project only after network recovery, as
described in the closeout. An offline archive is not a saved Sites version.
''')
paths.append('docs/execution/sites-preview-2026-11-01/README.md')
(CHECKPOINT / 'closeout.md').write_text('''# Sites reading preview closeout

The Section 9 reading preview is complete as a local, reviewed presentation
increment. It has a contents page, local passage search and navigation between
the chapter and its two computational companions. The [candidate archive](../../../artifacts/sites-preview/polyhedra-sites-preview.tar.gz)
is ready for the supported Sites workflow when source synchronization becomes
available. It has not been saved or deployed to Sites.

The clean research source commit is
`e79d4cee5b9fd7f999054617406ecebb1b9677cd`, directly after baseline
`800219f78bdacaf77639cf4d38ff27d4b7342faa`. The separate artifact/closeout commit
follows it; its final HEAD and postcommit checks are recorded outside the
checkout in `../execution/sites-preview-2026-11-01/final-postcommit-verification.json`.
The [verifier](final-postcommit-verification.py) avoids recursive final-HEAD
records in committed documents. The original source review is retained unchanged.

The [independent source review](independent-review.md) approved the final nine
source hashes with no unresolved finding after the path, symlink and explicit
index-link corrections. It ran 25 site tests, pure search assertions and six
real-edition queries, and checked all 473 local/search targets, 204 passages,
209 MathML nodes, two figures and the six subsections. The two new presentation
inserts can be removed from each derived chapter/companion HTML file to recover
its frozen input byte for byte. Initial failures and correction evidence remain
in the [source evidence inventory](evidence-copy-manifest.json).

The [final clean export](final-export-verification.json) records the source
commit above with `dirty: false`, separately from numerical source commit
`c1f100b957166b93eca0d214586322d5af71b9cf`. Its 48 payload files match the approved
draft; the 49th file is the clean-source preview manifest with SHA-256
`457f11d89ca415095ab80906abd501e014afc187744f6b70a3effcb42585f1dd`.
The final link/target and search checks passed while the research checkout
remained clean. All 46 scientific inputs retain their frozen bytes, including
PDF SHA-256 `9db08eec8405c637c8ac79ad0afcaaa4b4bf810435463dbb3361fee7616975f0`.
No numerical replay, scientific export, PDF build or PDF inspection was repeated.

The [generated metadata record](final-dist-metadata-cleanup.json) preserves the
paths, headers, hashes and sibling identities for 68 AppleDouble sidecars removed
only from the generated mirror `dist`. Genuine payload hashes were unchanged.
The actual directory contained exactly 49 ordinary files before packaging; no
symlink, extra payload, Git directory or metadata sidecar remained there.

The root agent ran the [official offline packager](offline-package-command.json)
with `COPYFILE_DISABLE=1`. Its unchanged 2,778,427-byte archive has SHA-256
`9425c791ecb0f7d88f91aae8b19dfb7d30c6526446b103cf6415e79734007cd1`.
Both the [parent check](parent-offline-package-verification.json) and the
[independent archive inspection](final-archive-verification.json) verified the
actual 71 tar members and 50 regular files: all 49 clean-export files plus the
official minimal `dist/.openai/hosting.json`. Validated files were safely
extracted outside the checkout and rehashed. There are no duplicate, traversal,
symlink, hardlink, extra-payload or sidecar-file members. The normalized hosting
manifest identifies the existing project and `static.directory: dist`.

The official macOS archive retains `mtime`,
`LIBARCHIVE.xattr.com.apple.provenance` and
`SCHILY.xattr.com.apple.provenance` PAX headers. Their value hashes are recorded;
these format headers are not claimed absent. The parent's first checker rejected
all xattr headers too broadly; its [correction history](parent-package-check-history.json)
is preserved. The corrected checks permit only these exact three keys. The
official archive was not rewritten or stripped.

The existing Site is `appgprj_6ae6b5b94abc8191aa00dfe244adcf37`, titled
*Polyhedra, Moduli, and Quantum Geometry*. The [fresh native observation](native-sites-state.json)
after packaging confirms owner role, custom access, one allowed owner, zero
groups, version zero, and null live/preview URLs. Registry status `active`
means registered. The official source-open helper failed with exit 128 because
`git.chatgpt-team.site` could not be resolved. It initialized an unborn mirror
Git checkout but performed no source push. There is no Sites source commit,
saved version or deployment; the research source SHA is not a substitute.
No token, credential, bypass secret or authentication header is retained here.

After actual network recovery, reuse the same project ID. Re-read Site access,
obtain a fresh source write credential, and run the supported source workflow
in the existing derived mirror. Verify the resulting source push and package,
then save/deploy the exact candidate privately while access remains owner-private.
Do not recreate the Site or present its expected registration URL as live.
Browser rendering, interaction and accessibility checks remain unperformed;
static checks and safe archive extraction do not establish those outcomes.

The final verifier checks the nine reviewed source hashes, 46 scientific files,
953 original tracked files, original repository heads and ancestry, original
archive and supplied reference PDF. All scientific, history, original-source
and earlier-checkpoint trees remain unchanged. Only the root README gains a
navigation link to this checkpoint. No canonical Git remote or push was added.
If new canonical `.git` sidecars exist, the verifier removes only header- and
table-verified AppleDouble files and records cumulative batches with unchanged
genuine siblings. It requires ordinary `git fsck --full` to exit zero with
empty stderr, preserves informational dangling objects, and then requires
`git fsck --full --no-dangling` to have empty diagnostics. No genuine objects or
refs are deleted to suppress notices. The final receipt records the results.
''')
paths.append('docs/execution/sites-preview-2026-11-01/closeout.md')
readme = ROOT / 'README.md'
text = readme.read_text()
anchor = '- [Computational status]'
assert text.count(anchor) == 1
text = text.replace(anchor, '- [Sites reading preview](docs/execution/sites-preview-2026-11-01/README.md): reviewed navigation and passage search, with an inspected offline candidate. The owner-private Site is registered but unpublished because source synchronization is blocked by Git-host DNS.\n' + anchor)
readme.write_text(text)
paths.append('README.md')

paths = sorted(paths)
expected = {name: digest(ROOT / name) for name in paths}
normal = []
ignored = []
for name in paths:
    result = subprocess.run(['git', 'check-ignore', '-q', '--', name], cwd=ROOT)
    assert result.returncode in (0, 1)
    (ignored if result.returncode == 0 else normal).append(name)
approved = json.loads((RAW / 'author-final-manifest.json').read_text())['source_sha256']
for name, value in approved.items():
    assert digest(ROOT / name) == value
write_json(RAW / 'final-staging-manifest.json', {
    'parent_source_commit': SOURCE, 'normal_paths': normal, 'explicit_ignored_evidence': ignored,
    'sha256': expected, 'reviewed_source_hashes_unchanged': len(approved),
    'navigation_documentation': ['README.md'],
    'scope': 'Offline candidate, current checkpoint closing evidence, and one root navigation link only.'})
print(json.dumps({'status': 'final_local_artifact_and_closeout_prepared',
                  'paths': len(paths), 'copied_evidence_and_archive': len(copies),
                  'explicit_ignored_evidence': ignored, 'archive_sha256': ARCHIVE_SHA}, indent=2))
