"""Prepare publication prose from frozen snapshots; never edit canonical files."""
from pathlib import Path
import difflib
import hashlib
import json
import re

HERE = Path(__file__).resolve().parent
BEFORE = HERE / "snapshots/before"
AFTER = HERE / "proposals"
CHECKPOINT = "docs/execution/counting-mixing-review-2026-11-01/"


def read(path):
    return (BEFORE / path).read_text()


def write(path, text):
    p = AFTER / path
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(text)


def replace(text, old, new):
    assert text.count(old) == 1, old[:160]
    return text.replace(old, new)


def save_json(path, value):
    write(path, json.dumps(value, ensure_ascii=False, indent=2) + "\n")


for p in BEFORE.rglob("*"):
    if p.is_file() and not p.name.startswith("._"):
        write(str(p.relative_to(BEFORE)), p.read_text())

# Only computational prose is added to the approved chapters.
p = "book/chapters/25-global-coefficient-filters.tex"
s = read(p)
s = replace(s, "\n\\clearpage\n", r"""
\paragraph{Finite computational companion.}
The maintained recipe \path{experiments/counting_mixing/run.py} checks
the trace recurrences through power $12$, four rational $SL_2$ word
fixtures, the global weights, finite support selectors, and a formal
length-valued Euler product through length $14$. Its result is
\path{artifacts/counting_mixing/result.json}; the input ranges and
independent review are recorded with the recipe and the checkpoint
\path{docs/execution/counting-mixing-review-2026-11-01/}.
These are exact finite algebraic checks. The formal lengths are not
asserted to come from one hyperbolic metric, and the checks do not
establish the infinite-product convergence, geometric first-atom
theorem, or a sharp counting remainder.

\clearpage
""")
write(p, s)

p = "book/chapters/29-controlled-observables.tex"
s = read(p).rstrip() + r"""

\paragraph{Finite computational companion.}
The companion \path{experiments/counting_mixing/run.py} records exact
finite matrix, inverse-residue, primitive-parity and Fourier checks,
together with one- and two-mark Gaussian comparisons at $60$ and $90$
decimal working digits. It compares the rank-two divisor and logarithm
series with determinant-orbit quadrature and records analytic truncation
bounds separately from measured numerical residuals. The result is
\path{artifacts/counting_mixing/result.json}; its reviewed source and
generation records are in
\path{docs/execution/counting-mixing-review-2026-11-01/}.
These selected formula checks do not certify quadrature or roundoff,
prove the general mixing theorem, or establish the geometric hypotheses
of the nonsquare genus-two model. The finite increase of collinear sums
is an illustration, not the proof of divergence above.

"""
write(p, s)

p = "book/chapters/30-sharp-diagnostics.tex"
s = read(p)
s = replace(s, "dyadic diagnostic using hyperbolic trace recursion on two tori, distinguish\nthe supplied draft's unreplayed numerical report from a new bounded\nreplacement calculation, and provide the latter's computational recipe.", "dyadic diagnostic using hyperbolic trace recursion on two tori. A new\nfull campaign reproduces the supplied draft's counts and rounded block\nvalues through length $8192$, with its own precision and provenance\nrecords; the historical implementation remains unrecovered.")
s = replace(s, r"\subsection{A trace diagnostic: retained report and bounded replacement}", r"\subsection{A trace diagnostic: historical report and new full campaign}")
s = replace(s, "was not included in the supplied materials. The bounded replacement below\nuses binary64 logarithmic recursion and a separate exact-trace oracle.\nNeither calculation provides an interval certificate of every event location.", "was not included in the supplied materials. Both maintained replacement\ncalculations below use binary64 logarithmic recursion, with separate\nmultiprecision trace checks. Neither provides an interval certificate\nof every event location.")
s = replace(s, r"\paragraph{Retained numerical report, awaiting reproduction.}", r"\paragraph{Historical report and reproduced printed values.}")
s = replace(s, "The following selected values are retained verbatim from that report;\nall entries are rounded and have not been reproduced for this edition.", "The following selected values are retained verbatim from that report.\nThe new full campaign below matches both integer counts and every\ndisplayed entry at four decimal places.")
s = replace(s, "Consequently these counts, table entries, precision comparisons, and\nsensitivity bounds remain unreplayed reported results. This edition does\nnot claim that the advertised diagnostic archive accompanies the book.", "The new campaign reproduces the counts and rounded table entries, but\ndoes not recover that implementation, its selected precision comparisons,\nor its sensitivity construction. Those historical precision and\nsensitivity claims remain unverified historical reports. This edition\ndoes not claim that the original diagnostic archive accompanies the book.")
s = replace(s, "The stability claims for this reported long run remain awaiting their\ncomputational evidence.\n\n\\paragraph{A bounded replacement calculation.}", r"""The historical stability claims remain distinct from the new evidence.

\paragraph{A new full campaign through length $8192$.}
The maintained recipe \path{experiments/torus_campaign/run.py} gives
new counts $18\,191\,508$ and $18\,486\,116$ for the two ordered trace
triples. It records every dyadic count and all ten blocks
$T=4,8,\ldots,2048$ for each surface, including the full/half event
sweep, both relevant one-sided limits and simultaneous multiplicities.
The compact result \path{artifacts/torus_campaign/result.json} retains
all twenty block rows, selected paths, residuals, conditional sensitivity
rows and source/input identities. The recipe describes the separately
hashed slope and sorted-length streams and their regeneration. The
checkpoint \path{docs/execution/counting-mixing-review-2026-11-01/}
records independent review and final source/generation identities.

The full campaign is supported by a complete exact-trace comparison
through length $64$, an independent direct-trace traversal and membership
probes through $512$, and selected long-path references. The latter use
$100$ and $140$ decimal digits on $151$ modular and $126$ asymmetric
samples, including $36$ distinct curves near length $8192$ on each
surface. The largest observed difference from binary64 is below
$1.2\times10^{-9}$; this is a sampled residual, not a bound at every
node. Independent review additionally checked long samples by matrix
words at $100$ and $160$ digits and recomputed every dyadic primitive
and signed all-point count from the full stored length streams.
Exact arithmetic on stored binary64 values does not certify membership
or ordering for the true transcendental lengths.

The new sensitivity calculation gives exact rational envelopes for
$M(T)$ conditional on an error at most $10^{-6}$ in each listed length.
Its maximum envelope widths across all ten blocks are below
$1.232\times10^{-6}$ and $5.613\times10^{-7}$, respectively.
These conservative bounds differ from the historical reported
construction and must not be substituted for its claimed width.
Application to the complete true spectrum also requires completeness
and exclusion of entry by omitted curves under perturbation. The
sampled precision checks certify neither hypothesis. The result also
records signed all-point counts and their dyadic differences, in
hyperbolic length units, as used at the end of
Section~\ref{sec:arithmeticgeometry}.

\paragraph{The frozen length-$64$ predecessor.}""")
s = replace(s, "The maintained recipe \\path{experiments/section30/run.py} performs a new\ncalculation", "The earlier recipe \\path{experiments/section30/run.py} records a frozen\ncalculation")
s = replace(s, "This is a replacement\nexperiment, not a reconstruction of the missing length-$8192$ run.", "This was the first bounded replacement\nexperiment; its code, README and result retain their earlier bytes.")
s = replace(s, "statistics are recorded in \\path{artifacts/section30/result.json}, with\nthe source identity and precision settings. The new block values are", "statistics are recorded in \\path{artifacts/section30/result.json}, with\nthat run's source identity and precision settings. Its block values are")
write(p, s)

