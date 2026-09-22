"""Recommended V1 source adapters.

Adapters only parse already-downloaded snapshots. Network access belongs to the
pipeline fetch stage, which keeps raw corpora under ignored build directories.
"""

from __future__ import annotations

import bz2
import gzip
import io
import json
import zipfile
from collections.abc import Iterator
from pathlib import Path
from typing import BinaryIO, cast
from xml.etree import ElementTree

from .base import NormalizedRecord, SourceAdapter


def _binary_stream(path: Path) -> BinaryIO:
    suffix = path.suffix.lower()
    if suffix == ".gz":
        return cast(BinaryIO, gzip.open(path, "rb"))
    if suffix == ".bz2":
        return cast(BinaryIO, bz2.open(path, "rb"))
    return path.open("rb")


class JMdictAdapter:
    """Stream JMdict/JMdict-NG XML and emit one source-native record per sense."""

    source_id = "edrdg:jmdict"
    adapter_id = "jmdict_ng"
    adapter_version = "1"
    emitted_fields = frozenset(
        {
            "japanese_forms",
            "readings",
            "english_glosses",
            "parts_of_speech",
            "restrictions",
            "sense_metadata",
        }
    )
    provenance_fields = frozenset({"source_record_id"})

    def normalize(self, path: Path) -> Iterator[NormalizedRecord]:
        with _binary_stream(path) as stream:
            for _event, element in ElementTree.iterparse(stream, events=("end",)):
                if element.tag.rsplit("}", 1)[-1] != "entry":
                    continue
                entry_seq = _first_text(element, "ent_seq")
                if entry_seq is None:
                    element.clear()
                    continue
                writings = _texts(element, "k_ele", "keb")
                readings = _texts(element, "r_ele", "reb")
                senses = [
                    child for child in element if child.tag.rsplit("}", 1)[-1] == "sense"
                ]
                for index, sense in enumerate(senses, start=1):
                    glosses = []
                    for gloss in _children(sense, "gloss"):
                        lang = (
                            gloss.attrib.get("{http://www.w3.org/XML/1998/namespace}lang")
                            or gloss.attrib.get("lang")
                            or "eng"
                        )
                        if lang in {"eng", "en"} and gloss.text:
                            glosses.append(gloss.text)
                    if not glosses:
                        continue
                    restrictions = [
                        value
                        for name in ("stagk", "stagr")
                        for value in _child_texts(sense, name)
                    ]
                    yield NormalizedRecord(
                        source_id=self.source_id,
                        source_record_id=entry_seq,
                        kind="jmdict_sense",
                        payload={
                            "japanese_forms": writings,
                            "readings": readings,
                            "english_glosses": glosses,
                            "parts_of_speech": _child_texts(sense, "pos"),
                            "restrictions": restrictions,
                            "sense_metadata": {"sense_index": index},
                        },
                    )
                element.clear()


class Kanjidic2Adapter:
    """Stream KANJIDIC2 XML using only P1.7-audited fields."""

    source_id = "edrdg:kanjidic2"
    adapter_id = "kanjidic2"
    adapter_version = "1"
    emitted_fields = frozenset(
        {"literal", "readings", "meanings", "stroke_count", "grade", "frequency", "jlpt_legacy"}
    )
    provenance_fields = frozenset({"source_record_id"})

    def normalize(self, path: Path) -> Iterator[NormalizedRecord]:
        with _binary_stream(path) as stream:
            for _event, element in ElementTree.iterparse(stream, events=("end",)):
                if element.tag.rsplit("}", 1)[-1] != "character":
                    continue
                literal = _first_text(element, "literal")
                if literal is None:
                    element.clear()
                    continue
                readings = [
                    {
                        "type": reading.attrib.get("r_type", "unknown"),
                        "value": reading.text,
                    }
                    for reading in _descendants(element, "reading")
                    if reading.text
                ]
                meanings = [
                    meaning.text
                    for meaning in _descendants(element, "meaning")
                    if meaning.attrib.get("m_lang", "en") == "en" and meaning.text
                ]
                yield NormalizedRecord(
                    source_id=self.source_id,
                    source_record_id=literal,
                    kind="kanjidic2_character",
                    payload={
                        "literal": literal,
                        "readings": readings,
                        "meanings": meanings,
                        "stroke_count": _first_int(element, "stroke_count"),
                        "grade": _first_int(element, "grade"),
                        "frequency": _first_int(element, "freq"),
                        "jlpt_legacy": _first_int(element, "jlpt"),
                    },
                )
                element.clear()


