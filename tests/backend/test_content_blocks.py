"""P1.3 content blocks, grading metadata and rich-text security tests."""

import pytest

from custom_components.locklearn.core import content as m
from custom_components.locklearn.core import content_blocks as cb


def _item_and_facets() -> tuple[m.LearningItem, m.Facet, m.Facet]:
    item = m.LearningItem(
        "locklearn:item:rest",
        "locklearn:dataset:starter",
        m.ContentType.VOCABULARY,
        ("edrdg:concept:1",),
    )
    prompt = m.Facet(
        "locklearn:facet:rest-prompt",
        item.learning_item_id,
        m.FacetKind.TEXT,
        "prompt",
        "ja",
        "Jpan",
    )
    answer = m.Facet(
        "locklearn:facet:rest-answer",
        item.learning_item_id,
        m.FacetKind.TEXT,
        "answer",
        "fr",
        "Latn",
    )
    return item, prompt, answer


def _text_block(
    *,
    role: cb.ContentRole = cb.ContentRole.PROMPT,
    reveals_answer: bool = False,
    mask_strategy: cb.MaskStrategy = cb.MaskStrategy.NONE,
) -> cb.ContentBlock:
    return cb.ContentBlock(
        content_block_id="locklearn:block:rest-prompt",
        learning_item_id="locklearn:item:rest",
        position=0,
        kind=cb.ContentBlockKind.TEXT,
        role=role,
        reveals_answer=reveals_answer,
        payload=cb.TextContent("休む"),
        mask_strategy=mask_strategy,
    )


def test_grading_metadata_does_not_change_card_identity() -> None:
    item, prompt, answer = _item_and_facets()
    baseline = m.CardDefinition.from_facets(item, prompt, answer)
    fuzzy = m.CardDefinition.from_facets(
        item,
        prompt,
        answer,
        answer_semantics=m.AnswerSemantics.FREE_TEXT,
        grading_policy=m.GradingPolicy(
            m.GradingPolicyKind.FUZZY_NORMALIZED,
            policy_version=2,
        ),
    )

    assert baseline.card_key == fuzzy.card_key
    assert baseline.card_definition_id == fuzzy.card_definition_id
    assert fuzzy.answer_semantics is m.AnswerSemantics.FREE_TEXT
    assert fuzzy.grading_policy.policy_version == 2


def test_context_hint_facets_are_validated_but_not_part_of_identity() -> None:
    item, prompt, answer = _item_and_facets()
    hint = m.Facet(
        "locklearn:facet:rest-context",
        item.learning_item_id,
        m.FacetKind.TEXT,
        "part-of-speech",
        "en",
        "Latn",
    )
    without_hint = m.CardDefinition.from_facets(item, prompt, answer)
    with_hint = m.CardDefinition.from_facets(
        item,
        prompt,
        answer,
        context_hints=(hint,),
    )
    assert without_hint.card_key == with_hint.card_key
    assert with_hint.context_hint_facet_ids == (hint.facet_id,)

    foreign_hint = m.Facet(
        "locklearn:facet:foreign-context",
        "locklearn:item:other",
        m.FacetKind.TEXT,
        "context",
    )
    with pytest.raises(m.ContentModelError, match="context hint facet"):
        m.CardDefinition.from_facets(
            item,
            prompt,
            answer,
            context_hints=(foreign_hint,),
        )


def test_content_block_reveal_metadata_is_explicit_and_hint_roles_stay_gated() -> None:
    prompt = _text_block()
    masked_answer = _text_block(
        role=cb.ContentRole.PROMPT,
        reveals_answer=True,
        mask_strategy=cb.MaskStrategy.BLANK_TERM,
    )
    mnemonic = _text_block(role=cb.ContentRole.MNEMONIC)

    assert prompt.requires_reveal_action is False
    assert masked_answer.reveals_answer is True
    assert masked_answer.mask_strategy is cb.MaskStrategy.BLANK_TERM
    assert masked_answer.requires_reveal_action is False
    assert mnemonic.requires_reveal_action is True


def test_masking_requires_declared_answer_revelation() -> None:
    with pytest.raises(cb.ContentBlockError, match="reveals_answer=true"):
        _text_block(mask_strategy=cb.MaskStrategy.BLANK_TERM)


