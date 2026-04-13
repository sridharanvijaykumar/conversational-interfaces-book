# Chapter 16: Industry Use-Cases

Three fully functional industry-specific chatbot implementations corresponding to the use-cases discussed in Chapter 16.

## Files

| File | Description |
|------|-------------|
| `customer_support_bot.py` | FAQ + order lookup + human escalation |
| `healthcare_assistant.py` | Appointment booking with symptom triage |
| `ecommerce_bot.py` | Product search, cart management, and personalised recommendations |

---

## customer_support_bot.py

A **customer support bot** for an e-commerce company, handling:
- Greetings, thanks, and goodbyes
- FAQ answering across 7 topic areas (returns, shipping, payment, warranty, coupons, etc.)
- Order status lookup by ID (e.g. `ORD-1001`)
- Human agent escalation

**Run:**
```bash
python customer_support_bot.py
```

**Try these inputs:**
```
"Hi"
"I want to return something"
"Where is my order ORD-1002?"
"What payment methods do you accept?"
"Connect me to an agent"
```

---

## healthcare_assistant.py

An **appointment booking assistant** for a medical clinic. Demonstrates slot-filling through a multi-turn conversation to collect specialty, day, and time preferences.

Features:
- Symptom triage → automatic specialist suggestion
- Emergency symptom detection with immediate escalation
- Available slot management per day
- Full booking confirmation

> ⚠️ **Disclaimer:** This is a demonstration only. Not a substitute for real medical advice.

**Run:**
```bash
python healthcare_assistant.py
```

**Try these inputs:**
```
"I need to book a doctor"
"I have a skin rash and itching"
"Tuesday"
"09:30"
"yes"
```

---

## ecommerce_bot.py

A **shopping assistant** that lets users discover products, manage a cart, and track orders — entirely through natural language.

Features:
- Product search by keyword or category
- Budget filtering ("show me items under ₹2000")
- Cart management (add, remove, view, clear)
- Contextual upsell suggestions
- Order tracking (uses same mock database as customer_support_bot.py)
- Top product recommendations

**Run:**
```bash
python ecommerce_bot.py
```

**Try these inputs:**
```
"Show me wireless headphones"
"add 1"
"What's in my cart?"
"Recommend something popular"
"Products under ₹1500"
"checkout"
```

---

## Requirements

```bash
pip install -r ../../requirements.txt
```

All three bots are **pure Python** — no external dependencies or API keys required.

> **Note:** `ecommerce_bot.py` imports the `ORDERS` dictionary from `customer_support_bot.py` for the order tracking feature. Keep both files in the same directory.
