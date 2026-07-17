import { useEffect, useState } from "react";
import {apiFetch} from "../api";

const API = "http://127.0.0.1:8000";

export default function DecisionEngine() {
  const [data, setData] = useState(null);
  const [executing, setExecuting] = useState(false);
  const [error, setError] = useState("");

  const load = async () => {
    try {
      const response = await apiFetch(`/decision/state`);
      if (!response.ok) throw new Error("Decision API unavailable");
      setData(await response.json());
      setError("");
    } catch (err) {
      setError(err.message);
    }
  };

  useEffect(() => {
    load();
    const timer = setInterval(load, 1500);
    return () => clearInterval(timer);
  }, []);

  const execute = async () => {
    setExecuting(true);
    try {
      const response = await apiFetch(`/decision/execute`, { method: "POST" });
      if (!response.ok) throw new Error("Intervention execution failed");
      await response.json();
      await load();
    } catch (err) {
      setError(err.message);
    } finally {
      setExecuting(false);
    }
  };

  if (!data) return <div className="causal-loading">{error || "LOADING DECISION ENGINE"}</div>;

  const recommendation = data.recommendation;
  const executed = data.execution?.status === "EXECUTED";
  const active = data.execution?.active_intervention;

  return (
    <div className="decision-page">
      <header className="decision-header">
        <div>
          <p>MINEMIND PLATFORM</p>
          <h1>Decision Engine</h1>
          <span>Counterfactual scenario comparison and intervention selection</span>
        </div>
        <div className="decision-live"><i /> {executed ? "INTERVENTION EXECUTED" : data.engine_status}</div>
      </header>

      <section className="decision-summary">
        <div><span>INCIDENT</span><strong>{data.incident.incident_id}</strong><small>{data.incident.entity_name}</small></div>
        <div><span>SCENARIOS TESTED</span><strong>{data.scenarios.length}</strong><small>Counterfactual futures</small></div>
        <div><span>DECISION SCORE</span><strong>{recommendation.decision_score}</strong><small>Optimal action score</small></div>
        <div><span>CONFIDENCE</span><strong>{recommendation.confidence}%</strong><small>Decision confidence</small></div>
      </section>

      <div className="decision-layout">
        <section className="decision-panel">
          <span className="eyebrow">COUNTERFACTUAL RANKING</span>
          <h2>What should the mine do next?</h2>
          <div className="decision-table">
            {data.scenarios.map((scenario, index) => {
              const selected = scenario.scenario_id === recommendation.scenario_id;
              return (
                <div className={`decision-row ${selected ? "decision-row-best" : ""}`} key={scenario.scenario_id}>
                  <b>0{index + 1}</b>
                  <div><strong>{scenario.title}</strong><span>{scenario.action}</span></div>
                  <div><small>LOSS</small><strong>{scenario.predicted_loss_mt} MT</strong></div>
                  <div><small>RISK</small><strong>{scenario.dispatch_risk}%</strong></div>
                  <div><small>PRODUCTION</small><strong>{scenario.production_rate_mt_h} MT/H</strong></div>
                  <div><small>SCORE</small><strong>{scenario.decision_score}</strong></div>
                  {selected && <em>OPTIMAL</em>}
                </div>
              );
            })}
          </div>
        </section>

        <aside className="recommendation-panel">
          <span className="eyebrow">MINEMIND OPTIMAL ACTION</span>
          <h2>{recommendation.title}</h2>
          <p>{recommendation.reason}</p>
          <div className="impact-grid">
            <div><span>LOSS AVOIDED</span><strong>{recommendation.avoided_loss_mt} MT</strong></div>
            <div><span>DISPATCH RISK</span><strong>{recommendation.dispatch_risk}%</strong></div>
            <div><span>PREDICTED LOSS</span><strong>{recommendation.predicted_loss_mt} MT</strong></div>
            <div><span>CONFIDENCE</span><strong>{recommendation.confidence}%</strong></div>
          </div>
          <button className={executed ? "execute-button executed" : "execute-button"} onClick={execute} disabled={executed || executing}>
            {executed ? "✓ INTERVENTION EXECUTED" : executing ? "EXECUTING..." : "EXECUTE INTERVENTION →"}
          </button>
          {executed && active && <div className="execution-note">Trucks {active.rerouted_trucks.join(" + ")} rerouted to C2 · Twin updated to {active.production_rate_mt_h} MT/H</div>}
          {error && <div className="decision-error">{error}</div>}
        </aside>
      </div>
    </div>
  );
}