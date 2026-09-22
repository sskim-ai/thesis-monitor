import pytest

from scripts.m12dc_r2_offline_exposure_audit import (
    classify_event,
    parse_events,
    safe_member,
    subject_tickers,
)


def test_failed_pipeline_is_not_successful_source_read():
    events = parse_events(
        [
            "exec",
            "zsh rg input | head",
            " succeeded in 0ms:",
            "zsh: command not found: rg",
            "codex",
            "{}",
        ]
    )
    assert classify_event(events[0])[0] == ["PATH_ONLY_OR_NO_CONTENT"]
    assert events[0]["before_final_response"]


def test_history_field_value_is_not_equivalent_to_schema_enum():
    base = {"command": "cat docs/reports/old.json", "attribution": "UNAMBIGUOUS"}
    assert classify_event(
        {**base, "returned_text": '{"overall_direction":{"enum":["BUY","HOLD"]}}'}
    )[0] == ["OTHER_UNBOUND_SOURCE"]
    assert classify_event({**base, "returned_text": '{"overall_direction":"SELL"}'})[0] == [
        "PRIOR_JUDGMENT_OR_CLASSIFICATION"
    ]


def test_interleaved_completions_are_not_falsely_assigned():
    events = parse_events(
        [
            "exec",
            "cmd one",
            "exec",
            "cmd two",
            " succeeded in 0ms:",
            "one payload",
            " succeeded in 0ms:",
            "two payload",
            "codex",
            "{}",
        ]
    )
    assert len(events) == 2
    assert all(e["attribution"] == "INTERLEAVED_OR_UNRESOLVED" for e in events)
    assert all(classify_event(e)[0] == ["UNRESOLVED_FROM_LOG"] for e in events)
    assert "one payload" in events[1]["returned_text"]


def test_response_or_reasoning_is_not_returned_content():
    events = parse_events(
        [
            "exec",
            "cmd",
            " succeeded in 0ms:",
            "file contents",
            "thinking",
            "not a source",
            "codex",
            "final",
        ]
    )
    assert events[0]["returned_text"] == "file contents"


def test_skill_is_undeclared_not_approved_static_contract():
    event = {
        "command": "cat .agents/skills/name/SKILL.md",
        "attribution": "UNAMBIGUOUS",
        "returned_text": "production procedure",
    }
    assert classify_event(event)[0] == ["UNDECLARED_PROJECT_OR_SKILL_INSTRUCTION"]


def test_filename_search_not_historical_content():
    event = {
        "command": "find docs",
        "attribution": "UNAMBIGUOUS",
        "returned_text": "docs/reports/old.json\ndocs/reports/other.json",
    }
    assert classify_event(event)[0] == ["PATH_ONLY_OR_NO_CONTENT"]


def test_static_owner_is_distinguished_from_fixture():
    event = {
        "command": "cat scripts/contract.py",
        "attribution": "UNAMBIGUOUS",
        "returned_text": "def check(): pass",
    }
    assert classify_event(event)[0] == ["APPROVED_STATIC_CONTRACT"]
    event["command"] = "cat tests/test_contract.py"
    assert classify_event(event)[0] == ["OTHER_UNBOUND_SOURCE"]


def test_archive_paths_fail_closed():
    assert safe_member("prefix/normal.json")
    assert not any(safe_member(path) for path in ("/etc/file", "../x", "a/../../x", "a\\b", ""))


def test_no_final_response_is_not_before_response_proof():
    event = parse_events(["exec", "cmd", " succeeded in 0ms:", "data"])[0]
    assert not event["before_final_response"]


def test_broad_grep_historical_values_are_not_missed():
    event = {
        "command": "grep -R pattern .",
        "attribution": "UNAMBIGUOUS",
        "returned_text": './docs/reports/old.json:7: "archetype":"DURABLE_FRANCHISE"',
    }
    assert classify_event(event)[0] == ["PRIOR_JUDGMENT_OR_CLASSIFICATION"]
    event["returned_text"] = './tests/test_policy.py:7: "archetype":"DURABLE_FRANCHISE"'
    assert classify_event(event)[0] == ["OTHER_UNBOUND_SOURCE"]


def test_null_classification_is_not_prior_label():
    event = {
        "command": "jq filter docs/reports/check.json",
        "attribution": "UNAMBIGUOUS",
        "returned_text": '{"archetype":null,"valuation_regime_tier":null}',
    }
    assert classify_event(event)[0] == ["OTHER_UNBOUND_SOURCE"]


def test_subject_wrapper_is_not_a_ticker():
    assert subject_tickers({"subjects": [{"ticker": "TEST"}]}) == ["TEST"]
    assert subject_tickers([{"ticker": "TEST"}]) == ["TEST"]
    with pytest.raises(ValueError):
        subject_tickers({"unknown": []})
    with pytest.raises(ValueError):
        subject_tickers({"subjects": [{"ticker": "TEST"}, {"ticker": "TEST"}]})


def test_line_counts_are_not_skill_content():
    event = {
        "command": "wc -l .agents/skills/name/SKILL.md",
        "attribution": "UNAMBIGUOUS",
        "returned_text": "  115 .agents/skills/name/SKILL.md",
    }
    assert classify_event(event)[0] == ["PATH_ONLY_OR_NO_CONTENT"]
