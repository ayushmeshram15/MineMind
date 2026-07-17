import { useCallback, useEffect, useState } from "react";
import {apiFetch} from "../api";

const API = "http://127.0.0.1:8000";

export default function CommandCenter() {
  const [twin, setTwin] = useState(null);
  const [causal, setCausal] = useState(null);
  const [simulation, setSimulation] = useState(null);
  const [error, setError] = useState("");
  const [streamAction, setStreamAction] = useState("");

  const loadData = useCallback(async () => {
    try {
      const [twinResponse, causalResponse, simulationResponse] = await Promise.all([
        apiFetch(`/twin/state`),
        apiFetch(`/causal/state`),
        apiFetch(`/simulation/state`),
      ]);
      if (!twinResponse.ok || !causalResponse.ok || !simulationResponse.ok) throw new Error("API request failed");
      const [twinData, causalData, simulationData] = await Promise.all([
        twinResponse.json(), causalResponse.json(), simulationResponse.json(),
      ]);
      setTwin(twinData);
      setCausal(causalData);
      setSimulation(simulationData);
      setError("");
    } catch (err) {
      console.error(err);
      setError("BACKEND CONNECTION LOST");
    }
  }, []);

  useEffect(() => {
    loadData();
    const interval = setInterval(loadData, 1000);
    return () => clearInterval(interval);
  }, [loadData]);

  async function simulationAction(path, pending, success) {
    try {
      setStreamAction(pending);
      const response = await apiFetch(`${path}`, { method: "POST" });
      if (!response.ok) throw new Error(`${path} failed`);
      setStreamAction(success);
      await loadData();
    } catch (err) {
      console.error(err);
      setStreamAction("ACTION FAILED");
    }
  }

  const startDemoStream = () => simulationAction("/simulation/start", "STARTING FLEET ENGINE...", "FLEET ENGINE ACTIVE");
  const pauseDemoStream = () => simulationAction("/simulation/pause", "PAUSING ENGINE...", "FLEET ENGINE PAUSED");
  const resumeDemoStream = () => simulationAction("/simulation/resume", "RESUMING ENGINE...", "FLEET ENGINE ACTIVE");
  const resetEnvironment = () => simulationAction("/simulation/reset", "RESETTING ENVIRONMENT...", "ENVIRONMENT RESET");

  if (error) return <div className="cc-error"><h2>{error}</h2><p>Check whether FastAPI is running on port 8000.</p></div>;
  if (!twin || !causal || !simulation) return <div className="cc-loading"><div className="cc-loader"></div><p>CONNECTING TO MINEMIND...</p></div>;

  const operations = twin.operations || {};
  const activeIncident = causal.active_incident;
  const prediction = causal.predictions?.[0];
  const production = operations.production_rate ?? 0;
  const activeTrucks = operations.active_trucks ?? 0;
  const truckQueue = operations.truck_queue ?? 0;
  const materialTransit = operations.material_in_transit ?? 0;
  const materialDispatched = operations.material_dispatched ?? 0;
  const traceability = operations.traceability_score ?? 0;
  const dispatchRisk = operations.dispatch_risk ?? prediction?.dispatch_delay_risk ?? 0;
  const predictedLoss = operations.predicted_loss ?? prediction?.predicted_loss_mt ?? 0;
  const confidence = prediction?.confidence ?? 0;
  const simulationStatus = simulation.status || "NOT_STARTED";
  const engineDotColor = simulationStatus === "RUNNING" ? "#21d890" : simulationStatus === "PAUSED" ? "#ffb020" : "#8b9ab8";

  return (
    <div className="cc-page">
      <header className="cc-header">
        <div><p className="cc-eyebrow">MINEMIND PLATFORM</p><h1>Command Center</h1><p className="cc-subtitle">Unified mine operations intelligence</p></div>
        <div className="cc-live"><span className="cc-live-dot" style={{ background: engineDotColor, boxShadow: `0 0 18px ${engineDotColor}` }}></span>{simulationStatus === "RUNNING" ? "LIVE OPERATIONS" : simulationStatus.replaceAll("_", " ")}</div>
      </header>

      <section className="cc-source-panel">
        <div><p className="cc-card-label">FLEET SIMULATION ENGINE</p><h2>Canonical Operational Stream</h2><p>One simulation clock drives truck movement, payload, fuel, health and production telemetry.</p></div>
        <div className="cc-source-actions">
          <span className="cc-stream-state"><span className="cc-live-dot" style={{ background: engineDotColor, boxShadow: `0 0 18px ${engineDotColor}` }}></span>{streamAction || `ENGINE ${simulationStatus} · T+${simulation.simulation_time_minutes || 0} MIN`}</span>
          <div>
            {simulationStatus === "NOT_STARTED" && <button className="cc-primary-button" onClick={startDemoStream}>START SIMULATION</button>}
            {simulationStatus === "RUNNING" && <button className="cc-primary-button" onClick={pauseDemoStream}>PAUSE SIMULATION</button>}
            {simulationStatus === "PAUSED" && <button className="cc-primary-button" onClick={resumeDemoStream}>RESUME SIMULATION</button>}
            <button className="cc-secondary-button" onClick={resetEnvironment}>RESET ENVIRONMENT</button>
          </div>
        </div>
      </section>

      <section className="cc-metrics">
        <Metric label="PRODUCTION" value={`${production} MT/H`} />
        <Metric label="ACTIVE TRUCKS" value={activeTrucks} />
        <Metric label="TRUCK QUEUE" value={truckQueue} />
        <Metric label="FLEET UTILIZATION" value={`${operations.fleet_utilization ?? 0}%`} />
        <Metric label="AVG FLEET HEALTH" value={`${operations.average_fleet_health ?? 0}%`} danger={(operations.average_fleet_health ?? 100) < 65} />
      </section>

      <section className="cc-content-grid">
        <article className="cc-card">
          <div className="cc-card-top"><div><p className="cc-card-label">ACTIVE INCIDENT</p><h2>{activeIncident ? activeIncident.incident_id : "NO ACTIVE INCIDENT"}</h2></div><span className={activeIncident ? "cc-status cc-status-danger" : "cc-status cc-status-normal"}>{activeIncident?.severity || "NORMAL"}</span></div>
          <p className="cc-card-description">{activeIncident ? `${activeIncident.entity_name || activeIncident.entity} — ${activeIncident.incident_type || "Operational anomaly"}` : "Mine operations are currently stable."}</p>
          {activeIncident && <div className="cc-incident-details"><div><span>ENTITY</span><strong>{activeIncident.entity_name || activeIncident.entity || "—"}</strong></div><div><span>CURRENT VALUE</span><strong>{activeIncident.current_value ?? "—"}</strong></div><div><span>THRESHOLD</span><strong>{activeIncident.threshold ?? "—"}</strong></div></div>}
        </article>

        <article className="cc-card cc-impact-card">
          <p className="cc-card-label">PREDICTED OPERATIONAL IMPACT</p><h2 className={predictedLoss > 0 ? "cc-danger-text" : ""}>{predictedLoss} MT LOSS</h2>
          <div className="cc-impact-list"><InfoRow label="Dispatch Delay Risk" value={`${dispatchRisk}%`} /><InfoRow label="Prediction Confidence" value={`${confidence}%`} /><InfoRow label="Fleet Trips" value={operations.fleet_trips_completed ?? 0} /></div>
        </article>
      </section>

      <section className="cc-bottom-card"><div><span>MATERIAL IN TRANSIT</span><strong>{materialTransit} MT</strong></div><div><span>MATERIAL MOVED</span><strong>{operations.fleet_material_moved ?? materialDispatched} MT</strong></div><div><span>TRACEABILITY</span><strong>{traceability}%</strong></div></section>
    </div>
  );
}

function Metric({ label, value, danger = false }) { return <div className="cc-metric"><span>{label}</span><strong className={danger ? "cc-danger-text" : ""}>{value}</strong></div>; }
function InfoRow({ label, value }) { return <div className="cc-info-row"><span>{label}</span><strong>{value}</strong></div>; }