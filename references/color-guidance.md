# MTSX Color Guidance

Load this before choosing token styles, declaring custom styles, or adding
token and line backgrounds. This guide keeps generated syntaxes visually close
to IntelliJ IDEA's Light/Darcula code colors while staying consistent with the
MT built-in syntax files.

## Table of Contents

- Grounding
- Core rules
- Style mapping
- Patterns from built-in syntaxes
- Custom colors
- Backgrounds and flags
- Examples

## Grounding

IntelliJ IDEA separates the editor color scheme from the UI theme. Its language
highlighting is designed around shared language-default text attributes, with
language-specific colors only when needed. Treat MTSX the same way: use stable
semantic styles first, then add local aliases or colors only when the language
needs a visible distinction.

The recommendations below are based on IntelliJ's color-scheme model and the
style patterns used by MT's built-in syntaxes. Use them as generation guidance,
not as a requirement to copy every existing custom color.

Useful references:

- IntelliJ IDEA: <https://www.jetbrains.com/help/idea/configuring-colors-and-fonts.html>
- IntelliJ Platform: <https://plugins.jetbrains.com/docs/intellij/color-scheme-management.html>

## Core Rules

- Reuse built-in style names from `styles-and-builtins.md` before inventing a
  custom style. This mirrors IntelliJ's default text-attribute inheritance.
- Prefer semantic consistency over language-specific decoration. A keyword,
  string, number, comment, or error should read similarly across languages.
- Prefer custom aliases such as `"preprocessor" > "meta"` or
  `"path" > "type"` over hard-coded colors. Aliases keep HTML classes useful
  without creating a new palette.
- Add explicit day/night colors only when an inherited style cannot carry a
  real visual distinction. Markdown headings/admonitions, lyrics timing marks,
  Smali method lines, and Brainfuck glyph groups are examples from the built-in
  syntaxes.
- Define both day and night colors whenever a custom color is necessary. Check
  that both themes remain readable and do not collapse into the background.
- Avoid token backgrounds and line backgrounds by default. Use them for
  structural regions that benefit from scanning, not for ordinary syntax.

## Style Mapping

Use this table as the default choice when designing the feature map.

| Language feature | Preferred style | Notes |
|---|---|---|
| Plain text or unclassified tokens | `default` | Avoid broad identifier coloring unless it improves scanning. |
| Control-flow, declaration, visibility, module keywords | `keyword` | Java/Kotlin/JS/C/C++/Go/Swift use this as the primary keyword color. |
| Secondary directives, pseudo-keywords, assembler directives | `keyword2` | Good for Smali directives, special language words, or secondary keyword groups. |
| Strings, raw strings, heredocs, CDATA bodies | `string` | Keep string bodies green-ish in both Light and Darcula style. |
| Escape sequences, interpolation delimiters, HTML/XML entities | `strEscape` | Use for the escape marker, not for the entire string. |
| Line/block comments | `comment` | Prefer `comment` helper for ordinary comments. |
| Doc comments or important comment tags | `comment` alias or `namespace` | Existing Rust/Zig syntaxes use distinct doc-comment aliases sparingly. |
| Numbers | `number` | Covers numeric literals and numeric time fragments. |
| Types, built-in types, class/interface names | `type` | Use capture groups for declarations when simple and reliable. |
| Constants, enum-like values, all-caps macros | `constant` | Java/C/C++/SQL use this for uppercase constants and literals. |
| Variables, parameters, registers, shell variables | `variable` | Smali registers and shell parameters are good examples. |
| Labels, jump targets, anchors | `label` | Use for goto labels, SQL labels, DTS node labels. |
| Operators and punctuation with semantic weight | `operator` | Do not color every punctuation mark unless the language benefits from it. |
| Annotations, attributes, preprocessor, DOCTYPE, regex literals | `meta` | Use for syntax that describes code rather than runtime values. |
| Property keys and values | `propKey`, `propVal` | Preferred for `.properties`, MTL-like files, and key/value formats. |
| Markup tag names, attribute names, namespaces | `tagName`, `attrName`, `namespace` | HTML/XML/SVG/ARSC editor syntaxes use this family consistently. |
| Syntax or validation errors | `error` | Reserve for likely-invalid constructs, not merely uncommon syntax. |

## Patterns From Built-in Syntaxes

The built-in syntaxes show six recurring color patterns.

1. Built-in style reuse

