import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import {apiFetch} from "../api";

const API = "http://127.0.0.1:8000";

export default function CausalIntelligence() {
  const navigate = useNavigate();
  const [twin, setTwin] = useState(null);
  const [causal, setCausal] = useState(null);
  const [counterfactual, setCounterfactual] = useState(null);

  useEffect(() => {
    const loadData = async () => {
      try {
        const [twinResponse, causalResponse, counterfactualResponse] =
          await Promise.all([
            apiFetch(`/twin/state`),
            apiFetch(`/causal/state`),
            apiFetch(`/counterfactual/state`),
          ]);

        const twinData = await twinResponse.json();
        const causalData = await causalResponse.json();
        const counterfactualData =
          await counterfactualResponse.json();

        setTwin(twinData);
        setCausal(causalData);
        setCounterfactual(counterfactualData);
      } catch (error) {
        console.error("MineMind causal fetch error:", error);
      }
    };

    loadData();

    const interval = setInterval(loadData, 1000);

    return () => clearInterval(interval);
  }, []);

  if (!twin || !causal || !counterfactual) {
    return (
      <div className="causal-page">
        <div className="causal-loading">
          MINE MIND CAUSAL ENGINE CONNECTING...
        </div>
      </div>
    );
  }

  const operations = twin.operations || {};

  const production = operations.production_rate || 0;
  const activeTrucks = operations.active_trucks || 0;
  const queue = operations.truck_queue || 0;
  const dispatchRisk = operations.dispatch_risk ?? 0;
  const predictedLoss = operations.predicted_loss ?? 0;

  const causalStatus = causal.engine_status || "READY";

  const confidence = causal.predictions?.[0]?.confidence
    ? `${causal.predictions[0].confidence}%`
    : "—";

  const detectedCause =
    causal.active_incident?.incident_type || "NO ACTIVE INCIDENT";

  const causeDescription = causal.active_incident
    ? `${causal.active_incident.entity_name || causal.active_incident.entity} value ${causal.active_incident.current_value} crossed threshold ${causal.active_incident.threshold}.`
    : "MineMind is monitoring live operational telemetry.";

  const propagation =
    causal.propagation_chain?.at(-1)?.effect ||
    "Waiting for causal propagation.";

 const rawScenarios =
  counterfactual?.scenarios ||
  counterfactual?.counterfactuals ||
  counterfactual?.results ||
  [];

const scenarios = Array.isArray(rawScenarios)
  ? rawScenarios
  : [];

  const recommendation =
  counterfactual?.recommendation?.action ||
  counterfactual?.recommendation ||
  counterfactual?.optimal_action?.action ||
  counterfactual?.optimal_action ||
  "Reroute Trucks to C2";

  return (
    <div className="causal-page">
      <header className="causal-header">
        <div>
          <div className="causal-eyebrow">
            MINEMIND PLATFORM
          </div>

          <h1>Causal Intelligence</h1>

          <p>
            Live root-cause analysis and counterfactual
            decision intelligence
          </p>
        </div>

        <div className="causal-live">
          <span />
          CAUSAL PROPAGATION ACTIVE
        </div>
      </header>

      <section className="causal-metrics">
        <Metric
          label="Production"
          value={`${production} MT/H`}
        />

        <Metric
          label="Active Trucks"
          value={activeTrucks}
        />

        <Metric
          label="Truck Queue"
          value={queue}
        />

        <Metric
          label="Dispatch Risk"
          value={`${dispatchRisk}%`}
          danger={dispatchRisk >= 50}
        />

        <Metric
          label="Predicted Loss"
          value={`${predictedLoss} MT`}
          danger={predictedLoss > 0}
        />
      </section>

      <div className="causal-layout">
        <section className="causal-card causal-chain-card">
          <div className="card-top-row">
            <div>
              <div className="section-label">
                CAUSAL INTELLIGENCE
              </div>

              <h2>Live Causal Chain</h2>
            </div>

            <div className="decision-badge">
              {causalStatus}
            </div>
          </div>

          <div className="confidence-row">
            <span>INFERENCE CONFIDENCE</span>

            <strong>{confidence}</strong>
          </div>

          <div className="causal-step danger-step">
            <div className="step-number">01</div>

            <div className="step-content">
              <span>DETECTED CAUSE</span>

              <h3>{detectedCause}</h3>

              <p>{causeDescription}</p>
            </div>
          </div>

          <div className="causal-arrow">↓</div>

          <div className="causal-step">
            <div className="step-number">02</div>

            <div className="step-content">
              <span>CAUSAL PROPAGATION</span>

              <h3>{propagation}</h3>

              <p>
                MineMind is tracing downstream operational
                effects across trucks, routes and crushers.
              </p>
            </div>
          </div>

          <div className="causal-arrow">↓</div>

          <div className="causal-step impact-step">
            <div className="step-number">03</div>

            <div className="step-content">
              <span>OPERATIONAL IMPACT</span>

              <h3>{predictedLoss} MT predicted loss</h3>

              <p>
                Dispatch risk has reached {dispatchRisk}% with
                a live truck queue of {queue}.
              </p>
            </div>
          </div>
        </section>

        <section className="causal-card decision-card">
          <div className="section-label">
            COUNTERFACTUAL DECISION ENGINE
          </div>

          <h2>What Should The Mine Do Next?</h2>

          <p className="decision-subtitle">
            MineMind compares simulated operational futures
            before recommending an intervention.
          </p>

          <div className="scenario-list">
            {scenarios.length > 0 ? (
              scenarios.map((scenario, index) => (
                <Scenario
                  key={
                    scenario.id ||
                    scenario.name ||
                    index
                  }
                  index={index}
                  scenario={scenario}
                />
              ))
            ) : (
              <>
                <Scenario
                  index={0}
                  scenario={{
                    name: "Continue Operation",
                    description:
                      "Continue current mine operation without intervention.",
                    predicted_loss: predictedLoss,
                    dispatch_risk: dispatchRisk,
                    production,
                    queue,
                  }}
                />

                <Scenario
                  index={1}
                  scenario={{
                    name: "Reduce Crusher Load",
                    description:
                      "Reduce Primary Crusher load to stabilize vibration.",
                    predicted_loss: 62,
                    dispatch_risk: 31,
                    production: 820,
                    queue: 4,
                    loss_avoided: 83,
                  }}
                />

                <Scenario
                  index={2}
                  recommended
                  scenario={{
                    name: "Reroute Trucks to C2",
                    description:
                      "Temporarily reroute eligible trucks to Secondary Crusher.",
                    predicted_loss: 24,
                    dispatch_risk: 12,
                    production: 930,
                    queue: 2,
                    loss_avoided: 121,
                  }}
                />
              </>
            )}
          </div>

          <div className="optimal-action">
            <span>MINEMIND OPTIMAL ACTION</span>

           <h3>
  {typeof recommendation === "string"
    ? recommendation
    : recommendation?.name ||
      recommendation?.action ||
      "Reroute Trucks to C2"}
</h3>

            <p>
              Selected using causal inference and
              counterfactual operational simulation.
            </p>

            <button type="button" onClick={() => navigate("/interventions")}>
              REVIEW INTERVENTION →
            </button>
          </div>
        </section>
      </div>
    </div>
  );
}

