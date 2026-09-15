"""Context-preserving aggregation for directional proof harnesses."""

from __future__ import annotations

from collections.abc import Callable, Mapping, Sequence


CONTRACT_VERSION = "context-preserving-proof-finalization-v1"
MAX_CONTEXT_CANDIDATES = 4


class FinalizationContractError(ValueError):
    """Raised when proof artifacts violate frozen context identity."""


def _fail(code: str, detail: object) -> None:
    raise FinalizationContractError(f"{code}:{detail}")


def _mapping(value: object, *, code: str) -> Mapping[str, object]:
    if not isinstance(value, Mapping):
        _fail(code, type(value).__name__)
    return value


def _sequence(value: object, *, code: str) -> Sequence[object]:
    if not isinstance(value, Sequence) or isinstance(value, (str, bytes)):
        _fail(code, type(value).__name__)
    return value


def _unique_tickers(values: Sequence[object], *, code: str) -> tuple[str, ...]:
    tickers = tuple(str(value) for value in values)
    if len(tickers) != len(set(tickers)):
        _fail(code, tickers)
    return tickers


def _document_tickers(
    document: Mapping[str, object],
    *,
    expected: Sequence[str],
    code: str,
) -> tuple[str, ...]:
    tickers = _unique_tickers(
        _sequence(document.get("tickers"), code=f"{code}_TICKERS_MISSING"),
        code=f"{code}_DUPLICATE_DECLARED_TICKER",
    )
    if len(tickers) > MAX_CONTEXT_CANDIDATES:
        _fail(f"{code}_CONTEXT_EXCEEDS_MAX", len(tickers))
    if set(tickers) != set(expected):
        _fail(f"{code}_DECLARED_MEMBERSHIP_MISMATCH", tickers)
    return tickers


def _row_tickers(
    rows: object,
    *,
    expected: Sequence[str],
    code: str,
    nested_candidate: bool = False,
) -> tuple[str, ...]:
    values = _sequence(rows, code=f"{code}_ROWS_MISSING")
    tickers: list[str] = []
    for value in values:
        row = _mapping(value, code=f"{code}_ROW_INVALID")
        if nested_candidate:
            row = _mapping(row.get("candidate"), code=f"{code}_CANDIDATE_INVALID")
        ticker = row.get("ticker")
        if ticker is None:
            _fail(f"{code}_TICKER_MISSING", row)
        tickers.append(str(ticker))
    unique = _unique_tickers(tickers, code=f"{code}_DUPLICATE_TICKER")
    if set(unique) != set(expected):
        _fail(f"{code}_MEMBERSHIP_MISMATCH", unique)
    return unique


def _invocation_id(document: Mapping[str, object], *, code: str) -> str:
    transport = _mapping(document.get("transport"), code=f"{code}_TRANSPORT_MISSING")
    invocation_id = transport.get("invocation_id")
    if not invocation_id:
        _fail(f"{code}_INVOCATION_ID_MISSING", transport)
    return str(invocation_id)


def _fictional_index(
    documents: Sequence[Mapping[str, object]],
    *,
    phase: str,
    generation_id: str,
) -> dict[tuple[int, int], Mapping[str, object]]:
    indexed: dict[tuple[int, int], Mapping[str, object]] = {}
    for document in documents:
        if str(document.get("generation_id")) != generation_id:
            _fail(f"{phase.upper()}_GENERATION_MISMATCH", document.get("generation_id"))
        if document.get("status") != "PASS":
            _fail(f"{phase.upper()}_DOCUMENT_NOT_PASS", document.get("status"))
        key = (int(document["repetition"]), int(document["context"]))
        if key in indexed:
            _fail(f"{phase.upper()}_DUPLICATE_CONTEXT", key)
        indexed[key] = document
    return indexed


