import Icon from "./Icon";
import { changePct, signed, transitRiskLevel } from "../insights";
import "./WeatherCard.css";

// Average local price change at the farmer's nearest market over the next 3 days,
// comparing the rain scenario with the last normal run.
function priceImpact(result, normalForecasts) {
  const origin = result.meta.origin_mandi;
  const rain = result.forecasts[origin];
  const normal = normalForecasts?.[origin];
  if (!rain || !normal) return null;
  const diffs = [1, 2, 3]
    .filter((i) => rain[i] && normal[i])
    .map((i) => changePct(rain[i].p50, normal[i].p50));
  return diffs.length ? diffs.reduce((sum, d) => sum + d, 0) / diffs.length : null;
}

export default function WeatherCard({ simulate, onChange, result, normalForecasts, loading }) {
  // Metrics are only shown when the displayed result matches the selected scenario.
  const ready = Boolean(result) && result.meta.rain_simulated === simulate;
  const origin = result?.meta.origin_mandi;
  const impact = ready && simulate ? priceImpact(result, normalForecasts) : null;
  const transit = ready ? transitRiskLevel(result.best.risk_pct) : null;

  const rows = [
    {
      icon: simulate ? "cloud-rain" : "sun",
      tone: simulate ? "blue" : "amber",
      label: "Weather",
      value: simulate ? "Heavy rain" : "Normal conditions",
      sub: simulate ? "Simulated near your farm for 3 days" : "Seasonal forecast data",
    },
    {
      icon: "alert",
      tone: simulate ? "red" : "gray",
      label: "Rain Risk",
      value: simulate ? "High" : "Baseline",
      sub: simulate ? "Roads and storage affected" : "No extra disruption assumed",
    },
    {
      icon: "trending-up",
      tone: impact != null && impact > 0 ? "green" : "gray",
      label: "Expected Price Impact",
      value: simulate ? (impact == null ? "—" : signed(impact)) : "None",
      sub: simulate
        ? impact == null
          ? "Run a normal scenario first to compare"
          : `at ${origin}, next 3 days`
        : "Prices follow the forecast",
    },
    {
      icon: "truck",
      tone: transit ? transit.tone : "gray",
      label: "Transit Risk",
      value: transit ? transit.label : "—",
      sub: transit ? `${result.best.risk_pct}% expected loss on the route` : "Run an optimization",
    },
  ];

  return (
    <div className="card weather">
      <div className="card-head">
        <h2>Weather scenario</h2>
      </div>

      <div className="seg" role="group" aria-label="Weather scenario">
        <button type="button" className={!simulate ? "active" : ""} aria-pressed={!simulate}
          disabled={loading} onClick={() => onChange({ simulate_rain: false }, true)}>
          Normal
        </button>
        <button type="button" className={simulate ? "active" : ""} aria-pressed={simulate}
          disabled={loading} onClick={() => onChange({ simulate_rain: true }, true)}>
          Heavy rain
        </button>
      </div>

      <ul className="wx-list">
        {rows.map((row) => (
          <li key={row.label} className="wx-row">
            <span className={`wx-icon wx-${row.tone}`}><Icon name={row.icon} size={18} /></span>
            <span className="wx-text">
              <span className="wx-label">{row.label}</span>
              <span className="wx-sub">{row.sub}</span>
            </span>
            <strong className="wx-value">{row.value}</strong>
          </li>
        ))}
      </ul>
    </div>
  );
}
