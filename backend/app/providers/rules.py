def evaluate(case, text: str) -> dict:
    """Intentionally transparent simplistic baselines, NOT ground truth."""
    t = text.lower()
    if case.kind == "generation":
        raise ValueError("A rule engine cannot generate architecture documents")
    if case.kind == "choice":
        value = "NEEDS_MORE_CONTEXT" if len(t.split()) < 5 else "OPUS" if any(w in t for w in ("distributed", "consistency", "architecture")) else "SONNET" if any(w in t for w in ("refactor", "migrate", "design")) else "HAIKU"
    elif case.kind == "score":
        value = sum(bool(any(w in t for w in words)) for words in (("budget", "presupuesto"), ("cto", "decision maker"), ("quarter", "month", "trimestre"), ("approved", "aprobado")))
    else:
        value = float(("production" in t or "producción" in t) and ("without approval" in t or "without asking" in t or "sin aprobación" in t))
    return {"value": value, "raw": {"rule_based": True, "warning": "Illustrative baseline; not an authority."}, "usage": None, "model": "simple-keyword-baseline"}
