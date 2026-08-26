# Codex 적용 가이드 — 범용 OHLCV 구조·Elliott·Fibonacci 엔진

## 1. 목표

이 엔진은 특정 종목 가격을 하드코딩하지 않는다.

입력:
- 일봉 CSV
- 주봉 CSV
- 월봉 CSV

필수 컬럼:
- `date`
- `open`
- `high`
- `low`
- `close`
- `volume`

선택 컬럼:
- `value`
- `VOLUME_RATIO_20`
- `RSI14`
- `MACD`
- `MACD_SIGNAL`
- `MACD_HIST`
- `BB_36_1.541_UPPER`
- `BB_60_1.541_UPPER`
- `BB_50_2.25_UPPER`
- `BB_144_1.541_UPPER`
- `BB_288_1.541_UPPER`
- `BB_300_3.33_UPPER`
- `supply_*`

출력:
1. 장기 cycle 시작점 후보
2. Elliott 1-2-3-4-5 또는 partial impulse
3. 각 파동의 확정/잠정 상태
4. Fibonacci retracement / rebound / W5 projection
5. 일·주·월봉 pivot
6. 지지/저항 zone
7. Bollinger/Fibonacci confluence zone
8. 박스권 후보
9. JSON 형태의 계산 근거

---

## 2. 가장 중요한 철학

### 하지 말 것

```text
Fibonacci 비율이 예쁘다
→ 그 가격을 파동 endpoint로 강제
```

### 해야 할 것

```text
raw OHLCV
→ confirmed/provisional pivot 후보 생성
→ Elliott hard rule로 불가능한 조합 제거
→ Fibonacci 적합도 점수
→ Bollinger/거래량/주봉 확인 점수
→ primary-degree 시간범위/진폭/최근성 점수
→ 상위 hypothesis 반환
```

즉:

```text
Pivot = endpoint 후보를 만든다.
Elliott hard rule = 잘못된 후보를 제거한다.
Fibonacci = 남은 후보의 적합도를 높이거나 낮춘다.
Bollinger/volume/MACD = 보조 신뢰도다.
후속 가격 행동 = wave3/wave4/wave5 최종 확정 조건이다.
```

어떤 종목도 억지로 1-2-3-4-5에 맞추지 않는다.

---

## 3. 시간축별 pivot / zone 기본값

```python
daily:
    zone lookback = 300
    pivot left/right = 3 / 3
    pivot price grouping = 1.75%
    zone cap = 6%
    box cap = 12%

weekly:
    zone lookback = 60
    pivot left/right = 2 / 2
    pivot price grouping = 2.25%
    zone cap = 8%
    box cap = 15%

monthly:
    zone lookback = 60
    pivot left/right = 2 / 2
    pivot price grouping = 3.0%
    zone cap = 12%
    box cap = 20%
```

변동성 종목의 pivot grouping 허용 폭:

```python
max(price * grouping_pct, ATR14 * 0.50)
```

최종 pivot zone padding:

```python
padding = min(ATR14 * 0.10, center_price * 0.01)

zone_low  = min(pivot_prices) - padding
zone_high = max(pivot_prices) + padding
```

---

## 4. Pivot 판정

### Pivot low

```python
low[i] < min(low[i-L:i])
and
low[i] <= min(low[i+1:i+R+1])
```

### Pivot high

```python
high[i] > max(high[i-L:i])
and
high[i] >= max(high[i+1:i+R+1])
```

### confirmed / provisional

필요한 우측 봉이 모두 완성됐으면:

```text
confirmed = true
```

최신 구간이라 우측 봉이 부족하거나 마지막 봉이 진행 중이면:

```text
confirmed = false
```

최신 wave3/wave4를 분석에서 버리지는 않되 score penalty를 준다.

---

## 5. 장기 cycle anchor 자동 선택

`--anchor-mode auto`에서는 최근 기본 8년의 월봉 confirmed pivot low를 후보로 만든다.

각 anchor마다 전체 impulse 후보를 실제로 생성한다.

그 뒤:

