"""R4-R4 output representation; R3 evidence semantics remain unchanged."""
from app.services.accepted_directional_balance_service import (
    compatible_buy_scores, accepted_directional_balance, DIRECTION_BALANCE_OUTPUT_RULE,
)
from scripts import m12ds_r3_schemas as r3

obj, enum, string, refs = r3.obj, r3.enum, r3.string, r3.refs
core_schema = r3.core_schema
DOCUMENT_LABEL_RULE = '''Document labels must follow the selected source's explicit document_evidence_class.
AUDITOR_REVIEWED_INTERIM_STATEMENT means an auditor-reviewed interim statement, not a preliminary
earnings release and not an audited annual statement. A legacy preliminary_earnings storage type
does not override this proven document description. Do not change evidence authority or direction
because of this presentation label. If no class is proven, use a neutral filed-statement description.'''
CORE_PROMPT = r3.CORE_PROMPT + "\n" + DOCUMENT_LABEL_RULE
B_PROMPT = r3.B_PROMPT + "\n" + DIRECTION_BALANCE_OUTPUT_RULE + "\n" + DOCUMENT_LABEL_RULE


def decision_schema(cap, valuation, entry_catalog):
    schema = r3.decision_schema(cap, valuation, entry_catalog)
    for branch in schema['properties']['overall']['anyOf']:
        props = branch['properties']
        direction = props['overall_direction']['enum'][0]
        props['directional_buy_score'] = {'type':'number','enum':list(compatible_buy_scores(direction))}
    return schema


def normalize_decision(raw):
    row = r3.normalize_decision(raw)
    accepted_directional_balance(row['directional_buy_score'],row['overall_direction'])
    return row
