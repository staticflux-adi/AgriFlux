import { MapContainer, TileLayer, CircleMarker, Polyline, Popup, Tooltip, useMapEvents } from "react-leaflet";
import "leaflet/dist/leaflet.css";
import { rupees } from "../api";
import "./MapView.css";

const COLORS = { farmer: "#2563eb", best: "#16a34a", alt: "#eab308", worst: "#dc2626", idle: "#6b7280" };
const LEGEND = [
  ["farmer", "Farmer"],
  ["best", "Best market"],
  ["alt", "Alternative"],
  ["worst", "Worst"],
];

function ClickToSet({ onPick }) {
  useMapEvents({ click: (e) => onPick(e.latlng.lat, e.latlng.lng) });
  return null;
}

export default function MapView({ mandis, form, result, onPick }) {
  const summary = new Map((result?.mandi_summary ?? []).map((m) => [m.id, m]));
  const ranked = [...summary.values()].sort((a, b) => b.best_net - a.best_net);
  const worstId = ranked.length > 2 ? ranked[ranked.length - 1].id : null;
  const bestName = result?.best.mandi;
  const farm = [form.lat || 0, form.lon || 0];

  function category(m) {
    if (!result || !summary.has(m.id)) return "idle";
    if (m.name === bestName) return "best";
    if (m.id === worstId) return "worst";
    return "alt";
  }

  // Draw the best market last so its route sits on top of the others.
  const ordered = [...mandis].sort((a, b) => (category(a) === "best") - (category(b) === "best"));

  return (
    <div className="card map-card">
      <div className="card-head">
        <h2>Markets and routes</h2>
        <ul className="map-legend" aria-label="Map legend">
          {LEGEND.map(([key, label]) => (
            <li key={key}><span className="map-dot" style={{ background: COLORS[key] }} />{label}</li>
          ))}
        </ul>
      </div>

      <MapContainer center={[18.9, 74.4]} zoom={7} className="map" scrollWheelZoom>
        <TileLayer
          attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>'
          url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
        />
        <ClickToSet onPick={onPick} />

        {result &&
          ordered
            .filter((m) => summary.has(m.id))
            .map((m) => {
              const cat = category(m);
              return (
                <Polyline
                  key={`route-${m.id}`}
                  positions={[farm, [m.lat, m.lon]]}
                  pathOptions={{
                    color: COLORS[cat],
                    weight: cat === "best" ? 4 : 2,
                    opacity: cat === "best" ? 0.95 : 0.7,
                    dashArray: cat === "best" ? undefined : "6 6",
                  }}
                />
              );
            })}

        {ordered.map((m) => {
          const s = summary.get(m.id);
          const cat = category(m);
          return (
            <CircleMarker
              key={m.id}
              center={[m.lat, m.lon]}
              radius={cat === "best" ? 13 : 9}
              pathOptions={{ color: "#ffffff", weight: 2, fillColor: COLORS[cat], fillOpacity: 0.95 }}
            >
              {s && (
                <Tooltip permanent direction="right" offset={[12, 0]} className="dist-tip">
                  {s.road_km} km
                </Tooltip>
              )}
              <Popup>
                <strong>{m.name}</strong>
                {s ? (
                  <>
                    <br />Best net: {rupees(s.best_net)} (day {s.best_day})
                    <br />{s.road_km} km · {s.transit_hours} h
                    <br />Data age: {s.stale_days} day(s) · confidence {Math.round(s.confidence * 100)}%
                  </>
                ) : (
                  <><br />Run an optimization to score this market.</>
                )}
              </Popup>
            </CircleMarker>
          );
        })}

        <CircleMarker
          center={farm}
          radius={10}
          pathOptions={{ color: "#ffffff", weight: 3, fillColor: COLORS.farmer, fillOpacity: 1 }}
        >
          <Tooltip permanent direction="top" offset={[0, -10]} className="dist-tip farm-tip">Your farm</Tooltip>
        </CircleMarker>
      </MapContainer>

      <p className="hint">Routes are drawn straight-line for clarity; the km shown beside each market is road distance.</p>
    </div>
  );
}
