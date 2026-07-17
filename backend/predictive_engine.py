from datetime import datetime

from mine_state import get_mine_state


# ============================================================
# MINEMIND PREDICTIVE ANALYTICS ENGINE
# ============================================================

MODEL_VERSION = "MineMind-Risk-v1.0"


def clamp(value, minimum=0, maximum=100):
    return max(minimum, min(maximum, value))


def get_trucks(state):
    return state.get("trucks", [])


def get_routes(state):
    return state.get("routes", [])


def get_crushers(state):
    return state.get("crushers", [])


def find_crusher(state, entity_id):
    for crusher in get_crushers(state):
        if crusher.get("entity_id") == entity_id:
            return crusher

    return {}


def calculate_operational_features(state):
    trucks = get_trucks(state)
    routes = get_routes(state)
    crushers = get_crushers(state)

    active_trucks = [
        truck
        for truck in trucks
        if truck.get("status") not in ["IDLE", "MAINTENANCE"]
    ]

    queue_count = len([
        truck
        for truck in trucks
        if truck.get("status") in ["WAITING", "QUEUED", "LOADING", "DUMPING"]
    ])

    average_truck_health = (
        sum(truck.get("health_score", 100) for truck in trucks) / len(trucks)
        if trucks
        else 100
    )

    minimum_truck_health = min(
        [truck.get("health_score", 100) for truck in trucks],
        default=100,
    )

    maximum_route_risk = max(
        [route.get("risk_score", 0) for route in routes],
        default=0,
    )

    average_route_risk = (
        sum(route.get("risk_score", 0) for route in routes) / len(routes)
        if routes
        else 0
    )

    maximum_vibration = max(
        [crusher.get("vibration", 0) for crusher in crushers],
        default=0,
    )

    maximum_temperature = max(
        [crusher.get("temperature", 0) for crusher in crushers],
        default=0,
    )

    minimum_crusher_health = min(
        [crusher.get("health_score", 100) for crusher in crushers],
        default=100,
    )

    production_rate = state.get("operations", {}).get("production_rate", 0)

    return {
        "production_rate": production_rate,
        "active_trucks": len(active_trucks),
        "queue_count": queue_count,
        "average_truck_health": round(average_truck_health, 2),
        "minimum_truck_health": minimum_truck_health,
        "maximum_route_risk": maximum_route_risk,
        "average_route_risk": round(average_route_risk, 2),
        "maximum_vibration": maximum_vibration,
        "maximum_temperature": maximum_temperature,
        "minimum_crusher_health": minimum_crusher_health,
    }


def calculate_crusher_risk(state, features):
    primary_crusher = find_crusher(state, "C1")

    vibration = primary_crusher.get("vibration", 0)
    temperature = primary_crusher.get("temperature", 0)
    health = primary_crusher.get("health_score", 100)

    vibration_risk = max(0, vibration - 30) * 2.2
    temperature_risk = max(0, temperature - 50) * 1.4
    health_risk = max(0, 100 - health) * 1.1

    probability = clamp(
        vibration_risk
        + temperature_risk
        + health_risk
    )

    predicted_loss = round(
        probability * 1.45,
        1,
    )

    return {
        "prediction_id": "PRED-CRUSHER-001",
        "risk_type": "CRUSHER_DEGRADATION",
        "title": "Primary Crusher Degradation",
        "affected_asset": "C1",
        "asset_name": primary_crusher.get(
            "name",
            "Primary Crusher",
        ),
        "probability": round(probability, 1),
        "severity": get_severity(probability),
        "forecast_horizon": "15 MIN",
        "current_signal": {
            "vibration": vibration,
            "temperature": temperature,
            "health_score": health,
        },
        "predicted_impact": {
            "production_loss_mt": predicted_loss,
            "production_rate_mt_h": features["production_rate"],
        },
        "reason": (
            "Crusher vibration, temperature and health signals "
            "indicate increasing operational degradation."
        ),
    }


def calculate_dispatch_risk(state, features):
    route_risk = features["maximum_route_risk"]
    queue_count = features["queue_count"]
    active_trucks = features["active_trucks"]

    probability = clamp(
        (route_risk * 0.75)
        + (queue_count * 7)
        + max(0, 4 - active_trucks) * 8
    )

    predicted_delay = round(
        probability * 0.42,
        1,
    )

    return {
        "prediction_id": "PRED-DISPATCH-001",
        "risk_type": "DISPATCH_DELAY",
        "title": "Dispatch Congestion Risk",
        "affected_asset": "HAUL_NETWORK",
        "asset_name": "Mine Haul Network",
        "probability": round(probability, 1),
        "severity": get_severity(probability),
        "forecast_horizon": "20 MIN",
        "current_signal": {
            "maximum_route_risk": route_risk,
            "truck_queue": queue_count,
            "active_trucks": active_trucks,
        },
        "predicted_impact": {
            "delay_minutes": predicted_delay,
            "production_loss_mt": round(
                probability * 0.9,
                1,
            ),
        },
        "reason": (
            "Route risk and truck queue conditions indicate "
            "possible dispatch congestion."
        ),
    }


