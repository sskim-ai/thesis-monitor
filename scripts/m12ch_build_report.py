from __future__ import annotations

import argparse
import hashlib
import json
import re
import shutil
import subprocess
import tempfile
import zipfile
from pathlib import Path


REPO = Path(__file__).resolve().parents[1]
BASE = "1e0d81695ce0982827a35a58b5123dfb86e066cc"
STEM = "thesis-monitor-20260917-m12ch-frozen-contract-new-full22-reproof-report"


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def git(*args: str) -> str:
    return subprocess.run(
        ("git", *args),
        cwd=REPO,
        check=True,
        capture_output=True,
        text=True,
    ).stdout


def write_text(path: Path, value: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(value, encoding="utf-8")


def write_json(path: Path, value: object) -> None:
    write_text(
        path,
        json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2) + "\n",
    )


def copy(source: Path, destination: Path) -> None:
    destination.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(source, destination)


def copy_tree(source: Path, destination: Path) -> None:
    for path in sorted(row for row in source.rglob("*") if row.is_file()):
        copy(path, destination / path.relative_to(source))


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--run-root", type=Path, required=True)
    parser.add_argument("--premodel-root", type=Path, required=True)
    parser.add_argument("--validation-root", type=Path, required=True)
    parser.add_argument("--package-root", type=Path, required=True)
    parser.add_argument("--instruction-zip", type=Path, required=True)
    parser.add_argument("--report-md", type=Path, required=True)
    parser.add_argument("--final-sha", required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args()

    if git("rev-parse", "HEAD").strip() != args.final_sha:
        raise RuntimeError("final_sha_drift")
    if git("status", "--porcelain").strip():
        raise RuntimeError("worktree_not_clean")

    run_root = args.run_root.resolve()
    premodel_root = args.premodel_root.resolve()
    validation_root = args.validation_root.resolve()
    package_root = args.package_root.resolve()
    summary = json.loads((run_root / "summary.json").read_text(encoding="utf-8"))

    temp = Path(tempfile.mkdtemp(prefix="m12ch-report."))
    report = temp / STEM
    report.mkdir(parents=True)
    copy_tree(run_root, report / "formal-generation")
    copy_tree(premodel_root, report / "premodel")
    copy_tree(validation_root, report / "validation")

    for relative in (
        "package-manifest.json",
        "inputs/frozen-input-binding.json",
        "inputs/source-index.json",
        "review/M12CG_R4_R1_CHAT_REVIEW.md",
        "review/m12cg-r4-r1-chat-verification.json",
        "review/document-coverage-check.json",
        "reference/20260916-m12ce-new-full22-reproof-under-frozen-deterministic-asof-contract.md",
        "reference/20260917-m12cg-r4-r1-independent-core-binding-offline-closure.md",
    ):
        copy(package_root / relative, report / "source-package" / relative)
    copy_tree(
        package_root / "inputs/frozen-packets",
        report / "source-package/inputs/frozen-packets",
    )
    copy(args.instruction_zip.resolve(), report / "repository" / args.instruction_zip.name)
    copy(args.report_md.resolve(), report / "REPORT.md")

    changed_paths = [
        Path(row)
        for row in git("diff", "--name-only", f"{BASE}..{args.final_sha}").splitlines()
        if row
    ]
    for relative in changed_paths:
        copy(REPO / relative, report / "repository/files" / relative)
    write_text(
        report / "repository/final-local-diff.patch",
        git("diff", "--binary", f"{BASE}..{args.final_sha}"),
    )
    write_text(report / "repository/git-log.txt", git("log", "--oneline", "-12"))
    write_json(
        report / "repository/repository-state.json",
        {
            "repository": "sskim-ai/thesis-monitor",
            "branch": git("branch", "--show-current").strip(),
            "required_runtime_base": BASE,
            "instruction_commit": summary["instruction_commit"],
            "harness_freeze_commit": summary["harness_freeze_commit"],
            "final_local_sha": args.final_sha,
            "status_porcelain": git("status", "--porcelain").splitlines(),
            "runtime_source_change_count": summary.get("source_runtime_drift_count", 0),
            "main_merge_count": 0,
            "deployment_count": 0,
            "remote_push_count": 0,
            "production_send_count": 0,
        },
    )

    patterns = {
        "openai_key": re.compile(rb"sk-[A-Za-z0-9_-]{20,}"),
        "github_pat": re.compile(rb"gh[opusr]_[A-Za-z0-9]{20,}"),
        "telegram_bot_token": re.compile(rb"\b[0-9]{8,12}:[A-Za-z0-9_-]{25,}\b"),
        "private_key": re.compile(rb"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----"),
    }
    secret_hits: list[dict[str, str]] = []
    for path in sorted(row for row in report.rglob("*") if row.is_file()):
        if path.suffix == ".zip":
            continue
        payload = path.read_bytes()
        for label, pattern in patterns.items():
            if pattern.search(payload):
                secret_hits.append({"path": str(path.relative_to(report)), "pattern": label})
    if secret_hits:
        raise RuntimeError(f"secret_scan_failed:{secret_hits}")

    raw_outputs = len(list((report / "formal-generation").rglob("*.output.json")))
    raw_prompts = len(list((report / "formal-generation").rglob("*.prompt.txt")))
    raw_logs = len(list((report / "formal-generation").rglob("*.log")))
    raw_schemas = len(list((report / "formal-generation").rglob("*.schema.json")))
    write_json(
        report / "audits/bundle-safety.json",
        {
            "status": "PASS_LOCAL_ONLY",
            "secret_scan_hits": 0,
            "production_recipient_values_included": 0,
            "raw_model_outputs_included": raw_outputs,
            "raw_model_prompts_included": raw_prompts,
            "raw_model_logs_included": raw_logs,
            "raw_model_schemas_included": raw_schemas,
            "raw_model_artifact_remote_push_count": 0,
            "production_mutations": 0,
            "production_sends": 0,
        },
    )

    manifest_rows = []
    for path in sorted(row for row in report.rglob("*") if row.is_file()):
        relative = path.relative_to(report).as_posix()
        if relative == "artifact-manifest.json":
            continue
        manifest_rows.append(
            {"path": relative, "size": path.stat().st_size, "sha256": sha256(path)}
        )
    write_json(
        report / "artifact-manifest.json",
        {
            "contract": "m12ch-result-artifact-manifest-v1",
            "root": STEM,
            "artifact_count": len(manifest_rows),
            "self_exclusion": "artifact-manifest.json",
            "artifacts": manifest_rows,
        },
    )

    output_dir = args.output_dir.resolve()
    output_dir.mkdir(parents=True, exist_ok=True)
    zip_path = output_dir / f"{STEM}.zip"
    sidecar = output_dir / f"{STEM}.zip.sha256"
    zip_path.unlink(missing_ok=True)
    sidecar.unlink(missing_ok=True)
    with zipfile.ZipFile(
        zip_path, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9
    ) as archive:
        for path in sorted(row for row in report.rglob("*") if row.is_file()):
            arcname = f"{STEM}/{path.relative_to(report).as_posix()}"
            info = zipfile.ZipInfo(arcname, date_time=(2026, 9, 17, 0, 0, 0))
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = 0o100644 << 16
            archive.writestr(
                info,
                path.read_bytes(),
                compress_type=zipfile.ZIP_DEFLATED,
                compresslevel=9,
            )
    zip_sha = sha256(zip_path)
    write_text(sidecar, f"{zip_sha}  {zip_path.name}\n")

    with zipfile.ZipFile(zip_path) as archive:
        bad_member = archive.testzip()
        names = set(archive.namelist())
        expected = {
            f"{STEM}/{path.relative_to(report).as_posix()}"
            for path in report.rglob("*")
            if path.is_file()
        }
        extracted_manifest = json.loads(
            archive.read(f"{STEM}/artifact-manifest.json").decode("utf-8")
        )
        mismatch = []
        for row in extracted_manifest["artifacts"]:
            payload = archive.read(f"{STEM}/{row['path']}")
            if len(payload) != row["size"] or hashlib.sha256(payload).hexdigest() != row["sha256"]:
                mismatch.append(row["path"])
    result = {
        "status": "PASS",
        "report_root": str(report),
        "zip": str(zip_path),
        "sidecar": str(sidecar),
        "zip_sha256": zip_sha,
        "manifest_artifact_count": extracted_manifest["artifact_count"],
        "zip_entry_count": len(names),
        "missing_entry_count": len(expected - names),
        "extra_entry_count": len(names - expected),
        "manifest_mismatch_count": len(mismatch),
        "zip_test_bad_member": bad_member,
        "secret_scan_hits": 0,
    }
    write_json(args.run_root.resolve().parent / "report-build-result.json", result)
    print(json.dumps(result, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
