# Optional Rule Counters

Use counters when deciding which additional samples would exercise edited rules,
custom dependencies or embedded branches. Enable them explicitly; ordinary
check/render/inspect/suite runs do not collect counters. Required capability:
`rule-coverage`. Counters are diagnostic evidence, not an acceptance threshold.

```bash
python3 scripts/run-validator.py --syntax-file host.mtsx \
  --syntax-dependency child.mtsx --sample-file sample.txt \
  --coverage-json coverage.json --report coverage.report.json

python3 scripts/run-validator.py --suite cases.json --suite-json results.json \
  --coverage --report suite.report.json
```

Native CLI uses `--coverage --output coverage.json` for one sample, or
`--suite cases.json --coverage --output results.json` for a suite. Native report
is optional. Single-sample mode accepts external bundles or `--syntax Smali`
(and `Text`), executes the whole sample, and excludes point/range queries,
`--max-details`, HTML, check, inspect, explain and diff modes. The wrapper uses
`--coverage-json` for single samples and bare `--coverage` only with a suite.
Dependencies retain input order and private bundle resolution. Protect all input
files, the jar and output/report paths from aliasing as in ordinary validation.

## Counter Meaning

The inventory is the **compiled reachable rule graph**, including structural and
built-in nodes. It is not every source declaration: unused defines may be absent,
includes may be expanded or shared, and different compiled instances may retain
the same source location. Never merge rules by location alone.

- `attempts`: actual rule-frame entries. Candidates skipped by start-character
  filtering or priority have no attempt; the engine does not force them to run.
- `matches`: successful returns from that rule, including zero-length/EOF
  matches. A later parent failure does not undo a child's successful return.
- `committedStyleWrites`: nonempty style writes in a surviving top-level result
  transaction. Parent rollback, discarded chains and clipped-empty writes do not
  count. Default base-style replacement is excluded. A write later overwritten
  by another rule still counts; this is not final visible ownership or character
  coverage. One match can produce multiple capture/color writes or no writes.

Counts do not measure regex backtracking, elapsed time, source-line coverage,
all possible branches, or line-background rule selection. A zero count does not
prove a rule is dead or defective. Inspect its role, ordering and sample before
adding a targeted case. To identify the final style at a point, use ordinary
inspection and `rule-explanation.md`.

## Single Sample

The artifact is `{schemaVersion: 1, kind: "rule-coverage", coverage: {...}}`.
`coverage` contains:

- `schemaVersion: 1`, `scope: compiled-rule-execution`, `complete: true`.
- `input` text/bundle hashes, ordered external source hashes/paths and language;
  `engine` metadata and fingerprint, using the inspection fingerprint contract.
- `rules`: each `rule` has ID, language, kind and optional declaration location
  (the same source model as explanation), plus `origin` and the three counters.
  Origins are `root`, `dependency`, `builtin` (classpath source), or `unknown`.
  Root/dependency identify external input provenance, not the executing language.
- `summary`: `compiledRules`, `attemptedRules`, `matchedRules`, `writingRules`,
  `unattemptedRuleIds`, `unmatchedRuleIds` (attempted but never successful), and
  `rulesByOrigin` counts. Only present origin categories appear.

Text has a valid empty rule inventory. `complete` means execution completed,
not that samples covered all requirements. Report `mode` is `coverage` and its
`coverage` carries the same evidence. This is not an inspection artifact and
cannot be passed to highlight diff. Keep ordinary inspections for comparisons.

## Suite Aggregation

With `--coverage`, each successful execution report carries per-case `coverage`,
and the suite result gains aggregate `coverage` with:

- `includedCases`: one-based index, ID, status, input fingerprints and group index.
  Both `passed` and `assertion_failed` are included: full highlighting still ran.
- `excludedCases`: index, ID and status for config/input/compile/execution failure
  or absent evidence. Missing execution is never counted as zero coverage.
- `complete`: true only when no cases were excluded; assertion failures can still
  leave coverage complete while the suite's overall `ok` is false.
- `groups`: one group per identical engine metadata/fingerprint and bundle hash.
  Each has `index`, `engine`, `bundleSha256`, `mergeable`, case indices, `summary`
  and summed `rules`. Without a `jar-sha256` fingerprint, each case stays in its
  own nonmergeable group. Do not combine groups or compare IDs across edits.

Group rows also list `attemptedCases`, `matchedCases`, `committedCases` with
nonzero contributions. The representative `rule` comes from the first included
case; `locations` preserves distinct declaration locations across copied bundles.
Use included-case `input.sources` to resolve a specific case's paths. Case indices
refer to the original manifest, not positions within the included list.

## Workflow And Limits

1. Run a representative sample or relevant suite with counters after identifying
   affected declarations. Read excluded cases and fingerprints first.
2. Check the relevant rule IDs and contributing cases, separated by origin.
   Add a meaningful sample/behavior assertion when a requested branch lacks
   evidence; do not manufacture inputs just to increase a percentage.
3. Rerun relevant assertions and review the final representative output after
   behavior edits. Review changed regexes as described in SKILL.md. Positive
   counters cannot establish correct highlighting; collecting them does not
   require an additional check invocation.

Counters add work within the existing execution budget. A counted timeout does
not establish that ordinary execution also times out. Only complete executions
publish usable counters; after failure read report/stderr and do not reuse old
artifacts. There are no partial counters, coverage gates or performance claims.
Retain coverage/results and reports with fingerprints and included/excluded
cases. Summarize relevant findings and link the evidence in the handoff or
optional summary. Do not change the suite exit status based on zero counters or omit assertion failures from the summary.
