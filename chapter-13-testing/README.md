# Chapter 13: Testing & Quality Assurance

Working implementations of the three core testing disciplines described in Chapter 13: automated usability testing, A/B testing, and NLU training data analysis.

## Files

| File | Description |
|------|-------------|
| `usability_testing.py` | Scripted end-to-end usability test runner with detailed reporting |
| `ab_testing.py` | A/B test framework for comparing response variants with statistical significance |
| `nlu_optimization.py` | NLU training data analyser — detects duplicates, imbalance, and intent confusion |

---

## usability_testing.py

Runs **scripted test conversations** against your chatbot and scores each turn on intent matching, keyword presence, forbidden content, and latency.

Works against:
- A **mock chatbot** built-in (no server needed, great for quick runs)
- A **live endpoint** — pass your server URL to `ChatbotTestRunner(endpoint="http://localhost:5000")`

**Run:**
```bash
python usability_testing.py
```

**Sample output:**
```
✅ PASS  Basic Greeting Flow        score=100%  turns=2
✅ PASS  Store Hours Query          score=100%  turns=3
✅ PASS  Return Policy              score=100%  turns=2
✅ PASS  Fallback Handling          score=100%  turns=1

  Total turns: 8  |  Passed: 8 (100%)  |  Fallback rate: 1/8 (12%)
  Avg latency: 0.1 ms  |  P95 latency: 0.2 ms
```

---

## ab_testing.py

A full **A/B testing framework** with sticky variant assignment (same session = same variant), conversion tracking, and a two-proportion z-test for statistical significance.

**Run the demo** (simulates 200 sessions with realistic conversion rates):
```bash
python ab_testing.py
```

**Integrate into your chatbot:**
```python
from ab_testing import ABTestManager, ABTest, Variant

manager = ABTestManager()
manager.register_test(ABTest(
    test_id="welcome_v2",
    name="Welcome Message Test",
    metric="engagement",
    variants=[
        Variant("control",   "Formal",   "Hello. How may I assist?",     weight=0.5),
        Variant("treatment", "Friendly", "Hey! 👋 What can I do for you?", weight=0.5),
    ]
))

# In your chat handler:
variant = manager.get_variant("welcome_v2", session_id)
# Show variant.response to the user

# When user engages (completes a task, gives high CSAT, etc.):
manager.record_conversion("welcome_v2", session_id)

# Check results anytime:
manager.print_report("welcome_v2")
```

---

## nlu_optimization.py

Analyses your **NLU training data** (the utterances you use to train your chatbot) and surfaces common quality problems before they affect model performance:

| Check | What it catches |
|-------|----------------|
| Class balance | Intents with too few examples |
| Duplicates | Identical or near-identical utterances |
| Short utterances | Single-word or two-word phrases that are too ambiguous |
| Intent confusion | Intents that share vocabulary and may be confused |

**Run:**
```bash
python nlu_optimization.py
```

**Use with your own data:**
```python
from nlu_optimization import NLUAnalyzer

my_data = {
    "order_status": ["where is my order", "track my package", ...],
    "cancel_order": ["cancel my order", "I want to cancel", ...],
}

analyzer = NLUAnalyzer(my_data)
analyzer.analyse()
analyzer.print_report()
```

---

## Requirements

```bash
pip install -r ../../requirements.txt
```

All three scripts have **zero external dependencies** beyond the standard library. The `requests` package is optional for running usability tests against a live endpoint.
