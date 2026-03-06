"""
Offline rule-based chat assistant for FANUC cobot predictive maintenance.
No LLM required — uses keyword matching + cached analysis results.
"""


class ChatEngine:
    """Generates natural-language answers from analysis data."""

    def __init__(self):
        self.analysis = None
        self.baselines = None

    def load(self, analysis: dict, baselines: dict):
        self.analysis = analysis
        self.baselines = baselines

    # ── Main entry point ───────────────────────────────────────────
    def respond(self, message: str) -> str:
        if not self.analysis:
            return ("I don't have any analysis data yet. "
                    "Please make sure the model has been trained and the actual data has been analyzed.")

        msg = message.lower().strip()

        # Joint-specific
        for i in range(6):
            if f'joint {i}' in msg or f'j{i}' in msg or f'joint{i}' in msg:
                return self._joint_report(i)

        # Topic routing
        if any(w in msg for w in ['temperature', 'temp', 'hot', 'heat', 'overheat', 'cool']):
            return self._temperature_report()

        if any(w in msg for w in ['current', 'electrical', 'power', 'motor', 'amp', 'overload']):
            return self._current_report()

        if any(w in msg for w in ['what', 'wrong', 'problem', 'issue', 'anomal', 'detect', 'find', 'found']):
            return self._anomaly_summary()

        if any(w in msg for w in ['health', 'score', 'status', 'overall', 'how is', 'how are']):
            return self._health_summary()

        if any(w in msg for w in ['maintenance', 'schedule', 'fix', 'repair', 'recommend', 'action', 'next step']):
            return self._maintenance_report()

        if any(w in msg for w in ['safe', 'safety', 'stop', 'protective', 'operate']):
            return self._safety_report()

        if any(w in msg for w in ['predict', 'forecast', 'future', 'when', 'how long', 'failure', 'time to']):
            return self._prediction_report()

        if any(w in msg for w in ['grip', 'gripper', 'tool', 'drop', 'pick']):
            return self._tool_report()

        if any(w in msg for w in ['sensor', 'noise', 'signal', 'wiring']):
            return self._sensor_report()

        if any(w in msg for w in ['help', 'what can', 'commands']):
            return self._help()

        if any(w in msg for w in ['hi', 'hello', 'hey', 'good morning']):
            return self._greeting()

        return self._default()

    # ── Report generators ──────────────────────────────────────────
    def _joint_report(self, joint_idx: int) -> str:
        jh = self.analysis['joint_health'].get(f'Joint {joint_idx}')
        if not jh:
            return f"No data available for Joint {joint_idx}."

        status_icon = {'Normal': '🟢', 'Warning': '🟡', 'Critical': '🔴'}
        anomalies = [a for a in self.analysis['anomalies']
                     if f'J{joint_idx}' in a.get('sensor', '') or f'Joint {joint_idx}' in a.get('sensor', '')]

        lines = [
            f"## Joint {joint_idx} Health Report",
            f"**Health Score: {jh['health_score']}/100**\n",
            f"| Metric | Status |",
            f"|--------|--------|",
            f"| Current | {status_icon.get(jh['current_status'], '⚪')} {jh['current_status']} (avg: {jh['avg_current']:.3f}A) |",
            f"| Temperature | {status_icon.get(jh['temp_status'], '⚪')} {jh['temp_status']} (avg: {jh['avg_temp']:.1f}°C, max: {jh['max_temp']:.1f}°C) |",
            f"| Speed | {status_icon.get(jh['speed_status'], '⚪')} {jh['speed_status']} |",
        ]

        if anomalies:
            lines.append(f"\n**⚠️ {len(anomalies)} anomalie(s) detected:**")
            for a in anomalies[:5]:
                lines.append(f"- **{a['type']}**: {a['message']}")
            lines.append(f"\n**Recommended action:** {anomalies[0]['action']}")
        else:
            lines.append("\n✅ No anomalies detected on this joint.")

        return '\n'.join(lines)

    def _temperature_report(self) -> str:
        temp_anomalies = [a for a in self.analysis['anomalies']
                          if a['type'] in ('Overheating', 'Rapid Heating')]
        s = self.analysis['summary']

        lines = ["## 🌡️ Temperature Analysis\n"]
        if temp_anomalies:
            lines.append(f"**{len(temp_anomalies)} temperature anomalie(s) detected:**\n")
            for a in temp_anomalies[:6]:
                sev = '🔴' if a['severity'] == 'HIGH' else '🟡'
                lines.append(f"- {sev} **{a['type']}** on {a['sensor']}: {a['message']}")
            lines.append(f"\n**Recommendation:** {temp_anomalies[0]['action']}")
        else:
            lines.append("✅ All temperature readings are within normal range.")

        # Show baselines
        lines.append("\n**Temperature baselines (from training data):**")
        for col in ['Temperature_T0'] + [f'Temperature_J{i}' for i in range(1, 6)]:
            bl = self.baselines.get(col, {})
            if bl:
                lines.append(f"- {col}: {bl['mean']:.1f}°C ± {bl['std']:.1f}°C")

        return '\n'.join(lines)

    def _current_report(self) -> str:
        curr_anomalies = [a for a in self.analysis['anomalies']
                          if a['type'] in ('Electrical Overload', 'Wear and Tear', 'Electrical Noise')]
        lines = ["## ⚡ Electrical / Current Analysis\n"]
        if curr_anomalies:
            lines.append(f"**{len(curr_anomalies)} electrical anomalie(s) detected:**\n")
            for a in curr_anomalies[:8]:
                sev = '🔴' if a['severity'] == 'HIGH' else '🟡' if a['severity'] == 'MEDIUM' else '🟢'
                lines.append(f"- {sev} **{a['type']}** on {a['sensor']}: {a['message']}")
            lines.append(f"\n**Recommendation:** Inspect motor connections and check for short circuits.")
        else:
            lines.append("✅ All current readings are within normal range.")
        return '\n'.join(lines)

    def _anomaly_summary(self) -> str:
        s = self.analysis['summary']
        lines = [
            "## 🔍 Anomaly Summary\n",
            f"**Total anomalies detected: {s['total_anomalies']}**\n",
            f"| Severity | Count |",
            f"|----------|-------|",
            f"| 🔴 High | {s['high_severity']} |",
            f"| 🟡 Medium | {s['medium_severity']} |",
            f"| 🟢 Low | {s['low_severity']} |\n",
            f"**Types detected:** {', '.join(s['anomaly_types'])}\n",
        ]

        # Top 5 anomalies
        high = [a for a in self.analysis['anomalies'] if a['severity'] == 'HIGH']
        if high:
            lines.append("**Most critical findings:**")
            for a in high[:5]:
                lines.append(f"- 🔴 **{a['type']}** ({a['sensor']}): {a['message']}")

        return '\n'.join(lines)

    def _health_summary(self) -> str:
        s = self.analysis['summary']
        jh = self.analysis['joint_health']
        icon = '🟢' if s['overall_health'] > 80 else '🟡' if s['overall_health'] > 50 else '🔴'

        lines = [
            f"## {icon} System Health Overview\n",
            f"**Overall Health Score: {s['overall_health']}/100** — Risk Level: **{s['risk_level']}**\n",
            "| Joint | Health | Status |",
            "|-------|--------|--------|",
        ]
        for name, data in jh.items():
            ji = '🟢' if data['health_score'] > 80 else '🟡' if data['health_score'] > 50 else '🔴'
            lines.append(f"| {name} | {ji} {data['health_score']}/100 | Curr: {data['current_status']}, Temp: {data['temp_status']} |")

        return '\n'.join(lines)

    def _maintenance_report(self) -> str:
        s = self.analysis['summary']
        pred = self.analysis.get('prediction', {})
        high = [a for a in self.analysis['anomalies'] if a['severity'] == 'HIGH']

        lines = ["## 🔧 Maintenance Recommendations\n"]

        if s['overall_health'] < 50:
            lines.append("**🔴 URGENT: Immediate maintenance required!**\n")
        elif s['overall_health'] < 70:
            lines.append("**🟡 Schedule maintenance within 24 hours.**\n")
        else:
            lines.append("**🟢 Routine inspection recommended.**\n")

        if high:
            lines.append("**Priority actions:**")
            actions = list(set(a['action'] for a in high))
            for i, action in enumerate(actions[:5], 1):
                lines.append(f"{i}. {action}")

        if pred and pred.get('cycles_to_critical'):
            lines.append(f"\n**⏱️ Estimated readings until critical: {pred['cycles_to_critical']}**")
        if pred:
            lines.append(f"**Trend: {pred.get('message', 'N/A')}**")

        return '\n'.join(lines)

    def _safety_report(self) -> str:
        s = self.analysis['summary']
        stops = s.get('protective_stops', 0)
        grips = s.get('grip_losses', 0)

        lines = [
            "## 🛡️ Safety Report\n",
            f"| Event | Count |",
            f"|-------|-------|",
            f"| Protective Stops | {stops} |",
            f"| Grip Losses | {grips} |\n",
        ]

        if stops > 10:
            lines.append(f"**⚠️ {stops} protective stops is ABOVE normal.** This indicates the robot is detecting hazards frequently.")
            lines.append("**Recommendation:** Check for obstacles, recalibrate safety zones, inspect safety sensors.")
        elif stops > 0:
            lines.append(f"Protective stops ({stops}) are within acceptable limits.")

        safe = s['overall_health'] > 60 and stops < 20
        lines.append(f"\n**Safe to operate:** {'✅ Yes, with monitoring' if safe else '❌ No — address issues first'}")

        return '\n'.join(lines)

    def _prediction_report(self) -> str:
        pred = self.analysis.get('prediction', {})
        s = self.analysis['summary']

        lines = [
            "## 🔮 Failure Prediction\n",
            f"**Current Health:** {s['overall_health']}/100",
            f"**Health Trend:** {pred.get('trend', 'unknown').title()}",
            f"**Slope:** {pred.get('slope', 'N/A')} points per 100 readings\n",
        ]

        if pred.get('cycles_to_critical'):
            lines.append(f"**⏱️ Estimated {pred['cycles_to_critical']} readings until critical threshold (health < 50).**")
            lines.append(f"\n{pred.get('message', '')}")
        elif pred.get('trend') == 'stable':
            lines.append("✅ No failure predicted in the near term. Health trend is stable.")
        else:
            lines.append("⚠️ System is already below critical threshold. Immediate action required.")

        return '\n'.join(lines)

    def _tool_report(self) -> str:
        tool_anomalies = [a for a in self.analysis['anomalies']
                          if 'Tool' in a.get('sensor', '') or 'grip' in a.get('sensor', '').lower()
                          or a['type'] in ('Tool Current Anomaly', 'Grip Failures')]
        bl = self.baselines.get('Tool_current', {})

        lines = ["## 🔧 Tool / Gripper Report\n"]
        if bl:
            lines.append(f"**Baseline tool current:** {bl['mean']:.4f}A ± {bl['std']:.4f}A\n")
        if tool_anomalies:
            for a in tool_anomalies[:5]:
                lines.append(f"- ⚠️ **{a['type']}**: {a['message']}")
            lines.append(f"\n**Recommendation:** {tool_anomalies[0]['action']}")
        else:
            lines.append("✅ Tool/gripper operation is normal.")
        return '\n'.join(lines)

    def _sensor_report(self) -> str:
        sensor_anomalies = [a for a in self.analysis['anomalies']
                            if a['type'] in ('Sensor Failure', 'Electrical Noise')]
        lines = ["## 📡 Sensor Health Report\n"]
        if sensor_anomalies:
            for a in sensor_anomalies[:6]:
                lines.append(f"- ⚠️ **{a['type']}** on {a['sensor']}: {a['message']}")
        else:
            lines.append("✅ All sensors appear to be functioning correctly.")
        return '\n'.join(lines)

    def _greeting(self) -> str:
        s = self.analysis['summary']
        return (
            f"Hello! I'm your FANUC CR-7iA/L maintenance assistant. 🤖\n\n"
            f"**Current system status:** Health {s['overall_health']}/100 "
            f"({'Good' if s['overall_health'] > 80 else 'Needs Attention' if s['overall_health'] > 50 else 'Critical'})\n\n"
            f"I detected **{s['total_anomalies']} anomalies** ({s['high_severity']} high severity).\n\n"
            f"Ask me about specific joints, temperatures, maintenance recommendations, or safety status!"
        )

    def _help(self) -> str:
        return (
            "## 💡 I can help with:\n\n"
            "- **\"What's wrong?\"** — Overview of all detected anomalies\n"
            "- **\"Joint 3\"** — Detailed report on a specific joint (0-5)\n"
            "- **\"Temperature\"** — Temperature analysis across all joints\n"
            "- **\"Current\"** — Electrical/current analysis\n"
            "- **\"Health\"** — Overall system health score\n"
            "- **\"Maintenance\"** — Recommended maintenance actions\n"
            "- **\"Safety\"** — Safety stop and grip analysis\n"
            "- **\"Predict\"** — Failure prediction and timeline\n"
            "- **\"Tool\"** — Gripper/end-effector status\n"
            "- **\"Sensor\"** — Sensor health and noise check\n"
        )

    def _default(self) -> str:
        return (
            "I'm not sure what you're asking about. Try one of these:\n\n"
            "- **\"What's wrong with the robot?\"**\n"
            "- **\"Tell me about Joint 3\"**\n"
            "- **\"Is it safe to operate?\"**\n"
            "- **\"When should we schedule maintenance?\"**\n"
            "- **\"What does the temperature look like?\"**\n\n"
            "Type **help** for a full list of topics."
        )
