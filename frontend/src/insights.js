// Presentation helpers: turn the /api/recommend response into display-ready values.
// Pure functions only. No business logic and no API calls live here.
import { rupees } from "./api";

const CONFIDENCE_OK = 0.7;

// "2026-10-13" -> local Date (avoids the UTC shift of new Date("YYYY-MM-DD")).
export function parseIso(iso) {
  const [y, m, d] = iso.split("-").map(Number);
  return new Date(y, m - 1, d);
}
export const shortDate = (iso) =>
  parseIso(iso).toLocaleDateString("en-IN", { day: "numeric", month: "short" });
export const weekdayDate = (iso) =>
  parseIso(iso).toLocaleDateString("en-IN", { weekday: "short", day: "numeric", month: "short" });

export const changePct = (value, base) => (base ? ((value - base) / base) * 100 : 0);
export function signed(n, digits = 1) {
  const v = Math.abs(n) < 0.05 ? 0 : n;
  return `${v >= 0 ? "+" : ""}${v.toFixed(digits)}%`;
}

export const priceAt = (forecasts, mandiName, offset) => forecasts?.[mandiName]?.[offset]?.p50 ?? null;

// Overall risk of the recommended plan: loss exposure, bumped up when data confidence is low.
export function riskLevel(best) {
  const exposure = best.spoilage_pct + best.risk_pct;
  let score = exposure < 4 ? 0 : exposure < 9 ? 1 : 2;
  if (best.confidence < CONFIDENCE_OK) score = Math.min(score + 1, 2);
  return [
    { label: "Low", tone: "green" },
    { label: "Medium", tone: "amber" },
    { label: "High", tone: "red" },
  ][score];
}

export function transitRiskLevel(riskPct) {
  if (riskPct < 1.5) return { label: "Low", tone: "green" };
  if (riskPct < 3) return { label: "Moderate", tone: "amber" };
  return { label: "High", tone: "red" };
}

// The API returns the top options only. Freight is linear in distance for a fixed
// load, so markets missing from the top list get an estimate from two known routes.
function freightEstimator(options) {
  const byMandi = new Map();
  options.forEach((o) => byMandi.set(o.mandi_id, { km: o.road_km, freight: o.freight }));
  const points = [...byMandi.values()].sort((a, b) => a.km - b.km);
  let line = null;
  if (points.length >= 2 && points[points.length - 1].km !== points[0].km) {
    const a = points[0];
    const b = points[points.length - 1];
    const slope = (b.freight - a.freight) / (b.km - a.km);
    line = { slope, intercept: a.freight - slope * a.km };
  }
  return (id, km) => {
    if (byMandi.has(id)) return { value: byMandi.get(id).freight, approx: false };
    if (line) return { value: Math.max(0, line.intercept + line.slope * km), approx: true };
    return { value: null, approx: true };
  };
}

export function marketRows(result) {
  const { mandi_summary: summary, forecasts, options, best } = result;
  const freightFor = freightEstimator(options);
  const rows = summary.map((m) => {
    const point = (forecasts[m.name] ?? [])[m.best_day];
    return {
      id: m.id,
      name: m.name,
      district: m.district,
      price: point ? point.p50 : null,
      priceDate: point ? point.date : null,
      km: m.road_km,
      freight: freightFor(m.id, m.road_km),
      net: m.best_net,
      isBest: m.name === best.mandi,
    };
  });
  rows.sort((a, b) => b.net - a.net);
  return rows.map((row, i) => ({ ...row, rank: i + 1 }));
}

// Today, Tomorrow, the recommended day and the day after, at the recommended market.
export function buildTimeline(result) {
  const rec = result.recommendation.sell_day;
  const series = result.forecasts[result.best.mandi] ?? [];
  const last = series.length - 1;
  const picked = new Set([0, 1, rec, rec + 1].filter((o) => o >= 0 && o <= last));
  for (let o = 0; picked.size < 4 && o <= last; o += 1) picked.add(o);
  const today = series[0]?.p50;

  return [...picked]
    .sort((a, b) => a - b)
    .map((offset) => {
      const point = series[offset];
      const isRec = offset === rec;
      let label = `Day ${offset}`;
      if (offset === 0) label = "Today";
      else if (offset === 1) label = "Tomorrow";
      if (isRec && rec > 1) label = "Recommended Day";
      else if (offset === rec + 1 && offset > 1) label = "Next Day";
      return {
        offset,
        label,
        isRec,
        date: point.date,
        price: point.p50,
        change: changePct(point.p50, today),
        action: isRec ? `Sell at ${result.best.mandi}` : offset < rec ? "Wait" : "Later option",
      };
    });
}

