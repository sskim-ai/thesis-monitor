# C21R Native technical input

The current OhlcvClient requests provider-native indicators with collection
ceilings daily 1000, weekly 700, monthly 300. These are not admission minima.
Local Pivot windows remain daily 300, weekly 120, monthly 60. Existing structural
algorithms are reused; the native path does not recalculate the 38 indicators.

Path: /ohlcv -> physical response hash + normalized row hashes -> versioned
native projection -> packet-owned native context -> compact typed decision
input -> existing S/R renderer -> dated NO-SEND reference.

Native RSI is rolling-simple, not Wilder. MACD uses provider EMA semantics.
Native Bollinger values are not mixed into legacy Bollinger confluence scores.
Missing values remain null; long-window warmup is not inferred from a value.
Invalid identity, adjusted basis, row content, or mixed captures reject the
affected period without granting authority to another period.

The default weekly/monthly completion registry remains unproven and therefore
unavailable. Synthetic tests inject a trusted fixture-only completion verifier;
no production registry or configuration is installed by these tests.

This projection permits only dated technical analysis. It does not issue
current-price, financial, economic-direction, Stage, or Strict Native authority.
The existing KR/US rollout configuration remains OFF. Historical V1 calculators,
old receipts and consumed Parent state are preserved, not promoted or rewritten.

Offline tests exercise MockTransport -> actual client -> typed prompt -> existing
S/R renderer. No deployed service, financial API, model, DB, or scheduler was
invoked. A live run needs independently verified service/code identity, source
Parent and account/Lane budget, and original completion-label authority.
