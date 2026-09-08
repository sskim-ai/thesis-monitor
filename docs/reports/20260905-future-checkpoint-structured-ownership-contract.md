# Future Checkpoint Structured Ownership Contract

`claim_type`, `metric_refs`, `time_scope`, `checkpoint_kind`, `direction`, `evidence_refs`가 의미를 소유한다. Future checkpoint는 같은 subject와 generation의 eligible evidence가 metric을 소유하고, kind/direction 관계와 source logical severity가 맞으며, 현재 관측값을 만들어내지 않을 때만 통과한다.

- Korean future-tense regex added: `0`
- Ticker exception added: `0`
- Global semantic threshold weakened: `0`
- Unknown-to-SELL conversion: `0`

Frozen B audit에서 metric alias union은 통과했지만 source logical severity 검사가 각 condition 단위 superset을 요구해 `IBM` 합성 invalidation claim을 거절했다. 이는 threshold를 완화할 근거가 아니라, 동일 subject/generation/severity의 선택 evidence를 안전하게 union할지를 별도 bounded repair로 검토할 근거다.

- Actual unowned metric failures: `0`
- Kind/severity ownership failures: `2` candidates
- Audited false reject: `1` (`IBM`)
- Intended fail-closed: `1` (`GOOGL`)
