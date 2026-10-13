# Rule Explanation

Use this mode when a reproduced token-style problem remains unclear after source
reading and you need the declarations that supplied the style. Straightforward
source fixes do not require tracing. It executes the complete sample, then
explains one UTF-16 position. Do not run it for every passing case.

```bash
python3 scripts/run-validator.py --syntax-file host.mtsx \
  --syntax-dependency child.mtsx --sample-file sample.txt \
  --explain-json explanation.json --at 12 --max-details 200 \
  --report explanation.report.json
```

Use `--position 2:3` instead of `--at` for one-based line/UTF-16 column.
Native CLI uses `--explain --output explanation.json`; report is optional there.
Required capability: `rule-explanation`. Exactly one point selector is required.
EOF, empty input, ranges and mixed output modes are rejected. Tracing adds work
within the existing execution budget; a traced timeout is not proof that normal
execution would time out. Dependencies retain
CLI order and existing explicit-bundle isolation. Outputs must differ from all
inputs, the executing jar, and each other, including aliases.

## Reading The Evidence

The artifact has `schemaVersion: 1`, `kind: rule-explanation`, and the same
`input`, `engine`, `selection`, `position`, `segments`, `contexts`, `lines` and
`defaults` evidence as the corresponding point inspection. It also contains
`explanation`. It is a separate artifact type: do not feed it into `--diff-json`.
Use ordinary full inspections for before/after comparisons.

`explanation` contains:

- `scope: committed-token-style-writes`: only committed token style operations
  that cover the requested point, in application order. Rolled-back, discarded
  and clipped-away operations are absent.
- `complete: true`: the full input executed successfully and replayed raw style
  matched the actual engine result. This does not mean history is untruncated,
  every alternative was tried, or the expected language behavior is correct.
- `writes`: bounded history, with zero-based `sequence`, `rule`, optional
  `capture` group number, final clipped `[start,end)` range, `operation`
  (`replace` or `merge`), raw `style`, and raw `before`/`after` states.
- `fieldOwners`: each style field points to the last write sufficient to determine
  that field. For accumulated true font flags this is the most recent write
  asserting that flag, not a list of every redundant contributor.
- `finalWrites`: the referenced final writes, retained even when history is
  truncated. Use these to locate declarations for the final foreground,
  background, style name and font flags independently.
- `writeCount`, `detailLimit`, `truncated`: counts cover all committed writes at
  the point. The default detail limit is 200, allowed range 0..10000. If history
  is truncated, rerun with a larger limit when the omitted sequence matters;
  do not claim a complete history if it still exceeds the limit.

A rule has `id`, `language`, `kind` and optional `location`. IDs are scoped to the
same engine/bundle fingerprints, not stable across syntax edits. Location gives
the declaration source, one-based line and **Unicode code-point column**, as
explicitly labeled by `coordinateSystem`. This differs from sample UTF-16
coordinates for supplementary characters. External sources use file paths;
bundled declarations use `classpath:` references. Generated declarations with
no reliable source location report null. Includes retain the original declaration
location; the artifact does not expose a full include call stack.

Raw styles use null for unspecified colors. These inherit during merge or fall
back to renderer defaults; null does not necessarily mean the final foreground
is absent. Raw background colors beginning `#06` are MT line-background markers,
not ordinary token backgrounds. `flags` preserves raw inheritance bits.
Use `segments` for the final visible token style and `lines` for final line
backgrounds. A default replacement belongs to the language root; Text uses a
null rule for global defaults. Rule locations identify the matching declaration,
not necessarily the separate custom style definition supplying its colors.

## Limits And Repair Workflow

This version does not trace line-background rule selection, every failed match,
unchosen candidates, regex backtracking, or performance. A missing rule in the
history does not prove it was unreachable or never matched. Multiple writes can
combine into one final style; do not treat the last whole write as the sole cause.

1. Reproduce the problem and locate it in the exact sample. Explain that point
   using the same syntax dependencies and jar. Explanation already includes
   point inspection evidence, so no separate inspection is needed if the location
   is known. Use inspection and source reading for line-background problems.
2. Read declarations named by relevant field owners; inspect matcher order,
   scope boundaries and includes when the cause remains unresolved.
3. After a correction, rerun relevant assertions and final sample/output review;
   use diff when broader effects need comparison, as described in SKILL.md.
   Explanation is diagnostic evidence, not acceptance.

Only successful full execution publishes an explanation artifact. On timeout or
other failure, read the report/stderr and never reuse an old artifact as current
proof. The report uses `mode: explain` and preserves `inspection` fingerprint
metadata. Keep the explanation and report with their fingerprints when used in
a diagnosis, and link them in the handoff or optional summary. Normal passing
work needs no extra explanation file.
