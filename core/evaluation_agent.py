"""Evaluation Agent: builds the scoring prompt for one supplier and calls the LLM.

The LLM only judges proposal content against the active criteria and returns
structured JSON. It never computes weights, benchmarks, tie-breaks, or ranks —
that is done deterministically in ranking.py.
"""
import json

from core.llm_client import call_llm

SYSTEM_PROMPT = """You are an RFP evaluation assistant for a procurement team.
You will be given the full text of one supplier's RFP response and a list of
evaluation criteria with their maximum scores.

Rules you MUST follow:
- Use ONLY evidence present in the supplier document below. Do not invent facts.
- Return exactly one result for every criterion listed, using its criterion_id.
- Each score must be an integer between 0 and that criterion's max_score, inclusive.
- Output JSON only. No markdown fences, no commentary before or after the JSON.

Output schema:
{
  "supplier_name": string,
  "criteria": [
    {"criterion_id": int, "score": int, "max_score": int, "justification": string, "evidence": string}
  ],
  "risks": [string],
  "overall_summary": string
}
"""


def build_user_prompt(supplier_name: str, supplier_text: str, criteria: list) -> str:
    criteria_desc = "\n".join(
        f"- criterion_id={c['criterion_id']}, name=\"{c['name']}\", "
        f"max_score={c['max_score']}, inspect: {c.get('description', '')}"
        for c in criteria
    )
    return (
        f"Supplier name: {supplier_name}\n\n"
        f"Evaluation criteria:\n{criteria_desc}\n\n"
        f"Supplier document text:\n\"\"\"\n{supplier_text[:12000]}\n\"\"\"\n"
    )


def evaluate_supplier(supplier_name: str, supplier_text: str, criteria: list, api_key: str, model: str) -> dict:
    """Returns the raw parsed JSON dict from the LLM (pre-validation)."""
    user_prompt = build_user_prompt(supplier_name, supplier_text, criteria)
    raw = call_llm(api_key, model, SYSTEM_PROMPT, user_prompt)

    cleaned = raw.strip()
    if cleaned.startswith("```"):
        cleaned = cleaned.strip("`")
        if cleaned.lower().startswith("json"):
            cleaned = cleaned[4:]
        cleaned = cleaned.strip()

    try:
        return json.loads(cleaned)
    except json.JSONDecodeError:
        return {"_parse_error": True, "_raw": raw, "supplier_name": supplier_name}