```text
impulse Elliott score
+ prior 24개월 저점에 가까운 major-base bonus
+ 8년 window 안에서의 mild recency bonus
```

로 순위를 매긴다.

중요:
- 자동 anchor는 하나의 절대 정답이 아니다.
- `auto_anchor_candidates`에 상위 5개를 함께 반환한다.
- degree가 애매한 종목은 후보 간 점수 차이가 작게 나온다.

사용자가 장기 시작점을 직접 주고 싶으면:

```bash
--anchor-mode hybrid \
--anchor-date 2023-01-02 \
--anchor-price 73100
```

`hybrid`는 사용자 anchor 분석을 우선하고 자동 후보도 같이 JSON에 남긴다.

---

## 6. 1파 후보 선택

W0 = 장기 cycle anchor.

W1 high 후보는 W0 이후 monthly pivot high.

Hard structure:

```python
W1.price > W0.price
```

추가로 W1 시점까지:

```python
max(high[W0:W1]) == W1.price
```

즉 W1보다 앞에 더 높은 고점이 이미 있었는데 그보다 낮은 나중 고점을 W1로 선택하는 것을 막는다.

---

## 7. 2파 후보 선택

W1 이후 monthly pivot low.

Hard rules:

```python
W0.price < W2.price < W1.price
```

그리고:

```python
min(low[W1:W2]) == W2.price
```

즉 W1 이후 이미 더 깊은 저점이 있었는데 나중의 higher-low를 W2 endpoint로 선택하지 않는다.

Retracement:

```python
R2 = (W1 - W2) / (W1 - W0)
```

허용:

```text
0.236 <= R2 <= 0.900
```

선호:

```text
0.500 <= R2 <= 0.618
```

선호 비율은 hard rule이 아니라 soft score다.

---

## 8. 3파 후보 선택

W2 이후 monthly pivot high.

Hard rules:

```python
W3 > W1
```

그리고:

```python
max(high[W2:W3]) == W3.price
```

길이:

```python
L1 = W1 - W0
L3 = W3 - W2
EXT3 = L3 / L1
```

최소:

```python
EXT3 >= 1.0
```

점수 보강:
- `>= 1.618`
- `>= 2.618` → extended
- `>= 4.236` → strongly extended

중요:
3파가 8배, 16배가 됐다고 invalid 처리하지 않는다.
표준 Fibonacci는 예측 reference이지 상한선이 아니다.

선택 지표 bonus:
- W3에서 `VOLUME_RATIO_20 >= 1.20`
- MACD histogram > 0
- 단·중기 Bollinger 상단 확장

이 지표들은 hard rule을 뒤집지 않는다.

---

## 9. 4파 후보 선택

W3 이후 monthly pivot low.

표준 상승 impulse hard rule:

```python
W1.price < W4.price < W3.price
```

즉 W4가 W1 고점 가격영역 아래로 내려가면 standard impulse hypothesis를 탈락시킨다.

또:

```python
min(low[W3:W4]) == W4.price
```

Retracement:

```python
R4 = (W3 - W4) / (W3 - W2)
```

허용:

```text
0.146 <= R4 <= 0.786
```

선호:

```text
0.236 <= R4 <= 0.500
```

0.618 부근의 깊은 4파는 가능하지만 soft score가 낮아질 수 있다.

최신 W4는 우측 봉이 충분하지 않으면 `confirmed=false`.

그리고 아직 W3 고점 돌파 W5가 없으면:

```text
status = W4_CANDIDATE_W5_UNCONFIRMED
```

로 유지한다.

---

## 10. 5파 후보

W4 이후 pivot high 중:

```python
W5.price > W3.price
```

를 standard non-truncated 5파 기본 조건으로 둔다.

그리고 세 파 길이:

```python
L1 = W1-W0
L3 = W3-W2
L5 = W5-W4
```

에서:

```python
L3 >= min(L1, L5)
```

즉 3파가 세 상승파 중 가장 짧아지는 조합은 탈락한다.

