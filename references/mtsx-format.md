# MTSX Format Generation Reference

This file is the entry point for generating `.mtsx` accepted by the bundled
validator. Load it before writing any syntax file. Load `matcher-semantics.md`
for matcher details,
`styles-and-builtins.md` for style and built-in names, and `examples.md` for
templates and common mistakes.

## Table of Contents

- File shape
- Lexical format rules
- `stringOrRegex` expressions
- Top-level properties
- Core matching flow
- Priority and ordering rules
- `// require MT` and preprocessing
- Generation checklist

## File Shape

Normal syntax files are one object-like compilation unit:

```mtsx
{
    name: ["ToyLang", ".toy"]
    contains: [
        {match: keywordsToRegex("if else return"), 0: "keyword"}
    ]
}
```

`name` is required for external validation by the bundled validator. The first string
is the language display name. Remaining strings are suffixes, usually including
the leading dot.

Grammar permits top-level items in any order, but generation should keep a
stable order:

1. `name`
2. `hide`
3. `ignoreCase`
4. `styles` or legacy `colors`
5. `comment`
6. `bracketPairs`
7. `defines`
8. `lineBackground`
9. `contains`
10. `codeFormatter`
11. `codeShrinker`

Commas are optional because the lexer skips `,`. Use newlines and indentation
for readability; do not depend on commas for parsing.

## Lexical Format Rules

The lexer is strict. These rules come from `SyntaxLexer.g4`:

- `STRING_LITERAL`: double-quoted Java-style string. It normally contains at
  least one character. `""` is accepted only as a `childrenSyntax` mapping
  selector, not as a name, target, style, regex fragment, or include name.
  Supported escapes are Java-style simple escapes, octal escapes, and Unicode
  escapes.
- `REGEX_LITERAL`: slash-delimited regex, for example `/[A-Za-z_]\w*/`. It must
  contain at least one character, cannot span lines, and any literal slash inside
  must be written as `\/`.
- `STYLE_LITERAL`: `#` plus a color value, optionally followed by token
  background with `#` or line background with `$`, for example `#0033B3`,
  `#0033B3#EEEEFF`, or `#0033B3$FFF5D0`.
- `STYLE_FLAGS`: `@` followed by one or more of `B`, `I`, `U`, `S`, or `_`.
  Use `@B`, `@I`, `@BI`, or `@_`.
- `BUILT_IN_LITERAL`: `#` plus uppercase letters, digits, or underscores, then
  `#`, for example `#JAVA_QUOTED_STRING#`.
- `BOOL_LITERAL`: exactly `true` or `false`.
- `DECIMAL_LITERAL`: non-negative decimal integer. Underscores are not allowed
  in this token.
- `FAIL`: case-insensitive `FAIL`; use it only in `=> FAIL` inside
  start/end `contains`.
- `//` starts a line comment and is skipped by the parser. The special
  `// require MT ...` directive is handled before parsing.

Do not invent identifiers. Field names are fixed keywords such as `match`,
`style`, `contains`, `recordAllGroups`, and `lineBackground`.

## `stringOrRegex` Expressions

The parser accepts five regex fragment forms in `stringOrRegexList`:

- `"..."`: Java string literal. This is safest when the pattern contains many
  slash characters.
- `/.../`: regex literal. Escape literal slashes as `\/`.
- `keywordsToRegex("if else return")`: optimized keyword regex generator.
- `include("regexName")`: insert a regex fragment from `defines`.
- `var("scopeName")`: insert a start-captured literal atom. This is legal only
  in the direct end `match` of the same `start/end` scope; read
  `scope-variables.md` before using it.

Fragments outside `keywordsToRegex(...)` must be joined with `+`:

```mtsx
{match: /\b/ + keywordsToRegex("if else return") + /\b/, 0: "keyword"}
```

Inside `keywordsToRegex(...)`, additional strings may be separated by `+` or by
plain adjacency:

```mtsx
{match: keywordsToRegex("if else" "for while"), 0: "keyword"}
```

