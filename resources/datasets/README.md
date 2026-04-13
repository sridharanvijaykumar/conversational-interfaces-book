# Sample Datasets

This folder contains sample datasets referenced throughout the book for hands-on exercises and code examples.

## Files

| File | Format | Description | Chapter |
|------|--------|-------------|---------|
| `intent_training_data.json` | JSON (Rasa NLU) | 45 annotated utterances across 8 intents with entities | Ch. 3, 6 |
| `entity_annotation_sample.json` | JSON (spaCy-style) | 12 entity-annotated sentences covering 6 entity types | Ch. 3 |
| `conversation_logs_sample.csv` | CSV | 10 multi-turn conversation logs with CSAT scores | Ch. 13, 14 |
| `ab_test_results_sample.csv` | CSV | 50 session records across 2 A/B tests and 4 variants | Ch. 13 |

---

## intent_training_data.json

Rasa-compatible NLU training file. Contains:
- **8 intents:** `greeting`, `farewell`, `track_order`, `return_product`, `shipping_info`, `cancel_order`, `payment_info`, `escalate`
- **2 entity types:** `order_id` (regex), `location` (lookup table)
- Character-level entity offsets for every example

Load in Python:
```python
import json

with open("intent_training_data.json") as f:
    data = json.load(f)["rasa_nlu_data"]

for ex in data["common_examples"]:
    print(ex["intent"], "→", ex["text"])
```

---

## entity_annotation_sample.json

12 sentences labelled with spaCy-style `(start, end, label)` entity spans. Suitable for:
- Training a custom NER model
- Demonstrating entity extraction logic (Chapter 3)
- Unit-testing entity parsers

Load in Python:
```python
import json
from chapter_03_nlp_fundamentals.entity_extraction import extract_entities

with open("entity_annotation_sample.json") as f:
    samples = json.load(f)["annotations"]

for sample in samples:
    print(sample["text"])
    print("  Gold entities:", sample["entities"])
```

---

## conversation_logs_sample.csv

10 realistic multi-turn conversation logs simulating a customer support chatbot. Columns:

| Column | Type | Description |
|--------|------|-------------|
| `session_id` | string | Unique session identifier |
| `turn` | int | Turn number within session |
| `timestamp` | ISO 8601 | When the turn occurred |
| `channel` | string | `web`, `mobile`, `whatsapp`, `voice` |
| `user_input` | string | Raw user message |
| `detected_intent` | string | Intent classification result |
| `confidence` | float | Model confidence score (0–1) |
| `bot_response` | string | Bot's reply |
| `csat_score` | int (1–5) | Post-conversation rating (end turn only) |
| `completed` | bool | Whether the user's goal was met |
| `exit_intent` | string | Intent at conversation end |

Load with pandas:
```python
import pandas as pd
df = pd.read_csv("conversation_logs_sample.csv")
print(df.groupby("detected_intent")["confidence"].mean())
```

---

## ab_test_results_sample.csv

50 session records across two A/B tests (`test_welcome_flow`, `test_cta_phrasing`), each with a `control` and `variant_b`. Columns:

| Column | Type | Description |
|--------|------|-------------|
| `test_id` | string | Which test this session belongs to |
| `variant` | string | `control` or `variant_b` |
| `session_id` | string | Unique session |
| `assigned_at` | ISO 8601 | When the user was assigned |
| `converted` | bool | Whether conversion goal was met |
| `conversion_event` | string | `task_complete`, `drop_off`, `escalate` |
| `session_length_turns` | int | Number of dialogue turns |
| `csat_score` | int (1–5) | Post-session rating (if given) |
| `channel` | string | Delivery channel |

Use with `chapter-13-testing/ab_testing.py`:
```python
import pandas as pd
from chapter_13_testing.ab_testing import ABTestManager

df = pd.read_csv("ab_test_results_sample.csv")
# Feed conversion data into ABTestManager for significance testing
```
