# Decision Evidence Packet

Contract: `decision-evidence-packet-v1`.

Each stock packet preserves identity, thesis, earnings, earnings quality, expectations, valuation, catalysts/risks, macro, market, flows, price structure, technical features, quality cautions, and unknowns. Every item has an opaque evidence ref and as-of/source reference.

The AI receives canonical facts and backend-calculated features, not raw XBRL or an instruction to calculate indicators. Final prose is selective: evidence omitted by materiality is not a failure, while every selected ref must exist in the same ticker packet.
