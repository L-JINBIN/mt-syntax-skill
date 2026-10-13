# Structured Highlight Inspection

Use inspection for exact style/language questions, embedded-boundary diagnosis,
or before/after evidence. Choose a point/range when that answers the question;
full exports are needed for diff. Inspection does not judge language correctness
or explain which matcher won. For automated before/after comparison, read
`highlight-diff.md`.

## Commands

Use the bundled jar through the wrapper. Supply the same dependencies and sample
as other evidence for that revision. Inspection is a separate invocation and
report; it does not require a preceding check or render:

```bash
python3 scripts/run-validator.py \
  --syntax-file host.mtsx \
  --syntax-dependency child.mtsx \
  --sample-file sample.lang \
  --inspect-json host.highlights.json \
  --report host.inspect.json
```

Add exactly one query when full output is unnecessary:

- `--at 24`: zero-based UTF-16 offset.
- `--position 3:5`: one-based line and UTF-16 column.
- `--range 20:40`: UTF-16 half-open range, clipped in the output.

The direct jar equivalent is `--inspect --output host.highlights.json`, with
`--input` instead of wrapper `--sample-file`. Direct CLI also supports built-in
`--syntax` and filename inference. The wrapper is for external `.mtsx` bundles.
Do not combine inspection with `--check-only` or `--html`.

All queries execute the complete input before selecting results. They are not
an incremental parser or a way to evade a timeout. Ranges are bounded by the
input length. Offsets may address either UTF-16 unit of a surrogate pair.
CRLF is one line break; line/column queries address the body and its end position
(first newline character, or EOF). Use `--at` to address the LF inside CRLF.
EOF is accepted as a point but returns no token segment. An empty document has
one empty physical line. A full export includes the trailing empty line after a
newline; an empty range has no token segments.

## Result Contract

`schemaVersion: 1` uses `coordinateSystem: utf16-zero-based-half-open`.

- `selection` records requested `start`, `end`, and nullable `point`.
- `position` is present for a point query and records offset, one-based line and
  UTF-16 column, and `eof`.
- `segments` records clipped `start`, `end`, effective `context` ID, `language`,
  and `style`. A null language means an executed missing child, not host fallback.
- `style` includes the original nullable MTSX `name`, ARGB hex day/night
  foreground and nullable token background, and bold/italic/underline/
  strikethrough booleans. Foreground defaults match the HTML renderer. Null token
  background means transparent; `$` markers are represented as line backgrounds.
- `contexts` records intersecting context nodes and their ancestors, using
  original full-input `id`, `parent`, `start`, `end`, and `language`. The root is
  always included. IDs are local to one execution, not stable rule identities.
- `lines` records selected physical lines with full body `start`/`end`, one-based
  `line`, and nullable `background` (`name`, `day`, `night`). Newline characters
  are excluded from the body. A null theme color means no declared line color.
- `defaults` supplies the renderer's day/night page background and foreground.

Inspect styles, language regions, and line backgrounds together. Identical style
names alone do not prove identical colors or language ownership. Do not compare
context IDs or segment counts as semantic identities. Queries omit source text;
use offsets with the exact sample recorded by the input fingerprint.

## Fingerprints And Reproducibility

`engine` contains `upstreamCommit`, `capabilities`, and `fingerprint`:

- `kind: jar-sha256` with `sha256` hashes the exact executing jar bytes, including
  bundled resources. Fat and ProGuard jars normally have different fingerprints.
- `kind: unavailable-classpath` with `sha256: null` means execution used class
  directories; do not claim complete engine identity from upstreamCommit alone.

`input` contains:

- `textSha256`: SHA-256 of the complete input text encoded as UTF-8, with no
  newline normalization; `lengthUtf16` records its UTF-16 length.
- `language`: the resolved root language.
- `sources`: root external `.mtsx` first, followed by explicit dependencies in
  CLI order; each has a diagnostic `path` and SHA-256 of raw file bytes. Empty
  for a built-in syntax. Concurrent source changes detected during compilation
  fail with `INPUT_CHANGED`.
- `bundleSha256`: SHA-256 of UTF-8 compact JSON `[language, [sourceSha256, ...]]`.
  Paths are excluded so relocating identical files preserves the fingerprint.
  Built-in content is identified by the engine jar fingerprint, not this field.

For comparisons, keep the engine and input text fingerprints fixed. The bundle
fingerprint is expected to change when editing syntax; retain both versions.
Neither matching hashes nor matching output establishes semantic correctness.

## Reports And Handoff

Inspection uses the ordinary success/error report with `mode: inspect`; success
also has `inspection` containing `schemaVersion`, `selection`, `input`, and
`engineFingerprint`. A successful invocation must have `ok: true` and an output
path identifying the current inspection JSON; an old file is not evidence.

Keep the result and report with their fingerprints and selection; link them in
the handoff or optional summary. Record failed inspections without presenting
stale results as current. If inspection is required to verify the requested
behavior, resolve its failure before declaring that behavior validated. For
behavior edits, retain the final representative HTML review from SKILL.md;
inspection-only questions do not require creating HTML.
