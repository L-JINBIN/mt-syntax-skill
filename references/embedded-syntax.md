# Embedded Syntax With `childrenSyntax`

Load this reference when a `start/end` body should be highlighted by another
installed or task-local language. `childrenSyntax` is for a real language
boundary; keep ordinary host tokens in `contains`.

## Contents

- Boundary and field rules
- Fixed target
- Dynamic selector
- Reusable mappings
- Custom dependency bundles
- Fallback and validation

## Boundary And Field Rules

`childrenSyntax` belongs to a `start/end` matcher and applies only to the body
between the matched delimiters:

```mtsx
{
    start: {match: /<script>/}
    end: {match: /<\/script>/}
    style: "tag"
    childrenStyle: "default"
    childrenSyntax: ".js"
    missingStyle: "comment"
}
```

Keep `start` and `end` first in generated blocks. The remaining relevant fields
are `style`, `childrenStyle`, `mustMatchEnd`, `matchEndFirst`, `endPriority`,
`childrenSyntax`, and `missingStyle`.

Rules:

- `childrenSyntax` and `contains` are mutually exclusive.
- With `childrenSyntax`, omitted `matchEndFirst` means `true`: the host finds
  a hard end boundary before running the child. Explicit `false` makes the host
  end and the entire child root compete at each token boundary. Child strings
  and comments can therefore consume text containing the host delimiter.
- In competing mode, `endPriority: 0` tries the host end first; any positive
  value tries the entire child root first. The default hard-boundary mode
  ignores this priority. The child input extends to the parent EOF; accepted
  body styles and nested contexts are clipped to the actual closing boundary.
- In competing mode, a failed child scope (for example, one missing its required
  end) rolls back its styles and nested contexts. Its strings and comments no
  longer shield host delimiters: the host resumes matching under its own rules,
  so a delimiter inside the failed scope may now close the host.
- `childrenStyle` is optional and falls back to `style`; if both are absent the
  normal default style is used.
- `missingStyle` is optional. It falls back through `childrenStyle`, then
  `style`, then the normal default style.
- A missing target language is valid. It does not make the host fail to compile.

Target strings are non-empty and may be either a language name such as
`"JavaScript"` or a suffix such as `".js"`.

## Fixed Target

Use a fixed target when the region always contains one language:

```mtsx
{
    start: {match: /<style>/}
    end: {match: /<\/style>/}
    childrenSyntax: "CSS"
}
```

Prefer the stable language name or suffix used by the installed syntax. Do not
copy CSS matchers into the host merely to keep the host flat.

## Dynamic Selector

Use a direct `match` start capture when the opener chooses the child language:

```mtsx
{
    start: {match: /<code\s+lang="([^"]*)">/}
    end: {match: /<\/code>/}
    childrenSyntax: {
        capture: 1
        ignoreCase: true
        "" => ".js"
        "js" => "JavaScript"
        "css" => ".css"
        "json" => ".json"
        "default" => ".json"
        default => ".js"
    }
    missingStyle: "comment"
}
```

Dynamic selector rules:

- `start` must be a direct `match` matcher. `capture` may be `0` for the whole
  start match or `1..N` for an actual capture group.
- `ignoreCase` controls only selector comparison and duplicate detection. It
  must follow `capture` and precede every `include` or mapping. If omitted, it
  inherits the language-level `ignoreCase` value.
- A quoted selector may be empty. Empty strings are not legal in ordinary MTSX
  string fields.
- Quoted `"default"` is an ordinary selector. Bare `default` is the optional
  fallback used when the capture is absent or no explicit selector matches.
- Explicit selectors always win. A matched selector whose target is missing
  does not continue to bare `default`.
- Every target string must be non-empty. The target is resolved only when the
  execution program is built, so absent languages remain a valid fallback case.

## Reusable Mappings

Define shared explicit selectors in `defines`:

