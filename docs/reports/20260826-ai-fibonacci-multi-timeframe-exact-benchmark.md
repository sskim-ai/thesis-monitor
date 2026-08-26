# AI Fibonacci Multi-Timeframe Exact Benchmark

Evidence-selected benchmark: `005490, 010120, GOOGL, WULF`. The set includes KR/US, extension/uptrend, mixed-timeframe, and no-added-value cases.

## 005490 (KR, steel_materials)

### Current Production Price Section

- Collapsed primary swing timeframe: `weekly`.
- Collapsed support: `{'atr': 24692.605903, 'bollinger_overlap': False, 'center': 337000.0, 'distance_to_lower_pct': 2.009985, 'distance_to_upper_pct': 4.871431, 'fibonacci_overlap': True, 'higher_timeframe_overlap_count': 1, 'higher_timeframe_score': 2, 'latest_reaction_date': '2025-10-27', 'lower_timeframe_overlap_count': 1, 'padding': 6173.151476, 'pivot_count': 3, 'pivot_dates': ['2025-10-27', '2025-03-17', '2025-07-21'], 'pivot_prices': [331500.0, 337000.0, 342000.0], 'pivot_type': 'high', 'reaction_count': 3, 'reaction_score': 3, 'recency_score': 0, 'score': 6, 'strength': 'Medium', 'timeframe': 'weekly', 'zone_high': 348173.151476, 'zone_low': 325326.848524}`.
- Collapsed resistance: `{'atr': 19904.538428, 'bollinger_overlap': False, 'center': 340000.0, 'distance_pct': 0.157791, 'fibonacci_overlap': True, 'higher_timeframe_overlap_count': 2, 'higher_timeframe_score': 3, 'latest_reaction_date': '2026-06-11', 'lower_timeframe_overlap_count': 0, 'padding': 4976.134607, 'pivot_count': 2, 'pivot_dates': ['2026-02-02', '2026-06-11'], 'pivot_prices': [337500.0, 342500.0], 'pivot_type': 'low', 'reaction_count': 2, 'reaction_score': 2, 'recency_score': 1, 'score': 7, 'strength': 'Medium', 'support_rank': None, 'timeframe': 'daily', 'zone_high': 347476.134607, 'zone_low': 332523.865393}`.
- Existing Fibonacci sets in packet: `['breakout', 'long_term', 'medium_term']`; not prose-rendered.

### Shadow V2

#### Monthly

- Status: `SELECTED`; role: `PRIMARY_STRUCTURAL_ZONE`; regime: `UPTREND_PULLBACK_HELD`; confidence: `medium`.
- Support: `None` (none)
- Resistance: `None` (none)
- Low anchor: `price-pivot:ff688252a014818e032d` (2022-09-01 / 211000.0; confirmed 2022-11-01)
- High anchor: `price-pivot:ba2b345da1c36a39d1a5` (2023-07-03 / 764000.0; confirmed 2023-08-01)
- Correction low: `price-pivot:1f47cf28b6d6044a74b6` (2025-02-03 / 227500.0; confirmed 2026-02-02)
- Fib mode: `BOTH`; backend levels: `7`.
  - `RETRACEMENT 0.382` = `552754.000000 KRW` from `price-pivot:ff688252a014818e032d` / `price-pivot:ba2b345da1c36a39d1a5`; `H - (H-L) * ratio`.
  - `RETRACEMENT 0.500` = `487500.000000 KRW` from `price-pivot:ff688252a014818e032d` / `price-pivot:ba2b345da1c36a39d1a5`; `H - (H-L) * ratio`.
  - `RETRACEMENT 0.618` = `422246.000000 KRW` from `price-pivot:ff688252a014818e032d` / `price-pivot:ba2b345da1c36a39d1a5`; `H - (H-L) * ratio`.
  - `EXTENSION 0.618` = `569254.000000 KRW` from `price-pivot:ff688252a014818e032d` / `price-pivot:ba2b345da1c36a39d1a5`, correction `price-pivot:1f47cf28b6d6044a74b6`; `C + (H-L) * ratio`.
  - `EXTENSION 1.000` = `780500.000000 KRW` from `price-pivot:ff688252a014818e032d` / `price-pivot:ba2b345da1c36a39d1a5`, correction `price-pivot:1f47cf28b6d6044a74b6`; `C + (H-L) * ratio`.
  - `EXTENSION 1.618` = `1122254.000000 KRW` from `price-pivot:ff688252a014818e032d` / `price-pivot:ba2b345da1c36a39d1a5`, correction `price-pivot:1f47cf28b6d6044a74b6`; `C + (H-L) * ratio`.
  - `EXTENSION 2.618` = `1675254.000000 KRW` from `price-pivot:ff688252a014818e032d` / `price-pivot:ba2b345da1c36a39d1a5`, correction `price-pivot:1f47cf28b6d6044a74b6`; `C + (H-L) * ratio`.
