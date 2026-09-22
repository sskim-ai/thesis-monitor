"""Bind KR local factual blocks to both canonical registry and current adapter rows."""


def local_kr_claims(source, completed, eligible):
    from app.services.market_numeric_claim_service import claim, component, digest, number

    adapter = source.get('adapter_context') or {}
    if adapter.get('session_date') != completed:
        return []
    registry = {}
    for row in source.get('numeric_registry') or []:
        key = (row.get('fact_id'), row.get('field_path'))
        if key in registry:
            raise ValueError('duplicate_kr_numeric_registry_key')
        registry[key] = row
    claims = []
    for fact in source.get('fact_catalog') or []:
        fields, ref = fact.get('fields') or {}, fact['fact_id']
        if fact.get('source') != 'KIWOOM_REST' or fact.get('as_of_date') != completed:
            continue
        kind, rows, pairs, units, texts = fact.get('fact_type'), [], {}, {}, []
        scope = fields.get('market_scope')
        if kind == 'market_cross_section_index':
            rows = [r for r in adapter.get('indices', []) if r.get('symbol') == fields.get('symbol')]
            pairs = {'close': 'close', 'return_pct': 'return_pct', 'label': 'name', 'symbol': 'symbol'}
            units = {'close': 'index', 'return_pct': 'pct'}
            title = str(fields.get('label'))
        elif kind == 'market_cross_section_sector':
            if fields.get('taxonomy') != 'kiwoom-sector-index-v1' or scope != 'KOSPI':
                continue
            rows = [r for r in adapter.get('size_context', []) if r.get('source_ref') == fields.get('source_ref')
                    and r.get('state') == 'CURRENT_DIRECTIONAL' and r.get('basis') == 'official_size_index']
            pairs = {'return_pct': 'return_pct', 'sector': 'name', 'source_ref': 'source_ref'}
            units = {'return_pct': 'pct'}
            title = f"{scope} {fields.get('sector')}"
        elif kind == 'market_flow':
            if scope not in {'KOSPI', 'KOSDAQ'} or fields.get('currency') != 'KRW':
                continue
            rows = [r for r in adapter.get('market_flows', []) if r.get('source_ref') == fields.get('source_ref')
                    and r.get('unit') == 'KRW']
            pairs = {'net_buy_amount': 'net_flow', 'actor': 'participant', 'market_scope': 'scope', 'source_ref': 'source_ref'}
            units = {'net_buy_amount': 'KRW'}
            actor = {'foreign': '외국인', 'institution': '기관', 'retail': '개인'}.get(fields.get('actor'))
            if actor is None:
                continue
            title = f"{scope} {actor} 순매수"
        elif kind == 'market_breadth_counts' and scope in {'KOSPI', 'KOSDAQ'}:
            aggregate = adapter.get('breadth') or {}
            refs = aggregate.get('source_refs') or []
            if aggregate.get('availability') != 'AVAILABLE' or not refs or not set(refs) <= eligible:
                continue
            rows = [r['breadth'] for r in adapter.get('breadth_by_scope', []) if r.get('scope') == scope
                    and (r.get('breadth') or {}).get('availability') == 'AVAILABLE']
            pairs = {'advance_count': 'advancers', 'decline_count': 'decliners', 'unchanged_count': 'unchanged',
                     'eligible_count': 'eligible_count'}
            units = dict.fromkeys(pairs, 'count')
            title = f'{scope} 등락 종목'
        else:
            continue
        if len(rows) != 1 or any(fields.get(k) != rows[0].get(v) for k, v in pairs.items()):
            continue
        row = rows[0]
        if kind != 'market_breadth_counts' and (row.get('source_ref') not in eligible or row.get('as_of_date') != completed):
            continue
        parts, permitted = [], True
        for key, unit in units.items():
            entry = registry.get((ref, 'fields.' + key)) or {}
            value = fields.get(key)
            if (not number(value) or entry.get('value') != value or entry.get('unit') != unit
                    or entry.get('registered') is not True or entry.get('prose_allowed') is not True
                    or entry.get('scope') not in {'market', 'both'}):
                permitted = False
                break
            if unit == 'count' and (value < 0 or int(value) != value):
                permitted = False
                break
            parts.append(component(ref, 'fields.' + key, value, 'OBSERVED_VALUE', unit, completed))
            if unit == 'pct':
                texts.append(f'{value:+.2f}%')
            elif unit == 'index':
                texts.append(f'{value:,.2f}')
            elif unit == 'KRW':
                texts.append(f'{value / 100000000:+,.2f}억원')
            else:
                label = {'advance_count': '상승', 'decline_count': '하락', 'unchanged_count': '보합', 'eligible_count': '전체'}[key]
                texts.append(f'{label} {int(value):,}개')
        if not permitted:
            continue
        parts += [component(ref, 'fields.' + k, fields[k], 'INSTRUMENT', 'TEXT', completed)
                  for k in pairs if k not in units]
        parts.append(component(ref, 'as_of_date', completed, 'DATE', 'ISO_DATE', completed))
        claims.append(claim('KR_LOCAL_MARKET', parts, f"• {title}: {' / '.join(texts)} ({completed})",
            parents=[ref], formula='KRW / 100000000 for display only' if kind == 'market_flow' else None,
            metadata=dict(fact_sha256=digest(fact), adapter_row_sha256=digest(row),
                          registry_sha256=digest([registry[(ref, 'fields.' + k)] for k in units]))))
    return claims
