import { useEffect, useState } from "react";
import "../index.css";
import {apiFetch} from "../api";

const API = "http://127.0.0.1:8000";

function severityClass(severity) {
  if (severity === "CRITICAL") return "prediction-critical";
  if (severity === "HIGH") return "prediction-high";
  if (severity === "MEDIUM") return "prediction-medium";

  return "prediction-low";
}

function PredictionCard({ prediction, index }) {
  const impact = prediction.predicted_impact || {};
  const signal = prediction.current_signal || {};

  return (
    <div
      className={`prediction-card ${severityClass(
        prediction.severity
      )}`}
    >
      <div className="prediction-top">
        <div>
          <div className="prediction-number">
            FORECAST {String(index + 1).padStart(2, "0")}
          </div>

          <h2>{prediction.title}</h2>

          <div className="prediction-asset">
            {prediction.asset_name}
          </div>
        </div>

        <div
          className={`severity-badge severity-${prediction.severity.toLowerCase()}`}
        >
          {prediction.severity}
        </div>
      </div>

      <div className="prediction-metrics">
        <div className="prediction-metric">
          <span>PROBABILITY</span>
          <strong>{prediction.probability}%</strong>
        </div>

        <div className="prediction-metric">
          <span>FORECAST HORIZON</span>
          <strong>{prediction.forecast_horizon}</strong>
        </div>

        <div className="prediction-metric">
          <span>PREDICTED LOSS</span>
          <strong>
            {impact.production_loss_mt ?? 0} MT
          </strong>
        </div>

        <div className="prediction-metric">
          <span>AFFECTED ASSET</span>
          <strong>
            {prediction.affected_asset || "SYSTEM"}
          </strong>
        </div>
      </div>

      <div className="prediction-reason">
        <span>PREDICTIVE SIGNAL</span>
        <p>{prediction.reason}</p>
      </div>

      <div className="signal-grid">
        {Object.entries(signal).map(([key, value]) => (
          <div className="signal-item" key={key}>
            <span>{key.replaceAll("_", " ")}</span>
            <strong>
              {value === null || value === undefined
                ? "N/A"
                : String(value)}
            </strong>
          </div>
        ))}
      </div>
    </div>
  );
}

export default function PredictiveAnalytics() {
  const [data, setData] = useState(null);
  const [backendOnline, setBackendOnline] = useState(true);

  async function loadPredictiveState() {
    try {
      const response = await fetch(
        `${API}/predictive/state`
      );

      if (!response.ok) {
        throw new Error("Predictive API failed");
      }

      const result = await response.json();

      setData(result);
      setBackendOnline(true);
    } catch (error) {
      console.error(
        "Predictive Analytics Error:",
        error
      );

      setBackendOnline(false);
    }
  }

  useEffect(() => {
    loadPredictiveState();

    const interval = setInterval(
      loadPredictiveState,
      2000
    );

    return () => clearInterval(interval);
  }, []);

  if (!data) {
    return (
      <main className="predictive-page">
        <div className="predictive-loading">
          {backendOnline
            ? "LOADING PREDICTIVE ENGINE..."
            : "PREDICTIVE BACKEND OFFLINE"}
        </div>
      </main>
    );
  }

  const summary = data.summary || {};
  const features = data.features || {};
  const predictions = data.predictions || [];

  return (
    <main className="predictive-page">
      <section className="predictive-header">
        <div>
          <div className="predictive-eyebrow">
            MINEMIND PLATFORM
          </div>

          <h1>Predictive Analytics</h1>

          <p>
            Production loss and operational risk forecasting
          </p>
        </div>

        <div className="predictive-status">
          <span className="predictive-status-dot" />

          <div>
            <strong>{data.engine_status}</strong>
            <small>{data.model}</small>
          </div>
        </div>
      </section>

      <section className="predictive-summary">
        <div className="predictive-summary-card">
          <span>SYSTEM RISK</span>
          <strong>{summary.system_risk ?? 0}%</strong>
          <small>Composite operational risk</small>
        </div>

        <div className="predictive-summary-card">
          <span>ACTIVE FORECASTS</span>
          <strong>
            {summary.active_predictions ?? 0}
          </strong>
          <small>Predictive signals active</small>
        </div>

        <div className="predictive-summary-card">
          <span>CRITICAL RISKS</span>
          <strong>
            {summary.critical_predictions ?? 0}
          </strong>
          <small>Immediate attention required</small>
        </div>

        <div className="predictive-summary-card">
          <span>HIGHEST RISK</span>
          <strong className="highest-risk-text">
            {(summary.highest_risk || "NONE").replaceAll(
              "_",
              " "
            )}
          </strong>
          <small>Top predicted operational threat</small>
        </div>
      </section>

      <section className="predictive-feature-panel">
        <div className="predictive-section-label">
          LIVE OPERATIONAL FEATURES
        </div>

        <h2>Prediction Inputs</h2>

        <div className="feature-grid">
          <div className="feature-box">
            <span>PRODUCTION</span>
            <strong>
              {features.production_rate ?? 0} MT/H
            </strong>
          </div>

          <div className="feature-box">
            <span>ACTIVE TRUCKS</span>
            <strong>
              {features.active_trucks ?? 0}
            </strong>
          </div>

          <div className="feature-box">
            <span>TRUCK QUEUE</span>
            <strong>
              {features.queue_count ?? 0}
            </strong>
          </div>

          <div className="feature-box">
            <span>MAX ROUTE RISK</span>
            <strong>
              {features.maximum_route_risk ?? 0}%
            </strong>
          </div>

          <div className="feature-box">
            <span>MAX VIBRATION</span>
            <strong>
              {features.maximum_vibration ?? 0}
            </strong>
          </div>

          <div className="feature-box">
            <span>MAX TEMPERATURE</span>
            <strong>
              {features.maximum_temperature ?? 0}°
            </strong>
          </div>

          <div className="feature-box">
            <span>MIN TRUCK HEALTH</span>
            <strong>
              {features.minimum_truck_health ?? 0}%
            </strong>
          </div>

          <div className="feature-box">
            <span>MIN CRUSHER HEALTH</span>
            <strong>
              {features.minimum_crusher_health ?? 0}%
            </strong>
          </div>
        </div>
      </section>

      <section className="forecast-section">
        <div className="predictive-section-label">
          AI RISK FORECAST
        </div>

        <h2>Operational Predictions</h2>

        <p className="forecast-description">
          MineMind continuously evaluates live digital twin
          telemetry to identify future operational risks.
        </p>

        <div className="prediction-list">
          {predictions.map((prediction, index) => (
            <PredictionCard
              key={prediction.prediction_id}
              prediction={prediction}
              index={index}
            />
          ))}
        </div>
      </section>
    </main>
  );
}