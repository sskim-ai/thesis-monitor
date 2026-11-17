"""One explicit current CLI binding; historical qualifications remain separate.

This local runtime review grants no Source use or model-call budget. It pins an
installed executable and existing credential reference, never credential bytes.
"""
from dataclasses import dataclass
import json
import os
from pathlib import Path
import shutil
import stat

from app.services.official_codex_shadow_transport_service import (
    OfficialCodexBinding, OfficialShadowError, command_prefix, file_sha256,
    validate_binding as validate_historical_binding,
)
from app.services.production_model_profile import sol_high
from app.services.unified_snapshot_contract import digest

CONTRACT='current-official-codex-runtime-binding-v1'
QUALIFICATION='current-official-codex-runtime-review-v1'
SIGNATURE_REQUIREMENT='=identifier "codex" and anchor apple generic and certificate leaf[subject.OU] = "2DC432GLL2"'
FLAGS=('--ephemeral','--skip-git-repo-check','--sandbox','--ignore-user-config',
    '--ignore-rules','--json','--output-schema','--output-last-message')
OVERRIDES=('OPENAI_API_KEY','CODEX_API_KEY','CODEX_ACCESS_TOKEN','OPENAI_BASE_URL',
    'OPENAI_FEDERATION_RULE_ID','OPENAI_IDENTITY_TOKEN_FILE','OPENAI_WORKLOAD_IDENTITY_CONTEXT')


@dataclass(frozen=True)
class CurrentOfficialCodexBinding(OfficialCodexBinding):
    runtime_contract: str=CONTRACT
    display_path: str=''
    auth_source: str=''


def _require(value,code):
    if not value:raise OfficialShadowError('CURRENT_RUNTIME_'+code)


def resolve_codex_executable(binding=None):
    if binding is not None:
        value=binding_from_json(binding) if isinstance(binding,dict) else binding
        return str(value.executable)
    candidates=(os.environ.get('CODEX_CLI_BIN'),'/Applications/ChatGPT.app/Contents/Resources/codex',
        shutil.which('codex'),str(Path.home()/'Applications/Codex.app/Contents/Resources/codex'),
        str(Path.home()/'.codex/packages/standalone/current/bin/codex'))
    for name in candidates:
        if name and Path(name).is_file() and os.access(name,os.X_OK):return str(Path(name).resolve())
    raise OfficialShadowError('CURRENT_RUNTIME_INSTALLED_CLI_MISSING')


def binding_from_json(value):
    raw=dict(value)
    for key in ('executable','qualification_path'):
        if raw.get(key) is not None:raw[key]=Path(raw[key])
    cls=CurrentOfficialCodexBinding if 'runtime_contract' in raw else OfficialCodexBinding
    return cls(**raw)


def auth_identity(path):
    path=Path(path).resolve();s=path.stat()
    _require(path.is_file() and s.st_uid==os.getuid() and not stat.S_IMODE(s.st_mode)&0o077,'AUTH_REFERENCE_UNSAFE')
    return dict(path=str(path),device=s.st_dev,inode=s.st_ino,uid=s.st_uid,mode=oct(stat.S_IMODE(s.st_mode)),content_read=False)


def freeze_current_binding(*, inspection_path, qualification_path, profile):
    """Freeze actual local inspection, not a model entitlement or approval."""
    profile=sol_high(profile)
    source=Path(inspection_path);inspection=json.loads(source.read_bytes())
    commands=inspection['commands'];signature=inspection['signature']
    _require(all(commands[k]['returncode']==0 and commands[k].get('inspection_started') is True
        for k in ('version','options','auth')),'LOCAL_INSPECTION_INCOMPLETE')
    _require(all(commands['options']['flags'].get(flag) is True for flag in FLAGS),'REQUIRED_FLAG_UNSUPPORTED')
    _require(commands['auth']['method']=='CHATGPT','CHATGPT_AUTH_UNVERIFIED')
    _require(signature['returncode']==0 and signature['requirement']==SIGNATURE_REQUIREMENT
        and signature['network']=='OS_DENY_NETWORK','INSTALLATION_SIGNATURE_UNVERIFIED')
    path=Path(inspection['selected_executable']);display=inspection['selected_display_path']
    _require(path.resolve()==path and Path(display).resolve()==path,'EXECUTABLE_RESOLUTION_DRIFT')
    observed=next(row for row in inspection['candidates'] if row['display_path']==display)
    _require(file_sha256(path)==observed['sha256'],'EXECUTABLE_DRIFT')
    package=path.parent.parent/'codex-package.json'
    metadata=json.loads(package.read_bytes())
    _require(commands['version']['version']=='codex-cli '+metadata['version']
        and metadata['variant']=='codex' and metadata['entrypoint']=='bin/codex','PACKAGE_VERSION_OR_LAYOUT')
    auth=auth_identity(inspection['auth_reference']['path'])
    _require(auth==inspection['auth_reference'],'AUTH_REFERENCE_DRIFT')
    qualification=dict(contract=QUALIFICATION,executable=str(path),display_path=display,
        executable_sha256=observed['sha256'],version=commands['version']['version'],
        package_path=str(package),package_sha256=file_sha256(package),
        installation_signature=signature,inspection_path=str(source),inspection_sha256=file_sha256(source),
        environment=inspection['environment'],auth_reference=auth,auth_method='CHATGPT_LOCAL_CONFIRMED',
        account_comparison='SAME_LOCAL_AUTH_REFERENCE_NOT_ACCOUNT_ID_INSPECTION',
        execution_profile=profile.model_request(),profile_contract=profile.contract,
        command_prefix=list(command_prefix(profile)),flags=commands['options']['flags'],
        user_config_policy='IGNORE_USER_CONFIG_AND_RULES_KEEP_MANAGED_REQUIREMENTS',
        model_entitlement='UNKNOWN_UNTIL_APPROVED_CALL',remote_metadata_requests=0,
        inspection_does_not_authorize_inference=True)
    from app.services.unified_run_artifacts import durable_json
    qualification_path=Path(qualification_path)
    durable_json(qualification_path,qualification,exclusive=True)
    return CurrentOfficialCodexBinding(executable=path,executable_sha256=observed['sha256'],
        version=commands['version']['version'],auth_method='CHATGPT_LOCAL_CONFIRMED',
        home=inspection['environment']['HOME'],codex_home=inspection['environment'].get('CODEX_HOME'),
        user_config_sha256=None,installation_verified=True,qualification_path=qualification_path,
        qualification_sha256=file_sha256(qualification_path),display_path=display,auth_source=auth['path'])


