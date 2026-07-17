from datetime import datetime
from causal_engine import get_causal_state
from mine_state import mine_state


def _clamp(value, low=0.0, high=100.0):
    return max(low, min(high, value))


def calculate_counterfactuals():
    causal = get_causal_state()
    active = causal.get("active_incident")
    operations = mine_state["operations"]
    incident = active or {"incident_id": "NO-ACTIVE-INCIDENT", "entity": "FLEET", "entity_name": "Mine Fleet", "incident_type": "NORMAL_OPERATION", "current_value": 0, "threshold": 45}

    incident_live = bool(active and active.get("status") not in {"RESOLVED"})
    baseline_loss = float(operations.get("predicted_loss", 0))
    baseline_risk = float(operations.get("dispatch_risk", 0))
    if incident_live and active.get("status") in {"PROPAGATING", "DECISION_REQUIRED"}:
        baseline_loss = max(baseline_loss, 140.0)
        baseline_risk = max(baseline_risk, 68.0)
    production = float(operations.get("production_rate", 0))
    queue = int(operations.get("truck_queue", 0))

    scenarios = [
        {"scenario_id": "CF-001", "action": "CONTINUE_OPERATION", "title": "Continue Current Fleet Cycle", "description": "Keep T14 in service and accept the current propagation risk.", "predicted_loss_mt": baseline_loss, "dispatch_risk": baseline_risk, "production_rate_mt_h": production, "truck_queue": queue, "avoided_loss_mt": 0.0, "confidence": 92},
        {"scenario_id": "CF-002", "action": "SLOW_T14", "title": "Restrict T14 Speed", "description": "Reduce T14 haul speed while retaining it in the active cycle.", "predicted_loss_mt": round(baseline_loss * 0.58, 1), "dispatch_risk": round(baseline_risk * 0.62, 1), "production_rate_mt_h": max(production, 810), "truck_queue": max(2, queue - 1), "avoided_loss_mt": round(baseline_loss * 0.42, 1), "confidence": 86},
        {"scenario_id": "CF-003", "action": "ISOLATE_T14_REBALANCE_FLEET", "title": "Isolate T14 and Rebalance Fleet", "description": "Remove T14 for preventive maintenance and rebalance healthy trucks across active routes.", "predicted_loss_mt": round(baseline_loss * 0.2, 1), "dispatch_risk": 18.0 if incident_live else baseline_risk, "production_rate_mt_h": 920 if incident_live else production, "truck_queue": 2 if incident_live else queue, "avoided_loss_mt": round(baseline_loss * 0.8, 1), "confidence": 92},
    ]

    target_production = max(float(operations.get("target_production_rate", 1000)), 1.0)
    safe_loss = max(baseline_loss, 1.0)
    safe_risk = max(baseline_risk, 1.0)
    baseline_queue = max(queue, 1)
    for scenario in scenarios:
        loss_score = (1 - min(scenario["predicted_loss_mt"] / safe_loss, 1)) * 45
        risk_score = (1 - min(scenario["dispatch_risk"] / safe_risk, 1)) * 35
        production_score = min(scenario["production_rate_mt_h"] / target_production, 1) * 15
        queue_score = (1 - min(scenario["truck_queue"] / baseline_queue, 1)) * 5
        scenario["decision_score"] = round(_clamp(loss_score + risk_score + production_score + queue_score), 1)

    recommended = max(scenarios, key=lambda item: item["decision_score"])
    return {
        "engine_status": "DECISION_READY" if incident_live and active.get("status") == "DECISION_REQUIRED" else ("INTERVENTION_ACTIVE" if incident_live and active.get("status") == "RECOVERING" else "MONITORING"),
        "timestamp": datetime.now().isoformat(),
        "incident": {**incident, "entity_id": incident.get("entity")},
        "baseline": {"predicted_loss_mt": baseline_loss, "dispatch_risk": baseline_risk},
        "scenarios": scenarios,
        "recommendation": {"scenario_id": recommended["scenario_id"], "action": recommended["action"], "title": recommended["title"], "reason": "This action isolates the degrading asset while preserving fleet throughput and reducing downstream dispatch risk.", "predicted_loss_mt": recommended["predicted_loss_mt"], "avoided_loss_mt": recommended["avoided_loss_mt"], "dispatch_risk": recommended["dispatch_risk"], "decision_score": recommended["decision_score"], "confidence": recommended["confidence"]},
    }
