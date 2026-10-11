const BASE = import.meta.env.VITE_API_URL || "";

async function request(path, options) {
  const res = await fetch(`${BASE}/api${path}`, {
    headers: { "Content-Type": "application/json" },
    ...options,
  });
  if (!res.ok) {
    const body = await res.json().catch(() => ({}));
    throw new Error(typeof body.detail === "string" ? body.detail : "Invalid input or server error");
  }
  return res.json();
}

export const getMandis = () => request("/mandis");
export const recommend = (payload) =>
  request("/recommend", { method: "POST", body: JSON.stringify(payload) });
export const getBacktest = (commodity) =>
  request(`/backtest?commodity=${encodeURIComponent(commodity)}`);

export const rupees = (value) => `₹${Math.round(value).toLocaleString("en-IN")}`;
