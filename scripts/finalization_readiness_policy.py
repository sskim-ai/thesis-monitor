"""Objective readiness gates with nonblocking decision-variance diagnostics."""

from __future__ import annotations

from collections.abc import Mapping


CONTRACT_VERSION = "hard-semantic-diagnostic-variance-readiness-v1"


def evaluate_hard_readiness(
    *,
    hard_gates: Mapping[str, bool],
    variance_diagnostics: Mapping[str, int],
) -> dict[str, object]:
    """Keep objective proof failures hard and repetition variance diagnostic."""

    failed = sorted(name for name, passed in hard_gates.items() if not passed)
    return {
        "status": "PASS" if not failed else "FAIL",
        "contract": CONTRACT_VERSION,
        "hard_gate_count": len(hard_gates),
        "failed_hard_gates": failed,
        "decision_material_variance": {
            str(name): int(count)
            for name, count in sorted(variance_diagnostics.items())
        },
        "decision_variance_readiness_blocking": False,
    }


def evaluate_finalization_readiness(
    *,
    hard_gates: Mapping[str, bool],
    variance_diagnostics: Mapping[str, int],
) -> dict[str, object]:
    """Canonical public name for the shared hard-vs-diagnostic policy."""

    return evaluate_hard_readiness(
        hard_gates=hard_gates,
        variance_diagnostics=variance_diagnostics,
    )
