import pytest
from app.pricing import estimate

def test_haiku_cost():
    result = estimate("haiku", "claude-haiku-4-5", {"input_tokens": 1000, "output_tokens": 100})
    assert result["estimatedCostUsd"] == pytest.approx(0.0015)
    assert result["costPer1000Usd"] == pytest.approx(1.5)

def test_sonnet_cost():
    result = estimate("sonnet", "claude-sonnet-4-5", {"input_tokens": 1000, "output_tokens": 100})
    assert result["estimatedCostUsd"] == pytest.approx(0.0045)

def test_unrecognized_model_is_not_zero():
    assert estimate("haiku", "model-unknown", {"input_tokens": 1000, "output_tokens": 5})["estimatedCostUsd"] is None

def test_missing_usage_is_not_zero():
    assert estimate("haiku", "claude-haiku-4-5", None)["pricingStatus"] == "missing_usage"

def test_jev_custom_rate(monkeypatch):
    monkeypatch.setenv("JEV_INPUT_USD_PER_MTOK", "0.042")
    result = estimate("jev", "jev-latest", {"input_tokens": 1000, "output_tokens": 20})
    assert result["estimatedCostUsd"] == pytest.approx(0.000042)
    assert result["pricingSource"] == "operator-configured"

def test_jev_published_default(monkeypatch):
    monkeypatch.delenv("JEV_INPUT_USD_PER_MTOK", raising=False)
    result = estimate("jev", "jev-latest", {"input_tokens": 1000})
    assert result["estimatedCostUsd"] == pytest.approx(0.000042)
    assert "typesafe.ai/blog/" in result["pricingSource"]

def test_jev_override(monkeypatch):
    monkeypatch.setenv("JEV_INPUT_USD_PER_MTOK", "0.05")
    result = estimate("jev", "jev-latest", {"input_tokens": 1000, "output_tokens": 0})
    assert result["estimatedCostUsd"] == pytest.approx(0.00005)

def test_jev_invalid_override(monkeypatch):
    monkeypatch.setenv("JEV_INPUT_USD_PER_MTOK", "not-a-price")
    assert estimate("jev", "jev-latest", {"input_tokens": 1000})["pricingStatus"] == "invalid_rate"

def test_reject_negative_usage():
    assert estimate("haiku", "claude-haiku-4-5", {"input_tokens": -1, "output_tokens": 10})["pricingStatus"] == "missing_usage"

def test_jev_default_returns_complete_cost_metadata(monkeypatch):
    """Regression: price source must be a declared variable, not part of a comment."""
    monkeypatch.delenv("JEV_INPUT_USD_PER_MTOK", raising=False)
    result = estimate("jev", "jev-latest", {"input_tokens": 413, "output_tokens": 53})
    assert result["pricingStatus"] == "estimated"
    assert result["estimatedCostUsd"] == pytest.approx(413 * 0.042 / 1_000_000)
    assert result["pricingSource"] == "https://typesafe.ai/blog/introducing-system-one-models-and-jev"