```mtsx
defines: [
    "webLanguages": {
        "" => ".js"
        "js" => "JavaScript"
        "css" => ".css"
        "json" => ".json"
    }
]
contains: [
    {
        start: {match: /<code\s+lang="([^"]*)">/}
        end: {match: /<\/code>/}
        childrenSyntax: {
            capture: 1
            ignoreCase: true
            include: "webLanguages"
            "javascript" => ".js"
            default => ".json"
        }
    }
]
```

A mapping define contains at least one quoted selector and cannot contain
`capture`, `ignoreCase`, bare `default`, or another `include`. Regex, matcher,
and children-syntax mapping defines share one name space.

At the use site, all `include` entries come before local selectors. Earlier
includes are overlaid by later includes, then local selectors overlay all
included mappings. Duplicate selectors within one layer are errors; the use
site's `ignoreCase` decides whether case-only variants collide. Bare `default`
is separate from this overlay.

## Custom Dependency Bundles

Built-in target languages resolve from the bundled registry automatically. A
task-local custom target must be passed as a repeatable dependency to each mode
used for that bundle (render, check, inspect, explanation or performance):

```bash
python3 scripts/run-validator.py \
  --syntax-file host.mtsx \
  --syntax-dependency child-a.mtsx \
  --syntax-dependency child-b.mtsx \
  --sample-file sample.txt \
  --html host.html \
  --report host.render.json
```

The root and dependencies form one private resolver view for that invocation.
Task-local names and suffixes override bundled languages only inside the bundle.
Dependencies may refer to each other, but every task-local language needed for
the exercised path must be passed once. Duplicate external language names are
compile errors; do not rely on argument order to choose between them.

Preserve dependency order across related invocations and keep their original
reports. If a model-written summary is requested, its dependency list must use
the same order. The CLI report exposes that order in `syntaxDependencies` and
records each compiled child reference in
`dependencyResolution` as `{reference,resolvedLanguage,missing}`.

## Fallback And Validation

For a new bundle or routing redesign, cover the introduced selectors and
boundaries below. For a local edit, cover affected paths and shared neighboring
boundaries; reuse existing regression samples for the rest.

- selectors expected in the affected ordinary input;
- task-local custom targets when the task uses them;
- bare `default`, when declared;
- an intentional unknown or absent target when `missingStyle` matters;
- an end-like token inside child code, proving the host boundary is correct.

For any missing reference found while compiling the program, expect a
`CHILD_SYNTAX_MISSING` warning diagnostic and a human-readable string in
`warnings`; `dependencyResolution` records it even when no sample reaches that
branch. With a sample, `contextSummary.missingCount` counts missing child
regions actually executed. This is not a compile failure. Decide from the task
intent and rendered fallback whether it is accepted or a missing dependency
argument.

Compare the languages expected in the sample with `contextSummary.languages`
and inspect `missingCount` for unexpected fallback. A resolved reference in
`dependencyResolution` proves availability, not that the sample exercised it.
Conversely, an intentional unresolved mapping may have zero executed missing
regions when the sample never selects it.

The context summary aggregates regions and languages; it does not identify
individual selectors or prove their coverage. Tie each intended selector and
boundary case to a sample region and inspect its rendered tokens. Several
selectors can resolve to the same language, so a matching language list alone
cannot establish that every branch worked.

In the final representative HTML, verify child tokens use the target language's
classes, host delimiters retain host styles, and missing bodies use the intended
fallback. The following canonical fixtures are optional reference or diagnostic
examples, not mandatory runs for every syntax edit:

- `fixtures/html-embedded.mtsx` with
  `fixtures/html-embedded-sample.html` covers HTML to JavaScript, CSS, and JSON.
- `fixtures/embedded-scope-host.mtsx` with
  `fixtures/embedded-child.mtsx` and
  `fixtures/embedded-scope-sample.txt` covers dynamic fences, custom-to-custom
  resolution, a built-in target, and intentional missing fallback.
