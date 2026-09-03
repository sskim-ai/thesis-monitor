# Korean Price-Subject Detector Contract

Recognized subjects are standalone `주가`/`종가` plus explicit current/day/session compounds. Each subject starts at a valid non-Hangul boundary, accepts bounded Korean particles, and must be followed by a nearby technical action (`돌파`, `상회`, `하회`, `회복`, `안착`, `재지지`, `이탈`, `붕괴`). Explicit support/resistance/confirmation nouns and the existing English patterns remain independently blocked.

Business fixtures: `17/17`. Technical fixtures: `21/21`.