def calculate_truck_failure_risk(state, features):
    trucks = get_trucks(state)

    if not trucks:
        return {
            "prediction_id": "PRED-TRUCK-001",
            "risk_type": "TRUCK_FAILURE",
            "title": "Truck Reliability Risk",
            "affected_asset": None,
            "asset_name": "No Truck Data",
            "probability": 0,
            "severity": "LOW",
            "forecast_horizon": "60 MIN",
            "current_signal": {},
            "predicted_impact": {
                "downtime_minutes": 0,
                "production_loss_mt": 0,
            },
            "reason": "No truck telemetry available.",
        }

    weakest_truck = min(
        trucks,
        key=lambda truck: truck.get("health_score", 100),
    )

    health = weakest_truck.get("health_score", 100)
    fuel = weakest_truck.get("fuel", 100)
    speed = weakest_truck.get("speed", 0)

    probability = clamp(
        ((100 - health) * 1.6)
        + max(0, 25 - fuel) * 1.2
        + (10 if speed == 0 else 0)
    )

    return {
        "prediction_id": "PRED-TRUCK-001",
        "risk_type": "TRUCK_FAILURE",
        "title": "Truck Reliability Risk",
        "affected_asset": weakest_truck.get("entity_id"),
        "asset_name": weakest_truck.get(
            "entity_id",
            "Truck",
        ),
        "probability": round(probability, 1),
        "severity": get_severity(probability),
        "forecast_horizon": "60 MIN",
        "current_signal": {
            "health_score": health,
            "fuel": fuel,
            "speed": speed,
            "status": weakest_truck.get("status"),
        },
        "predicted_impact": {
            "downtime_minutes": round(
                probability * 0.55,
                1,
            ),
            "production_loss_mt": round(
                probability * 0.65,
                1,
            ),
        },
        "reason": (
            "Truck health, fuel and operating state indicate "
            "potential reliability degradation."
        ),
    }


def calculate_production_loss_risk(state, features):
    production = features["production_rate"]
    queue = features["queue_count"]
    crusher_health = features["minimum_crusher_health"]
    route_risk = features["maximum_route_risk"]

    production_deficit = max(
        0,
        950 - production,
    )

    probability = clamp(
        (production_deficit / 5)
        + (queue * 5)
        + ((100 - crusher_health) * 0.7)
        + (route_risk * 0.25)
    )

    predicted_loss = round(
        probability * 1.5,
        1,
    )

    return {
        "prediction_id": "PRED-PRODUCTION-001",
        "risk_type": "PRODUCTION_LOSS",
        "title": "Production Loss Forecast",
        "affected_asset": "MINE_SYSTEM",
        "asset_name": "Mine Production System",
        "probability": round(probability, 1),
        "severity": get_severity(probability),
        "forecast_horizon": "30 MIN",
        "current_signal": {
            "production_rate": production,
            "truck_queue": queue,
            "crusher_health": crusher_health,
            "maximum_route_risk": route_risk,
        },
        "predicted_impact": {
            "production_loss_mt": predicted_loss,
            "forecast_production_mt_h": max(
                0,
                round(
                    production - predicted_loss,
                    1,
                ),
            ),
        },
        "reason": (
            "Production rate, queue pressure, crusher health "
            "and route risk indicate possible output loss."
        ),
    }


def get_severity(probability):
    if probability >= 75:
        return "CRITICAL"

    if probability >= 50:
        return "HIGH"

    if probability >= 25:
        return "MEDIUM"

    return "LOW"


def calculate_predictive_state():
    state = get_mine_state()

    features = calculate_operational_features(state)

    predictions = [
        calculate_production_loss_risk(
            state,
            features,
        ),
        calculate_crusher_risk(
            state,
            features,
        ),
        calculate_dispatch_risk(
            state,
            features,
        ),
        calculate_truck_failure_risk(
            state,
            features,
        ),
    ]

    predictions = sorted(
        predictions,
        key=lambda prediction: prediction["probability"],
        reverse=True,
    )

    critical_predictions = len([
        prediction
        for prediction in predictions
        if prediction["severity"] == "CRITICAL"
    ])

    high_predictions = len([
        prediction
        for prediction in predictions
        if prediction["severity"] == "HIGH"
    ])

    highest_risk = (
        predictions[0]
        if predictions
        else None
    )

    system_risk = (
        round(
            sum(
                prediction["probability"]
                for prediction in predictions
            ) / len(predictions),
            1,
        )
        if predictions
        else 0
    )

    return {
        "engine_status": "PREDICTING",
        "model": MODEL_VERSION,
        "generated_at": datetime.now().isoformat(),
        "summary": {
            "system_risk": system_risk,
            "active_predictions": len(predictions),
            "critical_predictions": critical_predictions,
            "high_predictions": high_predictions,
            "highest_risk": (
                highest_risk["risk_type"]
                if highest_risk
                else None
            ),
        },
        "features": features,
        "predictions": predictions,
    }


def get_predictive_state():
    return calculate_predictive_state()