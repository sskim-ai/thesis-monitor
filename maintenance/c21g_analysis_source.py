"""Re-enter the existing one-subject AnalysisView factories, never a JSON Owner."""
from copy import deepcopy
import json
from pathlib import Path
import zipfile

from app.services import valuation_analysis as analysis
from app.services.vnext_research_store import digest


def restore_view(*, packet, native_root, native_replay_sha256, kis_root, kis_generation,
                 calibration_archive, calibration_sha256, dated_archive,
                 dated_archive_sha256):
    native_root, kis_root = Path(native_root), Path(kis_root)
    raw_replay = (native_root / 'original-replay.json').read_bytes()
    if digest(raw_replay) != native_replay_sha256:
        raise ValueError('original_native_replay_changed')
    replay = json.loads(raw_replay)
    security_id = packet['base']['public_security']['canonical_security_id']
    securities = [s for s in replay['securities'] if s['canonical_security_id'] == security_id]
    if len(securities) != 1:
        raise ValueError('original_source_exact_security')
    security = securities[0]; ticker = security['ticker']
    from app.services.provider_native_valuation_acquisition import replay_native
    from app.services.provider_native_valuation_snapshot import derive_provider_snapshots
    from app.services.unified_source_policy import UnifiedSourcePolicy
    outcome = dict(replay['outcome'], logical_results={k: v for k, v in replay['outcome']['logical_results'].items() if v['status'] != 'NOT_SELECTED'})
    counts = dict(native_owner_consumptions=0, dated_fper_owner_consumptions=0, EPS_initial_original_parse=1)

    def native_read():
        if digest((native_root / 'original-replay.json').read_bytes()) != native_replay_sha256:
            raise ValueError('original_replay_drift')
        counts['native_owner_consumptions'] += 1
        inputs = replay_native(root=native_root, frozen=replay['frozen'], outcome=outcome,
                              security=security, policy=UnifiedSourcePolicy(frozenset({'kiwoom_rest', 'finnhub'})))
        facts = [analysis._native_fact(m.model_dump(mode='json'), security, replay['frozen']['generation_id'])
                 for m in derive_provider_snapshots(inputs, security=security, run_id=replay['frozen']['generation_id']) if m.display_eligible]
        return {ticker: security}, facts, []

    eraw = (kis_root / 'estimate' / (ticker + '.body')).read_bytes()
    receipt = json.loads((kis_root / 'estimate' / (ticker + '-receipt.json')).read_bytes())
    identity = json.loads((kis_root / 'identity' / (ticker + '.body')).read_bytes())
    docs, protocol = analysis.calibration_from_archive(Path(calibration_archive), calibration_sha256)
    # Exactly the original producer, once. No new estimate, unit rule, forecast or generation.
    eps = analysis.parse_analyst_eps(ticker=ticker, security=security, estimate=json.loads(eraw),
        identity=identity, receipt=receipt, generation=kis_generation,
        as_of=packet['base']['as_of'], docs=docs, protocol=protocol)
    if eps.raw_sha256 != digest(eraw):
        raise ValueError('original_eps_receipt_mismatch')
    archive = Path(dated_archive)
    if digest(archive.read_bytes()) != dated_archive_sha256:
        raise ValueError('original_dated_support_archive_changed')
    with zipfile.ZipFile(archive) as z:
        manifest = json.loads(z.read('manifest.json'))['files']
        def raw(name):
            data = z.read(name)
            if manifest[name] != dict(bytes=len(data), sha256=digest(data)):
                raise ValueError('original_support_member_changed')
            return data
        def read(name):
            return json.loads(raw(name))
        entry = next(e for e in read('evidence/ORIGINAL_MULTIPARENT_INPUTS.json')['entries']
                     if e['security']['ticker'] == ticker)
        plan = read('approved-support/plan.json')['per_security'][ticker]
        old = read('approved-support/live/owners/' + ticker + '.json')
        def item(name):
            return dict(raw=raw('approved-support/live/' + name + '.body'), receipt=read('approved-support/live/' + name + '-receipt.json'))
        cap = dict(security=entry['security'], eps=eps, eps_raw=eraw, eps_receipt=receipt,
            original_eps=old['eps'], price=item('price/' + ticker), calendar=plan['calendar'],
            price_docs=entry['static']['price_docs'], action_docs=entry['static']['action_docs'],
            actions={q['variant']: item(f"actions/{ticker}/action/{ticker}/{q['variant']}-1") for q in plan['qualified_action_requests']})
    # Keep original generation and dated price. The original Owner itself rechecks
    # receipt/units/actions/arithmetic on consumption; no stored JSON grants a use.
    dated = analysis.dated_fper_source(lambda: deepcopy(cap))
    def dated_read():
        counts['dated_fper_owner_consumptions'] += 1
        return dated.read()
    def eps_read():
        if (kis_root / 'estimate' / (ticker + '.body')).read_bytes() != eraw:
            raise ValueError('retained_eps_bytes_changed')
        current = json.loads((kis_root / 'estimate' / (ticker + '-receipt.json')).read_bytes())
        if current != receipt:
            raise ValueError('retained_eps_receipt_changed')
        return {ticker: security}, [eps], []
    view = analysis.AnalysisView(sources=[analysis.AnalysisSource(native_read), analysis.AnalysisSource(eps_read),
                                analysis.AnalysisSource(dated_read)], ticker=ticker,
                                as_of=packet['base']['as_of'], enabled=True)
    return view, counts
