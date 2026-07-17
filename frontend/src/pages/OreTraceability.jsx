import { useEffect, useState } from "react";
import {apiFetch} from "../api";

const API = "http://127.0.0.1:8000";

function OreTraceability() {
  const [state, setState] = useState(null);

  useEffect(() => {
    let active = true;

    const loadState = async () => {
      try {
        const response = await apiFetch(`/twin/state`);

        if (!response.ok) {
          throw new Error("Failed to load traceability state");
        }

        const data = await response.json();

        if (active) {
          setState(data);
        }
      } catch (error) {
        console.error("Ore traceability error:", error);
      }
    };

    loadState();

    const interval = setInterval(loadState, 1000);

    return () => {
      active = false;
      clearInterval(interval);
    };
  }, []);

  if (!state) {
    return (
      <div className="placeholder-page">
        <div className="placeholder-header">
          <p>MINEMIND PLATFORM</p>
          <h1>Ore Traceability</h1>
          <span>Connecting to digital ore passport engine...</span>
        </div>
      </div>
    );
  }

  const passports = Object.values(state.ore_passports || {});
  const operations = state.operations || {};

  const activeBatches = passports.filter((batch) => batch.status !== "STOCKPILED").length;

  const inTransit = passports.filter(
    (batch) =>
      batch.status === "IN_TRANSIT" || batch.status === "QUEUED" ||
      batch.current_stage === "HAULAGE"
  ).length;

  const completedBatches = passports.filter((batch) => batch.status === "STOCKPILED").length;

  const formatTime = (timestamp) => {
    if (!timestamp) return "--";

    return new Date(timestamp).toLocaleTimeString();
  };

  return (
    <div className="traceability-page">
      <div className="traceability-header">
        <div>
          <p className="traceability-eyebrow">
            MINEMIND PLATFORM
          </p>

          <h1>Ore Traceability</h1>

          <span>
            Live digital passports created from real fleet haul cycles
          </span>
        </div>

        <div className="traceability-live">
          <span className="status-dot"></span>
          LIVE CHAIN OF CUSTODY
        </div>
      </div>

      <div className="traceability-metrics">
        <div className="traceability-metric">
          <span>ACTIVE BATCHES</span>
          <strong>{activeBatches}</strong>
        </div>

        <div className="traceability-metric">
          <span>ORE IN TRANSIT</span>
          <strong>{inTransit}</strong>
        </div>

        <div className="traceability-metric">
          <span>COMPLETED BATCHES</span>
          <strong>{completedBatches}</strong>
        </div>

        <div className="traceability-metric">
          <span>TRACEABILITY COVERAGE</span>
          <strong>
            {operations.traceability_score ?? 0}%
          </strong>
        </div>
      </div>

      {passports.length === 0 ? (
        <div className="traceability-empty">
          No digital ore passports available.
        </div>
      ) : (
        passports.map((passport) => (
          <div
            className="ore-passport-card"
            key={passport.batch_id}
          >
            <div className="passport-top">
              <div>
                <p className="traceability-eyebrow">
                  DIGITAL ORE PASSPORT
                </p>

                <h2>{passport.batch_id}</h2>

                <span>
                  {passport.origin_name} ·{" "}
                  {passport.quantity_mt} MT
                </span>
              </div>

              <div className="passport-status">
                {passport.status}
              </div>
            </div>

            <div className="passport-grid">
              <div>
                <span>ORE GRADE</span>
                <strong>{passport.grade_fe}% Fe</strong>
              </div>

              <div>
                <span>CARRIER</span>
                <strong>{passport.carrier || "--"}</strong>
              </div>

              <div>
                <span>CURRENT STAGE</span>
                <strong>{passport.current_stage}</strong>
              </div>

              <div>
                <span>PROCESSED</span>
                <strong>{Number(passport.processed_mt || 0).toFixed(1)} / {passport.quantity_mt} MT</strong>
              </div>
            </div>

            <div className="custody-section">
              <p className="traceability-eyebrow">
                LIVE MATERIAL CUSTODY CHAIN
              </p>

              <div className="custody-chain">
                {(passport.trace_events || []).length === 0 ? (
                  <div className="custody-empty">
                    Waiting for first custody event...
                  </div>
                ) : (
                  passport.trace_events.map((event, index) => (
                    <div
                      className="custody-event"
                      key={`${event.timestamp}-${index}`}
                    >
                      <div className="custody-marker">
                        <span>{index + 1}</span>

                        {index <
                          passport.trace_events.length - 1 && (
                          <div className="custody-line"></div>
                        )}
                      </div>

                      <div className="custody-content">
                        <div className="custody-event-top">
                          <strong>{event.event}</strong>

                          <span>
                            {event.simulation_minute != null ? `T+${event.simulation_minute} MIN` : formatTime(event.timestamp)}
                          </span>
                        </div>

                        <p>
                          Entity {event.entity} · {event.stage}
                        </p>

                        <small>
                          Custody: {event.custody_owner}
                        </small>
                      </div>
                    </div>
                  ))
                )}
              </div>
            </div>
          </div>
        ))
      )}
    </div>
  );
}

export default OreTraceability;