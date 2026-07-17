from datetime import datetime
import threading

from mine_state import mine_state, add_causal_event

causal_intelligence = {
    "engine_status": "READY",
    "active_incident": None,
    "predictions": [],
    "recommendations": [],
    "propagation_chain": [],
}

_lock = threading.RLock()
_scenario = {"triggered": False, "trigger_tick": None, "completed_steps": set(), "recovery_tick": None}


def _now():
    return datetime.now().isoformat()


def get_entity(collection_name, entity_id):
    return next((item for item in mine_state.get(collection_name, []) if item.get("entity_id") == entity_id), None)


def create_propagation_step(sequence, source, target, cause, effect, impact_value, impact_unit):
    step = {
        "sequence": sequence,
        "timestamp": _now(),
        "source": source,
        "target": target,
        "cause": cause,
        "effect": effect,
        "impact_value": impact_value,
        "impact_unit": impact_unit,
    }
    causal_intelligence["propagation_chain"].append(step)
    return step


def _step_once(number, source, target, cause, effect, value, unit, severity="HIGH"):
    if number in _scenario["completed_steps"]:
        return
    _scenario["completed_steps"].add(number)
    create_propagation_step(number, source, target, cause, effect, value, unit)
    add_causal_event(cause, effect, target, severity)


def _trigger_truck_brake_incident(tick):
    truck = get_entity("trucks", "T14")
    route = get_entity("routes", "R1")
    if not truck or not route:
        return

    truck["brake_health"] = 38.0
    truck["health_score"] = round((truck["engine_health"] + truck["brake_health"] + truck["tire_health"] + truck["hydraulic_health"]) / 4)
    route["risk_score"] = 34
    route["status"] = "ELEVATED_RISK"
    mine_state["mine"]["status"] = "AT_RISK"

    causal_intelligence["active_incident"] = {
        "incident_id": "INC-FLEET-001",
        "timestamp": _now(),
        "entity": "T14",
        "entity_name": "Haul Truck T14",
        "incident_type": "BRAKE_HEALTH_DEGRADATION",
        "severity": "HIGH",
        "status": "PROPAGATING",
        "detected_value": 38,
        "current_value": 38,
        "threshold": 45,
    }
    causal_intelligence["engine_status"] = "ANALYZING"
    _scenario["triggered"] = True
    _scenario["trigger_tick"] = tick
    _step_once(1, "T14", "T14", "T14 brake health crossed preventive threshold", "Truck reliability risk increased", 38, "HEALTH_PERCENT")


