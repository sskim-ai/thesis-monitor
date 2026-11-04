"""Bounded archive-to-native inputs; archive integrity never grants source use."""

from hashlib import sha256
import json
from pathlib import Path, PurePosixPath
import stat
import zipfile

from app.services.canonical_source_replay import stock_inputs, validate_subject_view
from app.services.completed_price_state import require_plan
from app.services.sealed_fresh_dispatch import decode_request_plan
from app.services.unified_stock_acquisition import StockPlan
from app.services.unified_snapshot_contract import digest


class RetainedDependencyError(ValueError):
    def __init__(self, code, member):
        self.code, self.member = code, member
        super().__init__(f"{code}:{member}")


def _relative(value):
    path = PurePosixPath(value)
    if not value or path.is_absolute() or ".." in path.parts or str(path) != value:
        raise RetainedDependencyError("retained_path_invalid", value)
    return path


class RetainedArchive:
    """Pinned immutable ZIP, bounded verified reads and an exact dependency ledger."""

    def __init__(self, archive, *, archive_sha256, manifest_member,
                 manifest_sha256, max_selected_bytes=64 * 1024 * 1024):
        self.path = Path(archive)
        if any(p.is_symlink() for p in (self.path, *self.path.parents)):
            raise RetainedDependencyError("retained_archive_symlink", str(archive))
        with self.path.open("rb") as stream:
            actual = sha256()
            for block in iter(lambda: stream.read(1024 * 1024), b""):
                actual.update(block)
        if actual.hexdigest() != archive_sha256:
            raise RetainedDependencyError("retained_archive_sha_mismatch", str(archive))
        self.archive_sha256 = archive_sha256
        self.manifest_member = str(_relative(manifest_member))
        parent = PurePosixPath(manifest_member).parent
        self.base = "" if str(parent) == "." else str(parent) + "/"
        self.limit, self.ledger, self._bytes = max_selected_bytes, {}, {}
        with zipfile.ZipFile(self.path) as z:
            names = z.namelist()
            if len(names) != len(set(names)):
                raise RetainedDependencyError("retained_duplicate_member", manifest_member)
            for info in z.infolist():
                _relative(info.filename)
                if stat.S_ISLNK(info.external_attr >> 16):
                    raise RetainedDependencyError("retained_member_symlink", info.filename)
            raw = z.read(manifest_member)
            if sha256(raw).hexdigest() != manifest_sha256:
                raise RetainedDependencyError("retained_manifest_sha_mismatch", manifest_member)
            self.files = json.loads(raw)["files"]
            expected = {self.base + str(_relative(p)) for p in self.files}
            if set(names) != expected | {manifest_member}:
                raise RetainedDependencyError("retained_manifest_membership", manifest_member)

    def read(self, relative, purpose):
        relative = str(_relative(relative))
        member = self.base + relative
        if relative not in self.files:
            raise RetainedDependencyError("retained_dependency_missing", member)
        if relative not in self._bytes:
            record = self.files[relative]
            if sum(len(v) for v in self._bytes.values()) + record["bytes"] > self.limit:
                raise RetainedDependencyError("retained_dependency_budget", member)
            with zipfile.ZipFile(self.path) as z:
                if z.getinfo(member).file_size != record["bytes"]:
                    raise RetainedDependencyError("retained_member_size", member)
                raw = z.read(member)  # ZipFile checks this member's CRC.
            if len(raw) != record["bytes"] or sha256(raw).hexdigest() != record["sha256"]:
                raise RetainedDependencyError("retained_member_hash", member)
            self._bytes[relative] = raw
            self.ledger[relative] = dict(member=member, **record, crc="PASS", purposes=[])
        if purpose not in self.ledger[relative]["purposes"]:
            self.ledger[relative]["purposes"].append(purpose)
        return self._bytes[relative]

    def json(self, relative, purpose):
        return json.loads(self.read(relative, purpose))


def valuation_dependencies(inventory, results):
    """Mirror the existing valuation owner's bounded attempted-page contract."""
    selected = set(inventory.get("slots", []))
    if inventory.get("provider") == "kiwoom":
        base = "valuation:list:" + inventory["market_type"]
        for page in range(2, 6):
            key = base + f":continuation:{page}"
            if key not in results:
                break
            selected.add(key)
    return selected


def dispatch_raw_dependency(descriptor, final):
    # A normalization failure can still own a captured raw response.
    return "dispatch/" + descriptor.raw_path if final.get("raw_sha256") else None