- Value-gated render refs: none.

#### Weekly

- Status: `SELECTED`; role: `INTERMEDIATE_ZONE`; regime: `RETRACEMENT_WITHIN_CONFIRMED_SWING`; confidence: `medium`.
- Support: `price-zone:a085d5a19b2c27069b12` (325326.848524–348173.151476, Medium)
- Resistance: `None` (none)
- Low anchor: `price-pivot:68db0de6459c34a56ff8` (2025-10-10 / 258500.0; confirmed 2025-10-20)
- High anchor: `price-pivot:04666eff2209fc9126d7` (2026-02-23 / 427500.0; confirmed 2026-03-03)
- Correction low: `None` (none)
- Fib mode: `RETRACEMENT`; backend levels: `3`.
  - `RETRACEMENT 0.382` = `362942.000000 KRW` from `price-pivot:68db0de6459c34a56ff8` / `price-pivot:04666eff2209fc9126d7`; `H - (H-L) * ratio`.
  - `RETRACEMENT 0.500` = `343000.000000 KRW` from `price-pivot:68db0de6459c34a56ff8` / `price-pivot:04666eff2209fc9126d7`; `H - (H-L) * ratio`.
  - `RETRACEMENT 0.618` = `323058.000000 KRW` from `price-pivot:68db0de6459c34a56ff8` / `price-pivot:04666eff2209fc9126d7`; `H - (H-L) * ratio`.
- Value-gated render refs: `price-fib:d0c9917248e3187168d7`, `price-fib:2bb345ea8959a036cbdb`.

#### Daily

- Status: `SELECTED`; role: `NEAREST_TACTICAL_ZONE`; regime: `UPTREND_PULLBACK_HELD`; confidence: `high`.
- Support: `price-zone:2f80cd3f04db03e72ffa` (332523.865393–347476.134607, Medium)
- Resistance: `price-zone:437394928c782fdb488f` (333389.795533–345610.204467, Strong)
- Low anchor: `price-pivot:c0c80cd835489c077305` (2025-10-10 / 258500.0; confirmed 2025-10-16)
- High anchor: `price-pivot:b901fd5006b2a8227878` (2025-10-29 / 331500.0; confirmed 2025-11-07)
- Correction low: `price-pivot:554b8174abb7941ef936` (2026-07-29 / 275000.0; confirmed 2026-08-07)
- Fib mode: `BOTH`; backend levels: `7`.
  - `RETRACEMENT 0.382` = `303614.000000 KRW` from `price-pivot:c0c80cd835489c077305` / `price-pivot:b901fd5006b2a8227878`; `H - (H-L) * ratio`.
  - `RETRACEMENT 0.500` = `295000.000000 KRW` from `price-pivot:c0c80cd835489c077305` / `price-pivot:b901fd5006b2a8227878`; `H - (H-L) * ratio`.
  - `RETRACEMENT 0.618` = `286386.000000 KRW` from `price-pivot:c0c80cd835489c077305` / `price-pivot:b901fd5006b2a8227878`; `H - (H-L) * ratio`.
  - `EXTENSION 0.618` = `320114.000000 KRW` from `price-pivot:c0c80cd835489c077305` / `price-pivot:b901fd5006b2a8227878`, correction `price-pivot:554b8174abb7941ef936`; `C + (H-L) * ratio`.
  - `EXTENSION 1.000` = `348000.000000 KRW` from `price-pivot:c0c80cd835489c077305` / `price-pivot:b901fd5006b2a8227878`, correction `price-pivot:554b8174abb7941ef936`; `C + (H-L) * ratio`.
  - `EXTENSION 1.618` = `393114.000000 KRW` from `price-pivot:c0c80cd835489c077305` / `price-pivot:b901fd5006b2a8227878`, correction `price-pivot:554b8174abb7941ef936`; `C + (H-L) * ratio`.
  - `EXTENSION 2.618` = `466114.000000 KRW` from `price-pivot:c0c80cd835489c077305` / `price-pivot:b901fd5006b2a8227878`, correction `price-pivot:554b8174abb7941ef936`; `C + (H-L) * ratio`.