Java, Kotlin, JavaScript, JSON, Toml, YML, Prop, HTML, XML, SVG, C#, Dart, and
many other syntaxes mostly assign tokens directly to `keyword`, `string`,
`strEscape`, `comment`, `meta`, `number`, `type`, `constant`, `variable`, and
`error`. This is the preferred default for new syntaxes.

2. Semantic aliases over built-ins

CSS maps selectors and properties through aliases such as `"className" >
"constant"` and `"propertyName" > "keyword"`. SQL uses `"sqlFunction" >
"keyword2"` and `"sqlOperator" > "operator"`. Bat uses `"path" > "type"` and
`"envVar" > "constant"`. LaTeX, C, C++, GLSL, Rust, DTS, ABNF, Diff, ASM, JASM,
Zig, and MTSX itself follow the same pattern. Use this when the HTML class name
should say more than the base style.

Internal syntaxes such as Regex, regex replacement, folder comparison, and ARSC
translation editors are useful boundary examples: they color tool-specific
tokens, but still keep those colors anchored to a small set of semantic roles.

3. Explicit day/night colors

Python, Markdown, Lyrics, Brainfuck, Smali, PHP, and a few internal syntaxes
define real color values. Treat these as exceptions for readability or legacy
compatibility, not as a reason to create a large custom palette for every new
language.

4. Token backgrounds

Markdown image/link pieces, Brainfuck error tokens, and internal ARSC
translation items use `#FG#BG` backgrounds. Use this only when a small token
needs a visual block and foreground alone is not enough.

5. Line backgrounds

Smali uses a `$` line-background marker on `methodStart`. Markdown marks front
matter and code blocks. Lyrics and Swift use top-level `lineBackground` for
whole-line markers, and internal folder comparison uses line backgrounds for
headers. Prefer `$` markers when the background naturally attaches to a token;
use top-level `lineBackground` only for dedicated full-line conditions.

6. Pure style flags

Markdown defines `B`, `I`, `BI`, `S`, and `U` styles for inline formatting.
MTSX defines flag-demonstration styles, and MTD uses a bold-underlined
placeholder style. Use flags for text semantics such as emphasis,
deprecation, headings, or placeholders; do not use flags as a substitute for
missing lexical structure.

## Custom Colors

When a custom color is unavoidable:

- Keep the pair close to IntelliJ Light/Darcula contrast: dark enough on light
  backgrounds and bright enough on dark backgrounds.
- Start from an existing built-in hue. For example, derive a declaration-name
  style from `keyword2` or `tagName`, and derive markup subtypes from
  `tagName`, `attrName`, or `namespace`.
- Avoid one style per keyword. Group by semantic role, such as
  `preprocessor`, `docComment`, `functionName`, `sectionHeader`, or
  `specialChar`.
- Avoid copying historical custom colors blindly. Some built-in files predate
  this guidance or optimize for a very specific visual task.
- Do not reference unclear base names from old syntaxes unless that style is
  declared in the same file or listed in `styles-and-builtins.md`.

## Backgrounds and Flags

- Use `#FG#TOKEN_BG` for a compact token region such as a markdown image
  marker or an internal editor warning token.
- Use `#FG$LINE_BG` when a normal token should mark the whole line, such as a
  method header. This keeps line styling tied to the same matcher.
- Use top-level `lineBackground` for full-line state that cannot be attached to
  one token, such as lyrics interludes or Swift `MARK:` separator lines.
- Avoid transparent or low-contrast backgrounds. Line-background colors do not
  support transparency in MTSX.
- Use `@B`, `@I`, `@U`, and `@S` sparingly. Existing syntaxes use them for
  comments, headings, markdown emphasis, TODO markers, placeholders, and
  error-like text.

## Examples

Prefer aliases when a base style already communicates the color:

```mtsx
styles: [
    "preprocessor" > "meta"
    "functionName" > "keyword2"
    "path" > "type"
    "docComment" > "comment", @I
]
```

Use explicit colors only for a visible structural reason:

```mtsx
styles: [
    "sectionHeader", #7C1E8F, #BD80B8, @B
    "methodStart", #800000$FFEDED, #AE8ABE$443034
]
```

Keep ordinary matcher styles simple:

```mtsx
contains: [
    {builtin: #JAVA_QUOTED_STRING#}
    {builtin: #JAVA_NUMBER#}
    {match: /@\w+(?:\.\w+)*/, 0: "meta"}
    {match: keywordsToRegex("if else return class"), 0: "keyword"}
    {match: /\b[A-Z][A-Z0-9_]+\b/, 0: "constant"}
]
```