p = "book/chapters/31-arithmetic-remainder.tex"
s = read(p).rstrip() + r"""

The full campaign \path{experiments/torus_campaign/run.py} implements
this signed-multiple diagnostic at its dyadic cutoffs, with the all-point
rows and differences in \path{artifacts/torus_campaign/result.json}.
The floor comparisons use exact rational representations of the stored
binary64 lengths. Membership for the true geodesic lengths remains
numerical; the exact identity does not certify the required length or
completeness assumptions. The campaign uses hyperbolic lengths
$\ell_\gamma$ without rescaling. If
$s_X$ is the shortest hyperbolic length, the unit-shortest-vector gauge
uses $\lambda_\gamma=\ell_\gamma/s_X$ and hence
$A_B(L)=A_{\rm hyp}(s_XL)$. The campaign's hyperbolic dyadic rows must
be interpreted with that change of units; they do not establish a
uniform logarithmic bound. The separate finite companion
\path{experiments/counting_mixing/run.py} checks rational examples of
M\"obius inversion, signed multiples, row selectors, finite dyadic
identities and conditional balance exponents. These finite checks do
not supply either the required geometric modulus or an arithmetic
hypothesis. Source, independent-review and generation records are in
\path{docs/execution/counting-mixing-review-2026-11-01/}.

"""
write(p, s)

# Ledger additions preserve every claim ID, label and mathematical status.
common_computation = {
    "code_path": "experiments/counting_mixing/",
    "result_path": "artifacts/counting_mixing/result.json",
    "checkpoint": CHECKPOINT,
    "review_record": CHECKPOINT + "computation-review/revision-v2/review-v2.md",
    "approval_manifest": CHECKPOINT + "computation-review/revision-v2/approved-manifest-v2.json",
    "approval_manifest_sha256": "c059cf9591f534bb6517486389b111c79fdff77531b192cbfab846021bd6536e",
    "approved_source_set_sha256": "4b1f8f22f155c464f0ecda6ab95c581926db157bae4ee7583e67fbc6448ded63",
    "independent_review_status": "approved_v2_R1_resolved_no_open_findings",
    "reviewer_replay_counts": {"exact": 4054, "numerical_formula_comparisons": 354, "cross_precision_observations": 297, "focused_tests": 38},
    "prior_v1_status": "Initial numerical acceptance was rejected for R1 and is not retroactively approved; its evidence remains frozen.",
    "scope": "Exact finite fixtures and selected 60/90-digit formula comparisons; analytic truncation bounds are separate from uncertified quadrature and roundoff.",
    "generation_status": "Final generation and source identities are recorded separately in the checkpoint; author and reviewer runs retain their own provenance.",
}

p = "book/claims/sections23-25.json"
d = json.loads(read(p))
d["revision_review"] = "Author audit followed by independent mathematical approval of the frozen Chapters 23-25 and all 52 claims; integration adds computational prose and evidence metadata without changing proof statements."
d["independent_review"] = {
    "status": "approved_with_written_hypotheses",
    "record_directory": CHECKPOINT,
    "records": [CHECKPOINT + "algebra-review/review-report.md", CHECKPOINT + "algebra-review/approved-hash-manifest.json", CHECKPOINT + "algebra-review/source-audit.md"],
    "author_is_independent_reviewer": False,
    "scope": "Local derivations, external theorem statements and convention conversions; not complete external-proof, companion-code or PDF approval.",
}
d["snapshot_scope"] = "The snapshot below is the mathematically approved author freeze, before computational integration prose; final integrated source identities are in the checkpoint."
d["computational_companion"].update(common_computation)
d["computational_companion"]["implementation_status"] = "Implemented finite fixture groups are recorded per claim; optional numerical gap illustrations were omitted."
for source in d["sources"]:
    if source["key"] == "WolpertTwist":
        source["independent_review_supplement"] = {
            "url": source["url"] + "#page=1",
            "pin": "Section 3, printed page 134 (cosine sum and signed angles); page 135 (local contribution argument)",
            "record": CHECKPOINT + "algebra-review/source-audit.md",
            "scope": "The independent reviewer recovered the final formula; the author's earlier access-limit note above remains historical.",
        }
