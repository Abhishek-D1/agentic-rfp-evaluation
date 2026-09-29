"""Agentic RFP Evaluation and Supplier Ranking — Streamlit app."""
import datetime
import json

import streamlit as st

from core import database
from core.llm_client import CURATED_MODELS
from core.orchestrator import run_evaluation_batch

st.set_page_config(page_title="Agentic RFP Evaluation", layout="wide")
database.init_db()
database.ensure_seed_data()

if "last_run" not in st.session_state:
    st.session_state.last_run = None

# ---------------------------------------------------------------- Sidebar ---
with st.sidebar:
    st.header("OpenRouter Settings")
    api_key = st.text_input("OpenRouter API key", type="password", key="api_key")
    model_choice = st.selectbox("Model", CURATED_MODELS + ["Other (enter below)"])
    if model_choice == "Other (enter below)":
        model = st.text_input("Custom OpenRouter model slug", placeholder="e.g. mistralai/mistral-large")
    else:
        model = model_choice
    st.caption("Your key is kept only in this browser session and is never written to disk or the database.")

    st.divider()
    page = st.radio(
        "Navigate",
        ["Criteria", "Supplier Input & Evaluate", "Leaderboard", "Detailed Scorecard", "Run Details"],
    )

# --------------------------------------------------------------- Criteria ---
if page == "Criteria":
    st.title("Evaluation Criteria")
    st.caption("The weighted rubric every supplier is scored against. Active weights must total 100%.")
    criteria = database.get_all_criteria()
    active_weight = sum(c["weight"] for c in criteria if c["is_active"])
    st.metric("Active weight total", f"{active_weight * 100:.0f}%")
    if abs(active_weight - 1.0) > 1e-6:
        st.warning("Active criteria weights should sum to 100%.")
    else:
        st.success("Active weights sum to 100%.")

    if "editing_criterion_id" not in st.session_state:
        st.session_state.editing_criterion_id = None

    header = st.columns([2, 4, 1, 1, 1, 1])
    for col, label in zip(header, ["Name", "Description", "Weight", "Max score", "Active", ""]):
        col.markdown(f"**{label}**")

    for c in criteria:
        row = st.columns([2, 4, 1, 1, 1, 1])
        row[0].write(c["name"])
        row[1].write(c["description"])
        row[2].write(f"{c['weight']*100:.0f}%")
        row[3].write(c["max_score"])
        row[4].write("✓" if c["is_active"] else "—")
        if row[5].button("Edit", key=f"edit_btn_{c['criterion_id']}"):
            st.session_state.editing_criterion_id = c["criterion_id"]

        if st.session_state.editing_criterion_id == c["criterion_id"]:
            with st.form(key=f"edit_form_{c['criterion_id']}"):
                st.subheader(f"Edit: {c['name']}")
                new_name = st.text_input("Name", value=c["name"])
                new_description = st.text_area("Description", value=c["description"] or "")
                new_weight_pct = st.number_input(
                    "Weight (%)", min_value=0.0, max_value=100.0, value=c["weight"] * 100, step=1.0
                )
                new_max_score = st.number_input(
                    "Max score", min_value=1, max_value=100, value=int(c["max_score"]), step=1
                )
                new_active = st.checkbox("Active", value=bool(c["is_active"]))

                save_col, cancel_col = st.columns(2)
                saved = save_col.form_submit_button("Save", type="primary")
                cancelled = cancel_col.form_submit_button("Cancel")

                if saved:
                    database.upsert_criterion(
                        c["criterion_id"], new_name, new_description,
                        new_weight_pct / 100, new_max_score, new_active,
                    )
                    st.session_state.editing_criterion_id = None
                    st.rerun()
                if cancelled:
                    st.session_state.editing_criterion_id = None
                    st.rerun()
        st.divider()

