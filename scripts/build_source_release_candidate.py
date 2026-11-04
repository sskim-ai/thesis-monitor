"""Versioned, default-off candidate using the original release dependency walk."""
import ast
from copy import deepcopy
import hashlib
import json
from pathlib import Path
import sys


def pin(path):
    raw=Path(path).read_bytes()
    return dict(bytes=len(raw),sha256=hashlib.sha256(raw).hexdigest())


def build_candidate(root, base_path, *, core, modules, interpreter):
    root,base_path=Path(root),Path(base_path)
    original=base_path.read_bytes();base=json.loads(original)
    if (base['default_enabled'] is not False or base['owner_approved'] is not False
            or base['delivery']!='NO_SEND' or tuple(base['modules'])!=tuple(modules)):
        raise ValueError('candidate_original_policy_required')
    pending=list(base['source_pins'])+list(core)+['scripts/build_source_release_candidate.py']
    seen=set()
    while pending:
        name=pending.pop()
        if name in seen:continue
        path=root/name
        if (not path.is_file() or path.is_symlink() or path.suffix!='.py'
                or '..' in Path(name).parts or Path(name).is_absolute()):
            raise ValueError('candidate_dependency_not_source')
        seen.add(name);parts=Path(name).parts
        for count in range(1,len(parts)):
            init='/'.join(parts[:count])+'/__init__.py'
            if (root/init).is_file() and init not in seen:pending.append(init)
        for node in ast.walk(ast.parse(path.read_bytes())):
            names=[]
            if isinstance(node,ast.Import):names=[a.name for a in node.names]
            elif isinstance(node,ast.ImportFrom) and node.module:
                module=node.module
                if node.level:module='.'.join(parts[:-node.level])+'.'+module
                names=[module]+[module+'.'+a.name for a in node.names]
            for module in names:
                if module.startswith(('app.','scripts.')):
                    for candidate in (module.replace('.','/')+'.py',module.replace('.','/')+'/__init__.py'):
                        if (root/candidate).is_file() and candidate not in seen:pending.append(candidate)
    result=deepcopy(base)
    result.update(source_pins={name:pin(root/name) for name in sorted(seen)},
        candidate_state='CODE_REVIEWED_NOT_INSTALLED',base_manifest_sha256=hashlib.sha256(original).hexdigest(),
        candidate_contract='source-release-candidate-v1',release_review='OFFLINE_ONLY_NO_LIVE_AUTHORITY',
        runtime=dict(python_version=sys.version,platform=sys.platform),interpreter=str(interpreter),
        interpreter_pin=pin(Path(interpreter).resolve()))
    if base_path.read_bytes()!=original:raise ValueError('candidate_historical_base_changed')
    return result


def write_candidate(path, value):
    path=Path(path);path.parent.mkdir(parents=True,exist_ok=True)
    with path.open('x') as f:json.dump(value,f,sort_keys=True,indent=2);f.write('\n')
    return pin(path)