function Metric({ label, value, danger = false }) {
  return (
    <div className="causal-metric">
      <span>{label}</span>

      <strong className={danger ? "metric-danger" : ""}>
        {value}
      </strong>
    </div>
  );
}

function Scenario({
  scenario,
  index,
  recommended = false,
}) {
  const name =
    scenario.name ||
    scenario.action ||
    scenario.title ||
    `Scenario ${index + 1}`;

  const description =
    scenario.description ||
    scenario.explanation ||
    "";

  const loss =
    scenario.predicted_loss ??
    scenario.predicted_loss_mt ??
    0;

  const risk =
    scenario.dispatch_risk ??
    scenario.dispatch_delay_risk ??
    0;

  const production =
    scenario.production ??
    scenario.production_rate ??
    scenario.production_rate_mt_h ??
    0;

  const queue =
    scenario.queue ??
    scenario.truck_queue ??
    0;

  const avoided =
    scenario.loss_avoided ??
    scenario.loss_avoided_mt ??
    scenario.avoided_loss_mt ??
    0;

  const isRecommended =
    recommended ||
    scenario.recommended === true ||
    scenario.optimal === true ||
    scenario.scenario_id === "CF-003";

  return (
    <div
      className={`scenario-card ${
        isRecommended ? "recommended-scenario" : ""
      }`}
    >
      <div className="scenario-heading">
        <div>
          <span>
            SCENARIO {String(index + 1).padStart(2, "0")}
          </span>

          <h3>{name}</h3>
        </div>

        {isRecommended && (
          <div className="recommend-badge">
            MINEMIND RECOMMENDS
          </div>
        )}
      </div>

      <p>{description}</p>

      <div className="scenario-stats">
        <div>
          <span>PREDICTED LOSS</span>
          <strong>{loss} MT</strong>
        </div>

        <div>
          <span>DISPATCH RISK</span>
          <strong>{risk}%</strong>
        </div>

        <div>
          <span>PRODUCTION</span>
          <strong>{production} MT/H</strong>
        </div>

        <div>
          <span>QUEUE</span>
          <strong>{queue}</strong>
        </div>
      </div>

      <div className="loss-avoided">
        {avoided > 0
          ? `${avoided} MT LOSS AVOIDED`
          : "NO LOSS AVOIDED"}
      </div>
    </div>
  );
}