algebra_map = {
    "23.14": ["exact.trace_coefficients"], "23.15": ["exact.trace_coefficients"],
    "23.16": ["exact.trace_coefficients"], "23.21": ["exact.SL2_words"],
    "23.22": ["exact.finite_support"],
    "24.04": ["exact.finite_support", "exact.Mobius_lattice"],
    "24.05": ["exact.Mobius_lattice"],
    "24.11": ["exact.finite_support"], "24.12": ["exact.finite_support"],
    "24.13": ["exact.finite_support"], "24.15": ["exact.finite_support"],
    "25.01": ["exact.global_filter"], "25.02": ["exact.global_filter"],
    "25.03": ["exact.global_filter"], "25.05": ["exact.SL2_words", "exact.global_filter"],
    "25.06": ["exact.finite_Euler_convolution"], "25.07": ["exact.finite_Euler_convolution"],
    "25.09": ["exact.finite_Euler_convolution"],
}
for c in d["claims"]:
    cc = c["computational_coverage"]
    groups = algebra_map.get(c["id"], [])
    cc["implemented_result_groups"] = groups
    cc["maintained_companion_execution"] = "finite_examples_recorded_separately" if groups else "no_direct_finite_check_for_this_claim"
    cc["evidence_record"] = common_computation["result_path"] if groups else None
    cc["limit"] = "Finite examples do not prove the general geometric, convergence, source-theorem or asymptotic claim. Planned fixture numbers retain the author's specification provenance."
save_json(p, d)

p = "book/claims/sections26-29.json"
d = json.loads(read(p))
d["revision_scope"] = "Author mathematical audit followed by independent approval of all four chapters and 59 claims; three source/section metadata corrections were independently accepted. External proofs remain cited inputs. Integration changes computational prose and records only."
d["review_status"] = "independently_approved_with_written_hypotheses"
d["independent_review"] = {
    "status": "approved_after_targeted_metadata_repair",
    "records": [CHECKPOINT + "dynamics-review/review-report.md", CHECKPOINT + "dynamics-review/targeted-acceptance-v2.json", CHECKPOINT + "dynamics-review/targeted-acceptance-v2.md"],
    "scope": "All 59 claims and all four unchanged analytic chapters; no claim of complete external-proof, companion-code or PDF review.",
}
d["chapter_source_hash_scope"] = "Chapter hashes above identify the independently approved analytic freeze, before added computational integration prose; final integrated identities are in the checkpoint."
d["computational_companion"] = common_computation
d["computation_status"] = "Maintained finite checks are implemented for the groups recorded per claim. They do not prove general mixing, classify geometric strata, certify numerical errors, or implement every optional author fixture."
dynamics_map = {
    "s26.finite_trace": ["exact.scalar_trace_mixing"],
    "s26.parry_decay": ["exact.scalar_trace_mixing"],
    "s26.scalar_and_roof_obstructions": ["exact.scalar_trace_mixing"],
    "s27.full_rate": ["exact.terminal_exponential_algebra", "numerical.terminal_family"],
    "s27.residue_endpoint_arithmetic": ["exact.Bruhat_residues", "numerical.endpoint_Fourier"],
    "s27.totient_count": ["exact.Bruhat_residues"],
    "s28.global_correlation": ["numerical.affine_Gaussian", "numerical.rank_two_Gaussian"],
    "s28.return_derivative": ["exact.terminal_exponential_algebra", "numerical.terminal_family"],
    "s29.primitive_pole_arcs": ["exact.primitive_parity"],
    "s29.primitive_bound": ["exact.primitive_parity"],
    "s29.rotation_norm": ["exact.Gaussian_algebra", "numerical.affine_Gaussian"],
    "s29.terminal_norm": ["exact.terminal_exponential_algebra", "numerical.terminal_family"],
    "s29.parity_mean_and_scope": ["exact.primitive_parity"],
    "s29.affine_isometry": ["exact.Gaussian_algebra", "numerical.affine_Gaussian"],
    "s29.one_mark_gaussian": ["numerical.affine_Gaussian"],
    "s29.raw_two_mark_divergence": ["exact.Gaussian_algebra"],
    "s29.rank_two_definition_and_norm": ["exact.Gaussian_algebra", "numerical.rank_two_Gaussian"],
    "s29.rank_two_schwartz_norms": ["exact.Gaussian_algebra", "numerical.affine_Gaussian", "numerical.rank_two_Gaussian"],
    "s29.two_mark_gaussian": ["numerical.rank_two_Gaussian"],
}
for c in d["claims"]:
    fc = c["finite_computation"]
    groups = dynamics_map.get(c["id"], [])
    if groups:
        fc.update({"status": "implemented_finite_examples", "result_groups": groups,
                   "code_path": common_computation["code_path"], "result_path": common_computation["result_path"],
                   "limit": "Only the finite fixtures and selected Gaussian formulas are checked. This is not the proof of the full claim, its geometric hypotheses or its analytic tails; numerical residuals do not enclose quadrature or roundoff."})
    elif fc["status"] == "planned_not_executed_in_this_ledger":
        fc["status"] = "optional_fixture_not_implemented"
        fc["limit"] = "The author specification is retained as provenance. No direct maintained finite check of this claim was implemented; its analytic review is separate."
