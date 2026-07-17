from fastapi import FastAPI, Depends, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import os
from pathlib import Path

from mine_state import (
    get_mine_state,
    reset_mine_state,
)

from causal_engine import (
    get_causal_state,
    reset_causal_state,
)

from counterfactual_engine import (
    calculate_counterfactuals,
)

from intervention_engine import (
    get_decision_state,
    execute_recommendation,
    get_intervention_state,
    reset_intervention_state,
)

from predictive_engine import (
    get_predictive_state,
)

from incident_engine import (
    get_incident_history,
)

from vision_engine import analyze_video_bytes
from product_services import get_data_sources, ingest_dataset, record_vision_event, get_vision_events, reset_product_services, get_alerts, mark_alert_read, seed_demo_workspace, triage_vision_event
from auth_service import signup, login, current_session, session_payload, update_profile, logout

from fleet_simulation import (
    get_simulation_state,
    start_fleet_simulation,
    pause_fleet_simulation,
    resume_fleet_simulation,
    reset_fleet_simulation,
)


app = FastAPI(
    title="MineMind Causal Digital Twin API",
    version="1.0.0",
)


app.add_middleware(
    CORSMiddleware,
    allow_origins=[x.strip() for x in os.getenv("MINEMIND_CORS_ORIGINS", "http://localhost:5173,http://127.0.0.1:5173,http://localhost:5174,http://127.0.0.1:5174,http://localhost:5175,http://127.0.0.1:5175").split(",") if x.strip()],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ============================================================
# SYSTEM
# ============================================================

@app.get("/")
def root():
    return {
        "platform": "MineMind",
        "system": "Causal Predictive Digital Twin",
        "status": "ONLINE",
    }


@app.get("/health")
def health():
    return {
        "backend": "healthy",
    }


# ============================================================
# DIGITAL TWIN
# ============================================================

@app.get("/twin/state")
def twin_state(session=Depends(current_session)):
    return get_mine_state()


@app.post("/simulation/start")
def simulation_start(session=Depends(current_session)):
    fleet_result = start_fleet_simulation()
    return {
        "fleet": fleet_result,
        "scenario": "DETERMINISTIC_FLEET_INCIDENT",
        "causal": {"status": "MONITORING_FLEET_STREAM"},
    }


@app.post("/simulation/pause")
def simulation_pause(session=Depends(current_session)):
    return pause_fleet_simulation()


@app.post("/simulation/resume")
def simulation_resume(session=Depends(current_session)):
    return resume_fleet_simulation()


@app.get("/simulation/state")
def simulation_state(session=Depends(current_session)):
    return get_simulation_state()


@app.post("/simulation/reset")
def simulation_reset(session=Depends(current_session)):
    fleet = reset_fleet_simulation()
    intervention = reset_intervention_state()
    causal = reset_causal_state()
    twin = reset_mine_state()
    reset_product_services(session["workspace_id"])
    return {
        "status": "ENVIRONMENT_RESET",
        "fleet": fleet,
        "twin": twin,
        "causal": causal,
        "intervention": intervention,
    }


# ============================================================
# CAUSAL INTELLIGENCE
# ============================================================

@app.get("/causal/state")
def causal_state(session=Depends(current_session)):
    return get_causal_state()


# ============================================================
# COUNTERFACTUAL ENGINE
# ============================================================

@app.get("/counterfactual/state")
def counterfactual_state(session=Depends(current_session)):
    return calculate_counterfactuals()


# ============================================================
# DECISION ENGINE
# ============================================================

@app.get("/decision/state")
def decision_state(session=Depends(current_session)):
    return get_decision_state()


@app.post("/decision/execute")
def decision_execute(session=Depends(current_session)):
    return execute_recommendation()


# ============================================================
# INTERVENTION ENGINE
# ============================================================

@app.get("/interventions/state")
def interventions_state(session=Depends(current_session)):
    return get_intervention_state()


# ============================================================
# PREDICTIVE ANALYTICS ENGINE
# ============================================================

@app.get("/predictive/state")
def predictive_state(session=Depends(current_session)):
    return get_predictive_state()

# ============================================================
# INCIDENT HISTORY ENGINE
# ============================================================

@app.get("/incidents/state")
def incidents_state(session=Depends(current_session)):
    history = get_incident_history()
    vision = get_vision_events(session["workspace_id"])
    incidents = vision + history.get("incidents", [])
    incidents.sort(key=lambda x: x.get("timestamp", ""), reverse=True)
    summary = dict(history.get("summary", {}))
    summary["total_incidents"] = len(incidents)
    summary["warning_incidents"] = sum(1 for x in incidents if x.get("severity") == "WARNING")
    return {**history, "summary": summary, "incidents": incidents}


# ============================================================
# SAAS PRODUCT SERVICES
# ============================================================

@app.get("/data-sources/state")
def data_sources_state(session=Depends(current_session)):
    return get_data_sources(session["workspace_id"])

@app.post("/data-sources/ingest")
def data_sources_ingest(payload: dict, session=Depends(current_session)):
    return ingest_dataset(session["workspace_id"], payload)

@app.post("/vision/analyze")
async def vision_analyze(file: UploadFile = File(...), session=Depends(current_session)):
    if not (file.content_type or "").startswith("video/"):
        raise HTTPException(status_code=400, detail="Upload a video file")
    data = await file.read()
    if not data:
        raise HTTPException(status_code=400, detail="Uploaded video is empty")
    if len(data) > 200 * 1024 * 1024:
        raise HTTPException(status_code=413, detail="Video must be smaller than 200 MB")
    try:
        result = analyze_video_bytes(data, Path(file.filename or "video.mp4").suffix or ".mp4")
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"YOLO analysis failed: {exc}")
    event = record_vision_event(session["workspace_id"], {
        "camera_id": "UPLOAD-01",
        "detections": result["detections"],
        "confidence": max([x.get("confidence", 0) for x in result["detections"]] or [0]),
        "description": result["description"],
        "severity": result["severity"],
        "classification": result["classification"],
        "model": result["model"],
        "real_inference": True,
    })
    return {**result, "event": event}

