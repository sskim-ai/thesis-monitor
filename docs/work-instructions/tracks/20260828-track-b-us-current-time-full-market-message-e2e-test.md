# Track B — US Current-Time Full Market Message E2E Test

At actual execution time:

1. resolve latest completed US session
2. resolve expected Korean overnight-futures session
3. collect SPY/QQQ/IWM/SOXX/RSP
4. collect RSP/sector dispersion
5. run repaired night-futures canonical gate
6. collect temporal-safe macro
7. render AI + fallback
8. send one current message to dedicated test sink
9. if current night futures unavailable, optionally send one clearly labeled real historical positive fixture
10. verify exact received payload and readability

Never force unavailable night futures into the current message.
