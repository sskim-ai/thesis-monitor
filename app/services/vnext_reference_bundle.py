"""Independent non-authoritative references over one immutable public snapshot.

Both original validators see the same base packet. A rejected family never
removes another family's evidence; draft consumption revalidates projections.
This is not a source Owner or a currentness grant.
"""
import re
from zipfile import BadZipFile
from app.services.vnext_research_store import digest

CONTRACT = 'vnext-independent-reference-bundle-v1'
KEYS = ('component_reference', 'historical_price_reference', 'research_financial_reference', 'reference_bundle')


def base_packet(packet):
    from app.services.vnext_composite_research import numeric_catalog
    base = {k: v for k, v in packet.items() if k not in KEYS}
    base['numeric_catalog'] = numeric_catalog(base)
    return base


def load_family(loader, *args):
    """Invalid public custody input is local to a family, not a bypass."""
    try:
        return loader(*args)
    except (ValueError, KeyError, TypeError, FileNotFoundError, BadZipFile):
        return {'reference_input_rejected': True}


def assemble(packet, *, component_reference=None, price_reference=None, financial_reference=None):
    from app.services import vnext_component_reference as component
    from app.services import vnext_historical_price_reference as price
    from app.services import sec_research_source_authority as financial
    from app.services.vnext_composite_research import numeric_catalog, ALLOWED, CONTRACT as BASE
    if any(k in packet for k in KEYS):
        raise ValueError('reference_bundle_requires_unattached_base')
    if packet.get('contract') != BASE or packet.get('numeric_catalog') != numeric_catalog(packet):
        raise ValueError('reference_bundle_base_drift')
    if packet.get('model') != 'OFF' or any(packet.get(k) is not False for k in
            ('send','strict_ready','holdings_included','user_thesis_included')):
        raise ValueError('reference_bundle_public_scope_required')
    if component_reference is None and price_reference is None and financial_reference is None:
        return dict(packet)
    result = dict(packet)
    families = {}
    for name, key, reference, validator in (
        ('accounting_components', 'component_reference', component_reference, component.project),
        ('historical_chart', 'historical_price_reference', price_reference, price.project),
        ('exact_financial_research', 'research_financial_reference', financial_reference, financial.project),
    ):
        if reference is None:
            continue
        try:
            projected = validator(packet, reference)
            if name == 'accounting_components':
                numbers = component.catalog(projected)
            elif name == 'exact_financial_research':
                numbers = financial.catalog(projected)
            else:
                numbers = []
                for f in projected['facts']:
                    binding = next(b for b in projected['source_bindings'] if b['timeframe'] == f['timeframe'])
                    e = next(e for e in packet['evidence'] if e['ref'] == binding['ref'] and e['status'] in ALLOWED)
                    numbers.append(dict(field='historical_chart.'+f['kind'], path=f['timeframe'],
                        value=f['value'], unit=f['unit'], basis=f['basis'], as_of=f['as_of'],
                        source_sha=f['source_sha'], lineage_group=e['lineage_group']))
            occurrences = [(n['field'], n['path'], n['source_sha'], n['as_of']) for n in numbers]
            if len(occurrences) != len(set(occurrences)):
                raise ValueError('reference_duplicate_occurrence')
        except (ValueError, KeyError, TypeError, IndexError, StopIteration) as exc:
            code=str(exc) if isinstance(exc,ValueError) and re.fullmatch(r'[A-Za-z_]{1,80}',str(exc)) else 'INPUT_SHAPE_INVALID'
            families[name] = dict(status='DENIED', reason='ORIGINAL_REFERENCE_VALIDATION_FAILED',
                                  detail=code,original_validator=validator.__module__, numbers=[])
            continue
        result[key] = projected
        families[name] = dict(status='DATED_REFERENCE_ONLY', contract=projected['contract'],
            projection_sha256=digest(projected), numbers=numbers,
            lineage_groups=sorted({n['lineage_group'] for n in numbers}))
    result['reference_bundle'] = dict(contract=CONTRACT, base_sha256=digest(packet),
        families=families, current_owner_issued=False, economic_authority_issued=False,
        independent_corroboration_claimed=False)
    result['numeric_catalog'] = numeric_catalog(result)
    return result


def verify(packet, **references):
    expected = assemble(base_packet(packet), **references)
    if expected != packet:
        raise ValueError('reference_bundle_consumption_binding')
