# Chapter 10: Dialogflow CX — Sample Agent

A complete Dialogflow CX agent export demonstrating the concepts covered in Chapter 10, including intent design, entity extraction, context management, and webhook fulfillment.

## Files

| File / Folder | Description |
|---------------|-------------|
| `agent.json` | Top-level agent metadata (display name, language, timezone) |
| `intents/greeting.json` | 12 training phrases for greeting intent |
| `intents/track_order.json` | Order tracking with `@order_id` entity slot-filling |
| `intents/return_product.json` | Return / refund handling |
| `intents/escalate.json` | Human handoff with live-agent metadata |
| `intents/fallback.json` | Default fallback (low-confidence catch-all) |
| `entities/order_id.json` | Regex entity matching `ORD-XXXX` |
| `entities/product_name.json` | List entity with 8 products + synonyms |
| `webhook_fulfillment.py` | Flask webhook fulfilling `track.order`, `human.handoff`, `return.initiate` actions |

---

## Importing into Dialogflow CX

1. Create a new agent at [dialogflow.cloud.google.com](https://dialogflow.cloud.google.com)
2. Go to **Agent Settings → Export/Restore**
3. Select **Restore from ZIP** and upload a ZIP containing this directory

> **Note:** The JSON files follow the Dialogflow ES export format for readability. For a production CX import, use the Dialogflow CX REST API or gcloud CLI.

---

## Running the Webhook Locally

```bash
pip install flask
python webhook_fulfillment.py
# → Serving on http://0.0.0.0:8080
```

Then expose with [ngrok](https://ngrok.com) for local testing:
```bash
ngrok http 8080
# Copy the HTTPS URL → paste into Dialogflow fulfillment settings
```

Test the webhook directly:
```bash
curl -X POST http://localhost:8080/webhook \
  -H "Content-Type: application/json" \
  -d '{
    "queryResult": {
      "action": "track.order",
      "parameters": {"order_id": "ORD-1002"}
    },
    "session": "test-session-001"
  }'
```

Expected response:
```json
{
  "fulfillmentText": "🚚 Order ORD-1002:\n  Item: Running Shoes\n  Status: In Transit\n  Date: 2026-04-14"
}
```

---

## Intent Architecture

```
User Input
    │
    ▼
┌─────────────┐     high confidence    ┌──────────────────┐
│  NLU Model  │ ──────────────────────▶│  Matched Intent   │
└─────────────┘                        └──────────────────┘
    │                                           │
    │ low confidence                    requires fulfillment?
    ▼                                           │
┌─────────────┐                    Yes ◀────────┘────────▶ No
│  Fallback   │                     │                      │
└─────────────┘              ┌──────▼──────┐    ┌──────────▼───────┐
                             │   Webhook   │    │  Static Response  │
                             └─────────────┘    └──────────────────┘
```

---

## Chapter 10 Concepts Demonstrated

- **Intent design:** Training phrase variety, covering paraphrases and typos
- **Entity extraction:** Regex entity for structured IDs (`order_id`), list entity with fuzzy matching (`product_name`)
- **Slot-filling:** `track_order` intent prompts for `order_id` if not provided
- **Context management:** `track_order_followup` output context (lifespan 3) enables follow-up intents
- **Webhook fulfillment:** Dynamic order lookup, rich response cards, live-agent handoff payload
- **Fallback handling:** `isFallback: true` on default fallback intent
