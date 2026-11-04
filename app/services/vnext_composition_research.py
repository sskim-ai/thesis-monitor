"""Source-replayed arithmetic attachment to v4, preserving its acceptance gates."""
import copy
import re
from app.services import vnext_research_v4 as v4, vnext_research_v3 as v3
from app.services.vnext_earnings_composition import verify
from app.services.vnext_readable_research import readable_number, render
from app.services.vnext_research_store import digest

schema = v4.schema
CONTRACT = 'vnext-composition-research-v1'


def text_paths(value):
    return v3.text_paths({k: v for k, v in value.items() if k not in v4.EXTRA})


def validate_and_render(value, packet, *, original_context, price_source_bytes=None):
    v4.ResearchV4.model_validate(value)
    base, extra = verify(packet, original_context=original_context)
    catalog = {n['catalog_id']: n for n in extra}; draft = copy.deepcopy(value)
    paths = text_paths(value); seen = set(); occurrences = []; retained = []
    for b in value['numeric_fact_refs']:
        rid, path = b['ref_id'], b['text_ref']; token = '{{numeric:'+rid+'}}'
        if rid in seen or not re.fullmatch('[a-z][a-z_]{0,30}', rid): raise ValueError('numeric_occurrence_identity')
        seen.add(rid)
        if b['catalog_id'] not in catalog: retained.append(b); continue
        n = catalog[b['catalog_id']]
        if path not in paths or paths[path].count(token) != 1 or sum(t.count(token) for t in paths.values()) != 1:
            raise ValueError('numeric_source_occurrence_missing')
        if path.startswith(('timing_', 'newbuyer.', 'holder.', 'valuation_')):
            raise ValueError('derived_margin_wrong_consumer_slot')
        if path.startswith('economic_drivers_'):
            side, index, _ = path.split('.')
            if not set(n['supporting_refs']) <= set(value[side][int(index)]['refs']):
                raise ValueError('derived_margin_support_missing')
        marker = 'SOURCE_COMPOSITION_'+rid.upper()
        if any(marker in t for t in paths.values()): raise ValueError('composition_marker_collision')
        v3.put_text(draft, path, text_paths(draft)[path].replace(token, marker))
        occurrences.append(dict(**n, ref_id=rid, text_ref=path, marker=marker))
    draft['numeric_fact_refs'] = retained
    checked = v4.validate_and_render(draft, base, price_source_bytes=price_source_bytes)
    checked = render(checked, base)
    for n in occurrences:
        text = readable_number(n, packet)
        v3.put_text(checked['rendered'], n['text_ref'], text_paths(checked['rendered'])[n['text_ref']].replace(n.pop('marker'), text))
        n['rendered'] = text; checked['numeric_claims'].append(n)
    checked['rendered']['numeric_fact_refs'] = copy.deepcopy(value['numeric_fact_refs'])
    checked.update(packet_sha256=digest(packet), draft_sha256=digest(value), attachment_contract=CONTRACT,
        composition_sha256=digest(packet['earnings_composition']), source_replay_verified=True)
    return checked


def prompt(packet, stage, *, knowledge, prior=None):
    return v4.prompt(packet, stage, knowledge=knowledge, prior=prior) + '''
SOURCE-BOUND COMPOSITION ATTACHMENT: Original replay now supplies explicitly derived
operating margins when the exact revenue/operating accounts, period, unit and basis
match. These are not new independent source votes, normalized profit, cash conversion
or investment grants. Use their catalog placeholders only for economic explanation,
never in price/Holder/NewBuyer numeric slots or valuation. Cite BOTH original refs in
an economic driver using a derived margin. Underlying fact refs remain the only driver
ref namespace; catalog IDs or price fact IDs are not evidence refs.
An InsuranceRevenue denominator is not total operating revenue. Denied derived ratios
must stay absent. All source quality/corroboration gaps remain; a large ratio and
within-statement arithmetic do not establish durable profitability or causal mechanism.
Net income is ONLY the exact dated total. No growth, EPS, attributable-profit, TTM, FY1,
fair-value, or recurring-profit claim follows. Examine the actual account distinctions;
do not import issuer/industry narratives. Counter-hypotheses remain unresolved unless
available facts distinguish them. No desired signal or label is supplied.
'''
