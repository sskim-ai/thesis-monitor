# Main and Operating Lineage

The promotion candidate started from main and operating SHA `906b092749511dc42d5799ed335165819efee2ea`. The complete implementation through `03e230da22c1482339b4bb7b1c1883ce0ac01076` is a linear descendant and passes branch Actions run `33949330754`.

Promotion closed at runtime/report SHA `f031d72af76b408b90b1c9695a7143aeafad4c97`:

- documentation exact-SHA Actions: `33949976793 PASS`;
- main exact-SHA Actions: `33950260247 PASS`;
- main merge: clean linear fast-forward complete;
- operating synchronization: complete at the same SHA;
- API restart: complete for `com.seungsoo.thesis-monitor`;
- API health: `PASS`;
- scheduler definitions and recipients: unchanged;
- production Telegram resend: prohibited.

The post-promotion closure commit changes documentation and its assertion only. Runtime identity remains the promoted `f031d72` SHA; natural KR/US proof remains independently pending.