def materialize_subject(*, archive, live_prefix, subject, staging_root, policy):
    """Select a subject view of original plans and call the canonical input builder.

    Only referenced source/receipt members are staged because original financial
    owners consume filesystem directories. No saved stock/prepared output is used.
    """
    prefix = str(_relative(live_prefix))
    destination = Path(staging_root)
    if any(p.is_symlink() for p in (destination, *destination.parents)):
        raise RetainedDependencyError("retained_staging_symlink", str(destination))
    if destination.exists():
        raise RetainedDependencyError("retained_staging_must_be_new", str(destination))
    selected = {}

    def capture(name, purpose):
        name = str(_relative(name))
        raw = archive.read(prefix + "/" + name, purpose)
        selected[name] = raw
        return raw

    def data(name, purpose):
        return json.loads(capture(name, purpose))

    frozen = data("r9-rev11-final-provider-plan.json", "original_full_provider_and_stock_plan")
    outcome = data("acquisition-outcome.json", "original_dispatch_outcome")
    plan = StockPlan.model_validate(frozen["stock_plan"])
    sealed = decode_request_plan(frozen["plan"])
    require_plan(sealed, plan)
    members = {t: m for m, tickers in plan.universe.items() for t in tickers}
    if subject not in members:
        raise RetainedDependencyError("retained_subject_not_in_original_plan", subject)
    validate_subject_view(plan, (subject,))
    if frozen["generation_id"] != plan.run_id or sealed.generation_id != plan.run_id:
        raise RetainedDependencyError("retained_original_generation_mismatch", subject)
    market = members[subject]
    data("native/raw-owner-replay.json", "original_complete_replay_coverage")
    data(f"class-c/local-{market}.json", "original_local_seed")
    logical = set()
    for ordinal, entry in enumerate(plan.reads, 1):
        if entry.subject != subject:
            continue
        receipt = data(f"native/stocks/role-{ordinal:03d}.receipt.json", "selected_stock_receipt")
        capture("native/stocks/" + receipt["normalized_artifact"], "stock_normalized")
        for index, page in enumerate(receipt["pages"], 1):
            capture("native/stocks/" + page["artifact"], "stock_raw")
            logical.add(entry.entry_id + ":page1" + (f":continuation:{index}" if index > 1 else ""))
    financial_subjects = {subject}
    for issuer, dependency in frozen["candidate"].get("auxiliary_issuer_dependencies", {}).items():
        if dependency["primary_subject"] == subject:
            financial_subjects.add(issuer)
            capture("static/official-security-identity.json", "declared_issuer_bridge_identity")
    for financial_subject in sorted(financial_subjects):
        financial = f"financial/{financial_subject}/"
        data(financial + "owner-acquisition.json", "financial_acquisition")
        for receipt in data(financial + "owner-receipts.json", "financial_receipts"):
            logical.add(receipt["sealed_logical_id"])
            capture(financial + receipt["logical_id"].split(":")[-1] + ".plan.json",
                    "financial_original_request_plan")
            if receipt.get("artifact"):
                capture(financial + receipt["artifact"], "financial_raw")
    event_prefix = f"events/{subject}/"
    data(event_prefix + "bound-source.json", "event_owner_source")
    for relative in archive.files:
        if relative.startswith(prefix + "/" + event_prefix) and relative.endswith(".response.json"):
            receipt = data(relative[len(prefix) + 1:], "event_response")
            if receipt.get("artifact"):
                capture(event_prefix + receipt["artifact"], "event_raw")
    descriptors = {d.logical_request_id: d for d in sealed.descriptors}
    logical.update(d.logical_request_id for d in sealed.descriptors if d.role_id == "events:" + subject)
    logical.update(valuation_dependencies(frozen.get("valuation_slots", {}).get(subject, {}),
                                         outcome["logical_results"]))
    if market == "us":
        from app.services.sealed_completed_price import required_slot
        daily = next(r for r in plan.reads if r.subject == subject and r.role == "adjusted_daily")
        logical.add(required_slot(sealed, daily).logical_request_id)
        capture(frozen["completed_close_documentation"]["path"], "completed_close_official_spec")
    visited = set()

    def dispatch(key):
        if key in visited:
            return
        if key not in descriptors or key not in outcome["logical_results"]:
            raise RetainedDependencyError("retained_dispatch_dependency_missing", key)
        visited.add(key)
        descriptor = descriptors[key]
        base = "dispatch/receipts/" + key + "/"
        final = data(base + "final.json", "dispatch_final")
        for relative in archive.files:
            if relative.startswith(prefix + "/" + base):
                capture(relative[len(prefix) + 1:], "dispatch_receipt_or_attempt")
        raw_dependency = dispatch_raw_dependency(descriptor, final)
        if raw_dependency is not None:
            capture(raw_dependency, "dispatch_bound_raw")
        for parent in final.get("parent_receipts", {}):
            dispatch(parent)

    for key in sorted(logical):
        dispatch(key)
    # No filesystem mutation until the complete selected closure verifies.
    destination.mkdir(parents=True, exist_ok=False)
    for name, raw in selected.items():
        path = destination / name
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("xb") as stream:
            stream.write(raw)
    inputs, errors = stock_inputs(destination, frozen, policy, outcome, subjects=(subject,))
    receipt = dict(contract="retained-raw-stock-materializer-v1", subject=subject,
        original_generation=plan.run_id, original_subject_count=len(members),
        original_descriptor_count=len(sealed.descriptors), stock_plan_sha256=digest(plan.model_dump(mode="json")),
        provider_plan_sha256=sealed.plan_sha256, archive_sha256=archive.archive_sha256,
        selected_members=len(selected), selected_bytes=sum(map(len, selected.values())),
        source_use_authority="NOT_ISSUED", current_generation_relabelled=False,
        dependency_ledger=list(archive.ledger.values()), input_errors=errors)
    return (None if errors else inputs.get(subject)), receipt