- Value-gated render refs: `price-fib:15f828a1dc3a5c8038e5`.

### Multi-Timeframe Confluence

- `price-confluence:5d5840a0a7af6e19052a`: ['weekly', 'daily'] 337000.0–339500.0; tolerance `complete_link_min_timeframe_merge_pct` / 0.0175.
- `price-confluence:763adbec416a59ef53bf`: ['weekly', 'daily'] 340000.0–343000.000000; tolerance `complete_link_min_timeframe_merge_pct` / 0.0175.
- `price-confluence:3470e4fc5a690d61088b`: ['weekly', 'daily'] 320114.000000–323058.000000; tolerance `complete_link_min_timeframe_merge_pct` / 0.0175.

### Exact Shadow Render

```text
월봉(구조): 상승 구조의 조정 저점 유지
주봉(중기): 확정 스윙 범위 안의 되돌림; 현재 구간 325326.848524-348173.151476; Fib 되돌림 0.618 323058, 되돌림 0.500 343000
일봉(전술): 상승 구조의 조정 저점 유지; 지지 332523.865393-347476.134607; 저항 333389.795533-345610.204467; Fib 확장 0.618 320114
종합: 독립 시간축 주봉/일봉 근거가 337000-339500에서 겹칩니다.
```

Validation: `True`; human classification: `MATERIAL_IMPROVEMENT`; render length: `274` characters.

## 010120 (KR, industrial_epc)

### Current Production Price Section

- Collapsed primary swing timeframe: `weekly`.
- Collapsed support: `{'atr': 22755.77771, 'bollinger_overlap': False, 'center': 176500.0, 'distance_pct': 6.761032, 'fibonacci_overlap': True, 'higher_timeframe_overlap_count': 1, 'higher_timeframe_score': 2, 'latest_reaction_date': '2026-07-14', 'lower_timeframe_overlap_count': 0, 'padding': 5688.944428, 'pivot_count': 1, 'pivot_dates': ['2026-07-14'], 'pivot_prices': [176500.0], 'pivot_type': 'low', 'reaction_count': 1, 'reaction_score': 1, 'recency_score': 1, 'score': 5, 'strength': 'Medium', 'support_rank': 4, 'timeframe': 'daily', 'zone_high': 182188.944428, 'zone_low': 170811.055572}`.
- Collapsed resistance: `None`.
- Existing Fibonacci sets in packet: `['breakout', 'long_term', 'medium_term']`; not prose-rendered.

### Shadow V2

#### Monthly

- Status: `SELECTED`; role: `PRIMARY_STRUCTURAL_ZONE`; regime: `RETRACEMENT_WITHIN_CONFIRMED_SWING`; confidence: `medium`.
- Support: `None` (none)
- Resistance: `None` (none)
- Low anchor: `price-pivot:5a8cb7784aba8b561dc9` (2022-09-01 / 8960.0; confirmed 2023-04-03)
- High anchor: `price-pivot:e8ad06850724572e9fc9` (2026-05-04 / 335000.0; confirmed 2026-05-04)
- Correction low: `None` (none)
- Fib mode: `RETRACEMENT`; backend levels: `3`.
  - `RETRACEMENT 0.382` = `210452.720000 KRW` from `price-pivot:5a8cb7784aba8b561dc9` / `price-pivot:e8ad06850724572e9fc9`; `H - (H-L) * ratio`.
  - `RETRACEMENT 0.500` = `171980.000000 KRW` from `price-pivot:5a8cb7784aba8b561dc9` / `price-pivot:e8ad06850724572e9fc9`; `H - (H-L) * ratio`.
  - `RETRACEMENT 0.618` = `133507.280000 KRW` from `price-pivot:5a8cb7784aba8b561dc9` / `price-pivot:e8ad06850724572e9fc9`; `H - (H-L) * ratio`.
- Value-gated render refs: none.

#### Weekly