save_json(p, d)

for filename in ["section30", "section31"]:
    p = "book/claims/" + filename + ".json"
    d = json.loads(read(p))
    d["review_scope"] = "Author audit followed by independent analytic approval of the complete local argument and pinned primary-source statements in Chapters 30-31. Numerical and integration review have separate records; recent preprint applications remain conditional."
    d["independent_review"] = {
        "status": "approved_with_written_hypotheses",
        "records": [CHECKPOINT + "arithmetic-review/review.md", CHECKPOINT + "arithmetic-review/review-decisions.json", CHECKPOINT + "arithmetic-review/analytic-claim-review.json"],
        "scope": "All 57 claims in the frozen analytic chapters and ledgers; not a full audit of cited preprint proofs/formalizations, interval certification, or asymptotic inference from finite data.",
    }
    d["status_definitions"]["derivation_checked"] = "Local mathematical derivation checked by author and independent reviewer under the written hypotheses."
    d["status_definitions"]["numerical_check"] = "Finite numerical evidence tied to its own source/result and measured residuals; no interval certification or asymptotic conclusion."
    d["status_definitions"]["reported_unreplayed"] = "Historical implementation or precision/sensitivity report remains unrecovered; any reproduced numerical values are identified separately."
    d["computational_boundary"] = "The prior length-64 source/result remain frozen. A new length-8192 campaign reproduces counts and printed M/Q rows with its own provenance, sampled precision checks and conditional rational sensitivity. True-spectrum membership, every-node errors, asymptotic bounds, recent preprint proofs/formalizations and a flat-normal identification remain unverified."
    d["computational_companion"] = common_computation
    d["torus_campaign"] = {
        "code_path": "experiments/torus_campaign/",
        "result_path": "artifacts/torus_campaign/result.json",
        "review_record": CHECKPOINT + "arithmetic-review/review-decisions.json",
        "generation_record": CHECKPOINT,
        "scope": "New full campaign through hyperbolic length 8192; 18191508 modular and 18486116 asymmetric curves, all twenty block rows, dyadic signed all-point counts and conditional sensitivity.",
        "units": "Hyperbolic length. For unit-shortest gauge, lambda=ell/systole and A_B(L)=A_hyp(systole*L).",
        "historical_boundary": "No recovery of the historical extended-precision implementation, sample selection or sensitivity construction. The length-64 predecessor retains its prior bytes and source identity.",
        "generation_status": "Final repaired-source replay and source identities are recorded separately by the checkpoint; the reviewed v2 author run is not relabeled as a v3 or clean-source run.",
    }
    for c in d["claims"]:
        cid = c["id"]
        if cid == "s30.exact_roots":
            c["code_paths"].append("experiments/torus_campaign/run.py")
            c["evidence_scope"] = "Preserved bounded checks plus fresh campaign exact-root checks for the same two inputs; generation identities are in the checkpoint."
        if cid == "s30.bounded_replacement":
            c["coverage_gap"] = "Frozen earlier length-64 result; the new full campaign is separate evidence, not recovery of the original archive or a uniform true-length error certificate."
        if cid == "s30.historical_long_run":
            c["scope"] = "The historical implementation and its 100-digit, long-path, cutoff-distance and sensitivity comparisons remain unrecovered. The new full campaign separately reproduces the 18191508/18486116 counts and every printed M/Q entry at four decimals."
            c["new_reproduction"] = {
                "status": "new_finite_campaign_separate_provenance",
                "result_path": "artifacts/torus_campaign/result.json",
                "reproduced": ["Both length-8192 integer counts", "All four historically printed M/Q rows at four decimal places"],
                "new_evidence": ["All ten dyadic blocks per surface", "151/126 selected 100/140-digit samples including 36 near-8192 curves per surface", "Independent 100/160-digit matrix-word samples and full stored-stream dyadic count arithmetic", "Exact rational M envelopes conditional on epsilon=1e-6 and completeness/no-entry"],
                "limit": "The worst sampled binary64 difference is below 1.2e-9, not the historical 7.5e-13 claim. Across all blocks the new envelope widths are below 1.232e-6 and 5.613e-7; neither certifies the length-error or membership hypotheses.",
            }
        arithmetic_groups = {
            "s30.normalized_mobius": ["exact.Mobius_lattice"],
            "s30.square_totients": ["exact.Mobius_lattice"],
            "s30.dyadic_inversion": ["exact.dyadic_events"],
            "s30.block_events": ["exact.dyadic_events"],
            "s30.exact_row_divisors": ["exact.row_and_balance"],
            "s31.large_divisor_identity": ["exact.Mobius_lattice"],
            "s31.mobius_area_tail": ["exact.Mobius_lattice"],
            "s31.balanced_power": ["exact.row_and_balance"],
            "s31.all_point_dyadic": ["exact.dyadic_events"],
            "s31.all_point_from_primitive_lengths": ["exact.dyadic_events"],
        }
        if cid in arithmetic_groups:
            c["finite_computation"] = {"status": "implemented_finite_examples", "result_groups": arithmetic_groups[cid],
                                       "result_path": common_computation["result_path"],
                                       "limit": "Exact finite rational examples only; no geometric modulus, infinite-range bound or arithmetic hypothesis is established."}
        if cid in {"s31.all_point_dyadic", "s31.all_point_from_primitive_lengths"}:
            c["campaign_computation"] = {"result_path": "artifacts/torus_campaign/result.json",
                                         "scope": "Signed A_hyp(L)=2 sum floor(L/ell) and A_hyp(2L)-4 A_hyp(L) at finite dyadic hyperbolic cutoffs, using exact comparisons of stored binary64 rationals.",
                                         "limit": "Unit-shortest gauge needs lambda=ell/systole. Stored-length arithmetic does not certify true threshold membership or a uniform asymptotic bound."}
    save_json(p, d)

