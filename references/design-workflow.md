# MTSX Design Workflow

Load this before generating a new `.mtsx` syntax. The goal is a useful, stable
highlighter, not a full parser.

## Table of Contents

- Design mindset
- Feature map
- Default matcher plan
- V1 cut line
- Final handoff checklist

## Design Mindset

MTSX is an ordered set of competing matchers. It is closer to a lightweight
lexer than to Tree-sitter, TextMate, or a compiler grammar.

Before writing `.mtsx`, make a short design table:

| Language feature | MTSX shape | Style | Sample text | Notes |
|---|---|---|---|---|
| Line comment | `comment` helper | `comment` | `// hi` | Use helper when possible. |
| Block comment | `comment` helper or `start/end` | `comment` | `/* hi */` | Use `start/end` only for child tokens. |
| Quoted string | built-in or `start/end` | `string` | `"a\n"` | Add escape child matcher. |
| Number | `number` or built-in | `number` | `0x2A` | Prefer built-ins when exact. |
| Keywords | `keywordsToRegex` | `keyword` | `return` | Keep broad identifiers later. |
| Declaration name | `match` groups | custom or `variable` | `fn main` | Only if it adds visible value. |
| Embedded language | host `start/end` + `childrenSyntax` | target syntax | `<script>let x=1</script>` | Keep host boundaries hard; list task-local dependencies. |
| Opener-dependent close | direct start `export` + end `var()` | delimiter style | ```` ```lang ... ``` ```` | Export only short delimiter metadata. |
| Optional line marker | `$` style first; `lineBackground` only for dedicated full-line regex | custom | `.method` | Avoid by default; verify HTML line class when used. |

This table is working context for the agent. It does not need to be written into
the final `.mtsx` file.

## Default Matcher Plan

Use this order unless the language proves otherwise:

1. `comment` helpers or explicit comments.
2. Strings, raw strings, character literals, and escape matchers.
3. Numbers.
4. Keywords, constants, built-in types, and built-in functions through
   `keywordsToRegex`.
5. Declaration or call names when simple capture groups are reliable.
6. Operators and punctuation.
7. Broad identifiers only when they do not hide more precise matches.

Keep the top-level `contains` list flat. Use `defines` to avoid repeating a
small identifier regex or a short matcher set, not to build a recursive grammar.

Flat-first is a default, not a ban on real boundaries. Do not reimplement CSS,
JavaScript, JSON, or another complete language as host matchers; delegate a
bounded body with `childrenSyntax`. Do not approximate a variable-length fence
with a broad regex when the opener capture can safely feed the direct end.

For an embedded bundle, record three additional design facts before writing:

- how the host determines the body end;
- whether the child target is fixed, mapped, defaulted, or intentionally
  missing;
- which task-local `.mtsx` files must be passed as `--syntax-dependency`.

## V1 Cut Line

Prefer under-highlighting over fragile semantic parsing.

Do in v1:

- Highlight lexical categories that are visible in a single line or clear
  bounded region.
- Use `start/end` for strings, block comments, heredocs, or raw strings with
  obvious delimiters.
- Add a custom style only when built-in style names are not enough.
- Add sample coverage for every matcher family you introduce, plus any
  language-specific ambiguity that could plausibly fool the matcher order.
- For embedded syntax, exercise each intended selector, the host boundary, and
  missing fallback. For dynamic ends, include a shorter false closer and a
  repeated delimiter value.

Avoid in v1:

- Full nesting or scope-aware parsing.
- Catch-all identifier matchers before keyword and declaration matchers.
- Large lookbehind or lookahead chains.
- Recursive `include` chains copied from another highlighter without a matching
  MTSX reason.
- One style per sample token unless the language really needs that distinction.

`childrenSyntax` and direct start/end variables are bounded execution features,
not permission to build a general cross-scope data-flow grammar. Keep them at
the exact region that needs them.

## Sample Review

Samples should be realistic enough for a model to judge the rendered HTML, not
just minimal enough to compile. Include representative syntax and, where useful,
self-chosen adversarial probes for identifiers, comments, strings, keywords,
numbers, declarations, nesting, or other boundaries that matter for the target
language.

Do not track a seed for model-written probes. Reproducibility comes from the
sample file that was written to disk.

## Final Handoff Checklist

Identify the syntax, explicit dependencies and representative sample, and link
successful HTML and useful machine reports. Summarize the actual output review,
accepted limitations and relevant embedded/dynamic-boundary coverage. Distinguish
unverified behavior from intentionally unsupported features. Follow SKILL.md for
handoff; a separate model-written validation JSON is only needed when requested
or required by the project's delivery convention.
