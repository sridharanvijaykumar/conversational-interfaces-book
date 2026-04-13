"""
Chatbot Backend — Flask REST API
Chapter 11: Architecture & Backend Integration

This script demonstrates a production-style chatbot backend built with Flask.
It provides a REST API that a frontend (web, mobile, or voice) can call to
send messages and receive responses.

Architecture overview:
  Frontend → POST /chat → ChatEngine → (NLU + DialogueManager) → Response

Run with:
    pip install flask flask-cors
    python chatbot_backend.py
"""

import os
import uuid
import json
import logging
from datetime import datetime
from typing import Dict, Optional

from flask import Flask, request, jsonify
from flask_cors import CORS

# ─────────────────────────────────────────────
# Setup
# ─────────────────────────────────────────────

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s"
)
logger = logging.getLogger(__name__)

app = Flask(__name__)
CORS(app)  # Allow cross-origin requests from web frontends

# In-memory session store (use Redis in production)
SESSION_STORE: Dict[str, dict] = {}


# ─────────────────────────────────────────────
# Simple in-process chat engine
# (Replace with your NLU/LLM backend)
# ─────────────────────────────────────────────

class SimpleChatEngine:
    """
    A rule-based chat engine for demonstration purposes.
    In production, swap this out for an LLM API call, Rasa, or Dialogflow.
    """

    RESPONSES = {
        "greeting":   "Hello! How can I assist you today?",
        "farewell":   "Goodbye! Have a great day. 👋",
        "thanks":     "You're welcome! Is there anything else I can help with?",
        "help":       "I can help you with orders, returns, and general questions. What do you need?",
        "hours":      "We're open Monday–Friday, 9 AM to 6 PM IST.",
        "contact":    "You can reach us at support@example.com or call +91-800-123-4567.",
        "refund":     "Refunds are processed within 5–7 business days after the return is received.",
        "shipping":   "Standard shipping takes 3–5 business days. Express is 1–2 days.",
        "fallback":   "I'm sorry, I didn't quite understand that. Could you rephrase? Or type 'help' to see what I can do.",
    }

    INTENT_PATTERNS = {
        "greeting":  ["hello", "hi", "hey", "good morning", "good evening"],
        "farewell":  ["bye", "goodbye", "see you", "later", "exit"],
        "thanks":    ["thank", "thanks", "appreciate", "great"],
        "help":      ["help", "assist", "support", "what can you"],
        "hours":     ["hours", "open", "timing", "when"],
        "contact":   ["contact", "email", "phone", "reach"],
        "refund":    ["refund", "money back", "reimburs"],
        "shipping":  ["ship", "deliver", "dispatch", "courier"],
    }

    def detect_intent(self, text: str) -> str:
        text_lower = text.lower()
        for intent, patterns in self.INTENT_PATTERNS.items():
            if any(p in text_lower for p in patterns):
                return intent
        return "fallback"

    def respond(self, message: str, session: dict) -> dict:
        intent   = self.detect_intent(message)
        response = self.RESPONSES.get(intent, self.RESPONSES["fallback"])

        # Track turn count in session
        session["turn_count"] = session.get("turn_count", 0) + 1
        session["last_intent"] = intent
        session["last_active"] = datetime.utcnow().isoformat()

        return {
            "text":   response,
            "intent": intent,
            "turn":   session["turn_count"],
        }


chat_engine = SimpleChatEngine()


# ─────────────────────────────────────────────
# Session helpers
# ─────────────────────────────────────────────

def get_or_create_session(session_id: Optional[str]) -> tuple:
    """Return (session_id, session_dict), creating a new session if needed."""
    if not session_id or session_id not in SESSION_STORE:
        session_id = str(uuid.uuid4())
        SESSION_STORE[session_id] = {
            "created_at": datetime.utcnow().isoformat(),
            "turn_count": 0,
            "history":    [],
        }
        logger.info(f"New session created: {session_id}")
    return session_id, SESSION_STORE[session_id]


