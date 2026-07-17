import { Canvas } from "@react-three/fiber";
import { OrbitControls, Text, Line } from "@react-three/drei";
import { useEffect, useState } from "react";
import "./index.css";

const API = "http://127.0.0.1:8000";

function Pit({ position, name }) {
  return (
    <group position={position}>
      <mesh scale={[2.2, 0.35, 1.4]}>
        <sphereGeometry args={[1, 32, 32]} />
        <meshStandardMaterial color="#9b5427" />
      </mesh>

      <Text
        position={[0, 0.7, 0]}
        fontSize={0.35}
        color="white"
        anchorX="center"
      >
        {name}
      </Text>
    </group>
  );
}

function Crusher({ position, name, danger = false }) {
  return (
    <group position={position}>
      <mesh>
        <boxGeometry args={[1.8, 1.4, 1.8]} />
        <meshStandardMaterial color={danger ? "#ff3655" : "#617692"} />
      </mesh>

      <mesh position={[0, 1, 0]}>
        <coneGeometry args={[0.65, 1.2, 4]} />
        <meshStandardMaterial color={danger ? "#ff3655" : "#425772"} />
      </mesh>

      {danger && (
        <pointLight
          position={[0, 1, 0]}
          color="#ff3655"
          intensity={8}
          distance={7}
        />
      )}

      <Text
        position={[0, 2, 0]}
        fontSize={0.35}
        color="white"
        anchorX="center"
      >
        {name}
      </Text>

      <Text
        position={[0, 1.55, 0]}
        fontSize={0.22}
        color={danger ? "#ff3655" : "#42d392"}
        anchorX="center"
      >
        {danger ? "ABNORMAL VIBRATION" : "HEALTHY"}
      </Text>
    </group>
  );
}

function Truck({ position, name, danger = false }) {
  return (
    <group position={position}>
      <mesh>
        <boxGeometry args={[0.75, 0.35, 0.55]} />
        <meshStandardMaterial color={danger ? "#ff3655" : "#f5b51b"} />
      </mesh>

      <mesh position={[0.2, 0.28, 0]}>
        <boxGeometry args={[0.3, 0.25, 0.5]} />
        <meshStandardMaterial color="#ffd85c" />
      </mesh>

      <Text
        position={[0, 0.65, 0]}
        fontSize={0.22}
        color="white"
        anchorX="center"
      >
        {name}
      </Text>
    </group>
  );
}

function MineScene() {
  return (
    <>
      <ambientLight intensity={1.8} />
      <directionalLight position={[10, 15, 10]} intensity={2} />

      <gridHelper args={[35, 18, "#0d5a9a", "#0d5a9a"]} />

      <Pit position={[-6, 0.3, -5]} name="North Pit" />
      <Pit position={[7, 0.3, -5]} name="East Pit" />

      <Crusher
        position={[-2.5, 0.7, 0]}
        name="Primary Crusher"
        danger
      />

      <Crusher
        position={[3.5, 0.7, 0]}
        name="Secondary Crusher"
      />

      <Truck position={[-1.2, 0.4, -3]} name="T12" danger />
      <Truck position={[0.3, 0.4, -3]} name="T13" />
      <Truck position={[1.8, 0.4, -3]} name="T14" />
      <Truck position={[3.3, 0.4, -3]} name="T15" />
      <Truck position={[5, 0.4, -2]} name="T16" />

      <Line
        points={[
          [-2.5, 0.4, 0],
          [-0.5, 0.4, 1.5],
          [2, 0.4, 1.5],
          [3.5, 0.4, 0],
        ]}
        color="#ff3655"
        lineWidth={4}
        dashed
      />

      <OrbitControls
        enablePan
        enableZoom
        minDistance={8}
        maxDistance={30}
      />
    </>
  );
}

function Metric({ label, value, danger }) {
  return (
    <div className="metric">
      <span>{label}</span>
      <strong className={danger ? "danger-text" : ""}>{value}</strong>
    </div>
  );
}

function ScenarioCard({ scenario, recommended }) {
  return (
    <div className={`scenario-card ${recommended ? "recommended" : ""}`}>
      {recommended && <div className="best-badge">MINEMIND RECOMMENDS</div>}

      <div className="scenario-name">{scenario.title}</div>

      <div className="scenario-description">
        {scenario.description}
      </div>

      <div className="scenario-grid">
        <div>
          <span>PREDICTED LOSS</span>
          <strong>{scenario.predicted_loss_mt} MT</strong>
        </div>

        <div>
          <span>DISPATCH RISK</span>
          <strong>{scenario.dispatch_risk}%</strong>
        </div>

        <div>
          <span>PRODUCTION</span>
          <strong>{scenario.production_rate_mt_h} MT/H</strong>
        </div>

        <div>
          <span>QUEUE</span>
          <strong>{scenario.truck_queue}</strong>
        </div>
      </div>

      <div className="avoided-loss">
        {scenario.avoided_loss_mt > 0
          ? `${scenario.avoided_loss_mt} MT LOSS AVOIDED`
          : "NO LOSS AVOIDED"}
      </div>
    </div>
  );
}

