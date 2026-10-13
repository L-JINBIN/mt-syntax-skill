# Repair Policy

Treat validation failures by blast radius.

## Local Repair

Patch in place when the report points to a small, isolated issue:

- `REGEX_DELIMITER_ESCAPE`: run `scripts/repair-mtsx.py` once, re-check, and repeat at most one more time.
- Missing capture group style index.
- Typo in a style name.
- Missing `start` or `end` on a small bounded matcher.
- Illegal argument ordering such as `recordAllGroups` placement.
- A missing or duplicate `childrenSyntax` selector/include, incorrect local
  field order, or omitted repeatable `--syntax-dependency` argument.
- A direct start export/end `var()` name or group mismatch.

## Reassess Structural Failures

Revisit the diagnosis and affected rules when failures suggest structure problems:

- Circular include chains.
- Many unrelated parser errors.
- Deep recursive matcher structure causing repeated failures.
- Regex design depends on complex semantic parsing.
- The design attempts to carry scope variables through includes, groups, or
  nested matchers instead of one direct start/end scope.
- Embedded-language routing is being approximated with duplicated host rules or
  an unbounded cross-language regex.

Repeated local failures are a reason to inspect the cause and dependency chain,
not proof that the whole syntax needs regeneration. For new syntax or a
requested redesign, revise the design plan when warranted. For existing syntax,
repair the smallest affected structure and preserve unrelated behavior; do not
remove features merely to obtain a compiling file. If the requested behavior
requires a broader change, explain the concrete cause and scope. When it cannot
be completed within the request, report the limitation rather than silently
reducing coverage.

## Slash Repair Limit

`repair-mtsx.py` only escapes unescaped `/` inside a single unique `/.../`
regex literal near `match`, `lineBackground`, `start`, or `end`, including a
direct start regex followed by `export`. It must not convert the regex to a
quoted string, edit `var()` values, or edit comments/string literals.

## Missing Child Languages

A missing `childrenSyntax` target is a valid fallback state, not a compilation
error. Read `dependencyResolution`, `contextSummary`, and any
`CHILD_SYNTAX_MISSING` diagnostic before deciding what to repair:

- If the target is a task-local syntax that should be active, pass its file as
  `--syntax-dependency` to every invocation used for that bundle.
- If the target is intentionally optional, keep the fallback and verify
  `missingStyle` in the final representative output when changing that behavior.
- Do not add an unrelated mapping or silently redirect to a different language
  merely to remove the warning.
