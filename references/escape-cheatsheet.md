# MTSX Escape Cheatsheet

Load this before writing regexes or regex fragments. Most generation mistakes
come from mixing MTSX string escaping, MTSX `/.../` regex literals, and the Java
regex engine.

## Table of Contents

- Choose a fragment form
- Three layers
- Common examples
- Slash repair boundary
- Quick checks

## Choose A Fragment Form

Use `/.../` when the pattern is short and contains few literal `/` characters.
Use a quoted string regex when the pattern contains URLs, paths, HTML closing
tags, or many slashes.

```mtsx
{match: /[A-Za-z_]\w*/, 0: "variable"}
{match: "https?://[^\\s]+", 0: "string"}
```

Both forms are Java regex patterns after MTSX parsing.

## Three Layers

| Need in Java regex | In `/.../` | In quoted string |
|---|---|---|
| Word boundary | `/\bfoo\b/` | `"\\bfoo\\b"` |
| Whitespace class | `/\s+/` | `"\\s+"` |
| Literal backslash | `/\\/` | `"\\\\"` |
| Literal slash | `/\//` | `"/"` |
| Dot as wildcard | `/./` | `"."` |
| Literal dot | `/\./` | `"\\."` |
| Newline escape sequence | `/\\n/` | `"\\\\n"` |

Remember:

- `/.../` only has one MTSX-specific escape rule: a literal `/` must be `\/`.
- Quoted strings are Java-style string literals, so regex backslashes must be
  doubled.
- `""` is legal only as a `childrenSyntax` mapping selector. It is not a valid
  regex fragment, target, style, variable name, or include name.

## Common Examples

URL:

```mtsx
{match: "https?://[^\\s]+", 0: "string"}
```

HTML closing tag:

```mtsx
{match: /<\/[A-Za-z][A-Za-z0-9-]*>/, 0: "tagName"}
```

Unix-like path:

```mtsx
{match: "/(?:[^/\\s]+/)*[^/\\s]+", 0: "string"}
```

Windows path:

```mtsx
{match: "[A-Za-z]:\\\\(?:[^\\\\\\r\\n]+\\\\?)*", 0: "string"}
```

Word list:

```mtsx
{match: keywordsToRegex("if else return"), 0: "keyword"}
```

Boundary plus word list:

```mtsx
{match: /\b/ + keywordsToRegex("true false null") + /\b/, 0: "constant"}
```

Regex fragment define:

```mtsx
defines: [
    "ident": /[A-Za-z_][A-Za-z0-9_]*/
]
contains: [
    {match: /\bfn\s+/ + include("ident"), 0: "keyword"}
]
```

Dynamic end literal:

```mtsx
start: {match: /(`{3,})/ export: 1 => "fence"}
end: {match: /(?m)^/ + var("fence") + /`*[ \t]*$/}
```

The value inserted by `var()` is already quoted as one literal regex atom. If
the start captured `a+b`, the end matches literal `a+b`; do not pre-escape the
capture or surround `var()` with `\Q...\E`. Normal fragments before and after
it still use the rules in this file.

## Slash Repair Boundary

`repair-mtsx.py` only escapes unescaped `/` inside one unique `/.../` literal
near a matcher, including a direct start regex followed by `export`. It does not
rewrite quoted strings or `var()` values and must not edit examples in comments
or strings.

If a pattern has many slashes, prefer converting it manually to a quoted string
regex instead of asking the slash repair script to guess.

## Quick Checks

- Does every literal `/` inside `/.../` appear as `\/`?
- Does every Java regex backslash inside a quoted string appear doubled?
- Is `var()` a complete atom in a direct end match rather than part of a
  character class or a static fragment?
- Are keyword lists expressed with `keywordsToRegex`?
- Are cross-line patterns clearly bounded?
- Did the sample include at least one token that exercises this escape path?
