"""Whole frozen cohort regression and recorded foreign-route replay, with no network."""
import argparse
import asyncio
from datetime import date
from pathlib import Path
import re

import httpx
from sqlmodel import Session, SQLModel, create_engine, select

from app.models.financial import FinancialSnapshot
from app.services.sec_financial_snapshot_service import SecFinancialSnapshotService
from app.services.sec_foreign_comparison_service import foreign_comparison_quality
from scripts.m12dr_offline_source_closure import read, write, sha
from scripts.m12ds_r4_r2_offline import audit


def run(baseline, source_audit, output):
    audit(baseline, output)
    manifest = read(source_audit / 'raw-manifest.json')
    responses = {row['url']: row for row in manifest}
    submission = next(url for url in responses if '/submissions/CIK' in url)
    cik = re.search(r'CIK(\d+)\.json', submission)[1]

    def recorded(request):
        row = responses[str(request.url)]
        path = source_audit / (row['sha256'] + '.payload')
        if sha(path) != row['sha256']:
            raise ValueError('recorded_source_digest_mismatch')
        return httpx.Response(row['status'], content=path.read_bytes())

    async def scan():
        async with httpx.AsyncClient(transport=httpx.MockTransport(recorded)) as client:
            return await SecFinancialSnapshotService()._scan_foreign_filings(client, cik)

    parsed = asyncio.run(scan())['parsed_statement']
    engine = create_engine('sqlite://')
    SQLModel.metadata.create_all(engine)
    with Session(engine) as session:
        SecFinancialSnapshotService._upsert_foreign_preliminary_snapshot(session, 'RENAMED_ISSUER', parsed)
        row = session.exec(select(FinancialSnapshot)).one()
        quality = foreign_comparison_quality(formal=row, candidates=[], ticker=row.ticker, cutoff=date(2026,9,22))
    write(output / 'recorded-foreign-route.json', quality)
    receipt = read(output / 'receipt.json')
    receipt.update(recorded_foreign_route_status=quality['status'],
        recorded_foreign_comparisons=len(quality['comparative_observations']),
        recorded_foreign_manifest_sha256=sha(source_audit / 'raw-manifest.json'),
        historical_diagnostic_only=True, final_current_input=False, source_calls=0, model_calls=0)
    if quality['status'] != 'PASS':
        receipt['status'] = 'FAIL'
        receipt['errors'].append('recorded_foreign_source_lineage_incomplete')
    write(output / 'receipt.json', receipt)
    print(receipt)
    if receipt['status'] != 'PASS':
        raise ValueError('offline_foreign_lineage_failed')


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--baseline', type=Path, required=True)
    parser.add_argument('--source-audit', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    run(args.baseline, args.source_audit, args.output)
