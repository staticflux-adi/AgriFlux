import Icon from "./Icon";

const COMMODITIES = ["Onion", "Tomato", "Potato"];

export default function InputForm({ form, onChange, onSubmit, loading }) {
  const num = (key) => (e) =>
    onChange({ [key]: e.target.value === "" ? "" : Number(e.target.value) });
  const valid =
    form.quantity_qtl > 0 && form.lat !== "" && form.lon !== "" && form.harvest_age_days !== "";

  return (
    <form
      className="card"
      onSubmit={(e) => {
        e.preventDefault();
        if (valid) onSubmit();
      }}
    >
      <h2>Your harvest</h2>

      <label>
        Crop
        <select value={form.commodity} onChange={(e) => onChange({ commodity: e.target.value })}>
          {COMMODITIES.map((c) => <option key={c}>{c}</option>)}
        </select>
      </label>

      <label>
        Quantity (quintals)
        <input type="number" min="1" max="5000" value={form.quantity_qtl} onChange={num("quantity_qtl")} />
      </label>

      <label>
        Days since harvest
        <input type="number" min="0" max="30" value={form.harvest_age_days} onChange={num("harvest_age_days")} />
      </label>

      <fieldset className="location">
        <legend><Icon name="map-pin" size={14} />Farm location</legend>
        <div className="row">
          <label>
            Latitude
            <input type="number" step="0.0001" min="-90" max="90" value={form.lat} onChange={num("lat")} />
          </label>
          <label>
            Longitude
            <input type="number" step="0.0001" min="-180" max="180" value={form.lon} onChange={num("lon")} />
          </label>
        </div>
        <p className="hint">Or click anywhere on the map to set it.</p>
      </fieldset>

      <button type="submit" disabled={!valid || loading}>
        {loading ? "Optimizing…" : "Find best market"}
      </button>
    </form>
  );
}
