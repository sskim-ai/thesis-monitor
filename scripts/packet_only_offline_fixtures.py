"""Prepare the exact 16 archived request fixtures, without invoking an inspector or model."""

import argparse
import ast
import stat
import uuid
import zipfile
from pathlib import Path

from packet_only_offline_adapter import (
    APPROVAL_CONTRACT,
    MODEL,
    POLICY,
    canonical,
    digest,
    load_json,
    require,
    split_source,
)

ARCHIVES = {
    "A": (
        "54428273276e986c8fe1c36be705bed3967e8647290b8ebe3cce70fb643de6e7",
        "m12dc-20260919T074953Z-3e1bdeab",
    ),
    "B": (
        "30ba5076bb5785b89ac6e6806e1510f86b772d1dbe24221faa36aaa5bdb2b25c",
        "m12dc-r1-20260919T090738Z-fac9e4cc",
    ),
}


def record(path: Path) -> dict:
    return {"path": str(path.resolve()), "sha256": digest(path.read_bytes())}


def write_json(path: Path, value: object) -> dict:
    path.write_bytes(canonical(value) + b"\n")
    return record(path)


def prepare(a: Path, b: Path, catalog: Path, executable: Path, output: Path) -> dict:
    require(executable.is_absolute() and not executable.is_symlink(), "EXECUTABLE_PATH")
    output.mkdir(parents=True, exist_ok=False)
    models = load_json(catalog.read_bytes())["models"]
    model = next(model for model in models if model["slug"] == MODEL)
    messages = model["model_messages"]
    base = messages["instructions_template"]
    # Exact pinned ModelInfo::get_model_instructions(None) behavior.
    if messages.get("instructions_variables") is not None:
        default = messages["instructions_variables"].get("personality_default") or ""
        base = base.replace("{{ personality }}", default)
    base_path = output / "base-instructions.txt"
    base_path.write_bytes(base.encode())
    fixtures = []
    owners = {}
    owner_sources = {}
    for stage, filename, function in [
        ("A", "m12cr_shadow_contract.py", "future_pass_a_prompt_template"),
        ("B", "m12cv_pass_b_capability_contract.py", "capability_prompt_template"),
    ]:
        path = Path(__file__).parent / filename
        tree = ast.parse(path.read_bytes())
        node = next(
            node
            for node in tree.body
            if isinstance(node, ast.FunctionDef) and node.name == function
        )
        require(
            len(node.body) == 1 and isinstance(node.body[0], ast.Return), "TASK_OWNER_NOT_LITERAL"
        )
        template = ast.literal_eval(node.body[0].value)
        require(isinstance(template, str), "TASK_OWNER_NOT_TEXT")
        owners[stage] = digest(template.encode())
        owner_sources[stage] = {**record(path), "function": function}
    verified_archives = []
    for stage, archive in [("A", a), ("B", b)]:
        expected_hash, prefix = ARCHIVES[stage]
        require(digest(archive.read_bytes()) == expected_hash, "ARCHIVE_IDENTITY")
        with zipfile.ZipFile(archive) as z:
            names = z.namelist()
            require(len(names) == len(set(names)), "DUPLICATE_ARCHIVE_PATH")
            for info in z.infolist():
                require(
                    not Path(info.filename).is_absolute()
                    and ".." not in Path(info.filename).parts
                    and not stat.S_ISLNK(info.external_attr >> 16),
                    "UNSAFE_ARCHIVE_PATH",
                )
            require(z.testzip() is None, "ARCHIVE_CRC")
            manifest_raw = z.read(prefix + "/artifact-manifest.json")
            manifest = load_json(manifest_raw)
            for entry in manifest["files"]:
                data = z.read(prefix + "/" + entry["path"])
                require(
                    digest(data) == entry["sha256"] and len(data) == entry["size"],
                    "ARCHIVE_MANIFEST_DRIFT",
                )
            verified_archives.append(
                {
                    "stage": stage,
                    "sha256": expected_hash,
                    "manifest_sha256": digest(manifest_raw),
                    "manifest_matched": len(manifest["files"]),
                }
            )
            for market, count in [("kr", 3), ("us", 5)]:
                for batch in range(1, count + 1):
                    identity = f"{stage}/{market}/batch-{batch:02d}"
                    source_dir = (
                        f"{prefix}/frozen-requests/pass-{stage.lower()}/{market}/batch-{batch:02d}"
                    )
                    dest = output / identity
                    dest.mkdir(parents=True)
                    refs = {}
                    for name, filename in [
                        ("prompt", "prompt.txt"),
                        ("context", "subject-context.json"),
                        ("schema", "provider-wire-schema.json"),
                    ]:
                        data = z.read(source_dir + "/" + filename)
                        target = dest / filename
                        target.write_bytes(data)
                        refs[name] = record(target)
                    prompt = (dest / "prompt.txt").read_text()
                    context = load_json((dest / "subject-context.json").read_bytes())
                    schema = load_json((dest / "provider-wire-schema.json").read_bytes())
                    task, evidence = split_source(prompt, context, schema, stage)
                    require(owners[stage] == digest(task.encode()), "TASK_OWNER_VARIANCE")
                    fixtures.append(
                        {
                            "id": identity,
                            "stage": stage,
                            "source_archive_sha256": expected_hash,
                            **refs,
                            "sizes": {
                                "original_prompt_bytes": len(prompt.encode()),
                                "task_bytes": len(task.encode()),
                                "evidence_bytes": len(evidence.encode()),
                                "compact_context_bytes": len(canonical(context)),
                                "compact_schema_bytes": len(canonical(schema)),
                            },
                        }
                    )
    source = {
        "contract": "m12dc-archived-offline-source-fixtures-v1",
        "usage": "HISTORICAL_SHAPES_NOT_ACCEPTED_LIVE_CHECKPOINTS",
        "archives": verified_archives,
        "catalog": record(catalog),
        "task_owners": owners,
        "task_owner_sources": owner_sources,
        "fixtures": fixtures,
        "source_prompt_layout_owner": "scripts/m12db_model_view_readiness.py::_prompt",
        "base_owner": "codex_protocol::ModelInfo::get_model_instructions(None)",
    }
    source_record = write_json(output / "source-manifest.json", source)
    executable_record = record(executable)
    requests = []
    for fixture in fixtures:
        prompt = Path(fixture["prompt"]["path"]).read_text()
        context = load_json(Path(fixture["context"]["path"]).read_bytes())
        schema = load_json(Path(fixture["schema"]["path"]).read_bytes())
        task, evidence = split_source(prompt, context, schema, fixture["stage"])
        invocation_id = str(
            uuid.uuid5(
                uuid.NAMESPACE_URL,
                POLICY + fixture["id"] + fixture["prompt"]["sha256"] + executable_record["sha256"],
            )
        )
        frozen = {
            "policy": POLICY,
            "operation": "inspect",
            "invocation_id": invocation_id,
            "executable_sha256": executable_record["sha256"],
            "model": MODEL,
            "effort": "xhigh",
            "source_manifest_sha256": source_record["sha256"],
            "source_prompt_sha256": fixture["prompt"]["sha256"],
            "base_instructions_sha256": digest(base.encode()),
            "task_instructions": task,
            "evidence": evidence,
            "output_schema": schema,
            "managed_fixture": {"scope": "SYNTHETIC_CONFIG_ONLY_LIVE_UNRESOLVED", "layers": []},
        }
        input_record = write_json(output / fixture["id"] / "native-input.json", frozen)
        requests.append(
            {"id": fixture["id"], "invocation_id": invocation_id, "input": input_record}
        )
    approval = {
        "contract": APPROVAL_CONTRACT,
        "operation": "inspect",
        "policy": POLICY,
        "model": MODEL,
        "effort": "xhigh",
        "executable": executable_record,
        "source_manifest": source_record,
        "base_instructions": record(base_path),
        "requests": requests,
    }
    return write_json(output / "approval.json", approval)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    for flag in ["archive-a", "archive-b", "catalog", "executable", "output"]:
        parser.add_argument("--" + flag, type=Path, required=True)
    args = parser.parse_args()
    print(
        canonical(
            prepare(args.archive_a, args.archive_b, args.catalog, args.executable, args.output)
        ).decode()
    )


if __name__ == "__main__":
    main()
