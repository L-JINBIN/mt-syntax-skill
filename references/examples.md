# MTSX Examples and Anti-patterns

Use this file after loading `mtsx-format.md` and `matcher-semantics.md`. The
examples are intentionally small and flat so they can be copied, adapted, and
validated quickly.

## Table of Contents

- Minimal legal syntax
- Common flat language template
- Custom styles
- Comment helper with `addToContains`
- `keywordsToRegex`
- `number`
- `start/end` string
- Embedded language body
- Dynamic fence end
- Capture group submatcher
- `lineBackground`
- Regex define and matcher include
- Common anti-patterns
- Repair-oriented examples

## Minimal Legal Syntax

```mtsx
{
    name: ["MiniLang", ".mini"]
    contains: [
        {match: keywordsToRegex("if else return"), 0: "keyword"}
    ]
}
```

Use this shape for a first compile check before adding more matchers.

## Common Flat Language Template

```mtsx
{
    name: ["ToyLang", ".toy"]
    styles: [
        "functionName", #0055AA, #80C8FF
    ]
    comment: {startsWith: "//", insertSpace: true, addToContains: true}
    contains: [
        {
            start: {match: /"/}
            end: {match: /(?m)"|$/}
            style: "string"
            contains: [
                {match: /\\./, 0: "strEscape"}
            ]
        }
        {number: "10|16|F|E|_", style: "number"}
        {match: keywordsToRegex("section let return true false"), 0: "keyword"}
        {
            match: /\b(fn)\s+([A-Za-z_][A-Za-z0-9_]*)/
            1: "keyword"
            2: "functionName"
        }
        {match: /[+\-*=%!<>|&]+/, 0: "operator"}
    ]
}
```

This template covers custom `styles`, `comment addToContains`, `number`,
`keywordsToRegex`, a bounded string, and capture groups.

## Custom Styles

```mtsx
styles: [
    "docComment", > "comment", @I
    "functionName", #0055AA, #80C8FF
    "lineMark", #7A3E00$FFF4CC, #FFC66D$33243A
]
```

Use `>` to copy an existing style. Use `$` only when a token style should mark
its entire line in rendered HTML.

## Comment Helper With `addToContains`

```mtsx
comment: {startsWith: "#", insertSpace: true, addToContains: true}
```

This adds editor comment metadata and a generated `comment` matcher. Keep the
field order unchanged.

For block comments:

```mtsx
comment: {startsWith: "/*", endsWith: "*/", insertSpace: true, addToContains: true}
```

Use explicit `start/end` comments when comments have child tokens:

```mtsx
{
    start: {match: /\/\*/}
    end: {match: /\*\//}
    style: "comment"
    contains: [
        {match: /ALERT\b/, 0: "keyword"}
    ]
}
```

## `keywordsToRegex`

Good:

```mtsx
{match: keywordsToRegex("if else for while return break continue"), 0: "keyword"}
```

Also valid:

```mtsx
{match: keywordsToRegex("if else for" "while return break" "continue"), 0: "keyword"}
```

Preferred for long lists with one style:

```mtsx
{match: keywordsToRegex(
        // Control flow
        "if else for while return break continue"
        // Declarations with the same style
        "class interface enum record"
    ), 0: "keyword"
}
```

Avoid splitting lists into adjacent matchers when they use the same style and
same matching semantics; merge them into one `keywordsToRegex(...)` call.

Boundary-aware form:

```mtsx
{match: /\b/ + keywordsToRegex("true false null") + /\b/, 0: "constant"}
```

Avoid:

```mtsx
{match: /\b(if|else|for|while|return|break|continue)\b/, 0: "keyword"}
```

## `number`

Java-like:

```mtsx
{number: "2|10|16|F|E|P|_", iSuffixes: "L", fSuffixes: "F|D", style: "number"}
```

The `10` flag already highlights leading-zero digit sequences such as `0777`;
do not add a separate Java-octal regex unless you specifically need to reject
invalid forms such as `0888`.

C-like:

```mtsx
{number: "2|10|16|F|E|P|'", iSuffixes: "L|U|LU|UL", fSuffixes: "F", style: "number"}
```

Simple decimal:

```mtsx
{number: "10|F|E", style: "number"}
```

Prefer `number` or a built-in number matcher over a large numeric regex.

## `start/end` String

```mtsx
{
    start: {match: /"/}
    end: {match: /(?m)"|$/}
    style: "string"
    contains: [
        {match: /\\./, 0: "strEscape"}
    ]
}
```

For single quotes:

```mtsx
{
    start: {match: /'/}
    end: {match: /(?m)'|$/}
    style: "string"
    contains: [
        {match: /\\./, 0: "strEscape"}
    ]
}
```

If the language uses Java or C escapes, prefer the built-in quoted-string
matcher from `styles-and-builtins.md`.

## Embedded Language Body

Fixed built-in target:

```mtsx
{
    start: {match: /<script>/}
    end: {match: /<\/script>/}
    childrenSyntax: ".js"
}
```

Dynamic target with a task-local dependency:

