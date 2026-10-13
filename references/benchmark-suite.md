# Serial Performance Suites

Use this mode when a performance task needs several explicit samples. Required
capabilities: `benchmark-suite` and, for comparison, `benchmark-suite-diff`.
Read `benchmark.md` for fresh-execution timing boundaries, raw rounds, soft run
budgets and measurement noise. Keep behavior assertions in the ordinary
validation suite; a completed performance suite does not establish correctness.

## Manifest And Invocation

```json
{
  "schemaVersion": 1,
  "warmup": 3,
  "iterations": 7,
  "cases": [
    {
      "id": "embedded-example",
      "syntaxFile": "host.mtsx",
      "syntaxDependencies": ["child.mtsx"],
      "sampleFile": "samples/example.txt"
    },
    {"id": "plain-example", "syntax": "Text", "code": "example"}
  ]
}
```

All four top-level fields are required. IDs must be unique nonblank strings.
Each case specifies exactly one of `syntax` / `syntaxFile` and exactly one of
`sampleFile` / `code`. Dependencies require `syntaxFile` and keep their explicit
order. Paths resolve relative to the manifest directory, including symlink/`..`
semantics. No directory scanning, automatic text repetition, per-case repetition
overrides, assertions, coverage or explanation is supported in this manifest.

Limits: 1..100 cases, 0..20 warmup rounds, 1..50 measurement rounds, and at most
2000 requested rounds across the entire manifest (warmup included). These are
workload limits, not a wall-clock deadline.

```bash
python3 scripts/run-validator.py --benchmark-suite performance.json \
  --benchmark-suite-json results.json --report results.report.json
```

Native CLI: `--benchmark-suite performance.json --output results.json`, optionally
with `--report`. Both reject other execution modes, sample/syntax arguments,
queries and CLI repetition overrides; the manifest owns those settings.
The bundled `fixtures/performance-suite.json` is a small executable example.

Run relevant behavior assertions first. Preserve stable case IDs, explicit input
files and order when measuring before and after a syntax edit.

## Execution And Result

Cases run serially in manifest order in one JVM. Each case loads/compiles its own
bundle once and creates a fresh executor for every round. Cases do not share a
compiled program, but JVM JIT/GC and runtime state can affect later cases. This is
not process isolation; preserve order and use the same machine under similar
load. No process hard timeout or whole-command deadline is added.

The result has `schemaVersion: 1`, `kind: benchmark-suite`,
`executionModel: serial-shared-jvm`, manifest path/hash, uniform `config`, `ok`,
`cancelled`, `summary` and ordered `cases`. Each case includes one-based `index`,
`id`, `status`, a nullable `benchmark` and a nullable source-aware `error`.
`benchmark` is the same evidence object used inside a single `sample-benchmark`
artifact, including input/bundle/jar fingerprints, environment and raw rounds.

Statuses:

- `completed`: full measurement succeeded. It does not mean assertions passed.
- `config_error`, `input_error`, `compile_error`: no measurement object; preserve
  the error and source, then inspect other cases.
- `execution_error`: incomplete measurement retained, summary null. Soft run
  budget/regex resource failures stop that case, then continue later cases.
- `canceled`: explicit thread interruption during a case; measurement evidence
  is retained if available. Later cases are `not_run`.
- `not_run`: skipped after cancellation, no measurement. Cancellation before the
  first case can make every case unexecuted.

`summary` contains case count and exact counts by status, not average times or
an overall speedup. `ok` requires every case completed and no cancellation.
Any failure/cancellation returns nonzero with `BENCHMARK_SUITE_FAILED`, while
retaining the current batch artifact. Report `mode` is `benchmark-suite` and its
`suite` field contains the same artifact.

Invalid top-level schema, IDs, limits or unreadable manifest prevent execution.
Per-case configuration failures continue when IDs and manifest structure are
valid. The manifest and every recognizable sample/root/dependency path are
protected before any result/report is written, even for invalid cases. If the
manifest cannot be trusted, fallback report writing stays disabled: inspect
stderr and never treat an old output/report as current. The running jar and
output/report aliases are also protected. Fatal process termination may produce
no current artifact; it is not converted into a completed batch.

## Strict Batch Comparison

```bash
python3 scripts/run-validator.py --before before.results.json --after after.results.json \
  --benchmark-suite-diff-json performance.diff.json --report performance.diff.report.json
```

Native CLI uses `--benchmark-suite-diff --before ... --after ... --output ...`.
This consumes batch artifacts only, not manifests, reports or single-sample
artifacts. Use `--benchmark-diff-json` for single samples.

The strict reader rejects unknown/missing fields, duplicate IDs, inconsistent
indexes, summaries/statuses, resumed execution after cancellation, and per-case
measurement/config/error contradictions. Each embedded measurement passes the
same strict reader as B1; failed prefixes cannot become successful measurements.

Cases pair by ID. Output order follows before IDs, then IDs added in after:

- `added` / `removed`: retain the existing side; comparison is null.
- `not_comparable`: failed/unexecuted cases or incompatible measurement settings,
  inputs, engines or environments; preserve reasons and both sides.
- `comparable`: reuse B1's median delta, percentage, ratio and observation.

The complete ID sequence must match to publish numeric comparisons. Reordering,
adding or removing cases changes the shared-JVM execution sequence and suppresses
all numeric comparisons while retaining ID pairs. A canceled batch likewise
suppresses numeric comparisons. With unchanged order and no cancellation, one
failed/incompatible case does not erase valid comparisons for other cases.
Bundle and source-path changes are allowed; text changes are still incompatible.

The artifact has `kind: benchmark-suite-diff`, `schemaVersion: 1`, `comparable`,
batch-level `reasons`, full `before`/`after` artifacts, per-ID `cases` and a
`summary` containing counts for comparable/not-comparable/added/removed and
faster/slower/equal observations. Case reasons explain individual failures even
when batch-level reasons are empty. There is no cross-sample average speedup,
performance threshold, significance claim or automatic complexity inference.

All cases comparable means exit zero, including observed slowdowns. Otherwise
write the diagnostic comparison and return nonzero with
`BENCHMARK_SUITE_NOT_COMPARABLE`. Malformed/unreadable batch evidence returns
`INVALID_BENCHMARK_SUITE_RESULT` with no new comparison artifact. Report mode is
`benchmark-suite-diff` and `comparison` contains the same result object.