Prefer `keywordsToRegex` for language keywords, built-in names, constants, and
type names. Do not hand-write a large alternation such as
`/(if|else|for|while|return|...)/`.
If several keyword groups share the same style and matching semantics, combine
them into one `keywordsToRegex` matcher instead of emitting adjacent duplicate
matchers with the same `0: "style"`. For long lists, use multiple adjacent
string literals and optional comments inside the function call:

```mtsx
{match: keywordsToRegex(
        // Language keywords
        "if else for while return"
        // Built-in names with the same style
        "print input range"
    ), 0: "keyword"
}
```

Java regex inline modifiers are allowed inside fragments when needed:

- `(?i)`: case-insensitive.
- `(?m)`: multiline anchors, where `^` and `$` work per line.
- `(?s)`: dotall, where `.` can match line terminators.
- `(?u)`: Unicode-aware case folding when combined with case-insensitive
  matching.

## Top-Level Properties

### `name`

```mtsx
name: ["LanguageName", ".suffix", ".other"]
```

The first string is the display name. The rest are filename suffixes.

### `hide`

```mtsx
hide: true
```

Optional metadata. Use only when mirroring an existing MT syntax that should not
appear in normal selection lists.

### `ignoreCase`

```mtsx
ignoreCase: true
```

Compiles regex patterns with case-insensitive matching. Prefer explicit case in
regexes unless the whole language is case-insensitive.

### `styles` / `colors`

```mtsx
styles: [
    "keyword", #0033B3, #CC7832
    "todo", #7A3E00#FFF2CC, #FFC66D#3A2B00, @B
    "strongKeyword", > "keyword", @B
]
```

`colors` is the legacy alias for `styles`. See `styles-and-builtins.md` for
style names, color syntax, inheritance, backgrounds, and flags.

### `comment`

```mtsx
comment: {startsWith: "//", insertSpace: true, addToContains: true}
```

`comment` defines editor comment behavior and can also add a comment matcher.
The field order is fixed:

1. `startsWith`
2. optional `endsWith`
3. optional `insertSpace`
4. optional `addToContains`

Use it before hand-written comment regexes when it models the language.

### `bracketPairs`

```mtsx
bracketPairs: ["()", "[]", "{}"]
```

Each string must represent one pair of different characters. Use this for editor
metadata and bracket behavior.

### `defines`

```mtsx
defines: [
    "ident": /[A-Za-z_][A-Za-z0-9_]*/
    "fnDecl": {match: /\b(fn)\s+([A-Za-z_][A-Za-z0-9_]*)/, 1: "keyword", 2: "variable"}
    "stringSet": [
        {builtin: #DOUBLE_QUOTED_STRING#}
        {builtin: #SINGLE_QUOTED_STRING#}
    ]
]
```

A define value is one of:

- a regex fragment list for `include("name")`;
- a single matcher for `{include: "name"}`;
- a matcher list for `{include: "name"}` as a competing set.
- a quoted-selector mapping for `childrenSyntax` `include: "name"`.

Regex defines can only include earlier regex defines. Matcher defines may refer
to each other, including recursive and cross-recursive matcher includes, but
circular hard dependencies are rejected during compile. Avoid recursive matcher
graphs in generated v1 syntaxes unless the language truly needs nested
constructs.

Children-syntax mapping defines have their own merge and duplicate rules. Read
`embedded-syntax.md`; they are not regex or matcher includes despite sharing
the same `defines` name space.

### `lineBackground`

```mtsx
lineBackground: {match: /(?m)^[ \t]*section\b[^\r\n]*/, style: "heading"}
```

The regex is matched against a single line region with `matches()`, so write a
pattern that can consume the whole target line. The referenced style's day and
night foreground colors become the line background colors in HTML.

### `contains`

```mtsx
contains: [
    {builtin: #JAVA_QUOTED_STRING#}
    {number: "2|10|16|F|E|P|_", iSuffixes: "L", fSuffixes: "F|D"}
    {match: keywordsToRegex("class interface enum"), 0: "keyword"}
]
```

`contains` is the main ordered matcher list. Keep it flat unless a bounded
region really needs children. A `start/end` region may instead delegate its
body to another language through `childrenSyntax`; it cannot use both modes.
See `matcher-semantics.md` and `embedded-syntax.md`.

