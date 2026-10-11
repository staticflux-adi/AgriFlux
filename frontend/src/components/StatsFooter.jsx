import Icon from "./Icon";
import "./StatsFooter.css";

function formatDuration(ms) {
  if (ms == null) return "—";
  return ms < 1000 ? `${Math.round(ms)} ms` : `${(ms / 1000).toFixed(1)} s`;
}

export default function StatsFooter({ result, elapsedMs }) {
  const markets = result?.mandi_summary.length;
  const first = result ? Object.values(result.forecasts)[0] : null;
  const horizon = first ? first.length - 1 : null;

  const stats = [
    { icon: "layers", label: "Markets Compared", value: markets ?? "—", note: "nearby APMC mandis" },
    { icon: "route", label: "Routes Evaluated", value: markets ? `≈ ${markets * (horizon + 1)}` : "—", note: "market × sell-day options" },
    { icon: "calendar", label: "Forecast Horizon", value: horizon != null ? `${horizon} days` : "—", note: "with P25 to P75 range" },
    { icon: "timer", label: "Optimization Time", value: formatDuration(result ? elapsedMs : null), note: "end to end, incl. network" },
  ];

  return (
    <footer className="stats" aria-label="Run statistics">
      {stats.map((s) => (
        <div key={s.label} className="stat">
          <span className="stat-icon"><Icon name={s.icon} size={20} /></span>
          <div>
            <strong>{s.value}</strong>
            <span className="stat-name">{s.label}</span>
            <span className="stat-note">{s.note}</span>
          </div>
        </div>
      ))}
    </footer>
  );
}
