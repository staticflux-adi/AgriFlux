import { rupees } from "../api";
import { buildTimeline, signed, weekdayDate } from "../insights";
import "./DecisionTimeline.css";

export default function DecisionTimeline({ result }) {
  const steps = buildTimeline(result);

  return (
    <div className="card">
      <div className="card-head">
        <h2>Decision timeline</h2>
        <span className="tl-market">Prices at {result.best.mandi}</span>
      </div>

      <ol className="tl">
        {steps.map((s) => (
          <li key={s.offset} className={`tl-step ${s.isRec ? "rec" : ""}`} aria-current={s.isRec ? "step" : undefined}>
            <div className="tl-top">
              <span className="tl-label">{s.label}</span>
              {s.isRec && <span className="tl-tag">Recommended</span>}
            </div>
            <span className="tl-date">{weekdayDate(s.date)}</span>
            <strong className="tl-price">{rupees(s.price)}</strong>
            <span className="tl-change">
              {s.offset === 0 ? "Latest price" : `${signed(s.change)} vs today`}
            </span>
            <span className="tl-action">{s.action}</span>
          </li>
        ))}
      </ol>
    </div>
  );
}
