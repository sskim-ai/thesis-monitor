"""Archive-backed original financial-capture replay for detached SEC identity.

The composition root selects an independently sealed archive pin. No archive
expansion, DB access, provider call, field synthesis or current-use grant occurs.
"""
from dataclasses import dataclass
from datetime import date, datetime
import hashlib
import json
from pathlib import Path
import zipfile

from app.services.bounded_financial_projection import verify_capture
from app.services.scoped_current_identity import SecCoverCapture, TrustedIdentityReader
from app.services.scoped_routing_identity import SealedRoutingCatalog
from app.services.sealed_fresh_dispatch import decode_request_plan
from app.services.unified_snapshot_contract import digest


@dataclass(frozen=True)
class _ArchiveDirectory:
    reader: object
    prefix: str
    selected_member: str = ""
    selected_limit: int = 8_000_000

    def __truediv__(self, name):
        if not isinstance(name, str) or Path(name).name != name:
            raise ValueError("identity_capture_path_escape")
        return _ArchiveDirectory(self.reader, self.prefix + "/" + name, self.selected_member, self.selected_limit)

    def read_bytes(self):
        return self.reader._read(self.prefix, self.selected_limit if self.prefix == self.selected_member else 8_000_000)


class SealedFinancialIdentityReader(TrustedIdentityReader):
    def __init__(self, *, archive, pin):
        # Existing owner verifies ZIP SHA, CRC, exhaustive manifest and control.
        self.catalog = SealedRoutingCatalog(archive=Path(archive), pin=pin)
        self.archive = Path(archive)
        with zipfile.ZipFile(self.archive) as z:
            self.members = json.loads(z.read("manifest.json"))["files"]

    def _read(self, member, maximum_bytes=8_000_000):
        expected = self.members.get(member)
        if expected is None or expected["bytes"] > maximum_bytes:
            raise ValueError("identity_capture_member_missing_or_oversized")
        with zipfile.ZipFile(self.archive) as z:
            info = z.getinfo(member)
            if info.file_size != expected["bytes"]:
                raise ValueError("identity_capture_size_drift")
            raw = z.read(member)
        if hashlib.sha256(raw).hexdigest() != expected["sha256"]:
            raise ValueError("identity_capture_member_drift")
        return raw

    def read_sec_cover(self, reference, *, maximum_bytes):
        with self.archive.open("rb") as handle:
            if hashlib.file_digest(handle, "sha256").hexdigest() != self.catalog.pin.archive_sha256:
                raise ValueError("identity_capture_archive_drift")
        subject = reference.subject
        prefix = "financial/" + subject.ticker
        plan = json.loads(self._read(prefix + "/policy.json"))
        security = plan["security"]
        if (plan["provider"], plan["market"], plan["ticker"], plan["run_id"],
            plan["issuer"], security["canonical_security_id"], security["exchange"], digest(plan)) != (
                "sec_edgar", "us", subject.ticker, reference.source_generation_id,
                subject.issuer_id, subject.security_id, subject.venue, reference.source_plan_sha256):
            raise ValueError("identity_capture_plan_subject_mismatch")
        directory = _ArchiveDirectory(self, prefix + "/capture")
        acquisition = json.loads((directory/"acquisition-result.json").read_bytes())
        receipts = json.loads((directory/"owner-receipts.json").read_bytes())
        selected = [r for r in receipts if r["logical_id"] == reference.logical_request_id
            and r["stage"] == "document" and not r.get("failure_class")]
        if len(selected) != 1:
            return None
        r = selected[0]
        member = prefix + "/capture/" + r["artifact"]
        if maximum_bytes < 1 or self.members.get(member, {}).get("bytes", maximum_bytes+1) > maximum_bytes:
            raise ValueError("identity_capture_member_missing_or_oversized")
        directory = _ArchiveDirectory(self, prefix + "/capture", member, maximum_bytes)
        verify_capture(plan, acquisition, directory, receipts)
        if digest(r) != reference.receipt_sha256 or r["sealed_generation_id"] != plan["run_id"]:
            raise ValueError("identity_capture_receipt_mismatch")
        provider = decode_request_plan(json.loads(self._read(prefix + "/provider-plan.json")))
        descriptors = [d for d in provider.descriptors if d.logical_request_id == r["sealed_logical_id"]]
        if len(descriptors) != 1:
            raise ValueError("identity_capture_descriptor_missing")
        d = descriptors[0]
        final = json.loads(self._read(prefix + "/dispatch/receipts/" + d.logical_request_id + "/final.json"))
        if (provider.generation_id != plan["run_id"] or provider.frozen_at != datetime.fromisoformat(plan["cutoff"])
                or final["status"] != "PASS" or final["plan_sha256"] != provider.plan_sha256
                or final["generation_id"] != plan["run_id"] or final["descriptor_sha256"] != d.descriptor_sha256
                or final["receipt_sha256"] != r["sealed_final_receipt_sha256"]
                or digest({k: v for k, v in final.items() if k != "receipt_sha256"}) != final["receipt_sha256"]
                or final["raw_sha256"] != r["raw_sha256"] or d.subject != subject.ticker):
            raise ValueError("identity_capture_dispatch_binding")
        request = json.loads((directory/(r["logical_id"].split(":")[-1]+".plan.json")).read_bytes())
        raw = self._read(prefix + "/capture/" + r["artifact"], maximum_bytes)
        filing = r["filing"]
        return SecCoverCapture(reference=reference, raw=raw, raw_sha256=r["raw_sha256"],
            request_sha256=r["request_sha256"], issuer_cik=plan["issuer"],
            filing_accession=filing["accessionNumber"], source_url=request["url"],
            source_form=filing["form"], source_as_of=date.fromisoformat(filing["filingDate"]),
            source_run_started_at=datetime.fromisoformat(plan["cutoff"]),
            requested_at=datetime.fromisoformat(r["started_at"]), received_at=datetime.fromisoformat(r["finished_at"]))