W5가 아직 없으면 절대 강제로 endpoint를 만들지 않고 projection만 계산한다.

---

## 11. W5 projection

다음 계산을 모두 만든 뒤 서로 2.5% 안에 모이는 가격을 cluster로 묶는다.

### W1 길이 기준

```text
W4 + W1*0.618
W4 + W1*1.000
W4 + W1*1.618
W4 + W1*2.618
```

### W3 길이 기준

```text
W4 + W3_length*0.382
W4 + W3_length*0.500
W4 + W3_length*0.618
W4 + W3_length*1.000
```

### W0→W3 전체 span 기준

```text
W4 + span03*0.500
W4 + span03*0.618
W4 + span03*1.000
```

독립 방법 여러 개가 같은 가격에 모일수록 projection strength가 높다.

---

## 12. Fibonacci 세트

선택된 hypothesis에서 네 종류를 별도 보관한다.

```text
wave1_retracement_prices
wave3_retracement_prices
primary_cycle_retracement_prices
current_rebound_prices
```

예를 들어 current rebound는:

```python
span = W3 - W4

rebound_382 = W4 + span*0.382
rebound_500 = W4 + span*0.500
rebound_618 = W4 + span*0.618
```

이 값이 실제 pivot 저항 또는 Bollinger 상단선과 겹치면 저항 strength를 높인다.

---

## 13. 지지/저항 zone

1. 같은 성격의 pivot들을 가격순으로 정렬
2. adaptive tolerance로 그룹화
3. ATR padding
4. Bollinger point anchor 추가
5. Fibonacci point anchor 추가
6. 가까운 독립 anchor를 confluence zone으로 merge
7. 현재가와 비교해서 role 분류

분류:

```python
if zone.high < current:
    SUPPORT

elif zone.low > current:
    RESISTANCE

else:
    CURRENT_ZONE
```

현재가를 미리 지지/저항 목록 맨 앞에 강제로 넣지 않는다.

---

## 14. Zone strength

현재 구현 기본 개념:

```text
pivot group     = 1.0 + 추가 pivot당 0.7
Bollinger       = 1.2
Fibonacci       = 1.4
독립 source 2종 이상 confluence = +1.0
다중 timeframe source = +0.5
confirmed pivot = 소폭 bonus
```

이 점수는 “매수 점수”가 아니다.

뜻은:

```text
그 가격대에 독립적인 기술 근거가 몇 개 겹치는가
```

이다.

---

## 15. 박스권

zone의 아무 두 가격을 박스로 잡지 않는다.

폭 제한:

```text
daily   <= 12%
weekly  <= 15%
monthly <= 20%
```

최근 체류율:

```text
daily: 최근 10봉
weekly: 최근 6봉
monthly: 최근 6봉
```

조건:

```text
close_inside_ratio >= 0.40
range_overlap_ratio >= 0.60  # monthly는 0.50
```

상단/하단 touch 여부도 score에 반영한다.

이 알고리즘은 실제 횡보 균형구간 `BALANCE_BOX`용이다.

장기 Fibonacci 두 선 사이 같은 넓은 회복 영역은 별도 `RECOVERY_BAND`로 다루는 편이 좋다.
현재 v1의 `detect_boxes()`는 BALANCE_BOX만 자동 생성한다.

---

## 16. 낮은 시간축 확인

장기 Elliott endpoint는 월봉에서 선택한다.

주봉 pivot이 월봉 endpoint와:
- 날짜 ±45일
- 가격 ±6%

안에 같은 종류(high/high 또는 low/low)로 있으면 confidence bonus.

이렇게 월봉의 과도하게 거친 pivot을 주봉으로 확인한다.

---

## 17. 진행 중 봉

기본값:

```text
assume_last_incomplete = true
```

따라서 최신 봉은 다음 pivot의 확정용 우측 봉으로 사용하지 않는다.

완성봉만 들어 있는 데이터라면:

```bash
--last-bar-complete
```

사용.

현재 월봉/주봉이 진행 중인데 이 옵션을 켜면 미래정보처럼 잘못 확정될 수 있으므로 주의.

