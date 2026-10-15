from types import SimpleNamespace
import pytest
from app.catalog import BY_ID
from app.providers.claude import decision_schema, extract_decision

def response(payload):
    return SimpleNamespace(content=[
        SimpleNamespace(type="tool_use", name="submit_decision", input=payload)
    ])

@pytest.mark.parametrize("case_id,expected", [
    ("model-routing", "SONNET"),
    ("lead-scoring", 4),
    ("semantic-guardrails", 0.8),
])
def test_extract_valid_decision(case_id, expected):
    value, raw = extract_decision(response({"value": expected}), BY_ID[case_id])
    assert value == expected
    assert raw == {"value": expected}

@pytest.mark.parametrize("case_id,invalid", [
    ("model-routing", "INVALID"),
    ("lead-scoring", 9),
    ("lead-scoring", "4"),
    ("semantic-guardrails", 1.5),
    ("semantic-guardrails", True),
])
def test_reject_invalid_decision(case_id, invalid):
    with pytest.raises(ValueError):
        extract_decision(response({"value": invalid}), BY_ID[case_id])

def test_schema_has_strict_choice_enum():
    schema = decision_schema(BY_ID["model-routing"])["input_schema"]
    assert "SONNET" in schema["properties"]["value"]["enum"]
    assert schema["additionalProperties"] is False

def test_reject_missing_tool_call():
    with pytest.raises(ValueError):
        extract_decision(SimpleNamespace(content=[]), BY_ID["model-routing"])
