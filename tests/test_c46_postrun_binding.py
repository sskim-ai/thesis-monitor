"""Postrun startup binding only: no main, Mac commands, live receipts or network."""

import ast
from hashlib import sha256
import json
from pathlib import Path
from types import SimpleNamespace

import pytest


SCRIPT = Path(__file__).resolve().parents[1] / "ops/c44/postrun.py"
C45_COMMIT = "374145c4337d50673db672c73a49e071b1801b5b"


@pytest.fixture
def startup(tmp_path):
    here, c38 = tmp_path / "postrun", tmp_path / "c38"
    old, current = tmp_path / "old-code", tmp_path / "c45-code"
    for path in (here, c38, old, current):
        path.mkdir()
    schedule = dict(code_root=str(old), code_commit="old-C38", label="original-once",
        run_root="original-run", target_session="2026-11-23", max_models=42,
        max_http=710, calendar={"Hour": 8, "Minute": 10}, configuration_path="same-config",
        configuration_sha256="old-config", plist_sha256="old-plist",
        C37_timer_sha256="old-timer", after_terminal="original-policy")
    original = json.dumps(schedule).encode()
    (c38 / "SCHEDULE.json").write_bytes(original)
    installation = {"original_C38_schedule_sha256": sha256(original).hexdigest()}
    final_pin = {"script_sha256": sha256(SCRIPT.read_bytes()).hexdigest()}
    (current / "module.py").write_text("current C45 code\n")
    file_sha = sha256((current / "module.py").read_bytes()).hexdigest()
    binding = dict(prior_C38_schedule_sha256=installation["original_C38_schedule_sha256"],
        schedule_overrides=dict(code_root=str(current), code_commit=C45_COMMIT,
            configuration_sha256="new-config", plist_sha256="new-plist",
            C37_timer_sha256="new-timer", after_terminal="US_REGULAR_OFF"),
        code_pins={"files": {"module.py": {"sha256": file_sha}}})
    (c38 / "CODE_PINS.json").write_text(json.dumps(binding["code_pins"]))
    tree = ast.parse(SCRIPT.read_text())
    functions = [node for node in tree.body if isinstance(node, ast.FunctionDef)
                 and node.name in {"load_execution_schedule", "verify_receipts"}]
    env = dict(HERE=here, C38=c38, Path=Path, sha256=sha256, json=json,
        sys=SimpleNamespace(path=[str(old)]),
        read=lambda path: json.loads(Path(path).read_bytes()),
        pin=lambda path: sha256(Path(path).read_bytes()).hexdigest(),
        command=lambda *args: C45_COMMIT)
    exec(compile(ast.Module(body=functions, type_ignores=[]), str(SCRIPT), "exec"), env)
    return SimpleNamespace(here=here, c38=c38, old=old, current=current, schedule=schedule,
        original=original, installation=installation, final_pin=final_pin,
        binding=binding, env=env, tree=tree)


def install_binding(state):
    raw = json.dumps(state.binding).encode()
    (state.here / "CURRENT_EXECUTION_BINDING.json").write_bytes(raw)
    state.final_pin["current_execution_binding_sha256"] = sha256(raw).hexdigest()


def test_bound_startup_preserves_registration_and_selects_c45_before_observer(startup):
    install_binding(startup)
    effective = startup.env["load_execution_schedule"](startup.installation, startup.final_pin)
    for key, value in startup.schedule.items():
        if key not in startup.binding["schedule_overrides"]:
            assert effective[key] == value
    assert effective["code_commit"] == C45_COMMIT
    assert effective["after_terminal"] == "US_REGULAR_OFF"
    assert effective["_current_code_pins"] == startup.binding["code_pins"]
    assert startup.env["sys"].path[0] == str(startup.current)
    assert (startup.c38 / "SCHEDULE.json").read_bytes() == startup.original
    main = next(n for n in startup.tree.body if isinstance(n, ast.FunctionDef) and n.name == "main")
    calls = {n.func.id: n.lineno for n in ast.walk(main)
             if isinstance(n, ast.Call) and isinstance(n.func, ast.Name)
             and n.func.id in {"load_execution_schedule", "observe"}}
    assert calls["load_execution_schedule"] < calls["observe"]


def test_no_binding_keeps_original_schedule_and_original_pin_source(startup):
    effective = startup.env["load_execution_schedule"](startup.installation, startup.final_pin)
    assert effective == startup.schedule
    assert "_current_code_pins" not in effective
    assert startup.env["sys"].path[0] == str(startup.old)


def test_changed_binding_bytes_are_rejected_before_import_path_change(startup):
    install_binding(startup)
    path = startup.here / "CURRENT_EXECUTION_BINDING.json"
    path.write_bytes(path.read_bytes() + b"\n")
    with pytest.raises(AssertionError):
        startup.env["load_execution_schedule"](startup.installation, startup.final_pin)
    assert startup.env["sys"].path == [str(startup.old)]


def test_bound_wrong_code_pin_is_rejected_by_existing_receipt_check(startup):
    startup.binding["code_pins"]["files"]["module.py"]["sha256"] = "0" * 64
    install_binding(startup)
    effective = startup.env["load_execution_schedule"](startup.installation, startup.final_pin)
    # Existing CODE_PINS is correct, but must not override the bound current pin.
    with pytest.raises(AssertionError):
        startup.env["verify_receipts"](None, effective, {})
