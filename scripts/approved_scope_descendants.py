"""Exact accepted descendants for historical global scope freezes, not path exemptions."""
from hashlib import sha256
import json
from pathlib import Path
import subprocess


# Each pin names the implementation owner reviewed under its frozen instruction.
PINS = {
    "app/services/ai_review_service.py": ("M12DI", "5c757226f8c447cb93508e7bb34017c7b0f71af3"),
    "tests/test_ai_review_service.py": ("M12DI", "5c757226f8c447cb93508e7bb34017c7b0f71af3"),
    "app/services/financial_backfill_service.py": ("M12DQ", "d9907928dd659325fcec074f727e2005871acd79"),
    **{p: ("M12DS-R4-R1", "24cab21ba006412dcd11d22ada4c2fd6eab07a88") for p in (
        "app/macro/briefing.py",
        "app/services/night_futures_visibility_service.py",
        "app/services/valuation_snapshot_service.py",
    )},
    "app/services/sec_financial_snapshot_service.py": (
        "M12DS-R4-R3", "b3f89e4546b4d0783ba76870d2e890fe31b07e0d"),
    "app/services/daily_digest_renderer.py": ("M12DS-R4-R1", "dc8561e0fa199e5360eb4fda4bd59ac72fdffe09"),
}

CONTRACT = "m12ds-r5-r1-clean-history-provenance-v1"
ATTESTATION_PATH = Path(__file__).resolve().parents[1] / "docs/architecture/M12DS_R5_CLEAN_HISTORY_PROVENANCE.json"
CLEAN_IDENTITY = {
    "contract": CONTRACT,
    "mode": "REVIEWED_CLEAN_HISTORY",
    "clean_root_sha": "33d051ed80fface5741f59a4bff2de8794808931",
    "clean_root_tree_sha": "4c3443c1ae5221aed91cb846bb7a020f38fa1497",
    "parent_main_sha": "9b1fe2de10ff3a4d6b25b17bf1b6e24e5a5ac479",
    "approved_reference_sha": "ac2fa4aa6fe8e34af6b06b66829537eb0818ebe6",
    "result_zip_sha256": "27e0275ce59069c3afa6baea5d21afdaf36ddfa3302f98d93993cd41298f125a",
    "review_zip_sha256": "8a98ec82c27fae6776fed2b846631c6acf8b985f98158f1c49a5d6c9cc8d6012",
    "clean_history_report_sha256": "481ce342cd93b3aedd3bbd3de07e07643da31993d202d44a820bb21e5787dcfa",
}
# Independent reviewed hashes prevent the mutable attestation from authorizing new bytes.
REVIEWED_HASHES = {
    "app/services/ai_review_service.py": "db144a5c3957ce159f40849c5c22cf588cb7d3dd90889fcedc5fee309eb0f736",
    "tests/test_ai_review_service.py": "045624373d32a80877f90c209ce108b338289071c3bebc6a9184ab496106efc7",
    "app/services/financial_backfill_service.py": "9e04ad1391511448fb71ae02fc8be126ccef67f8e39d66e688ccf1d0c000857b",
    "app/macro/briefing.py": "dfca433901d2b9e8b6a9477a29bf35b362d2e890afc556ec7233496f31d27928",
    "app/services/night_futures_visibility_service.py": "fb6ddf374d66a8af939251175dfa28dd286070ee4aa67dd5abb0dec105e43062",
    "app/services/valuation_snapshot_service.py": "93099f9a896cab602337af045254fe0d038aae7d8393b2e49c63f7479ca5846a",
    "app/services/sec_financial_snapshot_service.py": "4976b66380a9a54607119483edb846134b9bdf2dc5070c9983c28a0fd96dc4e9",
    "app/services/daily_digest_renderer.py": "d662bcbd55d8f131c8350be4487066c54532c7249902d40baa8aebd45cdfed8c",
}


def _git(*args):
    return subprocess.check_output(["git", *args], stderr=subprocess.DEVNULL, timeout=10)


def _ancestor(commit):
    try:
        _git("merge-base", "--is-ancestor", commit, "HEAD")
        return True
    except (subprocess.SubprocessError, OSError):
        return False


def _unique_keys(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError("duplicate_attestation_key")
        result[key] = value
    return result


def _clean_approval(path, observed):
    expected_rows = [{"path": p, "owner": owner, "historical_pin": commit,
                      "sha256": REVIEWED_HASHES[p]} for p, (owner, commit) in PINS.items()]
    expected = {**CLEAN_IDENTITY, "protected_paths": expected_rows}
    try:
        attestation = json.loads(ATTESTATION_PATH.read_text(), object_pairs_hook=_unique_keys)
        if attestation != expected:
            return None
        root = CLEAN_IDENTITY["clean_root_sha"]
        if (_git("rev-parse", root + "^{tree}").decode().strip() != CLEAN_IDENTITY["clean_root_tree_sha"]
                or _git("show", "-s", "--format=%P", root).decode().strip() != CLEAN_IDENTITY["parent_main_sha"]):
            return None
        digest = REVIEWED_HASHES[path]
        root_bytes = _git("show", f"{root}:{path}")
        head_bytes = _git("show", f"HEAD:{path}")
        if not all(sha256(data).hexdigest() == digest for data in (root_bytes, head_bytes, observed)):
            return None
    except (OSError, ValueError, KeyError, subprocess.SubprocessError):
        return None
    owner, commit = PINS[path]
    return {"owner": owner, "commit": commit, "path": path, "sha256": digest,
            "contract": CONTRACT, "provenance_mode": "REVIEWED_CLEAN_HISTORY",
            "ancestor_verified": False, "historical_ancestor_verified": False,
            "clean_root": root, "clean_root_ancestor_verified": True,
            "clean_root_tree_verified": True, "exact_blob_verified": True}


def approved_descendant(path):
    pin = PINS.get(path)
    if pin is None or not Path(path).is_file() or Path(path).is_symlink():
        return None
    try:
        observed = Path(path).read_bytes()
    except OSError:
        return None
    # A failed clean attestation must never fall back to a different proof mode.
    if _ancestor(CLEAN_IDENTITY["clean_root_sha"]):
        return _clean_approval(path, observed)
    owner, commit = pin
    try:
        if not _ancestor(commit):
            return None
        expected = _git("show", f"{commit}:{path}")
    except (subprocess.SubprocessError, OSError):
        return None
    if observed != expected:
        return None
    return {"owner": owner, "commit": commit, "path": path, "sha256": sha256(expected).hexdigest(),
            "ancestor_verified": True, "historical_ancestor_verified": True,
            "provenance_mode": "LEGACY_HISTORICAL_ANCESTRY", "exact_blob_verified": True}
