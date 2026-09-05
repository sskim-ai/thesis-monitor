# Future Checkpoint Root Cause

Run A/B의 거짓 거절은 source evidence가 ROIC/FCF 같은 checkpoint metric을 소유해도 validator가 자연어 문장의 한국어 시제와 어미를 다시 추정한 데서 발생했다. 같은 의미가 다른 자연어 표면형으로 표현되면 evidence-backed future checkpoint가 current-value fabrication처럼 분류됐다.

수리는 자연어 미래형 regex 확장이 아니다. Source occurrence와 claim이 가진 typed semantic metadata가 metric, time scope, checkpoint kind, direction, evidence ownership을 직접 소유한다.

## Frozen experiment result

2026-09-06 KST에 완료된 frozen generation은 FIRST `22/22`, A `22/22`, B `17/22`에서 fail-fast 중단됐다. C는 실행되지 않았다.

B의 future-checkpoint ownership 거절은 두 종목이었다.

- `GOOGL`: FCF/ROIC metric은 선택 evidence에 있지만 `STRENGTHENING` source logical severity가 없어 `future_checkpoint_kind_not_owned`로 차단됐다. 의도된 fail-closed다.
- `IBM`: FCF와 ROIC가 각각 별도의 `INVALIDATION_CANDIDATE` evidence에 소유되었으나 validator가 하나의 source condition이 두 metric 전체를 소유하도록 요구했다. 선택된 동일-severity evidence union 기준에서 false reject `1`로 분류한다.

Metric 소유권 거절은 B `2`종목, 실제 unowned metric 거절(`unsupported_future_checkpoint_metric`)은 `0`, audited future-checkpoint false reject는 A `0`, B `1`이다. 실험 후 hotfix와 rerun은 `0`이다.