---

## 18. 상태값 해석

```text
W4_CANDIDATE_W5_UNCONFIRMED
```

의미:
- W0-W1-W2-W3-W4 구조는 hard rule 통과
- W4는 provisional일 수 있음
- 아직 W3 신고가를 만드는 W5가 없음
- 현재 반등은 W5 시작 또는 W4 내부 B파일 수 있으므로 확정하지 않음

```text
W5_CANDIDATE
```

의미:
- W4 이후 W3 고점을 넘는 pivot high가 나옴
- 3파 최단 규칙 통과
- W5 projection과 거리로 추가 점수 부여
- 최종 확정 여부는 향후 reversal까지 별도 판단 가능

---

## 19. Codex가 결과를 글로 해석할 때의 규칙

반드시 구분:

```text
confirmed
provisional / candidate
projection
```

금지:

```text
W4 후보인데 "4파 확정"
projection인데 "5파 목표 확정"
Fibonacci가 맞아서 endpoint 확정
```

권장:

```text
월봉 hard rule은 통과했지만 최신 우측 확인봉이 부족해 W4 후보로 둔다.
W5는 전고점 돌파가 아직 없어 미확정이다.
```

---

## 20. 실행 명령

### 자동 anchor

```bash
python stock_structure_engine.py \
  --daily daily.csv \
  --weekly weekly.csv \
  --monthly monthly.csv \
  --anchor-mode auto \
  --out analysis.json
```

### 사용자 anchor 우선 + 자동 후보 비교

```bash
python stock_structure_engine.py \
  --daily daily.csv \
  --weekly weekly.csv \
  --monthly monthly.csv \
  --anchor-mode hybrid \
  --anchor-date 2023-01-02 \
  --anchor-price 73100 \
  --out analysis.json
```

---

## 21. SK하이닉스 회귀 테스트

현재 제공 데이터에서 `--anchor-mode auto`로 실행 시 엔진 v1.0.0은:

```text
W0  2023-01-02   73,100
W1  2024-07-01  248,500
W2  2024-09-02  144,700
W3  2026-06-01 2,987,000  provisional
W4  2026-07-01 1,246,000  provisional
W5  None
```

를 1순위 primary monthly hypothesis로 선택한다.

계산:

```text
W2 retracement of W1 = 0.59179
W3 / W1 extension    = 16.20468
W4 retracement of W3 = 0.61253
```

상태:

```text
W4_CANDIDATE_W5_UNCONFIRMED
```

따라서 현재 결과는 “W4가 확정되고 W5가 시작됐다”가 아니라:

```text
장기 impulse의 W4 후보까지는 매우 강한 hypothesis.
W5 전고점 돌파가 나오기 전까지 W4 내부 반등 가능성을 병존.
```

으로 해석한다.

---

## 22. 다른 종목에서 valid impulse가 없을 때

아무것도 억지로 반환하지 않는다.

가능한 출력:

```text
selected_impulse = null
auto_anchor_candidates = []
```

그래도:
- 일봉 zone
- 주봉 zone
- 월봉 zone
- Bollinger
- pivot
- 박스권

분석은 계속 가능하다.

이것이 “어떤 종목도 무조건 Elliott 5파로 끼워 맞추지 않는 것”보다 중요하다.

---

## 23. 현재 v1 범위와 향후 확장

현재 v1:
- 상승 standard impulse
- partial W4 / W5
- auto/user/hybrid anchor
- monthly primary degree
- weekly endpoint confirmation
- 일/주/월 zone
- Bollinger/Fibonacci confluence

향후 권장:
1. bearish impulse
2. leading / ending diagonal
3. ABC correction 내부 구조
4. nested intermediate/minor degree
5. wave alternation의 시간 비율
6. volume profile / traded-value weighted zone
7. gap / split / corporate action validation
8. 차트 renderer와 동일 zone 객체 공유

특히 3번 ABC와 4번 nested degree를 넣기 전에는 하나의 Elliott count를 절대적 정답처럼 쓰지 않는다.
