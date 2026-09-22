"""P1.2 signed package contract, trust, policy and hostile archive tests."""

from __future__ import annotations

import copy
import hashlib
import json
import sqlite3
import stat
import zipfile
from collections.abc import Callable
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import pytest
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

from custom_components.locklearn.datasets import (
    DEFAULT_ARCHIVE_LIMITS,
    ArchiveLimits,
    DatasetPackageError,
    KeyStatus,
    KeyUsage,
    LicensePolicyError,
    ManifestError,
    OfficialRegistryPolicy,
    TrustedKey,
    TrustError,
    TrustStore,
    parse_manifest,
    serialize_manifest,
    validate_dataset_package,
)
from custom_components.locklearn.datasets.package import (
    ArchiveStructureError,
    DatasetDatabaseError,
    PayloadIntegrityError,
)
from custom_components.locklearn.datasets.policy import (
    LicensePolicyRecord,
    SourcePolicyRecord,
)

# Deterministic test-only key. Production/runtime code contains no private keys.
_TEST_PRIVATE_KEY = Ed25519PrivateKey.from_private_bytes(bytes(range(1, 33)))
_TEST_PUBLIC_KEY = _TEST_PRIVATE_KEY.public_key().public_bytes(
    encoding=serialization.Encoding.Raw,
    format=serialization.PublicFormat.Raw,
)
_BUILT_AT = datetime(2026, 9, 22, 12, tzinfo=UTC)


def _sqlite_bytes(path: Path) -> bytes:
    database = path / "fixture.db"
    with sqlite3.connect(database) as connection:
        connection.execute("CREATE TABLE fixture (value TEXT NOT NULL)")
        connection.execute("INSERT INTO fixture VALUES ('synthetic')")
    return database.read_bytes()


