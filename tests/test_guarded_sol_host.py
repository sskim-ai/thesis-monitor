from copy import deepcopy
import json

import pytest

from maintenance.guarded_sol_host import Binding, TASK, VERSION, digest, require_request, write_once, plain, host_profile


def subject():
    packet = {'base': {'public_security': {'canonical_security_id': 'SYNTHETIC'}, 'as_of': 'DATED_ONLY'}}
    schema = {'type': 'object'}
    prompt = 'SYNTHETIC_NO_MODEL'
    scope = dict(account='SYNTHETIC_ACCOUNT', security='SYNTHETIC', owner_sha256=digest(packet), source_generation='DATED_ONLY')
    request = dict(model='gpt-6.1-sol', effort='high', execution_profile='SOL_61_HIGH_EXECUTION_V1',
        prompt_version=VERSION, contract='UNIFIED_STAGE_REVIEW_V3_SOL_61_HIGH_V1', timeout_seconds=600,
        input_bytes=393216, output_bytes=131072, retries=0, send=False, stage='BLIND', invocation_id='SYNTHETIC_BLIND',
        prompt_sha=digest(prompt.encode()), schema_sha=digest(schema), source_sha=digest(packet), account=scope['account'],
        security=packet['base']['public_security'], source_as_of=scope['source_generation'], prior_stage_sha=None)
    return request, prompt, schema, packet, scope


def test_exact_sol_request_and_bound_adj():
    values = list(subject())
    require_request(*values)
    values[0].update(stage='ADJUDICATION', invocation_id='SYNTHETIC_ADJ', prior_stage_sha='accepted-stage-digest')
    require_request(*values)


@pytest.mark.parametrize('field,value', [('model', 'gpt-6-astra'), ('effort', 'medium'),
    ('execution_profile', 'ASTRA_XHIGH_EXECUTION_V1'), ('prompt_version', 'V1'), ('account', 'OTHER'),
    ('source_sha', '0' * 64), ('prompt_sha', '0' * 64), ('schema_sha', '0' * 64), ('retries', 1), ('timeout_seconds', 601)])
def test_mixed_identity_denied(field, value):
    values = list(subject()); values[0][field] = value
    with pytest.raises(ValueError):
        require_request(*values)


def test_unaccepted_prior_and_oversized_input_denied():
    values = list(subject()); values[0]['stage'] = 'ADJUDICATION'
    with pytest.raises(ValueError, match='prior'):
        require_request(*values)
    values = list(subject()); values[1] = 'x' * 393217; values[0]['prompt_sha'] = digest(values[1].encode())
    with pytest.raises(ValueError):
        require_request(*values)


def test_binding_exact_catalog_scope_and_helper_bytes(tmp_path):
    binary = tmp_path / 'binary'; write_once(binary, b'SYNTHETIC_NOT_EXECUTABLE')
    catalog = tmp_path / 'models.json'; write_once(catalog, dict(models=[dict(slug='gpt-6.1-sol', supported_reasoning_levels=[dict(effort='high')])]))
    legacy = tmp_path / 'legacy'; legacy.mkdir()
    helper = tmp_path / 'helper.py'; write_once(helper, b'# SYNTHETIC\n')
    scope = tmp_path / 'scope.json'; write_once(scope, dict(task=TASK, execution_profile='SOL_61_HIGH_EXECUTION_V1', root=str(tmp_path), ledger=str(tmp_path / 'inference-ledger.json')), 0o400)
    binding = Binding(binary, digest(binary.read_bytes()), catalog, digest(catalog.read_bytes()), legacy,
                      {'helper.py': digest(helper.read_bytes())}, tmp_path, scope, digest(scope.read_bytes()))
    binding.verify()
    helper.write_bytes(b'# CHANGED\n')
    with pytest.raises(ValueError, match='helper'):
        binding.verify()


def test_symlink_and_overwrite_rejected(tmp_path):
    target = tmp_path / 'original'; write_once(target, b'unchanged')
    link = tmp_path / 'link'; link.symlink_to(target)
    with pytest.raises(ValueError): plain(link)
    with pytest.raises(FileExistsError): write_once(target, b'bad')
    assert target.read_bytes() == b'unchanged'


def test_shared_response_filter_is_exact_and_network_defaults_off(tmp_path):
    from types import SimpleNamespace
    binding = SimpleNamespace(root=tmp_path, binary=tmp_path/'binary', catalog=tmp_path/'models.json', scope=tmp_path/'scope.json')
    text = host_profile(binding, tmp_path/'stage')
    assert text.count('[a-f0-9]') == 128  # read and write deny exceptions
    assert '(regex #"' in text and '(deny network*)' in text
    assert 'allow network-outbound' not in text and 'auth.json' not in text