def finalize_fictional_contexts(
    *,
    generation_id: str,
    stage1_documents: Sequence[Mapping[str, object]],
    stage2_documents: Sequence[Mapping[str, object]],
    expected_membership: Mapping[tuple[int, int], Sequence[str]],
    finalize_context: Callable[
        [Mapping[str, object], Mapping[str, object]], Sequence[Mapping[str, object]]
    ],
) -> dict[str, object]:
    """Validate and aggregate fictional rows without a repetition-wide model batch."""

    stage1 = _fictional_index(
        stage1_documents,
        phase="stage1",
        generation_id=generation_id,
    )
    stage2 = _fictional_index(
        stage2_documents,
        phase="stage2",
        generation_id=generation_id,
    )
    expected_keys = set(expected_membership)
    if set(stage1) != expected_keys:
        _fail("STAGE1_CONTEXT_IDENTITY_MISMATCH", sorted(stage1))
    if set(stage2) != expected_keys:
        _fail("STAGE2_CONTEXT_IDENTITY_MISMATCH", sorted(stage2))

    final_rows: list[dict[str, object]] = []
    lineage_rows: list[dict[str, object]] = []
    context_rows: list[dict[str, object]] = []
    for key in sorted(expected_keys):
        repetition, context = key
        expected = tuple(str(ticker) for ticker in expected_membership[key])
        if len(expected) > MAX_CONTEXT_CANDIDATES:
            _fail("EXPECTED_CONTEXT_EXCEEDS_MAX", {"key": key, "count": len(expected)})
        first = stage1[key]
        second = stage2[key]
        first_declared = _document_tickers(
            first,
            expected=expected,
            code="STAGE1",
        )
        second_declared = _document_tickers(
            second,
            expected=expected,
            code="STAGE2",
        )
        if set(first_declared) != set(second_declared):
            _fail("STAGE1_STAGE2_CONTEXT_MEMBERSHIP_MISMATCH", key)
        _row_tickers(first.get("rows"), expected=expected, code="STAGE1")
        _row_tickers(second.get("rows"), expected=expected, code="STAGE2")
        compositions = _sequence(
            second.get("compositions"),
            code="FINAL_COMPOSITIONS_MISSING",
        )
        _row_tickers(
            compositions,
            expected=expected,
            code="FINAL_COMPOSITION",
            nested_candidate=True,
        )
        composition_by_ticker: dict[str, Mapping[str, object]] = {}
        for value in compositions:
            composition = _mapping(value, code="FINAL_COMPOSITION_INVALID")
            candidate = _mapping(
                composition.get("candidate"),
                code="FINAL_COMPOSITION_CANDIDATE_INVALID",
            )
            ticker = str(candidate["ticker"])
            if composition.get("core_snapshot_sha256") != composition.get(
                "post_compose_core_sha256"
            ):
                _fail("CORE_HASH_MISMATCH", {"key": key, "ticker": ticker})
            composition_by_ticker[ticker] = composition

        audited = [dict(row) for row in finalize_context(first, second)]
        _row_tickers(audited, expected=expected, code="FINAL_AUDIT")
        stage1_invocation_id = _invocation_id(first, code="STAGE1")
        stage2_invocation_id = _invocation_id(second, code="STAGE2")
        for row in audited:
            ticker = str(row["ticker"])
            composition = composition_by_ticker[ticker]
            row.update(
                {
                    "repetition": repetition,
                    "context": context,
                    "stage1_invocation_id": stage1_invocation_id,
                    "stage2_invocation_id": stage2_invocation_id,
                    "core_snapshot_sha256": composition["core_snapshot_sha256"],
                    "post_compose_core_sha256": composition[
                        "post_compose_core_sha256"
                    ],
                }
            )
            final_rows.append(row)
            lineage_rows.append(
                {
                    "repetition": repetition,
                    "context": context,
                    "ticker": ticker,
                    "stage1_invocation_id": stage1_invocation_id,
                    "stage2_invocation_id": stage2_invocation_id,
                    "core_snapshot_sha256": composition["core_snapshot_sha256"],
                }
            )
        context_rows.append(
            {
                "repetition": repetition,
                "context": context,
                "tickers": list(expected),
                "candidate_count": len(expected),
                "stage1_invocation_id": stage1_invocation_id,
                "stage2_invocation_id": stage2_invocation_id,
                "status": "PASS",
            }
        )

    identities = [(int(row["repetition"]), str(row["ticker"])) for row in final_rows]
    if len(identities) != len(set(identities)):
        _fail("DUPLICATE_FINAL_IDENTITY", identities)
    expected_identities = {
        (repetition, str(ticker))
        for (repetition, _context), tickers in expected_membership.items()
        for ticker in tickers
    }
    if set(identities) != expected_identities:
        _fail("FINAL_IDENTITY_COVERAGE_MISMATCH", identities)
    return {
        "status": "PASS",
        "contract": CONTRACT_VERSION,
        "context_count": len(context_rows),
        "final_row_count": len(final_rows),
        "unique_identity_count": len(set(identities)),
        "directional_core_batch_over_limit_use_count": 0,
        "aggregate_uses_context_model_schema": False,
        "context_rows": context_rows,
        "lineage_rows": lineage_rows,
        "final_rows": final_rows,
    }


def _shadow_index(
    documents: Sequence[Mapping[str, object]],
    *,
    phase: str,
    generation_id: str,
) -> dict[int, Mapping[str, object]]:
    indexed: dict[int, Mapping[str, object]] = {}
    for document in documents:
        if str(document.get("generation_id")) != generation_id:
            _fail(f"SHADOW_{phase.upper()}_GENERATION_MISMATCH", document.get("generation_id"))
        if document.get("status") != "PASS":
            _fail(f"SHADOW_{phase.upper()}_DOCUMENT_NOT_PASS", document.get("status"))
        key = int(document["context"])
        if key in indexed:
            _fail(f"SHADOW_{phase.upper()}_DUPLICATE_CONTEXT", key)
        indexed[key] = document
    return indexed