# Shared status documents describe this completed local review increment,
# while deferring final artifact/source/build identities to its checkpoint.
p = "README.md"
s = read(p)
s = replace(s, "and bounded computational evidence for Section 30. Each increment", "and the locally reviewed counting, mixing and arithmetic arguments of Sections 23–31 with finite companions. Each increment")
anchor = "- [Current Section 15 checkpoint]"
s = replace(s, anchor, "- [Counting, mixing and arithmetic checkpoint](docs/execution/counting-mixing-review-2026-11-01/README.md): nine modular chapters, 168 independently reviewed claims, an [exact finite and 60/90-digit formula companion](experiments/counting_mixing/README.md), and a [new full torus campaign](experiments/torus_campaign/README.md). The new campaign reproduces both length-8192 counts and the four printed M/Q rows, and records all twenty block rows, signed all-point diagnostics, selected precision checks and conditional sensitivity. Finite agreement does not prove general mixing, asymptotic bounds or every-node accuracy; the original torus precision archive remains unrecovered.\n- [Section 15 checkpoint]")
s = replace(s, "The current exact-integrand result path is `artifacts/section15_quantum/result.json`;", "The new result paths are `artifacts/counting_mixing/result.json` and `artifacts/torus_campaign/result.json`; the [counting/mixing checkpoint](docs/execution/counting-mixing-review-2026-11-01/README.md) records independent reviews, final generation, source identities and the integrated PDF separately. The Section 15 exact-integrand result remains `artifacts/section15_quantum/result.json`;")
s = replace(s, "The counting/mixing chapters and the other unrevised sections specified in the plan remain next.", "The remaining chapter reviews are Sections 10–11, 17–22, 32 and Appendix B, followed by cross-chapter and local-release checks.")
write(p, s)

p = "book/README.md"
s = read(p)
anchor = "The [current Section 15 checkpoint]"
s = replace(s, anchor, "The [counting, mixing and arithmetic checkpoint](../docs/execution/counting-mixing-review-2026-11-01/README.md) records independent local review of Sections 23–31 and all 168 claims in four ledgers: [23–25](claims/sections23-25.json), [26–29](claims/sections26-29.json), [30](claims/section30.json) and [31](claims/section31.json). The [finite companion](../experiments/counting_mixing/README.md) checks exact algebra and selected 60/90-digit formulas; the [new full torus campaign](../experiments/torus_campaign/README.md) reproduces both length-8192 counts and all four printed M/Q rows, and adds all-block, signed all-point and conditional sensitivity records. The chapter proofs retain their hypotheses; finite evidence supplies no general mixing or asymptotic theorem, every-node error certificate, or validation of the recent preprints' complete proofs and formalizations. The all-point O(L/log L) target now explicitly requires compatibility with the local row widths.\n\nThe [Section 15 checkpoint]")
s = replace(s, "Section 30's length-8192 report and broader proof dependencies remain outstanding.", "The later counting/mixing increment supplies Section 30's local analytic review and a separately identified full replacement campaign; the original long-run precision archive remains unrecovered.")
s = replace(s, "Sections 1–9, 12–16, 30 and Appendix A.", "Sections 1–9, 12–16, 23–31 and Appendix A.")
s = replace(s, "At the repository root, the current exact-integrand result path is `artifacts/section15_quantum/result.json`; its checkpoint records final generation, source identities and integrated PDF verification separately.", "At the repository root, the new result paths are `artifacts/counting_mixing/result.json` and `artifacts/torus_campaign/result.json`, with the working PDF at `artifacts/counting-mixing-review-2026-11-01/monograph-working-draft.pdf`. The checkpoint records final generation, source identities and integrated PDF verification separately. The exact-integrand result `artifacts/section15_quantum/result.json` retains its earlier identity.")
s = replace(s, "They have not been regenerated for the later Sections 15/30 or normalization revisions.", "They have not been regenerated for the later manuscript revisions, including Sections 23–31.")
s = replace(s, "Sections 23–31's counting and mixing dependencies, the original long torus calculation, and the remaining Sections 10–11, 17–22, 32 and Appendix B still need the review and evidence work specified in the [plan](../INTEGRATION_PLAN.md).", "Sections 23–31 have completed their bounded local analytic review; the new full campaign replaces the missing numerical coverage without recovering the original torus implementation or precision archive. Sections 10–11, 17–22, 32 and Appendix B still need the review and evidence work specified in the [plan](../INTEGRATION_PLAN.md). Cross-chapter consistency and the complete local release remain later gates.")
write(p, s)

