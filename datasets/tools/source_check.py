"""Lightweight availability checks for registered build sources."""

from __future__ import annotations

import json
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
BUILD_SOURCES = ROOT / "datasets" / "resources" / "source_builds.json"


def _probe(url: str, timeout: float = 30.0) -> None:
    request = urllib.request.Request(
        url,
        headers={"User-Agent": "LockLearn-source-check/1", "Range": "bytes=0-0"},
    )
    with urllib.request.urlopen(request, timeout=timeout) as response:
        response.read(1)


def check() -> list[dict[str, Any]]:
    document = json.loads(BUILD_SOURCES.read_text(encoding="utf-8"))
    results: list[dict[str, Any]] = []
    for row in document["sources"]:
        if row["fetch_mode"] == "local":
            results.append({"source_id": row["source_id"], "status": "local"})
            continue
        url = row["download_url"] or row["discovery_url"]
        try:
            _probe(url)
        except (OSError, urllib.error.URLError) as err:
            results.append(
                {"source_id": row["source_id"], "status": "unreachable", "error": str(err)}
            )
        else:
            results.append({"source_id": row["source_id"], "status": "ok"})
    return results


def main() -> int:
    results = check()
    print(json.dumps(results, indent=2, sort_keys=True))
    return 1 if any(row["status"] == "unreachable" for row in results) else 0


if __name__ == "__main__":
    raise SystemExit(main())