def audit_shadow_context_aggregation(
    *,
    generation_id: str,
    monolithic_documents: Sequence[Mapping[str, object]],
    stage1_documents: Sequence[Mapping[str, object]],
    stage2_documents: Sequence[Mapping[str, object]],
    expected_membership: Mapping[int, Sequence[str]],
) -> dict[str, object]:
    """Audit a multi-context shadow aggregation without global model batches."""

    documents = {
        "monolithic": _shadow_index(
            monolithic_documents,
            phase="monolithic",
            generation_id=generation_id,
        ),
        "stage1": _shadow_index(
            stage1_documents,
            phase="stage1",
            generation_id=generation_id,
        ),
        "stage2": _shadow_index(
            stage2_documents,
            phase="stage2",
            generation_id=generation_id,
        ),
    }
    expected_keys = set(expected_membership)
    for phase, indexed in documents.items():
        if set(indexed) != expected_keys:
            _fail(f"SHADOW_{phase.upper()}_CONTEXT_IDENTITY_MISMATCH", sorted(indexed))

    final_tickers: list[str] = []
    lineage_rows: list[dict[str, object]] = []
    context_rows: list[dict[str, object]] = []
    for context in sorted(expected_keys):
        expected = tuple(str(ticker) for ticker in expected_membership[context])
        if len(expected) > MAX_CONTEXT_CANDIDATES:
            _fail(
                "SHADOW_EXPECTED_CONTEXT_EXCEEDS_MAX",
                {"context": context, "count": len(expected)},
            )
        current = {phase: indexed[context] for phase, indexed in documents.items()}
        for phase, document in current.items():
            _document_tickers(document, expected=expected, code=f"SHADOW_{phase.upper()}")
        _row_tickers(
            current["monolithic"].get("rows"),
            expected=expected,
            code="SHADOW_MONOLITHIC",
        )
        _row_tickers(
            current["stage1"].get("rows"),
            expected=expected,
            code="SHADOW_STAGE1",
        )
        _row_tickers(
            current["stage2"].get("rows"),
            expected=expected,
            code="SHADOW_STAGE2",
        )
        compositions = _sequence(
            current["stage2"].get("compositions"),
            code="SHADOW_COMPOSITIONS_MISSING",
        )
        _row_tickers(
            compositions,
            expected=expected,
            code="SHADOW_COMPOSITION",
            nested_candidate=True,
        )
        _row_tickers(
            current["stage2"].get("final_rows"),
            expected=expected,
            code="SHADOW_FINAL",
        )
        composition_by_ticker = {
            str(_mapping(value, code="SHADOW_COMPOSITION_INVALID")["candidate"]["ticker"]): _mapping(
                value,
                code="SHADOW_COMPOSITION_INVALID",
            )
            for value in compositions
        }
        invocation_ids = {
            phase: _invocation_id(document, code=f"SHADOW_{phase.upper()}")
            for phase, document in current.items()
        }
        for ticker in expected:
            composition = composition_by_ticker[ticker]
            if composition.get("core_snapshot_sha256") != composition.get(
                "post_compose_core_sha256"
            ):
                _fail(
                    "SHADOW_CORE_HASH_MISMATCH",
                    {"context": context, "ticker": ticker},
                )
            final_tickers.append(ticker)
            lineage_rows.append(
                {
                    "context": context,
                    "ticker": ticker,
                    "monolithic_invocation_id": invocation_ids["monolithic"],
                    "stage1_invocation_id": invocation_ids["stage1"],
                    "stage2_invocation_id": invocation_ids["stage2"],
                    "core_snapshot_sha256": composition["core_snapshot_sha256"],
                }
            )
        context_rows.append(
            {
                "context": context,
                "tickers": list(expected),
                "candidate_count": len(expected),
                "invocation_ids": invocation_ids,
                "status": "PASS",
            }
        )

    if len(final_tickers) != len(set(final_tickers)):
        _fail("SHADOW_DUPLICATE_FINAL_TICKER", final_tickers)
    expected_tickers = {
        str(ticker) for tickers in expected_membership.values() for ticker in tickers
    }
    if set(final_tickers) != expected_tickers:
        _fail("SHADOW_FINAL_TICKER_COVERAGE_MISMATCH", final_tickers)
    return {
        "status": "PASS",
        "contract": CONTRACT_VERSION,
        "context_count": len(context_rows),
        "final_row_count": len(final_tickers),
        "unique_ticker_count": len(set(final_tickers)),
        "directional_core_batch_over_limit_use_count": 0,
        "aggregate_uses_context_model_schema": False,
        "context_rows": context_rows,
        "lineage_rows": lineage_rows,
    }
