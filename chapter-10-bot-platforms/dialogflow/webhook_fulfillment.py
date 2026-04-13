"""
Dialogflow Webhook Fulfillment Handler
Chapter 10: Bot Platforms — Dialogflow

This Flask webhook handles Dialogflow fulfillment requests for:
  - Order tracking (action: track.order)
  - Human handoff (action: human.handoff)
  - Return initiation (action: return.initiate)

Deploy this to any Python-compatible host (Cloud Run, App Engine, etc.)
and point your Dialogflow agent's fulfillment webhook URL at it.

Requirements:
  pip install flask
"""

from flask import Flask, request, jsonify
import re

app = Flask(__name__)


# ─────────────────────────────────────────────
# Mock order database (mirrors customer_support_bot.py)
# ─────────────────────────────────────────────

ORDERS = {
    "ORD-1001": {"status": "Delivered",         "date": "2026-03-28", "item": "Wireless Headphones"},
    "ORD-1002": {"status": "In Transit",         "date": "2026-04-14", "item": "Running Shoes"},
    "ORD-1003": {"status": "Processing",         "date": "2026-04-16", "item": "Laptop Stand"},
    "ORD-1004": {"status": "Cancelled",          "date": "2026-04-01", "item": "Phone Case"},
    "ORD-1005": {"status": "Out for Delivery",   "date": "2026-04-12", "item": "Smart Watch"},
}

STATUS_ICONS = {
    "Delivered": "✅",
    "In Transit": "🚚",
    "Processing": "⏳",
    "Cancelled": "❌",
    "Out for Delivery": "🛵",
}


# ─────────────────────────────────────────────
# Webhook endpoint
# ─────────────────────────────────────────────

@app.route("/webhook", methods=["POST"])
def webhook():
    """
    Main Dialogflow webhook handler.
    Dialogflow sends a JSON body; we return a fulfillment response.
    """
    body = request.get_json(silent=True)

    if not body:
        return jsonify({"fulfillmentText": "Invalid request."}), 400

    action     = body.get("queryResult", {}).get("action", "")
    parameters = body.get("queryResult", {}).get("parameters", {})
    session    = body.get("session", "")

    if action == "track.order":
        return jsonify(_handle_track_order(parameters))

    if action == "human.handoff":
        return jsonify(_handle_escalation())

    if action == "return.initiate":
        return jsonify(_handle_return())

    # Default passthrough
    return jsonify({"fulfillmentText": "How else can I help you?"})


# ─────────────────────────────────────────────
# Action handlers
# ─────────────────────────────────────────────

def _handle_track_order(parameters: dict) -> dict:
    order_id = parameters.get("order_id", "").upper().replace(" ", "-")

    if not order_id:
        return {
            "fulfillmentText": (
                "Please share your order ID. "
                "It looks like ORD-XXXX and can be found in your confirmation email."
            )
        }

    order = ORDERS.get(order_id)
    if not order:
        return {
            "fulfillmentText": (
                f"I couldn't find order {order_id}. "
                "Please double-check the ID — it should be in format ORD-XXXX."
            )
        }

    icon = STATUS_ICONS.get(order["status"], "📦")
    return {
        "fulfillmentText": (
            f"{icon} Order {order_id}:\n"
            f"  Item: {order['item']}\n"
            f"  Status: {order['status']}\n"
            f"  Date: {order['date']}"
        ),
        "fulfillmentMessages": [
            {
                "card": {
                    "title": f"{icon} Order {order_id}",
                    "subtitle": f"Status: {order['status']}",
                    "imageUri": "",
                    "buttons": [
                        {
                            "text": "Track on website",
                            "postback": "https://shop.example.com/orders"
                        }
                    ]
                }
            }
        ]
    }


def _handle_escalation() -> dict:
    return {
        "fulfillmentText": (
            "Connecting you to a live agent now. "
            "Estimated wait: 3–5 minutes.\n"
            "You can also reach us at:\n"
            "  📧 support@example.com\n"
            "  📞 1800-123-4567 (Mon–Fri 9 AM–6 PM)"
        ),
        "payload": {
            "google": {
                "expectUserResponse": False
            },
            "liveAgentHandoff": True
        }
    }


def _handle_return() -> dict:
    return {
        "fulfillmentText": (
            "Our return policy:\n"
            "  • Returns accepted within 30 days of delivery.\n"
            "  • Refunds processed in 5–7 business days.\n"
            "  • Items must be unused and in original packaging.\n\n"
            "To initiate a return: support.example.com/returns"
        ),
        "fulfillmentMessages": [
            {
                "quickReplies": {
                    "title": "What would you like to do?",
                    "quickReplies": [
                        "Start a return",
                        "Talk to an agent",
                        "Track my order"
                    ]
                }
            }
        ]
    }


# ─────────────────────────────────────────────
# Health check
# ─────────────────────────────────────────────

@app.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "ok", "service": "dialogflow-webhook"})


if __name__ == "__main__":
    # For local testing only. Use a production WSGI server for deployment.
    app.run(host="0.0.0.0", port=8080, debug=True)