- Status: `SELECTED`; role: `INTERMEDIATE_ZONE`; regime: `RETRACEMENT_WITHIN_CONFIRMED_SWING`; confidence: `medium`.
- Support: `None` (none)
- Resistance: `None` (none)
- Low anchor: `price-pivot:88fb52bba7eda55f14d6` (2025-04-07 / 29360.0; confirmed 2025-05-07)
- High anchor: `price-pivot:943c9a2018db4c1d37ce` (2026-05-04 / 335000.0; confirmed 2026-05-11)
- Correction low: `None` (none)
- Fib mode: `RETRACEMENT`; backend levels: `3`.
  - `RETRACEMENT 0.382` = `218245.520000 KRW` from `price-pivot:88fb52bba7eda55f14d6` / `price-pivot:943c9a2018db4c1d37ce`; `H - (H-L) * ratio`.
  - `RETRACEMENT 0.500` = `182180.000000 KRW` from `price-pivot:88fb52bba7eda55f14d6` / `price-pivot:943c9a2018db4c1d37ce`; `H - (H-L) * ratio`.
  - `RETRACEMENT 0.618` = `146114.480000 KRW` from `price-pivot:88fb52bba7eda55f14d6` / `price-pivot:943c9a2018db4c1d37ce`; `H - (H-L) * ratio`.
- Value-gated render refs: none.

#### Daily

- Status: `SELECTED`; role: `NEAREST_TACTICAL_ZONE`; regime: `ABOVE_CONFIRMED_SWING_HIGH`; confidence: `medium`.
- Support: `price-zone:72042f05d37a2b39edf9` (170811.055572–182188.944428, Medium)
- Resistance: `None` (none)
- Low anchor: `price-pivot:b9f4b44e8bfd4598751e` (2025-09-26 / 53800.0; confirmed 2025-10-10)
- High anchor: `price-pivot:949c676ca1caf40e08b2` (2025-11-03 / 102000.0; confirmed 2025-11-05)
- Correction low: `None` (none)
- Fib mode: `RETRACEMENT`; backend levels: `3`.
  - `RETRACEMENT 0.382` = `83587.600000 KRW` from `price-pivot:b9f4b44e8bfd4598751e` / `price-pivot:949c676ca1caf40e08b2`; `H - (H-L) * ratio`.
  - `RETRACEMENT 0.500` = `77900.000000 KRW` from `price-pivot:b9f4b44e8bfd4598751e` / `price-pivot:949c676ca1caf40e08b2`; `H - (H-L) * ratio`.
  - `RETRACEMENT 0.618` = `72212.400000 KRW` from `price-pivot:b9f4b44e8bfd4598751e` / `price-pivot:949c676ca1caf40e08b2`; `H - (H-L) * ratio`.
- Value-gated render refs: none.

### Multi-Timeframe Confluence

- None.

### Exact Shadow Render

```text
월봉(구조): 확정 스윙 범위 안의 되돌림
주봉(중기): 확정 스윙 범위 안의 되돌림
일봉(전술): 확정 스윙 고점 상회; 지지 170811.055572-182188.944428
종합: 독립 시간축 근거의 유의미한 가격 중첩은 확인되지 않았습니다.
```

Validation: `True`; human classification: `NO_ADDED_VALUE`; render length: `138` characters.

## GOOGL (US, cloud_platform_software)

### Current Production Price Section

- Collapsed primary swing timeframe: `weekly`.
- Collapsed support: `{'atr': 10.831993, 'bollinger_overlap': False, 'center': 348.72, 'distance_to_lower_pct': 0.953423, 'distance_to_upper_pct': 1.96795, 'fibonacci_overlap': False, 'higher_timeframe_overlap_count': 1, 'higher_timeframe_score': 2, 'latest_reaction_date': '2026-07-09', 'lower_timeframe_overlap_count': 0, 'padding': 2.707998, 'pivot_count': 2, 'pivot_dates': ['2026-06-11', '2026-07-09'], 'pivot_prices': [346.36, 351.08], 'pivot_type': 'low', 'reaction_count': 2, 'reaction_score': 2, 'recency_score': 1, 'score': 5, 'strength': 'Medium', 'support_rank': 1, 'timeframe': 'daily', 'zone_high': 353.787998, 'zone_low': 343.652002}`.
- Collapsed resistance: `None`.
- Existing Fibonacci sets in packet: `['breakout', 'long_term', 'medium_term']`; not prose-rendered.

### Shadow V2

#### Monthly