### `codeFormatter` and `codeShrinker`

```mtsx
codeFormatter: #BUILT_IN_JSON_FORMATTER#
codeShrinker: #BUILT_IN_JSON_SHRINKER#
```

These are optional built-in tool metadata. See `styles-and-builtins.md` for the
current supported names.

## Core Matching Flow

The engine scans text with a competing matcher set:

- The match that starts earliest wins.
- If multiple matchers start at the same position, the earlier matcher in
  `contains` wins.
- `start/end` regions own the text from `start` through `end`, with child
  matchers competing inside the region.
- A `childrenSyntax` region defaults to finding its host end first. Explicit
  `matchEndFirst: false` makes the host end compete with the selected language's
  entire root; child tokens can consume text containing the host delimiter.
  Actual opening and closing delimiters remain host matches. See
  `embedded-syntax.md` for priority and boundary handling.
- A direct start `match` may export short captured delimiter text for `var()`
  in its direct end `match`.
- A parent style fills gaps inside a region; child matchers can override ranges.

This is why matcher order matters. Put comments and strings before keywords or
identifiers when their content should not be highlighted as normal code.

## Priority and Ordering Rules

Use this default order for ordinary generated syntaxes:

1. `comment` helper, if it applies.
2. Block comments and strings with `start/end`.
3. Built-in string or number matchers.
4. `number` matcher.
5. Keyword, built-in-name, constant, and type keyword matchers generated by
   `keywordsToRegex`.
6. Declaration or identifier matchers that add visible value.
7. Operators and punctuation.

When two regexes can start at the same byte, put the more specific matcher
first. When a broad regex can start earlier than a precise regex, narrow the
broad regex instead of relying only on order.

Flat ordering is not a reason to duplicate a complete embedded language into
the host or approximate an opener-dependent delimiter. Use the dedicated
bounded features for those real requirements.

## `// require MT` and Preprocessing

`// require MT` directives are line comments for the parser but are processed
before compilation:

```mtsx
// require MT >= 2.16.0
// require MT > 20240429
```

The version may be a version name or an exactly eight-digit version code.

Preprocessor directives are standalone line directives:

```mtsx
contains: [
#if MT >= 2.19.4
    {match: /newFeature/, 0: "keyword"}
#elif MT >= 2.18.0
    {match: /oldFeature/, 0: "keyword2"}
#else
    #error Unsupported MT version
#endif
]
```

Supported directives are `#if`, `#elif`, `#else`, `#endif`, and `#error`.
Conditions use `MT` plus one of `>`, `>=`, `<`, `<=`, `==`, or `!=`.
`#else` and `#endif` must not carry extra content, and each `#if` block may have
only one `#else`.

Preprocessor directives are supported by MT 2.19.4 and later. If a generated
syntax uses them, either add an explicit `// require MT >= 2.19.4` directive or
accept that older MT versions may fail before preprocessing.

`childrenSyntax`, reusable selector mappings, and start/end scope variables are
available in the current 2.26.9 syntax model. Add
`// require MT >= 2.26.9` when distributing a file that uses them.

## Generation Checklist

- Every generated syntax has non-blank `name`.
- Every slash regex has literal `/` written as `\/`, or uses a string regex
  instead.
- `recordAllGroups` appears immediately after `match`.
- Direct start exports appear after optional `recordAllGroups` and before group
  style entries; every export is consumed by the direct end.
- `comment` fields are in the fixed order.
- `start/end` matchers include both `start` and `end`.
- `childrenSyntax` is not combined with `contains`; omitted `matchEndFirst`
  keeps the hard boundary, while explicit `false` enables end/child competition.
- Every task-local `childrenSyntax` target required by the sample is passed as
  a `--syntax-dependency` in each validation mode used for that bundle.
- `keywordsToRegex` is used for keyword lists.
- `defines` names are unique, and regex defines only include earlier regex
  defines.
- Any style referenced by matchers is either built in or declared in `styles`.
- `lineBackground` patterns match entire line regions.
- Files using preprocessor directives declare or intentionally document the MT
  2.19.4 compatibility floor.
