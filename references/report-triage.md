# MTSX Report Triage

Load this when `run-validator.py` returns a report or exits non-zero.

## Table of Contents

- Report shape
- Error codes
- Diagnostics codes
- Evidence and optional validation summary
- Repair loop

## Report Shape

The Java CLI report is a JSON object with stable fields:

```json
{
  "ok": true,
  "mode": "check",
  "engine": {
    "upstreamCommit": "<MT commit>",
    "capabilities": [
      "fresh-execution",
      "children-syntax",
      "competing-children-syntax",
      "scope-variables",
      "external-language-dependencies",
      "syntax-contexts",
      "line-backgrounds",
      "structured-highlighting",
      "highlight-position-query",
      "inspection-fingerprints",
      "highlight-diff",
      "sample-assertions",
      "batch-validation",
      "rule-explanation",
      "rule-coverage",
      "sample-benchmark",
      "benchmark-diff",
      "benchmark-suite",
      "benchmark-suite-diff"
    ]
  },
  "syntaxFile": "lang.mtsx",
  "syntaxDependencies": [],
  "languageName": "Toy",
  "suffixes": [".toy"],
  "output": null,
  "warnings": [],
  "error": null,
  "diagnostics": [],
  "dependencyResolution": [],
  "contextSummary": null
}
```

Rules:

- `ok: false` with `error` means validation failed. For `mode: suite`,
  `SUITE_FAILED` can accompany a complete result artifact containing failed cases;
  read `sample-assertions.md` before handling it as a generation failure.
- `ok: true` means the CLI compile/render path succeeded. The CLI does not
  perform static regex-risk linting; regex quality is reviewed by the model
  against the source `.mtsx`.
- `diagnostics` may contain runtime observations such as sample highlight time
  when a sample is passed to check mode.
- `syntaxDependencies` preserves the repeated `--syntax-dependency` path order.
- `engine` identifies the synchronized MT commit and explicit runtime
  capabilities. Required features should be present before interpreting later
  output.
- `dependencyResolution` contains
  `{reference,resolvedLanguage,missing}` for child-language references found in
  the compiled program, whether or not the sample executes that region. A
  missing target is valid and does not make `ok` false.
- `contextSummary` contains `{contextCount,languages,missingCount}` for the
  sample execution. Check without a sample may legitimately have no contexts.
- `warnings` remains an array of human-readable strings. Structured warning
  identity belongs in `diagnostics`, not in `warnings` objects.
- Missing report output is a validation failure, even when the process printed
  useful stderr.

## Error Codes

| Code | Meaning | Next step |
|---|---|---|
| `MISSING_LANGUAGE_NAME` | External `.mtsx` compiled without a non-blank `name`. | Add `name: ["Language", ".suffix"]`, then re-check. |
| `REGEX_DELIMITER_ESCAPE` | A `/.../` literal likely contains an unescaped `/`. | Run `repair-mtsx.py` once, re-check, repeat at most once. |
| `COMPILE_ERROR` | Parser or compile-time validation failed. | Use `line` and `column`; patch field order, missing groups, style names, or grammar shape. |
| `VERSION_TOO_LOW` | `// require MT` or preprocessor requires a newer MT version. | Remove the requirement only if the generated syntax does not need that feature. |
| `INVALID_ARGUMENTS` | CLI invocation is malformed. | Fix the command; do not edit `.mtsx` first. |
| `INPUT_CHANGED` | Inspection detected changed syntax source during compilation. | Stabilize the source files and rerun inspection; do not accept the old output. |
| `FILE_NOT_FOUND` | Input, syntax, or sample path is missing. | Fix paths or generate the missing sample. |
| `FILE_READ_ERROR` | A benchmark syntax-source fingerprint could not be read. | Inspect the reported root/dependency path and permissions; do not edit the sample to fix it. |
| `RENDER_ERROR` | Compilation passed but sample highlighting or HTML render failed. | Inspect the sample and affected matcher; follow [repair-policy.md](repair-policy.md) to determine the repair scope from the concrete cause. |
| `SYNTAX_TIMEOUT` | The fresh execution exhausted its total syntax budget. | Reduce sample size only for diagnosis, then narrow expensive matcher or boundary design. |
| `REGEX_TIMEOUT` | One regex exhausted its execution budget. | Review the reported path and user-authored regexes for unbounded or ambiguous scanning. |
| `REGEX_RESOURCE_LIMIT` | Regex evaluation exhausted execution resources. | Reduce backtracking complexity; smaller input is only a diagnostic aid. Revalidate the original required input before accepting the repair. |
| `REGEX_STACK_OVERFLOW` | Regex evaluation exhausted stack resources. | Redesign nested/recursive regex structure; do not retry unchanged input. |

If the report itself cannot be written, the CLI prints `REPORT_WRITE_FAILED` to
stderr. Treat that as an automation failure and choose a writable report path.

## Diagnostics Codes

| Code | Severity | Meaning | Response |
|---|---|---|---|
| `SAMPLE_HIGHLIGHT_TIME` | info | Sample highlight elapsed time from sample-bearing check mode. | Investigate large jumps; use repeated comparable runs before claiming a performance improvement, as described in `regex-performance.md`. |
| `CHILD_SYNTAX_MISSING` | warning | The compiled program references an unavailable child language. | Add the intended `--syntax-dependency`, or verify and accept `missingStyle` fallback. |

Do not infer regex quality from missing diagnostics. For new or changed regexes,
use `regex-performance.md` and the task-appropriate output review in SKILL.md.

For `mode: inspect`, output is structured JSON rather than HTML. See
[structured-inspection.md](structured-inspection.md) for coordinates, fingerprints,
and retaining inspection evidence for the handoff.

