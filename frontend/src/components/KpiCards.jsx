import Icon from "./Icon";
import { rupees } from "../api";
import "./KpiCards.css";

// Thresholds mirror the backend's low-confidence cutoff (0.7).
function confidenceLevel(confidence) {
  if (confidence >= 0.85) return { label: "High", tone: "green", meter: "" };
  if (confidence >= 0.7) return { label: "Medium", tone: "amber", meter: "warn" };
  return { label: "Low", tone: "red", meter: "bad" };
}

export default function KpiCards({ result, loading }) {
  const r = result?.recommendation;
  const level = r ? confidenceLevel(r.confidence) : null;

  const cards = [
    {
      key: "profit",
      icon: "rupee",
      tone: "green",
      label: "Expected Profit",
      value: r ? rupees(r.net) : "—",
      note: r
        ? `${result.quantity_qtl} qtl of ${result.commodity}, after all costs`
        : "Net of freight, spoilage and fees",
    },
    {
      key: "additional",
      icon: "trending-up",
      tone: "teal",
      label: "Additional Profit",
      value: r ? `${r.uplift > 0 ? "+" : ""}${rupees(r.uplift)}` : "—",
      note: r
        ? r.uplift > 0
          ? "more than selling at the nearest market"
          : "Selling nearby is already the best option"
        : "Compared with the nearest market",
    },
    {
      key: "market",
      icon: "map-pin",
      tone: "blue",
      label: "Recommended Market",
      value: r ? r.mandi : "—",
      isText: true,
      note: r ? (r.sell_day === 0 ? "Sell today" : `Sell on ${r.sell_label}`) : "Best net-profit market",
    },
    {
      key: "confidence",
      icon: "shield",
      tone: level ? level.tone : "gray",
      label: "Confidence Score",
      value: r ? `${Math.round(r.confidence * 100)}%` : "—",
      note: r ? `${level.label} confidence in the forecast` : "Based on data freshness",
      meter: r ? { pct: Math.round(r.confidence * 100), tone: level.meter } : null,
    },
  ];

  return (
    <section className={`kpis ${loading ? "is-loading" : ""}`} aria-label="Key results" aria-busy={loading}>
      {cards.map((c) => (
        <article key={c.key} className="kpi">
          <div className={`kpi-icon kpi-tone-${c.tone}`}>
            <Icon name={c.icon} size={22} />
          </div>
          <div className="kpi-body">
            <p className="kpi-label">{c.label}</p>
            <p className={`kpi-value ${c.isText ? "kpi-value--text" : ""}`}>{c.value}</p>
            <p className="kpi-note">{c.note}</p>
            {c.meter && (
              <div
                className={`kpi-meter ${c.meter.tone}`}
                role="progressbar"
                aria-valuenow={c.meter.pct}
                aria-valuemin="0"
                aria-valuemax="100"
                aria-label="Confidence"
              >
                <span style={{ width: `${c.meter.pct}%` }} />
              </div>
            )}
          </div>
        </article>
      ))}
    </section>
  );
}
