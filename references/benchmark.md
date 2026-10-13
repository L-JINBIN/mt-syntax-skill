# Repeatable Single-Sample Benchmark

Use this mode for a slow sample, a performance-focused edit, or a requested
measurement. Do not add benchmarking to every successful validation. Required
capability: `sample-benchmark`. It measures observed performance, not correctness
or a guaranteed speed on another machine.

```bash
python3 scripts/run-validator.py --syntax-file host.mtsx \
  --syntax-dependency child.mtsx --sample-file sample.txt \
  --benchmark-json benchmark.json --warmup 3 --iterations 7 \
  --report benchmark.report.json
```

Native CLI uses `--benchmark --output benchmark.json` and accepts external syntax
or `--syntax Smali` / `--syntax Text`; report is optional there. The wrapper uses
`--benchmark-json` and requires a root syntax and report as usual. Dependencies
retain their explicit order and bundle isolation. Defaults are 3 warmup rounds
and 7 measured rounds; ranges are 0..20 and 1..50 respectively. Invalid integers,
unknown explicit built-in languages, mixed modes, queries, `--max-details`, and
rendering options are rejected. Repetition options require benchmark mode.
For serial multi-sample measurements, read `benchmark-suite.md`. For single-sample
before/after comparison, use the strict evidence comparison below.

## Measurement Boundary

- Read the sample once. Initialize the bundled language registry outside timing.
- Compile one program. External `compilation.elapsedNanos` measures the phase
  that loads/compiles the root and dependencies and prepares language/dependency
  metadata. It includes source I/O and is not a pure compiler microbenchmark.
  Built-ins measure program compilation/metadata after registry loading. Neither
  figure includes JVM startup; initial fingerprint reads are outside timing.
- Every warmup and measured round creates a new ordinary fresh execution and
  runs the complete sample. Execution timing includes executor construction,
  matching, style runs and context construction. Compiled patterns are shared;
  execution-local state and dynamic-end caches are recreated for each round.
- Execution timing excludes compilation, sample/source reads, hashing, HTML,
  inspection serialization, statistics and output writes. Rule coverage and
  explanation are off. Run these separately with the same fingerprints when
  diagnostic evidence is needed.
- Text uses `backend: plain-text`: the default-style run construction path,
  without a syntax program. Do not compare it as if it ran a rule engine.

Timers use monotonic `nanoTime`; nanosecond units do not imply nanosecond
accuracy. JIT, GC, thermal state and other workloads can affect observations.
No forced GC or claim of independent process samples is made. Warmup rounds
are retained as raw evidence but excluded from the measured summary.

The normal syntax execution's fixed 3000 ms **soft run budget** applies separately
to each round. Construction is measured but is outside that budget. Compilation,
I/O and the whole invocation have no new hard deadline. Text has no engine budget.
Do not describe this command as process-isolated or guaranteed to stop within
`rounds × 3 seconds`. Stop investigating a failing sample rather than repeatedly
raising workloads to obtain a success; there is no timeout override in this mode.

## Artifact And Failure Contract

The artifact has `schemaVersion: 1`, `kind: sample-benchmark`, and `benchmark`:

- `scope: fresh-execution`, `backend`, `complete`.
- `input` and `engine`: the same text/bundle/ordered sources and engine fingerprint
  contract as inspection. Rule IDs are not part of performance evidence.
- `environment`: Java version/vendor, VM name/version, OS name/version/architecture,
  available processor count and JVM maximum heap. This is descriptive metadata,
  not a complete hardware or system-load fingerprint.
- `compilation`: scope and elapsed nanoseconds for the separate preparation phase.
- `config`: requested warmup/measurement counts, engine budget and its kind,
  `includesExecutionConstruction: true`, `coverage: false`, `explanation: false`.
- `warmupNanos`, `measurementNanos`: completed rounds in execution order, with
  `warmupCompleted` and `measurementCompleted` counts.
- `summary`: measured-round `minNanos`, `medianNanos`, `maxNanos`, only on complete
  success. An even-sized median is the average of the two central samples.
- `failure`: null on success; otherwise `phase` (`warmup` or `measurement`),
  one-based iteration within that phase and the failed round's `elapsedNanos`.
  `error` retains the CLI error code/message/source.

A warmup or measurement failure stops immediately. The command writes a failure
artifact, returns nonzero, and emits report `mode: benchmark`, `ok: false` with
the same `benchmark`. Completed prefix samples remain available for diagnosis,
but `summary` is null. Never summarize that prefix as a completed measurement or
interpret a timeout's elapsed value as successful execution time.

