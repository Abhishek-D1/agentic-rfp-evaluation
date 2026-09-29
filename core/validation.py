"""Validation Tool: schema-checks and normalizes raw LLM output before scoring.

Never lets a malformed/missing LLM result crash the batch — instead clips,
fills defaults, and records a warning so the run stays auditable.
"""


def normalize(raw: dict, supplier_name: str, criteria: list) -> dict:
    warnings = []

    if raw.get("_parse_error"):
        warnings.append("LLM response was not valid JSON; all criteria defaulted to 0.")
        raw = {}

    by_id = {}
    for entry in raw.get("criteria", []) or []:
        cid = entry.get("criterion_id")
        if cid is not None:
            by_id[cid] = entry

    normalized_criteria = []
    for c in criteria:
        cid = c["criterion_id"]
        max_score = c["max_score"]
        entry = by_id.get(cid)

        if entry is None:
            normalized_criteria.append({
                "criterion_id": cid,
                "name": c["name"],
                "weight": c["weight"],
                "max_score": max_score,
                "score": 0,
                "justification": "",
                "evidence": "",
            })
            warnings.append(f"Missing score for criterion '{c['name']}' — defaulted to 0.")
            continue

        score = entry.get("score", 0)
        try:
            score = float(score)
        except (TypeError, ValueError):
            warnings.append(f"Non-numeric score for criterion '{c['name']}' — defaulted to 0.")
            score = 0

        if score < 0 or score > max_score:
            warnings.append(
                f"Score {score} for criterion '{c['name']}' out of range [0, {max_score}] — clipped."
            )
            score = max(0, min(score, max_score))

        normalized_criteria.append({
            "criterion_id": cid,
            "name": c["name"],
            "weight": c["weight"],
            "max_score": max_score,
            "score": score,
            "justification": entry.get("justification", ""),
            "evidence": entry.get("evidence", ""),
        })

    return {
        "supplier_name": raw.get("supplier_name") or supplier_name,
        "criteria": normalized_criteria,
        "risks": raw.get("risks", []) or [],
        "overall_summary": raw.get("overall_summary", ""),
        "warnings": warnings,
    }