# ------------------------------------------------- Supplier Input & Evaluate ---
elif page == "Supplier Input & Evaluate":
    st.title("Supplier Input")
    criteria = database.get_active_criteria()
    st.info(f"{len(criteria)} active criteria will be used for this batch.")

    uploaded_files = st.file_uploader(
        "Upload supplier RFP PDFs", type=["pdf"], accept_multiple_files=True
    )

    suppliers = []
    if uploaded_files:
        st.subheader("Supplier metadata")
        for f in uploaded_files:
            cols = st.columns([2, 1, 1])
            default_name = f.name.rsplit(".", 1)[0].replace("_", " ").title()
            name = cols[0].text_input(f"Supplier name for {f.name}", value=default_name, key=f"name_{f.name}")
            sub_date = cols[1].date_input(
                "Submission date", value=datetime.date.today(), key=f"date_{f.name}"
            )
            experience = cols[2].slider(
                "Historical experience rating", 0.0, 10.0, 5.0, key=f"exp_{f.name}"
            )
            suppliers.append({
                "name": name,
                "file": f,
                "submission_date": sub_date.isoformat(),
                "experience_rating": experience,
            })

    disabled = not api_key or not uploaded_files or not model
    if not api_key:
        st.warning("Enter your OpenRouter API key in the sidebar to enable evaluation.")

    if st.button("Evaluate", disabled=disabled, type="primary"):
        try:
            with st.spinner("Extracting PDFs, scoring with the LLM, and ranking suppliers..."):
                result = run_evaluation_batch(suppliers, api_key, model)
            st.session_state.last_run = result
            st.success(f"Run {result['rfp_run_id']} completed. See Leaderboard.")
        except Exception as e:
            st.error(f"Evaluation failed: {e}")

# ------------------------------------------------------------- Leaderboard ---
elif page == "Leaderboard":
    st.title("Leaderboard")
    run = st.session_state.last_run
    if not run:
        st.info("Run a batch evaluation first (Supplier Input & Evaluate).")
    else:
        rows = [
            {
                "Rank": r["final_rank"],
                "Supplier": r["supplier_name"],
                "Absolute Score (%)": r["absolute_score"],
                "PPI (%)": r["ppi"],
                "Submission Date": r["submission_date"],
                "Experience Rating": r["experience_rating"],
            }
            for r in run["results"]
        ]
        st.dataframe(rows, use_container_width=True, hide_index=True)

# -------------------------------------------------------- Detailed Scorecard ---
elif page == "Detailed Scorecard":
    st.title("Detailed Scorecard")
    run = st.session_state.last_run
    if not run:
        st.info("Run a batch evaluation first (Supplier Input & Evaluate).")
    else:
        supplier_names = [r["supplier_name"] for r in run["results"]]
        selected = st.selectbox("Supplier", supplier_names)
        supplier = next(r for r in run["results"] if r["supplier_name"] == selected)

        st.write(f"**Overall summary:** {supplier.get('overall_summary', '')}")
        if supplier.get("risks"):
            st.write("**Risks:**", ", ".join(supplier["risks"]))
        if supplier.get("warnings"):
            st.warning("Warnings: " + "; ".join(supplier["warnings"]))

        for c in supplier["criteria"]:
            with st.expander(f"{c['name']} — score {c['score']}/{c['max_score']} (weight {c['weight']*100:.0f}%)"):
                st.write(f"Benchmark: {c['benchmark_score']} | Gap: {c['gap']} | Relative %: {c['relative_pct']}%")
                st.write(f"**Justification:** {c['justification']}")
                st.write(f"**Evidence:** {c['evidence']}")

# ------------------------------------------------------------- Run Details ---
elif page == "Run Details":
    st.title("Run Details")
    run = st.session_state.last_run
    if not run:
        st.info("Run a batch evaluation first (Supplier Input & Evaluate).")
    else:
        st.write(f"**RFP_RUN_ID:** `{run['rfp_run_id']}`")
        st.write(f"**Created at (UTC):** {run['created_at']}")
        st.write(f"**Status:** {run['status']}")

        all_warnings = []
        for r in run["results"]:
            for w in r.get("warnings", []):
                all_warnings.append(f"{r['supplier_name']}: {w}")
        if all_warnings:
            st.subheader("Warnings")
            for w in all_warnings:
                st.write(f"- {w}")
        else:
            st.write("No validation warnings for this run.")

        st.subheader("Tie-break rule applied")
        st.write(
            "1) Higher PPI first → 2) Earlier submission date → 3) Higher historical experience "
            "rating → 4) Supplier name ascending. Ranks assigned 1, 2, 3... after this stable sort."
        )

        st.subheader("Download")
        st.download_button(
            "Download full result as JSON",
            data=json.dumps(run, indent=2),
            file_name=f"rfp_run_{run['rfp_run_id']}.json",
            mime="application/json",
        )
