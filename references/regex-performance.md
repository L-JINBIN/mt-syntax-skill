# Model Regex Review Checklist

Review regexes with model reasoning before writing them into `.mtsx`. This is a
source review step, not a mechanical warning pass from the Java CLI.

## Review Scope

Review new or changed user-authored regex fragments and directly affected
interactions. A local edit does not require reviewing unrelated regexes in the
same file. Relevant forms include:

- `/.../` regex literals.
- Quoted string fragments used as regex patterns.
- `lineBackground`, `match`, `start`, and `end` patterns.
- Regex `defines` within that review scope.
- Static fragments around `var()` in a dynamic end template.

Skip built-ins, generated output and unchanged trusted includes by default,
unless concrete evidence points to them:

- `{builtin: #...#}` matchers.
- `keywordsToRegex(...)` output.
- Unchanged trusted regex fragments reached through `include("...")`.

## Required Checks

- Is it anchored or bounded when scanning large files?
- Can `.*` be replaced with a character class or a delimiter-aware pattern?
- Does a repeated group contain another repeated token?
- Can a keyword alternation become `keywordsToRegex(...)`?
- Does lookaround scan across arbitrary text?
- Does `/.../` contain literal `/` that must be escaped as `\/`?
- Does the pattern work line-by-line unless multiline matching is required?

## Strong Pushback Cases

- Nested unbounded quantifiers such as `(.*)+`, `(.+)*`, or `(\w+\s*)+` over large ranges.
- Cross-line `(?s).*?` without a clear delimiter.
- Large manual alternation of keywords.
- Variable-length lookbehind.
- Broad negative lookahead at every character position.

## Embedded And Dynamic Boundaries

Flat matchers remain the default for one language, but flattening a complete
embedded language into its host duplicates work and changes semantics. Use
`childrenSyntax` when the body is genuinely another language and keep the host
start/end boundary narrow and deterministic.

With `childrenSyntax`, `matchEndFirst` defaults to `true`. In that mode, the host
establishes the end before scanning the body. Review that end pattern as a
large-region boundary: avoid an unbounded ambiguous search when a line anchor,
closing tag, or delimiter-aware class is available.

Explicit `matchEndFirst: false` makes the host end compete with the entire child
root at token boundaries. Review end-pattern cost together with child rules that
can consume end-like text; do not assume the host delimiter pre-bounds their
input. See `embedded-syntax.md` for priority and boundary handling.

Each distinct value inserted by `var()` may compile a dynamic end pattern. A
small execution-local cache handles repeated values, but exported values should
still be short, low-cardinality delimiters rather than identifiers or body text.
The expanded source has a 4096-character limit. `var()` quotes captured text as
a literal atom, so do not add escaping regexes around the dynamic value.

These shapes are not automatically wrong. Keep them when the delimiter,
ordering, and sample coverage make the risk acceptable, and state that decision
in the handoff.

## Safer Rewrites

- Prefer `[^"\n]*` over `.*?` inside strings.
- Prefer `(?m)^[ \t]*...` for line constructs.
- Prefer explicit delimiter alternatives over "anything until later".
- Prefer multiple small top-level matchers over one clever mega-regex.
- Prefer `export`/`var()` over a backtracking approximation when a short opener
  token truly determines the closer; prefer a fixed end regex when it does not.

## Runtime Evidence

For changed regexes, validate the affected sample through the final render or
relevant assertions. A separate sample-bearing check is useful when diagnosing
execution without HTML; do not require it just to collect `SAMPLE_HIGHLIGHT_TIME`.
That single observation is not a warmed benchmark or proof of worst-case safety.

For a slow sample or performance-focused rewrite, use `benchmark.md` for repeated
fresh measurements and strict before/after comparison; use `benchmark-suite.md`
when several explicit samples matter. Keep the same jar, sample and dependency
order, preserve both bundle revisions and record comparable runtime conditions.
Retain raw measurements and reports. If the original times out or hits a resource
limit, report that outcome rather than inventing a baseline duration.

Collect rule counts separately if needed; frequent attempts alone do not identify
the slowest rule. Smaller inputs can isolate a failure but cannot replace the
original required input for acceptance. Recheck that input and the final output
after the repair; reduced coverage is not a performance fix. Use relevant behavior
assertions and the task-appropriate final HTML/difference review from SKILL.md.