```mtsx
{
    start: {match: /<code\s+lang="([^"]*)">/}
    end: {match: /<\/code>/}
    childrenSyntax: {
        capture: 1
        ignoreCase: true
        "toy" => ".toy-child"
        "json" => ".json"
        default => ".json"
    }
    missingStyle: "comment"
}
```

Pass `toy-child.mtsx` with `--syntax-dependency toy-child.mtsx` in both check
and render. Do not add `contains` to either example. See
`embedded-syntax.md` for mapping includes, override order, fallback, and report
expectations.

## Dynamic Fence End

```mtsx
{
    start: {
        match: /(?m)^(`{3,})([^`\r\n]*)$/
        export: 1 => "fence"
        1: "operator"
        2: "type"
    }
    end: {match: /(?m)^/ + var("fence") + /`*[ \t]*$/, 0: "operator"}
    childrenSyntax: {
        capture: 2
        ignoreCase: true
        "js" => ".js"
        default => ".js"
    }
}
```

The captured fence is inserted literally, so a shorter fence cannot satisfy
the dynamic prefix. Keep exports on the direct start and `var()` on the direct
end. See `scope-variables.md` for ordering, atom placement, and performance
limits.

## Capture Group Submatcher

```mtsx
{
    match: /\b(fn)\s+([A-Za-z_][A-Za-z0-9_]*)/
    1: "keyword"
    2: {
        match: /^[A-Z][A-Za-z0-9_]*/
        0: "type"
    }
}
```

The nested matcher runs only inside capture group `2`. Keep it small and
anchored to the captured substring when possible.

## `lineBackground`

```mtsx
styles: [
    "sectionLine", #FFF4CC, #33243A
]
lineBackground: {match: /(?m)^[ \t]*section\b[^\r\n]*/, style: "sectionLine"}
```

The regex must match the full line region. If the pattern only matches a prefix,
the line will not be highlighted.

## Regex Define and Matcher Include

Regex fragment define:

```mtsx
defines: [
    "ident": /[A-Za-z_][A-Za-z0-9_]*/
]
contains: [
    {match: /\btype\s+/ + include("ident"), 0: "type"}
]
```

Matcher define:

```mtsx
defines: [
    "quoted": [
        {builtin: #SINGLE_QUOTED_STRING#}
        {builtin: #DOUBLE_QUOTED_STRING#}
    ]
]
contains: [
    {include: "quoted"}
]
```

Do not confuse `{include: "quoted"}` with `include("ident")`.

## Common Anti-patterns

Unescaped slash inside `/.../`:

```mtsx
{match: /https?://[^\s]+/, 0: "string"}
```

Fix:

```mtsx
{match: /https?:\/\/[^\s]+/, 0: "string"}
```

Or use a string regex:

```mtsx
{match: "https?://[^\\s]+", 0: "string"}
```

`recordAllGroups` in the wrong position:

```mtsx
{
    match: /([A-Za-z_]\w*)/
    1: "variable"
    recordAllGroups: true
}
```

Fix:

```mtsx
{
    match: /([A-Za-z_]\w*)/
    recordAllGroups: true
    1: "variable"
}
```

Missing `end`:

```mtsx
{
    start: {match: /"/}
    style: "string"
}
```

Fix:

```mtsx
{
    start: {match: /"/}
    end: {match: /(?m)"|$/}
    style: "string"
}
```

Combining host children with an embedded language:

```mtsx
{
    start: {match: /<script>/}
    end: {match: /<\/script>/}
    childrenSyntax: ".js"
    contains: [{match: /TODO/, 0: "comment"}]
}
```

Fix by choosing one body owner. Keep `childrenSyntax` for a complete child
language; use `contains` only when the body remains host-defined.

Exporting through an include or consuming a variable outside the direct end is
also invalid. Move the direct match into the same `start/end` scope instead of
trying to create cross-matcher variables.

Large manual keyword alternation:

```mtsx
{match: /\b(if|else|for|while|return|break|continue)\b/, 0: "keyword"}
```

Fix:

```mtsx
{match: keywordsToRegex("if else for while return break continue"), 0: "keyword"}
```

Too-broad catch-all before precise matchers:

```mtsx
contains: [
    {match: /[A-Za-z_][A-Za-z0-9_]*/, 0: "variable"}
    {match: keywordsToRegex("class interface"), 0: "keyword"}
]
```

Fix:

```mtsx
contains: [
    {match: keywordsToRegex("class interface"), 0: "keyword"}
    {match: /[A-Za-z_][A-Za-z0-9_]*/, 0: "variable"}
]
```

## Repair-oriented Examples

If validation reports `REGEX_DELIMITER_ESCAPE`, make the smallest slash escape
change in the reported regex literal.

Before:

```mtsx
{match: /</[A-Za-z][A-Za-z0-9-]*>/, 0: "tagName"}
```

After:

```mtsx
{match: /<\/[A-Za-z][A-Za-z0-9-]*>/, 0: "tagName"}
```

Already escaped slashes must not be escaped again. If there are multiple
possible regex literals near the error, do not auto-repair; inspect the report
and source manually.
