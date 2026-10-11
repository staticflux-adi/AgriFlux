import { useEffect, useState } from "react";
import { getMandis, recommend } from "./api";
import Icon from "./components/Icon";
import KpiCards from "./components/KpiCards";
import InputForm from "./components/InputForm";
import WeatherCard from "./components/WeatherCard";
import MapView from "./components/MapView";
import ForecastChart from "./components/ForecastChart";
import Recommendation from "./components/Recommendation";
import ProfitBreakdown from "./components/ProfitBreakdown";
import DecisionTimeline from "./components/DecisionTimeline";
import MarketComparison from "./components/MarketComparison";
import WhyCards from "./components/WhyCards";
import StatsFooter from "./components/StatsFooter";

const DEFAULT_FORM = {
  commodity: "Onion",
  quantity_qtl: 40,
  lat: 18.15,
  lon: 74.58,
  truck_type: "pickup",
  harvest_age_days: 1,
  simulate_rain: false,
};

// Identifies a harvest setup ignoring the weather scenario, so a normal run
// can be compared with the rain run for the same inputs.
const setupKey = (f) =>
  JSON.stringify([f.commodity, f.quantity_qtl, f.lat, f.lon, f.truck_type, f.harvest_age_days]);

export default function App() {
  const [form, setForm] = useState(DEFAULT_FORM);
  const [mandis, setMandis] = useState([]);
  const [result, setResult] = useState(null);
  const [normalRun, setNormalRun] = useState(null);
  const [selectedMandi, setSelectedMandi] = useState("");
  const [elapsedMs, setElapsedMs] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  useEffect(() => {
    getMandis().then(setMandis).catch((e) => setError(e.message));
  }, []);

  async function run(payload) {
    setLoading(true);
    setError("");
    const started = performance.now();
    try {
      const data = await recommend(payload);
      setElapsedMs(performance.now() - started);
      setResult(data);
      setSelectedMandi(data.best.mandi);
      if (!payload.simulate_rain) {
        setNormalRun({ key: setupKey(payload), forecasts: data.forecasts });
      }
    } catch (e) {
      setError(e.message);
    } finally {
      setLoading(false);
    }
  }

  // rerun=true is used by the weather scenario switch so the change shows instantly.
  function update(patch, rerun = false) {
    const next = { ...form, ...patch };
    setForm(next);
    if (rerun && result) run(next);
  }

  const normalForecasts = normalRun && normalRun.key === setupKey(form) ? normalRun.forecasts : null;

  return (
    <div className="app">
      <header className="topbar">
        <div className="container topbar-inner">
          <div className="logo"><Icon name="leaf" size={24} /></div>
          <div>
            <h1>AgriFlux</h1>
            <p>Where and when should this harvest be sold? Forecast prices, freight, and spoilage in one score.</p>
          </div>
        </div>
      </header>

      <div className="container">
        {error && <div className="error" role="alert">{error}</div>}

        <KpiCards result={result} loading={loading} />

        <main className="layout">
          <section className="col">
            <InputForm form={form} onChange={update} onSubmit={() => run(form)} loading={loading} />
            <WeatherCard
              simulate={form.simulate_rain}
              onChange={update}
              result={result}
              normalForecasts={normalForecasts}
              loading={loading}
            />
          </section>

          <section className="col">
            <MapView
              mandis={mandis}
              form={form}
              result={result}
              onPick={(lat, lon) => update({ lat: Number(lat.toFixed(4)), lon: Number(lon.toFixed(4)) })}
            />
            {result && (
              <ForecastChart
                forecasts={result.forecasts}
                selected={selectedMandi}
                onSelect={setSelectedMandi}
                result={result}
              />
            )}
          </section>

          <section className="col">
            {result ? (
              <>
                <Recommendation result={result} />
                <ProfitBreakdown best={result.best} />
              </>
            ) : (
              <div className="card muted">Enter your harvest details and press “Find best market”.</div>
            )}
          </section>
        </main>

        <div className="below">
          {result && (
            <>
              <DecisionTimeline result={result} />
              <MarketComparison result={result} />
              <WhyCards result={result} />
            </>
          )}
          <StatsFooter result={result} elapsedMs={elapsedMs} />
        </div>
      </div>
    </div>
  );
}
