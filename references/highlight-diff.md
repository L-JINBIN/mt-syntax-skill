# Highlight Difference Review

Use this for requested before/after evidence or behavior changes whose wider
effects need checking, such as matcher order, boundaries, includes or embedded
routing. Narrow edits can use focused assertions and final output review without
a diff. When comparing, use full inspection exports of the same sample produced
by the exact same jar. A separate baseline HTML is only needed for useful visual
comparison. Keep the baseline root and explicit dependencies before editing;
a baseline exported from already edited files cannot demonstrate what changed.

```bash
python3 scripts/run-validator.py --before before.highlights.json \
  --after after.highlights.json --diff-json changes.json \
  --report changes.report.json --max-details 200
```

The native equivalent is `java -jar lib/mt-syntax.jar --diff --before ...
--after ... --output changes.json --report changes.report.json`. No syntax or
sample arguments are accepted. The `highlight-diff` engine capability is required.
The command reads existing artifacts and does not execute syntax again.

## Comparison Contract

- Both inputs must be complete schema-v1 inspection documents. Point/partial-range
  exports, unknown/missing fields, duplicate JSON keys, invalid coverage,
  invalid parent chains and broken references are rejected.
- Text SHA-256 and UTF-16 length must agree. Line coordinates must agree too.
  Newlines are not normalized. There is no general text diff or cross-version
  schema conversion.
- Both engine fingerprints must be available `jar-sha256` values and match;
  engine metadata must also agree. Fat versus ProGuard and classpath-only
  evidence are not interchangeable. If rebuilding changed the jar, regenerate
  both baselines with that jar before comparing.
- Bundle fingerprints may differ, as expected for syntax edits. Source paths
  are diagnostic metadata and do not count as highlighting changes. Both sides'
  input and engine metadata are retained.
- Styles are compared over aligned UTF-16 intervals. Equal effects with different
  run splitting are equal; adjacent identical before/after differences merge.
  Style names, colors, font flags and effective language are distinct fields.
- Context trees are compared by parent structure, original ranges and language,
  ignoring IDs and array order. Complete child subtrees are part of identity,
  so moving children between otherwise identical parents remains visible.
  Repeated identical nodes retain multiplicity.
  Effective language changes are also reported in segment differences.
- Line backgrounds compare their original names and declared day/night colors;
  defaults compare separately. These are structured attribute differences, not
  a pixel diff; transparent/no-color declarations are not composited away.

## Reading Results

Successful comparison exits 0 even when `changed: true`. The ordinary report has
`mode: diff`, `ok: true`, the output path, and a `comparison` summary. A change is
not automatically a regression, and no change is not proof of correct syntax.

The artifact has its own `schemaVersion: 1`, `before`/`after` fingerprints,
`summary`, `details`, `detailLimit`, and `truncated`. Each detail has `kind`:

- `segment`: UTF-16 start/end, changed field paths, and before/after styles and language.
- `lineBackground`: physical line, body range, and before/after background.
- `context`: node range/language, canonical parent key and `subtreeKey`, with
  before/after counts. Subtree changes propagate to ancestor identities and
  their descendants' parent keys; counts describe structural entries, not a
  minimal tree-edit script.
- `defaults`: before/after page defaults.

`summary.byKind` counts normalized changes, not matcher hits. `changedUtf16`
counts only changed segment units, not context-only or line-background changes.
`affectedLineRanges` uses one-based inclusive `first`/`last`; newline characters
belong to the preceding physical line. Statistics cover all changes even when
`--max-details` truncates details (default 200; 0 requests summary only).
If truncated, rerun with a sufficient limit before claiming every change was
reviewed. Context parent keys are structural hashes, not matcher identities.

Failure exits nonzero: `INVALID_INSPECTION` identifies a malformed or partial
input; `INSPECTION_NOT_COMPARABLE` identifies incompatible text, engines or line
coordinates. Neither may be reported as “no differences”. Do not use stale
artifacts left by a failed call. Hashes identify declared evidence; offline
comparison cannot authenticate that a user-edited JSON came from the jar.

Review changes against the requested behavior and investigate unexpected ranges.
For a behavior edit, also review the final representative HTML as described in
SKILL.md; reading existing diff evidence alone does not require a new render.
Retain the diff, input inspections and report, including changed state, summary,
truncation state and both fingerprint sets. Link them in the handoff or optional
summary. Report unavailable or failed baselines explicitly; do not claim
before/after equivalence without valid comparison evidence.