// Short badges for the recommendation card.
export function buildBadges(result) {
  const { best, baseline, recommendation: r, meta } = result;
  const gain = changePct(best.price_used, baseline.price_used);
  const badges = [];
  if (!r.same_as_baseline && gain > 0.5) {
    badges.push({ icon: "trending-up", tone: "green", label: `${signed(gain)} price vs nearby` });
  }
  badges.push({ icon: "truck", tone: "blue", label: `${best.road_km} km · ${best.transit_hours} h` });
  badges.push({
    icon: "leaf",
    tone: best.spoilage_pct > 5 ? "amber" : "green",
    label: `${best.spoilage_pct}% spoilage`,
  });
  badges.push(
    r.sell_day === 0
      ? { icon: "check", tone: "green", label: "No waiting needed" }
      : { icon: "clock", tone: "amber", label: `Forecast favors day ${r.sell_day}` }
  );
  badges.push(
    meta.rain_simulated
      ? { icon: "cloud-rain", tone: "amber", label: "Rain scenario" }
      : {
          icon: "shield",
          tone: r.confidence >= CONFIDENCE_OK ? "green" : "amber",
          label: `${Math.round(r.confidence * 100)}% confidence`,
        }
  );
  return badges;
}

// The "Why this recommendation?" cards.
export function buildInsights(result) {
  const { best, baseline, recommendation: r, meta, forecasts, mandi_summary: summary, quantity_qtl: qty } = result;
  const gain = changePct(best.price_used, baseline.price_used);
  const todayPrice = priceAt(forecasts, best.mandi, 0);
  const salePrice = priceAt(forecasts, best.mandi, r.sell_day);
  const timingGain = todayPrice && salePrice ? changePct(salePrice, todayPrice) : 0;
  const stale = summary.find((m) => m.name === best.mandi)?.stale_days ?? 0;
  const days = `${r.sell_day} day${r.sell_day > 1 ? "s" : ""}`;

  const cards = [
    {
      key: "price",
      icon: "trending-up",
      tone: "green",
      title: r.same_as_baseline ? "Local price holds up" : "Better price",
      text: r.same_as_baseline
        ? `${rupees(best.price_used)}/qtl at ${best.mandi} beats the alternatives after costs.`
        : `${rupees(best.price_used)}/qtl at ${best.mandi}, ${signed(gain)} vs ${rupees(baseline.price_used)} at ${baseline.mandi}.`,
    },
    {
      key: "transport",
      icon: "truck",
      tone: "blue",
      title: "Transport cost",
      text: `${rupees(best.freight)} for ${best.road_km} km (about ${best.transit_hours} h), ${rupees(best.freight / qty)} per quintal${
        r.same_as_baseline ? "" : `, vs ${rupees(baseline.freight)} to the nearest market`
      }.`,
    },
    {
      key: "fresh",
      icon: "leaf",
      tone: "teal",
      title: "Freshness",
      text: `${best.spoilage_pct}% spoilage and ${best.risk_pct}% transit risk cost about ${rupees(
        best.spoilage_loss + best.risk_loss
      )}.`,
    },
    {
      key: "timing",
      icon: "clock",
      tone: "amber",
      title: "Timing",
      text:
        r.sell_day === 0
          ? "Selling now: waiting does not beat today's net after storage and spoilage."
          : timingGain > 0.5
            ? `Forecast is ${signed(timingGain)} higher by ${r.sell_label} (${rupees(salePrice)} vs ${rupees(todayPrice)} today), enough to beat storage and spoilage.`
            : `Waiting ${days} gives the best net after storage, spoilage and transit.`,
    },
    meta.rain_simulated
      ? {
          key: "weather",
          icon: "cloud-rain",
          tone: "blue",
          title: "Weather risk",
          text: "The heavy-rain scenario raises spoilage and transit risk; this plan already accounts for it.",
        }
      : {
          key: "confidence",
          icon: "shield",
          tone: r.confidence >= CONFIDENCE_OK ? "green" : "amber",
          title: "Data confidence",
          text: `${Math.round(r.confidence * 100)}% confidence; the latest price report is ${stale} day${stale === 1 ? "" : "s"} old.`,
        },
  ];
  return cards;
}
