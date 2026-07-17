from datetime import datetime
from copy import deepcopy


def _now():
    return datetime.now().isoformat()


mine_state = {
    "timestamp": _now(),
    "mine": {"mine_id": "MINE-01", "name": "MineMind Demo Mine", "status": "NORMAL"},
    "pits": [
        {"entity_id": "P1", "name": "North Pit", "ore_grade": 63.2, "available_ore": 128540.0, "status": "ACTIVE", "position": {"x": -40, "y": 0, "z": -30}},
        {"entity_id": "P2", "name": "East Pit", "ore_grade": 58.7, "available_ore": 86420.0, "status": "ACTIVE", "position": {"x": 40, "y": 0, "z": -25}},
    ],
    "trucks": [
        {"entity_id": "T12", "status": "IDLE", "speed": 0, "fuel": 76, "payload": 0, "route_id": "R1", "batch_id": None, "health_score": 91, "data_confidence": 97, "position": {"x": -40, "y": 0, "z": -30}},
        {"entity_id": "T13", "status": "IDLE", "speed": 0, "fuel": 68, "payload": 0, "route_id": "R1", "batch_id": None, "health_score": 88, "data_confidence": 95, "position": {"x": -40, "y": 0, "z": -30}},
        {"entity_id": "T14", "status": "IDLE", "speed": 0, "fuel": 54, "payload": 0, "route_id": "R1", "batch_id": None, "health_score": 84, "data_confidence": 96, "position": {"x": -40, "y": 0, "z": -30}},
        {"entity_id": "T15", "status": "IDLE", "speed": 0, "fuel": 81, "payload": 0, "route_id": "R2", "batch_id": None, "health_score": 94, "data_confidence": 98, "position": {"x": 40, "y": 0, "z": -25}},
        {"entity_id": "T16", "status": "IDLE", "speed": 0, "fuel": 62, "payload": 0, "route_id": "R2", "batch_id": None, "health_score": 79, "data_confidence": 92, "position": {"x": 40, "y": 0, "z": -25}},
    ],
    "routes": [
        {"entity_id": "R1", "name": "North Haul Road", "risk_score": 12, "status": "NORMAL"},
        {"entity_id": "R2", "name": "East Haul Road", "risk_score": 8, "status": "NORMAL"},
    ],
    "crushers": [
        {"entity_id": "C1", "name": "Primary Crusher", "status": "RUNNING", "throughput": 0, "vibration": 42, "temperature": 61, "health_score": 92, "position": {"x": -6, "y": 0, "z": 30}},
        {"entity_id": "C2", "name": "Secondary Crusher", "status": "RUNNING", "throughput": 0, "vibration": 36, "temperature": 57, "health_score": 95, "position": {"x": 23, "y": 0, "z": 30}},
    ],
    "stockyards": [
        {"entity_id": "SY1", "name": "Central Stockyard", "inventory": 102780.0, "baseline_inventory": 102780.0, "live_inflow_mt": 0.0, "capacity_percentage": 77.9, "grade_fe": 61.2, "status": "ACTIVE", "position": {"x": 10, "y": 0, "z": 60}}
    ],
    "weighbridges": [{"entity_id": "WB1", "name": "Main Weighbridge", "status": "ONLINE", "current_weight": 0, "processed_today": 182, "position": {"x": 10, "y": 0, "z": 78}}],
    "dispatch_gates": [{"entity_id": "D1", "name": "Dispatch Gate", "status": "OPEN", "on_time_dispatch": 92.6, "delay_risk": 8, "position": {"x": 10, "y": 0, "z": 95}}],
    "ore_passports": {},
    "traceability": {"next_batch_number": 1, "batches_created": 0, "batches_stockpiled": 0, "traced_mass_mt": 0.0},
    "operations": {"production_rate": 0, "target_production_rate": 1000, "fleet_utilization": 0, "active_trucks": 0, "truck_queue": 0, "material_in_transit": 0, "material_dispatched": 0, "traceability_score": 100, "dispatch_risk": 0, "predicted_loss": 0},
    "causal_events": [],
}

INITIAL_MINE_STATE = deepcopy(mine_state)


def add_trace_event(batch_id, event, entity, stage, custody_owner, simulation_minute=None):
    passport = mine_state["ore_passports"].get(batch_id)
    if not passport:
        return
    passport["trace_events"].append({"timestamp": _now(), "simulation_minute": simulation_minute, "event": event, "entity": entity, "stage": stage, "custody_owner": custody_owner})
    passport.update({"current_stage": stage, "current_entity": entity, "custody_owner": custody_owner})
    mine_state["timestamp"] = _now()


def add_causal_event(cause, effect, entity, severity="INFO"):
    mine_state["causal_events"].append({"timestamp": _now(), "cause": cause, "effect": effect, "entity": entity, "severity": severity})
    mine_state["timestamp"] = _now()


def reset_mine_state():
    mine_state.clear()
    mine_state.update(deepcopy(INITIAL_MINE_STATE))
    mine_state["timestamp"] = _now()
    return {"status": "MINE_STATE_RESET"}


def get_mine_state():
    return mine_state
