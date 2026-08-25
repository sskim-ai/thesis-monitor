# Free Analyst Production Port Manifest

- Instruction commit: `3df40de53cf35ff5c47d662e0a14fbf9e30be3f7`
- Implementation base: `f7d2552185ff2ff6d932337e7555ce02f87fa613`
- US packet: `2026-08-25-us-run-37-7e04812311c2`
- KR packet: `2026-08-24-kr-run-36-e4ac1c029c06`
- Provider recollection: `0`
- Manual Telegram / Task / DB mutation: `0 / 0 / 0`

## Proven sources

- Evidence-Locked Free Analyst: `aad3041affd2036bc265e35d3ec1fe55ef97262b`
- Adaptive Renderer: `5e30b17bf1fa10acb5483bfb6961b2a6d6fc8a86`
- Natural packet adapter: `d70313991c3cd2e4b4e54200aedb612ec772bcb6`

## Production units

- `free_analyst_message_service.py`
- `evidence_locked_free_analyst_service.py`
- `free_analyst_natural_packet_adapter_service.py`
- `adaptive_renderer_selector_service.py`
- `free_analyst_production_integration_service.py`
- bounded wiring in `ai_assisted_delivery_service.py`

Open Research, Event Attribution, benchmark artifacts, and shadow runners were not ported.
