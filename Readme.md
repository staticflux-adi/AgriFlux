# 🌾 AgriFlux
### AI-Powered Agricultural Market Intelligence & Dispatch Optimization Platform

 **Helping farmers maximize profits through AI-driven market forecasting, logistics optimization, and intelligent dispatch recommendations.**



---

# 📖 Overview

AgriFlux is an AI-powered decision support system designed to solve one of India's biggest agricultural challenges: **distress selling**.

Smallholder farmers often sell their produce at the nearest mandi (APMC) without knowing whether another nearby market could provide significantly higher returns. Local supply gluts, weather disruptions, transportation costs, and perishability make this decision extremely difficult.

AgriFlux continuously analyzes multiple markets, predicts short-term prices, estimates logistics costs, and recommends the best market and selling time to maximize net profit.

---

# 🚜 Problem Statement

Farmers regularly face:

- Lack of real-time price visibility
- Local market oversupply
- Rapid price fluctuations
- High transportation uncertainty
- Crop spoilage during transit
- Weather-related risks
- No intelligent decision support

Most farmers ultimately sell below production cost due to limited information.

---

# 💡 Solution

AgriFlux combines Artificial Intelligence, predictive analytics, and logistics optimization to answer one simple question:

 **Where and when should the farmer sell the harvest for maximum profit?**

Instead of showing only market prices, AgriFlux evaluates:

- Future market prices
- Distance to markets
- Transportation cost
- Fuel expenses
- Crop perishability
- Weather conditions
- Transit risks
- Expected net realization

The platform then recommends the most profitable market backed by explainable AI insights.

---

# ✨ Key Features

## 📈 AI Price Forecasting

- Predicts commodity prices
- 3–7 day forecast horizon
- Multi-market comparison
- Historical trend analysis

---

## 🚚 Smart Dispatch Optimization

Calculates:

- Freight cost
- Road distance
- Transit duration
- Spoilage loss
- Risk-adjusted profit

Then recommends the optimal mandi.

---

## 🗺 Interactive Market Map

- Farmer location
- Nearby mandis
- Route visualization
- Distance estimation
- Best market highlighting

---

## 💰 Profit Optimization

Instead of highest selling price, AgriFlux optimizes:

```
Net Profit =
Predicted Selling Price
− Freight Cost
− Spoilage Loss
− Transit Risk
```

---

## 📊 Market Comparison

Compare multiple mandis based on:

- Predicted price
- Distance
- Profit
- Transport cost
- Rank

---

## 📉 Forecast Visualization

Interactive charts showing:

- Daily predicted prices
- Confidence
- Best selling day

---

## 🌧 Weather-aware Recommendations

Considers:

- Rainfall impact
- Transit delays
- Spoilage probability
- Market supply changes

---

## 🤖 Explainable AI

Every recommendation includes reasoning such as:

- Higher future demand
- Lower transport cost
- Better market prices
- Reduced spoilage risk
- Higher confidence

---

# 🧠 How It Works

```
Farmer Input
      │
      ▼
Market Data Collection
      │
      ▼
Price Forecast Model
      │
      ▼
Logistics Cost Estimation
      │
      ▼
Spoilage Analysis
      │
      ▼
Profit Optimization Engine
      │
      ▼
AI Recommendation
```

---

# 🏗 System Architecture

```
                   AGMARKNET
                    Weather
                    Fuel Data
                        │
                        ▼
               Data Processing Layer
                        │
                        ▼
              Forecasting Engine
                        │
                        ▼
         Logistics Optimization Engine
                        │
                        ▼
        Explainable AI Recommendation
                        │
                        ▼
          React Dashboard + Maps
```

---

# ⚙ Technology Stack

## Frontend

- React
- Vite
- Tailwind CSS
- Leaflet Maps

---

## Backend

- FastAPI
- Python

---

## Machine Learning

- Pandas
- NumPy
- Scikit-learn
- Time Series Forecasting

---

## Database

- SQLite
- PostgreSQL (optional)

---

## APIs

- AGMARKNET
- Weather API
- OpenRouteService
- Fuel Cost Estimation

---

# 📊 Recommendation Algorithm

For each market:

```
Net Profit

=

Forecast Price

×

Quantity

−

Transport Cost

−

Spoilage Loss

−

Risk Cost
```

The market with the highest net profit is recommended.

---

# 📂 Project Structure

```
backend/
│
├── app/
├── routes/
├── models/
├── scripts/
└── requirements.txt

frontend/
│
├── src/
│   ├── components/
│   ├── api.js
│   ├── App.jsx
│   └── styles/
└── package.json
```

---

# 🚀 Getting Started

## Clone Repository

```bash
git clone https://github.com/yourusername/AgriFlux.git
```

---

## Backend

```bash
cd backend

python -m venv venv

venv\Scripts\activate

pip install -r requirements.txt

uvicorn app.main:app --reload
```

---

## Frontend

```bash
cd frontend

npm install

npm run dev
```

---

# 📈 Example Workflow

1. Select commodity
2. Enter quantity
3. Choose vehicle
4. Select location
5. Click **Find Best Market**
6. Compare recommendations
7. View AI explanation
8. Dispatch to recommended mandi

---

# 🎯 Impact

AgriFlux helps farmers:

- Increase profits
- Reduce distress sales
- Make informed decisions
- Minimize transportation losses
- Reduce spoilage
- Improve market access

---

# 🌍 Future Scope

- Live AGMARKNET integration
- eNAM integration
- Satellite crop intelligence
- AI chatbot
- Voice support in regional languages
- Offline mode
- SMS recommendations
- Farmer cooperative optimization
- Carbon-efficient route planning

---


# ⭐ Why AgriFlux?

AgriFlux transforms agricultural market intelligence into actionable recommendations. Instead of overwhelming farmers with raw market prices, it combines AI forecasting, logistics optimization, and explainable insights to recommend **the right market, at the right time, for the highest possible profit**.

```

---

