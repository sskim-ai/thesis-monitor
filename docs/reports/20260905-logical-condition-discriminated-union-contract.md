# Logical Condition Discriminated Union Contract

`type`이 union discriminator다. `LEAF`는 `leaf_ref`를 필수로 갖고 `children` 필드 자체를 허용하지 않는다. `ANY_OF`와 `ALL_OF`는 최소 두 child를 필수로 갖고 `leaf_ref`를 허용하지 않는다. Source expression도 같은 구조적 분리를 사용한다.

Cross-condition branch mixing과 cross-ticker refs는 기존 source-condition identity 검증으로 계속 차단한다.
