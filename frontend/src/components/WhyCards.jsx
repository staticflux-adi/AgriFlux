import Icon from "./Icon";
import { buildInsights } from "../insights";
import "./WhyCards.css";

export default function WhyCards({ result }) {
  const cards = buildInsights(result);

  return (
    <section aria-labelledby="why-title">
      <h2 id="why-title" className="why-title">Why this recommendation?</h2>
      <div className="why-grid">
        {cards.map((c) => (
          <article key={c.key} className="why-card">
            <span className={`why-icon why-${c.tone}`}><Icon name={c.icon} size={20} /></span>
            <h3>{c.title}</h3>
            <p>{c.text}</p>
          </article>
        ))}
      </div>
    </section>
  );
}
