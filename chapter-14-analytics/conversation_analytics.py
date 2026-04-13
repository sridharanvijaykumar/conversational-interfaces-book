"""
Conversation Analytics & Metrics
Chapter 14: Analytics & Performance Optimization

Parses conversation logs and computes the key performance metrics
described in Chapter 14:
  - CSAT (Customer Satisfaction Score)
  - Task Completion Rate
  - Fallback Rate
  - Average Conversation Length (turn count)
  - Conversation Funnel

Generates an interactive HTML dashboard saved to analytics_dashboard.html.
"""

import json
import random
import math
from datetime import datetime, timedelta
from collections import Counter, defaultdict
from dataclasses import dataclass, field
from typing import List, Dict, Optional


# ─────────────────────────────────────────────
# Data structures
# ─────────────────────────────────────────────

@dataclass
class ConversationLog:
    session_id:   str
    channel:      str
    started_at:   str
    ended_at:     str
    turns:        List[Dict]
    csat_score:   Optional[float]    # 1–5; None if not rated
    completed:    bool
    exit_intent:  Optional[str]      # Last intent before drop-off


# ─────────────────────────────────────────────
# Sample data generator
# ─────────────────────────────────────────────

def generate_sample_logs(n: int = 150, seed: int = 42) -> List[ConversationLog]:
    """Generate realistic synthetic conversation logs for demo purposes."""
    random.seed(seed)

    INTENTS    = ["greeting", "book_flight", "check_status", "cancel",
                  "help", "farewell", "fallback"]
    CHANNELS   = ["web", "whatsapp", "mobile_app", "voice"]
    BASE_DATE  = datetime(2026, 3, 1)

    logs = []
    for i in range(n):
        channel   = random.choices(CHANNELS, weights=[40, 25, 25, 10])[0]
        n_turns   = random.choices(range(1, 15), weights=[
            5, 10, 15, 18, 17, 12, 8, 6, 4, 2, 1, 1, 0.5, 0.5
        ])[0]
        start     = BASE_DATE + timedelta(
            days=random.randint(0, 41),
            hours=random.randint(0, 23),
            minutes=random.randint(0, 59),
        )
        end       = start + timedelta(minutes=random.randint(1, 20))
        completed = random.random() < 0.68
        csat      = round(random.gauss(3.8, 0.9), 0) if random.random() < 0.45 else None
        csat      = max(1, min(5, csat)) if csat else None

        turns = []
        for t in range(n_turns):
            intent = random.choices(
                INTENTS,
                weights=[15, 20, 18, 12, 15, 10, 10]
            )[0]
            turns.append({
                "turn":   t + 1,
                "intent": intent,
                "confidence": round(random.uniform(0.55, 0.99), 2),
            })

        exit_intent = turns[-1]["intent"] if not completed else "farewell"

        logs.append(ConversationLog(
            session_id=f"sess_{i:04d}",
            channel=channel,
            started_at=start.isoformat(),
            ended_at=end.isoformat(),
            turns=turns,
            csat_score=csat,
            completed=completed,
            exit_intent=exit_intent,
        ))

    return logs


# ─────────────────────────────────────────────
# Metrics engine
# ─────────────────────────────────────────────

