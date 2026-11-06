# C12: typed pending completed-close capture

The old chart Source Parent is unchanged. A new, default-OFF
`issue_completed_close_parent` accepts only the original US14 price selection,
with no chart reads, one mandatory auth slot and 14 mandatory usa20590 slots.
The original compiler binds explicit registered venues; this selection has no
usa10099 discovery dependencies. The separate US Market graph still has its
original exchange-discovery parents. No receipt or optional slot is rewritten.

The versioned scope is `SCOPED_COMPLETED_CLOSE_ONLY_PENDING`, not ACTIVE,
technical, Financial, valuation, economic-direction or Native authority.
Issue and every state read consume the original per-security completed_close
intake, original session and code pins. STOP, expiry, PID, single dispatch,
authenticated Worker handoff, exact wire and physical budget remain enforced.
The original close validator and public field-documentation SHA are unchanged.

The Worker binds its internal command validator before replacing the app module
namespace with the pinned external Owner namespace. The launch helper has an
explicit completed-close profile; it does not masquerade as a Market window or
identity-only profile. The immutable public documentation fixture was restored
byte-for-byte from retained source, not regenerated from synthetic responses.

## Evidence and limits

- 26 distinct focused cases passed across retained runs: 25 contract cases and
  one actual OS-isolated Worker / MockTransport integration. Earlier failed
  runs remain in the result. Duplicate executions are not counted as new tests.
- One live read-only registration capture: one session, five SELECT, no writes.
- One live campaign: 15 physical Kiwoom attempts, retries zero, all HTTP 200.
- Original Owners qualified 13 of 14 closes for 2026-11-05. IBM was denied by
  original source quality (`LOW_GT_CLOSE`). Its response was not repaired or
  re-requested. A separate process exactly replayed all 14 outcomes.
- The successful close-only contract is not a 14/14 live campaign PASS.
- The KR original 42-request resolver trace preserves parent-before-child
  ordering. Resolving KOSPI continuation 16 without a persisted continuation 15
  reproduces `binding_parent_not_executed`; the absent original stack and
  dispatcher snapshot prevent attribution to the actual failed runtime caller.
  No speculative KR resolver patch or fresh KR HTTP was performed.
- Full Market Parents remain 0/2; Strict READY remains 0/22. Existing C10R and
  C11 evidence is historical, not reissued as unexpired C12 authority.

No investment model, scheduling, deployment, send, order or source deletion.
All live capture and private registration material stays outside Git/results.
