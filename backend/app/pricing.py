"""Editable USD-per-million-token pricing registry. Local SQLite persistence."""
import os
import sqlite3
from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation
from pathlib import Path

DB_PATH = Path(os.getenv("PRICING_DB_PATH", "/app/data/pricing.sqlite3"))
DEFAULTS = [
    ("jev", "jev-latest", "0.042", "0", "https://typesafe.ai/blog/introducing-system-one-models-and-jev"),
    ("haiku", "claude-haiku-5-5", "0.10", "0.50", "https://www.anthropic.com/claude/haiku"),
    ("sonnet", "claude-sonnet-5-5", "2", "10", "https://www.anthropic.com/claude/sonnet"),
]
LEGACY = {
    "claude-haiku-4-5": ("1", "5"),
    "claude-haiku-4-5-20251001": ("1", "5"),
    "claude-sonnet-4-5": ("3", "15"),
    "claude-sonnet-4-5-20250929": ("3", "15"),
}

def _connect():
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH, timeout=10)
    conn.execute("""CREATE TABLE IF NOT EXISTS prices (
      provider TEXT PRIMARY KEY, model TEXT NOT NULL, input_rate TEXT NOT NULL,
      output_rate TEXT NOT NULL, source TEXT NOT NULL, updated_at TEXT NOT NULL)""")
    return conn

def list_prices():
    with _connect() as conn:
        now = datetime.now(timezone.utc).isoformat()
        for provider, model, input_rate, output_rate, source in DEFAULTS:
            conn.execute("INSERT OR IGNORE INTO prices VALUES (?,?,?,?,?,?)",
                         (provider, model, input_rate, output_rate, source, now))
        rows = conn.execute("SELECT provider, model, input_rate, output_rate, source, updated_at FROM prices ORDER BY CASE provider WHEN 'jev' THEN 0 WHEN 'haiku' THEN 1 ELSE 2 END").fetchall()
    return [{"provider": p, "model": m, "inputUsdPerMillion": float(i),
             "outputUsdPerMillion": float(o), "source": s, "updatedAt": dt} for p,m,i,o,s,dt in rows]

def change_price(provider, input_rate, output_rate):
    if provider not in ("jev", "haiku", "sonnet"):
        raise ValueError("Unknown provider")
    def valid(value):
        try:
            number = Decimal(str(value))
        except (InvalidOperation, ValueError):
            raise ValueError("Invalid rate")
        if not number.is_finite() or number < 0 or number > 100000:
            raise ValueError("Rate must be finite and between 0 and 100000")
        return str(number)
    inp, out = valid(input_rate), valid(output_rate)
    list_prices()
    with _connect() as conn:
        conn.execute("UPDATE prices SET input_rate=?, output_rate=?, source=?, updated_at=? WHERE provider=?",
                     (inp, out, "user-configured", datetime.now(timezone.utc).isoformat(), provider))
    return next(p for p in list_prices() if p["provider"] == provider)

def estimate(provider, model, usage):
    base = {"estimatedCostUsd": None, "costPer1000Usd": None,
            "pricingStatus": "missing_usage", "pricingVersion": None}
    if not isinstance(usage, dict):
        return base
    try:
        inp = int(usage["input_tokens"])
        out = int(usage.get("output_tokens", 0))
        if inp < 0 or out < 0:
            return base
    except (ValueError, TypeError, KeyError, OverflowError):
        return base
    configured = next((p for p in list_prices() if p["provider"] == provider), None)
    if configured is None:
        return {**base, "pricingStatus": "unknown_provider"}
    input_rate, output_rate = Decimal(str(configured["inputUsdPerMillion"])), Decimal(str(configured["outputUsdPerMillion"]))
    source = configured["source"]
    # Always price by the actual model returned by the provider; don't silently apply a 5.5 price to 4.5.
    if provider != "jev" and model != configured["model"]:
        if model not in LEGACY:
            return {**base, "pricingStatus": "unknown_model"}
        input_rate, output_rate = map(Decimal, LEGACY[model])
        source = "legacy-price-table"
    # Haiku 5.5 has a different rate for prompts over 100k tokens.
    if provider == "haiku" and model == "claude-haiku-5-5" and inp > 100000 and source != "user-configured":
        input_rate, output_rate = Decimal("0.50"), Decimal("2.50")
        source = "https://www.anthropic.com/claude/haiku (over 100k)"
    cost = (Decimal(inp) * input_rate + Decimal(out) * output_rate) / Decimal(1_000_000)
    return {"estimatedCostUsd": float(cost), "costPer1000Usd": float(cost * 1000),
            "pricingStatus": "estimated", "pricingVersion": configured["updatedAt"],
            "pricingSource": source,
            "ratesUsdPerMillion": {"input": float(input_rate), "output": float(output_rate)}}
