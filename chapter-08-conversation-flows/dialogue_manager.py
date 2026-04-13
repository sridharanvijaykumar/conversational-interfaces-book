"""
Dialogue Manager - Conversation State Machine
Chapter 8: Conversational Flows & Prototyping

This script demonstrates how to implement a dialogue manager using a
finite state machine (FSM). The FSM controls the flow of a conversation
by tracking the current state and transitioning based on user intent.

Example domain: Flight booking assistant
"""

from enum import Enum, auto
from dataclasses import dataclass, field
from typing import Optional, Dict, List, Callable
import re


# ─────────────────────────────────────────────
# States
# ─────────────────────────────────────────────

class State(Enum):
    """All possible states in the conversation flow."""
    GREETING        = auto()
    COLLECT_ORIGIN  = auto()
    COLLECT_DEST    = auto()
    COLLECT_DATE    = auto()
    CONFIRM_BOOKING = auto()
    BOOKING_DONE    = auto()
    HANDLE_CANCEL   = auto()
    FALLBACK        = auto()
    END             = auto()


# ─────────────────────────────────────────────
# Slots (entities to collect)
# ─────────────────────────────────────────────

@dataclass
class BookingSlots:
    """Holds the information collected during the conversation."""
    origin:      Optional[str] = None
    destination: Optional[str] = None
    date:        Optional[str] = None
    confirmed:   bool          = False

    def is_complete(self) -> bool:
        return all([self.origin, self.destination, self.date])

    def summary(self) -> str:
        return (
            f"  From:   {self.origin}\n"
            f"  To:     {self.destination}\n"
            f"  Date:   {self.date}"
        )


# ─────────────────────────────────────────────
# Simple NLU (pattern-based)
# ─────────────────────────────────────────────

def detect_intent(text: str) -> str:
    """Detect user intent using simple pattern matching."""
    text = text.lower().strip()

    if re.search(r'\b(hi|hello|hey|good\s+morning|good\s+evening)\b', text):
        return "greeting"
    if re.search(r'\b(book|reserve|fly|flight|ticket)\b', text):
        return "book_flight"
    if re.search(r'\b(cancel|stop|nevermind|never mind|quit|exit)\b', text):
        return "cancel"
    if re.search(r'\b(yes|yeah|yep|confirm|correct|sure|ok|okay)\b', text):
        return "affirm"
    if re.search(r'\b(no|nope|nah|wrong|incorrect)\b', text):
        return "deny"
    if re.search(r'\b(bye|goodbye|see you|later|thanks)\b', text):
        return "goodbye"

    # Date patterns
    if re.search(r'\b(\d{1,2}[\/\-]\d{1,2}[\/\-]\d{2,4}|'
                 r'january|february|march|april|may|june|july|'
                 r'august|september|october|november|december|'
                 r'monday|tuesday|wednesday|thursday|friday|'
                 r'tomorrow|next week)\b', text):
        return "provide_date"

    # City patterns (very simplified)
    known_cities = [
        "delhi", "mumbai", "bangalore", "chennai", "kolkata",
        "london", "paris", "new york", "tokyo", "dubai", "singapore",
        "hyderabad", "pune", "ahmedabad", "jaipur"
    ]
    if any(city in text for city in known_cities):
        return "provide_location"

    return "unknown"


def extract_location(text: str) -> Optional[str]:
    """Extract a city name from the user's input."""
    known_cities = {
        "delhi": "New Delhi", "mumbai": "Mumbai", "bangalore": "Bangalore",
        "chennai": "Chennai", "kolkata": "Kolkata", "hyderabad": "Hyderabad",
        "pune": "Pune", "ahmedabad": "Ahmedabad", "jaipur": "Jaipur",
        "london": "London", "paris": "Paris", "new york": "New York",
        "tokyo": "Tokyo", "dubai": "Dubai", "singapore": "Singapore",
    }
    text_lower = text.lower()
    for key, city in known_cities.items():
        if key in text_lower:
            return city
    # Fallback: capitalise the first word if nothing matched
    words = text.strip().split()
    if words:
        return " ".join(w.capitalize() for w in words[:2])
    return None


def extract_date(text: str) -> Optional[str]:
    """Extract a date or time reference from the user's input."""
    # Match numeric date
    m = re.search(r'\d{1,2}[\/\-]\d{1,2}[\/\-]\d{2,4}', text)
    if m:
        return m.group(0)
    # Named months
    m = re.search(
        r'(january|february|march|april|may|june|july|august|'
        r'september|october|november|december)\s+\d{1,2}',
        text.lower()
    )
    if m:
        return m.group(0).title()
    # Relative dates
    for word in ["tomorrow", "next week", "next monday", "next friday"]:
        if word in text.lower():
            return word.title()
    # Weekdays
    for day in ["monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"]:
        if day in text.lower():
            return day.title()
    return text.strip()  # Return raw input as fallback


# ─────────────────────────────────────────────
# Dialogue Manager
# ─────────────────────────────────────────────