- Status: `SELECTED`; role: `PRIMARY_STRUCTURAL_ZONE`; regime: `UPTREND_PULLBACK_HELD`; confidence: `medium`.
- Support: `None` (none)
- Resistance: `None` (none)
- Low anchor: `price-pivot:a8220d274f1aa6d5e0f6` (2022-11-01 / 83.34; confirmed 2023-05-01)
- High anchor: `price-pivot:8cffafed62ca66aa29f5` (2025-02-03 / 207.05; confirmed 2025-03-03)
- Correction low: `price-pivot:3a2991ff4326ea4dcac9` (2025-04-01 / 140.53; confirmed 2025-07-01)
- Fib mode: `BOTH`; backend levels: `7`.
  - `RETRACEMENT 0.382` = `159.792780 USD` from `price-pivot:a8220d274f1aa6d5e0f6` / `price-pivot:8cffafed62ca66aa29f5`; `H - (H-L) * ratio`.
  - `RETRACEMENT 0.500` = `145.195000 USD` from `price-pivot:a8220d274f1aa6d5e0f6` / `price-pivot:8cffafed62ca66aa29f5`; `H - (H-L) * ratio`.
  - `RETRACEMENT 0.618` = `130.597220 USD` from `price-pivot:a8220d274f1aa6d5e0f6` / `price-pivot:8cffafed62ca66aa29f5`; `H - (H-L) * ratio`.
  - `EXTENSION 0.618` = `216.982780 USD` from `price-pivot:a8220d274f1aa6d5e0f6` / `price-pivot:8cffafed62ca66aa29f5`, correction `price-pivot:3a2991ff4326ea4dcac9`; `C + (H-L) * ratio`.
  - `EXTENSION 1.000` = `264.240000 USD` from `price-pivot:a8220d274f1aa6d5e0f6` / `price-pivot:8cffafed62ca66aa29f5`, correction `price-pivot:3a2991ff4326ea4dcac9`; `C + (H-L) * ratio`.
  - `EXTENSION 1.618` = `340.692780 USD` from `price-pivot:a8220d274f1aa6d5e0f6` / `price-pivot:8cffafed62ca66aa29f5`, correction `price-pivot:3a2991ff4326ea4dcac9`; `C + (H-L) * ratio`.
  - `EXTENSION 2.618` = `464.402780 USD` from `price-pivot:a8220d274f1aa6d5e0f6` / `price-pivot:8cffafed62ca66aa29f5`, correction `price-pivot:3a2991ff4326ea4dcac9`; `C + (H-L) * ratio`.
- Value-gated render refs: `price-fib:983fba78eb7c575b3243`.

#### Weekly

- Status: `SELECTED`; role: `INTERMEDIATE_ZONE`; regime: `RETRACEMENT_WITHIN_CONFIRMED_SWING`; confidence: `medium`.
- Support: `None` (none)
- Resistance: `None` (none)
- Low anchor: `price-pivot:eeb94ce134c9839156dd` (2026-03-30 / 272.11; confirmed 2026-04-13)
- High anchor: `price-pivot:a3cb277945f995a8f04f` (2026-05-18 / 408.61; confirmed 2026-06-22)
- Correction low: `None` (none)
- Fib mode: `RETRACEMENT`; backend levels: `3`.
  - `RETRACEMENT 0.382` = `356.467000 USD` from `price-pivot:eeb94ce134c9839156dd` / `price-pivot:a3cb277945f995a8f04f`; `H - (H-L) * ratio`.
  - `RETRACEMENT 0.500` = `340.360000 USD` from `price-pivot:eeb94ce134c9839156dd` / `price-pivot:a3cb277945f995a8f04f`; `H - (H-L) * ratio`.
  - `RETRACEMENT 0.618` = `324.253000 USD` from `price-pivot:eeb94ce134c9839156dd` / `price-pivot:a3cb277945f995a8f04f`; `H - (H-L) * ratio`.
- Value-gated render refs: `price-fib:dbf63e7ebd1ceb677244`, `price-fib:258726bef1e5a48b3a9f`.

#### Daily

