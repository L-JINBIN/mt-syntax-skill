# MTSX Styles and Built-ins

Load this when a generated syntax declares custom styles, references built-in
styles, uses `comment`, `lineBackground`, `bracketPairs`, `builtin`,
`codeFormatter`, or `codeShrinker`.

For style selection and IntelliJ-like color guidance, see
`color-guidance.md`; this file focuses on MTSX syntax and built-in names.

## Table of Contents

- Style declaration syntax
- Built-in style names
- Color literals
- Token background and line background
- Style flags
- Style inheritance and `!!`
- `comment`
- `bracketPairs`
- `lineBackground`
- Built-in matchers
- Built-in formatters and shrinkers
- Style naming guidance

## Style Declaration Syntax

Custom styles are declared under `styles` or legacy `colors`:

```mtsx
styles: [
    "docComment", #5F6B00, #99AA00, @I
    "functionName", #0055AA, #80C8FF
    "strongKeyword", > "keyword", @B
    "deprecated", @S
]
```

Supported item shapes:

- `"name", dayColor, nightColor`
- `"name", dayColor, nightColor, flags`
- `"name", > "baseStyle"`
- `"name", > "baseStyle", flags`
- `"name", flags`

Custom style names must not start with `!!`; that prefix is reserved for style
references.

## Built-in Style Names

These names are available in the bundled validator and are safe to reference:

- `default`
- `string`
- `strEscape`
- `comment`
- `meta`
- `number`
- `keyword`
- `keyword2`
- `constant`
- `type`
- `label`
- `variable`
- `operator`
- `propKey`
- `propVal`
- `tagName`
- `attrName`
- `namespace`
- `error`

Use these before inventing new names. Add a custom style only when the language
needs a visible category that is not covered above.

## Color Literals

`STYLE_LITERAL` has this shape:

```text
#FG
#FG#TOKEN_BG
#FG$LINE_BG
```

Color values accept the same compact color token as the lexer:

- `#RGB`
- `#ARGB`
- `#RRGGBB`
- `#AARRGGBB`
- `#NULL`

Day and night colors are separate values in style declarations. The first color
literal is the day style. The second is the night style.
Use `#NULL#BG` when only a token background should be defined and the foreground
should remain inherited or defaulted.

Examples:

```mtsx
"keyword", #0033B3, #CC7832
"selectionLike", #202020#FFF1A8, #E8E8E8#4A3A00
"sectionLine", #0033B3$FFF7D6, #CC7832$3A2B00
```

## Token Background and Line Background

Use `#FG#BG` when a token itself needs a background. The HTML renderer emits it
as a token background class.

Use `#FG$LINEBG` when a token style should mark the whole line background. The
renderer keeps the MTSX style name and turns the `$` background into a
`.line-bg.<style>` class for the line.

Avoid line backgrounds unless they clearly improve readability or mark important
structure. When a line background is necessary, prefer a `$` style marker so the
line mark is tied to an ordinary token match.

Do not mix token background and line background in one color literal; the lexer
allows only one optional suffix.
Line-background colors do not support transparency, and if several characters
on one line carry line-background colors, MT uses the first one it encounters.

Top-level `lineBackground` is separate from the `$` marker. It matches an entire
line region by regex and uses the referenced style foreground colors as the line
background colors.

## Style Flags

Flags use `@` plus one or more letters:

- `@B`: bold
- `@I`: italic
- `@U`: underline
- `@S`: strikethrough
- `@BI`, `@BU`, etc.: combine flags
- `@_`: explicit no-style flag token

Use flags sparingly. They are most useful for comments, deprecations, headings,
or error-like markers.

## Style Inheritance and `!!`

Custom styles can copy an existing style:

```mtsx
styles: [
    "macroKeyword", > "keyword", @B
]
```

Matcher style references may start with `!!`:

```mtsx
{match: /ERROR\b/, 0: "!!error"}
```

`!!styleName` disables inheritance or parent-style merging for that reference.
Use it only when a nested region must force an exact style instead of inheriting
from the surrounding region. Do not declare custom styles whose names start with
`!!`.

## `comment`

`comment` is both metadata for editor comment actions and an optional generated
matcher:

```mtsx
comment: {startsWith: "//", insertSpace: true, addToContains: true}
comment: {startsWith: "/*", endsWith: "*/", insertSpace: true, addToContains: true}
```

Field order is fixed:

1. `startsWith`
2. optional `endsWith`
3. optional `insertSpace`
4. optional `addToContains`

Defaults:

- `insertSpace` defaults to `true`.
- `addToContains` defaults to `true`.

