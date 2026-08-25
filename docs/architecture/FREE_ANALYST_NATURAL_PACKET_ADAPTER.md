# Free Analyst Natural Packet Adapter

## Status

`free-analyst-natural-packet-adapter-shadow-v1` is shadow-only. It is not
imported by production runtime modules and does not change delivery, Telegram,
scheduled tasks, Production Assist, or the Public Action contract.

## Boundary

The adapter converts the persisted US natural production message shape into
the common rendered-message semantics already consumed by Evidence-Locked Free
Analyst:

```text
US natural production message
  -> heading/section normalization
  -> common evidence section namespace
  -> existing Evidence-Locked Free Analyst
  -> existing Adaptive Renderer
```

It normalizes shape only. It does not add facts, perform arithmetic, infer
missing context, change temporal roles, or rewrite financial conclusions.

## Current Mappings

The 2026-08-25 natural fallback used two headings that the common parser did
not classify under the intended semantic keys:

| Production heading | Common heading | Semantic key |
| --- | --- | --- |
| `🎯 핵심` | `🎯 핵심 판단` | `core` |
| `📅 오늘/근접 일정` | `📌 다음 확인` | `next_check` |

All non-heading lines remain byte-equivalent in order and content. The adapter
stores original and normalized SHA-256 values and fails if the content
fingerprint changes.

## Evidence References

Every normalized metadata or section atom gets a deterministic map:

```text
natural-message:<original-sha>:<section>:<ordinal>
  -> evidence:<section>:<ordinal>
```

The map is validated for completeness, collisions, and exact section-body
hashes before Free Analyst runs. A missing or altered map fails closed. Open
Research remains a separate immutable sidecar and is attached after this
common Free Analyst stage by the existing research shadow service; source,
entity, event-time, causal-time, negative-evidence, and hypothesis identities
are not rewritten by this adapter.

## Isolation

The pure adapter entry point is `normalize_us_natural_packet`. Archive-only
orchestration validates its result, passes `normalized_text` to the existing
Adaptive Renderer, and retains `original_text` as the deterministic fallback
reference. The adapter does not import the renderer, and no production module
imports the adapter. Promotion requires a separate integration instruction.
