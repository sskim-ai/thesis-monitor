"""Typed same-session sector extrema, never a model-generated ranking."""
from collections import defaultdict


def ranked_sector_claims(facts, registry, market, completed, eligible, source):
    from app.services.market_numeric_claim_service import claim, component, digest, number, _eligible
    from app.services.market_current_context_service import kr_sector_alias

    permitted = {}
    for row in registry:
        if row.get('field_path') != 'fields.return_pct':
            continue
        if row.get('fact_id') in permitted:
            raise ValueError('duplicate_sector_registry_key')
        permitted[row.get('fact_id')] = row
    groups = defaultdict(list)
    for fact in facts:
        fields, ref = fact.get('fields') or {}, fact['fact_id']
        if fact.get('as_of_date') != completed or not number(fields.get('return_pct')):
            continue
        if market == 'us':
            # SOXX is a subindustry proxy; do not rank it against broad sectors.
            if (fact.get('fact_type') != 'market_sector' or fields.get('series_code') not in
                    {'XLB','XLC','XLE','XLF','XLI','XLK','XLP','XLRE','XLU','XLV','XLY'}
                    or ref not in eligible or not _eligible(fact, completed, source['session']['assessment_date'])):
                continue
            scope, label = 'US_SECTOR_ETF', fields['label']
        else:
            if not kr_sector_alias(fact, source, completed, eligible):
                continue
            scope, label = fields['market_scope'], fields['sector']
        row = permitted.get(ref) or {}
        if (row.get('registered') is not True or row.get('prose_allowed') is not True
                or row.get('scope') not in {'market','both'} or row.get('unit') != 'pct'
                or row.get('value') != fields['return_pct']):
            continue
        groups[scope].append((fact, row, label))
    claims = []
    for scope, rows in sorted(groups.items()):
        rows = sorted(rows, key=lambda row: row[0]['fact_id'])
        for direction, sign in (('TOP3', -1), ('BOTTOM3', 1)):
            selected = sorted(rows, key=lambda r: (sign*r[0]['fields']['return_pct'], r[0]['fact_id']))[:3]
            parts, texts = [], []
            for fact, registry_row, label in selected:
                ref, fields = fact['fact_id'], fact['fields']
                for path, value, role, unit in (
                    ('fields.return_pct', fields['return_pct'], 'RETURN', 'pct'),
                    ('as_of_date', completed, 'DATE', 'ISO_DATE'),
                    ('fields.label' if market == 'us' else 'fields.sector', label, 'INSTRUMENT', 'TEXT')):
                    parts.append(component(ref, path, value, role, unit, completed))
                texts.append(f"{label} {fields['return_pct']:+.2f}%")
            heading = '미국 업종 ETF' if scope == 'US_SECTOR_ETF' else scope
            claims.append(claim('SECTOR_RANKING', parts,
                f"{heading} {'상위' if direction == 'TOP3' else '하위'} {len(selected)} · {completed}\n" + ' / '.join(texts),
                parents=[r[0]['fact_id'] for r in selected],
                formula=f'sort same-session return {direction}; tie=canonical fact_id; take 3',
                metadata=dict(scope=scope, taxonomy='sector_etf' if market == 'us' else 'kiwoom-sector-index-v1',
                              candidate_count=len(rows), candidate_sha256=digest(rows), rank_direction=direction,
                              missing_count=max(0, 3-len(selected)), zero_rows_fabricated=0)))
    return claims
