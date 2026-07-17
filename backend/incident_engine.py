from datetime import datetime

from mine_state import mine_state
from causal_engine import get_causal_state
from intervention_engine import get_intervention_state
from predictive_engine import get_predictive_state


def _event_severity(event):
    return event.get("severity", "INFO")


def _build_operational_incidents():
    events = mine_state.get("causal_events", [])
    incidents = []

    for index, event in enumerate(reversed(events), start=1):
        severity = _event_severity(event)
        if severity not in {"WARNING", "HIGH", "CRITICAL"}:
            continue

        timestamp = event.get("timestamp", datetime.now().isoformat())
        incidents.append({
            "incident_id": f"EVT-{len(events) - index + 1:03d}",
            "timestamp": timestamp,
            "source_type": "DIGITAL_TWIN",
            "source_id": event.get("entity", "MINE-01"),
            "incident_type": "OPERATIONAL_EVENT",
            "title": event.get("cause", "Operational event detected"),
            "description": event.get("effect", "Mine state changed"),
            "severity": severity,
            "status": "RECORDED",
            "confidence": 100,
        })

    return incidents


def get_incident_history():
    causal = get_causal_state()
    intervention = get_intervention_state()
    predictive = get_predictive_state()

    incidents = _build_operational_incidents()
    active = causal.get("active_incident")

    if active:
        prediction = (causal.get("predictions") or [{}])[0]
        recommendation = (causal.get("recommendations") or [{}])[0]
        active_record = {
            "incident_id": active.get("incident_id", "INC-001"),
            "timestamp": active.get("timestamp", datetime.now().isoformat()),
            "source_type": "CAUSAL_ENGINE",
            "source_id": active.get("entity", "C1"),
            "incident_type": active.get("incident_type", "ANOMALY"),
            "title": f"{active.get('entity_name', 'Mine asset')} anomaly detected",
            "description": (
                f"{active.get('incident_type', 'Operational anomaly').replace('_', ' ')} "
                f"at {active.get('entity', 'asset')}. Current value "
                f"{active.get('current_value', 'N/A')} against threshold "
                f"{active.get('threshold', 'N/A')}."
            ),
            "severity": active.get("severity", "HIGH"),
            "status": active.get("status", "ACTIVE"),
            "confidence": prediction.get("confidence", 89),
            "predicted_impact": {
                "production_loss_mt": prediction.get("predicted_loss_mt", 0),
                "dispatch_delay_risk": prediction.get("dispatch_delay_risk", 0),
            },
            "recommendation": recommendation.get("title"),
            "causal_steps": len(causal.get("propagation_chain", [])),
        }
        incidents.insert(0, active_record)

    history = intervention.get("history", [])
    for item in reversed(history):
        incidents.insert(0, {
            "incident_id": item.get("intervention_id", "INT-001"),
            "timestamp": item.get("timestamp", datetime.now().isoformat()),
            "source_type": "INTERVENTION_ENGINE",
            "source_id": item.get("target_entity", "C2"),
            "incident_type": "AUTONOMOUS_INTERVENTION",
            "title": item.get("title", "MineMind intervention executed"),
            "description": (
                f"Action {item.get('action', 'UNKNOWN').replace('_', ' ')} executed. "
                f"Production restored to {item.get('production_rate_mt_h', 0)} MT/H "
                f"and dispatch risk reduced to {item.get('dispatch_risk', 0)}%."
            ),
            "severity": "INFO",
            "status": item.get("status", "EXECUTED"),
            "confidence": 100,
            "recovery_result": {
                "avoided_loss_mt": item.get("avoided_loss_mt", 0),
                "truck_queue": item.get("truck_queue", 0),
                "rerouted_trucks": item.get("rerouted_trucks", []),
            },
        })

    critical = sum(1 for item in incidents if item["severity"] == "CRITICAL")
    high = sum(1 for item in incidents if item["severity"] == "HIGH")
    warning = sum(1 for item in incidents if item["severity"] == "WARNING")

    return {
        "engine_status": "AUDIT_ACTIVE",
        "generated_at": datetime.now().isoformat(),
        "summary": {
            "total_incidents": len(incidents),
            "critical_incidents": critical,
            "high_incidents": high,
            "warning_incidents": warning,
            "interventions_executed": len(history),
            "current_system_risk": predictive.get("summary", {}).get("system_risk", 0),
        },
        "incidents": incidents,
    }
