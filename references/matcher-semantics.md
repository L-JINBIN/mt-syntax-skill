# MTSX Matcher Semantics

Load this after `mtsx-format.md` when generating or repairing `.mtsx`
matchers. The parser recognizes exactly six matcher families:

- `match`
- `start/end`
- `group`
- `number`
- `builtin`
- `include`

## Table of Contents

- Common matcher rules
- `match`
- Capture group styles and submatchers
- `recordAllGroups`
- Direct start exports
- `parseColor(...)`
- `start/end`
- Start/end advanced controls
- Embedded child language routing
- `group`
- `number`
- `builtin`
- `include`
- Recommended matcher order

## Common Matcher Rules

Every matcher is wrapped in braces:

```mtsx
{match: /.../, 0: "keyword"}
```

Some matcher families accept an optional matcher display name:

```mtsx
{
    name: "functionDeclaration"
    match: /\b(fn)\s+([A-Za-z_][A-Za-z0-9_]*)/
    1: "keyword"
    2: "variable"
}
```

The optional matcher name is parsed as `name: "..."` before the matcher keyword
for `match`, `start/end`, `number`, and `group`. It can label a rule in the syntax
source but is not required for highlighting. Current fresh execution and
`--explain` identify rules by rule ID and source location, not this name.

Do not mix matcher families in one object. These are different matchers:

```mtsx
{match: /abc/, 0: "keyword"}
{number: "10|16|F|E", style: "number"}
{builtin: #JAVA_QUOTED_STRING#}
```

## `match`

Shape:

```mtsx
{
    name: "optionalMatcherName"
    match: stringOrRegexList
    recordAllGroups: true
    export: 1 => "scopeVariable"
    0: "styleName"
    1: "styleName"
    2: {match: /child/, 0: "styleName"}
}
```

Field order is strict:

1. optional matcher `name`
2. `match`
3. optional `recordAllGroups`
4. zero or more `export` entries
5. zero or more capture-group style or capture-group submatcher entries

`recordAllGroups` must be immediately after `match`. Putting it after a group
entry is a parse error.

`export` is legal only when this matcher is the direct `start` of a
`start/end` scope and the direct `end` consumes it with `var()`. It is not a
general match-metadata feature. Read `scope-variables.md` before adding one.

Use `0: "styleName"` to style the whole match. Use `1`, `2`, and so on for
capture groups. The compiler checks that referenced groups exist.
When `0` is combined with other capture-group styles, it acts as the default
style for the whole matched range and the more specific group styles override
their subranges.

Good:

```mtsx
{
    match: /\b(fn)\s+([A-Za-z_][A-Za-z0-9_]*)/
    1: "keyword"
    2: "variable"
}
```

Bad:

```mtsx
{
    match: /\b(fn)\s+([A-Za-z_][A-Za-z0-9_]*)/
    1: "keyword"
    recordAllGroups: true
    2: "variable"
}
```

## Capture Group Styles and Submatchers

Capture group entries accept either a style string or a nested matcher:

```mtsx
{
    match: /\b(@)([A-Za-z_][A-Za-z0-9_]*)/
    1: "operator"
    2: {match: /[A-Z][A-Za-z0-9_]*/, 0: "type"}
}
```

Nested matchers receive the captured group range as an independent input.
`^` and `$` use that input's boundaries (and its internal line boundaries when
multiline mode applies); lookahead and lookbehind cannot read outside the group.
Absent or empty captures do not run the nested scan.

These matchers are useful when a group contains smaller pieces that need separate
styling. Keep them small; a top-level matcher is usually easier to reason about.

The same capture group may have multiple nested matchers. A capture group may
also have both a style entry and nested matcher entries; the style is the
default for that captured range, and nested matchers override their hits.

Multiple `0` style entries are accepted and are applied in order before other
capture groups. Prefer one `0` entry unless intentionally layering styles.

## `recordAllGroups`

`recordAllGroups: true` tells the regex engine to keep overridden or repeated
captures, so styles and submatchers can apply to repeated capture groups.

Use it only when a repeated capture group must be highlighted:

```mtsx
{
    match: /\b([A-Za-z_]\w*)(?:\.([A-Za-z_]\w*))+\b/
    recordAllGroups: true
    1: "variable"
    2: "propKey"
}
```

Avoid it for simple regexes; it adds work and is easy to put in the wrong
position.

## `parseColor(...)`

A group style string may be a dynamic color parser:

```mtsx
{
    match: /#([0-9a-fA-F]{6})([0-9a-fA-F]{2})?/
    0: "parseColor(1,_,HEX,constant)"
}
```

Format:

```text
parseColor(foregroundGroup,backgroundGroup,FORMAT,baseStyle)
```

