# Agentic RFP Evaluation and Supplier Ranking

An AI-assisted Streamlit application that reads supplier RFP PDFs, has an LLM score each
proposal against configurable weighted criteria, and then uses **deterministic Python only**
to compute weighted scores, peer benchmarks, a Peer Performance Index (PPI), and a final
tie-broken ranking. Built for the "Agentic RFP Evaluation and Supplier Ranking" classroom
mini-project brief.

## Architecture

```
Streamlit UI (app.py)
   |
   v
Orchestrator Agent (core/orchestrator.py)
   |-- Document Tool      core/pdf_tool.py        (PyMuPDF text extraction)
   |-- Evaluation Agent   core/evaluation_agent.py (prompt + OpenRouter call)
   |-- Validation Tool    core/validation.py       (schema check, clipping, warnings)
   |-- Ranking Tool       core/ranking.py          (weighted score, benchmark, PPI, tie-break — deterministic only)
   |
   v
SQLite (core/database.py, db/schema.sql)
```

The LLM (via OpenRouter) only judges proposal content and returns a criterion-wise score,
justification, and evidence in JSON. It never computes weights, benchmarks, tie-breaks, or
final rank — that arithmetic lives entirely in `core/ranking.py` so results are reproducible
and explainable.

## Setup

```bash
cd rfp_evaluation
python -m venv .venv
source .venv/Scripts/activate   # Windows Git Bash; use .venv\Scripts\activate on cmd/PowerShell
pip install -r requirements.txt
python db/seed_criteria.py               # seeds the 5 default evaluation criteria
python sample_rfps/generate_sample_pdfs.py   # generates 4 fictional supplier PDFs
streamlit run app.py
```

Open the app, paste an **OpenRouter API key** (https://openrouter.ai/keys) into the sidebar,
pick a model (a curated list of JSON-capable models is provided, plus a free-text override
for any other OpenRouter model slug), then go to **Supplier Input & Evaluate**, upload the
4 sample PDFs from `sample_rfps/`, fill in supplier name / submission date / experience
rating for each, and click **Evaluate**.

The API key is kept only in `st.session_state` for the browser session — it is never written
to disk or to the SQLite database.

## Formulas

- **Absolute weighted score** = Σ (criterion score / criterion max_score) × criterion weight, shown as a percentage.
- **Criterion benchmark** = highest valid score observed for that criterion across all suppliers in the batch.
- **Criterion gap** = supplier score − benchmark score (0 for the leader, negative otherwise).
- **Relative performance %** = (supplier score / benchmark score) × 100; defined as 0% when the benchmark is 0 (avoids divide-by-zero).
- **Peer Performance Index (PPI)** = weighted average of each criterion's relative-performance percentage.
- **Tie-break order** (mandatory, applied only after all suppliers are scored): higher PPI → earlier submission date → higher historical experience rating → supplier name ascending. Ranks 1, 2, 3… are assigned only after this stable sort.

## Assumptions

- Criterion weights are stored as fractions (e.g. 0.30) and are expected to sum to 1.0 across active criteria; the Criteria screen flags a mismatch.
- If the LLM's JSON is malformed or a criterion is missing from its response, the Validation Tool fills a 0 score and records a warning rather than failing the whole batch.
- Scores outside `[0, max_score]` are clipped, with a warning recorded.
- Each evaluation run gets one UUID `RFP_RUN_ID`, and all supplier results for that run are persisted together in `supplier_results`, joined to `rfp_runs`.

## Project structure

See file tree in the repository root; `core/` holds the agent/tool logic, `db/` the schema and seed script, `sample_rfps/` the 4 synthetic proposals and their generator script, `sample_output/` a sample exported run JSON.

## Testing / demo

1. Run a full successful batch with the 4 sample PDFs (see Setup) — check the Leaderboard, Detailed Scorecard, and Run Details screens, and download the JSON.
2. Validation/error case: clear the OpenRouter key mid-session (Evaluate button disables), or paste an invalid key and click Evaluate — the app shows a clean error (`401 Unauthorized`) instead of crashing.
3. Re-running the same validated scorecards twice produces identical formulas and ordering (deterministic ranking).

## Deployment (Streamlit Community Cloud)

See the deployment walkthrough provided separately, or:
1. Push this repo to GitHub (public or private, connected to your Streamlit Cloud account).
2. On https://share.streamlit.io, click "New app", pick the repo/branch, and set the main file path to `rfp_evaluation/app.py` (adjust if you flatten the folder into its own repo).
3. No secrets are required at deploy time — the OpenRouter key is entered by each user in the running app's sidebar.
4. Deploy, then confirm the leaderboard flow works end-to-end on the public URL.