export default function App() {
  const [causal, setCausal] = useState(null);
  const [counterfactual, setCounterfactual] = useState(null);
  const [error, setError] = useState("");

  useEffect(() => {
    const loadMineMind = async () => {
      try {
        const [causalResponse, counterfactualResponse] = await Promise.all([
          fetch(`${API}/causal/state`),
          fetch(`${API}/counterfactual/state`),
        ]);

        if (!causalResponse.ok || !counterfactualResponse.ok) {
          throw new Error("MineMind API request failed");
        }

        const causalData = await causalResponse.json();
        const counterfactualData = await counterfactualResponse.json();

        setCausal(causalData);
        setCounterfactual(counterfactualData);
        setError("");
      } catch (err) {
        console.error(err);
        setError("BACKEND CONNECTION LOST");
      }
    };

    loadMineMind();

    const interval = setInterval(loadMineMind, 3000);

    return () => clearInterval(interval);
  }, []);

  if (!causal || !counterfactual) {
    return (
      <div className="loading-screen">
        <h1>MINEMIND</h1>
        <p>{error || "INITIALIZING CAUSAL DIGITAL TWIN..."}</p>
      </div>
    );
  }

  const incident = causal.active_incident;
  const prediction = causal.predictions?.[0];

  const recommendation = counterfactual.recommendation;
  const scenarios = counterfactual.scenarios || [];

  return (
    <main className="app-shell">
      <header className="topbar">
        <div>
          <h1>MINEMIND</h1>
          <p>CAUSAL OPERATIONAL DIGITAL TWIN</p>
        </div>

        <div className="live-status">
          <span className="live-dot" />
          LIVE TWIN
        </div>
      </header>

      <section className="main-grid">
        <div className="twin-column">
          <div className="panel twin-panel">
            <div className="panel-heading">
              <span>LIVE OPERATIONAL GRAPH</span>
              <strong>CAUSAL PROPAGATION ACTIVE</strong>
            </div>

            <Canvas camera={{ position: [12, 11, 15], fov: 48 }}>
              <MineScene />
            </Canvas>
          </div>

          <div className="metrics">
            <Metric label="PRODUCTION" value="710 MT/H" danger />
            <Metric label="ACTIVE TRUCKS" value="4" />
            <Metric label="TRUCK QUEUE" value="7" danger />
            <Metric label="DISPATCH RISK" value="70.3%" danger />
            <Metric label="PREDICTED LOSS" value="145 MT" danger />
          </div>
        </div>

        <aside className="panel causal-panel">
          <div className="causal-header">
            <div>
              <span>CAUSAL INTELLIGENCE</span>
              <h2>{incident?.incident_id}</h2>
            </div>

            <strong>DECISION_READY</strong>
          </div>

          <div className="severity">HIGH</div>

          <div className="causal-step">
            <span>01 · DETECTED CAUSE</span>
            <h3>{incident?.entity_name} vibration</h3>
            <p>
              Sensor value {incident?.current_value} crossed the operational
              threshold of {incident?.threshold}.
            </p>
          </div>

          <div className="arrow">↓</div>

          <div className="causal-step">
            <span>02 · CAUSAL PROPAGATION</span>
            <h3>Operational bottleneck spreading</h3>
            <p>Crusher → Route → Fleet → Mine Production</p>
          </div>

          <div className="arrow">↓</div>

          <div className="causal-step impact-step">
            <span>03 · PREDICTED IMPACT</span>
            <h3>{prediction?.predicted_loss_mt || 145} MT LOSS</h3>
            <p>
              Dispatch delay risk{" "}
              {prediction?.dispatch_delay_risk || 70.3}%
            </p>
            <p>
              Prediction confidence {prediction?.confidence || 89}%
            </p>
          </div>
        </aside>
      </section>

      <section className="decision-section">
        <div className="decision-title">
          <div>
            <span>COUNTERFACTUAL DECISION ENGINE</span>
            <h2>WHAT SHOULD THE MINE DO NEXT?</h2>
          </div>

          <div className="engine-status">DECISION READY</div>
        </div>

        <div className="scenario-container">
          {scenarios.map((scenario) => (
            <ScenarioCard
              key={scenario.scenario_id}
              scenario={scenario}
              recommended={
                scenario.scenario_id === recommendation.scenario_id
              }
            />
          ))}
        </div>

        <div className="recommendation-panel">
          <div>
            <span>MINEMIND OPTIMAL ACTION</span>
            <h2>{recommendation.title}</h2>
            <p>{recommendation.reason}</p>
          </div>

          <div className="recommendation-stats">
            <div>
              <span>AVOIDED LOSS</span>
              <strong>{recommendation.avoided_loss_mt} MT</strong>
            </div>

            <div>
              <span>RESIDUAL RISK</span>
              <strong>{recommendation.dispatch_risk}%</strong>
            </div>

            <div>
              <span>CONFIDENCE</span>
              <strong>{recommendation.confidence}%</strong>
            </div>
          </div>
        </div>
      </section>
    </main>
  );
}