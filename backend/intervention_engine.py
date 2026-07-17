from datetime import datetime
from mine_state import mine_state, add_causal_event
from counterfactual_engine import calculate_counterfactuals
from causal_engine import mark_incident_recovering

intervention_state = {"status": "READY", "active_intervention": None, "history": []}


def get_decision_state():
    return {**calculate_counterfactuals(), "execution": intervention_state}


def execute_recommendation():
    decision = calculate_counterfactuals()
    recommendation = decision["recommendation"]
    if recommendation["action"] != "ISOLATE_T14_REBALANCE_FLEET":
        return {"status": "REJECTED", "reason": "No fleet-isolation recommendation is active"}
    if intervention_state["status"] == "EXECUTED":
        return intervention_state

    t14 = next((t for t in mine_state["trucks"] if t["entity_id"] == "T14"), None)
    route = next((r for r in mine_state["routes"] if r["entity_id"] == "R1"), None)
    gate = next((d for d in mine_state["dispatch_gates"] if d["entity_id"] == "D1"), None)
    if t14:
        t14["status"] = "MAINTENANCE"
        t14["speed"] = 0
        t14["maintenance_ticks"] = 0
    if route:
        route["risk_score"] = 20
        route["status"] = "RECOVERING"
    if gate:
        gate["delay_risk"] = 18
        gate["status"] = "RECOVERING"

    operations = mine_state["operations"]
    operations.update({"production_rate": 920, "truck_queue": 2, "dispatch_risk": 18, "predicted_loss": recommendation["predicted_loss_mt"]})
    mine_state["mine"]["status"] = "RECOVERING"
    mine_state["timestamp"] = datetime.now().isoformat()
    mark_incident_recovering()
    add_causal_event("MineMind isolated T14 from haulage", "Fleet rebalanced and downstream risk entered recovery", "T14", "INFO")

    record = {"intervention_id": "INT-FLEET-001", "timestamp": datetime.now().isoformat(), "action": recommendation["action"], "title": recommendation["title"], "status": "EXECUTED", "rerouted_trucks": ["T12", "T13", "T15", "T16"], "target_entity": "T14", "production_rate_mt_h": 920, "dispatch_risk": 18, "truck_queue": 2, "predicted_loss_mt": recommendation["predicted_loss_mt"], "avoided_loss_mt": recommendation["avoided_loss_mt"]}
    intervention_state.update({"status": "EXECUTED", "active_intervention": record})
    intervention_state["history"].append(record)
    return intervention_state


def get_intervention_state():
    return intervention_state


def reset_intervention_state():
    intervention_state.update({"status": "READY", "active_intervention": None, "history": []})
    return {"status": "INTERVENTION_STATE_RESET"}
