---
name: mt-syntax
description: Generate, edit, repair, optimize, and validate MT .mtsx syntax files and embedded-language bundles using the bundled mt-syntax jar and task-appropriate source and output review.
---

# MT Syntax Skill

Use this skill to create or edit `.mtsx`, diagnose compilation or highlighting
failures, and validate external syntax bundles. Match the workflow to the request:
analysis and read-only review do not authorize edits or require new artifacts.

## Reference Routing

Read the relevant sections, reusing material already in context. These references
and the bundled validator are authoritative for this custom format; do not guess
MTSX syntax from model memory.

- For unfamiliar constructs, consult `references/mtsx-format.md` and
  `references/matcher-semantics.md`. Read them broadly for a new syntax or
  structural redesign; a local edit only needs the affected sections.
- For new syntax or redesign, read `references/design-workflow.md` and
  `references/flat-patterns.md`. Consult `references/color-guidance.md` when
  selecting or changing styles, colors or line backgrounds.
- Before writing or changing regex fragments, read the relevant parts of
  `references/escape-cheatsheet.md` and `references/regex-performance.md`.
- For embedded languages, dependencies, selector mappings or missing-language
  fallback, read `references/embedded-syntax.md`; for opener-dependent closing
  delimiters, read `references/scope-variables.md`.
- For styles, built-ins, comments, brackets, line backgrounds, formatters or
  shrinkers, consult `references/styles-and-builtins.md`.
- Use `references/existing-syntax-map.md` and `references/examples.md` when an
  existing example would resolve a concrete question.
- Choose runtime evidence using the table below. Read the corresponding reference
  only when that capability is needed.
- For errors or report interpretation, consult `references/report-triage.md`;
  for repair scope and the slash-repair helper, read `references/repair-policy.md`.

## Workflow

1. Establish the requested behavior and affected rules. For a bug, reproduce the
   failure when possible; for a new syntax, make a compact feature-to-matcher
   plan. Resolve uncertain language facts from authoritative documentation.
2. Read and edit the relevant source in place, preserving unrelated work and
   existing coverage. For attachments, use a task-local copy and keep the original.
   Honor explicit paths; reuse existing samples and dependency files.
3. Select evidence that answers the task. For highlighting changes, render a
   representative final sample and run existing relevant suites. Add focused
   assertions for durable regressions when useful; do not create a suite for
   every small edit. Use the capability table for additional evidence.
4. Review results against the intended behavior. During diagnosis, use focused
   checks instead of repeating every mode. After the final behavior change,
   complete the required sample/output review and rerun affected validation.
   Retry with a new diagnosis or correction; when progress stalls, reassess the
   cause and report any remaining blocker rather than repeating unchanged runs.
5. Keep useful machine reports and artifacts. Explain what changed, what was
   actually checked, and any limitations. A separate model-written validation
   JSON is optional; see Evidence And Handoff below.

For analysis-only requests or reading existing results, run tools only to resolve
an actual uncertainty. Prose-comment-only or other demonstrably behavior-neutral
edits do not require a new sample, HTML, diff or suite; version requirements and preprocessor
directives are not merely prose comments. If neutrality is uncertain,
validate the affected behavior. A requested compile-only check may stop at check
mode, with no claim that highlighting was reviewed.

## Choose Runtime Evidence

| Question | Tool and reference |
|---|---|
| Does the syntax compile, or where does compilation fail? | `--check-only`; `references/report-triage.md` |
| Is the resulting highlighting correct? | Render HTML and review the representative sample |
| What style, language or line background applies here? | `--inspect-json` with a point/range; `references/structured-inspection.md` |
| Which rules supplied an unexplained token style? | `--explain-json`; `references/rule-explanation.md` |
| What highlighting changed after an edit? | Full inspections plus `--diff-json`; `references/highlight-diff.md` |
| Did established requirements regress? | Existing relevant `--suite`; `references/sample-assertions.md` |
| Did samples execute the affected rules or branches? | Optional `--coverage-json` or suite `--coverage`; `references/rule-coverage.md` |
| Did performance change? | `--benchmark-json` and `--benchmark-diff-json`; `references/benchmark.md` |
| How do several performance samples compare? | `--benchmark-suite` / `--benchmark-suite-json` and `--benchmark-suite-diff-json`; `references/benchmark-suite.md` |

