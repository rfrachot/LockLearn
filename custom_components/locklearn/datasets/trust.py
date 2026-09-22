"""Ed25519 trust registry and historical-key semantics."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum

from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey


class TrustError(ValueError):
    """Raised when a signing key or signature is not trusted."""


class KeyStatus(StrEnum):
    """Lifecycle state for a trusted public signing key."""

    ACTIVE = "active"
    DEPRECATED = "deprecated"
    REVOKED = "revoked"


class KeyUsage(StrEnum):
    """Whether validating an historical artifact or authorizing a new build."""

    HISTORICAL = "historical"
    NEW_BUILD = "new_build"


@dataclass(frozen=True, slots=True)
class TrustedKey:
    """One public Ed25519 key and its signed-build validity interval."""

    key_id: str
    public_key: bytes
    valid_from: datetime
    valid_until: datetime
    status: KeyStatus

    def __post_init__(self) -> None:
        if not self.key_id:
            raise TrustError("key_id is required")
        if len(self.public_key) != 32:
            raise TrustError("Ed25519 public keys must contain exactly 32 raw bytes")
        if self.valid_from.tzinfo is None or self.valid_until.tzinfo is None:
            raise TrustError("key validity timestamps must be timezone-aware")
        if self.valid_until <= self.valid_from:
            raise TrustError("key valid_until must be later than valid_from")


class TrustStore:
    """Immutable-by-construction registry containing public keys only."""

    def __init__(self, keys: tuple[TrustedKey, ...]) -> None:
        self._keys = {key.key_id: key for key in keys}
        if len(self._keys) != len(keys):
            raise TrustError("duplicate signing key_id")

    def resolve(self, key_id: str) -> TrustedKey:
        """Resolve a public key without treating manifest data as trust material."""
        try:
            return self._keys[key_id]
        except KeyError as err:
            raise TrustError(f"unknown signing key: {key_id}") from err

    def verify(
        self,
        *,
        key_id: str,
        built_at: datetime,
        manifest_bytes: bytes,
        signature: bytes,
        usage: KeyUsage = KeyUsage.HISTORICAL,
    ) -> TrustedKey:
        """Verify exact manifest bytes and enforce status at the signed build time."""
        key = self.resolve(key_id)
        if len(signature) != 64:
            raise TrustError("SIGNATURE.ed25519 must contain exactly 64 raw bytes")
        try:
            Ed25519PublicKey.from_public_bytes(key.public_key).verify(signature, manifest_bytes)
        except InvalidSignature as err:
            raise TrustError("invalid Ed25519 manifest signature") from err
        if key.status is KeyStatus.REVOKED:
            raise TrustError(f"signing key is revoked: {key_id}")
        if usage is KeyUsage.NEW_BUILD and key.status is not KeyStatus.ACTIVE:
            raise TrustError("new builds require an active signing key")
        if not key.valid_from <= built_at < key.valid_until:
            raise TrustError("signing key was not valid at manifest built_at")
        return key
