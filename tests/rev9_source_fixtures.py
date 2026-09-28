"""Data-only descriptor roundtrips of synthetic raw owner fixtures."""
from app.services.unified_run_artifacts import durable_bytes, durable_json, sha256_bytes
from app.services.unified_snapshot_contract import digest
from app.services.official_security_identity_service import OfficialSecurityIdentityEvidence
from app.services.fresh_financial_stock_owner import fresh_stock_baseline
from app.services.bounded_financial_stock_owner import assemble
from tests.rev8_source_fixtures import fresh_inputs


def write_descriptor(root, inputs):
    tech, fin = inputs['technical_inputs'], inputs['financial_inputs']
    ticker = tech['ticker']
    prefix = root / 'descriptors' / ticker

    def put(name, data, raw=False):
        path = prefix / name
        if raw:
            durable_bytes(path, data, exclusive=True)
        else:
            durable_json(path, data, exclusive=True)
        return dict(path=str(path.relative_to(root)), sha256=sha256_bytes(path.read_bytes()))

    result = dict(ticker=ticker, local=put('local.json', tech['local_seed']),
        receipts=put('receipts.json', tech['receipts']), components=put('components.json', tech['components']),
        artifacts={name: put('artifacts/' + name, body, True) for name, body in tech['artifacts'].items()},
        financial_plan=put('financial-plan.json', fin['plan']),
        financial_acquisition=put('financial-acquisition.json', fin['acquisition']),
        financial_receipts=put('financial-receipts.json', fin['receipts']),
        financial_raw=str(fin['directory'].relative_to(root)), allowed_providers=sorted(tech['policy'].allowed_providers))
    if 'valuation_inputs' in inputs:
        native = inputs['valuation_inputs']
        result['valuation'] = dict(raw=put('valuation.body', native['raw'], True),
            receipt=put('valuation-receipt.json', native['receipt']), cutoff=native['cutoff'].isoformat())
    return result


def bridge_inputs(root):
    source = fresh_inputs(root / 'underlying', '000660')
    target = fresh_inputs(root / 'target', 'SKHY', empty_financial=True,
        security_overrides={'issuer_type': 'adr', 'security_type': 'ads'})
    source_owner = dict(baseline=fresh_stock_baseline(source['technical_inputs']),
        local_seed=source['technical_inputs']['local_seed'], **source['financial_inputs'])
    official = OfficialSecurityIdentityEvidence(ticker='SKHY', issuer_name='Synthetic issuer',
        security_title='American Depositary Shares', security_type='ads', issuer_type='adr', exchange='NASDAQ',
        source_url='https://www.sec.gov/Archives/edgar/data/1234/000000123426000001/prospectus.htm',
        source_form='424(b)(4)', filing_accession='0000001234-26-000001', as_of_date='2026-06-01',
        source_reference='SYNTHETIC SEC identity fixture; NOT LIVE', cik='1234',
        ordinary_share_identifier='000660').to_payload()
    target['financial_inputs']['issuer_business'] = dict(source_inputs=source_owner, official_identity=official,
        official_identity_sha256=digest(official), source_result_sha256=digest(assemble(**source_owner)))
    return target, source
