"""SQLite access layer: schema init, criteria CRUD, and run persistence."""
import json
import os
import sqlite3
from contextlib import contextmanager

DB_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "db", "rfp_evaluation.db")
SCHEMA_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "db", "schema.sql")


@contextmanager
def get_conn():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()


DEFAULT_CRITERIA = [
    ("Technical Capability", "Architecture, integrations, scalability, technical fit", 0.30, 10),
    ("Implementation Plan", "Timeline, milestones, staffing, risk plan", 0.20, 10),
    ("Commercial Value", "Pricing clarity, total cost, assumptions", 0.20, 10),
    ("Security & Compliance", "Controls, certifications, privacy, auditability", 0.20, 10),
    ("Support & Experience", "Support model, similar projects, references", 0.10, 10),
]


def init_db():
    with open(SCHEMA_PATH, "r", encoding="utf-8") as f:
        schema = f.read()
    with get_conn() as conn:
        conn.executescript(schema)


def dedupe_criteria_by_name():
    """Removes duplicate rows that share the same name, keeping the lowest criterion_id.
    Cleans up any duplicates inserted before the unique index existed (e.g. from a race
    between concurrent Streamlit Cloud workers seeding at the same time)."""
    with get_conn() as conn:
        conn.execute(
            """DELETE FROM evaluation_criteria
               WHERE criterion_id NOT IN (
                   SELECT MIN(criterion_id) FROM evaluation_criteria GROUP BY name
               )"""
        )


def ensure_seed_data():
    """Seeds the default criteria if missing, and cleans up any duplicate rows.
    Race-safe: a UNIQUE index on name means concurrent seeders can't double-insert,
    and this cleans up any duplicates a previous, non-race-safe version left behind."""
    dedupe_criteria_by_name()
    with get_conn() as conn:
        conn.execute(
            "CREATE UNIQUE INDEX IF NOT EXISTS idx_evaluation_criteria_name ON evaluation_criteria(name)"
        )
        for name, description, weight, max_score in DEFAULT_CRITERIA:
            conn.execute(
                """INSERT OR IGNORE INTO evaluation_criteria
                   (name, description, weight, max_score, is_active)
                   VALUES (?, ?, ?, ?, 1)""",
                (name, description, weight, max_score),
            )


def get_active_criteria():
    with get_conn() as conn:
        rows = conn.execute(
            "SELECT * FROM evaluation_criteria WHERE is_active = 1 ORDER BY criterion_id"
        ).fetchall()
        return [dict(r) for r in rows]


def get_all_criteria():
    with get_conn() as conn:
        rows = conn.execute("SELECT * FROM evaluation_criteria ORDER BY criterion_id").fetchall()
        return [dict(r) for r in rows]


def upsert_criterion(criterion_id, name, description, weight, max_score, is_active):
    with get_conn() as conn:
        if criterion_id:
            conn.execute(
                """UPDATE evaluation_criteria
                   SET name=?, description=?, weight=?, max_score=?, is_active=?
                   WHERE criterion_id=?""",
                (name, description, weight, max_score, int(is_active), criterion_id),
            )
        else:
            conn.execute(
                """INSERT INTO evaluation_criteria (name, description, weight, max_score, is_active)
                   VALUES (?, ?, ?, ?, ?)""",
                (name, description, weight, max_score, int(is_active)),
            )


def create_run(rfp_run_id, created_at, status="completed"):
    with get_conn() as conn:
        conn.execute(
            "INSERT INTO rfp_runs (rfp_run_id, created_at, status) VALUES (?, ?, ?)",
            (rfp_run_id, created_at, status),
        )


def persist_supplier_result(rfp_run_id, result):
    with get_conn() as conn:
        conn.execute(
            """INSERT INTO supplier_results
               (rfp_run_id, supplier_name, submission_date, experience_rating,
                absolute_score, ppi, final_rank, result_json)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                rfp_run_id,
                result["supplier_name"],
                result["submission_date"],
                result["experience_rating"],
                result["absolute_score"],
                result["ppi"],
                result["final_rank"],
                json.dumps(result),
            ),
        )


def get_run_results(rfp_run_id):
    with get_conn() as conn:
        rows = conn.execute(
            "SELECT * FROM supplier_results WHERE rfp_run_id = ? ORDER BY final_rank",
            (rfp_run_id,),
        ).fetchall()
        return [json.loads(r["result_json"]) for r in rows]


def get_run(rfp_run_id):
    with get_conn() as conn:
        row = conn.execute(
            "SELECT * FROM rfp_runs WHERE rfp_run_id = ?", (rfp_run_id,)
        ).fetchone()
        return dict(row) if row else None


def list_runs():
    with get_conn() as conn:
        rows = conn.execute(
            "SELECT * FROM rfp_runs ORDER BY created_at DESC"
        ).fetchall()
        return [dict(r) for r in rows]