def process_fleet_tick(tick):
    """Deterministic Phase-2 scenario driven by the canonical fleet clock."""
    with _lock:
        if not _scenario["triggered"] and tick >= 18:
            _trigger_truck_brake_incident(tick)

        if not _scenario["triggered"]:
            causal_intelligence["engine_status"] = "MONITORING"
            return

        elapsed = tick - _scenario["trigger_tick"]
        route = get_entity("routes", "R1")
        operations = mine_state["operations"]
        incident = causal_intelligence["active_incident"]

        if incident and incident.get("status") == "RECOVERING":
            # Recovery timing starts on the first fleet tick after the intervention,
            # never from the original incident trigger tick.
            if _scenario["recovery_tick"] is None:
                _scenario["recovery_tick"] = tick
            recovery_elapsed = tick - _scenario["recovery_tick"]
            operations["production_rate"] = 920
            operations["truck_queue"] = 2
            operations["dispatch_risk"] = 18
            operations["predicted_loss"] = 28.0
            if route:
                route["risk_score"] = 20
                route["status"] = "RECOVERING"
            gate = get_entity("dispatch_gates", "D1")
            if gate:
                gate["delay_risk"] = 18
                gate["status"] = "RECOVERING"
            if recovery_elapsed >= 10:
                incident["status"] = "RESOLVED"
                causal_intelligence["engine_status"] = "MONITORING"
                mine_state["mine"]["status"] = "NORMAL"
                operations["dispatch_risk"] = 6
                operations["predicted_loss"] = 0
                if route:
                    route["risk_score"] = 12
                    route["status"] = "NORMAL"
                if gate:
                    gate["delay_risk"] = 6
                    gate["status"] = "OPEN"
                add_causal_event("Fleet intervention recovery completed", "Mine operation returned to monitored normal state", "MINE-01", "INFO")
            return

        if incident and incident.get("status") == "RESOLVED":
            return

        if elapsed >= 2:
            route["risk_score"] = 52
            route["status"] = "RESTRICTED"
            _step_once(2, "T14", "R1", "Brake degradation requires reduced haul speed", "North Haul Road capacity reduced", 52, "RISK_SCORE")

        if elapsed >= 4:
            operations["truck_queue"] = max(operations.get("truck_queue", 0), 4)
            _step_once(3, "R1", "FLEET", "North Haul Road capacity reduced", "Fleet queue pressure increased", operations["truck_queue"], "TRUCKS")

        if elapsed >= 6:
            normal = operations.get("target_production_rate", 1000)
            operations["production_rate"] = min(operations.get("production_rate", normal), 720)
            drop = round((normal - operations["production_rate"]) / normal * 100, 1)
            _step_once(4, "FLEET", "MINE_PRODUCTION", "Fleet queue pressure propagated downstream", "Mine production rate reduced", drop, "PERCENT", "CRITICAL")

        if elapsed >= 8:
            operations["dispatch_risk"] = 68.0
            operations["predicted_loss"] = 140.0
            gate = get_entity("dispatch_gates", "D1")
            if gate:
                gate["delay_risk"] = 68.0
                gate["status"] = "AT_RISK"
            _step_once(5, "MINE_PRODUCTION", "D1", "Production degradation reduced dispatch buffer", "Dispatch SLA is at risk", 68.0, "RISK_SCORE", "CRITICAL")
            causal_intelligence["predictions"] = [{
                "prediction_id": "PRED-FLEET-001",
                "timestamp": _now(),
                "prediction_type": "PRODUCTION_LOSS",
                "prediction_horizon_minutes": 30,
                "message": "If T14 remains in the active haul cycle, MineMind predicts 140 MT of production loss in 30 minutes.",
                "predicted_loss_mt": 140.0,
                "dispatch_delay_risk": 68.0,
                "confidence": 92,
            }]
            causal_intelligence["recommendations"] = [{
                "recommendation_id": "REC-FLEET-001",
                "timestamp": _now(),
                "title": "Isolate T14 and Rebalance Fleet",
                "problem": "T14 brake degradation is reducing R1 capacity and propagating queue pressure into production and dispatch.",
                "recommended_actions": ["Remove T14 from active haulage", "Move T14 to preventive maintenance", "Rebalance healthy trucks across R1 and R2", "Restore dispatch buffer"],
                "expected_result": {"queue_reduction": 2, "production_recovery_percentage": 25, "dispatch_risk_reduction_percentage": 50, "estimated_ore_loss_avoided_mt": 112.0},
                "confidence": 92,
                "decision_status": "PENDING",
            }]
            incident["status"] = "DECISION_REQUIRED"
            causal_intelligence["engine_status"] = "DECISION_READY"


def mark_incident_recovering():
    with _lock:
        incident = causal_intelligence.get("active_incident")
        if incident:
            incident["status"] = "RECOVERING"
        _scenario["recovery_tick"] = None
        causal_intelligence["engine_status"] = "INTERVENTION_ACTIVE"


def resolve_active_incident():
    with _lock:
        incident = causal_intelligence.get("active_incident")
        if incident:
            incident["status"] = "RESOLVED"
        causal_intelligence["engine_status"] = "MONITORING"


def start_crusher_anomaly():
    return {"status": "LEGACY_SCENARIO_DISABLED", "scenario": "FLEET_DRIVEN_INCIDENT"}


def reset_causal_state():
    with _lock:
        causal_intelligence.update({"engine_status": "READY", "active_incident": None, "predictions": [], "recommendations": [], "propagation_chain": []})
        _scenario["triggered"] = False
        _scenario["trigger_tick"] = None
        _scenario["completed_steps"] = set()
        _scenario["recovery_tick"] = None
    return {"status": "CAUSAL_STATE_RESET"}


def get_causal_state():
    return causal_intelligence
