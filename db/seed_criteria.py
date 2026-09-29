"""CLI entrypoint to seed the evaluation_criteria table (also runs automatically on app startup).
Run: python db/seed_criteria.py
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.database import init_db, ensure_seed_data, get_conn  # noqa: E402


def seed():
    init_db()
    with get_conn() as conn:
        existing = conn.execute("SELECT COUNT(*) AS c FROM evaluation_criteria").fetchone()["c"]
    ensure_seed_data()
    if existing > 0:
        print(f"evaluation_criteria already had {existing} rows — skipped seeding.")
    else:
        print("Seeded default evaluation criteria.")


if __name__ == "__main__":
    seed()