- Status: `SELECTED`; role: `NEAREST_TACTICAL_ZONE`; regime: `RETRACEMENT_WITHIN_CONFIRMED_SWING`; confidence: `medium`.
- Support: `price-zone:e0c229087896c4c724fa` (343.652002–353.787998, Medium)
- Resistance: `None` (none)
- Low anchor: `price-pivot:e3dd966a810999ad0fea` (2026-06-26 / 330.2; confirmed 2026-07-01)
- High anchor: `price-pivot:210798955a010c3e6bb8` (2026-07-16 / 375.27; confirmed 2026-07-22)
- Correction low: `None` (none)
- Fib mode: `RETRACEMENT`; backend levels: `3`.
  - `RETRACEMENT 0.382` = `358.053260 USD` from `price-pivot:e3dd966a810999ad0fea` / `price-pivot:210798955a010c3e6bb8`; `H - (H-L) * ratio`.
  - `RETRACEMENT 0.500` = `352.735000 USD` from `price-pivot:e3dd966a810999ad0fea` / `price-pivot:210798955a010c3e6bb8`; `H - (H-L) * ratio`.
  - `RETRACEMENT 0.618` = `347.416740 USD` from `price-pivot:e3dd966a810999ad0fea` / `price-pivot:210798955a010c3e6bb8`; `H - (H-L) * ratio`.
- Value-gated render refs: `price-fib:2d16169f539c60bc0761`, `price-fib:d083808e5a5e3beeb8d3`.

### Multi-Timeframe Confluence

- `price-confluence:cc79558781ba6bb1b9b3`: ['weekly', 'daily'] 352.735000–356.467000; tolerance `complete_link_min_timeframe_merge_pct` / 0.0175.
- `price-confluence:0396731826e353d06db5`: ['monthly', 'weekly'] 340.360000–340.692780; tolerance `complete_link_min_timeframe_merge_pct` / 0.0225.

### Exact Shadow Render

```text
월봉(구조): 상승 구조의 조정 저점 유지; Fib 확장 1.618 340.69278
주봉(중기): 확정 스윙 범위 안의 되돌림; Fib 되돌림 0.500 340.36, 되돌림 0.382 356.467
일봉(전술): 확정 스윙 범위 안의 되돌림; 현재 구간 343.652002-353.787998; Fib 되돌림 0.618 347.41674, 되돌림 0.500 352.735
종합: 독립 시간축 주봉/일봉 근거가 352.735-356.467에서 겹칩니다.
```

Validation: `True`; human classification: `MATERIAL_IMPROVEMENT`; render length: `254` characters.

## WULF (US, hpc_data_center)

### Current Production Price Section

- Collapsed primary swing timeframe: `weekly`.
- Collapsed support: `{'atr': 2.175615, 'bollinger_overlap': False, 'center': 16.545, 'distance_to_lower_pct': 1.954069, 'distance_to_upper_pct': 4.711422, 'fibonacci_overlap': False, 'higher_timeframe_overlap_count': 2, 'higher_timeframe_score': 3, 'latest_reaction_date': '2026-07-17', 'lower_timeframe_overlap_count': 0, 'padding': 0.543904, 'pivot_count': 1, 'pivot_dates': ['2026-07-17'], 'pivot_prices': [16.545], 'pivot_type': 'low', 'reaction_count': 1, 'reaction_score': 1, 'recency_score': 1, 'score': 5, 'strength': 'Medium', 'support_rank': 1, 'timeframe': 'daily', 'zone_high': 17.088904, 'zone_low': 16.001096}`.
- Collapsed resistance: `{'atr': 1.485393, 'bollinger_overlap': False, 'center': 17.7225, 'distance_pct': 6.149828, 'fibonacci_overlap': False, 'higher_timeframe_overlap_count': 2, 'higher_timeframe_score': 3, 'latest_reaction_date': '2026-03-25', 'lower_timeframe_overlap_count': 0, 'padding': 0.371348, 'pivot_count': 2, 'pivot_dates': ['2026-02-10', '2026-03-25'], 'pivot_prices': [17.695, 17.75], 'pivot_type': 'high', 'reaction_count': 2, 'reaction_score': 2, 'recency_score': 0, 'score': 5, 'strength': 'Medium', 'timeframe': 'daily', 'zone_high': 18.121348, 'zone_low': 17.323652}`.
- Existing Fibonacci sets in packet: `['breakout']`; not prose-rendered.

### Shadow V2

#### Monthly

