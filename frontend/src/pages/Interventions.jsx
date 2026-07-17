import { useEffect, useState } from "react";
import {apiFetch} from "../api";

const API = "http://127.0.0.1:8000";

export default function Interventions() {
  const [data, setData] = useState(null);
  const [error, setError] = useState("");

  useEffect(() => {
    let alive = true;
    const load = async () => {
      try {
        const response = await apiFetch(`/interventions/state`);
        if (!response.ok) throw new Error("Intervention API unavailable");
        const json = await response.json();
        if (alive) { setData(json); setError(""); }
      } catch (e) { if (alive) setError(e.message); }
    };
    load();
    const timer = setInterval(load, 1000);
    return () => { alive = false; clearInterval(timer); };
  }, []);

  const active = data?.active_intervention;
  const history = data?.history || [];

  return (
    <div className="interventions-page">
      <header className="interventions-header">
        <div><p>MINEMIND PLATFORM</p><h1>Interventions</h1><span>Operational intervention execution and tracking</span></div>
        <div className="interventions-live"><i></i> LIVE EXECUTION TRACKER</div>
      </header>

      {error && <div className="interventions-error">{error}</div>}

      <section className="intervention-summary">
        <div><span>ENGINE STATUS</span><strong>{data?.status || "READY"}</strong><small>Decision execution state</small></div>
        <div><span>ACTIVE ACTION</span><strong>{active ? "1" : "0"}</strong><small>Live intervention</small></div>
        <div><span>LOSS AVOIDED</span><strong>{active?.avoided_loss_mt ?? 0} MT</strong><small>Predicted operational recovery</small></div>
        <div><span>PRODUCTION</span><strong>{active?.production_rate_mt_h ?? 0} MT/H</strong><small>Post-intervention state</small></div>
      </section>

      {!active ? (
        <section className="intervention-empty">
          <span className="eyebrow">AWAITING EXECUTION</span>
          <h2>No intervention executed</h2>
          <p>Open Decision Engine and execute the optimal MineMind recommendation. The intervention will appear here automatically.</p>
        </section>
      ) : (
        <div className="intervention-layout">
          <section className="intervention-active">
            <span className="eyebrow">ACTIVE INTERVENTION</span>
            <div className="intervention-title-row"><div><h2>{active.title}</h2><p>{active.action}</p></div><b>{active.status}</b></div>
            <div className="execution-flow">
              <div><span>01</span><strong>DECISION ACCEPTED</strong><small>Optimal counterfactual selected</small></div>
              <i>→</i>
              <div><span>02</span><strong>TRUCKS REROUTED</strong><small>{active.rerouted_trucks?.join(", ") || "—"} redirected to {active.target_entity}</small></div>
              <i>→</i>
              <div><span>03</span><strong>MINE RECOVERING</strong><small>Live operational state updated</small></div>
            </div>
            <div className="intervention-impact">
              <div><span>DISPATCH RISK</span><strong>{active.dispatch_risk}%</strong></div>
              <div><span>TRUCK QUEUE</span><strong>{active.truck_queue}</strong></div>
              <div><span>PREDICTED LOSS</span><strong>{active.predicted_loss_mt} MT</strong></div>
              <div><span>LOSS AVOIDED</span><strong>{active.avoided_loss_mt} MT</strong></div>
            </div>
          </section>

          <aside className="intervention-log">
            <span className="eyebrow">EXECUTION LOG</span><h2>Intervention History</h2>
            {history.slice().reverse().map((item) => (
              <article key={`${item.intervention_id}-${item.timestamp}`}>
                <div><strong>{item.intervention_id}</strong><b>{item.status}</b></div>
                <h3>{item.title}</h3>
                <p>{new Date(item.timestamp).toLocaleString()}</p>
                <small>{item.rerouted_trucks?.join(", ")} → {item.target_entity}</small>
              </article>
            ))}
          </aside>
        </div>
      )}
    </div>
  );
}