#!/usr/bin/env python3
import json
import sys

p = sys.argv[1] if len(sys.argv) > 1 else "SK하이닉스_structure_analysis_auto.json"
r = json.load(open(p, encoding="utf-8"))
h = r["selected_impulse"]

expected = {
    "wave0": ("2023-01-02", 73100.0),
    "wave1": ("2024-07-01", 248500.0),
    "wave2": ("2024-09-02", 144700.0),
    "wave3": ("2026-06-01", 2987000.0),
    "wave4": ("2026-07-01", 1246000.0),
}

for k, (date, price) in expected.items():
    got = h[k]
    assert got["date"] == date, (k, got["date"], date)
    assert abs(got["price"] - price) < 1e-9, (k, got["price"], price)

assert h["wave5"] is None
assert h["status"] == "W4_CANDIDATE_W5_UNCONFIRMED"

print("SK Hynix regression: PASS")