def _review(binding,profile):
    _require(type(binding) is CurrentOfficialCodexBinding and binding.runtime_contract==CONTRACT,'BINDING_TYPE')
    profile=sol_high(profile)
    path=binding.executable
    _require(path.is_absolute() and path.resolve()==path and Path(binding.display_path).resolve()==path
        and path.is_file() and os.access(path,os.X_OK) and path.stat().st_uid==os.getuid()
        and not path.stat().st_mode&stat.S_IWOTH,'EXECUTABLE_IDENTITY')
    _require(file_sha256(path)==binding.executable_sha256,'EXECUTABLE_DRIFT')
    qpath=binding.qualification_path
    _require(qpath is not None and qpath.is_absolute() and qpath.resolve()==qpath and qpath.is_file()
        and qpath.stat().st_uid==os.getuid() and file_sha256(qpath)==binding.qualification_sha256,'REVIEW_DRIFT')
    q=json.loads(qpath.read_bytes())
    _require(binding.installation_verified and q['contract']==QUALIFICATION
        and q['executable']==str(path) and q['display_path']==binding.display_path
        and q['executable_sha256']==binding.executable_sha256 and q['version']==binding.version,
        'REVIEW_EXECUTABLE_MISMATCH')
    _require(q['installation_signature']['returncode']==0
        and q['installation_signature']['requirement']==SIGNATURE_REQUIREMENT
        and file_sha256(Path(q['inspection_path']))==q['inspection_sha256'],'PROVENANCE_DRIFT')
    package=Path(q['package_path'])
    _require(file_sha256(package)==q['package_sha256'] and package==path.parent.parent/'codex-package.json',
        'PACKAGE_DRIFT')
    metadata=json.loads(package.read_bytes())
    _require(binding.version=='codex-cli '+metadata['version'] and metadata['entrypoint']=='bin/codex',
        'PACKAGE_VERSION_MISMATCH')
    _require(q['execution_profile']==profile.model_request() and q['profile_contract']==profile.contract
        and q['command_prefix']==list(command_prefix(profile)) and all(q['flags'].get(f) is True for f in FLAGS),
        'PROFILE_OR_OPTIONS_DRIFT')
    _require(q['auth_reference']==auth_identity(binding.auth_source) and q['auth_method']==binding.auth_method
        and binding.auth_method=='CHATGPT_LOCAL_CONFIRMED' and binding.user_config_sha256 is None,
        'AUTH_REFERENCE_DRIFT')
    _require(q['environment']['HOME']==binding.home and q['environment'].get('CODEX_HOME')==binding.codex_home,
        'ENVIRONMENT_BINDING_DRIFT')
    return q


def validate_binding(binding,codex_bin,*,profile=None):
    if type(binding) is not CurrentOfficialCodexBinding:
        return validate_historical_binding(binding,codex_bin,profile=profile)
    q=_review(binding,profile)
    _require(codex_bin==str(binding.executable),'EXECUTABLE_MISMATCH')
    _require(not any(os.environ.get(key) for key in OVERRIDES),'AUTH_OR_PROVIDER_OVERRIDE')
    _require(os.environ.get('HOME')==binding.home,'HOME_DRIFT')
    current=Path(os.environ.get('CODEX_HOME',str(Path(binding.home)/'.codex')))/'auth.json'
    _require(auth_identity(current)==q['auth_reference'],'CREDENTIAL_STORE_DRIFT')
    override=os.environ.get('CODEX_CLI_BIN')
    _require(not override or Path(override).resolve()==binding.executable,'CLI_OVERRIDE_DRIFT')
    _require(os.environ.get('PATH')==q['environment']['PATH'],'PATH_DRIFT')


def parent_environment(binding,base=None):
    if type(binding) is not CurrentOfficialCodexBinding:
        return dict(os.environ if base is None else base)
    from app.services.vnext_execution_profile import SOL_HIGH_V1
    q=_review(binding,SOL_HIGH_V1)
    env={k:v for k,v in (os.environ if base is None else base).items() if k in ('TMPDIR','LANG')}
    env.update(HOME=binding.home,PATH=q['environment']['PATH'])
    if binding.codex_home is not None:env['CODEX_HOME']=binding.codex_home
    return env


def invocation_environment(binding,*,root,namespace):
    if type(binding) is not CurrentOfficialCodexBinding:return None
    from app.services.codex_runtime_state_service import prepare_codex_runtime_state
    state=prepare_codex_runtime_state(Path(root),namespace=namespace,auth_source=Path(binding.auth_source))
    env=state.environment(parent_environment(binding))
    _require(auth_identity(state.codex_home/'auth.json')==auth_identity(binding.auth_source),
        'ISOLATED_AUTH_REFERENCE_DRIFT')
    return env
