# Start/End Scope Variables

Load this reference when an end delimiter must reuse text captured by the
corresponding start delimiter, such as Markdown fences, heredoc markers, or raw
string tags.

## Canonical Shape

```mtsx
{
    start: {
        match: /(?m)^(`{3,})([^`\r\n]*)$/
        export: 1 => "fence"
        1: "operator"
        2: "type"
    }
    end: {
        match: /(?m)^/ + var("fence") + /`*[ \t]*$/
        0: "operator"
    }
    childrenStyle: "string"
}
```

`export` saves a start match range under a scope-local name. `var("name")`
inserts that captured text as one regex-literal atom when the direct end matcher
is activated. The captured text is escaped; it is never interpreted as regex
source.

## Placement And Ordering

Bindings are deliberately limited to one direct `start/end` scope:

- The exporter must be the direct `match` matcher in `start`.
- The consumer must be the direct `match` matcher in `end`.
- An export does not cross `{include: ...}`, a nested matcher, a nested
  `start/end`, or a `group` boundary.
- `var()` is illegal in `defines`, the start matcher, ordinary `contains`, and
  every other static match field.

Inside the direct start `match`, keep this order:

1. `match`
2. optional `recordAllGroups`
3. one or more `export` entries
4. capture-group styles or submatchers

For example:

```mtsx
start: {
    match: /(?m)^([A-Z]+):(.*)$/
    recordAllGroups: true
    export: 1 => "tag"
    1: "operator"
    2: "string"
}
```

## Binding Rules

- The export group may be `0` for the complete start match or `1..N` for a
  capture group.
- Every exported group must participate in the concrete start match and its
  captured range must be fully inside the complete start match. If any export
  is unmatched, or a lookaround captures outside that range, the engine rejects
  this start/end candidate rather than establishing a dynamic scope.
- Each capture group can be exported at most once and each variable name must
  be unique in the start matcher.
- Every export must be referenced by the direct end matcher. An unused export
  is a compile error.
- Every `var()` must name an export from the same scope. The same variable may
  occur more than once in the end expression.
- Variable names are non-empty MTSX strings and are case-sensitive.
- `var()` must occupy a complete regex atom position. Do not place it inside a
  character class or splice it into the middle of another token.

Good:

```mtsx
end: {match: /(?m)^/ + var("tag") + /[ \t]*$/}
```

Bad:

```mtsx
end: {match: /[/ + var("tag") + /]/}
```

The bad form tries to put the generated atom inside a character class and is
rejected. Put static character classes in their own fragments.

Capture validity depends on the input, so it cannot always be diagnosed while
compiling the syntax. This start has a usable export for a three-backtick
opener:

```mtsx
start: {match: /(`{3,})/ export: 1 => "fence"}
```

These starts match their sample text as regular expressions, but their exports
invalidate the whole start/end candidate:

```mtsx
// On ``` the optional group does not participate.
start: {match: /(x)?```/ export: 1 => "prefix"}

// On ```x the lookahead captures beyond the complete match.
start: {match: /```(?=(x))/ export: 1 => "suffix"}
```

For an optional or lookaround-based export, render one sample where the group
is present inside the opener and one where it is absent or outside the opener;
verify that only the valid candidate establishes the scope.

## Literal Semantics

If the start captures `a+b`, `var("tag")` matches the three literal characters
`a+b`; the `+` does not become a quantifier. Do not pre-escape the captured text
and do not wrap `var()` in `\Q...\E` yourself.

Static fragments around `var()` follow the normal MTSX escaping rules:

```mtsx
end: {match: "(?m)^" + var("tag") + "[ \\t]*$"}
```

`var()` preserves the static capture-group numbering of the end expression. It
does not add a user-visible capturing group.

## Design And Performance Boundary

Use a scope variable only when the opener truly determines the closer. A fixed
end regex is simpler for ordinary quotes, comments, and tags.

Export short delimiter metadata, not arbitrary body text. The expanded dynamic
regex source is limited to 4096 characters. Each distinct captured value may
require a regex compilation; a small execution-local cache reuses repeated
values but is not a reason to export high-cardinality identifiers. Samples
should include multiple delimiters and a repeated delimiter to expose both
correctness and avoidable compilation churn.

For fence-like syntax, test at least:

- a valid opener and matching closer;
- a shorter closer that must not terminate the scope;
- regex metacharacters in the captured delimiter when the language permits
  them, proving literal handling;
- a missing closer under the intended `mustMatchEnd` behavior;
- child-language content when `childrenSyntax` is also present.

`export`/`var()` works with either normal `contains` scanning or
`childrenSyntax`. With `childrenSyntax`, `matchEndFirst` defaults to `true`,
finding the dynamic end first. Explicit `false` makes that end compete with the
entire child root. Captured text remains literal in either mode. See
`embedded-syntax.md` for priority and boundary handling.

The canonical regression fixture combining dynamic fences and an embedded
custom dependency is `fixtures/embedded-scope-host.mtsx`.