def _sha256(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def _canonical_json(document: dict[str, Any]) -> bytes:
    return (
        json.dumps(document, ensure_ascii=False, separators=(",", ":"), sort_keys=True) + "\n"
    ).encode()


def _base_payloads(tmp_path: Path) -> dict[str, bytes]:
    return {
        "dataset.db": _sqlite_bytes(tmp_path),
        "assets/example.txt": b"synthetic asset\n",
        "LICENSES/CC-BY-SA-4.0.txt": b"Synthetic fixture attribution\n",
    }


def _manifest_document(payloads: dict[str, bytes], *, key_id: str = "test-2026") -> dict[str, Any]:
    roles = {
        "dataset.db": "database",
        "assets/example.txt": "asset",
        "LICENSES/CC-BY-SA-4.0.txt": "license",
    }
    files = [
        {"path": path, "size": len(value), "sha256": _sha256(value), "role": roles[path]}
        for path, value in sorted(payloads.items())
    ]
    return {
        "manifest_version": 1,
        "dataset_id": "locklearn:dataset:synthetic",
        "dataset_version": "1.0.0",
        "built_at": "2026-09-22T12:00:00Z",
        "content_schema_version": 1,
        "minimum_locklearn_version": "0.0.2",
        "build_tool_version": "1.0.0",
        "signing_key_id": key_id,
        "sources": [
            {
                "source_id": "locklearn:original",
                "snapshot_id": "locklearn:snapshot:synthetic-1",
                "upstream_version": "fixture-1",
                "retrieved_at": "2026-09-22T10:00:00Z",
                "source_url": "https://example.invalid/fixture",
                "sha256": "0" * 64,
            }
        ],
        "licenses": [
            {
                "license_id": "CC-BY-SA-4.0",
                "path": "LICENSES/CC-BY-SA-4.0.txt",
            }
        ],
        "item_counts": {"learning_items": 1},
        "added_count": 1,
        "changed_count": 0,
        "removed_count": 0,
        "asset_count": 1,
        "entry_count": len(files),
        "required_free_disk": 1024,
        "canonical_content_hash": "1" * 64,
        "files": files,
    }


def _components(
    tmp_path: Path,
    *,
    mutate_manifest: Callable[[dict[str, Any]], None] | None = None,
    key_id: str = "test-2026",
) -> tuple[bytes, bytes, dict[str, bytes]]:
    payloads = _base_payloads(tmp_path)
    document = _manifest_document(payloads, key_id=key_id)
    if mutate_manifest is not None:
        mutate_manifest(document)
    manifest = _canonical_json(document)
    return manifest, _TEST_PRIVATE_KEY.sign(manifest), payloads


def _write_zip(
    path: Path,
    manifest: bytes,
    signature: bytes,
    members: list[tuple[str | zipfile.ZipInfo, bytes]],
    *,
    include_manifest: bool = True,
    include_signature: bool = True,
) -> Path:
    with zipfile.ZipFile(path, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        if include_manifest:
            archive.writestr("manifest.json", manifest)
        for name, value in members:
            archive.writestr(name, value)
        if include_signature:
            archive.writestr("SIGNATURE.ed25519", signature)
    return path


def _package(
    tmp_path: Path,
    *,
    mutate_manifest: Callable[[dict[str, Any]], None] | None = None,
    mutate_archive: Callable[[dict[str, bytes]], None] | None = None,
    key_id: str = "test-2026",
    filename: str = "synthetic.zip",
) -> Path:
    manifest, signature, payloads = _components(
        tmp_path, mutate_manifest=mutate_manifest, key_id=key_id
    )
    archive_payloads = copy.deepcopy(payloads)
    if mutate_archive is not None:
        mutate_archive(archive_payloads)
    return _write_zip(
        tmp_path / filename,
        manifest,
        signature,
        list(archive_payloads.items()),
    )


def _key(
    *,
    key_id: str = "test-2026",
    status: KeyStatus = KeyStatus.ACTIVE,
    valid_from: datetime = datetime(2026, 1, 1, tzinfo=UTC),
    valid_until: datetime = datetime(2027, 1, 1, tzinfo=UTC),
) -> TrustedKey:
    return TrustedKey(
        key_id=key_id,
        public_key=_TEST_PUBLIC_KEY,
        valid_from=valid_from,
        valid_until=valid_until,
        status=status,
    )


def _validate(
    package: Path,
    *,
    key: TrustedKey | None = None,
    policy: OfficialRegistryPolicy | None = None,
    limits: ArchiveLimits = DEFAULT_ARCHIVE_LIMITS,
    key_usage: KeyUsage = KeyUsage.HISTORICAL,
):
    return validate_dataset_package(
        package,
        trust_store=TrustStore((key or _key(),)),
        policy=policy or OfficialRegistryPolicy.from_repository(),
        limits=limits,
        key_usage=key_usage,
    )


def test_valid_signed_minimal_sqlite_package_passes(tmp_path: Path) -> None:
    result = _validate(_package(tmp_path))
    assert result.manifest.dataset_id == "locklearn:dataset:synthetic"
    assert result.manifest.content_schema_version == 1
    assert result.signing_key.key_id == "test-2026"


def test_manifest_build_is_deterministic(tmp_path: Path) -> None:
    raw, _, _ = _components(tmp_path)
    manifest = parse_manifest(raw)
    assert serialize_manifest(manifest) == raw
    assert parse_manifest(serialize_manifest(manifest)) == manifest


def test_exact_manifest_byte_tamper_breaks_signature(tmp_path: Path) -> None:
    manifest, signature, payloads = _components(tmp_path)
    package = _write_zip(
        tmp_path / "tampered-manifest.zip",
        manifest + b" ",
        signature,
        list(payloads.items()),
    )
    with pytest.raises(TrustError, match="signature"):
        _validate(package)


def test_signature_tamper_fails(tmp_path: Path) -> None:
    manifest, signature, payloads = _components(tmp_path)
    tampered_signature = bytes([signature[0] ^ 1]) + signature[1:]
    package = _write_zip(
        tmp_path / "tampered-signature.zip",
        manifest,
        tampered_signature,
        list(payloads.items()),
    )
    with pytest.raises(TrustError, match="signature"):
        _validate(package)


@pytest.mark.parametrize(
    "path",
    ["dataset.db", "LICENSES/CC-BY-SA-4.0.txt", "assets/example.txt"],
)
def test_payload_byte_tamper_fails_hash(tmp_path: Path, path: str) -> None:
    def tamper(payloads: dict[str, bytes]) -> None:
        payloads[path] += b"tamper"

    with pytest.raises(PayloadIntegrityError):
        _validate(_package(tmp_path, mutate_archive=tamper))


def test_unknown_signing_key_fails(tmp_path: Path) -> None:
    with pytest.raises(TrustError, match="unknown"):
        _validate(_package(tmp_path, key_id="unknown-key"))


def test_revoked_signing_key_always_fails(tmp_path: Path) -> None:
    with pytest.raises(TrustError, match="revoked"):
        _validate(_package(tmp_path), key=_key(status=KeyStatus.REVOKED))


def test_key_invalid_at_signed_build_time_fails(tmp_path: Path) -> None:
    with pytest.raises(TrustError, match="built_at"):
        _validate(
            _package(tmp_path),
            key=_key(valid_from=datetime(2026, 9, 23, tzinfo=UTC)),
        )


def test_deprecated_key_accepts_historical_artifact_but_not_new_build(tmp_path: Path) -> None:
    package = _package(tmp_path)
    deprecated = _key(status=KeyStatus.DEPRECATED)
    assert _validate(package, key=deprecated).manifest.built_at == _BUILT_AT
    with pytest.raises(TrustError, match="active"):
        _validate(package, key=deprecated, key_usage=KeyUsage.NEW_BUILD)


@pytest.mark.parametrize(
    ("missing", "message"),
    [("manifest", "manifest.json"), ("signature", "SIGNATURE.ed25519")],
)
def test_missing_envelope_member_fails(tmp_path: Path, missing: str, message: str) -> None:
    manifest, signature, payloads = _components(tmp_path)
    package = _write_zip(
        tmp_path / f"missing-{missing}.zip",
        manifest,
        signature,
        list(payloads.items()),
        include_manifest=missing != "manifest",
        include_signature=missing != "signature",
    )
    with pytest.raises(ArchiveStructureError, match=message):
        _validate(package)


@pytest.mark.parametrize("duplicate", ["manifest.json", "SIGNATURE.ed25519", "dataset.db"])
def test_duplicate_critical_member_fails(tmp_path: Path, duplicate: str) -> None:
    manifest, signature, payloads = _components(tmp_path)
    members: list[tuple[str | zipfile.ZipInfo, bytes]] = list(payloads.items())
    value = payloads.get(duplicate, manifest if duplicate == "manifest.json" else signature)
    members.append((duplicate, value))
    with pytest.warns(UserWarning, match="Duplicate name"):
        package = _write_zip(tmp_path / "duplicate.zip", manifest, signature, members)
    with pytest.raises(ArchiveStructureError, match="duplicate"):
        _validate(package)


def test_missing_dataset_database_fails(tmp_path: Path) -> None:
    manifest, signature, payloads = _components(tmp_path)
    del payloads["dataset.db"]
    package = _write_zip(tmp_path / "missing-db.zip", manifest, signature, list(payloads.items()))
    with pytest.raises(ArchiveStructureError, match=r"dataset\.db"):
        _validate(package)


@pytest.mark.parametrize(
    "unsafe_name",
    ["/absolute", "../traversal", "assets\\..\\traversal"],
)
def test_unsafe_member_path_fails(tmp_path: Path, unsafe_name: str) -> None:
    manifest, signature, payloads = _components(tmp_path)
    members: list[tuple[str | zipfile.ZipInfo, bytes]] = list(payloads.items())
    members.append((unsafe_name, b"hostile"))
    package = _write_zip(tmp_path / "unsafe-path.zip", manifest, signature, members)
    with pytest.raises(ArchiveStructureError):
        _validate(package)


def test_symlink_member_fails(tmp_path: Path) -> None:
    manifest, signature, payloads = _components(tmp_path)
    symlink = zipfile.ZipInfo("assets/symlink")
    symlink.create_system = 3
    symlink.external_attr = (stat.S_IFLNK | 0o777) << 16
    members: list[tuple[str | zipfile.ZipInfo, bytes]] = list(payloads.items())
    members.append((symlink, b"dataset.db"))
    package = _write_zip(tmp_path / "symlink.zip", manifest, signature, members)
    with pytest.raises(ArchiveStructureError, match="non-regular"):
        _validate(package)


def test_casefold_collision_fails(tmp_path: Path) -> None:
    manifest, signature, payloads = _components(tmp_path)
    members: list[tuple[str | zipfile.ZipInfo, bytes]] = list(payloads.items())
    members.append(("assets/EXAMPLE.txt", b"collision"))
    package = _write_zip(tmp_path / "casefold.zip", manifest, signature, members)
    with pytest.raises(ArchiveStructureError, match="case-insensitive"):
        _validate(package)


def test_undeclared_extra_payload_fails(tmp_path: Path) -> None:
    def extra(payloads: dict[str, bytes]) -> None:
        payloads["assets/undeclared.txt"] = b"extra"

    with pytest.raises(PayloadIntegrityError, match="extra"):
        _validate(_package(tmp_path, mutate_archive=extra))


def test_declared_missing_payload_fails(tmp_path: Path) -> None:
    def missing(payloads: dict[str, bytes]) -> None:
        del payloads["assets/example.txt"]

    with pytest.raises(PayloadIntegrityError, match="missing"):
        _validate(_package(tmp_path, mutate_archive=missing))


def test_wrong_declared_size_fails(tmp_path: Path) -> None:
    def mutate(document: dict[str, Any]) -> None:
        document["files"][0]["size"] += 1

    with pytest.raises(PayloadIntegrityError, match="size"):
        _validate(_package(tmp_path, mutate_manifest=mutate))


def test_wrong_declared_sha256_fails(tmp_path: Path) -> None:
    def mutate(document: dict[str, Any]) -> None:
        document["files"][0]["sha256"] = "f" * 64

    with pytest.raises(PayloadIntegrityError, match="SHA-256"):
        _validate(_package(tmp_path, mutate_manifest=mutate))


@pytest.mark.parametrize(
    ("mutation", "match"),
    [
        (lambda document: document.update(manifest_version=2), "manifest_version"),
        (lambda document: document.update(built_at="not-a-time"), "built_at"),
        (lambda document: document.update(dataset_id="invalid"), "dataset_id"),
        (lambda document: document.update(dataset_version=""), "dataset_version"),
        (lambda document: document.pop("dataset_id"), "missing"),
        (lambda document: document.pop("dataset_version"), "missing"),
        (lambda document: document.update(unknown_critical_field=True), "unknown"),
        (
            lambda document: document["files"][0].update(sha256="not-a-hash"),
            "SHA-256",
        ),
    ],
)
def test_strict_manifest_rejects_invalid_fields(
    tmp_path: Path,
    mutation: Callable[[dict[str, Any]], None],
    match: str,
) -> None:
    with pytest.raises(ManifestError, match=match):
        _validate(_package(tmp_path, mutate_manifest=mutation))


def test_duplicate_logical_source_id_fails(tmp_path: Path) -> None:
    def mutate(document: dict[str, Any]) -> None:
        duplicate = copy.deepcopy(document["sources"][0])
        duplicate["snapshot_id"] = "locklearn:snapshot:synthetic-2"
        document["sources"].append(duplicate)

    with pytest.raises(ManifestError, match="duplicate logical source_id"):
        _validate(_package(tmp_path, mutate_manifest=mutate))


def test_manifest_payload_path_must_be_normalized(tmp_path: Path) -> None:
    def mutate(document: dict[str, Any]) -> None:
        document["files"][0]["path"] = "LICENSES/../license.txt"

    with pytest.raises(ManifestError, match="normalized"):
        _validate(_package(tmp_path, mutate_manifest=mutate))


def _policy(*, license_id: str, commercial: bool, derivatives: bool, allowed: bool):
    return OfficialRegistryPolicy(
        licenses=(
            LicensePolicyRecord(
                license_id=license_id,
                commercial_use_allowed=commercial,
                derivatives_allowed=derivatives,
                official_dataset_allowed=allowed,
            ),
        ),
        sources=(SourcePolicyRecord("locklearn:original", license_id),),
    )


@pytest.mark.parametrize(
    ("license_id", "policy", "message"),
    [
        (
            "LicenseRef-Unknown",
            _policy(license_id="CC-BY-SA-4.0", commercial=True, derivatives=True, allowed=True),
            "unknown",
        ),
        (
            "CC-BY-NC-4.0",
            _policy(license_id="CC-BY-NC-4.0", commercial=False, derivatives=True, allowed=False),
            "commercial",
        ),
        (
            "CC-BY-ND-4.0",
            _policy(license_id="CC-BY-ND-4.0", commercial=True, derivatives=False, allowed=False),
            "derivatives",
        ),
    ],
)
def test_official_policy_rejects_unknown_nc_and_nd(
    tmp_path: Path,
    license_id: str,
    policy: OfficialRegistryPolicy,
    message: str,
) -> None:
    def mutate(document: dict[str, Any]) -> None:
        document["licenses"][0]["license_id"] = license_id

    with pytest.raises(LicensePolicyError, match=message):
        _validate(_package(tmp_path, mutate_manifest=mutate), policy=policy)


def test_official_policy_accepts_commercial_derivative_license(tmp_path: Path) -> None:
    assert _validate(_package(tmp_path)).manifest.licenses[0].license_id == "CC-BY-SA-4.0"


def test_non_sqlite_database_fails(tmp_path: Path) -> None:
    payloads = _base_payloads(tmp_path)
    payloads["dataset.db"] = b"not sqlite"
    document = _manifest_document(payloads)
    manifest = _canonical_json(document)
    package = _write_zip(
        tmp_path / "non-sqlite.zip",
        manifest,
        _TEST_PRIVATE_KEY.sign(manifest),
        list(payloads.items()),
    )
    with pytest.raises(DatasetDatabaseError):
        _validate(package)


def test_corrupt_sqlite_database_fails(tmp_path: Path) -> None:
    payloads = _base_payloads(tmp_path)
    payloads["dataset.db"] = payloads["dataset.db"][:100]
    document = _manifest_document(payloads)
    manifest = _canonical_json(document)
    package = _write_zip(
        tmp_path / "corrupt-sqlite.zip",
        manifest,
        _TEST_PRIVATE_KEY.sign(manifest),
        list(payloads.items()),
    )
    with pytest.raises(DatasetDatabaseError):
        _validate(package)


def test_archive_count_and_expansion_limits_are_enforced(tmp_path: Path) -> None:
    package = _package(tmp_path)
    strict_count = ArchiveLimits(
        max_entries=1,
        max_manifest_bytes=DEFAULT_ARCHIVE_LIMITS.max_manifest_bytes,
        max_signature_bytes=64,
        max_member_uncompressed=DEFAULT_ARCHIVE_LIMITS.max_member_uncompressed,
        max_total_uncompressed=DEFAULT_ARCHIVE_LIMITS.max_total_uncompressed,
        max_total_compressed=DEFAULT_ARCHIVE_LIMITS.max_total_compressed,
        max_expansion_ratio=DEFAULT_ARCHIVE_LIMITS.max_expansion_ratio,
    )
    with pytest.raises(ArchiveStructureError, match="entry-count"):
        _validate(package, limits=strict_count)

    strict_ratio = ArchiveLimits(
        max_entries=DEFAULT_ARCHIVE_LIMITS.max_entries,
        max_manifest_bytes=DEFAULT_ARCHIVE_LIMITS.max_manifest_bytes,
        max_signature_bytes=64,
        max_member_uncompressed=DEFAULT_ARCHIVE_LIMITS.max_member_uncompressed,
        max_total_uncompressed=DEFAULT_ARCHIVE_LIMITS.max_total_uncompressed,
        max_total_compressed=DEFAULT_ARCHIVE_LIMITS.max_total_compressed,
        max_expansion_ratio=1.0,
    )
    with pytest.raises(ArchiveStructureError, match="expansion-ratio"):
        _validate(package, limits=strict_ratio)


def test_trust_store_rejects_duplicate_keys() -> None:
    with pytest.raises(TrustError, match="duplicate"):
        TrustStore((_key(), _key()))


def test_validation_errors_are_package_or_contract_errors(tmp_path: Path) -> None:
    with pytest.raises((DatasetPackageError, ManifestError, TrustError, LicensePolicyError)):
        _validate(tmp_path / "not-a-zip")


def test_registry_policy_enforces_source_field_allowlist() -> None:
    policy = OfficialRegistryPolicy.from_repository()
    policy.validate_import_fields("edrdg:kanjidic2", {"literal", "readings", "stroke_count"})
    with pytest.raises(LicensePolicyError, match="not allowlisted"):
        policy.validate_import_fields("edrdg:kanjidic2", {"literal", "search_codes"})


def test_registry_policy_requires_tatoeba_sentence_attribution() -> None:
    policy = OfficialRegistryPolicy.from_repository()
    required = {"source_record_id", "author", "license_id", "language"}
    policy.validate_provenance_fields("tatoeba:text", required)
    with pytest.raises(LicensePolicyError, match="required provenance"):
        policy.validate_provenance_fields("tatoeba:text", {"source_record_id", "language"})


def test_registry_policy_keeps_software_and_content_license_scopes_separate() -> None:
    policy = OfficialRegistryPolicy(
        licenses=(
            LicensePolicyRecord(
                license_id="MIT",
                commercial_use_allowed=True,
                derivatives_allowed=True,
                official_dataset_allowed=True,
                allowed_scopes=frozenset({"software"}),
            ),
        ),
        sources=(
            SourcePolicyRecord(
                source_id="locklearn:original",
                license_id="MIT",
                license_scope="editorial",
            ),
        ),
    )
    manifest = parse_manifest(_components(Path("."))[0])
    with pytest.raises(LicensePolicyError, match="scope"):
        policy.validate(manifest)
