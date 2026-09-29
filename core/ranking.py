"""Ranking Tool: deterministic-only arithmetic. The LLM never touches this.

Formulas (per the project brief):
- absolute weighted score = sum over criteria of (score / max_score) * weight   [0..1, shown as %]
- criterion benchmark      = highest valid score observed for that criterion across all suppliers
- criterion gap            = supplier score - benchmark score (0 for the leader, else negative)
- relative performance %   = (supplier score / benchmark score) * 100, 0 if benchmark is 0
- PPI                      = weighted average of criterion relative-performance percentages

Tie-break order (mandatory): PPI desc -> submission_date asc -> experience_rating desc -> supplier_name asc.
"""


def compute_absolute_score(validated: dict) -> float:
    total = 0.0
    for c in validated["criteria"]:
        if c["max_score"] > 0:
            total += (c["score"] / c["max_score"]) * c["weight"]
    return round(total * 100, 2)  # expressed as a percentage of total weight


def compute_benchmarks(all_validated: list) -> dict:
    """Returns {criterion_id: best_score_observed}."""
    benchmarks = {}
    for v in all_validated:
        for c in v["criteria"]:
            cid = c["criterion_id"]
            benchmarks[cid] = max(benchmarks.get(cid, 0), c["score"])
    return benchmarks


def annotate_with_benchmarks(validated: dict, benchmarks: dict) -> dict:
    annotated_criteria = []
    relative_pcts = []
    for c in validated["criteria"]:
        benchmark_score = benchmarks.get(c["criterion_id"], 0)
        gap = c["score"] - benchmark_score
        relative_pct = (c["score"] / benchmark_score * 100) if benchmark_score > 0 else 0.0
        relative_pcts.append((relative_pct, c["weight"]))
        annotated_criteria.append({
            **c,
            "benchmark_score": benchmark_score,
            "gap": round(gap, 2),
            "relative_pct": round(relative_pct, 2),
        })

    ppi = sum(pct * weight for pct, weight in relative_pcts)
    ppi = round(ppi, 2)

    return {
        **validated,
        "criteria": annotated_criteria,
        "ppi": ppi,
    }


def rank_suppliers(annotated_suppliers: list, metadata: dict) -> list:
    """metadata: {supplier_name: {"submission_date": "YYYY-MM-DD", "experience_rating": float}}"""
    enriched = []
    for s in annotated_suppliers:
        meta = metadata.get(s["supplier_name"], {})
        enriched.append({
            **s,
            "submission_date": meta.get("submission_date", ""),
            "experience_rating": meta.get("experience_rating", 0),
            "absolute_score": s.get("absolute_score", 0),
        })

    # Mandatory tie-break order: PPI desc, submission_date asc, experience_rating desc, name asc.
    enriched.sort(
        key=lambda s: (
            -s["ppi"],
            s["submission_date"],
            -s["experience_rating"],
            s["supplier_name"],
        )
    )

    for i, s in enumerate(enriched, start=1):
        s["final_rank"] = i

    return enriched


def compute_full_ranking(validated_suppliers: list, metadata: dict) -> list:
    for v in validated_suppliers:
        v["absolute_score"] = compute_absolute_score(v)

    benchmarks = compute_benchmarks(validated_suppliers)
    annotated = [annotate_with_benchmarks(v, benchmarks) for v in validated_suppliers]
    return rank_suppliers(annotated, metadata)
