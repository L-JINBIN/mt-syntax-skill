# Sample Assertions And Batch Validation

Run existing relevant suites after behavior changes. Add focused assertions for
requirements worth preserving across future edits; a small edit does not require
creating a new suite. Write expectations from the task and accepted examples,
never automatically from current inspection output. A passing suite verifies
only its assertions. Apply the final output and source review appropriate to the
task in SKILL.md; running a suite does not require an extra check invocation.

## Invocation

```bash
python3 scripts/run-validator.py --suite cases.json --suite-json cases.results.json \
  --report cases.report.json
```

Native CLI: `java -jar lib/mt-syntax.jar --suite cases.json --output
cases.results.json --report cases.report.json`. Only the native report is
optional. Required capabilities: `sample-assertions` and `batch-validation`.
Do not combine with generation, inspection, diff, or query arguments. The jar
executes each case fresh with its own explicit dependency bundle; it does not
reuse execution state or search neighboring files for dependencies.

## Suite Schema v1

```json
{
  "schemaVersion": 1,
  "cases": [
    {
      "id": "link-boundaries",
      "syntaxFile": "language.mtsx",
      "syntaxDependencies": ["child.mtsx"],
      "sampleFile": "sample.txt",
      "assertions": [
        {
          "range": [0, 7],
          "text": "rel.plt",
          "notExpect": {"style.name": "urlU"}
        },
        {
          "position": [2, 1],
          "expect": {"language": "JavaScript", "style.name": "keyword"}
        },
        {
          "line": 3,
          "expect": {"background.present": false}
        }
      ]
    }
  ]
}
```

The example illustrates the schema; choose coordinates and expected values that
actually describe the user's sample. The bundled `fixtures/validation-suite.json`
is a runnable canonical suite covering custom dependencies, missing-language
fallback, built-in JSON, UTF-16 positions, and Smali line backgrounds.

- `cases` and each `assertions` array must be nonempty. IDs must be nonempty and
  unique. Unknown fields, invalid types, duplicate JSON keys, unsupported schema
  versions and incompatible options are rejected.
- Each case requires exactly one of `syntaxFile` or `syntax` (an explicit built-in
  name, including `Text`). Unknown built-in names are configuration errors.
- `syntaxDependencies` is an optional ordered path array, only with `syntaxFile`.
- Each case requires exactly one of `sampleFile` or `code` (including empty code).
- All file paths resolve relative to the suite file's directory, not the current
  working directory. Paths are not shell commands and are not expanded as globs.
- Every assertion requires exactly one selector: `at` (zero-based UTF-16 integer),
  `position` ([one-based line, one-based UTF-16 column]), `range` ([start, end),
  both zero-based UTF-16), or `line` (one-based physical line number).
- CRLF is one line break. Token queries at EOF and empty ranges are configuration
  errors, even with negative expectations. A line assertion may target an empty
  line, including the trailing empty line. Use range [1,3] for a two-unit emoji
  starting at offset 1; a point addresses one UTF-16 unit.
- Optional `text` must equal the exact selected substring; for a line it excludes
  newline characters. A mismatch fails the assertion and skips its property
  checks. Use this guard for coordinates that might drift after editing a sample.

Each assertion supplies `expect`, `notExpect`, or both; supplied objects must be
nonempty. All listed fields must satisfy their conditions. `expect` requires
equality throughout the selected range; `notExpect` requires inequality
throughout it. Matching the first character is insufficient.

Token selectors accept these fields:

| Field | Value |
|---|---|
| `language` | Resolved language name, or null for an executed missing child |
| `style.name` | Original MTSX style name, or null |
| `style.dayForeground`, `style.nightForeground` | `#AARRGGBB` |
| `style.dayBackground`, `style.nightBackground` | `#AARRGGBB`, or null |
| `style.bold`, `style.italic`, `style.underline`, `style.strikethrough` | Boolean |

`line` accepts only `background.present` (boolean), `background.name` (string or
null), and `background.day`/`background.night` (`#AARRGGBB` or null). Absent line
background has `present: false` and all other values null. Colors compare
case-insensitively after normalization. These use the shared inspection model;
`$` markers are line backgrounds, not token backgrounds.

## Results And Failures

The result artifact has its own `schemaVersion: 1`, `ok`, `manifest` path/hash,
`summary`, and ordered `cases`. Summary includes case counts by status and
`assertionsPassed`/`assertionsFailed` for assertions actually evaluated. Cases
that fail before evaluation have no assertion results; they never count as
passing. Each case records its one-based index and ID, with status:

- `passed`: all assertions passed.
- `assertion_failed`: execution succeeded but at least one expectation failed.
- `config_error`: malformed case, assertion, duplicate ID or invalid coordinate.
- `input_error`: sample or external syntax/dependency could not be read.
- `compile_error`: syntax compilation failed.
- `execution_error`: fresh highlighting or evidence construction failed.

Ordinary case failures do not stop later cases. Existing engine execution budgets
still apply independently to each fresh execution. There is no new performance
benchmark or whole-suite timing guarantee.

`execution` is the in-memory inspection report, including dependency diagnostics
and, on success, the input/bundle/engine fingerprints in `inspection`. Its `output`
is null because no per-case inspection file is written. For failures before
execution, use the case's `error`. Assertion results include selector, resolved
range, expectations, `ok`, and mismatch details with actual values and ranges.
At most 20 mismatches are retained per assertion; `mismatchCount` remains complete
and `truncated` declares omitted details. Counts are property/segment mismatches,
not a count of bad characters. Text mismatch excerpts are limited to 128 UTF-16
units and explicitly marked when truncated.

The command exits 0 only when every case passed. If cases fail, it still writes
the complete result artifact and returns nonzero; the CLI report has `ok: false`,
`mode: suite`, `error.code: SUITE_FAILED`, and the current artifact path/summary.
Read that artifact to diagnose failures instead of stopping at the first case.

An unreadable, malformed, unsupported or empty suite produces no current result.
Before the suite's referenced paths are known and protected, the CLI suppresses
report-file writes and reports the error on stderr; this also applies to malformed
CLI arguments. Never use old result/report files from such a failed call. Output
and report must differ from the manifest, every referenced sample/root/dependency,
the executing jar, and each other, including aliases.

Retain the suite, current result and report with their status, summary, manifest
hash and per-case fingerprints. Link them in the handoff; a model-written summary
is optional and need not duplicate those fields. Resolve required failures
before reporting overall success. Do not weaken expectations
merely to make a failing implementation pass; update them only when the intended
behavior changed and was reviewed.

For optional rule evidence, add `--coverage` to the suite command and read
`rule-coverage.md`. Per-case reports and the suite artifact then include counts;
complete executions with assertion failures contribute, while earlier failures
are explicitly excluded. This does not change assertion semantics or exit status.
