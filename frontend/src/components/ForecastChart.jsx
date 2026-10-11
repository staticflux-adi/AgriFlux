import {
  ComposedChart, Area, Line, XAxis, YAxis, Tooltip, CartesianGrid,
  ReferenceLine, ReferenceDot, ResponsiveContainer,
} from "recharts";
import { rupees } from "../api";
import { changePct, shortDate, signed, weekdayDate } from "../insights";
import "./ForecastChart.css";

function ChartTooltip({ active, payload, markOffset, isRecommended }) {
  if (!active || !payload?.length) return null;
  const d = payload[0].payload;
  return (
    <div className="chart-tip">
      <strong>{weekdayDate(d.iso)}{d.offset === 0 ? " · Today" : ""}</strong>
      <div className="chart-tip-row"><span>Median</span><b>{rupees(d.p50)}</b></div>
      <div className="chart-tip-row"><span>Likely range</span><b>{rupees(d.p25)} – {rupees(d.p75)}</b></div>
      {d.offset > 0 && <div className="chart-tip-row"><span>vs today</span><b>{signed(d.change)}</b></div>}
      {d.offset === markOffset && (
        <span className="chart-tip-tag">{isRecommended ? "Recommended sale day" : "Best day here"}</span>
      )}
    </div>
  );
}

export default function ForecastChart({ forecasts, selected, onSelect, result }) {
  const rows = forecasts[selected] ?? [];
  if (!rows.length) return null;

  const isRecommended = selected === result.best.mandi;
  const summary = result.mandi_summary.find((m) => m.name === selected);
  const markOffset = isRecommended ? result.recommendation.sell_day : summary?.best_day ?? 0;
  const today = rows[0].p50;

  const data = rows.map((d, i) => ({
    label: shortDate(d.date),
    iso: d.date,
    offset: i,
    p25: d.p25,
    p75: d.p75,
    band: d.p75 - d.p25,
    p50: d.p50,
    change: changePct(d.p50, today),
  }));
  const mark = data[markOffset] ?? data[0];
  const low = Math.floor(Math.min(...data.map((d) => d.p25)) * 0.98);
  const high = Math.ceil(Math.max(...data.map((d) => d.p75)) * 1.02);

  return (
    <div className="card">
      <div className="card-head">
        <h2>7-day price forecast</h2>
        <select value={selected} onChange={(e) => onSelect(e.target.value)} aria-label="Market">
          {Object.keys(forecasts).map((name) => <option key={name}>{name}</option>)}
        </select>
      </div>

      <div className="fc-chips">
        <div className="fc-chip">
          <span>Today's price</span>
          <strong>{rupees(today)}</strong>
        </div>
        <div className="fc-chip fc-chip-rec">
          <span>{isRecommended ? "Recommended sale" : "Best day here"} · {mark.label}</span>
          <strong>{rupees(mark.p50)} <em>{signed(mark.change)}</em></strong>
        </div>
        {summary && (
          <div className="fc-chip">
            <span>Data confidence</span>
            <strong>{Math.round(summary.confidence * 100)}% <em>{summary.stale_days}d old</em></strong>
          </div>
        )}
      </div>

      <ResponsiveContainer width="100%" height={260}>
        <ComposedChart data={data} margin={{ top: 28, right: 16, left: 0, bottom: 0 }}>
          <defs>
            <linearGradient id="bandFill" x1="0" y1="0" x2="0" y2="1">
              <stop offset="0%" stopColor="#1f7a4d" stopOpacity={0.28} />
              <stop offset="100%" stopColor="#1f7a4d" stopOpacity={0.08} />
            </linearGradient>
          </defs>
          <CartesianGrid strokeDasharray="3 3" vertical={false} />
          <XAxis dataKey="label" tickLine={false} />
          <YAxis domain={[low, high]} width={60} tickLine={false} tickFormatter={(v) => `₹${v}`} />
          <Tooltip content={<ChartTooltip markOffset={markOffset} isRecommended={isRecommended} />} />
          <Area dataKey="p25" stackId="band" stroke="none" fill="transparent" isAnimationActive={false} />
          <Area dataKey="band" stackId="band" stroke="none" fill="url(#bandFill)" isAnimationActive={false} />
          <ReferenceLine
            x={mark.label}
            stroke="#16a34a"
            strokeDasharray="4 4"
            label={{ value: isRecommended ? "Recommended sale" : "Best day here", position: "top", fill: "#166534", fontSize: 11 }}
          />
          <Line dataKey="p50" stroke="#1f7a4d" strokeWidth={2.5} dot={{ r: 3 }} isAnimationActive={false} />
          <ReferenceDot x={mark.label} y={mark.p50} r={7} fill="#16a34a" stroke="#fff" strokeWidth={2} ifOverflow="extendDomain" />
          <ReferenceDot
            x={data[0].label} y={data[0].p50} r={6} fill="#2563eb" stroke="#fff" strokeWidth={2} ifOverflow="extendDomain"
            label={{ value: "Today", position: "bottom", fill: "#1d4ed8", fontSize: 11 }}
          />
        </ComposedChart>
      </ResponsiveContainer>

      <ul className="fc-legend">
        <li><span className="sw sw-line" />Median forecast</li>
        <li><span className="sw sw-band" />Confidence band (P25 to P75)</li>
        <li><span className="sw sw-today" />Today</li>
        <li><span className="sw sw-rec" />Sale day</li>
      </ul>
    </div>
  );
}
