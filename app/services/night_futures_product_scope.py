"""Product scope shared by acquisition, replay, consumption, and display."""

CONTRACT = "configured-night-product-scope-v1"
PRODUCTS = ("KOSPI200",)
SERIES_CODES = {product: f"KRX_{product}_NIGHT_FUT" for product in PRODUCTS}
SERIES = tuple(SERIES_CODES.values())
LABELS = {series: f"{product} 최근월물" for product, series in SERIES_CODES.items()}
FACT_IDS = {SERIES_CODES["KOSPI200"]: "market:night_futures:1"}


def complete_series(observations):
    values = [getattr(row, "series_code", None) for row in observations]
    return len(values) == len(SERIES) and set(values) == set(SERIES)


def scope_receipt():
    return {"contract": CONTRACT, "products": list(PRODUCTS), "series": list(SERIES)}
