from __future__ import annotations

import argparse
import hashlib
import json
import os
from datetime import UTC, datetime
from pathlib import Path
from tempfile import NamedTemporaryFile


KNOWLEDGE_NAME = "Investment Thesis Analysis & Monitoring Knowledge Guide"
KNOWLEDGE_VERSION = "3.0"
CANONICAL_PATH = Path(
    "docs/knowledge/investment-thesis-analysis-monitoring-knowledge-v3.md"
)
UPLOAD_PATH = Path("docs/custom_gpt_knowledge_ko.md")
ARCHIVE_PATH = Path("docs/knowledge/archive")
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
    canonical = (root / CANONICAL_PATH).read_bytes()
    upload = (root / UPLOAD_PATH).read_bytes()
    runtime = (root / SKILL_PATH).read_bytes()
    manifest = json.loads((root / MANIFEST_PATH).read_text(encoding="utf-8"))
    metrics = knowledge_metrics(canonical)
    if canonical != upload or canonical != runtime:
        raise ValueError(
            "Knowledge canonical, upload artifact, and runtime mirror are not "
            "byte-identical"
        )
    for key in ("sha256", "line_count", "byte_count"):
        if manifest.get(key) != metrics[key]:
            raise ValueError(f"Knowledge manifest mismatch: {key}")
    if manifest.get("knowledge_version") != KNOWLEDGE_VERSION:
        raise ValueError("Knowledge manifest mismatch: knowledge_version")
    if manifest.get("source_path") != str(CANONICAL_PATH):
        raise ValueError("Knowledge manifest mismatch: source_path")
    if manifest.get("upload_artifact_path") != str(UPLOAD_PATH):
        raise ValueError("Knowledge manifest mismatch: upload_artifact_path")
    if manifest.get("mirror_path") != str(SKILL_PATH):
        raise ValueError("Knowledge manifest mismatch: mirror_path")
    return metrics


def sync_repository_mirror(
    root: Path,
    *,
    mirror_revision: str,
) -> dict[str, object]:
    canonical_source = root / CANONICAL_PATH
    try:
        canonical_source.resolve().relative_to((root / ARCHIVE_PATH).resolve())
    except ValueError:
        pass
    else:
        raise ValueError("Archived Knowledge cannot be used as the active source")
    canonical = canonical_source.read_bytes()
    canonical.decode("utf-8")
    metrics = knowledge_metrics(canonical)
    _atomic_bytes(root / UPLOAD_PATH, canonical)
    _atomic_bytes(root / SKILL_PATH, canonical)
    manifest = {
        "byte_count": metrics["byte_count"],
        "created_from": [
            "current-custom-gpt-knowledge",
            "1-thesis_monitor_analysis_knowledge_v2.md",
        ],
        "imported_at": datetime.now(UTC).isoformat(),
        "knowledge_name": KNOWLEDGE_NAME,
        "knowledge_version": KNOWLEDGE_VERSION,
        "line_count": metrics["line_count"],
        "mirror_path": str(SKILL_PATH),
        "mirror_revision": mirror_revision,
        "sha256": metrics["sha256"],
        "source": "Knowledge v3 canonical",
        "source_path": str(CANONICAL_PATH),
        "source_role": "knowledge_v3_canonical",
        "upload_artifact_path": str(UPLOAD_PATH),
    }
    _atomic_json(root / MANIFEST_PATH, manifest)
    validate_repository_mirror(root)
    return metrics


def _arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Synchronize or validate the Knowledge v3 Custom GPT upload artifact "
            "and Codex runtime mirror."
        )
    )
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--check", action="store_true")
    parser.add_argument(
        "--mirror-revision",
        default="knowledge-v3-canonical-activation",
    )
    return parser.parse_args()


def main() -> None:
    args = _arguments()
    if args.check:
        result = validate_repository_mirror(args.root)
    else:
        result = sync_repository_mirror(
            args.root,
            mirror_revision=args.mirror_revision,
        )
    print(json.dumps(result, sort_keys=True))


if __name__ == "__main__":
    main()
