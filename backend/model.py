"""
Predictive Maintenance Model — FANUC CR-7iA/L Cobot
Trains on healthy baseline data, detects anomalies in actual data,
and scores custom sensor inputs.
"""

import pandas as pd
import numpy as np
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import StandardScaler
from sklearn.linear_model import LinearRegression

# ── Sensor column definitions ──────────────────────────────────────
CURRENT_COLS = [f'Current_J{i}' for i in range(6)]
TEMP_COLS = ['Temperature_T0'] + [f'Temperature_J{i}' for i in range(1, 6)]
SPEED_COLS = [f'Speed_J{i}' for i in range(6)]
ALL_SENSOR_COLS = CURRENT_COLS + TEMP_COLS + SPEED_COLS + ['Tool_current']

JOINT_TEMP_MAP = {
    0: 'Temperature_T0', 1: 'Temperature_J1', 2: 'Temperature_J2',
    3: 'Temperature_J3', 4: 'Temperature_J4', 5: 'Temperature_J5'
}


class RobotHealthModel:
    """Anomaly detection and health scoring model for the FANUC cobot."""

    def __init__(self):
        self.baselines = {}
        self.isolation_forest = None
        self.scaler = None
        self.is_trained = False

    # ── Training ───────────────────────────────────────────────────
    def train(self, training_data_path: str) -> dict:
        """Learn baseline statistics and train IsolationForest on healthy data."""
        df = pd.read_csv(training_data_path)
        df.columns = df.columns.str.strip()

        # Statistical baselines per sensor
        for col in ALL_SENSOR_COLS:
            series = df[col].dropna()
            self.baselines[col] = {
                'mean': float(series.mean()),
                'std': float(series.std()),
                'min': float(series.min()),
                'max': float(series.max()),
                'q1': float(series.quantile(0.25)),
                'q3': float(series.quantile(0.75)),
                'iqr': float(series.quantile(0.75) - series.quantile(0.25)),
            }

        # Train IsolationForest (unsupervised anomaly detector)
        self.scaler = StandardScaler()
        X = self.scaler.fit_transform(df[ALL_SENSOR_COLS].fillna(0))
        self.isolation_forest = IsolationForest(
            contamination=0.05, random_state=42, n_estimators=150
        )
        self.isolation_forest.fit(X)

        self.is_trained = True
        return self.baselines

    # ── Full analysis of actual data ───────────────────────────────
    def analyze_data(self, actual_data_path: str) -> dict:
        """Run all anomaly detectors on the actual dataset."""
        df = pd.read_csv(actual_data_path)
        df.columns = df.columns.str.strip()

        # Boolean flags
        df['Robot_ProtectiveStop'] = df['Robot_ProtectiveStop'].astype(str).str.strip().str.lower() == 'true'
        df['grip_lost'] = df['grip_lost'].astype(str).str.strip().str.lower() == 'true'

        # IsolationForest scoring
        X = self.scaler.transform(df[ALL_SENSOR_COLS].fillna(0))
        df['anomaly_score'] = self.isolation_forest.decision_function(X)
        df['is_anomaly'] = self.isolation_forest.predict(X) == -1

        anomalies = []

        # ── 1. Electrical Overload ─────────────────────────────────
        for col in CURRENT_COLS:
            bl = self.baselines[col]
            upper = bl['mean'] + 3.5 * bl['std']
            lower = bl['mean'] - 3.5 * bl['std']
            spikes = df[(df[col] > upper) | (df[col] < lower)]
            for _, row in spikes.head(8).iterrows():
                anomalies.append(self._anomaly(
                    'Electrical Overload', 'HIGH', col, row,
                    f"{col} at {row[col]:.2f}A (normal range: {lower:.2f} to {upper:.2f}A)",
                    f"Inspect motor on {col.replace('Current_', 'Joint ')} for electrical faults"
                ))

        # ── 2. Overheating ─────────────────────────────────────────
        for col in TEMP_COLS:
            bl = self.baselines[col]
            threshold = bl['mean'] + 3.5 * bl['std']
            hot = df[df[col] > threshold]
            for _, row in hot.head(6).iterrows():
                anomalies.append(self._anomaly(
                    'Overheating', 'HIGH', col, row,
                    f"{col} at {row[col]:.1f}°C (baseline limit: {threshold:.1f}°C)",
                    f"Check cooling system on {col.replace('Temperature_', 'Joint ').replace('Temperature_T', 'Joint ')}"
                ))

            # Rapid heating (rate of change)
            rate = df[col].diff().rolling(window=15).mean()
            rapid = df[rate > bl['std'] * 1.5]
            for _, row in rapid.head(3).iterrows():
                rate_val = rate.loc[row.name]
                anomalies.append(self._anomaly(
                    'Rapid Heating', 'MEDIUM', col, row,
                    f"{col} rising at {rate_val:.3f}°C/sample",
                    f"Monitor {col.replace('Temperature_', 'Joint ')} — accelerating heat buildup"
                ))

        # ── 3. Repeated Safety Stops ───────────────────────────────
        stops = df[df['Robot_ProtectiveStop']].index.tolist()
        clusters_reported = 0
        for i in range(len(stops) - 2):
            if stops[i + 2] - stops[i] < 60 and clusters_reported < 5:
                row = df.loc[stops[i]]
                anomalies.append(self._anomaly(
                    'Repeated Safety Stops', 'HIGH', 'Robot_ProtectiveStop', row,
                    f"3+ protective stops within 60 readings near row {int(row['Num'])}",
                    "Check for obstacles in robot path; inspect safety sensors"
                ))
                clusters_reported += 1

        grips = df[df['grip_lost']].index.tolist()
        if len(grips) > 3:
            row = df.loc[grips[0]]
            anomalies.append(self._anomaly(
                'Grip Failures', 'MEDIUM', 'grip_lost', row,
                f"{len(grips)} grip-lost events detected",
                "Inspect gripper mechanism and pneumatic pressure"
            ))

        # ── 4. Wear and Tear ──────────────────────────────────────
        quarter = len(df) // 4
        for col in CURRENT_COLS:
            q1_mean = df[col].iloc[:quarter].abs().mean()
            q4_mean = df[col].iloc[-quarter:].abs().mean()
            if q1_mean > 0.01 and q4_mean > q1_mean * 1.15:
                pct = (q4_mean - q1_mean) / q1_mean * 100
                anomalies.append({
                    'type': 'Wear and Tear', 'severity': 'LOW', 'sensor': col,
                    'value': round(pct, 1),
                    'row': int(df['Num'].iloc[-quarter]),
                    'timestamp': str(df['Timestamp'].iloc[-quarter]),
                    'message': f"{col}: current draw increased {pct:.1f}% over the session",
                    'action': f"Schedule preventive maintenance for {col.replace('Current_', 'Joint ')}"
                })

        # ── 5. Sensor Failure ──────────────────────────────────────
        for i in range(6):
            s_col, c_col = f'Speed_J{i}', f'Current_J{i}'
            impossible = df[(df[s_col].abs() > 0.5) & (df[c_col].abs() < 0.02)]
            for _, row in impossible.head(3).iterrows():
                anomalies.append(self._anomaly(
                    'Sensor Failure', 'MEDIUM', f'J{i}', row,
                    f"Joint {i}: speed={row[s_col]:.3f} but current={row[c_col]:.3f} (physically impossible)",
                    f"Inspect sensors on Joint {i} — possible encoder or current sensor malfunction"
                ))

        # ── 6. Tool Current Anomaly ────────────────────────────────
        bl = self.baselines['Tool_current']
        upper = bl['mean'] + 3.5 * bl['std']
        lower = bl['mean'] - 3.5 * bl['std']
        tool_bad = df[(df['Tool_current'] > upper) | (df['Tool_current'] < lower)]
        for _, row in tool_bad.head(4).iterrows():
            anomalies.append(self._anomaly(
                'Tool Current Anomaly', 'MEDIUM', 'Tool_current', row,
                f"Tool current at {row['Tool_current']:.4f}A (normal: {bl['mean']:.4f} ± {bl['std']*3:.4f}A)",
                "Check gripper/end-effector for wear or obstruction"
            ))

        # ── 7. Electrical Noise ────────────────────────────────────
        for col in CURRENT_COLS:
            rolling_std = df[col].rolling(window=20).std()
            bl_std = self.baselines[col]['std']
            noisy = df[rolling_std > bl_std * 2.5]
            for _, row in noisy.head(3).iterrows():
                anomalies.append(self._anomaly(
                    'Electrical Noise', 'LOW', col, row,
                    f"{col}: high variance detected (local σ={rolling_std.loc[row.name]:.3f} vs baseline σ={bl_std:.3f})",
                    f"Check wiring and connections on {col.replace('Current_', 'Joint ')}"
                ))

        # ── Health Timeline (every 100 rows) ──────────────────────
        health_timeline = self._compute_health_timeline(df, 100)

        # ── Per-Joint Health ──────────────────────────────────────
        joint_health = self._compute_joint_health(df)

        # ── Failure Prediction ────────────────────────────────────
        prediction = self._predict_failure(health_timeline)

        # ── Down-sampled sensor data for charts ───────────────────
        step = max(1, len(df) // 200)
        sampled = df.iloc[::step]
        sensor_data = {
            'rows': sampled['Num'].astype(int).tolist(),
            'timestamps': sampled['Timestamp'].tolist(),
        }
        for col in ALL_SENSOR_COLS:
            sensor_data[col] = [round(v, 4) for v in sampled[col].tolist()]

        # ── Summary ───────────────────────────────────────────────
        overall_health = np.mean([j['health_score'] for j in joint_health.values()])
        summary = {
            'overall_health': round(float(overall_health), 1),
            'risk_level': 'LOW' if overall_health > 80 else 'MEDIUM' if overall_health > 50 else 'HIGH',
            'total_anomalies': len(anomalies),
            'high_severity': len([a for a in anomalies if a['severity'] == 'HIGH']),
            'medium_severity': len([a for a in anomalies if a['severity'] == 'MEDIUM']),
            'low_severity': len([a for a in anomalies if a['severity'] == 'LOW']),
            'protective_stops': int(df['Robot_ProtectiveStop'].sum()),
            'grip_losses': int(df['grip_lost'].sum()),
            'anomaly_types': list(set(a['type'] for a in anomalies)),
        }

        return {
            'summary': summary,
            'joint_health': joint_health,
            'anomalies': anomalies,
            'health_timeline': health_timeline,
            'prediction': prediction,
            'sensor_data': sensor_data,
        }

    # ── Custom input prediction ────────────────────────────────────
    def predict_health(self, input_values: dict) -> dict:
        """Score arbitrary sensor values against the trained baseline."""
        scores = {}
        anomalies = []

        for sensor, value in input_values.items():
            if sensor not in self.baselines:
                continue
            bl = self.baselines[sensor]
            z = abs(value - bl['mean']) / bl['std'] if bl['std'] > 0 else 0
            health = max(0, min(100, 100 - z * 16.67))
            status = 'Critical' if z > 3 else 'Warning' if z > 2 else 'Normal'

            scores[sensor] = {
                'health': round(health, 1),
                'z_score': round(z, 2),
                'status': status,
                'value': round(value, 4),
                'baseline_mean': round(bl['mean'], 4),
                'baseline_std': round(bl['std'], 4),
            }
            if z > 2:
                anomalies.append({
                    'sensor': sensor,
                    'value': round(value, 4),
                    'expected': f"{bl['mean']:.3f} ± {bl['std']*2:.3f}",
                    'z_score': round(z, 2),
                    'status': status,
                    'message': f"{sensor} value {value:.3f} is {z:.1f}σ from normal baseline",
                })

        overall = np.mean([s['health'] for s in scores.values()]) if scores else 100.0
        risk = 'LOW' if overall > 80 else 'MEDIUM' if overall > 50 else 'HIGH'

        return {
            'overall_health': round(float(overall), 1),
            'risk_level': risk,
            'sensor_scores': scores,
            'anomalies': anomalies,
            'recommendation': self._recommend(overall, anomalies),
        }

    # ── Private helpers ────────────────────────────────────────────
    @staticmethod
    def _anomaly(atype, severity, sensor, row, message, action):
        return {
            'type': atype, 'severity': severity, 'sensor': sensor,
            'value': round(float(row.get(sensor, 0)) if sensor in row.index else 0, 4),
            'row': int(row['Num']),
            'timestamp': str(row['Timestamp']),
            'message': message, 'action': action,
        }

    def _compute_health_timeline(self, df, window):
        timeline = []
        for start in range(0, len(df), window):
            end = min(start + window, len(df))
            chunk = df.iloc[start:end]
            scores = []
            for col in ALL_SENSOR_COLS:
                bl = self.baselines[col]
                z_max = ((chunk[col] - bl['mean']) / bl['std']).abs().max() if bl['std'] > 0 else 0
                scores.append(max(0, min(100, 100 - z_max * 16.67)))
            timeline.append({
                'row_start': int(start + 1),
                'row_end': int(end),
                'timestamp': str(chunk['Timestamp'].iloc[0]),
                'health_score': round(float(np.mean(scores)), 1),
                'anomaly_count': int(chunk['is_anomaly'].sum()),
            })
        return timeline

    def _compute_joint_health(self, df):
        joint_health = {}
        for i in range(6):
            c_col = f'Current_J{i}'
            t_col = JOINT_TEMP_MAP[i]
            s_col = f'Speed_J{i}'

            def avg_z(col):
                bl = self.baselines[col]
                return ((df[col] - bl['mean']) / bl['std']).abs().mean() if bl['std'] > 0 else 0

            cz, tz, sz = avg_z(c_col), avg_z(t_col), avg_z(s_col)
            health = max(0, min(100, 100 - ((cz + tz + sz) / 3) * 16.67))
            status = lambda z: 'Normal' if z < 2 else 'Warning' if z < 3 else 'Critical'

            joint_health[f'Joint {i}'] = {
                'health_score': round(float(health), 1),
                'current_status': status(cz),
                'temp_status': status(tz),
                'speed_status': status(sz),
                'avg_current': round(float(df[c_col].mean()), 3),
                'avg_temp': round(float(df[t_col].mean()), 1),
                'max_temp': round(float(df[t_col].max()), 1),
            }
        return joint_health

    def _predict_failure(self, timeline):
        """Linear extrapolation of health trend to estimate time-to-critical."""
        if len(timeline) < 5:
            return {'cycles_to_critical': None, 'trend': 'insufficient data'}
        X = np.arange(len(timeline)).reshape(-1, 1)
        y = np.array([t['health_score'] for t in timeline])
        reg = LinearRegression().fit(X, y)
        slope = reg.coef_[0]
        current_health = y[-1]

        if slope >= 0:
            return {
                'cycles_to_critical': None,
                'trend': 'stable',
                'slope': round(float(slope), 3),
                'message': 'Health trend is stable or improving. No imminent failure predicted.',
            }
        # Extrapolate to health = 50
        steps_to_50 = (50 - current_health) / slope if slope < 0 else None
        est_cycles = int(steps_to_50 * 100) if steps_to_50 and steps_to_50 > 0 else None
        return {
            'cycles_to_critical': est_cycles,
            'trend': 'degrading',
            'slope': round(float(slope), 3),
            'message': (
                f"Health declining at {abs(slope):.2f} points per 100 readings. "
                f"Estimated {est_cycles} readings until critical threshold."
                if est_cycles else
                "Health is below critical threshold. Immediate maintenance recommended."
            ),
        }

    @staticmethod
    def _recommend(health, anomalies):
        if health > 90:
            return 'System operating within normal parameters. No maintenance required.'
        if health > 70:
            sensors = ', '.join(set(a['sensor'] for a in anomalies[:3]))
            return f'Minor deviations in {sensors}. Schedule routine inspection within 1 week.'
        if health > 50:
            return f'WARNING: {len(anomalies)} sensor(s) abnormal. Recommend maintenance within 24 hours.'
        return f'CRITICAL: {len(anomalies)} sensor(s) in critical range. Immediate maintenance required. Do not operate.'