def test_answer_role_must_declare_answer_revelation() -> None:
    with pytest.raises(cb.ContentBlockError, match="answer blocks"):
        _text_block(role=cb.ContentRole.ANSWER)


def test_content_block_payload_must_match_declared_kind() -> None:
    with pytest.raises(cb.ContentBlockError, match="rich_text block payload"):
        cb.ContentBlock(
            content_block_id="locklearn:block:bad",
            learning_item_id="locklearn:item:rest",
            position=0,
            kind=cb.ContentBlockKind.RICH_TEXT,
            role=cb.ContentRole.PROMPT,
            reveals_answer=False,
            payload=cb.TextContent("plain text"),
        )


def test_span_and_term_masks_are_text_only() -> None:
    with pytest.raises(cb.ContentBlockError, match="only valid for text/rich_text"):
        cb.ContentBlock(
            content_block_id="locklearn:block:image",
            learning_item_id="locklearn:item:rest",
            position=0,
            kind=cb.ContentBlockKind.IMAGE,
            role=cb.ContentRole.PROMPT,
            reveals_answer=False,
            payload=cb.MediaReference("locklearn:asset:rest"),
            mask_strategy=cb.MaskStrategy.BLANK_SPAN,
        )


def test_ruby_segments_are_structured_without_unicode_offsets() -> None:
    content = cb.TextContent(
        text="休む",
        reading="やすむ",
        furigana="やすむ",
        ruby_segments=(
            cb.RubySegment("休", "やす"),
            cb.RubySegment("む"),
        ),
    )
    assert "".join(segment.text for segment in content.ruby_segments) == content.text
    assert content.ruby_segments[0].reading == "やす"

    with pytest.raises(cb.ContentBlockError, match="concatenate"):
        cb.TextContent(
            text="休む",
            ruby_segments=(cb.RubySegment("休", "やす"),),
        )


def test_safe_rich_text_ast_accepts_only_allowlisted_nodes() -> None:
    document = cb.parse_rich_text_ast(
        {
            "type": "document",
            "children": [
                {
                    "type": "paragraph",
                    "children": [
                        {"type": "text", "text": "読む "},
                        {
                            "type": "strong",
                            "children": [{"type": "text", "text": "practice"}],
                        },
                        {"type": "line_break"},
                        {"type": "ruby", "text": "本", "reading": "ほん"},
                    ],
                }
            ],
        }
    )
    assert document.children[0].node_type is cb.RichTextNodeType.PARAGRAPH
    assert document.children[0].children[-1].node_type is cb.RichTextNodeType.RUBY


@pytest.mark.parametrize(
    "node",
    [
        {"type": "html", "text": "<script>alert(1)</script>"},
        {"type": "link", "href": "javascript:alert(1)", "text": "click"},
        {"type": "image", "src": "https://attacker.invalid/x"},
        {"type": "text", "text": "safe", "onclick": "alert(1)"},
    ],
)
def test_safe_rich_text_ast_rejects_html_links_remote_media_and_extra_attributes(
    node: dict[str, object],
) -> None:
    with pytest.raises(cb.ContentBlockError):
        cb.parse_rich_text_ast(
            {
                "type": "document",
                "children": [{"type": "paragraph", "children": [node]}],
            }
        )


def test_html_like_characters_remain_plain_text_not_markup() -> None:
    document = cb.parse_rich_text_ast(
        {
            "type": "document",
            "children": [
                {
                    "type": "paragraph",
                    "children": [{"type": "text", "text": "<script>alert(1)</script>"}],
                }
            ],
        }
    )
    assert document.children[0].children[0].text == "<script>alert(1)</script>"


def test_unrecognized_grading_is_not_a_definitive_failure() -> None:
    assert m.GradingOutcome.WRONG.is_definitive_failure is True
    assert m.GradingOutcome.UNRECOGNIZED.is_definitive_failure is False


def test_grading_policy_version_must_be_positive() -> None:
    with pytest.raises(m.ContentModelError, match="policy_version"):
        m.GradingPolicy(m.GradingPolicyKind.EXACT, policy_version=0)
