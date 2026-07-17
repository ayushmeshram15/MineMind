# MineMind 3.0 — Final Product Candidate

## Product flow
Landing → Signup/Login → Mine Workspace → Guided Demo → Fleet Operations → Live Digital Twin → Causal Intelligence → Predictive Analytics → Decision Engine → Intervention → Recovery → Ore Traceability → Data Sources → Vision Intelligence → Incident History.

## Run locally
Backend: `cd backend && source ../.venv/bin/activate && python3 -m pip install -r requirements.txt && python3 -m uvicorn main:app --reload`
Frontend: `cd frontend && npm install && npm run dev`

## QA
With backend running: `cd backend && python3 smoke_test.py`
Production frontend: `cd frontend && npm run build`

## Product boundaries
The fleet engine and AI workflows are a deterministic operational demo/simulation. CSV ingestion, workspace auth/persistence, event ledger, alert read-state, and workspace-scoped Vision events are implemented application workflows. Vision detection is a demo inference workflow, not a deployed mine-trained CV model.
