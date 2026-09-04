# Track B — Korean Compound Regression Corpus

Expand deterministic regression fixtures.

Business MUST PASS:
- exact 047810 prior sentence
- 수주가/발주가 compounds
- 최종가격/제품가격/판매가격/평균판매가격
- prior CRCL and MU fixtures

Technical MUST FAIL:
- 주가가 확인선 돌파
- 현재주가 저항 회복
- 정규장종가 안착
- 전일종가 하회
- 지지선/저항선/확인선 explicit structures
- existing English technical fixtures

Test spaced and unspaced forms.
