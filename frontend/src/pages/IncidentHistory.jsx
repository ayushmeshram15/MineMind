import { useEffect, useMemo, useState } from "react";
import "../index.css";
import {api} from "../api";

function label(value = "") {
  return String(value).replaceAll("_", " ");
}

function formatTime(value) {
  if (!value) return "N/A";
  return new Date(value).toLocaleString();
}

export default function IncidentHistory() {
  const [data, setData] = useState(null);
  const [filter, setFilter] = useState("ALL");
  const [online, setOnline] = useState(true);

  async function loadIncidents() {
    try {
      const [ops, vision] = await Promise.all([api("/incidents/state"), api("/vision/events")]);
      const visionEvents = vision.events || [];
      setData({...ops, incidents:[...(visionEvents), ...(ops.incidents || [])], summary:{...(ops.summary || {}), total_incidents:(ops.summary?.total_incidents || 0)+visionEvents.length}});
      setOnline(true);
    } catch (error) {
      console.error("Incident History Error:", error);
      setOnline(false);
    }
  }

  useEffect(() => {
    loadIncidents();
    const interval = setInterval(loadIncidents, 2000);
    return () => clearInterval(interval);
  }, []);

  const incidents = useMemo(() => {
    const list = data?.incidents || [];
    if (filter === "ALL") return list;
    return list.filter((item) => item.severity === filter);
  }, [data, filter]);

  if (!data) {
    return (
      <main className="incident-page">
        <div className="incident-loading">
          {online ? "LOADING INCIDENT AUDIT..." : "INCIDENT BACKEND OFFLINE"}
        </div>
      </main>
    );
  }

  const summary = data.summary || {};

  return (
    <main className="incident-page">
      <section className="incident-header">
        <div>
          <div className="incident-eyebrow">MINEMIND PLATFORM</div>
          <h1>Incident History</h1>
          <p>Operational anomaly, decision and intervention audit trail</p>
        </div>
        <div className="incident-engine-status">
          <span className="incident-live-dot" />
          <div><strong>{data.engine_status}</strong><small>LIVE AUDIT STREAM</small></div>
        </div>
      </section>

      <section className="incident-summary-grid">
        <div className="incident-summary-card"><span>TOTAL RECORDS</span><strong>{summary.total_incidents ?? 0}</strong><small>Auditable events</small></div>
        <div className="incident-summary-card"><span>CRITICAL</span><strong>{summary.critical_incidents ?? 0}</strong><small>Critical incidents</small></div>
        <div className="incident-summary-card"><span>HIGH</span><strong>{summary.high_incidents ?? 0}</strong><small>High severity</small></div>
        <div className="incident-summary-card"><span>INTERVENTIONS</span><strong>{summary.interventions_executed ?? 0}</strong><small>Actions executed</small></div>
        <div className="incident-summary-card"><span>SYSTEM RISK</span><strong>{summary.current_system_risk ?? 0}%</strong><small>Current predictive risk</small></div>
      </section>

      <section className="incident-audit-panel">
        <div className="incident-panel-top">
          <div><div className="incident-section-label">AUDIT LEDGER</div><h2>MineMind Event Timeline</h2></div>
          <div className="incident-filters">
            {["ALL", "CRITICAL", "HIGH", "WARNING", "INFO"].map((item) => (
              <button key={item} className={filter === item ? "active" : ""} onClick={() => setFilter(item)}>{item}</button>
            ))}
          </div>
        </div>

        <div className="incident-list">
          {incidents.length === 0 ? (
            <div className="incident-empty">NO INCIDENTS IN THIS FILTER</div>
          ) : incidents.map((incident) => (
            <article className={`incident-record incident-${incident.severity?.toLowerCase()}`} key={`${incident.incident_id || incident.event_id}-${incident.timestamp}`}>
              <div className="incident-record-top">
                <div>
                  <div className="incident-id">{incident.incident_id || incident.event_id} · {label(incident.source_type)}</div>
                  <h3>{incident.title}</h3>
                  <p>{incident.description}</p>
                </div>
                <span className={`incident-badge badge-${incident.severity?.toLowerCase()}`}>{incident.severity}</span>
              </div>

              <div className="incident-meta-grid">
                <div><span>SOURCE</span><strong>{incident.source_id || "SYSTEM"}</strong></div>
                <div><span>TYPE</span><strong>{label(incident.incident_type)}</strong></div>
                <div><span>STATUS</span><strong>{label(incident.status)}</strong></div>
                <div><span>CONFIDENCE</span><strong>{incident.confidence ?? 100}%</strong></div>
                <div><span>TIMESTAMP</span><strong>{formatTime(incident.timestamp)}</strong></div>
              </div>

              {incident.recommendation && <div className="incident-detail"><span>MINEMIND DECISION</span><strong>{incident.recommendation}</strong></div>}
              {incident.predicted_impact && <div className="incident-detail"><span>PREDICTED IMPACT</span><strong>{incident.predicted_impact.production_loss_mt ?? 0} MT loss · {incident.predicted_impact.dispatch_delay_risk ?? 0}% dispatch risk · {incident.causal_steps ?? 0} causal steps</strong></div>}
              {incident.recovery_result && <div className="incident-detail recovery"><span>RECOVERY RESULT</span><strong>{incident.recovery_result.avoided_loss_mt ?? 0} MT loss avoided · queue {incident.recovery_result.truck_queue ?? 0} · rerouted {(incident.recovery_result.rerouted_trucks || []).join(", ") || "N/A"}</strong></div>}
            </article>
          ))}
        </div>
      </section>
    </main>
  );
}