class TatoebaTextAdapter:
    """Parse Tatoeba per-language sentences_detailed TSV exports."""

    source_id = "tatoeba:text"
    adapter_id = "tatoeba_text"
    adapter_version = "1"
    emitted_fields = frozenset(
        {"sentence_id", "text", "language", "author", "license", "translation_links"}
    )
    provenance_fields = frozenset({"source_record_id", "author", "license_id", "language"})

    def normalize(self, path: Path) -> Iterator[NormalizedRecord]:
        with _binary_stream(path) as raw:
            stream = io.TextIOWrapper(raw, encoding="utf-8", newline="")
            for line_number, line in enumerate(stream, start=1):
                row = line.rstrip("\n").split("\t")
                if len(row) != 6:
                    raise ValueError(
                        f"Tatoeba detailed TSV line {line_number} must contain 6 columns"
                    )
                sentence_id, language, text, username, _added, _modified = row
                if not sentence_id or not language or not text or not username:
                    raise ValueError(f"Tatoeba detailed TSV line {line_number} is incomplete")
                yield NormalizedRecord(
                    source_id=self.source_id,
                    source_record_id=sentence_id,
                    kind="tatoeba_sentence",
                    payload={
                        "sentence_id": sentence_id,
                        "text": text,
                        "language": language,
                        "author": username,
                        "license": "CC-BY-2.0-FR",
                        "translation_links": [],
                    },
                    author=username,
                    language=language,
                    license_id="CC-BY-2.0-FR",
                )


class KaikkiAdapter:
    """Stream raw Wiktextract JSONL while retaining only audited textual fields."""

    source_id = "wikimedia:wiktionary-kaikki"
    adapter_id = "wiktextract_kaikki"
    adapter_version = "1"
    emitted_fields = frozenset(
        {"word", "language", "part_of_speech", "senses", "forms", "translations", "examples_text"}
    )
    provenance_fields = frozenset({"source_record_id"})

    def normalize(self, path: Path) -> Iterator[NormalizedRecord]:
        with _binary_stream(path) as raw:
            stream = io.TextIOWrapper(raw, encoding="utf-8")
            for line_number, line in enumerate(stream, start=1):
                if not line.strip():
                    continue
                value = json.loads(line)
                if not isinstance(value, dict):
                    raise ValueError(f"Kaikki line {line_number} must be a JSON object")
                word = value.get("word")
                language = value.get("lang_code") or value.get("lang")
                if not isinstance(word, str) or not word:
                    continue
                record_id = value.get("id")
                if not isinstance(record_id, str) or not record_id:
                    record_id = f"{language or 'und'}:{word}:{line_number}"
                senses = value.get("senses", [])
                forms = value.get("forms", [])
                translations = value.get("translations", [])
                examples: list[str] = []
                if isinstance(senses, list):
                    for sense in senses:
                        if not isinstance(sense, dict):
                            continue
                        for example in sense.get("examples", []):
                            if isinstance(example, dict) and isinstance(example.get("text"), str):
                                examples.append(example["text"])
                yield NormalizedRecord(
                    source_id=self.source_id,
                    source_record_id=record_id,
                    kind="wiktextract_entry",
                    payload={
                        "word": word,
                        "language": language,
                        "part_of_speech": value.get("pos"),
                        "senses": senses,
                        "forms": forms,
                        "translations": translations,
                        "examples_text": examples,
                    },
                )


