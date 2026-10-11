import { rupees } from "../api";
import "./ProfitBreakdown.css";

export default function ProfitBreakdown({ best }) {
  const parts = [
    { key: "net", label: "Net Profit", value: Math.max(best.net, 0), shown: best.net },
    { key: "transport", label: "Transport", value: best.freight, shown: best.freight },
    { key: "spoilage", label: "Spoilage & transit loss", value: best.spoilage_loss + best.risk_loss,
      shown: best.spoilage_loss + best.risk_loss },
    { key: "other", label: "Fees & storage", value: best.fees + best.storage, shown: best.fees + best.storage },
  ];
  const total = parts.reduce((sum, p) => sum + p.value, 0) || 1;

  return (
    <div className="card">
      <h2>Profit breakdown</h2>

      <div className="pb-gross">
        <span>Gross Revenue</span>
        <strong>{rupees(best.gross)}</strong>
      </div>

      <div className="pb-bar" role="img"
        aria-label={`Of ${rupees(best.gross)} gross revenue, ${rupees(best.net)} is net profit`}>
        {parts.map((p) => (
          <span key={p.key} className={`pb-seg pb-${p.key}`} style={{ width: `${(p.value / total) * 100}%` }} />
        ))}
      </div>

      <ul className="pb-list">
        {parts.map((p) => (
          <li key={p.key} className={p.key === "net" ? "pb-net-row" : ""}>
            <span className={`pb-dot pb-${p.key}`} />
            <span className="pb-label">{p.label}</span>
            <strong>{p.key === "net" ? "" : "-"}{rupees(Math.abs(p.shown))}</strong>
            <span className="pb-pct">{Math.round((p.value / total) * 100)}%</span>
          </li>
        ))}
      </ul>
    </div>
  );
}
