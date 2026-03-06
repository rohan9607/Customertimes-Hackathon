# 🤖 FANUC CR-7iA/L Predictive Maintenance Dashboard

**Hackathon 2026 — UW-Milwaukee Connected Systems Institute**

A fully offline predictive maintenance assistant for the FANUC CR-7iA/L collaborative robot. Built with Python (Flask + scikit-learn) backend and React frontend.

---

## Features

- **🔬 ML-Trained Anomaly Detection** — IsolationForest + statistical baselines trained on healthy data
- **📊 Real-Time Dashboard** — Health gauges, sensor trends, anomaly timeline
- **🔮 Failure Prediction** — Linear extrapolation estimates time-to-critical
- **🔢 Custom Sensor Input** — Enter any sensor values → instant health score
- **💬 Chat Assistant** — Natural language Q&A about robot health (fully offline)
- **🚨 Alert System** — Prioritized anomalies with recommended maintenance actions

## Anomaly Types Detected

1. ⚡ Electrical Overload (current spikes)
2. 🌡️ Overheating (temperature anomalies)
3. 🛑 Repeated Safety Stops (clustering)
4. 📈 Wear and Tear (gradual degradation)
5. 📡 Sensor Failure (impossible readings)
6. 📊 Electrical Noise (high variance)
7. 🔧 Tool Current Anomaly (gripper issues)

---

## Quick Start

### Prerequisites
- Python 3.9+
- Node.js 16+

### Option 1: One-Click (Windows)
```
Double-click start.bat
```

### Option 2: Manual

**Terminal 1 — Backend:**
```bash
cd backend
pip install -r requirements.txt
python app.py
```

**Terminal 2 — Frontend:**
```bash
cd frontend
npm install
npm start
```

### Data Files
Place `training_data.csv` and `actual_data.csv` in one of these locations:
- `PredictiveMaintenance/data/` folder
- The parent `Microsoft Co-Innovation/` folder (auto-detected)

---

## Architecture

```
┌───────────────────────────────────────────────────┐
│          React Dashboard (port 3000)               │
│  📊 Dashboard │ 🔢 Sensor Input │ 💬 Chat         │
├───────────────────────────────────────────────────┤
│          Flask API (port 5000)                     │
│  /api/dashboard │ /api/predict │ /api/chat         │
├───────────────────────────────────────────────────┤
│  model.py          │  chat_engine.py               │
│  IsolationForest   │  Rule-based NLP               │
│  Statistical Z-scores│  Keyword matching            │
│  Linear Regression  │  Template responses           │
├───────────────────────────────────────────────────┤
│  training_data.csv (baseline) │ actual_data.csv    │
└───────────────────────────────────────────────────┘
```

## API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/status` | GET | Check if model is trained |
| `/api/dashboard` | GET | Full analysis results |
| `/api/baselines` | GET | Training baseline statistics |
| `/api/predict` | POST | Score custom sensor values |
| `/api/chat` | POST | Chat with maintenance assistant |

---

## Tech Stack

- **Backend:** Python, Flask, scikit-learn, pandas, numpy, scipy
- **Frontend:** React 18, Recharts, React Markdown
- **ML Model:** IsolationForest (unsupervised) + statistical z-scores
- **No cloud services required — 100% offline**
# Customertimes-Hackathon
