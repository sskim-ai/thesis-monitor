"""Import previously acquired group-A documents for lookup after regular discovery."""
import argparse
from dataclasses import asdict
import json
from pathlib import Path

from app.services.opendart_financial_recovery_service import filing_from_row
from app.services.retained_dart_reports import DartReportStore, document_proof
from app.services.unified_run_artifacts import sha256_bytes


def import_originals(originals, run_root):
    inventory = json.loads((originals/'INVENTORY.json').read_bytes())
    records = [json.loads(line) for line in (originals/'HTTP_LEDGER.jsonl').read_bytes().splitlines()]
    store = DartReportStore(run_root)
    imported = []
    for company in inventory['companies']:
        if company['group'] != 'A':
            continue
        row, ticker = company['filing'], company['ticker']
        corp = company['identity']['corp_code']
        selected = filing_from_row(row, ticker=ticker, corp_code=corp)
        if (selected is None or row['stock_code'] != ticker or row['corp_code'] != corp
                or inventory['identity']['selected_by_stock_code'][ticker] != company['identity']
                or ticker not in inventory['saved_kr_tickers'] or company['status'] != 'DOCUMENT_SAVED'):
            raise ValueError('dart_import_issuer_or_selected_report_invalid')
        filing = dict(asdict(selected), receipt_date=selected.receipt_date.isoformat(), role='current')
        folder = originals/'A'/ticker
        search = (folder/'list.json').read_bytes()
        if sha256_bytes(search) != company['search']['file']['sha256'] or row not in json.loads(search)['list']:
            raise ValueError('dart_import_original_listing_mismatch')
        doc = company['document']
        raw = (folder/(selected.receipt_no+'.zip')).read_bytes()
        if len(raw) != doc['zip']['bytes'] or sha256_bytes(raw) != doc['zip']['sha256']:
            raise ValueError('dart_import_original_zip_mismatch')
        attempt, = [r for r in records if r['event'] == 'ATTEMPT' and r['subject'] == ticker
                    and r['endpoint'] == 'document.xml' and r['params'] == {'rcept_no': selected.receipt_no}]
        result, = [r for r in records if r['event'] == 'RESULT' and r['number'] == attempt['number']]
        origin = dict(kind='independent', attempt=attempt, result=result, search_sha256=sha256_bytes(search))
        store.save(filing, raw, document_proof(filing, raw, origin, doc['received_at']))
        imported.append(dict(ticker=ticker, receipt_no=selected.receipt_no, sha256=sha256_bytes(raw),
                             received_at=doc['received_at']))
    if sorted(x['ticker'] for x in imported) != sorted(inventory['saved_kr_tickers']):
        raise ValueError('dart_import_incomplete_preserved_group')
    return imported


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('originals', type=Path, help='extracted preserved inventory and source files')
    parser.add_argument('run_root', type=Path, help='existing KR regular run_root')
    args = parser.parse_args()
    print(json.dumps(import_originals(args.originals, args.run_root), ensure_ascii=False, indent=2))
