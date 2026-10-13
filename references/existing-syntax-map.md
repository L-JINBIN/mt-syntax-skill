# Existing Syntax Map

Load this when choosing a nearby built-in syntax pattern to emulate.
Use these summaries as examples; the installed skill may not include the
original built-in `.mtsx` source files.

## Table of Contents

- Common language templates
- Special matcher patterns
- Styles and visual output
- Formatter metadata
- How to use this map

## Common Language Templates

| Need | Nearby built-in pattern | Why |
|---|---|---|
| Java-like language | Java | Flat comments, built-in Java strings and numbers, keyword list. |
| C-like language | C or C++ | C strings, numeric suffixes, preprocessor-like constructs. |
| Go-like language | Go | Custom strings, raw strings, declaration names, built-in type/function styles. |
| Scripting language | Python or Shell | Significant line constructs and mixed string forms. |
| Markup language | XML, HTML, or SVG | Tags, attributes, embedded JS/CSS/JSON, color parsing, formatter metadata. |
| Data format | JSON, Toml, or YML | Small syntax with strings, numbers, constants, and property keys. |
| Large keyword DSL | Smali | Large `keywordsToRegex` lists, custom type fragments, line background marker. |
| MTSX itself | MTSX | DSL highlighting, preprocessor directives, `group`, flags, and parseColor. |

## Special Matcher Patterns

| Pattern | Known built-in use | Notes |
|---|---|---|
| `group: link` declarations | `go.mtsx`, `sql.mtsx`, `dts.mtsx` | Use only when consecutive child matchers are clearer than one regex. |
| `group: linkAll` | `markdown.mtsx` | Useful for tightly linked delimiter sequences. Avoid for broad syntax. |
| `group: select` | `mtsx.mtsx` | Use for alternative child branches at the same position. |
| `recordAllGroups` | `toml.mtsx` | Use only for repeated capture groups that must all be styled. |
| `<EndMatcher>` | `markdown.mtsx`, `cs.mtsx` | Controls where end matching competes with children. |
| `matchEndFirst` / `mustMatchEnd` | `markdown.mtsx`, `brainfuck.mtsx` | Advanced bounded-region control. `childrenSyntax` defaults to end-first; explicit `matchEndFirst: false` enables competition. |
| `childrenSyntax` fixed/dynamic routing | `html.mtsx`, `markdown.mtsx` | Use for bounded independent languages; read `embedded-syntax.md`. |
| start `export` + end `var()` | `markdown.mtsx` | Keeps fence length in the direct start/end scope; read `scope-variables.md`. |
| `lineBackground` | `swift.mtsx`, `lyrics.mtsx` | Top-level full-line regex. Must match the whole line region. |
| `$` line background style | `smali.mtsx` | Token style marks the whole line in rendered HTML. |
| `parseColor(...)` | `css.mtsx`, `xml.mtsx`, `markdown.mtsx` | Only for color literal syntaxes. |

## Styles And Visual Output

- Reuse built-in style names from `styles-and-builtins.md` first.
- Use `go.mtsx` for small custom style examples such as `funcName` and
  `builtinType`.
- Use `smali.mtsx` for `$` line background style examples.
- Use `mtsx.mtsx` for style inheritance, flags, dynamic color parsing, and DSL
  keyword highlighting for `childrenSyntax`, `export`, and `var()`.
- Use `html.mtsx` for fixed CSS, fixed JavaScript, and capture-selected
  JavaScript/JSON bodies.
- Use `markdown.mtsx` for a dynamic fence end combined with capture-selected
  child syntax and missing fallback.

## Formatter Metadata

Only add formatter or shrinker metadata when the language exactly matches an
existing built-in tool:

- Java: `java.mtsx`
- JSON: `json.mtsx`
- CSS: `css.mtsx`
- HTML: `html.mtsx`
- XML/SVG: `xml.mtsx`, `svg.mtsx`
- Smali: `smali.mtsx`

Generated syntaxes usually do not need `codeFormatter` or `codeShrinker`.

## How To Use This Map

1. Pick one nearby syntax family and reuse only the relevant pattern.
2. If source is available in the current workspace, inspect only the relevant
   matcher family; otherwise rely on the summaries in this file.
3. Keep the generated v1 flatter than the referenced pattern if that pattern is
   complex.
4. Add sample cases that prove the adapted pattern works in the new syntax.
