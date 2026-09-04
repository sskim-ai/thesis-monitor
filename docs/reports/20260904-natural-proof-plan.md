# 2026-09-04 Natural Proof Plan

Observe only the next ordinary scheduled KR and US runs. Do not invoke a task manually and do not resend production messages.

KR PASS requires accepted market `1` plus stocks `8`, AI sent `9/9`, fallback `0`, duplicate `0`, orphan `0`, and no healthy-primary backup reclaim.

US PASS requires accepted market `1` plus stocks `14`, AI sent `15/15`, fallback `0`, duplicate `0`, TLS UnknownIssuer `0`, and no healthy-primary backup reclaim. A genuinely dead primary may be recovered once by the fenced backup.

Record the two market verdicts independently. Until both are clean, Structured Autonomy shadow/promotion review may continue, but production decision mutation stays disabled.