class KanjiVGAdapter:
    """Read a KanjiVG release ZIP without extracting it to disk."""

    source_id = "kanjivg:svg"
    adapter_id = "kanjivg_svg"
    adapter_version = "1"
    emitted_fields = frozenset({"character", "svg", "stroke_paths", "components"})
    provenance_fields = frozenset({"source_record_id"})

    def normalize(self, path: Path) -> Iterator[NormalizedRecord]:
        with zipfile.ZipFile(path) as archive:
            for name in sorted(archive.namelist()):
                member = Path(name)
                if member.suffix.lower() != ".svg" or member.name.startswith("."):
                    continue
                stem = member.stem.split("-", 1)[0]
                try:
                    character = chr(int(stem, 16))
                except (ValueError, OverflowError):
                    continue
                raw = archive.read(name)
                root = ElementTree.fromstring(raw)
                paths = [
                    child.attrib.get("d", "")
                    for child in root.iter()
                    if child.tag.rsplit("}", 1)[-1] == "path" and child.attrib.get("d")
                ]
                components = sorted(
                    {
                        value
                        for child in root.iter()
                        for key, value in child.attrib.items()
                        if key.rsplit("}", 1)[-1] == "element" and value
                    }
                )
                yield NormalizedRecord(
                    source_id=self.source_id,
                    source_record_id=stem,
                    kind="kanjivg_svg",
                    payload={
                        "character": character,
                        "svg": raw.decode("utf-8"),
                        "stroke_paths": paths,
                        "components": components,
                    },
                )


class LockLearnEditorialAdapter:
    """Read trusted repository-authored JSONL without network access."""

    source_id = "locklearn:original"
    adapter_id = "locklearn_editorial"
    adapter_version = "1"
    emitted_fields = frozenset()
    provenance_fields = frozenset()

    def normalize(self, path: Path) -> Iterator[NormalizedRecord]:
        with path.open("r", encoding="utf-8") as stream:
            for line_number, line in enumerate(stream, start=1):
                if not line.strip():
                    continue
                value = json.loads(line)
                if not isinstance(value, dict):
                    raise ValueError(f"editorial line {line_number} must be a JSON object")
                record_id = value.get("id")
                kind = value.get("kind")
                payload = value.get("payload")
                if (
                    not isinstance(record_id, str)
                    or not record_id
                    or not isinstance(kind, str)
                    or not kind
                    or not isinstance(payload, dict)
                ):
                    raise ValueError(f"editorial line {line_number} has invalid fields")
                yield NormalizedRecord(
                    source_id=self.source_id,
                    source_record_id=record_id,
                    kind=kind,
                    payload=payload,
                    modified_from_source=True,
                )


_ADAPTERS: dict[str, type[SourceAdapter]] = {
    "jmdict_ng": JMdictAdapter,
    "kanjidic2": Kanjidic2Adapter,
    "tatoeba_text": TatoebaTextAdapter,
    "wiktextract_kaikki": KaikkiAdapter,
    "kanjivg_svg": KanjiVGAdapter,
    "locklearn_editorial": LockLearnEditorialAdapter,
}


def adapter_for_id(adapter_id: str) -> SourceAdapter:
    """Instantiate a known build-time adapter by registry adapter_id."""
    try:
        adapter_type = _ADAPTERS[adapter_id]
    except KeyError as err:
        raise ValueError(f"unknown dataset adapter_id: {adapter_id}") from err
    return adapter_type()


def _children(element: ElementTree.Element, local_name: str) -> list[ElementTree.Element]:
    return [child for child in element if child.tag.rsplit("}", 1)[-1] == local_name]


def _descendants(element: ElementTree.Element, local_name: str) -> list[ElementTree.Element]:
    return [child for child in element.iter() if child.tag.rsplit("}", 1)[-1] == local_name]


def _first_text(element: ElementTree.Element, local_name: str) -> str | None:
    for child in element.iter():
        if child.tag.rsplit("}", 1)[-1] == local_name and child.text:
            return child.text
    return None


def _first_int(element: ElementTree.Element, local_name: str) -> int | None:
    value = _first_text(element, local_name)
    if value is None:
        return None
    try:
        return int(value)
    except ValueError:
        return None


def _child_texts(element: ElementTree.Element, local_name: str) -> list[str]:
    return [child.text for child in _children(element, local_name) if child.text]


def _texts(element: ElementTree.Element, container_name: str, value_name: str) -> list[str]:
    result: list[str] = []
    for container in _children(element, container_name):
        result.extend(_child_texts(container, value_name))
    return result
