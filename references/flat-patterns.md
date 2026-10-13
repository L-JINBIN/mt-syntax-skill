# Flat Pattern Defaults

The mt-syntax engine is friendlier to shallow, predictable matcher lists. Default to a flat top-level `contains` array and avoid recursive `include` chains unless the language truly needs them.

## Preferred Shape

1. `comment` helpers for line and block comments.
2. String or character literal `start`/`end` blocks.
3. `number` matcher for numeric literals.
4. `keywordsToRegex` for keywords, builtins, constants, and type names.
5. Simple operator and punctuation matchers.
6. Identifier or declaration matchers only when they add visible value.

## Use `start`/`end` Only For

- Quoted strings with escapes.
- Block comments.
- Multiline raw strings or heredocs with clear delimiters.
- Regions where child highlighting is important and bounded.
- Bodies that are genuinely another language and use `childrenSyntax`.
- Regions whose direct end reuses a short direct-start capture through
  `export`/`var()`.

## Avoid In v1

- Deep nested `contains`.
- Recursive `include` unless copied from a proven existing syntax.
- Catch-all regexes before precise matchers.
- Semantic parsing that depends on large lookbehind/lookahead.
- Manual keyword alternation where `keywordsToRegex` works.

When in doubt, highlight fewer constructs and keep performance stable.

Flat-first applies within one language. It does not justify copying another
language's complete matcher set into a host, and it does not require replacing
a true opener-dependent delimiter with a fragile mega-regex. Keep those cases
bounded and read `embedded-syntax.md` or `scope-variables.md`.
