"""Seeds the evaluation_criteria table with the 5 example criteria from the project brief.
Run once: python db/seed_criteria.py
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.database import init_db, get_conn  # noqa: E402

DEFAULT_CRITERIA = [
    ("Technical Capability", "Architecture, integrations, scalability, technical fit", 0.30, 10),
    ("Implementation Plan", "Timeline, milestones, staffing, risk plan", 0.20, 10),
    ("Commercial Value", "Pricing clarity, total cost, assumptions", 0.20, 10),
    ("Security & Compliance", "Controls, certifications, privacy, auditability", 0.20, 10),
    ("Support & Experience", "Support model, similar projects, references", 0.10, 10),
]


def seed():
    init_db()
    with get_conn() as conn:
        existing = conn.execute("SELECT COUNT(*) AS c FROM evaluation_criteria").fetchone()["c"]
        if existing > 0:
            print(f"evaluation_criteria already has {existing} rows — skipping seed.")
            return
        for name, description, weight, max_score in DEFAULT_CRITERIA:
            conn.execute(
                """INSERT INTO evaluation_criteria (name, description, weight, max_score, is_active)
                   VALUES (?, ?, ?, ?, 1)""",
                (name, description, weight, max_score),
            )
    print(f"Seeded {len(DEFAULT_CRITERIA)} evaluation criteria.")


if __name__ == "__main__":
    seed()