These are alternatives for different questions, not a checklist to run in full.
Render already compiles and executes the sample, so it does not need a mandatory
preceding check. A sample-bearing check is useful for execution diagnosis without
HTML; its single timing diagnostic is not a benchmark. Counters and explanation
are separate from performance measurement and never establish correctness alone.

Use explanation when source reading leaves token-style ownership unclear. It
already includes point inspection evidence; a separate inspection is unnecessary
if the failing location is known. It does not explain line-background selection.

## Editing And Output Review

- Make the smallest coherent change. Preserve unrelated matcher order, style
  names, dependency mappings and coverage. New-syntax defaults do not justify
  flattening or regenerating an existing file.
- Select regression evidence before editing. Prefer a full inspection baseline
  and diff for matcher-order, boundary, include, embedded-routing or other changes
  with broad effects. A narrow change can use focused assertions and final output
  review. Save baseline HTML additionally when visual before/after comparison is
  useful, not automatically alongside every inspection baseline.
- Baselines must come from the original files. Keep the sample and engine fixed
  for comparisons and retain both source/bundle fingerprints. When the baseline
  cannot execute, preserve its diagnostic and state the comparison limitation.
  New success alone does not prove unchanged behavior elsewhere.
- For local behavior changes, cover the requested case, neighboring boundaries
  and previously correct cases sharing the affected rules. For new syntax or
  redesign, cover introduced matcher families, embedded selectors and fallbacks.
  Do not re-exercise unrelated branches merely because they exist in the file.
- Review the complete final representative HTML against its sample, rather than
  accepting a few correct tokens. Keep samples manageable; focused intermediate
  probes do not replace the original required input for acceptance. For styles
  or line backgrounds, inspect day/night presentation and whole-line coverage.
  Distinguish HTML/source inspection from an actual browser visual check.
- Review new or changed user-authored regexes and directly affected interactions.
  Skip built-ins, `keywordsToRegex(...)` output and unchanged trusted includes
  unless concrete evidence points to them. Use `references/regex-performance.md` for risks.
- Assertions must come from requirements and reviewed examples, not automatically
  from current output. Investigate every relevant failed case; do not weaken
  expectations or remove features simply to pass. Review unexpected diff ranges;
  expand truncated details before claiming all changes were reviewed.

## Authoring Rules

- Keep ordinary new lexical rules flat. Prefer `comment`, `number`, `builtin`
  and `keywordsToRegex` when they fit the language.
- Use `start`/`end` for bounded regions; use `childrenSyntax` for a genuinely
  independent embedded language and direct start `export` / end `var()` for
  opener-dependent delimiters. Do not duplicate a complete child grammar in
  the host or introduce an embedded language for a few ordinary host tokens.
- For new syntax, prefer modest lexical coverage over fragile semantic parsing.
  For edits, preserve coverage unless changing it belongs to the request.
- Preserve parser field order for strict constructs such as `comment`, match
  exports/styles and `group`. In `/.../`, escape every literal slash as `\/`;
  a quoted regex string or fragments may be clearer for slash-heavy patterns.
- Keep newly generated files together unless paths were specified. Preserve
  existing locations for edits. Pass every required custom dependency explicitly
  with repeatable `--syntax-dependency`, in the same order for related runs;
  built-in target languages need no dependency argument.

## Runtime Requirements

- **macOS, Linux, or Windows**: use the same bundled jar and Python launcher.
- **Java 17 or newer**, available as `java` on `PATH`. The bundled
  `lib/mt-syntax.jar` targets Java 17 (class-file version 61.0);
  older runtimes cannot load it. Running the jar needs a Java runtime only;
  Gradle and a Java compiler are not required.
- **Python 3.6+ on macOS/Linux, Python 3.8+ on Windows**, for the launcher's
  capability checks and input/output path protection, and for
  `scripts/repair-mtsx.py`. Windows requires the junction/symlink resolution
  added to `os.path.realpath` in Python 3.8. Only the standard library is needed.
- Skill execution requires **Java and Python only**; Bash, Git Bash, and WSL
  are not required.

