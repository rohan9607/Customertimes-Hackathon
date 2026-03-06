"""
Flask API for the Predictive Maintenance Dashboard.
Auto-trains on startup — no manual steps needed.
"""

import os
import json
from flask import Flask, jsonify, request
from flask_cors import CORS
from model import RobotHealthModel
from chat_engine import ChatEngine

app = Flask(__name__)
CORS(app)

# ── Locate data files ─────────────────────────────────────────────
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_CANDIDATES = [
    os.path.join(BASE_DIR, '..', 'data'),                       # PredictiveMaintenance/data/
    os.path.join(BASE_DIR, '..', '..'),                          # Microsoft Co-Innovation/
]

training_path = None
actual_path = None
for d in DATA_CANDIDATES:
    t = os.path.join(d, 'training_data.csv')
    a = os.path.join(d, 'actual_data.csv')
    if os.path.exists(t) and os.path.exists(a):
        training_path = t
        actual_path = a
        break

# ── Initialize model & chat ───────────────────────────────────────
model = RobotHealthModel()
chat = ChatEngine()
dashboard_cache = None


def startup():
    global dashboard_cache
    if not training_path:
        print("⚠️  Data files not found! Place training_data.csv and actual_data.csv in the data/ folder or parent directory.")
        return
    print(f"📂 Training data: {training_path}")
    print(f"📂 Actual data:   {actual_path}")
    print("🔧 Training model on healthy baseline data...")
    baselines = model.train(training_path)
    print(f"✅ Model trained — {len(baselines)} sensor baselines computed.")
    print("🔍 Analyzing actual data for anomalies...")
    dashboard_cache = model.analyze_data(actual_path)
    print(f"✅ Analysis complete — {dashboard_cache['summary']['total_anomalies']} anomalies detected.")
    chat.load(dashboard_cache, baselines)
    print("💬 Chat engine loaded.")
    print("🚀 Backend ready!")


# ── API Routes ─────────────────────────────────────────────────────

@app.route('/api/status')
def status():
    return jsonify({
        'trained': model.is_trained,
        'data_found': training_path is not None,
    })


@app.route('/api/dashboard')
def dashboard():
    if not dashboard_cache:
        return jsonify({'error': 'Model not trained yet'}), 503
    return jsonify(dashboard_cache)


@app.route('/api/baselines')
def baselines():
    if not model.is_trained:
        return jsonify({'error': 'Model not trained yet'}), 503
    return jsonify(model.baselines)


@app.route('/api/predict', methods=['POST'])
def predict():
    if not model.is_trained:
        return jsonify({'error': 'Model not trained yet'}), 503
    data = request.get_json(force=True)
    input_values = {}
    for key, val in data.items():
        try:
            input_values[key] = float(val)
        except (ValueError, TypeError):
            continue
    if not input_values:
        return jsonify({'error': 'No valid sensor values provided'}), 400
    result = model.predict_health(input_values)
    return jsonify(result)


@app.route('/api/chat', methods=['POST'])
def chat_route():
    data = request.get_json(force=True)
    message = data.get('message', '').strip()
    if not message:
        return jsonify({'reply': 'Please type a question.'})
    reply = chat.respond(message)
    return jsonify({'reply': reply})


# ── Entry point ────────────────────────────────────────────────────
if __name__ == '__main__':
    startup()
    print("\n🌐 API running at http://localhost:5000")
    app.run(host='0.0.0.0', port=5000, debug=False)
