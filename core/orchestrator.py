"""Orchestrator Agent: wires the full evaluate -> validate -> score -> rank -> persist flow."""
import datetime
import uuid

from core import database
from core.evaluation_agent import evaluate_supplier
from core.pdf_tool import extract_text
from core.ranking import compute_full_ranking
from core.validation import normalize


def run_evaluation_batch(suppliers: list, api_key: str, model: str) -> dict:
    """suppliers: list of dicts with keys: name, file (path or file-like), submission_date, experience_rating.

    Returns {"rfp_run_id": str, "results": [...], "status": "completed"|"failed"}.
    """
    criteria = database.get_active_criteria()
    if not criteria:
        raise ValueError("No active evaluation criteria found. Seed or activate criteria first.")

    metadata = {
        s["name"]: {
            "submission_date": s["submission_date"],
            "experience_rating": s["experience_rating"],
        }
        for s in suppliers
    }

    validated_results = []
    for s in suppliers:
        supplier_text = extract_text(s["file"])
        raw = evaluate_supplier(s["name"], supplier_text, criteria, api_key, model)
        validated = normalize(raw, s["name"], criteria)
        validated_results.append(validated)

    ranked = compute_full_ranking(validated_results, metadata)

    rfp_run_id = str(uuid.uuid4())
    created_at = datetime.datetime.utcnow().isoformat()
    database.create_run(rfp_run_id, created_at, status="completed")
    for r in ranked:
        database.persist_supplier_result(rfp_run_id, r)

    return {"rfp_run_id": rfp_run_id, "created_at": created_at, "results": ranked, "status": "completed"}
