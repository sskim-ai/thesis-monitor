# Release-Equivalent Model and Effort

The current operating source and Run-57 CLI log both resolve:

```text
model = gpt-5.6-sol
reasoning_effort = xhigh
```

The work instruction carried an older note that production might still be `high`; current repository constants and immutable operating evidence supersede it. Release-equivalent KR and US E2E therefore use the exact operating pair `gpt-5.6-sol / xhigh`. There is no silent GPT-5.5 fallback and no model/effort configuration mutation in this change set.