class ConversationMetrics:
    """Computes all KPIs from a list of conversation logs."""

    def __init__(self, logs: List[ConversationLog]):
        self.logs = logs

    def csat(self) -> Dict:
        rated   = [l.csat_score for l in self.logs if l.csat_score is not None]
        if not rated:
            return {"avg": None, "count": 0, "distribution": {}}
        distribution = Counter(int(s) for s in rated)
        return {
            "avg":          round(sum(rated) / len(rated), 2),
            "count":        len(rated),
            "response_rate": round(len(rated) / len(self.logs), 3),
            "distribution": {str(k): distribution[k] for k in range(1, 6)},
        }

    def completion_rate(self) -> Dict:
        completed = sum(1 for l in self.logs if l.completed)
        return {
            "completed":   completed,
            "total":       len(self.logs),
            "rate":        round(completed / len(self.logs), 3),
        }

    def fallback_rate(self) -> Dict:
        total_turns    = sum(len(l.turns) for l in self.logs)
        fallback_turns = sum(
            sum(1 for t in l.turns if t["intent"] == "fallback")
            for l in self.logs
        )
        return {
            "fallback_turns": fallback_turns,
            "total_turns":    total_turns,
            "rate":           round(fallback_turns / total_turns, 3) if total_turns else 0,
        }

    def avg_conversation_length(self) -> Dict:
        lengths = [len(l.turns) for l in self.logs]
        return {
            "mean":   round(sum(lengths) / len(lengths), 1),
            "median": sorted(lengths)[len(lengths) // 2],
            "min":    min(lengths),
            "max":    max(lengths),
        }

    def channel_breakdown(self) -> Dict[str, int]:
        return dict(Counter(l.channel for l in self.logs))

    def intent_distribution(self) -> Dict[str, int]:
        all_intents = [t["intent"] for l in self.logs for t in l.turns]
        return dict(Counter(all_intents).most_common())

    def funnel(self) -> List[Dict]:
        """
        Simplified funnel: how many sessions pass through key stages.
        Stages: Started → Engaged (>1 turn) → Task Attempted → Completed
        """
        started         = len(self.logs)
        engaged         = sum(1 for l in self.logs if len(l.turns) > 1)
        task_attempted  = sum(1 for l in self.logs
                              if any(t["intent"] in ("book_flight", "check_status", "cancel")
                                     for t in l.turns))
        completed       = sum(1 for l in self.logs if l.completed)

        return [
            {"stage": "Started",         "count": started,        "rate": 1.0},
            {"stage": "Engaged (>1 turn)","count": engaged,        "rate": round(engaged / started, 3)},
            {"stage": "Task Attempted",  "count": task_attempted,  "rate": round(task_attempted / started, 3)},
            {"stage": "Completed",       "count": completed,       "rate": round(completed / started, 3)},
        ]

    def daily_volume(self) -> Dict[str, int]:
        """Count conversations per day."""
        volume: Dict[str, int] = defaultdict(int)
        for log in self.logs:
            day = log.started_at[:10]
            volume[day] += 1
        return dict(sorted(volume.items()))

    def drop_off_analysis(self) -> Dict[str, int]:
        """Where do users drop off (last intent before abandoning)?"""
        drop_offs = [l.exit_intent for l in self.logs
                     if not l.completed and l.exit_intent]
        return dict(Counter(drop_offs).most_common())

    def summary(self) -> Dict:
        return {
            "total_conversations": len(self.logs),
            "csat":                self.csat(),
            "completion":          self.completion_rate(),
            "fallback":            self.fallback_rate(),
            "avg_length":          self.avg_conversation_length(),
            "channels":            self.channel_breakdown(),
            "intent_distribution": self.intent_distribution(),
            "funnel":              self.funnel(),
            "daily_volume":        self.daily_volume(),
            "drop_off":            self.drop_off_analysis(),
        }


# ─────────────────────────────────────────────
# HTML Dashboard Generator
# ─────────────────────────────────────────────

def generate_dashboard(metrics_data: Dict, output_path: str = "analytics_dashboard.html"):
    """Generate a standalone interactive HTML analytics dashboard."""
    summary     = metrics_data
    csat        = summary["csat"]
    completion  = summary["completion"]
    fallback    = summary["fallback"]
    avg_len     = summary["avg_length"]
    channels    = summary["channels"]
    funnel      = summary["funnel"]
    daily_vol   = summary["daily_volume"]
    intents     = summary["intent_distribution"]

    # Format series for Chart.js
    daily_labels  = json.dumps(list(daily_vol.keys()))
    daily_values  = json.dumps(list(daily_vol.values()))
    intent_labels = json.dumps(list(intents.keys()))
    intent_values = json.dumps(list(intents.values()))
    chan_labels    = json.dumps(list(channels.keys()))
    chan_values    = json.dumps(list(channels.values()))
    funnel_labels  = json.dumps([f["stage"] for f in funnel])
    funnel_values  = json.dumps([f["count"] for f in funnel])
    csat_labels    = json.dumps(["⭐1","⭐⭐2","⭐⭐⭐3","⭐⭐⭐⭐4","⭐⭐⭐⭐⭐5"])
    csat_values    = json.dumps([csat["distribution"].get(str(k), 0) for k in range(1, 6)])

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <title>Chatbot Analytics Dashboard</title>
  <script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.0/dist/chart.umd.min.js"></script>
  <style>
    * {{ box-sizing: border-box; margin: 0; padding: 0; }}
    body {{ font-family: Arial, sans-serif; background: #f4f6f9; color: #333; }}
    header {{ background: #1F3864; color: white; padding: 20px 32px; }}
    header h1 {{ font-size: 1.5rem; }}
    header p  {{ font-size: 0.85rem; opacity: 0.8; margin-top: 4px; }}
    .grid {{ display: grid; gap: 20px; padding: 24px; }}
    .kpis {{ grid-template-columns: repeat(auto-fit, minmax(180px, 1fr)); }}
    .charts {{ grid-template-columns: repeat(auto-fit, minmax(380px, 1fr)); }}
    .card {{ background: white; border-radius: 10px; padding: 20px;
             box-shadow: 0 1px 4px rgba(0,0,0,0.1); }}
    .kpi-value {{ font-size: 2.2rem; font-weight: bold; color: #1F3864; }}
    .kpi-label {{ font-size: 0.8rem; color: #888; margin-top: 4px; }}
    .kpi-sub   {{ font-size: 0.85rem; color: #555; margin-top: 8px; }}
    .chart-title {{ font-size: 1rem; font-weight: bold; color: #1F3864;
                    margin-bottom: 14px; }}
    canvas {{ max-height: 220px; }}
    .funnel-row {{ display: flex; align-items: center; margin: 6px 0; }}
    .funnel-bar {{ height: 24px; background: #2E75B6; border-radius: 4px;
                   min-width: 4px; transition: width 0.3s; }}
    .funnel-label {{ min-width: 160px; font-size: 0.82rem; color: #555; }}
    .funnel-val {{ margin-left: 10px; font-size: 0.82rem; color: #333; font-weight: bold; }}
    footer {{ text-align: center; padding: 16px; font-size: 0.75rem; color: #aaa; }}
  </style>
</head>
<body>

<header>
  <h1>📊 Chatbot Analytics Dashboard</h1>
  <p>Generated: {datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC')} &nbsp;|&nbsp;
     Total conversations: {summary['total_conversations']}</p>
</header>

<!-- KPI Cards -->
<div class="grid kpis">
  <div class="card">
    <div class="kpi-value">{csat['avg'] if csat['avg'] else 'N/A'}</div>
    <div class="kpi-label">Avg CSAT Score (/ 5)</div>
    <div class="kpi-sub">Based on {csat['count']} ratings
     ({csat.get('response_rate',0):.0%} response rate)</div>
  </div>
  <div class="card">
    <div class="kpi-value">{completion['rate']:.0%}</div>
    <div class="kpi-label">Task Completion Rate</div>
    <div class="kpi-sub">{completion['completed']} of {completion['total']} sessions</div>
  </div>
  <div class="card">
    <div class="kpi-value">{fallback['rate']:.1%}</div>
    <div class="kpi-label">Fallback Rate</div>
    <div class="kpi-sub">{fallback['fallback_turns']} of {fallback['total_turns']} turns</div>
  </div>
  <div class="card">
    <div class="kpi-value">{avg_len['mean']}</div>
    <div class="kpi-label">Avg Turns / Conversation</div>
    <div class="kpi-sub">Median: {avg_len['median']} &nbsp;|&nbsp;
      Max: {avg_len['max']}</div>
  </div>
</div>

<!-- Charts -->
<div class="grid charts">
  <div class="card">
    <div class="chart-title">Daily Conversation Volume</div>
    <canvas id="dailyChart"></canvas>
  </div>
  <div class="card">
    <div class="chart-title">Intent Distribution</div>
    <canvas id="intentChart"></canvas>
  </div>
  <div class="card">
    <div class="chart-title">Channel Breakdown</div>
    <canvas id="channelChart"></canvas>
  </div>
  <div class="card">
    <div class="chart-title">CSAT Score Distribution</div>
    <canvas id="csatChart"></canvas>
  </div>
  <div class="card">
    <div class="chart-title">Conversation Funnel</div>
    {''.join(
        f'<div class="funnel-row">'
        f'<div class="funnel-label">{f["stage"]}</div>'
        f'<div class="funnel-bar" style="width:{f[\"rate\"]*300:.0f}px"></div>'
        f'<div class="funnel-val">{f["count"]} ({f["rate"]:.0%})</div>'
        f'</div>'
        for f in funnel
    )}
  </div>
  <div class="card">
    <div class="chart-title">Drop-off Points</div>
    <canvas id="dropoffChart"></canvas>
  </div>
</div>

<footer>Conversational Interfaces and Chatbot UI Design — Vijay Kumar Sridharan</footer>

<script>
const BLUE  = '#2E75B6', NAVY = '#1F3864', LBLUE = '#D6E4F7';
const PALETTE = ['#2E75B6','#1F3864','#4CAF50','#FF9800','#E91E63','#9C27B0','#00BCD4'];

new Chart(document.getElementById('dailyChart'), {{
  type: 'line',
  data: {{ labels: {daily_labels}, datasets: [{{
    label: 'Conversations', data: {daily_values},
    borderColor: BLUE, backgroundColor: LBLUE, fill: true, tension: 0.3,
  }}]}},
  options: {{ plugins: {{ legend: {{ display: false }} }}, scales: {{ y: {{ beginAtZero: true }} }} }}
}});

new Chart(document.getElementById('intentChart'), {{
  type: 'bar',
  data: {{ labels: {intent_labels}, datasets: [{{
    label: 'Turns', data: {intent_values},
    backgroundColor: PALETTE,
  }}]}},
  options: {{ plugins: {{ legend: {{ display: false }} }}, scales: {{ y: {{ beginAtZero: true }} }} }}
}});

new Chart(document.getElementById('channelChart'), {{
  type: 'doughnut',
  data: {{ labels: {chan_labels}, datasets: [{{ data: {chan_values}, backgroundColor: PALETTE }}]}},
  options: {{ plugins: {{ legend: {{ position: 'right' }} }} }}
}});

new Chart(document.getElementById('csatChart'), {{
  type: 'bar',
  data: {{ labels: {csat_labels}, datasets: [{{
    label: 'Responses', data: {csat_values},
    backgroundColor: ['#E53935','#FB8C00','#FDD835','#7CB342','#2E75B6'],
  }}]}},
  options: {{ plugins: {{ legend: {{ display: false }} }}, scales: {{ y: {{ beginAtZero: true }} }} }}
}});

const dropoff = {json.dumps(summary["drop_off"])};
new Chart(document.getElementById('dropoffChart'), {{
  type: 'bar',
  data: {{ labels: Object.keys(dropoff), datasets: [{{
    label: 'Drop-offs', data: Object.values(dropoff),
    backgroundColor: '#E53935',
  }}]}},
  options: {{ plugins: {{ legend: {{ display: false }} }}, scales: {{ y: {{ beginAtZero: true }} }} }}
}});
</script>
</body>
</html>"""

    with open(output_path, "w") as f:
        f.write(html)
    print(f"Dashboard saved to {output_path}")
    return output_path


# ─────────────────────────────────────────────
# Main
# ─────────────────────────────────────────────

if __name__ == "__main__":
    print("Generating sample conversation logs...")
    logs = generate_sample_logs(n=150)

    print(f"Analysing {len(logs)} conversations...\n")
    metrics = ConversationMetrics(logs)
    data    = metrics.summary()

    # Print key metrics to console
    csat = data["csat"]
    comp = data["completion"]
    fb   = data["fallback"]
    avl  = data["avg_length"]

    print(f"{'─'*40}")
    print(f"  Total conversations:   {data['total_conversations']}")
    print(f"  CSAT (avg / 5):        {csat['avg']}  ({csat['count']} ratings)")
    print(f"  Completion rate:       {comp['rate']:.1%}")
    print(f"  Fallback rate:         {fb['rate']:.1%}")
    print(f"  Avg turns/conv:        {avl['mean']}")
    print(f"\n  Funnel:")
    for stage in data["funnel"]:
        print(f"    {stage['stage']:<22} {stage['count']:>4}  ({stage['rate']:.0%})")
    print(f"{'─'*40}\n")

    # Generate dashboard
    generate_dashboard(data, "analytics_dashboard.html")
    print("\nOpen analytics_dashboard.html in your browser to view the dashboard.")
