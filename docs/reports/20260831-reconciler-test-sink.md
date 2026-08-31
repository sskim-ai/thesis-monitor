# Reconciler Test Sink

The pre-main test used a SQLite operating snapshot and the dedicated non-production sink. The initial pass sent 20 exact payloads; identity-aware continuation sent only the remaining 2.

Final: planned `22`, sent `22`, exact payload `PASS`, duplicate `0`, orphan `0`, production collision `0`, production recipient send `0`, production delivery intent `0`.

Message artifact SHA-256: `429f17e04840006a632954882a3ddc1bfc29ff5784e1e3585d8d0d43e1b57a67`. Raw recipient values, message identifiers, tokens, and auth data are excluded.
