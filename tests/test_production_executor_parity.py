"""Production admission cannot silently change the qualified CLI execution body."""
import ast
import inspect

from app.services import official_codex_production_executor as production
from app.services import official_codex_shadow_transport_service as historical


def test_production_executor_body_preserves_frozen_transport_semantics():
    original = ast.parse(inspect.getsource(historical.invoke_official_shadow)).body[0]
    candidate = ast.parse(inspect.getsource(production.invoke_official_bound)).body[0]

    class ReceiptContractOnly(ast.NodeTransformer):
        def visit_Name(self, node):
            if node.id == 'receipt_contract':
                return ast.Name(id='CONTRACT', ctx=node.ctx)
            return node

    statements = candidate.body[1:]
    assert isinstance(candidate.body[0], ast.Expr) and isinstance(candidate.body[0].value, ast.Constant)
    assert ast.dump(ast.Module(body=original.body, type_ignores=[]), include_attributes=False) == ast.dump(
        ReceiptContractOnly().visit(ast.Module(body=statements, type_ignores=[])), include_attributes=False)
    for name in ('COMMAND_PREFIX', '_require', 'validate_binding', 'file_sha256', 'classify_input_events'):
        assert getattr(production, name) is getattr(historical, name)
