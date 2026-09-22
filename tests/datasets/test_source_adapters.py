"""Build-time source adapter tests using tiny synthetic fixtures only."""

from __future__ import annotations

import bz2
import json
import zipfile
from pathlib import Path

from datasets.adapters import (
    JMdictAdapter,
    Kanjidic2Adapter,
    KaikkiAdapter,
    KanjiVGAdapter,
    LockLearnEditorialAdapter,
    TatoebaTextAdapter,
)


def test_jmdict_adapter_emits_source_native_senses(tmp_path: Path) -> None:
    path = tmp_path / "jmdict.xml"
    path.write_text(
        """<JMdict><entry><ent_seq>123</ent_seq>
        <k_ele><keb>休む</keb></k_ele><r_ele><reb>やすむ</reb></r_ele>
        <sense><pos>v5m</pos><gloss>to rest</gloss><gloss xml:lang="fre">se reposer</gloss></sense>
        <sense><gloss>to take a break</gloss></sense>
        </entry></JMdict>""",
        encoding="utf-8",
    )
    records = list(JMdictAdapter().normalize(path))
    assert [record.source_record_id for record in records] == ["123", "123"]
    assert records[0].payload["japanese_forms"] == ["休む"]
    assert records[0].payload["readings"] == ["やすむ"]
    assert records[0].payload["english_glosses"] == ["to rest"]
    assert records[1].payload["sense_metadata"] == {"sense_index": 2}


def test_kanjidic2_adapter_uses_only_audited_fields(tmp_path: Path) -> None:
    path = tmp_path / "kanjidic.xml"
    path.write_text(
        """<kanjidic2><character><literal>休</literal>
        <misc><grade>1</grade><stroke_count>6</stroke_count><freq>500</freq><jlpt>3</jlpt></misc>
        <reading_meaning><rmgroup><reading r_type="ja_on">キュウ</reading>
        <meaning>rest</meaning><meaning m_lang="fr">repos</meaning></rmgroup></reading_meaning>
        </character></kanjidic2>""",
        encoding="utf-8",
    )
    record = next(Kanjidic2Adapter().normalize(path))
    assert record.source_record_id == "休"
    assert record.payload == {
        "literal": "休",
        "readings": [{"type": "ja_on", "value": "キュウ"}],
        "meanings": ["rest"],
        "stroke_count": 6,
        "grade": 1,
        "frequency": 500,
        "jlpt_legacy": 3,
    }


def test_tatoeba_adapter_keeps_sentence_attribution_and_tolerates_extra_columns(
    tmp_path: Path,
) -> None:
    path = tmp_path / "fra_sentences_detailed.tsv.bz2"
    with bz2.open(path, "wt", encoding="utf-8") as stream:
        stream.write("42\tfr\tBonjour.\talice\t2020-01-01\t2020-01-02\textra\n")
    record = next(TatoebaTextAdapter().normalize(path))
    assert record.source_record_id == "42"
    assert record.author == "alice"
    assert record.language == "fr"
    assert record.license_id == "CC-BY-2.0-FR"


def test_kaikki_fallback_identity_is_content_based_not_line_number(tmp_path: Path) -> None:
    value = {"word": "休む", "lang_code": "ja", "pos": "verb", "senses": [{"glosses": ["rest"]}]}
    first = tmp_path / "first.jsonl"
    second = tmp_path / "second.jsonl"
    line = json.dumps(value, ensure_ascii=False)
    first.write_text(line + "\n", encoding="utf-8")
    second.write_text("\n\n" + line + "\n", encoding="utf-8")
    first_record = next(KaikkiAdapter().normalize(first))
    second_record = next(KaikkiAdapter().normalize(second))
    assert first_record.source_record_id.startswith("derived:")
    assert first_record.source_record_id == second_record.source_record_id


def test_kanjivg_adapter_reads_release_zip_without_extracting(tmp_path: Path) -> None:
    path = tmp_path / "kanjivg.zip"
    svg = """<svg xmlns="http://www.w3.org/2000/svg"
        xmlns:kvg="http://kanjivg.tagaini.net">
        <g kvg:element="休"><path d="M1 1L2 2"/></g></svg>"""
    with zipfile.ZipFile(path, "w") as archive:
        archive.writestr("kanji/04f11.svg", svg)
    record = next(KanjiVGAdapter().normalize(path))
    assert record.source_record_id == "04f11"
    assert record.payload["character"] == "休"
    assert record.payload["stroke_paths"] == ["M1 1L2 2"]
    assert record.payload["components"] == ["休"]


def test_locklearn_editorial_adapter_keeps_repository_authored_payload(tmp_path: Path) -> None:
    path = tmp_path / "editorial.jsonl"
    path.write_text(
        json.dumps(
            {"id": "grammar:teiru", "kind": "grammar", "payload": {"title": "〜ている"}},
            ensure_ascii=False,
        )
        + "\n",
        encoding="utf-8",
    )
    record = next(LockLearnEditorialAdapter().normalize(path))
    assert record.source_record_id == "grammar:teiru"
    assert record.modified_from_source is True
    assert record.payload == {"title": "〜ている"}
