"""REV46 attempt policy over the unchanged KR8 KIS valuation/render owners."""
from scripts.kr8_fy1_models import Kr8Execution, SUBJECTS, require_kr8_plan, p
from scripts.r9_rev11_models import FreshExecution, owner
from scripts.us14_models import Us14Execution


class Rev46Kr8Execution(Kr8Execution):
    TIMEOUT_SECONDS = 600
    MAX_RETRIES = 2
    ATTEMPT_BUDGET = 30
    MESSAGE_COUNT = 9
    SUCCESS_TERMINAL = 'R2B_R9_REV46_KR_9_MESSAGE_PASS'
    FAILURE_TERMINAL = 'R2B_R9_REV46_KR_MODEL_MESSAGE_GAP'
    invoke = Us14Execution.invoke
    bounded = Us14Execution.bounded
    run = Us14Execution.run
    run_qualified = Us14Execution.run_qualified
    authorize_launch_context = Us14Execution.authorize_launch_context
    execution_policy = Us14Execution.execution_policy
    identity = Us14Execution.identity

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.active_batches = None

    def full_topology(self):
        rows = [r for r in owner._batch_topology() if r['market'] == 'kr']
        p.require(len(rows) == 3 and sorted(t for r in rows for t in r['subjects']) == list(SUBJECTS), 'kr8_batch_topology_gap')
        return rows

    def batch_topology(self):
        return [r for r in self.full_topology() if self.active_batches is None or r['batch'] in self.active_batches]

    def freeze_extra(self):
        return dict(super().freeze_extra(), maximum_attempts=self.ATTEMPT_BUDGET,
            capture_contract='KR8_MARKET_PLUS_STOCK_CAPTURE_V1')

    def verify(self):
        FreshExecution.verify(self)
        require_kr8_plan(self.source_frozen)
        p.require(self.frozen['scope'] == 'KR8_ONLY' and self.frozen['max_calls'] == 10, 'kr8_model_budget_scope')
        p.require(self.frozen['timeout_seconds'] == 600 and self.frozen['retries'] == 2, 'kr8_attempt_policy_drift')
        p.require(set(self.prepared) == set(SUBJECTS) and set(self.projected) == {'kr'}, 'kr8_model_input_scope')
        p.require(self.freeze_extra() == {k: self.frozen[k] for k in self.freeze_extra()}, 'kr8_source_or_authority_drift')
        p.require(self.guard.blocked_attempts == 0, 'kr8_manual_mutation_attempt')
        p.require(all(r['market'] == 'kr' and set(r['subjects']) <= set(SUBJECTS) and r['attempts'] <= 3
            for r in self.ledger), 'kr8_call_scope')
        for stage, limit in self.CALL_LIMITS.items():
            p.require(sum(r['stage'] == stage for r in self.ledger) <= limit, 'kr8_logical_call_budget')

    def render(self):
        super().render()
        output = self.root/'messages'
        support = p.read(output/'supporting-market-kr.json')
        p.require(support['production_sends'] == support['network_requests'] == 0, 'kr_market_delivery_not_disabled')
        (output/'MARKET_KR.txt').write_text(support['prepared_text'])
        manifest = p.read(output/'manifest.json')
        p.require(manifest['stock_message_count'] == 8 and len(list(output.glob('*.txt'))) == 9,
            'kr8_exact_nine_messages_required')
        p.write(output/'manifest.json', dict(manifest, total=9, capture_contract='KR8_MARKET_PLUS_STOCK_CAPTURE_V1',
            market_message_sha256=support['prepared_text_sha256']))
