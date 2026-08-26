# SK hynix Price Structure v3 Pre-Enablement Regression

SK_HYNIX_FAMILY_LEVEL_PRICE_STRUCTURE = PASS

SK_HYNIX_STRUCTURAL_RESISTANCE_REGRESSION = PASS

## Before

```json
{
  "cross_timeframe": {
    "high": "1915785.936000",
    "low": "1869166.264000",
    "stability": "CONFLUENCE_PRICE_EQUIVALENT",
    "zone_id": "v3-zone:28c6ae16dafad0f7ff21"
  },
  "daily": {
    "high": "1915788.795250",
    "low": "1869163.404750",
    "stability": "CONFLUENCE_PRICE_EQUIVALENT",
    "zone_id": "v3-zone:b02ee6cc76a3415bf447"
  },
  "monthly": {
    "high": "1915788.795250",
    "low": "1869163.404750",
    "stability": "CONFLUENCE_PRICE_EQUIVALENT",
    "zone_id": "v3-zone:a653befe54b314be5ddf"
  },
  "weekly": {
    "high": "1915781.361200",
    "low": "1869170.838800",
    "stability": "CONFLUENCE_PRICE_EQUIVALENT",
    "zone_id": "v3-zone:ebcece473077b667bea0"
  }
}
```

## After

```json
{
  "monthly": {
    "low": "1869163.404750",
    "high": "1915788.795250",
    "zone_id": "v3-zone:a653befe54b314be5ddf",
    "display": "약 186.9만~191.6만원"
  },
  "weekly": {
    "low": "1869170.838800",
    "high": "1915781.361200",
    "zone_id": "v3-zone:ebcece473077b667bea0",
    "display": "약 186.9만~191.6만원"
  },
  "daily": {
    "low": "1869163.404750",
    "high": "1915788.795250",
    "zone_id": "v3-zone:b02ee6cc76a3415bf447",
    "display": "약 186.9만~191.6만원"
  },
  "cross_timeframe": {
    "low": "1869166.264000",
    "high": "1915785.936000",
    "zone_id": "v3-zone:28c6ae16dafad0f7ff21",
    "display": "약 186.9만~191.6만원"
  }
}
```