When `addToContains` is true, the compiler adds a matcher styled as `comment`.
For line comments it matches escaped `startsWith` plus the rest of the line. For
block comments it uses a cross-line lazy pattern ending at `endsWith` or EOF.

Prefer `comment` for ordinary line and block comments. Use explicit `start/end`
comment matchers only when the language has nested comments, special doc-comment
tokens, or content inside comments that needs child highlighting.

## `bracketPairs`

```mtsx
bracketPairs: ["()", "[]", "{}"]
```

Each string must be exactly two different characters. Invalid examples:

```mtsx
bracketPairs: ["("]
bracketPairs: ["aa"]
```

## `lineBackground`

```mtsx
styles: [
    "methodLine", #FFEDED, #33243A
]
lineBackground: {match: /(?m)^[ \t]*\.method\b[^\r\n]*/, style: "methodLine"}
```

The regex runs against one line region and must match that whole line. Use
`(?m)^[ \t]*...[^\r\n]*` or another bounded full-line pattern. The referenced
style's day and night foreground colors are used for the line background in the
explicit `lineBackground` path.

Avoid line backgrounds by default. When one is necessary, prefer `$` style
markers because they reuse an ordinary token match and avoid an extra full-line
regex. Use top-level `lineBackground` only when the line marker cannot naturally
attach to a token, or when a dedicated full-line condition is required.

- `$` style marker: preferred path; a normal token match also marks its line.
- Top-level `lineBackground`: exception path; a dedicated full-line regex.

## Built-in Matchers

These built-in matcher names are available in the bundled validator:

- `#ESCAPED_CHAR#`: generic backslash escape, styled as `strEscape`.
- `#SINGLE_QUOTED_STRING#`: single-quoted string using `#ESCAPED_CHAR#`.
- `#DOUBLE_QUOTED_STRING#`: double-quoted string using `#ESCAPED_CHAR#`.
- `#QUOTED_STRING#`: both single and double quoted strings.
- `#JAVA_ESCAPED_CHAR#`: Java escapes, invalid escapes styled as `error`.
- `#JAVA_SINGLE_QUOTED_STRING#`: Java single-quoted string.
- `#JAVA_DOUBLE_QUOTED_STRING#`: Java double-quoted string.
- `#JAVA_QUOTED_STRING#`: Java single and double quoted strings.
- `#C_ESCAPED_CHAR#`: C-style escapes, invalid escapes styled as `error`.
- `#C_SINGLE_QUOTED_STRING#`: C single-quoted string.
- `#C_DOUBLE_QUOTED_STRING#`: C double-quoted string.
- `#C_QUOTED_STRING#`: C single and double quoted strings.
- `#NORMAL_NUMBER#`: decimal integer and normal float.
- `#PROGRAM_NUMBER#`: binary, decimal, hex, normal float, exponent float.
- `#PROGRAM_NUMBER2#`: decimal, hex, normal float, exponent float.
- `#JAVA_NUMBER#`: Java-like binary, decimal, hex, float, exponent,
  hexadecimal-float, underscore separators, `L`, `F`, and `D` suffixes.
- `#C_NUMBER#`: C-like binary, decimal, hex, float, exponent, hexadecimal-float,
  single-quote separators, `L`, `U`, `LU`, `UL`, and `F` suffixes.

Prefer a built-in when it matches the language closely. If the built-in is only
almost correct, use an explicit `number` or `start/end` matcher instead of
forcing the wrong built-in.

## Built-in Formatters and Shrinkers

Formatter names accepted by the bundled validator:

- `#BUILT_IN_CSS_FORMATTER#`
- `#BUILT_IN_HTML_FORMATTER#`
- `#BUILT_IN_JAVA_FORMATTER#`
- `#BUILT_IN_JS_FORMATTER#`
- `#BUILT_IN_JSON_FORMATTER#`
- `#BUILT_IN_XML_FORMATTER#`
- `#BUILT_IN_SMALI_FORMATTER#`

Shrinker names accepted by the bundled validator:

- `#BUILT_IN_CSS_SHRINKER#`
- `#BUILT_IN_HTML_SHRINKER#`
- `#BUILT_IN_JSON_SHRINKER#`

Only add these when the language truly matches the formatter or shrinker.
Generated syntaxes usually do not need either field.

## Style Naming Guidance

- Reuse built-in names for common categories.
- Use short, stable custom names such as `docComment`, `functionName`, or
  `sectionHeader`.
- Avoid style names based on one sample file.
- Do not create one style per keyword unless the visual distinction is important.
- Remember that style names become HTML classes; use ASCII letters and digits
  where possible.
