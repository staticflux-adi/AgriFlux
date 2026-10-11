import { rupees } from "../api";
import { marketRows, shortDate } from "../insights";
import "./MarketComparison.css";

export default function MarketComparison({ result }) {
  const rows = marketRows(result);
  const hasEstimate = rows.some((r) => r.freight.approx && r.freight.value != null);

  return (
    <div className="card">
      <div className="card-head">
        <h2>Market comparison</h2>
        <span className="mc-note">{rows.length} nearby markets, ranked by expected profit</span>
      </div>

      <div className="scroll">
        <table className="mc-table">
          <thead>
            <tr>
              <th>Rank</th>
              <th>Market</th>
              <th>Predicted price</th>
              <th>Distance</th>
              <th>Transport cost</th>
              <th>Expected profit</th>
            </tr>
          </thead>
          <tbody>
            {rows.map((row) => (
              <tr key={row.id} className={row.isBest ? "mc-best" : ""}>
                <td><span className={`mc-rank ${row.isBest ? "top" : ""}`}>#{row.rank}</span></td>
                <td>
                  <span className="mc-name">{row.name}</span>
                  {row.isBest && <span className="mc-pill">Best</span>}
                  <span className="mc-sub">{row.district}</span>
                </td>
                <td>
                  {row.price != null ? rupees(row.price) : "—"}
                  <span className="mc-sub">per qtl{row.priceDate ? ` · ${shortDate(row.priceDate)}` : ""}</span>
                </td>
                <td>{row.km} km</td>
                <td>
                  {row.freight.value != null
                    ? `${row.freight.approx ? "≈ " : ""}${rupees(row.freight.value)}`
                    : "—"}
                </td>
                <td className="mc-profit">{rupees(row.net)}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      {hasEstimate && <p className="hint">≈ Transport cost is estimated from the distance for markets outside the top routes.</p>}
    </div>
  );
}
