from __future__ import annotations

import argparse
import hashlib
import json
import os
from datetime import UTC, datetime
from pathlib import Path
from tempfile import NamedTemporaryFile


KNOWLEDGE_NAME = "Investment Thesis Analysis & Monitoring Knowledge Guide"
DOCS_PATH = Path("docs/custom_gpt_knowledge_ko.md")
SKILL_PATH = Path(
    ".agents/skills/thesis-monitor-daily-review/references/"
    "investment-thesis-analysis-monitoring-knowledge.md"
)
MANIFEST_PATH = Path(
    ".agents/skills/thesis-monitor-daily-review/references/knowledge-manifest.json"
)


def _atomic_bytes(path: Path, payload: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with NamedTemporaryFile("wb", dir=path.parent, delete=False) as handle:
        handle.write(payload)
        handle.flush()
        os.fsync(handle.fileno())
        temporary = Path(handle.name)
    os.replace(temporary, path)


def _atomic_json(path: Path, payload: dict[str, object]) -> None:
    encoded = (
        json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    ).encode("utf-8")
    _atomic_bytes(path, encoded)


def knowledge_metrics(payload: bytes) -> dict[str, object]:
    return {
        "sha256": hashlib.sha256(payload).hexdigest(),
        "line_count": len(payload.splitlines()),
        "byte_count": len(payload),
    }


def validate_repository_mirror(root: Path) -> dict[str, object]:
    docs = (root / DOCS_PATH).read_bytes()
    runtime = (root / SKILL_PATH).read_bytes()
    manifest = json.loads((root / MANIFEST_PATH).read_text(encoding="utf-8"))
    metrics = knowledge_metrics(docs)
    if docs != runtime:
        raise ValueError("Knowledge docs and runtime mirror are not byte-identical")
    for key in ("sha256", "line_count", "byte_count"):
        if manifest.get(key) != metrics[key]:
            raise ValueError(f"Knowledge manifest mismatch: {key}")
    return metrics


def sync_repository_mirror(
    canonical_source: Path,
    root: Path,
    *,
    mirror_revision: str,
) -> dict[str, object]:
    canonical = canonical_source.read_bytes()
    canonical.decode("utf-8")
    manifest_path = root / MANIFEST_PATH
    previous = json.loads(manifest_path.read_text(encoding="utf-8"))
    metrics = knowledge_metrics(canonical)
    _atomic_bytes(root / DOCS_PATH, canonical)
    _atomic_bytes(root / SKILL_PATH, canonical)
    manifest = {
        "byte_count": metrics["byte_count"],
        "imported_at": datetime.now(UTC).isoformat(),
        "knowledge_name": KNOWLEDGE_NAME,
        "knowledge_version": str(previous.get("knowledge_version") or "unknown"),
        "line_count": metrics["line_count"],
        "mirror_path": str(SKILL_PATH),
        "mirror_revision": mirror_revision,
        "sha256": metrics["sha256"],
        "source": "Custom GPT Knowledge",
        "source_path": str(DOCS_PATH),
        "source_role": "custom_gpt_canonical_mirror",
    }
    _atomic_json(manifest_path, manifest)
    validate_repository_mirror(root)
    return metrics


def _arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Synchronize or validate the Custom GPT Knowledge runtime mirror."
    )
    parser.add_argument("canonical_source", nargs="?", type=Path)
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--check", action="store_true")
    parser.add_argument(
        "--mirror-revision",
        default="canonical-parity-correction",
    )
    return parser.parse_args()


def main() -> None:
    args = _arguments()
    if args.check:
        result = validate_repository_mirror(args.root)
    else:
        if args.canonical_source is None:
            raise SystemExit("canonical_source is required unless --check is used")
        result = sync_repository_mirror(
            args.canonical_source,
            args.root,
            mirror_revision=args.mirror_revision,
        )
    print(json.dumps(result, sort_keys=True))


if __name__ == "__main__":
    main()