Invalid arguments, unreadable inputs or compilation failure publish no new
benchmark artifact; use report/stderr. Fatal process termination may also leave
no current artifact. Never reuse an old output after such a failure. Input files,
the running jar, output and report are protected against aliasing.

## Using The Result

1. Preserve representative behavior assertions and establish a valid baseline.
2. Measure the same sample with the same jar and explicit dependency order;
   retain config, environment and all fingerprints alongside the raw rounds.
3. Use source review and optional separate rule counts/explanation to investigate.
   Frequent attempts are not proof that a rule is the runtime bottleneck.
4. After editing, rerun relevant assertions, final representative HTML review,
   and measurement under comparable conditions. Use full inspection diff when
   needed to verify preserved behavior across the rewrite. Bundle hashes may change; preserve
   both and run `--benchmark-diff-json`. A single median improvement is evidence
   to investigate, not a universal
   performance claim or an automatic acceptance gate.

Keep benchmark artifacts and reports with raw rounds and fingerprints; link them
and summarize relevant observations in the handoff or optional summary. This mode
has no P95, coverage gate, performance threshold, automatic size-scaling, or
per-rule timing. It supplements model-led regex review.


## Strict Before/After Comparison

Required capability: `benchmark-diff`. Compare the standalone `sample-benchmark`
artifacts, not report files, inspection exports, or prior comparison outputs:

```bash
python3 scripts/run-validator.py --before before.benchmark.json --after after.benchmark.json \
  --benchmark-diff-json performance.diff.json --report performance.diff.report.json
```

Native CLI uses `--benchmark-diff --before ... --after ... --output ...`, with an
optional report. This is a separate mode from highlight `--diff`; do not supply
syntax/sample inputs, queries, repetition counts, `--max-details`, or other modes.
It reads existing measurements without rerunning the sample.

The strict v1 reader rejects unknown/missing fields, duplicate keys, invalid
fingerprints, noninteger/negative/overflowed durations, inconsistent round counts
and failure positions, and summaries that disagree with the raw measured rounds.
An incomplete measurement is valid diagnostic evidence, but cannot be compared
numerically. Warmup rounds and failed-round elapsed time never enter a summary.

Both results must be complete and have the same text hash/UTF-16 length/encoding,
available jar SHA-256, engine metadata (capabilities as a set), backend, timing
scope, warmup/measurement counts, budget, tracing settings, and every recorded
environment field. There is no override for incompatible conditions. Classpath
fingerprints are readable but not comparable. The comparator's running jar need
not be the measured jar; both measured fingerprints must match each other.
Bundle contents and language names may change; source paths do not determine
comparability. Retain both bundles and use assertions/highlight diff to establish
that behavior still meets the task.

The artifact has `schemaVersion: 1`, `kind: benchmark-diff`, `comparable`, `reasons`,
complete `before`/`after` benchmark objects, and a nullable `comparison`:

- `medianDeltaNanos`: after minus before.
- `medianChangePercent`: `(after - before) / before * 100`.
- `medianRatio`: after divided by before; above 1 means observed slower.
- `observation`: `faster`, `slower`, or `equal`, describing the measured medians.
- A zero baseline gives null percent/ratio and
  `ratioUnavailableReason: zero-baseline-median`; the absolute delta remains valid.

A valid compatible comparison exits zero even when slower. Incompatible or
incomplete evidence writes a diagnostic comparison with `comparable: false`,
nonempty reasons, null `comparison`, and a nonzero exit/report error
`BENCHMARK_NOT_COMPARABLE`. Invalid/unreadable evidence returns `INVALID_BENCHMARK`
and writes no new comparison artifact. Never reuse an old artifact after failure;
check the current report/exit code. Before/after files, the running jar, output and
report are protected against aliasing.

The report uses `mode: benchmark-diff` and includes the same artifact under
`comparison`. Both sides retain min/median/max, raw rounds, preparation timing,
fingerprints and environment. Preparation is a single observation that includes
I/O/metadata work; it receives no performance ratio or regression judgment.

Measure on the same machine under similar load. Equal environment metadata does
not prove identical hardware or load. This comparison has no significance test,
automatic acceptance threshold, or claim of universal speed; repeat controlled
measurements when the observed difference may be noise. Keep timing comparison
separate from rule counters/explanation and behavioral acceptance.
