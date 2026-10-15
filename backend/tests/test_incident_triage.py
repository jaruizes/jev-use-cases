from types import SimpleNamespace
import pytest
from app.catalog import BY_ID
from app.providers.claude import decision_schema, extract_decision
from app.scenarios import assess, public_scenarios

def tool_response(payload):
    return SimpleNamespace(content=[SimpleNamespace(
        type="tool_use", name="submit_decision", input=payload)])

def test_multi_case_catalog_and_scenarios():
    case = BY_ID["incident-triage"]
    assert case.kind == "multi"
    assert len(public_scenarios(case.id)) == 30

def test_multi_schema_contains_three_typed_fields():
    schema = decision_schema(BY_ID["incident-triage"])["input_schema"]
    assert set(schema["required"]) == {"priority", "security_risk", "team"}
    assert schema["properties"]["team"]["enum"] == ["PLATFORM", "BACKEND", "SECURITY"]

def test_valid_claude_multi_output():
    output = {"priority": 4, "security_risk": 0.12, "team": "BACKEND"}
    value, raw = extract_decision(tool_response(output), BY_ID["incident-triage"])
    assert value == output
    assert raw == output

@pytest.mark.parametrize("payload", [
    {"priority": 4, "security_risk": 0.1},
    {"priority": "4", "security_risk": 0.1, "team": "BACKEND"},
    {"priority": 4, "security_risk": 1.4, "team": "BACKEND"},
    {"priority": 4, "security_risk": True, "team": "BACKEND"},
    {"priority": 4, "security_risk": 0.1, "team": "UNKNOWN"},
])
def test_invalid_multi_output_rejected(payload):
    with pytest.raises(ValueError):
        extract_decision(tool_response(payload), BY_ID["incident-triage"])

def test_multi_reference_requires_all_three_correct():
    expected = {"priority": 4, "security_risk": 0, "team": "BACKEND"}
    assert assess("incident-triage", {"priority": 3.99, "security_risk": 0.1, "team": "BACKEND"}, expected)
    assert not assess("incident-triage", {"priority": 3.99, "security_risk": 0.9, "team": "BACKEND"}, expected)
    assert not assess("incident-triage", {"priority": 3.99, "security_risk": 0.1, "team": "PLATFORM"}, expected)