class DialogueManager:
    """
    A finite-state-machine dialogue manager for a flight booking bot.

    Transitions are driven by the detected intent and current state.
    Slots are filled incrementally as the user provides information.
    """

    def __init__(self):
        self.state   = State.GREETING
        self.slots   = BookingSlots()
        self.history: List[Dict] = []
        self.turn    = 0

    # ── Public API ────────────────────────────

    def respond(self, user_input: str) -> str:
        """Process a user utterance and return the bot's response."""
        self.turn += 1
        intent  = detect_intent(user_input)
        response = self._transition(user_input, intent)

        self.history.append({
            "turn":     self.turn,
            "user":     user_input,
            "intent":   intent,
            "state":    self.state.name,
            "bot":      response,
        })
        return response

    def is_done(self) -> bool:
        return self.state in (State.END,)

    def print_history(self):
        print("\n=== Conversation History ===")
        for h in self.history:
            print(f"\n[Turn {h['turn']}] State: {h['state']} | Intent: {h['intent']}")
            print(f"  User: {h['user']}")
            print(f"  Bot:  {h['bot']}")

    # ── State machine ─────────────────────────

    def _transition(self, text: str, intent: str) -> str:

        # Cancel can happen from any state
        if intent == "cancel" and self.state not in (State.END, State.BOOKING_DONE):
            self.state = State.HANDLE_CANCEL
            return self._handle_cancel()

        if self.state == State.GREETING:
            return self._handle_greeting(intent)

        if self.state == State.COLLECT_ORIGIN:
            return self._handle_origin(text, intent)

        if self.state == State.COLLECT_DEST:
            return self._handle_destination(text, intent)

        if self.state == State.COLLECT_DATE:
            return self._handle_date(text, intent)

        if self.state == State.CONFIRM_BOOKING:
            return self._handle_confirmation(intent)

        if self.state == State.HANDLE_CANCEL:
            return self._handle_cancel()

        if self.state in (State.BOOKING_DONE, State.END):
            self.state = State.END
            return "Your booking is complete. Safe travels! Type 'book' to start a new booking."

        return self._fallback()

    # ── Handlers ──────────────────────────────

    def _handle_greeting(self, intent: str) -> str:
        if intent in ("greeting", "book_flight", "unknown"):
            self.state = State.COLLECT_ORIGIN
            return (
                "Hello! Welcome to SkyBot, your flight booking assistant. ✈️\n"
                "I can help you book a flight in just a few steps.\n\n"
                "Where would you like to fly FROM?"
            )
        if intent == "goodbye":
            self.state = State.END
            return "Goodbye! Have a wonderful day. 👋"
        return self._fallback()

    def _handle_origin(self, text: str, intent: str) -> str:
        location = extract_location(text)
        if location:
            self.slots.origin = location
            self.state = State.COLLECT_DEST
            return f"Got it — departing from {location}. 🛫\nAnd where are you flying TO?"
        return (
            "I didn't catch that. Could you please tell me your departure city?\n"
            "For example: 'Mumbai' or 'New Delhi'"
        )

    def _handle_destination(self, text: str, intent: str) -> str:
        location = extract_location(text)
        if location:
            if location == self.slots.origin:
                return "Your destination can't be the same as your origin! Where would you like to fly TO?"
            self.slots.destination = location
            self.state = State.COLLECT_DATE
            return (
                f"Perfect — flying from {self.slots.origin} to {location}. 🌍\n"
                "What date would you like to travel? (e.g. '15/06/2026' or 'Next Monday')"
            )
        return (
            "I didn't catch that destination. Could you please name a city?\n"
            "For example: 'London' or 'Singapore'"
        )

    def _handle_date(self, text: str, intent: str) -> str:
        date = extract_date(text)
        if date:
            self.slots.date = date
            self.state = State.CONFIRM_BOOKING
            return (
                f"Great! Here's a summary of your booking:\n\n"
                f"{self.slots.summary()}\n\n"
                "Shall I confirm this booking? (yes / no)"
            )
        return "Please provide a travel date. For example: '20/06/2026' or 'Next Friday'."

    def _handle_confirmation(self, intent: str) -> str:
        if intent == "affirm":
            self.slots.confirmed = True
            self.state = State.BOOKING_DONE
            return (
                "✅ Your flight has been booked!\n\n"
                f"{self.slots.summary()}\n\n"
                "A confirmation will be sent to you. Is there anything else I can help with?"
            )
        if intent == "deny":
            self.slots = BookingSlots()
            self.state = State.COLLECT_ORIGIN
            return "No problem! Let's start over. Where would you like to fly FROM?"
        return "Please reply with 'yes' to confirm or 'no' to start over."

    def _handle_cancel(self) -> str:
        self.slots = BookingSlots()
        self.state = State.GREETING
        return "No problem — booking cancelled. Feel free to start a new one anytime!"

    def _fallback(self) -> str:
        self.state = State.FALLBACK
        return (
            "I'm sorry, I didn't understand that. 🤔\n"
            "You can say things like:\n"
            "  • 'Book a flight'\n"
            "  • 'Cancel'\n"
            "  • 'Yes' / 'No'"
        )


# ─────────────────────────────────────────────
# Main
# ─────────────────────────────────────────────

def demo_scripted():
    """Run a scripted demo conversation."""
    print("=== Scripted Demo ===\n")
    dm = DialogueManager()

    exchanges = [
        "Hello!",
        "I want to book a flight",
        "Mumbai",
        "London",
        "15/07/2026",
        "yes",
    ]

    for utterance in exchanges:
        print(f"User: {utterance}")
        response = dm.respond(utterance)
        print(f"Bot:  {response}\n")

    dm.print_history()


def interactive_mode():
    """Run an interactive conversation in the terminal."""
    print("\n=== Interactive Mode ===")
    print("Talk to SkyBot (type 'quit' to exit)\n")
    dm = DialogueManager()

    # Kick off with the greeting
    print(f"Bot: {dm.respond('hello')}\n")

    while not dm.is_done():
        user_input = input("You: ").strip()
        if not user_input:
            continue
        if user_input.lower() in ("quit", "exit", "q"):
            print("Bot: Goodbye! 👋")
            break
        print(f"Bot: {dm.respond(user_input)}\n")


if __name__ == "__main__":
    demo_scripted()
    print("\n" + "=" * 50 + "\n")
    interactive_mode()
