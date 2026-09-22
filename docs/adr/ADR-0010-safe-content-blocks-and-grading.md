# ADR-0010 — Safe content blocks and grading contract

## Status

Accepted for the P1.3 content-block contract on 2026-09-22.

## Context

LockLearn content must support prompt, answer, hint, example, mnemonic and
metadata blocks without letting a renderer infer pedagogical meaning from the
content type alone. Some blocks contain the answer but can still be used before
retrieval if a declared mask is applied. Hints and mnemonics also weaken the
learning signal even when they do not literally contain the final answer.

Third-party dataset content is hostile. Rendering arbitrary HTML, trusting
Markdown extensions, accepting event-handler attributes or loading remote
resources would create an XSS/privacy boundary inside the Home Assistant panel.

Japanese is the first showcase, so text needs reading/furigana/ruby structure,
but the core must not encode Japanese-only behavior or store character offsets
whose meaning differs between Python Unicode code points and JavaScript UTF-16
code units.

`CardDefinition` also needs answer semantics and grading metadata, while ADR-0008
requires progression identity to remain only:

```text
(learning_item_id, prompt_facet_id, answer_facet_id)
```

Changing a grading policy, context hint or presentation block must not reset
progress for the same tested skill.

## Decision

### Content blocks

A `ContentBlock` carries:

```text
content_block_id
learning_item_id
position
kind
role
reveals_answer
mask_strategy
payload
```

Kinds are `text`, `rich_text`, `image` and `audio`. Roles are `prompt`,
`answer`, `hint`, `example`, `mnemonic` and `metadata`. The
`reveals_answer` flag is explicit rather than inferred from role or text.

`answer`, `hint` and `mnemonic` roles stay gated before an unaided attempt.
`blank_term` and `blank_span` are valid only for textual content. P1.3 models
the masking contract; later quiz/cloze work owns selection of concrete blanks.

Image/audio blocks use only a stable `asset_id` reference here. Full Asset
metadata, serving and renderers remain P1.11/P7.3 scope.

### Structured readings

Text payloads may carry:

```text
reading
furigana
ruby_segments[]
```

A ruby segment contains visible text plus an optional reading. Segment text must
concatenate exactly to the visible block text. No code-point/UTF-16 offsets are
stored.

This is language-neutral: Japanese packs can use it for furigana while other
writing systems can reuse the same reading annotation without language branches
in the core.

### Rich text

The canonical signed/runtime representation is a strict AST, not trusted HTML.
The P1.3 allowlist contains only:

```text
document
paragraph
text
emphasis
strong
inline_code
line_break
ruby
```

Unknown node types and unknown attributes fail closed. There are no links,
remote media, style/class fields, raw HTML nodes, scripts or event handlers.
Tree depth, node count and individual text size are bounded.

Literal strings such as `<script>` remain plain text nodes. A future frontend
renderer must map the AST node-by-node to safe DOM/Lit primitives and must never
pass dataset strings to `unsafeHTML`.

Author-facing Markdown may be supported by offline build tooling later, but it
must compile into this canonical allowlisted AST before package publication.
The HA runtime does not need a permissive Markdown/HTML parser.

### Grading metadata

`CardDefinition` carries mutable/non-identifying metadata:

```text
answer_semantics
grading_policy(kind, policy_version)
context_hint_facet_ids[]
```

Answer semantics include `single_value`, `set_of_valid_values`,
`ordered_sequence`, `free_text` and `reserved_rule_based`. Grading policy
kinds include `exact`, `any_of`, `fuzzy_normalized` and
`rule_based_reserved`.

P1.3 defines the contract only. Script-aware normalization is P1.4 and the
runtime grading engine/content-quality workflow is P3.7.

The grading result vocabulary includes:

```text
correct
wrong
unrecognized
```

Only `wrong` is a definitive failure. `unrecognized` means the grader lacks
enough evidence to declare the answer wrong; downstream SRS code must not
reinterpret it as an automatic failure.

None of the grading, context or content-block metadata participates in
`card_key` or `card_definition_id`.

## Alternatives considered

- Arbitrary sanitized HTML: rejected because sanitizer drift and frontend
  rendering mistakes create a much larger attack surface.
- Runtime Markdown parsing: rejected for P1.3 because extensions/raw-HTML
  behavior varies and is unnecessary once a canonical AST exists.
- Store ruby/furigana as character offsets: rejected because Python and
  JavaScript index Unicode differently and edits make offsets fragile.
- Infer `reveals_answer` from role: rejected because masked prompt/example
  blocks can contain answer-bearing source text while hints may be gated without
  literally containing the final answer.
- Put grading policy into card identity: rejected because tuning grading would
  silently reset progression for an unchanged skill.
- Implement fuzzy normalization now: rejected because language/script-aware,
  versioned normalization is explicitly P1.4 scope.

## Consequences

- Dataset rich text has a small auditable attack surface and cannot request
  executable markup or remote resources.
- Renderers receive explicit pedagogical reveal/mask metadata instead of
  guessing from block type.
- Ruby/furigana survives Python/JavaScript boundaries without offset ambiguity.
- Grading policy can evolve without changing progression identity.
- P1.3 does not provide a frontend renderer, SRS mutation, full Asset schema,
  normalization engine, content.db schema or cloze-question generator; those
  remain in their existing work packages.
