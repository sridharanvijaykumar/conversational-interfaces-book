# Chapter 11: Architecture & Backend Integration

Working code examples for the system architecture patterns described in Chapter 11, including a Flask REST API backend, external API integration, and database-backed conversation storage.

## Files

| File | Description |
|------|-------------|
| `chatbot_backend.py` | A production-style Flask REST API for chatbot backends |
| `api_integration.py` | External API integration patterns (weather, generic REST client, webhooks) |
| `database_storage.py` | SQLite-backed conversation persistence (sessions, messages, user profiles) |

---

## chatbot_backend.py

A fully working **Flask REST API** that exposes the chatbot as a service any frontend can call.

**Endpoints:**
| Method | Path | Description |
|--------|------|-------------|
| GET | `/health` | Health check |
| POST | `/chat` | Send a message, get a response |
| GET | `/session/<id>/history` | Retrieve full conversation history |
| DELETE | `/session/<id>` | End a session |

**Run it:**
```bash
pip install flask flask-cors
python chatbot_backend.py
```

**Test with curl:**
```bash
# Start a conversation
curl -X POST http://localhost:5000/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "Hello!"}'

# Continue the same session
curl -X POST http://localhost:5000/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "What are your hours?", "session_id": "<id from above>"}'
```

---

## api_integration.py

Demonstrates three common integration patterns:

1. **Weather Service** — calls the free Open-Meteo API to fetch live weather data based on a city name extracted by the NLU. No API key required.
2. **Generic REST Client** — a reusable `APIClient` class with retry logic, exponential back-off, and timeout handling.
3. **Webhook Receiver** — a Flask blueprint that receives inbound events from external systems (payments, CRM updates) with HMAC signature verification.

**Run the demo:**
```bash
pip install requests flask
python api_integration.py
```

---

## database_storage.py

Shows how to persist conversation data using **SQLite** locally, with the same interface you'd use against PostgreSQL in production.

**What's stored:**
- `sessions` — one row per conversation, with channel and user metadata
- `messages` — every turn (user + bot text, intent, confidence, entities)
- `user_profiles` — persistent preferences across sessions

**Run the demo:**
```bash
python database_storage.py
```

---

## Architecture Diagram

Refer to **Figure 11.1** in the book for the full system architecture showing how these components connect:

```
[Web / Mobile / Voice Frontend]
           │
           ▼
   [Flask REST API]  ←──→  [Session Store / DB]
           │
           ▼
   [Chat Engine / NLU]
           │
     ┌─────┴──────┐
     ▼            ▼
[LLM / Rasa]  [External APIs]
```

## Requirements

```bash
pip install flask flask-cors requests
```
