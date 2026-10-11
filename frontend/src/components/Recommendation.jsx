import Icon from "./Icon";
import { rupees } from "../api";
import { buildBadges, riskLevel } from "../insights";
import "./Recommendation.css";

function Metric({ icon, label, value, tone }) {
  return (
    <div className="ai-metric">
      <span className="ai-metric-label"><Icon name={icon} size={14} />{label}</span>
      <span className={`ai-metric-value ${tone ?? ""}`}>{value}</span>
    </div>
  );
}

export default function Recommendation({ result }) {
  const r = result.recommendation;
  const best = result.best;
  const risk = riskLevel(best);
  const badges = buildBadges(result);
  const confidence = Math.round(r.confidence * 100);
  const action = r.sell_day === 0 ? "Sell Today" : `Wait ${r.sell_day} day${r.sell_day > 1 ? "s" : ""}`;

  return (
    <section className="ai-card" aria-label="AI recommendation">
      <header className="ai-head">
        <span className="ai-chip"><Icon name="sparkles" size={14} />AI Recommendation</span>
        <span className={`ai-action ${r.sell_day === 0 ? "now" : "wait"}`}>{action}</span>
      </header>

      <h2 className="ai-market">{r.mandi}</h2>
      <p className="ai-sub">
        {r.same_as_baseline
          ? "Your nearest market is the best choice"
          : `${best.road_km} km away · sell on ${r.sell_label}`}
      </p>

      <div className="ai-grid">
        <Metric icon="rupee" label="Expected Profit" value={rupees(r.net)} tone="green" />
        <Metric icon="trending-up" label="Additional Profit" value={`${r.uplift > 0 ? "+" : ""}${rupees(r.uplift)}`} tone="green" />
        <Metric icon="shield" label="Confidence" value={`${confidence}%`} tone={r.confidence >= 0.7 ? "green" : "amber"} />
        <Metric icon="alert" label="Risk Level" value={risk.label} tone={risk.tone} />
      </div>

      <div className="ai-score">
        <div
          className="ai-gauge"
          style={{ "--pct": r.realization_score }}
          role="img"
          aria-label={`Market realization score ${r.realization_score} out of 100`}
        >
          <span>{r.realization_score}</span>
        </div>
        <p>
          <strong>Market realization score</strong>
          <span>Share of the best theoretical value captured after freight, spoilage, risk and fees.</span>
        </p>
      </div>

      <ul className="ai-badges">
        {badges.map((b) => (
          <li key={b.label} className={`pill pill-${b.tone}`}>
            <Icon name={b.icon} size={13} />{b.label}
          </li>
        ))}
      </ul>
    </section>
  );
}
