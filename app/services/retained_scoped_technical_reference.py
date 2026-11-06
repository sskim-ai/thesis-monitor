"""Original retained chart -> dated Owner; never restores current Source rights."""
import json
from pathlib import Path

from app.services.unified_stock_acquisition import bound_artifact
from app.services.vnext_dated_calendar import POLICY
from app.services.vnext_dated_technical_owner import (
    CapturedScopedStockPlan, DatedTechnicalOwner, LegacyChartReplay,
)


def build_owner(*, security, receipt_paths, parser_root, parser_pins, enabled=False):
    """Caller supplies exact retained paths; raw/receipt validators remain original.

    A full Source-only count verdict is not a prerequisite for dated summary
    references. Unadjusted valuation roles must never enter this adapter.
    """
    if not enabled or not receipt_paths:
        raise ValueError('retained_reference_disabled_or_empty')
    sources = {}
    seen = set()
    for supplied in receipt_paths:
        path = Path(supplied)
        if any(p.is_symlink() for p in (path, *path.parents)):
            raise ValueError('retained_reference_symlink')
        path = path.resolve(strict=True)
        if path in seen:
            raise ValueError('retained_reference_duplicate_receipt')
        seen.add(path)
        receipt = json.loads(path.read_bytes())
        entry = receipt['entry']
        tf = entry['timeframe']
        if (entry['subject'] != security['ticker'] or not entry['adjusted']
                or tf not in {'daily', 'weekly', 'monthly'}
                or entry['role'] != 'adjusted_' + tf):
            raise ValueError('retained_reference_subject_or_adjustment')
        frozen_path = path.parent.parent.parent / 'frozen.json'
        if frozen_path.is_symlink():
            raise ValueError('retained_reference_symlink')
        frozen = json.loads(frozen_path.read_bytes())
        if frozen['external_pins'] != json.loads(Path(parser_pins).read_bytes()):
            raise ValueError('retained_reference_parser_pin_drift')
        replay = LegacyChartReplay(plan=CapturedScopedStockPlan(frozen['stock_plan']),
            receipts={entry['entry_id']: receipt},
            artifact_reader=lambda n, s, parent=path.parent: bound_artifact(parent, n, s),
            parser_root=Path(parser_root), parser_pins=Path(parser_pins))
        # Exact security/receipt/parser verification precedes Owner creation.
        replay.replay(security, tf)
        sources.setdefault(tf, []).append(replay)
    return DatedTechnicalOwner({tf: tuple(items) for tf, items in sources.items()},
        parser_root=Path(parser_root), parser_pins=Path(parser_pins),
        enabled=True, calendar_policy=POLICY)
