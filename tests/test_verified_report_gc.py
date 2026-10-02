from hashlib import sha256
import json
import zipfile

import pytest

from scripts.verified_report_gc import directory_proof, fingerprint, remove_verified, verify_archive


def fixture(tmp_path):
    expanded = tmp_path / "expanded"
    expanded.mkdir()
    (expanded / "source.json").write_text('{"fixture":true}\n')
    archive = tmp_path / "report.zip"
    with zipfile.ZipFile(archive, "w") as z:
        z.write(expanded / "source.json", "result/source.json")
        z.writestr("result/bundle-manifest.json", json.dumps({"source.json": fingerprint(expanded / "source.json")}))
    archive.with_suffix(".zip.sha256").write_text(sha256(archive.read_bytes()).hexdigest())
    receipt, manifest = verify_archive(archive)
    row = directory_proof(expanded, archive=receipt, manifest=manifest, prefix="", protected=[])
    return expanded, archive, row


def test_verified_only_keeps_archive(tmp_path):
    expanded, archive, row = fixture(tmp_path)
    assert remove_verified(row, protected=[])["deleted"]
    assert not expanded.exists() and archive.exists() and archive.with_suffix(".zip.sha256").exists()


@pytest.mark.parametrize("mutation", ["changed", "extra", "protected", "symlink", "archive_changed", "db"])
def test_never_deletes_unproven_or_protected(tmp_path, mutation):
    expanded, archive, row = fixture(tmp_path)
    protected = []
    if mutation == "changed":
        (expanded / "source.json").write_text("changed")
    elif mutation == "extra":
        (expanded / "unique.txt").write_text("only copy")
    elif mutation == "protected":
        protected = [expanded / "source.json"]
    elif mutation == "symlink":
        (expanded / "link").symlink_to(archive)
    elif mutation == "db":
        (expanded / "production.db").write_bytes(b"db")
    else:
        archive.with_suffix(".zip.sha256").write_text("0" * 64)
    with pytest.raises(ValueError):
        remove_verified(row, protected=protected)
    assert expanded.exists()