# ─────────────────────────────────────────────
# Routes
# ─────────────────────────────────────────────

@app.route("/health", methods=["GET"])
def health_check():
    """Health-check endpoint — used by load balancers and monitoring tools."""
    return jsonify({
        "status":       "healthy",
        "timestamp":    datetime.utcnow().isoformat(),
        "active_sessions": len(SESSION_STORE),
    })


@app.route("/chat", methods=["POST"])
def chat():
    """
    Main chat endpoint.

    Request body (JSON):
        {
            "message":    "Hello!",          # required
            "session_id": "abc-123"          # optional; omit to start new session
        }

    Response (JSON):
        {
            "session_id": "abc-123",
            "response":   "Hello! How can I assist?",
            "intent":     "greeting",
            "turn":       1,
            "timestamp":  "2026-04-12T10:00:00"
        }
    """
    data = request.get_json(silent=True)
    if not data or "message" not in data:
        return jsonify({"error": "Request body must include 'message'."}), 400

    message    = data["message"].strip()
    session_id = data.get("session_id")

    if not message:
        return jsonify({"error": "'message' cannot be empty."}), 400

    session_id, session = get_or_create_session(session_id)

    # Get response from chat engine
    result = chat_engine.respond(message, session)

    # Append to session history
    turn_record = {
        "turn":      result["turn"],
        "user":      message,
        "bot":       result["text"],
        "intent":    result["intent"],
        "timestamp": datetime.utcnow().isoformat(),
    }
    session["history"].append(turn_record)

    logger.info(
        f"Session {session_id[:8]} | Turn {result['turn']} | "
        f"Intent: {result['intent']}"
    )

    return jsonify({
        "session_id": session_id,
        "response":   result["text"],
        "intent":     result["intent"],
        "turn":       result["turn"],
        "timestamp":  turn_record["timestamp"],
    })


@app.route("/session/<session_id>/history", methods=["GET"])
def get_history(session_id: str):
    """Return the full conversation history for a session."""
    if session_id not in SESSION_STORE:
        return jsonify({"error": "Session not found."}), 404
    return jsonify({
        "session_id": session_id,
        "history":    SESSION_STORE[session_id]["history"],
        "turn_count": SESSION_STORE[session_id]["turn_count"],
    })


@app.route("/session/<session_id>", methods=["DELETE"])
def delete_session(session_id: str):
    """End and clear a session."""
    if session_id in SESSION_STORE:
        del SESSION_STORE[session_id]
        logger.info(f"Session deleted: {session_id}")
        return jsonify({"message": "Session ended."})
    return jsonify({"error": "Session not found."}), 404


@app.route("/sessions", methods=["GET"])
def list_sessions():
    """List all active sessions (for admin/debugging)."""
    return jsonify({
        "active_sessions": len(SESSION_STORE),
        "session_ids": list(SESSION_STORE.keys()),
    })


# ─────────────────────────────────────────────
# Error handlers
# ─────────────────────────────────────────────

@app.errorhandler(404)
def not_found(e):
    return jsonify({"error": "Endpoint not found."}), 404


@app.errorhandler(500)
def server_error(e):
    logger.error(f"Server error: {e}")
    return jsonify({"error": "An internal server error occurred."}), 500


# ─────────────────────────────────────────────
# Main
# ─────────────────────────────────────────────

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    debug = os.environ.get("FLASK_DEBUG", "true").lower() == "true"

    print(f"\n🤖 Chatbot Backend starting on http://localhost:{port}")
    print("   Endpoints:")
    print("     GET  /health")
    print("     POST /chat")
    print("     GET  /session/<id>/history")
    print("     DEL  /session/<id>")
    print("\n   Example request:")
    print('     curl -X POST http://localhost:5000/chat \\')
    print('       -H "Content-Type: application/json" \\')
    print('       -d \'{"message": "Hello!"}\'\n')

    app.run(host="0.0.0.0", port=port, debug=debug)