## Evidence And Optional Validation Summary

Default to keeping machine reports/results and a concise handoff. There is no
required model-written JSON or report cleanup step. Preserve evidence for the
final revision and material failures; do not delete reports merely because they
have been summarized. SKILL.md defines which validation and review the task needs.

For each invocation used in the conclusion:

- Verify exit status, report `ok` and expected current artifact. A successful
  comparison can still report differences; a successful measurement says nothing
  about highlighting correctness. Read mode-specific outcome fields.
- For rendered HTML, resolve the report's `output` and intended HTML path against
  the invocation's working directory and normalize them before comparing. A
  matching basename or an old file is insufficient. On failure or mismatch, do
  not present that file as current successful output.
- Retain the report's `engine`, ordered `syntaxDependencies`,
  `dependencyResolution`, `contextSummary`, diagnostics and warnings as produced.
  Keep available text, bundle and jar fingerprints in their original artifacts.
  Check that combined evidence belongs to the intended revision and inputs;
  do not merge away conflicting metadata. Follow the mode's stricter fingerprint
  requirements for before/after comparison.
- A missing/unreadable required report or failed required invocation cannot be
  represented as success. Some failures intentionally suppress report writing;
  retain stderr and describe the failure. A mode not needed by the task does
  not need to be run simply to populate a summary.

If the user or an existing delivery convention requires `<name>.validation.json`,
write valid JSON that links the original evidence and records the task's required
checks, their actual outcomes, review scope and limitations. Prefer paths and
concise findings over copying whole capability lists and duplicate reports.
Respect an existing consumer's schema when one is specified; do not invent passing
values for omitted steps or silently redefine what that consumer accepts.

Without an existing schema, distinguish `passed`, `failed`, `not_run` and
`not_applicable` per step. An optional overall `ok: true` requires all checks and
reviews needed for the requested claim to have passed; it is not universal
certification of the syntax. Analysis-only work or a compile-only result must not
be labeled as reviewed highlighting. Not-run required validation is incomplete,
not passed; an inapplicable extra mode does not make an otherwise validated task
fail. Identify accepted simplifications without concealing required failures.

## Repair Loop

1. Fix invocation and input-path problems before editing syntax; inspect the real
   failing source, including explicit dependencies.
2. Use check for compilation diagnosis, or the relevant inspection/assertion for
   a behavior failure. Missing child targets may be intentional fallback.
3. Make a focused correction and rerun evidence affected by that correction.
   Do not repeat every mode during each diagnostic iteration. For behavior edits,
   finish with the representative output review and relevant suites from SKILL.md.
4. If progress stalls, revisit the diagnosis and dependency chain using
   `repair-policy.md`. Retry only with a new diagnosis or meaningful correction;
   report unresolved blockers without silently dropping features. The dedicated
   slash-repair helper retains its two-attempt limit.

## Difference reports

For `mode: diff`, read `highlight-diff.md`. `ok: true` means comparison completed;
`comparison.changed` may still be true. `INVALID_INSPECTION` means a malformed or
partial artifact; `INSPECTION_NOT_COMPARABLE` means text, engine or line coordinates
differ. Preserve both fingerprint sets and never treat either failure as no change.
The required engine capability is `highlight-diff`.

## Batch suite reports

For `mode: suite`, read `sample-assertions.md`. `SUITE_FAILED` means the batch
completed with one or more failed cases; inspect the current result artifact and
its per-case status. `INVALID_SUITE` means the manifest could not be accepted.
Report-file writes are suppressed until all suite input paths are protected;
read stderr and do not reuse stale artifacts if validation stopped before that.

## Rule explanation reports

For `mode: explain`, read `rule-explanation.md`. Successful execution retains
`inspection` input and engine fingerprints. Only the standalone artifact holds
the committed write history and field owners; it is not an input for highlight
diff. A failed execution produces no current explanation artifact.

## Rule counter reports

For `mode: coverage`, read `rule-coverage.md`; successful `coverage` includes the
full execution counters and input/engine fingerprints. A suite invoked with
`--coverage` keeps `mode: suite`; read its result artifact for aggregate groups
and included/excluded cases. Complete counters do not imply passing assertions,
and missing or failed execution is never zero coverage.

## Benchmark reports

For `mode: benchmark`, read `benchmark.md`. The report and standalone artifact
carry the same measurement evidence. Failed warmup or measurement produces
`complete: false`, a phase/iteration failure and a null summary; do not treat the
completed prefix as a passing benchmark. Preparation failures produce no new
artifact. Preserve the underlying error code and source file when diagnosing.


For `mode: benchmark-diff`, read `benchmark.md`. `ok: true` means a compatible
comparison completed, including an observed slowdown. `BENCHMARK_NOT_COMPARABLE`
writes the current diagnostic artifact with reasons and both measurements but
no numeric comparison. `INVALID_BENCHMARK` rejects malformed/unreadable evidence
and produces no new comparison artifact. Neither failure means unchanged or
faster. Report `comparison` holds the same object as the standalone artifact.


For `mode: benchmark-suite` and `mode: benchmark-suite-diff`, read
`benchmark-suite.md`. `BENCHMARK_SUITE_FAILED` retains per-case measurement or
preparation errors and unexecuted cases. `BENCHMARK_SUITE_NOT_COMPARABLE` retains
ID pairs and reasons; a slowdown alone does not fail comparison.
`INVALID_BENCHMARK_SUITE_RESULT` rejects batch evidence and publishes no new
comparison artifact. Invalid/unreadable manifests cannot safely enumerate inputs,
so batch execution suppresses fallback report writing until path protection is
complete. Use stderr and do not reuse previous artifacts as current results.