@app.post("/vision/events")
def vision_event(payload: dict, session=Depends(current_session)):
    return record_vision_event(session["workspace_id"], payload)

@app.get("/vision/events")
def vision_events(session=Depends(current_session)):
    return {"events": get_vision_events(session["workspace_id"])}

@app.get("/alerts/state")
def alerts_state(session=Depends(current_session)):
    return get_alerts(session["workspace_id"], get_incident_history().get("incidents", []))

@app.post("/alerts/read")
def alerts_read(payload: dict, session=Depends(current_session)):
    return mark_alert_read(session["workspace_id"], payload.get("alert_key", ""))

@app.post("/workspace/demo-seed")
def demo_seed(session=Depends(current_session)):
    return seed_demo_workspace(session["workspace_id"])


@app.post("/vision/events/{event_id}/triage")
def vision_triage(event_id: str, session=Depends(current_session)):
    return triage_vision_event(session["workspace_id"], event_id)

@app.post("/workspace/demo-launch")
def demo_launch(session=Depends(current_session)):
    seed = seed_demo_workspace(session["workspace_id"])
    reset_fleet_simulation(); reset_intervention_state(); reset_causal_state(); reset_mine_state()
    fleet = start_fleet_simulation()
    return {"status":"DEMO_RUNNING","seed":seed,"fleet":fleet,"journey":["FLEET_LIVE","T14_DEGRADATION","CAUSAL_EXPLANATION","DECISION_REQUIRED","INTERVENTION","RECOVERY"]}

@app.get("/workspace/demo-status")
def demo_status(session=Depends(current_session)):
    sim = get_simulation_state()
    causal = get_causal_state()
    decision = get_decision_state()
    intervention = get_intervention_state()
    active = causal.get("active_incident")
    history = intervention.get("history", [])
    if history:
        stage = 6
    elif active and (decision.get("recommended_action") or decision.get("recommendation")):
        stage = 4
    elif active:
        stage = 3
    elif sim.get("status") in {"RUNNING", "ACTIVE"}:
        stage = 1
    else:
        stage = 0
    return {"stage": stage, "simulation": sim.get("status", "IDLE"), "incident_id": active.get("incident_id") if active else None, "interventions": len(history)}

# ============================================================
# AUTHENTICATION & WORKSPACES
# ============================================================
@app.post("/auth/signup")
def auth_signup(payload: dict): return signup(payload)
@app.post("/auth/login")
def auth_login(payload: dict): return login(payload)
@app.get("/auth/me")
def auth_me(session=Depends(current_session)): return session_payload(session["token"])
@app.put("/workspace/profile")
def workspace_profile(payload: dict, session=Depends(current_session)): return update_profile(session,payload)
@app.post("/auth/logout")
def auth_logout(session=Depends(current_session)): return logout(session)
