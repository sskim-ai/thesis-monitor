# Phase 8.3 US Peer Valuation Preview

Immutable 2026-08-18 final assessments using the completed 2026-08-17 XNYS price session. Read-only
archive audit; Telegram sends: 0.

## Result

No mandatory US fixture has a `MEDIUM` or `HIGH` eligible peer distribution. The point-in-time fix
correctly compares the 2026-08-17 exchange session rather than the KST assessment date, but exact
taxonomy, issuer, denominator and depositary-basis gates still suppress every user-facing peer Fact.

| Ticker | Role | Candidate result | Phase 8.3 peer Fact | Message-length delta |
|---|---|---|---|---:|
| MU | memory/semiconductor | technology sector fallback only; LOW | suppressed | 0 |
| TSM | foundry/depositary | P/E/PBR security basis unsafe | suppressed | 0 |
| TSLA | automotive | fewer than 3 comparable issuers | suppressed | 0 |
| RXRX | biotech negative control | generic PER/PBR peer comparison not meaningful | suppressed | 0 |
| CORZ | HPC/crypto representative | negative EPS and negative equity | suppressed | 0 |
| GOOGL | general representative | technology sector fallback only; LOW | suppressed | 0 |

## Before / After

### MU

**BEFORE - Phase 8.5.3.2 operating baseline**

> ASP·HBM 믹스와 FCF의 배수 관계에서 현재 PER 20.68배; 시장 예상 fPER 5.87배. 후행·선행
> 이익 배수 관계에서 선행 배수는 더 낮습니다. 이는 이익 확대 기대를 담지만 메모리 피크
> 이익과 공급 확대 위험은 별도 검증해야 합니다.

**AFTER - Phase 8.3 experimental preview**

Unchanged. A mixed technology-sector sample is not labeled as a memory peer median.

### TSM

**BEFORE**

> 현재 미국 상장 증권의 identity와 주당 이익 분모가 확인되지 않아 PER 해석은 보류합니다.
> 현재 미국 상장 증권의 장부 주당 분모도 확인되지 않아 PBR 해석은 보류합니다.

**AFTER**

Unchanged. Peer availability cannot repair the subject's unsafe depositary denominator.

### TSLA

**BEFORE**

> 자동차 마진과 Robotaxi 단위경제성의 배수 관계에서 현재 PER 176.72배; 시장 예상 fPER
> 145.9배. 후행·선행 이익 배수 관계에서 선행 배수는 더 낮습니다. 이는 이익 확대 기대를
> 담지만 자동차 마진과 Robotaxi 실행이 부족하면 압축 위험이 남습니다. PER 역사적 백분위
> 95.9%입니다. 이는 현재 PER이 비교 가능한 과거 관측치 대부분보다 높은 구간이라는 뜻입니다.

**AFTER**

Unchanged. No unrelated consumer-discretionary median is added.

### RXRX

**BEFORE**

> 임상 milestone과 cash runway의 배수 관계에서 현재 PBR 1.82배; 역사적 PBR 중앙값 3.28배;
> PBR 역사적 백분위 9.5%. 현재 PBR은 비교 가능한 과거 관측치 대부분보다 낮은 구간이지만,
> cash runway·희석·임상 성공확률을 대신하지 않습니다.

**AFTER**

Unchanged. Phase 8.3 marks generic biotech PER/PBR peer valuation as not economically meaningful;
cash runway, milestone probability and dilution remain primary.

### CORZ / GOOGL Controls

CORZ's finance-services candidate group does not create a usable distribution: the subject has
negative EPS and negative equity. GOOGL reaches only a broad technology-sector fallback containing
semiconductor, storage and office-equipment issuers; the resulting audit statistic is `LOW` and is
not emitted. Neither control adds a user-visible peer line.

## Forward Basis

Consensus and modeled forward PER distributions are built separately. A `consensus_forward` row can
never enter `forward_pe_modeled`, and vice versa. The current active universe has raw forward values,
but no safe three-issuer group, so forward peer Facts remain unavailable.

## Human Review

- New decision information: none was safely available, so none was printed.
- Point-in-time session: 2026-08-17 XNYS, not the 2026-08-18 KST assessment label.
- Sector sample misrepresented as peer industry: 0.
- ADR/share-basis leakage: 0.
- Biotech PER attractiveness claims: 0.
- Peer discount/premium used as automatic verdict: 0.
- Message expansion: 0 characters for selected valuation blocks.

Human quality: `PASS_FAIL_CLOSED`; data capability remains `STRONG PARTIAL`.