- `foregroundGroup` and `backgroundGroup` are capture group numbers, `_`, or
  `AUTO`.
- `_` keeps the value from the base style, or leaves the existing value unchanged
  when no base style is supplied.
- `AUTO` computes an inverted or readable value from the other color.
- At least one of foreground or background must be a capture group number;
  `parseColor(_,AUTO,...)` and similar forms do not carry useful input.
- `FORMAT` may be `HEX`, `HEXA`, `RGB`, `HSL`, `HSV`, `RGBA`, `HSLA`, `HSVA`,
  `XRGB`, `RGBX`, `ARGB`, `RGBf`, `ARGBf`, or `RGBAf`. Format names are
  case-insensitive; use the lowercase `f` spelling in generated files.
- `baseStyle` is optional. Omit it to preserve existing styling in fields where
  no color is produced; if color parsing fails entirely, no new style is applied.
  Supply a style such as `constant` when that explicit fallback is intended.
  Adding a base style can change the appearance of invalid color text, so choose
  it according to the desired behavior rather than always filling it in.

RGB-family formats use these component rules:

- `RGB` reads integer red, green, and blue components from `0` through `255`.
- `RGBA` and `ARGB` use the position of `A` for an alpha component written as a
  `0..1` decimal or `0%..100%`; their RGB components remain integers.
- `RGBX` and `XRGB` use the position of `X` for an integer alpha component from
  `0` through `255`.
- The `f` suffix changes all three RGB components to normalized decimals or
  percentages. `RGBf` has no alpha, while `ARGBf` and `RGBAf` place normalized
  alpha before or after the RGB components.
- Each normalized component independently accepts decimal or percentage form,
  so `RGBf(1, 0%, 0)` is valid and represents red.

Use dynamic color parsing only for color literal syntaxes such as CSS, XML, or
Android resources.
If using `HEXA` for MT-distributed syntax files, add `// require MT >= 2.18.4`.
`ARGB` gained independent fractional-alpha semantics and the three `f` formats
were added in MT 2.26.9. Add `// require MT >= 2.26.9` when using them.

## `start/end`

Shape:

```mtsx
{
    name: "string"
    start: {match: /"/}
    end: {match: /(?m)"|$/}
    style: "string"
    childrenStyle: "string"
    contains: [
        {match: /\\./, 0: "strEscape"}
    ]
}
```

`start` and `end` are required. A missing `start` or `end` compiles as a
validation error. `start` and `end` each hold a full matcher object, so simple
delimiters normally use nested `match` matchers.

Use `start/end` for:

- strings and character literals;
- block comments;
- raw strings or heredocs with clear delimiters;
- bounded regions where children need highlighting.

Avoid using `start/end` for ordinary keywords or single-token constructs.

`style` applies to the delimiter and default region style. `childrenStyle`
applies to text between child matches; if omitted it falls back to `style`.

A bounded body may use either host `contains` or `childrenSyntax`, never both.
Read `embedded-syntax.md` before delegating to another language. When an end
delimiter reuses opener text, read `scope-variables.md`.

## Start/End Advanced Controls

Full shape:

```mtsx
{
    start: {match: /\/\*/}
    end: {match: /\*\//}
    style: "comment"
    childrenStyle: "comment"
    matchEndFirst: false
    mustMatchEnd: false
    contains: [
        {match: /ALERT\b/, 0: "keyword"} => FAIL
        <EndMatcher>
        {match: /@\w+/, 0: "meta"}
    ]
}
```

The parser accepts these `start/end` items:

- `start`
- `end`
- `style` or `color`
- `childrenStyle`
- `childrenSyntax`
- `missingStyle`
- `contains`
- `matchEndFirst`
- `mustMatchEnd`
- `endPriority`

Generation should keep a stable order: `start`, `end`, `style`,
`childrenStyle`, `mustMatchEnd`, mode-specific controls, then either `contains`
or `childrenSyntax` plus optional `missingStyle`.

`matchEndFirst`:

- With ordinary `contains`, defaults to `false`: the end matcher competes
  with child matchers.
- `true` finds the end first, then only highlights children before that end.
  Use this when the host delimiter must end the region even inside child tokens.
- With `childrenSyntax`, defaults to `true` only when omitted. Explicit `false`
  makes the host end compete with the entire child root at each token boundary;
  child strings and comments can consume text containing the host delimiter.
  See `embedded-syntax.md` for boundary and context handling.

`mustMatchEnd`:

- `false` by default. If the end is missing, the region may extend to EOF.
- `true` makes the whole `start/end` matcher fail when the end is absent.

`endPriority`:

