# Main and Operating Lineage

The promotion candidate starts from main and operating SHA `906b092749511dc42d5799ed335165819efee2ea`. The complete implementation through `03e230da22c1482339b4bb7b1c1883ce0ac01076` is a linear descendant and passes branch Actions run `33949330754`.

At this report stage:

- main merge: pending the documentation exact-SHA gate;
- operating synchronization: pending main promotion;
- API restart: required after synchronization because production-imported validation/runtime modules changed;
- scheduler definitions and recipients: unchanged;
- production Telegram resend: prohibited.

The post-promotion closure updates persistent state with the promoted SHA, operating parity, health, and final Actions receipt. The final documentation SHA is resolved from Git at closure rather than self-embedded.