Check command resolution with `java -version` and `python3 --version`
(`py -3 --version` on Windows). The launcher invokes `java` from `PATH`;
setting `JAVA_HOME` alone does not select that executable. Confirm the jar starts with
`java -jar <skill-dir>/lib/mt-syntax.jar --engine-info`.

On macOS/Linux, Ctrl+C, SIGTERM, or SIGHUP during the metadata check stops and
reaps the Java child before the launcher exits. After that check, the launcher
uses `exec` for validation: Java takes over the same PID, so hard timeouts and
SIGKILL terminate Java directly. SIGKILL during the metadata check still bypasses
Python cleanup.
On Windows, the launcher uses a Job Object to stop its descendants even if the
Python launcher process is forcibly terminated. If the host prevents Job setup,
the launcher fails before starting Java. Cancellation does not roll back files
already written or guarantee a complete report.

## Validation Commands

Use the bundled jar through the launcher for your platform:

| Platform | Command prefix (from the skill directory) |
|---|---|
| macOS / Linux | `python3 scripts/run-validator.py` |
| Windows PowerShell / Command Prompt | `py -3 scripts/run-validator.py` |

If Windows provides Python 3 as `python` instead of `py`, use
`python scripts/run-validator.py`. Both commands run the same Python entrypoint.
Invoke other Python helpers, including `scripts/repair-mtsx.py`, with the same
Python command for your platform.
Examples below and in references use `python3` and Bash line continuations.
On Windows, use `py -3` (or `python`) and join the continued lines into one command,
removing each trailing `\`.
When invoking from Python, use `[sys.executable, launcher_path, ...]` without a shell;
do not rely on executable permissions or `.py` file associations.
Quote paths containing spaces; relative input/output paths use the current
working directory. The default jar is resolved relative to the launcher.

For example, in PowerShell or Command Prompt:

```text
py -3 scripts/run-validator.py --syntax-file "my syntax.mtsx" --report "check.json" --check-only
```

The launcher defaults to `lib/mt-syntax.jar` and checks capabilities. Do not
build or substitute a project-local jar during normal skill use. If a built-in name is uncertain,
query `java -jar <skill-dir>/lib/mt-syntax.jar --list-syntax`. That list is not a
suffix catalog; use actual `dependencyResolution` to confirm target resolution.

Compile-only diagnosis:

```bash
python3 scripts/run-validator.py --syntax-file lang.mtsx \
  --report lang.check.json --check-only
```

Final bundle render (no separate check required):

```bash
python3 scripts/run-validator.py --syntax-file host.mtsx \
  --syntax-dependency child.mtsx --sample-file sample.lang \
  --html host.html --report host.render.json
```

For an execution check without HTML, use the same inputs with `--check-only`
and a report instead of `--html`. Only sample-bearing check reports include
`SAMPLE_HIGHLIGHT_TIME`. `--code` is useful for quick probes; retain the exact
sample input for reproducible final evidence. One HTML file supports both themes.

## Evidence And Handoff

- For each required invocation, check its exit status, readable current report,
  and expected artifact. Some failures intentionally suppress report writing;
  inspect stderr and report the failure, never reuse old output as current proof.
- Outputs and reports must differ from inputs, dependencies, the running jar and
  each other, including aliases. Use fresh task-owned output paths where practical;
  never delete a user-selected output just to prepare validation.
- Confirm the successful report identifies the intended artifact. Keep engine,
  ordered dependencies, resolution/context information and available fingerprints
  in the original machine evidence. Related results must describe the intended
  input revision; comparisons require the compatibility rules of their mode.
- Retain useful final and failure reports; there is no mandatory report-deletion
  step. Clean up only disposable task-owned probes, preserving evidence used in
  the conclusion. Do not remove user inputs or historical baselines.
- The final reply normally identifies changed files, relevant evidence paths,
  checks/review performed and meaningful remaining limitations. Do not enumerate
  unused modes or claim that compilation alone proves highlighting correctness.
- Create `<name>.validation.json` only when requested or required by an existing
  delivery convention. Follow the optional summary guidance in
  `references/report-triage.md`; link machine evidence rather than duplicating it.
  Not-run or inapplicable steps are not successes, and required failed checks
  must remain visible in the conclusion.
