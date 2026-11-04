"""Actual v4 research consumer with live component-owner admission, not Core."""
import copy,re
from app.services import vnext_composition_research as previous,vnext_research_v3 as v3
from app.services.vnext_operating_components import replay
from app.services.vnext_readable_research import readable_number
from app.services.vnext_research_store import digest
schema=previous.schema

def validate_and_render(value,packet,*,original_context,owner,receipt,invocation,price_source_bytes=None):
    owner.consume(packet,receipt,invocation=invocation)
    base,extra=replay(packet,original_context=original_context)
    cat={n['catalog_id']:n for n in extra};draft=copy.deepcopy(value);paths=previous.text_paths(value)
    retained=[];occurrences=[];seen=set()
    for b in value['numeric_fact_refs']:
        rid,path=b['ref_id'],b['text_ref'];token='{{numeric:'+rid+'}}'
        if rid in seen or not re.fullmatch('[a-z][a-z_]{0,30}',rid):raise ValueError('numeric_occurrence_identity')
        seen.add(rid)
        if b['catalog_id'] not in cat:retained.append(b);continue
        n=cat[b['catalog_id']]
        if path not in paths or paths[path].count(token)!=1 or sum(t.count(token) for t in paths.values())!=1:
            raise ValueError('component_numeric_occurrence_missing')
        if path.startswith(('timing_','newbuyer.','holder.','valuation_')):raise ValueError('component_wrong_consumer_slot')
        if path.startswith('economic_drivers_'):
            side,i,_=path.split('.')
            if not set(n['supporting_refs'])<=set(value[side][int(i)]['refs']):raise ValueError('component_support_missing')
        marker='REPORTED_COMPONENT_'+rid.upper()
        if any(marker in t for t in paths.values()):raise ValueError('component_marker_collision')
        v3.put_text(draft,path,previous.text_paths(draft)[path].replace(token,marker))
        occurrences.append(dict(**n,ref_id=rid,text_ref=path,marker=marker))
    draft['numeric_fact_refs']=retained
    checked=previous.validate_and_render(draft,base,original_context=original_context,price_source_bytes=price_source_bytes)
    for n in occurrences:
        text=readable_number(n,packet)
        v3.put_text(checked['rendered'],n['text_ref'],previous.text_paths(checked['rendered'])[n['text_ref']].replace(n.pop('marker'),text))
        n['rendered']=text;checked['numeric_claims'].append(n)
    checked['rendered']['numeric_fact_refs']=copy.deepcopy(value['numeric_fact_refs'])
    checked.update(packet_sha256=digest(packet),draft_sha256=digest(value),component_sha=digest(packet['operating_components']),
        component_owner_consumed=True,component_use='RESEARCH_ONLY')
    return checked

def prompt(packet,stage,*,knowledge,prior=None):
    return previous.prompt(packet,stage,knowledge=knowledge,prior=prior)+'''
SOURCE-BOUND OPERATING COMPONENTS: The operating_components attachment is newly
admitted research-only consumption of existing original statements, not new collection.
Account components and their prior comparable values reconcile to the reported total.
Use only catalog placeholders for numbers; cite the supporting original operating
income ref when describing component evidence. Explain observed accounting contributions
and distinguish them from causal mechanism, recurrence, underwriting quality or a
one-off investment gain. Missing explanation is not evidence of nonrecurrence.
Same filing remains ONE lineage. Insurance revenue still cannot become the denominator
of total operating margin. No valuation, EPS, trading direction or strict Core authority
is granted. NewBuyer and hypothetical Holder may discuss bounded qualitative risks,
but these component numeric facts belong only in economic explanation slots.
Do not use probability vocabulary even in a negated disclaimer. No target signal is given.
'''