p = "book/computational-status.md"
s = read(p)
s = replace(s, "The [current Section 15 checkpoint]", "The [counting/mixing checkpoint](../docs/execution/counting-mixing-review-2026-11-01/README.md) adds independently reviewed Sections 23–31, finite formula checks and a new full torus diagnostic with its own provenance. The [Section 15 checkpoint]")
start = s.index("## Section 30: bounded replacement")
end = s.index("## Further editorial and release work", start)
s = s[:start] + """## Sections 23–31: counting, mixing and arithmetic

The four ledgers cover 168 independently reviewed claims: [52 in Sections 23–25](claims/sections23-25.json), [59 in Sections 26–29](claims/sections26-29.json), [32 in Section 30](claims/section30.json), and [25 in Section 31](claims/section31.json). They retain the distinction between local derivations, external theorem statements, conditional implications and open comparisons. The nonsquare genus-two restriction, endpoint weights and observable norms remain explicit. The all-point `O(L/log L)` target requires the compatible local row-width condition; infinite flatness alone does not provide it. The pinned recent OpenAI and Doan–Li–Nguyen statements were checked, but their complete proofs and formalizations were not audited.

The [finite companion](../experiments/counting_mixing/README.md) supplies these bounded checks:

| Source formulas | Implemented evidence | Limit |
| --- | --- | --- |
| Sections 23–25 trace and coefficient filters | Exact recurrences through power 12, four rational SL₂ word fixtures, global weights, support selectors and finite length-valued Euler convolution. | Formal lengths need not come from one hyperbolic metric; no infinite-product or general first-atom proof follows from the fixture. |
| Sections 26–28 counting and endpoint models | Exact periodic/aperiodic matrix examples, terminal exponential identities, inverse-residue characters and finite Fourier checks. | No general mixing theorem, spectrum, geometric classification or square-tiling/bisector comparison is computed. |
| Section 29 observables | Exact rational primitive/parity counts and Gaussian algebra; one- and two-mark Gaussian formulas, divisor/logarithm series and determinant-orbit quadrature at 60/90 working digits. | Analytic series/integral truncation bounds are separate from uncertified quadrature and roundoff. Finite collinear growth does not prove divergence. Optional rectangle clipping and geometric length-derivative illustrations were not implemented. |
| Sections 30–31 arithmetic | Exact square/diamond Möbius inversion, finite dyadic telescopes and event sweeps, signed multiples, closed row selectors and conditional balance exponents. | No geometric modulus, arithmetic hypothesis or uniform infinite-range estimate is established. |

The result path is `artifacts/counting_mixing/result.json`. Independent review found and required repair of the initial rank-two radial quadrature acceptance, where a tiny signal could pass an absolute tolerance despite poor relative accuracy. The corrected v2 source has independent approval with no open findings: the reviewer's fresh replay passes 4054 exact checks, 354 numerical comparisons and 297 cross-precision observations, and all 38 focused tests pass. The [targeted review](../docs/execution/counting-mixing-review-2026-11-01/computation-review/revision-v2/review-v2.md) and its [approved manifest](../docs/execution/counting-mixing-review-2026-11-01/computation-review/revision-v2/approved-manifest-v2.json) preserve that source identity. This approval does not extend to the rejected v1 numerical acceptance. The final canonical replay and its generation identity have a separate checkpoint record. Neither the earlier nominal pass count nor the repaired comparisons is a total error certificate.

## Section 30: new full torus campaign and frozen predecessor

The [new full campaign](../experiments/torus_campaign/README.md) uses the same two exact trace triples as the [sharp-diagnostics chapter](chapters/30-sharp-diagnostics.tex). It obtains 18,191,508 modular and 18,486,116 asymmetric curves through hyperbolic length 8192 and matches every historically printed M/Q entry at four decimals. The result path `artifacts/torus_campaign/result.json` records all twenty block rows, dyadic primitive counts, signed all-point `A(L)=2 sum floor(L/ell)` and `A(2L)-4A(L)`, selected precision checks and exact rational conditional sensitivity envelopes. Slope identity streams and sorted binary64 length streams have separate hashes and are not index-aligned; the recipe and checkpoint record their retention and regeneration.

The campaign compares the complete length-64 list with an exact-trace oracle at 100/140 digits, validates a moderate length-512 traversal independently, and retains 151/126 selected long samples, including 36 near-8192 curves per surface. The worst selected binary64 residual is below `1.2e-9`. Independent review additionally used 100/160-digit matrix-word samples and recomputed every dyadic primitive and all-point count from all 36,677,624 stored lengths. These are finite sampled comparisons and exact operations on stored binary64 values; they do not certify all true lengths, threshold membership, event order or numerical pruning.

The new rational sensitivity envelopes assume length error at most `1e-6` for each listed curve. Their maximum widths across all ten blocks per surface are below `1.232e-6` and `5.613e-7`. Applying them to the true spectrum also requires completeness and no entry by omitted curves under perturbation. The historical `7.5e-13` long-path precision and `7.1e-7` sensitivity claims retain their historical status; their implementation, sample choice and bound construction remain unrecovered. Reproducing the counts and rounded rows does not reconstruct that missing archive.

The [length-64 predecessor](../experiments/section30/README.md) and its [result](../artifacts/section30/result.json) retain their earlier source and artifact bytes. They record 1104/1127 curves and their own oracle, metric and sensitivity checks. The [historical torus-bundle script](../research/ipoly/v8_torus_bundles.py) concerns three-dimensional bundle volumes and is not the missing counting experiment.

The Section 31 signed-multiple extension uses hyperbolic length units. For systole `s_X`, the unit-shortest gauge is `lambda=ell/s_X`, so `A_B(L)=A_hyp(s_X L)`. The campaign's dyadic cutoffs must be interpreted with that scaling. No finite diagnostic proves an asymptotic linear, sublinear or logarithmic remainder, identifies the required flat rational-normal point, or validates a recent preprint proof.

The [checkpoint](../docs/execution/counting-mixing-review-2026-11-01/README.md) records the analytic and computational approvals, required numerical/parser repairs, final source generation, raw-stream identities and integrated PDF verification separately. The working PDF path is `artifacts/counting-mixing-review-2026-11-01/monograph-working-draft.pdf`. Reviewed author runs retain their actual source states and are not relabeled as final clean replays.

""" + s[end:]
s = replace(s, "Section 30 retains its earlier bounded replacement computation and still requires review of its broader counting dependencies and missing length-8192 evidence. The counting/mixing dependencies in Sections 23–31 and the remaining Sections 10–11, 17–22, 32 and Appendix B still need their corresponding review, modularization and evidence coverage.", "Sections 23–31 now have their bounded local analytic reviews and the finite companions described above. The original torus precision archive remains unrecovered. Sections 10–11, 17–22, 32 and Appendix B still need their corresponding review, modularization and evidence coverage, followed by cross-chapter consistency and complete local-release checks.")
write(p, s)

