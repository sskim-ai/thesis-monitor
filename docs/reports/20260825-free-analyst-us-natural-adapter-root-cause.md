# Free Analyst US Natural Adapter Root Cause

Classification: `A. production packet field/section shape mismatch`.

All 14 natural messages preserved valid factual content. The stock fallback heading `🎯 핵심` was classified as `other`, so Free Analyst rules requiring `core + next_check` saw no core evidence. The market heading `📅 오늘/근접 일정` was not a recognized heading prefix and did not become `next_check`. This produced 14/14 `support_semantic_mismatch` fallback outcomes. Open Research sidecars independently passed 14/14.

No Free Analyst reasoning, research evidence, or renderer threshold defect was found.
