# Logical LEAF Schema Root Cause

이전 재귀 모델은 하나의 객체에 `type`, optional `condition_ref`, default-empty `children`를 함께 열어 두었다. 모델 출력 단계에서 `LEAF + children` 같은 모순된 shape가 표현 가능했고, Run C가 parser 경계에서 중단됐다.

의미 있는 child를 삭제하는 보정은 추가하지 않았다. Invalid shape는 typed schema error로 fail-closed한다.