p = "docs/INTEGRATION_STATUS.md"
s = read(p)
s = replace(s, "The [current Section 15 checkpoint]", "The [counting, mixing and arithmetic checkpoint](execution/counting-mixing-review-2026-11-01/README.md) records completed independent local review of Sections 23–31: nine modular chapters and 168 claims in four ledgers. All 607 labels and 129 bibliography keys are retained. The [finite companion](../experiments/counting_mixing/README.md) checks exact fixtures and selected 60/90-digit formulas; the [new full torus campaign](../experiments/torus_campaign/README.md) reproduces the length-8192 counts 18,191,508/18,486,116 and all four printed M/Q rows, with all twenty block rows and signed all-point diagnostics. The checkpoint records the required rank-two quadrature and native-parser repairs, independent acceptance, final generation and PDF verification separately. The new result paths are `artifacts/counting_mixing/result.json` and `artifacts/torus_campaign/result.json`.\n\nThe new campaign's selected 100/140-digit references have a worst binary64 difference below `1.2e-9`; independent matrix-word and full stored-stream count checks provide separate evidence. Conditional rational sensitivity assumes a uniform listed-length error and completeness/no-entry. Neither finite agreement nor exact stored-value arithmetic supplies an every-node certificate or an asymptotic theorem. The original torus implementation/precision archive remains unrecovered; the length-64 predecessor remains frozen. Recent preprint statements are pinned, while their complete proofs and formalizations remain unaudited and their uses conditional.\n\nThe [Section 15 checkpoint]")
s = replace(s, "The length-8192 torus archive remains unavailable. The next substantive reviews address counting/mixing dependencies in Sections 23–31 and the remaining Sections 10–11, 17–22, 32 and Appendix B.", "The original length-8192 torus archive remains unavailable; the new full campaign supplies separate reproducible numerical evidence. The next substantive reviews address Sections 10–11, 17–22, 32 and Appendix B, followed by cross-chapter consistency and full local-release checks.")
write(p, s)

