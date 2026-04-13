# Chapter 14: Analytics & Performance Optimization

A complete conversation analytics pipeline that generates synthetic logs, computes all the key metrics described in Chapter 14, and produces an interactive HTML dashboard.

## Files

| File | Description |
|------|-------------|
| `conversation_analytics.py` | Full analytics pipeline: log parsing → KPI computation → interactive dashboard |

---

## What it does

1. **Generates 150 synthetic conversation logs** (realistic distribution of intents, channels, CSAT scores, and completion outcomes).
2. **Computes all Chapter 14 KPIs:**

| Metric | Description |
|--------|-------------|
| CSAT Score | Average customer satisfaction (1–5) and response rate |
| Task Completion Rate | % of conversations where the user completed their goal |
| Fallback Rate | % of turns where the bot had no confident response |
| Avg Conversation Length | Mean and median turn count |
| Channel Breakdown | Distribution across web, WhatsApp, mobile, voice |
| Intent Distribution | Which intents are triggered most |
| Conversation Funnel | Started → Engaged → Task Attempted → Completed |
| Drop-off Analysis | Where users abandon the conversation |
| Daily Volume | Conversations per day over the period |

3. **Generates `analytics_dashboard.html`** — a fully interactive, standalone dashboard built with Chart.js. No server required; just open in a browser.

---

## Run it

```bash
python conversation_analytics.py
```

Then open `analytics_dashboard.html` in your browser.

**Sample console output:**
```
Analysing 150 conversations...

────────────────────────────────────────
  Total conversations:   150
  CSAT (avg / 5):        3.82  (68 ratings)
  Completion rate:       68.0%
  Fallback rate:         9.8%
  Avg turns/conv:        6.3

  Funnel:
    Started               150  (100%)
    Engaged (>1 turn)     138  ( 92%)
    Task Attempted        103  ( 69%)
    Completed             102  ( 68%)
────────────────────────────────────────

Dashboard saved to analytics_dashboard.html
```

---

## Using with real data

Replace the `generate_sample_logs()` call with your own log loading function. Each log should be a `ConversationLog` object:

```python
from conversation_analytics import ConversationLog, ConversationMetrics, generate_dashboard

logs = [
    ConversationLog(
        session_id="abc123",
        channel="web",
        started_at="2026-03-15T10:00:00",
        ended_at="2026-03-15T10:08:00",
        turns=[
            {"turn": 1, "intent": "greeting",    "confidence": 0.95},
            {"turn": 2, "intent": "book_flight",  "confidence": 0.88},
            {"turn": 3, "intent": "farewell",     "confidence": 0.97},
        ],
        csat_score=4,
        completed=True,
        exit_intent="farewell",
    ),
    # ... more logs
]

metrics = ConversationMetrics(logs)
data    = metrics.summary()
generate_dashboard(data, "my_dashboard.html")
```

## Requirements

```bash
pip install -r ../../requirements.txt
```

No external dependencies needed — only the Python standard library and Chart.js (loaded from CDN in the dashboard).
