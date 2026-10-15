"""Versioned, explicit *estimated* token-rate registry. USD per million tokens."""
from decimal import Decimal
import os

VERSION = "2026-10-15"
# Rates correspond to the standard Anthropic API, without batch / cache discounts.
# Jev rate is supplied by the operator: no automatic verified price available.
RATES = {
    "claude-haiku-4-5": ("1", "5", "https://www.anthropic.com/news/claude-haiku-4-5"),
    "claude-haiku-4-5-20251001": ("1", "5", "https://www.anthropic.com/news/claude-haiku-4-5"),
    "claude-sonnet-4-5": ("3", "15", "https://www.anthropic.com/news/claude-sonnet-4-5"),
    "claude-sonnet-4-5-20250929": ("3", "15", "https://www.anthropic.com/news/claude-sonnet-4-5"),
}

def _nonnegative(value):
    try:
        number = int(value)
        return number if number >= 0 else None
    except (TypeError, ValueError, OverflowError):
        return None

def _usage_counts(usage):
    if not isinstance(usage, dict):
        return None
    inp = _nonnegative(usage.get("input_tokens"))
    out = _nonnegative(usage.get("output_tokens"))
    return (inp, out) if inp is not None and out is not None else None

def estimate(provider, model, usage):
    """Null cost means unpriced or missing usage, never zero-cost."""
    counts = _usage_counts(usage)
    if counts is None:
        return {"estimatedCostUsd": None, "costPer1000Usd": None, "pricingStatus": "missing_usage", "pricingVersion": VERSION}
    if provider == "jev":
        configured = os.getenv("JEV_INPUT_USD_PER_MTOK", "").strip()
        if not configured:
            return {"estimatedCostUsd": None, "costPer1000Usd": None, "pricingStatus": "rate_not_configured", "pricingVersion": VERSION}
        try:
            rate_in = Decimal(configured)
            if not rate_in.is_finite() or rate_in < 0:
                raise ValueError
        except Exception:
            return {"estimatedCostUsd": None, "costPer1000Usd": None, "pricingStatus": "invalid_rate", "pricingVersion": VERSION}
        rate_out = Decimal("0")
        source = "operator-configured"
    elif model in RATES:
        i, o, source = RATES[model]
        rate_in, rate_out = Decimal(i), Decimal(o)
    else:
        return {"estimatedCostUsd": None, "costPer1000Usd": None, "pricingStatus": "unknown_model", "pricingVersion": VERSION}
    cost = (Decimal(counts[0]) * rate_in + Decimal(counts[1]) * rate_out) / Decimal(1_000_000)
    return {"estimatedCostUsd": float(cost), "costPer1000Usd": float(cost * 1000),
            "pricingStatus": "estimated", "pricingVersion": VERSION,
            "pricingSource": source,
            "ratesUsdPerMillion": {"input": float(rate_in), "output": float(rate_out)}}
