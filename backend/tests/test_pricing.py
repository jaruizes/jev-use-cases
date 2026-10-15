from app.pricing import change_price, estimate, list_prices

def test_default_rates(tmp_path, monkeypatch):
    monkeypatch.setattr("app.pricing.DB_PATH", tmp_path / "rates.sqlite3")
    rates = {x["provider"]:x for x in list_prices()}
    assert rates["jev"]["inputUsdPerMillion"] == 0.042
    assert rates["haiku"]["model"] == "claude-haiku-5-5"
    assert rates["sonnet"]["model"] == "claude-sonnet-5-5"
    assert estimate("haiku", "claude-haiku-5-5", {"input_tokens":1000,"output_tokens":100})["estimatedCostUsd"] == 0.00015

def test_edit_persists_and_affects_cost(tmp_path, monkeypatch):
    monkeypatch.setattr("app.pricing.DB_PATH", tmp_path / "rates.sqlite3")
    change_price("haiku", "0.20", "1.0")
    assert next(x for x in list_prices() if x["provider"] == "haiku")["inputUsdPerMillion"] == 0.2
    assert estimate("haiku", "claude-haiku-5-5", {"input_tokens":1000,"output_tokens":100})["estimatedCostUsd"] == 0.0003

def test_haiku_long_prompt_rate(tmp_path, monkeypatch):
    monkeypatch.setattr("app.pricing.DB_PATH", tmp_path / "rates.sqlite3")
    result = estimate("haiku", "claude-haiku-5-5", {"input_tokens":100001,"output_tokens":10})
    assert result["ratesUsdPerMillion"] == {"input":0.5,"output":2.5}