- Applies to competition with `matchEndFirst: false`; end-first mode ignores it.
- With ordinary `contains`, inserts the end matcher at a numeric index in the
  child list. Default `0` checks the end first when matches start together.
- With `childrenSyntax`, `0` tries the host end first; any positive value tries
  the entire child root first. It does not index individual child-language rules.
- It cannot be used together with `<EndMatcher>`.

`<EndMatcher>`:

- A marker inside `contains` that sets where the end matcher participates in
  child competition.
- It is not a matcher and has no braces.
- It cannot appear more than once and cannot be combined with `endPriority`.

`=> FAIL`:

- Allowed only after a matcher inside a `start/end` `contains` list.
- If that matcher hits, the whole `start/end` match fails.
- Use sparingly for disqualifying constructs, not for normal styling.

## `group`

Shape:

```mtsx
{
    name: "qualifiedName"
    group: linkAll
    style: "variable"
    contains: [
        {match: /[A-Za-z_][A-Za-z0-9_]*/, 0: "variable"}
        {match: /\./, 0: "operator"}
        {match: /[A-Za-z_][A-Za-z0-9_]*/, 0: "propKey"}
    ]
}
```

Field order is strict:

1. optional matcher `name`
2. `group`
3. optional `style`
4. `contains`

Group types:

- `link`: first child must match at the start, then later children are attempted
  consecutively. Partial chains are accepted after the first child.
- `linkAll`: every child must match consecutively.
- `select`: child matchers are tried in order at the same start position; the
  first successful child wins.

`style` is the group's default style over the selected or linked range. Child
matchers may add more precise styles.

Use `group` only when consecutive child matchers are genuinely clearer than a
single regex. Do not wrap a normal top-level matcher list in `group: select`;
plain `contains` already has the same competition behavior. Do not use `select`
around one child; it adds no value.

## `number`

Shape:

```mtsx
{number: "2|10|16|F|E|P|_", iSuffixes: "L", fSuffixes: "F|D", style: "number"}
```

Recommended field order:

1. optional matcher `name`
2. `number`
3. optional `iSuffixes`
4. optional `fSuffixes`
5. optional `style`

Only optional `name` followed by `number` has a fixed position. After `number`,
`iSuffixes`, `fSuffixes`, and `style` may appear in any order.

The `number` format string is a `|`-separated set of flags:

- `2`: binary integers with `0b` or `0B`.
- `8`: octal integers with `0o` or `0O`.
- `10`: decimal integers, including leading-zero digit sequences such as
  `0777`. This broad match is intentional for highlighting; it may also
  highlight invalid octal-like text such as `0888`.
- `16`: hexadecimal integers with `0x` or `0X`.
- `F`: normal decimals such as `1.2`.
- `E`: decimal exponent floats such as `1.2e3`.
- `P`: hexadecimal floats such as `0x1.2p3`.
- `_`: allow underscores inside digits.
- `'`: allow single quotes inside digits.

`iSuffixes` and `fSuffixes` are `|`-separated suffix lists. Suffix matching is
case-insensitive, and longer suffixes are matched first by the engine.

Prefer built-ins such as `#JAVA_NUMBER#` when they exactly match the language.
Otherwise use a `number` matcher instead of hand-written numeric regexes.
Do not add a separate regex solely to cover Java-style leading-zero numbers
such as `0777`; `10` already highlights them. Use a custom regex only when the
syntax must avoid highlighting invalid leading-zero forms.

## `builtin`

Shape:

```mtsx
{builtin: #JAVA_QUOTED_STRING#}
```

`builtin` inserts a named built-in matcher from `init/builtins.mtsx`. Built-ins
are good defaults for common quoted strings, escape handling, and numeric
literals. See `styles-and-builtins.md` for the current built-in list.

Built-in matcher objects do not accept an inline style override. If a language
needs different colors, override the referenced style names globally with
`styles`, or write an explicit matcher.

## `include`

Shape:

```mtsx
{include: "stringLike"}
```

`include` inserts a matcher or matcher list from `defines`. It is different from
`include("regexName")`, which inserts a regex fragment inside `match`.

Use matcher includes to reuse a small bounded construct. Avoid long recursive
include chains in generated v1 syntaxes; they are harder to validate and repair.

## Recommended Matcher Order

For generated flat syntaxes, start with this order:

1. comment helper or explicit block comments;
2. quoted strings and raw strings;
3. numbers;
4. keywords, constants, built-in names, and type names through
   `keywordsToRegex`;
5. declarations where capture groups add useful styling;
6. operators and punctuation;
7. broad identifiers only if they do not create noise.

When the complete HTML review shows a wrong token class, adjust the narrowest
affected matcher and validate again. Do not regenerate the whole file for a
local matcher ordering issue.