p = "INTEGRATION_PLAN.md"
s = read(p)
s = replace(s, "The length-8192 torus evidence, broader chapter review and computational coverage, browser verification and publication metadata/licensing remain outstanding.", "The later counting/mixing increment below supplies local review and a new full torus replacement campaign. The original long-run precision archive, remaining chapter coverage, browser verification and publication metadata/licensing remain outstanding.")
s = replace(s, "The [current Section 15 checkpoint]", "The [Section 15 checkpoint]")
anchor = "On 1 November 2026 the user directed that revision continue and upload be the last step."
s = replace(s, anchor, "The [counting, mixing and arithmetic checkpoint](docs/execution/counting-mixing-review-2026-11-01/README.md) completes the bounded local review of Sections 23–31. All nine chapters and 168 claims have independent analytic review, with 607 labels and 129 bibliography keys preserved. The [finite companion](experiments/counting_mixing/README.md) implements exact fixtures and selected 60/90-digit formulas; the [full torus campaign](experiments/torus_campaign/README.md) reproduces both length-8192 counts and every printed M/Q row, recording all twenty block rows, signed all-point diagnostics, selected precision comparisons and conditional rational sensitivity. The checkpoint distinguishes rejected initial quadrature acceptance, repaired code approval, author evidence, final source generation and integrated PDF verification. The result paths are `artifacts/counting_mixing/result.json` and `artifacts/torus_campaign/result.json`; the working PDF is `artifacts/counting-mixing-review-2026-11-01/monograph-working-draft.pdf`. These finite checks do not prove general mixing or asymptotic rates, certify all transcendental events, identify a flat supporting point on the example tori, or validate the recent preprints' proofs/formalizations. The all-point logarithmic target retains its explicit row-width compatibility condition. The original torus precision archive and all frozen predecessor artifacts retain their separate status.\n\n" + anchor)
start = s.index("After closing the current Section 15 numerical-integration and local-evidence gates:")
end = s.index("\n## Recommendation", start)
s = s[:start] + """With the Sections 23–31 local analytic and computational review gates closed:

1. Apply the same claim, convention and computation review to Sections 10–11, 17–22 and 32 and Appendix B before the full-publication gate. Revisit Appendix A only as new cross-chapter dependencies require. Keep introductory explanations consistent with the revised claims and leave open research questions explicit.
2. Reconcile cross-chapter notation, references, figures, introductions and computational links; resolve authorship, credits and licensing; then run the local edition and complete-release gates below. Earlier optional-dependency full-suite limitations remain separate from the focused companion checks.
3. Upload and deploy only after those gates are satisfied. The existing Section 9 exports and Sites preview remain frozen until the final edition is generated and verified. Open research questions remain explicit rather than becoming implicit publication requirements.
""" + s[end:]
s = replace(s, "Preserve the recent-source qualifications already in the book. The cited OpenAI quasi-RH preprints exist; their correctness and formalization coverage were not verified here. Pin cited versions and keep uses conditional. The official [OpenAI math repository](https://github.com/openai/math) itself distinguishes verification stages. Audit the recent Doan–Li–Nguyen version and the remaining foundational references by exact statement and hypothesis before upgrading any source status.", "Preserve the recent-source qualifications already in the book. The Sections 23–31 increment pins and independently checks the relevant OpenAI quasi-RH and Doan–Li–Nguyen theorem statements and their stated hypotheses. Their complete proofs and formalization coverage were not audited; applications remain conditional. The official [OpenAI math repository](https://github.com/openai/math) itself distinguishes verification stages. Further source-status upgrades require their own evidence rather than following from statement inspection or finite computations.")
s = replace(s, "| P0, Section 30 | Reported 18-million-curve enumerations but missing archive | Markoff/Farey enumerator preserving slope multiplicity, stable logarithmic recurrence, dyadic event statistics and sensitivity calculation. Start with small exact/high-precision cross-checks; then replay length 8192 with checkpointed inputs, raw counts, precision evidence and full block tables. |", "| P0, Section 30 | New `experiments/torus_campaign/` length-8192 campaign, all twenty block rows and separately hashed raw streams; frozen length-64 predecessor | Retain the new campaign's reviewed source/generation identity, sampled 100/140-digit and independent matrix-word checks, signed all-point diagnostics and conditional rational envelopes. Original precision provenance remains missing; no every-node certificate or asymptotic claim follows. |")
s = replace(s, "| P1, Sections 23–25 | Finite algebraic identities | Trace/skein polynomial examples, bracelet coefficients, selector obstruction, first atoms and finite Euler-product examples. Exact arithmetic for small cases; finite truncations retain explicit limitations. |", "| P1, Sections 23–25 | Maintained exact trace, word, global-filter, support-selector and finite Euler fixtures in `experiments/counting_mixing/` | Completed bounded coverage; retain formal-length and finite-truncation limitations. General geometry, infinite products and asymptotic counting rest on separate mathematical arguments. |")
s = replace(s, "| P1, Sections 26–29 | Explicit finite models/formulas | Finite Markov count-versus-mixing example, marked-torus endpoint-weight lattice sums, Gaussian two-mark correlation. Check explicit formulas and norms without claiming a numerical proof of general mixing. |", "| P1, Sections 26–29 | Maintained matrix, endpoint-residue, primitive-parity and Gaussian fixtures in `experiments/counting_mixing/` | Completed declared finite checks with reviewed quadrature repair and explicit analytic-tail/numerical-error distinction. Optional rectangle clipping and geometric length-derivative illustrations remain omitted; no numerical proof of general mixing is claimed. |")
s = replace(s, "| P1, Sections 30–31 | Torus enumerator after recovery | Möbius inversion and main-term-free discrepancy diagnostics that show geometric and arithmetic contributions separately. No inference of an asymptotic bound from a finite plot. |", "| P1, Sections 30–31 | Maintained finite Möbius/row/dyadic identities and the full torus signed-multiple extension | Completed bounded formula and diagnostic coverage. Hyperbolic versus unit-shortest gauge units and the geometric/arithmetic hypotheses remain explicit. No uniform bound follows from the finite range. |")
write(p, s)

# Exact reviewable diff and preservation manifest. No canonical writes occur.
manifest = {"status": "proposal_only_not_applied", "files": {}, "claim_invariants": {}}
diffs = []
for old in sorted(BEFORE.rglob("*")):
    if not old.is_file() or old.name.startswith("._"):
        continue
    rel = old.relative_to(BEFORE)
    new = AFTER / rel
    a, b = old.read_bytes(), new.read_bytes()
    manifest["files"][str(rel)] = {"before_sha256": hashlib.sha256(a).hexdigest(), "proposal_sha256": hashlib.sha256(b).hexdigest(), "changed": a != b}
    if a != b:
        diffs.extend(difflib.unified_diff(a.decode().splitlines(True), b.decode().splitlines(True), fromfile="a/" + str(rel), tofile="b/" + str(rel)))
    if old.suffix == ".tex":
        labels = lambda x: re.findall(r"\\label\{([^}]+)\}", x.decode())
        assert labels(a) == labels(b), rel
    if str(rel).startswith("book/claims/"):
        da, db = json.loads(a), json.loads(b)
        invariant = lambda d: [(c["id"], c.get("labels", []), c["status"]) for c in d["claims"]]
        assert invariant(da) == invariant(db), rel
        manifest["claim_invariants"][str(rel)] = {"count": len(da["claims"]), "ids_labels_statuses_preserved": True}
(HERE / "proposal.diff").write_text("".join(diffs))
(HERE / "proposal-manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
print(json.dumps({"files": len(manifest["files"]), "changed": sum(x["changed"] for x in manifest["files"].values()), "claims_preserved": sum(x["count"] for x in manifest["claim_invariants"].values())}, indent=2))