- Status: `SELECTED`; role: `PRIMARY_STRUCTURAL_ZONE`; regime: `RETRACEMENT_WITHIN_CONFIRMED_SWING`; confidence: `medium`.
- Support: `None` (none)
- Resistance: `None` (none)
- Low anchor: `price-pivot:7288aa0d2e246fea4932` (2023-03-01 / 0.535; confirmed 2024-11-01)
- High anchor: `price-pivot:604d10a294a8efd11b93` (2026-06-01 / 29.84; confirmed 2026-07-01)
- Correction low: `None` (none)
- Fib mode: `RETRACEMENT`; backend levels: `3`.
  - `RETRACEMENT 0.382` = `18.645490 USD` from `price-pivot:7288aa0d2e246fea4932` / `price-pivot:604d10a294a8efd11b93`; `H - (H-L) * ratio`.
  - `RETRACEMENT 0.500` = `15.187500 USD` from `price-pivot:7288aa0d2e246fea4932` / `price-pivot:604d10a294a8efd11b93`; `H - (H-L) * ratio`.
  - `RETRACEMENT 0.618` = `11.729510 USD` from `price-pivot:7288aa0d2e246fea4932` / `price-pivot:604d10a294a8efd11b93`; `H - (H-L) * ratio`.
- Value-gated render refs: none.

#### Weekly

- Status: `SELECTED`; role: `INTERMEDIATE_ZONE`; regime: `ABOVE_CONFIRMED_SWING_HIGH`; confidence: `medium`.
- Support: `None` (none)
- Resistance: `None` (none)
- Low anchor: `price-pivot:8d3d8b709ee4d89fa81e` (2023-11-27 / 1.16; confirmed 2023-12-26)
- High anchor: `price-pivot:77cdf1e2cd278940f77d` (2023-12-26 / 3.17; confirmed 2024-01-02)
- Correction low: `None` (none)
- Fib mode: `RETRACEMENT`; backend levels: `3`.
  - `RETRACEMENT 0.382` = `2.402180 USD` from `price-pivot:8d3d8b709ee4d89fa81e` / `price-pivot:77cdf1e2cd278940f77d`; `H - (H-L) * ratio`.
  - `RETRACEMENT 0.500` = `2.165000 USD` from `price-pivot:8d3d8b709ee4d89fa81e` / `price-pivot:77cdf1e2cd278940f77d`; `H - (H-L) * ratio`.
  - `RETRACEMENT 0.618` = `1.927820 USD` from `price-pivot:8d3d8b709ee4d89fa81e` / `price-pivot:77cdf1e2cd278940f77d`; `H - (H-L) * ratio`.
- Value-gated render refs: none.

#### Daily

- Status: `SELECTED`; role: `NEAREST_TACTICAL_ZONE`; regime: `ABOVE_CONFIRMED_SWING_HIGH`; confidence: `high`.
- Support: `price-zone:098012127b7eccc27505` (15.552386–16.461814, Medium)
- Resistance: `price-zone:d4bcd07acc8b76f5bb5a` (17.323652–18.121348, Medium)
- Low anchor: `price-pivot:479c68d680d02fa01a58` (2025-07-07 / 4.52; confirmed 2025-08-14)
- High anchor: `price-pivot:edf44bd21dd0cbc2bbcd` (2025-08-18 / 10.7099; confirmed 2025-08-19)
- Correction low: `None` (none)
- Fib mode: `RETRACEMENT`; backend levels: `3`.
  - `RETRACEMENT 0.382` = `8.345358 USD` from `price-pivot:479c68d680d02fa01a58` / `price-pivot:edf44bd21dd0cbc2bbcd`; `H - (H-L) * ratio`.
  - `RETRACEMENT 0.500` = `7.614950 USD` from `price-pivot:479c68d680d02fa01a58` / `price-pivot:edf44bd21dd0cbc2bbcd`; `H - (H-L) * ratio`.
  - `RETRACEMENT 0.618` = `6.884542 USD` from `price-pivot:479c68d680d02fa01a58` / `price-pivot:edf44bd21dd0cbc2bbcd`; `H - (H-L) * ratio`.
- Value-gated render refs: none.

### Multi-Timeframe Confluence

- None.

### Exact Shadow Render

```text
월봉(구조): 확정 스윙 범위 안의 되돌림
주봉(중기): 확정 스윙 고점 상회
일봉(전술): 확정 스윙 고점 상회; 현재 구간 15.552386-16.461814; 저항 17.323652-18.121348
종합: 독립 시간축 근거의 유의미한 가격 중첩은 확인되지 않았습니다.
```

Validation: `True`; human classification: `NO_ADDED_VALUE`; render length: `153` characters.
