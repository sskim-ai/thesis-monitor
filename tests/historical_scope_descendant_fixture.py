"""Exact REV63D drift evidence, not an exemption from the M12U scope freeze."""
from hashlib import sha256
from pathlib import Path

REV63D_CONTROL_SHA256 = "756c46bbe5e50d09603578ba9b3edcf7ac7e5aa55dfc307b0394c5811e4074c4"
CALENDAR_PATH = "app/services/price_structure_wave_fibonacci_v3_service.py"
CALENDAR_SHA256 = "fcb9d0c799628af9ae53855238f07dd28d8f9542cdb8ff0a3f3e5ab821d4fd78"


def require_exact_calendar_descendant(body=None):
    if body is None:
        body = (Path(__file__).resolve().parents[1] / CALENDAR_PATH).read_bytes()
    assert sha256(body).hexdigest() == CALENDAR_SHA256, "unreviewed_calendar_descendant"
