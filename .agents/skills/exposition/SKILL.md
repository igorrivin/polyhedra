---
name: exposition
description: Audit and revise mathematical or technical writing for readers who lack the author's specialist background. Use for unexplained notation, missing motivation, compressed arguments, worked examples, or explanatory diagrams, including whole-document exposition passes. Preserve mathematical claims and their qualifications.
---

# Exposition

Make the reader able to follow the argument and perform a representative calculation. A paragraph that merely names the subject more gently has not supplied the missing explanation.

## Establish the reader and the actual scope

Infer the reader's background from the request and existing material; ask only when the distinction materially changes the revision. State the working assumption. Separate assumed prerequisites from notions the text must teach. An advanced monograph need not become a first course in every subject it uses.

For a whole-document request, inventory the introduction, numbered sections, appendices, boxes, captions and computational guides. Record the source revision and an entry for each requested unit. Read the unit itself, including its proofs and formulas; an opening-paragraph sample or a notation search does not establish that the whole unit was reviewed. Distinguish `reviewed`, `revised`, `example checked`, `rendered`, and `published`. Do not describe a list of issues or a set of new chapter introductions as a completed revision of all the material.

## Diagnose the missing bridge

For each important definition, construction or claim, locate the first point at which a reader would have to guess:

- **Objects and types:** What is the object, and what kind of thing is it: scalar, operator, vector, space, measure, distribution or equivalence class? Define the notation where it first becomes necessary.
- **Bindings and conventions:** Give index sets, ranges, fixed versus varying parameters, units, sign/normalization conventions and dependence on earlier choices. Distinguish an operator from its eigenvalue and a dimensional quantity from its dimensionless label.
- **Purpose:** State the question the construction answers before asking the reader to absorb its formula. Explain why this particular coordinate, quotient, transform or approximation helps.
- **Mechanism:** Identify the actual step that connects two descriptions: change of basis, gluing, change of variables, projection, limit, estimate or external theorem. A citation can support the step without explaining it.
- **Consequence:** Say what the formula lets one compute or infer, and what assumptions are needed to use it.

Recheck local completeness after editing. Boxes and captions should identify their own essential notation even when it was introduced elsewhere. Explain deliberate reuse of a symbol when its meaning changes. A glossary helps navigation but does not replace a definition at first use.

## Revise at the point of difficulty

Insert or rewrite the smallest passage that supplies the bridge. Preserve useful existing material and the author's voice. Avoid attaching the same generic preface to every chapter. For a difficult proof, explain the strategy and the role of the next estimate, then unpack the steps that actually require unfamiliar ideas. Keep precise hypotheses next to the claim they support.

When specialist machinery must remain a prerequisite, name it, give a short working definition sufficient for the present use, and provide a precise route to the necessary background. Do not imply that a sentence has taught an entire theory. Conversely, do not classify a missing elementary explanation as an unavoidable specialist prerequisite.

Read [the revision examples](references/revision-examples.md) when calibrating the difference between naming a concept and explaining it, especially for operator/label notation, sums over states, and unfolding.

## Add an example that does work

Choose a small example that exercises the actual construction or theorem, with admissible inputs and stated conventions. Work from input to output; do not stop at “for example, consider...”. Explain what the example illustrates. A counterexample or failed limiting case can be better than a second routine example.

Check arithmetic and algebra independently when practical: exact arithmetic, a second derivation or an existing trusted implementation. Name the coordinates and normalization. A finite calculation illustrates an asymptotic or global theorem; it does not prove it. Do not invent missing measurements or replace unresolved analytic hypotheses with a numerical tolerance. Add reusable computation when it materially helps verification or exploration; a one-line arithmetic example does not require a new package.

## Draw only what clarifies a relationship

Choose the picture after identifying its teaching purpose: a quotient, a cut and regluing, a change of variables, a geometric constraint, two coalescing critical points or a comparison of scales. Use reproducible mathematical drawing/plotting tools for precise diagrams and exportable figures. Label objects and axes, explain color or line conventions, and say when a sketch is schematic or not to scale. Give an accompanying textual explanation and accessible description. Avoid decorative pictures and pictures that assert a geometric realization not established by the text.

## Preserve meaning and verify the edition

Keep theorem hypotheses, quantifiers, constants, signs, normalization and evidence status intact unless a mathematical correction is explicitly justified. Preserve existing anchors and numbering where feasible. Keep historical computations and review receipts attached to their original source versions. For long manuscripts, use bounded patches and a source comparison so an exposition edit cannot silently rewrite an unrelated proof.

Check citations for new specialist assertions using primary sources. Recompute new examples, compile changed sources, check cross-references, and inspect rendered formulas, boxes and pictures in the actual output formats. Parsing or building alone does not demonstrate that the exposition is understandable. Reread the revised passage using only the stated prerequisites: can the reader explain each symbol, the reason for the construction, and the worked example without guessing?

Close with the changes, their verification and remaining substantive gaps. Keep a per-unit record for a whole-document pass. Publication and external actions follow the user's authorization; this skill does not grant it or add its own approval gate.
